#!/usr/bin/env python3
"""
al-modules.py — Module operations for Agent Lattice.

Usage:
  al-modules.py inspect --all
  al-modules.py inspect --module {name}

All commands output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import sys


def default_modules_dir():
    """Find .al/modules/ relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Script is at .al/runtime/scripts/ → .al/modules/ is ../../modules/
    return os.path.join(script_dir, "..", "..", "modules")


def discover_modules(modules_dir):
    """Scan modules directory and read module.json metadata."""
    modules = []
    if not os.path.isdir(modules_dir):
        return modules

    for name in sorted(os.listdir(modules_dir)):
        mod_dir = os.path.join(modules_dir, name)
        mod_json = os.path.join(mod_dir, "module.json")
        if not os.path.isfile(mod_json):
            continue

        with open(mod_json, encoding="utf-8") as f:
            meta = json.load(f)
        deps = meta.get("dependencies", [])
        if isinstance(deps, str):
            deps = [deps]

        modules.append({
            "name": meta.get("name", name),
            "description": meta.get("description", ""),
            "prefix": meta.get("prefix", ""),
            "output": meta.get("output", ""),
            "schema": meta.get("schema", ""),
            "dependencies": deps,
            "path": os.path.normpath(mod_dir),
        })

    return modules


def enrich_with_health(modules):
    """Add dependency health fields to each module entry."""
    installed_names = {m["name"] for m in modules}
    for mod in modules:
        missing = [d for d in mod.get("dependencies", []) if d not in installed_names]
        mod["missingDeps"] = missing
        mod["healthy"] = len(missing) == 0
    return modules


def cmd_inspect(args):
    modules_dir = args.modules_dir or default_modules_dir()
    modules = enrich_with_health(discover_modules(modules_dir))

    if args.all:
        print(json.dumps({"status": "ok", "modules": modules, "count": len(modules)}))
    else:
        for mod in modules:
            if mod["name"] == args.module:
                print(json.dumps({"status": "ok", **mod}))
                return
        print(json.dumps({"status": "error", "message": f"Module '{args.module}' not found"}))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Agent Lattice module operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect", help="Inspect module metadata and dependency health")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Inspect all installed modules")
    group.add_argument("--module", help="Inspect a single module by name")
    p.add_argument("--modules-dir")

    args = parser.parse_args()
    {"inspect": cmd_inspect}[args.command](args)


if __name__ == "__main__":
    main()
