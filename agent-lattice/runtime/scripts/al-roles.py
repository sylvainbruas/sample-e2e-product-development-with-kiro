#!/usr/bin/env python3
"""
al-roles.py — Role operations for Agent Lattice.

Generic role validation and discovery. Works with any module's
role definitions that follow the H1 heading + metadata + markdown body format.

Usage:
  al-roles.py validate [--module MOD] --source FILE [--schema FILE]
  al-roles.py discover [--module MOD] [--static-dir DIR] [--dynamic-dir DIR]
  al-roles.py append-section [--module MOD] --source FILE --section NAME [--content TEXT] [--content-file FILE]
  al-roles.py read-profile [--module MOD] --source FILE

All commands output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import re
import sys

from al_paths import resolve_path, resolve_module_dir, resolve_module_output


def extract_section_items(body, heading):
    """Extract bullet items under a markdown ## heading."""
    pattern = rf'^##\s+{re.escape(heading)}\s*$'
    lines = body.split("\n")
    items = []
    in_section = False

    for line in lines:
        if re.match(pattern, line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())

    return items


def extract_metadata(body):
    """Extract bold-key metadata lines between H1 and first ## heading."""
    metadata = {}
    lines = body.split("\n")
    past_h1 = False

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            past_h1 = True
            continue
        if not past_h1:
            continue
        if line.startswith("## "):
            break
        match = re.match(r'^- \*\*(.+?):\*\*\s*(.*)', line.strip())
        if match:
            key = match.group(1).strip().lower()
            metadata[key] = match.group(2).strip()

    return metadata


def is_generic(text):
    """Check if a text is too generic / shallow."""
    generic_patterns = [
        r'^wants things to be better$',
        r'^improve\w* things$',
        r'^make\w* it better$',
        r'^help\w* people$',
        r'^do\w* good work$',
    ]
    text_lower = text.lower().strip()
    if len(text_lower.split()) < 4:
        return True
    for pat in generic_patterns:
        if re.match(pat, text_lower):
            return True
    return False


def cmd_validate(args):
    """Validate a role definition file."""
    findings = []

    # Resolve source: --slug (dynamic role) or --source (any file)
    if hasattr(args, 'slug') and args.slug and args.module:
        source = resolve_path(args.module, f"roles/{args.slug}.md")
    elif hasattr(args, 'source') and args.source:
        source = args.source
        if hasattr(args, 'module') and args.module and not os.path.isabs(source):
            source = resolve_path(args.module, source)
    else:
        print(json.dumps({"status": "error", "message": "Provide --slug (with --module) or --source"}))
        sys.exit(1)

    if not source:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)

    if not os.path.exists(source):
        print(json.dumps({"status": "error", "message": f"File not found: {source}"}))
        sys.exit(1)

    with open(source, encoding="utf-8") as f:
        body = f.read()

    # --- Runtime contract: H1 + metadata ---

    # Check H1 (display name)
    has_h1 = any(line.startswith("# ") and not line.startswith("## ") for line in body.split("\n"))
    if not has_h1:
        findings.append({
            "severity": "critical",
            "issue": "Missing H1 heading (display name)",
            "fix": "Add '# {Display Name}' as the first heading",
        })

    # Check metadata
    metadata = extract_metadata(body)
    if "type" not in metadata:
        findings.append({
            "severity": "high",
            "issue": "Missing metadata: Type",
            "fix": "Add '- **Type:** {role type}' after the H1 heading",
        })
    if "role" not in metadata:
        findings.append({
            "severity": "high",
            "issue": "Missing metadata: Role",
            "fix": "Add '- **Role:** {one-line description}' after the H1 heading",
        })

    # --- Module schema validation (optional) ---

    schema_path = getattr(args, 'schema', None)
    if schema_path:
        if args.module and not os.path.isabs(schema_path):
            mod_dir = resolve_module_dir(args.module)
            if mod_dir:
                schema_path = os.path.join(mod_dir, schema_path)
        if os.path.exists(schema_path):
            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)
            findings.extend(_validate_schema(body, schema))

    status = "pass" if not findings else "fail"
    critical = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")

    print(json.dumps({
        "script": "al-roles",
        "status": status,
        "findings": findings,
        "summary": {"total": len(findings), "critical": critical, "high": high},
    }))

    if findings:
        sys.exit(1)


