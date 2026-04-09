#!/usr/bin/env python3
"""
al-config.py — Configuration operations for Agent Lattice.

Reads config from .al/config.json (runtime) or .al/output/{module}/config.json (module).
Schemas live at .al/runtime/config-schema.json or .al/modules/{module}/config-schema.json.

Usage:
  al-config.py init --runtime
  al-config.py init --module MOD
  al-config.py get --runtime --key KEY
  al-config.py get --module MOD --key KEY
  al-config.py get-all --runtime
  al-config.py get-all --module MOD
  al-config.py validate --runtime
  al-config.py validate --module MOD

All commands output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from al_paths import resolve_al_root, resolve_module_output, resolve_module_dir


def resolve_paths(args):
    """Resolve config and schema paths based on --runtime or --module."""
    al_root = resolve_al_root()
    if not al_root:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)
    if args.runtime:
        config_path = os.path.join(al_root, "config.json")
        schema_path = os.path.join(al_root, "runtime", "config-schema.json")
    else:
        config_path = os.path.join(resolve_module_output(args.module, al_root), "config.json")
        schema_path = os.path.join(resolve_module_dir(args.module, al_root), "config-schema.json")
    return config_path, schema_path


def read_schema(schema_path):
    """Read and return the config schema."""
    if not os.path.exists(schema_path):
        print(json.dumps({"status": "error", "message": f"Schema not found: {schema_path}"}))
        sys.exit(1)
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def defaults_from_schema(schema):
    """Extract default values from schema properties."""
    config = {}
    for key, prop in schema.get("properties", {}).items():
        if "default" in prop:
            config[key] = prop["default"]
    return config


def cmd_init(args):
    config_path, schema_path = resolve_paths(args)
    if os.path.exists(config_path):
        print(json.dumps({"status": "exists", "path": config_path}))
        return
    schema = read_schema(schema_path)
    config = defaults_from_schema(schema)
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print(json.dumps({"status": "created", "path": config_path}))


def cmd_get(args):
    config_path, schema_path = resolve_paths(args)
    schema = read_schema(schema_path)
    if args.key not in schema.get("properties", {}):
        print(json.dumps({"status": "error", "message": f"Key '{args.key}' not in schema"}))
        sys.exit(1)
    if not os.path.exists(config_path):
        print(json.dumps({"status": "error", "message": f"Config not initialized. Run: al-config.py init"}))
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    if args.key in config:
        print(json.dumps({"key": args.key, "value": config[args.key]}))
    else:
        default = schema["properties"][args.key].get("default")
        print(json.dumps({"key": args.key, "value": default, "source": "default"}))


def cmd_get_all(args):
    config_path, schema_path = resolve_paths(args)
    if not os.path.exists(config_path):
        # If schema has no properties, return empty config without requiring init
        schema = read_schema(schema_path)
        if not schema.get("properties"):
            print(json.dumps({"status": "ok", "config": {}}))
            return
        print(json.dumps({"status": "error", "message": "Config not initialized. Run: al-config.py init"}))
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    print(json.dumps({"status": "ok", "config": config}))


def cmd_validate(args):
    config_path, schema_path = resolve_paths(args)
    if not os.path.exists(config_path):
        print(json.dumps({"status": "error", "message": "Config not initialized"}))
        sys.exit(1)
    schema = read_schema(schema_path)
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    # Basic validation: check types and unknown keys
    errors = []
    props = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        for key in config:
            if key not in props:
                errors.append(f"Unknown key: '{key}'")
    for key, prop in props.items():
        if key in config:
            expected = prop.get("type")
            value = config[key]
            if expected == "boolean" and not isinstance(value, bool):
                errors.append(f"'{key}' must be boolean, got {type(value).__name__}")
            elif expected == "string" and not isinstance(value, str):
                errors.append(f"'{key}' must be string, got {type(value).__name__}")
            elif expected == "integer" and not isinstance(value, int):
                errors.append(f"'{key}' must be integer, got {type(value).__name__}")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}))
        sys.exit(1)
    print(json.dumps({"valid": True}))


def main():
    parser = argparse.ArgumentParser(description="Agent Lattice configuration operations")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ["init", "get", "get-all", "validate"]:
        p = sub.add_parser(name)
        scope = p.add_mutually_exclusive_group(required=True)
        scope.add_argument("--runtime", action="store_true")
        scope.add_argument("--module")
        if name == "get":
            p.add_argument("--key", required=True)

    args = parser.parse_args()
    cmds = {"init": cmd_init, "get": cmd_get, "get-all": cmd_get_all, "validate": cmd_validate}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
