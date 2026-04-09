#!/usr/bin/env python3
"""
al-dt-roles.py — Design Thinking role operations.

Converts personas from the empathize phase into dynamic role definition files.
Validates personas against the strict format defined in steering/persona-format.md.
Enriches role files with data extracted from workflow artifacts.

Usage:
  al-dt-roles.py create-from-personas --module MOD --personas REL_PATH
  al-dt-roles.py validate-personas --module MOD --personas REL_PATH
  al-dt-roles.py enrich-role --module MOD --source SOURCE

Sources for enrich-role: interviews, empathy-maps, insights, user-flows, requirements.

Paths are module-relative, resolved to .al/output/{module}/.

Output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))


def slugify(name):
    """Convert a name to a filename slug, transliterating accents."""
    normalized = unicodedata.normalize('NFKD', name)
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')


REQUIRED_FIELDS = ["age", "occupation", "location", "goals", "frustrations", "behaviors", "skeptical of", "quote"]
MULTI_VALUE_FIELDS = ["goals", "frustrations", "behaviors", "skeptical of"]
MIN_MULTI_ITEMS = 2


def parse_personas(content):
    """Parse personas from the strict format. Returns list of dicts."""
    personas = []
    current = None

    for line in content.split("\n"):
        # New persona
        heading = re.match(r'^## Persona:\s+(.+)$', line)
        if heading:
            if current:
                personas.append(current)
            current = {"name": heading.group(1).strip(), "fields": {}, "_lines": []}
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
        if sub and "_last_key" in current:
            key = current["_last_key"]
            if isinstance(current["fields"].get(key), list):
                current["fields"][key].append(sub.group(1).strip())
            continue

    if current:
        personas.append(current)

    # Clean up internal keys
    for p in personas:
        p.pop("_last_key", None)
        p.pop("_lines", None)

    return personas


def validate_personas(personas):
    """Validate parsed personas against the strict format. Returns findings list."""
    findings = []

    if not personas:
        findings.append({"severity": "critical", "issue": "No personas found"})
        return findings

    for i, p in enumerate(personas):
        prefix = f"Persona '{p['name']}'"

        for field in REQUIRED_FIELDS:
            val = p["fields"].get(field)
            if val is None:
                findings.append({"severity": "high", "issue": f"{prefix}: missing required field '{field}'"})
            elif isinstance(val, list):
                if field in MULTI_VALUE_FIELDS and len(val) < MIN_MULTI_ITEMS:
                    findings.append({"severity": "high", "issue": f"{prefix}: '{field}' has {len(val)} items (minimum {MIN_MULTI_ITEMS})"})
            elif isinstance(val, str) and not val.strip():
                findings.append({"severity": "high", "issue": f"{prefix}: field '{field}' is empty"})

    return findings


def persona_to_role(persona):
    """Convert a parsed persona to role file content."""
    f = persona["fields"]
    name = persona["name"]
    slug = slugify(name)

    occupation = f.get("occupation", "")
    age = f.get("age", "")
    location = f.get("location", "")
    role_parts = [p for p in [occupation, age, location] if p]
    role_desc = ", ".join(role_parts)

    lines = [f"# {name}"]
    lines.append("")
    lines.append("- **Type:** persona")
    lines.append(f"- **Role:** {role_desc}")
    lines.append("")

    # Context
    lines.append("## Context")
    lines.append("")
    for key in ["age", "occupation", "location", "demographics", "devices"]:
        val = f.get(key)
        if val and isinstance(val, str):
            lines.append(f"- **{key.title()}:** {val}")
    for key in ["goals", "frustrations", "behaviors"]:
        val = f.get(key)
        if val and isinstance(val, list):
            lines.append(f"- **{key.title()}:**")
            for item in val:
                lines.append(f"  - {item}")
    env = f.get("environment", "")
    if env:
        lines.append(f"- **Environment:** {env}")
    quote = f.get("quote", "")
    if quote:
        lines.append(f'- **Quote:** "{quote}"')
    lines.append("")

    # Skeptical of
    skeptical = f.get("skeptical of", [])
    if isinstance(skeptical, str):
        skeptical = [skeptical] if skeptical else []
    lines.append("## Skeptical of")
    lines.append("")
    for item in skeptical:
        lines.append(f"- {item}")
    lines.append("")

    return "\n".join(lines), slug


def cmd_validate_personas(args):
    """Validate a personas file against the strict format."""
    # Resolve path
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "runtime", "scripts"))
    try:
        from al_paths import resolve_path
    except ImportError:
        # Installed layout
        sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "..", "runtime", "scripts"))
        from al_paths import resolve_path

    full_path = resolve_path(args.module, args.personas) if args.module else args.personas
    if not full_path or not os.path.exists(full_path):
        print(json.dumps({"status": "error", "message": f"File not found: {args.personas}"}))
        sys.exit(1)

    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    personas = parse_personas(content)
    findings = validate_personas(personas)

    status = "pass" if not findings else "fail"
    print(json.dumps({
        "script": "al-dt-roles",
        "status": status,
        "personas": len(personas),
        "findings": findings,
        "summary": {"total": len(findings)},
    }))
    if findings:
        sys.exit(1)


def cmd_create_from_personas(args):
    """Convert personas file to dynamic role definitions."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "runtime", "scripts"))
    try:
        from al_paths import resolve_path, resolve_module_output
    except ImportError:
        sys.path.insert(0, os.path.join(scripts_dir, "..", "..", "..", "..", "runtime", "scripts"))
        from al_paths import resolve_path, resolve_module_output

    full_path = resolve_path(args.module, args.personas) if args.module else args.personas
    if not full_path or not os.path.exists(full_path):
        print(json.dumps({"status": "error", "message": f"File not found: {args.personas}"}))
        sys.exit(1)

    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    personas = parse_personas(content)
    findings = validate_personas(personas)
    if findings:
        print(json.dumps({"status": "error", "message": "Personas validation failed", "findings": findings}))
        sys.exit(1)

    # Output dir: .al/output/{module}/roles/
    if args.module:
        output_dir = os.path.join(resolve_module_output(args.module), "roles")
    else:
        output_dir = args.output_dir or "roles"
    os.makedirs(output_dir, exist_ok=True)
    created = []

    for persona in personas:
        role_content, slug = persona_to_role(persona)
        path = os.path.join(output_dir, f"{slug}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(role_content)
        created.append({"name": persona["name"], "slug": slug, "path": path})

    print(json.dumps({"status": "ok", "created": created, "count": len(created)}))


# --- Role enrichment ---

def _resolve_paths(module):
    """Resolve al_paths imports and return (resolve_path, resolve_module_output)."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    for rel in [
        os.path.join(scripts_dir, "..", "..", "..", "runtime", "scripts"),
        os.path.join(scripts_dir, "..", "..", "..", "..", "runtime", "scripts"),
    ]:
        sys.path.insert(0, rel)
        try:
            from al_paths import resolve_path, resolve_module_output
            return resolve_path, resolve_module_output
        except ImportError:
            continue
    print(json.dumps({"status": "error", "message": "Cannot import al_paths"}))
    sys.exit(2)


def _section_replace(content, section_name, new_content):
    """Replace or append a named section in markdown content."""
    section_heading = f"## {section_name}"
    section_pattern = rf'^## {re.escape(section_name)}\s*$'
    lines = content.split("\n")
    new_lines = []
    in_old = False
    replaced = False
    for line in lines:
        if re.match(section_pattern, line, re.MULTILINE):
            in_old = True
            replaced = True
            new_lines.append(section_heading)
            new_lines.append("")
            new_lines.append(new_content.strip())
            new_lines.append("")
            continue
        if in_old:
            if line.startswith("## "):
                in_old = False
                new_lines.append(line)
            continue
        new_lines.append(line)
    if not replaced:
        new_lines.extend(["", section_heading, "", new_content.strip(), ""])
    return "\n".join(new_lines)


def _update_role(output_dir, slug, section, content):
    """Write a section to a role file via append/replace."""
    path = os.path.join(output_dir, "roles", f"{slug}.md")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        existing = f.read()
    new_content = _section_replace(existing, section, content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return path


def _discover_slugs(output_dir):
    """Discover all dynamic role slugs from the roles/ directory."""
    roles_dir = os.path.join(output_dir, "roles")
    if not os.path.isdir(roles_dir):
        return []
    return [f[:-3] for f in sorted(os.listdir(roles_dir)) if f.endswith(".md")]


def _slug_from_name(name, slugs):
    """Match a persona name to a known slug."""
    candidate = slugify(name)
    if candidate in slugs:
        return candidate
    # Fuzzy: check if the slug is contained in or contains the candidate
    for s in slugs:
        if s in candidate or candidate in s:
            return s
    return None


def _parse_personas_field(text):
    """Extract persona names from a **Personas:** field value."""
    return [n.strip() for n in text.split(",") if n.strip()]


def _extract_interviews(output_dir, slugs):
    """Extract Key Insights section from each interview-{slug}.md."""
    results = {}
    empathize_dir = os.path.join(output_dir, "01-empathize")
    if not os.path.isdir(empathize_dir):
        return results
    for slug in slugs:
        path = os.path.join(empathize_dir, f"interview-{slug}.md")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Extract ## Key Insights section
        match = re.search(r'^## Key Insights.*?\n(.*?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if match:
            results[slug] = match.group(1).strip()
    return results


def _extract_empathy_maps(output_dir, slugs):
    """Extract per-persona sections from empathy-maps.md."""
    results = {}
    path = os.path.join(output_dir, "01-empathize", "empathy-maps.md")
    if not os.path.exists(path):
        return results
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # Split by ## headings
    sections = re.split(r'^## ', content, flags=re.MULTILINE)
    for section in sections[1:]:  # skip content before first ##
        first_line = section.split("\n", 1)[0]
        # Match persona name from the heading
        for slug in slugs:
            # Try matching the slug against the heading (lowercased, hyphenated)
            heading_slug = slugify(first_line.split("—")[0].strip())
            if heading_slug == slug or slug in heading_slug:
                results[slug] = section.strip()
                break
    return results


def _extract_by_personas_field(content, slugs, heading_pattern):
    """Extract entries that have a **Personas:** field, grouped by slug."""
    results = {s: [] for s in slugs}
    # Split into entries by heading pattern
    entries = re.split(heading_pattern, content, flags=re.MULTILINE)
    # entries[0] is preamble, then alternating: heading-capture, body
    for i in range(1, len(entries), 2):
        heading = entries[i].strip() if i < len(entries) else ""
        body = entries[i + 1] if i + 1 < len(entries) else ""
        full_entry = f"{heading}\n{body}"
        # Find **Personas:** field
        match = re.search(r'\*\*Personas:\*\*\s*(.+)', full_entry)
        if not match:
            continue
        names = _parse_personas_field(match.group(1))
        for name in names:
            slug = _slug_from_name(name, slugs)
            if slug:
                results[slug].append(full_entry.strip())
    return results


def _extract_insights(output_dir, slugs):
    """Extract insights per persona from insights.md."""
    path = os.path.join(output_dir, "02-define", "insights.md")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    grouped = _extract_by_personas_field(content, slugs, r'^## Insight:\s+(.+)$')
    return {s: "\n\n".join(entries) for s, entries in grouped.items() if entries}


def _extract_user_flows(output_dir, slugs):
    """Extract user flows per persona from user-flows.md."""
    path = os.path.join(output_dir, "04-prototype", "user-flows.md")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    grouped = _extract_by_personas_field(content, slugs, r'^## (.+)$')
    return {s: "\n\n".join(entries) for s, entries in grouped.items() if entries}


def _normalize_req_headings(text):
    """Convert bold-format requirements (**FR-X.X: Title**) to ### headings."""
    return re.sub(r'^\*\*(FR-[\w.]+[\s:—–-]+.+?)\*\*', r'### \1', text, flags=re.MULTILINE)


def _extract_requirements(output_dir, slugs):
    """Extract requirements per persona from requirements.md."""
    path = os.path.join(output_dir, "04-prototype", "requirements.md")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # Split on individual requirement entries (**FR-X.X** ...) rather than
    # group headings, since each FR has its own **Personas:** field.
    grouped = _extract_by_personas_field(content, slugs, r'^(\*\*FR-[\w.]+\*\*.*)')
    if not any(grouped.values()):
        # Fall back to ### headings then ## headings
        grouped = _extract_by_personas_field(content, slugs, r'^(?=###\s+)')
        if not any(grouped.values()):
            grouped = _extract_by_personas_field(content, slugs, r'^## (.+)$')
    # Normalize bold-format requirements to ### headings for consistency
    return {s: _normalize_req_headings("\n\n".join(entries)) for s, entries in grouped.items() if entries}


SOURCES = {
    "interviews":   ("Interview Insights",   _extract_interviews),
    "empathy-maps": ("Empathy Map",          _extract_empathy_maps),
    "insights":     ("Validated Insights",   _extract_insights),
    "user-flows":   ("User Flows",           _extract_user_flows),
    "requirements": ("Requirements",         _extract_requirements),
}


def cmd_enrich_role(args):
    """Enrich dynamic role files with data from a specific artifact source."""
    resolve_path, resolve_module_output = _resolve_paths(args.module)
    output_dir = resolve_module_output(args.module)
    if not output_dir:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)

    source = args.source
    if source not in SOURCES:
        print(json.dumps({"status": "error", "message": f"Unknown source '{source}'. Valid: {', '.join(SOURCES.keys())}"}))
        sys.exit(1)

    section_name, extract_fn = SOURCES[source]
    slugs = _discover_slugs(output_dir)
    if not slugs:
        print(json.dumps({"status": "error", "message": "No dynamic roles found in roles/"}))
        sys.exit(1)

    extracted = extract_fn(output_dir, slugs)
    updated = []
    for slug in slugs:
        content = extracted.get(slug)
        if content:
            path = _update_role(output_dir, slug, section_name, content)
            if path:
                updated.append({"slug": slug, "section": section_name, "path": path})

    print(json.dumps({
        "status": "ok",
        "source": source,
        "section": section_name,
        "updated": updated,
        "skipped": [s for s in slugs if s not in extracted],
    }))


def main():
    parser = argparse.ArgumentParser(description="Design Thinking role operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate-personas", help="Validate personas format")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--personas", required=True, help="Module-relative path to personas.md")

    p = sub.add_parser("create-from-personas", help="Convert personas to role definitions")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--personas", required=True, help="Module-relative path to personas.md")
    p.add_argument("--output-dir", help="Override output directory (optional)")

    p = sub.add_parser("enrich-role", help="Enrich role files from a workflow artifact")
    p.add_argument("--module", required=True, help="Module name")
    p.add_argument("--source", required=True, choices=list(SOURCES.keys()),
                   help="Artifact source to extract from")

    args = parser.parse_args()
    commands = {
        "validate-personas": cmd_validate_personas,
        "create-from-personas": cmd_create_from_personas,
        "enrich-role": cmd_enrich_role,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
