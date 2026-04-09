#!/usr/bin/env python3
"""
al-write.py — Unified markdown write operations for Agent Lattice.

Validates content against a structural schema, then writes the file.
Replaces al-artifacts.py (init, append, update-frontmatter, validate).

Usage:
  al-write.py write   --module MOD --path REL_PATH --type TYPE
                       [--mode overwrite|append] [--content TEXT]
  al-write.py schema  --module MOD --type TYPE
  al-write.py list    --module MOD --dir REL_DIR

Content is read from stdin (heredoc) by default, or --content for short text.
All commands output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from al_paths import resolve_path, resolve_module_output, resolve_module_dir


RUNTIME_SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas")


def load_schema(schema_type, module=None):
    """Load schema, checking module schemas first, then runtime schemas."""
    if module:
        mod_dir = resolve_module_dir(module)
        if mod_dir:
            mod_schema = os.path.join(mod_dir, "schemas", f"{schema_type}.json")
            if os.path.isfile(mod_schema):
                with open(mod_schema, encoding="utf-8") as f:
                    return json.load(f)
    rt_schema = os.path.join(RUNTIME_SCHEMAS_DIR, f"{schema_type}.json")
    if os.path.isfile(rt_schema):
        with open(rt_schema, encoding="utf-8") as f:
            return json.load(f)
    return None


# --- Validation helpers ---

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


def extract_h1(content):
    """Extract the first H1 heading from content."""
    for line in content.split("\n"):
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return None


def parse_entries(content, heading_pattern):
    """Parse entries delimited by a heading pattern (e.g., '## Persona: Name')."""
    entries = []
    current = None
    for line in content.split("\n"):
        match = re.match(heading_pattern, line)
        if match:
            if current:
                entries.append(current)
            current = {"name": match.group(1).strip(), "fields": {}, "_last_key": None}
            continue
        if current is None:
            continue
        stripped = line.strip()
        # Bold-key field: - **Key:** value
        field = re.match(r'^- \*\*(.+?):\*\*\s*(.*)', stripped)
        if field:
            key = field.group(1).lower().strip()
            val = field.group(2).strip().strip('"')
            if val:
                current["fields"][key] = val
            else:
                current["fields"][key] = []
            current["_last_key"] = key
            continue
        # Sub-item:   - value
        sub = re.match(r'^\s+- (.+)', line)
        if sub and current["_last_key"]:
            key = current["_last_key"]
            if isinstance(current["fields"].get(key), list):
                current["fields"][key].append(sub.group(1).strip())
            continue
    if current:
        entries.append(current)
    for e in entries:
        e.pop("_last_key", None)
    return entries


def get_section_text(content, heading, level=2):
    """Extract the raw text of a section (from heading to next same-level heading or EOF)."""
    prefix = "#" * level
    pattern = rf'^{prefix}\s+{re.escape(heading)}\s*$'
    lines = content.split("\n")
    in_section = False
    section_lines = []
    for line in lines:
        if re.match(pattern, line, re.IGNORECASE):
            in_section = True
            continue
        if in_section:
            if re.match(rf'^{prefix}\s+', line) and not line.startswith(prefix + "#"):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


# --- JSON validation engine ---

def validate_json_content(content, schema):
    """Validate JSON content against a JSON-format schema."""
    findings = []

    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        findings.append({"severity": "critical", "issue": f"Invalid JSON: {e}"})
        return findings

    # Rule: required_keys — top-level keys that must exist
    for key in schema.get("required_keys", []):
        if key not in data:
            findings.append({"severity": "critical", "issue": f"Missing required key '{key}'"})

    # Rule: properties — type and structure checks for top-level keys
    for key, prop_schema in schema.get("properties", {}).items():
        if key not in data:
            continue
        val = data[key]

        # Type check
        expected_type = prop_schema.get("type")
        type_map = {"array": list, "object": dict, "string": str, "number": (int, float)}
        if expected_type and expected_type in type_map:
            if not isinstance(val, type_map[expected_type]):
                findings.append({"severity": "critical",
                                 "issue": f"'{key}' must be {expected_type}, got {type(val).__name__}"})
                continue

        # Array-specific: min_items, item checks
        if isinstance(val, list):
            min_items = prop_schema.get("min_items", 0)
            if len(val) < min_items:
                findings.append({"severity": "high",
                                 "issue": f"'{key}' has {len(val)} items (minimum {min_items})"})

            # item_required_keys — each item must have these keys
            item_required = prop_schema.get("item_required_keys", [])
            if item_required:
                for i, item in enumerate(val):
                    if not isinstance(item, dict):
                        findings.append({"severity": "high",
                                         "issue": f"'{key}[{i}]' must be an object"})
                        continue
                    for rk in item_required:
                        if rk not in item:
                            findings.append({"severity": "high",
                                             "issue": f"'{key}[{i}]' missing required key '{rk}'"})

            # item_properties — type checks on item fields
            item_props = prop_schema.get("item_properties", {})
            if item_props:
                for i, item in enumerate(val):
                    if not isinstance(item, dict):
                        continue
                    for ik, ip_schema in item_props.items():
                        if ik not in item:
                            continue
                        iv = item[ik]
                        itype = ip_schema.get("type")
                        if itype and itype in type_map:
                            if not isinstance(iv, type_map[itype]):
                                findings.append({"severity": "high",
                                                 "issue": f"'{key}[{i}].{ik}' must be {itype}, got {type(iv).__name__}"})

    return findings


# --- Markdown validation engine ---
# One function, all rules declared in the schema. If a key exists, it's applied.

def validate_content(content, schema):
    """Validate markdown content against all rules declared in the schema."""
    findings = []

    # Rule: h1_required
    if schema.get("h1_required") and not extract_h1(content):
        findings.append({"severity": "critical", "issue": "Missing H1 heading"})

    # Rule: min_content_length
    min_len = schema.get("min_content_length", 0)
    if min_len and len(content.strip()) < min_len:
        findings.append({"severity": "high",
                         "issue": f"Content too short ({len(content.strip())} chars, minimum {min_len})"})

    # Rule: required_sections — heading presence, optional min_items, min_length, no_generic
    for section in schema.get("required_sections", []):
        heading = section["heading"]
        level = section.get("level", 2)
        prefix = "#" * level
        if not re.search(rf'^{prefix}\s+{re.escape(heading)}\s*$', content, re.MULTILINE | re.IGNORECASE):
            findings.append({"severity": "high", "issue": f"Missing '{prefix} {heading}' section"})
        else:
            if section.get("min_length"):
                text = get_section_text(content, heading, level).strip()
                if len(text) < section["min_length"]:
                    findings.append({"severity": "medium",
                                     "issue": f"'{heading}' section too brief ({len(text)} chars)"})
            min_items = section.get("min_items", 0)
            if min_items:
                items = extract_section_items(content, heading)
                if len(items) < min_items:
                    findings.append({"severity": "high",
                                     "issue": f"'{heading}' has {len(items)} items (minimum {min_items})"})
                if section.get("no_generic"):
                    for item in items:
                        if is_generic(item):
                            findings.append({"severity": "medium",
                                             "issue": f"Generic '{heading}' entry: '{item}'"})

    # Rule: content_patterns — regex matches across the whole document
    for pat_rule in schema.get("content_patterns", []):
        matches = re.findall(pat_rule["pattern"], content, re.MULTILINE)
        min_matches = pat_rule.get("min_matches", 1)
        if len(matches) < min_matches:
            desc = pat_rule.get("description", pat_rule["pattern"])
            findings.append({"severity": "high",
                             "issue": f"Expected at least {min_matches} matches for {desc}, found {len(matches)}"})

    # Rule: entries — repeating entry blocks with bold-key fields
    entries_schema = schema.get("entries")
    if entries_schema:
        pattern = entries_schema["heading_pattern"]
        entries = parse_entries(content, pattern)
        if not entries:
            findings.append({"severity": "critical", "issue": "No entries found"})
        else:
            min_entries = entries_schema.get("min_entries", 1)
            max_entries = entries_schema.get("max_entries")
            if len(entries) < min_entries:
                findings.append({"severity": "high",
                                 "issue": f"Only {len(entries)} entries found (minimum {min_entries})"})
            if max_entries and len(entries) > max_entries:
                findings.append({"severity": "medium",
                                 "issue": f"{len(entries)} entries found (recommended maximum {max_entries})"})
            required_fields = entries_schema.get("required_bold_fields", [])
            multi_fields = entries_schema.get("multi_value_fields", {})
            for entry in entries:
                name = f"'{entry['name']}'"
                for field in required_fields:
                    val = entry["fields"].get(field)
                    if val is None:
                        findings.append({"severity": "high",
                                         "issue": f"{name}: missing required field '{field}'"})
                    elif isinstance(val, list):
                        min_items = multi_fields.get(field, 0)
                        if min_items and len(val) < min_items:
                            findings.append({"severity": "high",
                                             "issue": f"{name}: '{field}' has {len(val)} items (minimum {min_items})"})
                    elif isinstance(val, str) and not val.strip():
                        findings.append({"severity": "high",
                                         "issue": f"{name}: field '{field}' is empty"})

    # Rule: subsections — required sub-headings within a parent section
    for sub in schema.get("subsections", []):
        parent_text = get_section_text(content, sub["parent"], level=sub.get("parent_level", 2))
        if parent_text:
            child_level = sub.get("level", 3)
            child_prefix = "#" * child_level
            for child in sub.get("required", []):
                if not re.search(rf'^{child_prefix}\s+{re.escape(child)}\s*$',
                                 parent_text, re.MULTILINE | re.IGNORECASE):
                    findings.append({"severity": "high",
                                     "issue": f"'{sub['parent']}' missing '{child_prefix} {child}' section"})

    # Rule: section_patterns — regex matches scoped to a specific section
    for sp in schema.get("section_patterns", []):
        section_text = get_section_text(content, sp["section"], level=sp.get("level", 2))
        if section_text:
            matches = re.findall(sp["pattern"], section_text, re.MULTILINE)
            min_matches = sp.get("min_matches", 1)
            if len(matches) < min_matches:
                desc = sp.get("description", sp["pattern"])
                findings.append({"severity": "high",
                                 "issue": f"'{sp['section']}' has {len(matches)} matches for {desc} (minimum {min_matches})"})

    return findings


# --- Commands ---

def cmd_write(args):
    full_path = resolve_path(args.module, args.path)
    if not full_path:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)

    # Read content
    if args.content:
        content = args.content
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print(json.dumps({"status": "error", "message": "No content provided (use stdin or --content)"}))
        sys.exit(1)

    # Load and validate against schema (checks module schemas first, then runtime)
    schema = load_schema(args.type, args.module)
    if schema is None:
        print(json.dumps({"status": "error", "message": f"Unknown type '{args.type}'. No schema found in module or runtime schemas."}))
        sys.exit(1)

    # For append mode, validate the full document (existing + new content)
    mode = args.mode or "overwrite"
    validate_text = content
    if mode == "append" and os.path.isfile(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            existing = f.read()
        validate_text = existing + "\n\n" + content

    if schema.get("format") == "json":
        findings = validate_json_content(validate_text, schema)
    else:
        findings = validate_content(validate_text, schema)
    critical = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")

    if critical > 0 or high > 0:
        print(json.dumps({
            "status": "fail",
            "findings": findings,
            "summary": {"total": len(findings), "critical": critical, "high": high},
        }))
        sys.exit(1)

    # Write file
    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
    if mode == "append":
        with open(full_path, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    result = {"status": "ok", "path": full_path}
    if findings:
        result["warnings"] = findings
    print(json.dumps(result))


def cmd_schema(args):
    schema = load_schema(args.type, args.module)
    if schema is None:
        print(json.dumps({"status": "error", "message": f"Unknown type '{args.type}'. No schema found in module or runtime schemas."}))
        sys.exit(1)
    print(json.dumps({"status": "ok", "type": args.type, "schema": schema}))


def cmd_list(args):
    output = resolve_module_output(args.module)
    if not output:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)
    full_dir = os.path.join(output, args.dir)
    if not os.path.isdir(full_dir):
        print(json.dumps({"status": "error", "message": f"Directory not found: {full_dir}"}))
        sys.exit(1)
    artifacts = []
    for fname in sorted(os.listdir(full_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(full_dir, fname)
        if not os.path.isfile(path):
            continue
        artifacts.append({"filename": fname, "path": path})
    print(json.dumps({"status": "ok", "artifacts": artifacts, "count": len(artifacts)}))


def main():
    parser = argparse.ArgumentParser(description="Agent Lattice unified write operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("write", help="Write content with structural validation")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--path", required=True, help="Module-relative path")
    p.add_argument("--type", required=True, help="Schema name (loads from module or runtime schemas/)")
    p.add_argument("--mode", choices=["overwrite", "append"], default="overwrite", help="Write mode (default: overwrite)")
    p.add_argument("--content", help="Content string (short text; prefer stdin for large content)")

    p = sub.add_parser("schema", help="Show the validation schema for a type")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--type", required=True, help="Schema name (loads from module or runtime schemas/)")

    p = sub.add_parser("list", help="List artifacts in a directory")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--dir", required=True, help="Module-relative directory")

    args = parser.parse_args()
    commands = {
        "write": cmd_write,
        "schema": cmd_schema,
        "list": cmd_list,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
