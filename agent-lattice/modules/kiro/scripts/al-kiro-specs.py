#!/usr/bin/env python3
"""
al-kiro-specs.py — Spec plan operations for the Kiro module.

All operations take --module. The spec plan lives at .al/output/{module}/spec-plan.json.

Usage:
  al-kiro-specs.py init --module MOD --sources JSON
  al-kiro-specs.py add-spec --module MOD --name NAME --slug SLUG
                            --description DESC --feature-groups JSON
                            --requirement-ids JSON --priority P0|P1|P2
  al-kiro-specs.py validate --module MOD
  al-kiro-specs.py list --module MOD [--filter created|pending]
  al-kiro-specs.py get --module MOD --slug SLUG

Status is detected from the filesystem: if specPath exists, the spec is created.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

# Resolve runtime scripts for shared utilities
scripts_dir = os.path.dirname(os.path.abspath(__file__))
for p in [
    os.path.join(scripts_dir, "..", "..", "..", "runtime", "scripts"),
    os.path.join(scripts_dir, "..", "..", "..", "..", "runtime", "scripts"),
]:
    if os.path.isdir(p):
        sys.path.insert(0, p)
        break

from al_paths import resolve_module_output


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def plan_path(module):
    output = resolve_module_output(module)
    if not output:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)
    return os.path.join(output, "spec-plan.json")


def read_plan(module):
    path = plan_path(module)
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def write_plan(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def spec_status(spec):
    return "created" if os.path.isdir(spec["specPath"]) else "pending"


SPEC_PLAN_SCHEMA = "spec-plan-v1"
VALID_PRIORITIES = ["P0", "P1", "P2"]


def cmd_init(args):
    path = plan_path(args.module)
    sources = json.loads(args.sources)
    plan = {
        "schema": SPEC_PLAN_SCHEMA,
        "module": args.module,
        "sourceFiles": sources,
        "specs": [],
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    write_plan(path, plan)
    print(json.dumps({"status": "ok", "path": path}))


def cmd_add_spec(args):
    plan, path = read_plan(args.module)
    existing = {s["slug"] for s in plan["specs"]}
    slug = args.slug or slugify(args.name)
    if slug in existing:
        print(json.dumps({"status": "error", "message": f"Slug '{slug}' already exists"}))
        sys.exit(1)
    if args.priority not in VALID_PRIORITIES:
        print(json.dumps({"status": "error", "message": f"Invalid priority. Use: {VALID_PRIORITIES}"}))
        sys.exit(1)
    spec = {
        "name": args.name, "slug": slug, "description": args.description,
        "featureGroups": json.loads(args.feature_groups),
        "requirementIds": json.loads(args.requirement_ids),
        "priority": args.priority, "specPath": f".kiro/specs/{slug}/",
    }
    plan["specs"].append(spec)
    plan["updatedAt"] = now_iso()
    write_plan(path, plan)
    print(json.dumps({"status": "ok", "slug": slug, "specPath": spec["specPath"]}))


def cmd_validate(args):
    plan, _ = read_plan(args.module)
    findings = []
    if plan.get("schema") != SPEC_PLAN_SCHEMA:
        findings.append({"severity": "critical", "issue": f"Schema mismatch"})
    if not plan.get("module"):
        findings.append({"severity": "critical", "issue": "Missing 'module'"})
    required = ["name", "slug", "description", "featureGroups", "requirementIds", "priority", "specPath"]
    for i, s in enumerate(plan.get("specs", [])):
        for f in required:
            if f not in s or not s[f]:
                findings.append({"severity": "high", "issue": f"Spec '{s.get('slug', '?')}': missing '{f}'"})
    status = "pass" if not findings else "fail"
    print(json.dumps({"script": "al-kiro-specs", "status": status, "findings": findings}))
    if findings:
        sys.exit(1)


def cmd_list(args):
    plan, _ = read_plan(args.module)
    specs = [{"detected_status": spec_status(s), **s} for s in plan.get("specs", [])]
    if args.filter:
        specs = [s for s in specs if s["detected_status"] == args.filter]
    print(json.dumps({"status": "ok", "specs": specs, "count": len(specs)}))


def cmd_get(args):
    plan, _ = read_plan(args.module)
    for s in plan.get("specs", []):
        if s["slug"] == args.slug:
            print(json.dumps({"status": "ok", "spec": {**s, "detected_status": spec_status(s)}, "sourceFiles": plan.get("sourceFiles", {})}))
            return
    print(json.dumps({"status": "error", "message": f"Slug '{args.slug}' not found", "available": [s["slug"] for s in plan.get("specs", [])]}))
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Kiro spec plan operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init"); p.add_argument("--module", required=True); p.add_argument("--sources", required=True)
    p = sub.add_parser("add-spec"); p.add_argument("--module", required=True); p.add_argument("--name", required=True); p.add_argument("--slug"); p.add_argument("--description", required=True); p.add_argument("--feature-groups", required=True); p.add_argument("--requirement-ids", required=True); p.add_argument("--priority", required=True)
    p = sub.add_parser("validate"); p.add_argument("--module", required=True)
    p = sub.add_parser("list"); p.add_argument("--module", required=True); p.add_argument("--filter")
    p = sub.add_parser("get"); p.add_argument("--module", required=True); p.add_argument("--slug", required=True)

    args = parser.parse_args()
    cmds = {"init": cmd_init, "add-spec": cmd_add_spec, "validate": cmd_validate, "list": cmd_list, "get": cmd_get}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