def _validate_schema(body, schema):
    """Validate role body against a module role schema."""
    findings = []

    # Required sections
    for section_name in schema.get("required_sections", []):
        items = extract_section_items(body, section_name)
        if not items:
            # Check if section heading exists at all
            pattern = rf'^##\s+{re.escape(section_name)}\s*$'
            if not re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
                findings.append({
                    "severity": "high",
                    "issue": f"Missing required section: {section_name}",
                    "fix": f"Add '## {section_name}' with content",
                })

    # Min items per section
    min_items = schema.get("min_items_per_section", 0)
    if min_items > 0:
        for section_name in schema.get("required_sections", []):
            items = extract_section_items(body, section_name)
            if 0 < len(items) < min_items:
                findings.append({
                    "severity": "high",
                    "issue": f"'{section_name}' has {len(items)} entries (minimum {min_items})",
                    "fix": f"Add more entries to '## {section_name}'",
                })

    # Generic check on specified sections
    for section_name in schema.get("check_generic", []):
        items = extract_section_items(body, section_name)
        for item in items:
            if is_generic(item):
                findings.append({
                    "severity": "medium",
                    "issue": f"Generic '{section_name}' entry: '{item}'",
                    "fix": "Replace with a specific, domain-informed entry",
                })

    # Required context fields (for ## Context sections with bold-key format)
    for field_name in schema.get("required_context_fields", []):
        pattern = rf'- \*\*{re.escape(field_name)}:\*\*'
        if not re.search(pattern, body, re.IGNORECASE):
            findings.append({
                "severity": "high",
                "issue": f"Missing context field: {field_name}",
                "fix": f"Add '- **{field_name.title()}:** {{value}}' to the Context section",
            })

    return findings


def cmd_discover(args):
    """Discover available roles from static and dynamic directories."""
    roles = []

    static_dir = args.static_dir
    dynamic_dir = args.dynamic_dir

    # If --module is provided, resolve dirs automatically
    if args.module:
        mod_dir = resolve_module_dir(args.module)
        if mod_dir:
            static_dir = static_dir or os.path.join(mod_dir, "roles")
        output_dir = resolve_module_output(args.module)
        if output_dir:
            dynamic_dir = dynamic_dir or os.path.join(output_dir, "roles")

    def scan_dir(directory, source_type):
        if not directory or not os.path.isdir(directory):
            return
        for fname in sorted(os.listdir(directory)):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(directory, fname)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            # Derive display name from H1 heading
            name = os.path.splitext(fname)[0]
            for line in content.split("\n"):
                if line.startswith("# ") and not line.startswith("## "):
                    name = line[2:].strip()
                    break
            # Extract metadata
            metadata = extract_metadata(content)
            roles.append({
                "name": name,
                "type": metadata.get("type", ""),
                "role": metadata.get("role", ""),
                "path": path,
                "source": source_type,
            })

    scan_dir(static_dir, "static")
    scan_dir(dynamic_dir, "dynamic")

    print(json.dumps({"status": "ok", "roles": roles, "count": len(roles)}))


def cmd_append_section(args):
    """Append a named section to a role file without touching existing content."""
    # Resolve source: --slug (dynamic role) or --source (any file)
    if hasattr(args, 'slug') and args.slug and args.module:
        source = resolve_path(args.module, f"roles/{args.slug}.md")
    elif args.source:
        source = args.source
        if args.module and not os.path.isabs(source):
            source = resolve_path(args.module, source)
    else:
        print(json.dumps({"status": "error", "message": "Provide --slug (with --module) or --source"}))
        sys.exit(1)

    if not source:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)

    if not os.path.exists(source):
        print(json.dumps({"status": "error", "message": f"File not found: {source}"}))
        sys.exit(1)

    # Read content from --content or --content-file
    if args.content:
        content = args.content
    elif args.content_file:
        with open(args.content_file, encoding="utf-8") as f:
            content = f.read()
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print(json.dumps({"status": "error", "message": "Provide --content or --content-file"}))
        sys.exit(1)

    with open(source, encoding="utf-8") as f:
        existing = f.read()

    section_heading = f"## {args.section}"

    # Check if section already exists — replace it
    section_pattern = rf'^## {re.escape(args.section)}\s*$'
    lines = existing.split("\n")
    new_lines = []
    in_old_section = False
    replaced = False

    for line in lines:
        if re.match(section_pattern, line, re.MULTILINE):
            in_old_section = True
            replaced = True
            # Write new section
            new_lines.append(section_heading)
            new_lines.append("")
            new_lines.append(content.strip())
            new_lines.append("")
            continue
        if in_old_section:
            if line.startswith("## "):
                in_old_section = False
                new_lines.append(line)
            # Skip old section content
            continue
        new_lines.append(line)

    if not replaced:
        # Append new section at the end
        new_lines.append("")
        new_lines.append(section_heading)
        new_lines.append("")
        new_lines.append(content.strip())
        new_lines.append("")

    # Delete temp file if requested
    if getattr(args, 'delete_after', False) and args.content_file and os.path.exists(args.content_file):
        os.remove(args.content_file)

    with open(source, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    action = "replaced" if replaced else "appended"
    print(json.dumps({"status": "ok", "source": source, "section": args.section, "action": action}))


def cmd_read_profile(args):
    """Read a role file and output all sections as structured JSON."""
    if hasattr(args, 'slug') and args.slug and args.module:
        source = resolve_path(args.module, f"roles/{args.slug}.md")
    elif args.source:
        source = args.source
        if args.module and not os.path.isabs(source):
            source = resolve_path(args.module, source)
    else:
        print(json.dumps({"status": "error", "message": "Provide --slug (with --module) or --source"}))
        sys.exit(1)

    if not source or not os.path.exists(source):
        print(json.dumps({"status": "error", "message": "File not found"}))
        sys.exit(1)

    with open(source, encoding="utf-8") as f:
        body = f.read()

    # Extract metadata
    metadata = extract_metadata(body)

    # Extract all ## sections
    sections = {}
    current_section = None
    current_items = []

    for line in body.split("\n"):
        heading_match = re.match(r'^## (.+)$', line)
        if heading_match:
            if current_section:
                sections[current_section] = current_items
            current_section = heading_match.group(1).strip()
            current_items = []
            continue
        if current_section:
            stripped = line.strip()
            if stripped.startswith("- "):
                # Check for sub-items (indented)
                if line.startswith("  - "):
                    if current_items and isinstance(current_items[-1], dict):
                        current_items[-1]["items"].append(stripped[2:].strip())
                    else:
                        current_items.append(stripped[2:].strip())
                else:
                    # Check for bold-key format: - **Key:** value
                    bold_match = re.match(r'^- \*\*(.+?):\*\*\s*(.*)', stripped)
                    if bold_match:
                        key = bold_match.group(1).strip()
                        val = bold_match.group(2).strip()
                        if val:
                            current_items.append({"key": key, "value": val})
                        else:
                            current_items.append({"key": key, "items": []})
                    else:
                        current_items.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                current_items.append(stripped)

    if current_section:
        sections[current_section] = current_items

    print(json.dumps({"status": "ok", "metadata": metadata, "sections": sections}))


def main():
    parser = argparse.ArgumentParser(description="Agent Lattice role operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="Validate a role definition")
    p.add_argument("--source", help="File path (for static roles or arbitrary files)")
    p.add_argument("--module", help="Module name")
    p.add_argument("--slug", help="Persona slug (resolves to {output}/roles/{slug}.md)")
    p.add_argument("--schema", help="Module role schema file (JSON)")

    p = sub.add_parser("discover", help="Discover available roles")
    p.add_argument("--module", help="Module name (auto-resolves dirs)")
    p.add_argument("--static-dir", help="Static roles directory (overrides --module)")
    p.add_argument("--dynamic-dir", help="Dynamic roles directory (overrides --module)")

    p = sub.add_parser("append-section", help="Append or replace a named section in a role file")
    p.add_argument("--source", help="File path")
    p.add_argument("--module", help="Module name")
    p.add_argument("--slug", help="Persona slug (resolves to {output}/roles/{slug}.md)")
    p.add_argument("--section", required=True, help="Section heading")
    p.add_argument("--content", help="Content string (short)")
    p.add_argument("--content-file", help="File to read content from (large)")
    p.add_argument("--delete-after", action="store_true", help="Delete --content-file after success")

    p = sub.add_parser("read-profile", help="Read all sections from a role file as JSON")
    p.add_argument("--source", help="File path")
    p.add_argument("--module", help="Module name")
    p.add_argument("--slug", help="Persona slug (resolves to {output}/roles/{slug}.md)")

    args = parser.parse_args()
    commands = {
        "validate": cmd_validate,
        "discover": cmd_discover,
        "append-section": cmd_append_section,
        "read-profile": cmd_read_profile,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
