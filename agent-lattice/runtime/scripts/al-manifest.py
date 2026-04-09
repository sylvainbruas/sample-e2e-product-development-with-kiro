#!/usr/bin/env python3
"""
al-manifest.py — Manifest operations for Agent Lattice.

All operations take --module. The manifest lives at .al/output/{module}/manifest.json.

Usage:
  al-manifest.py init --module MOD --schema SCHEMA_PATH
  al-manifest.py update-step --module MOD --phase ID --step ID --status STATUS
                             [--roles JSON] [--mode MODE] [--metadata JSON]
  al-manifest.py update-phase --module MOD --phase ID --status STATUS
  al-manifest.py check-prereqs --module MOD --phase ID
  al-manifest.py validate --module MOD --schema SCHEMA_PATH
  al-manifest.py resume --module MOD --phase ID
  al-manifest.py check-exempt --module MOD --phase ID --step ID --mode MODE
  al-manifest.py steps --module MOD --phase ID
  al-manifest.py status --module MOD

All commands output JSON to stdout. Non-zero exit on failure.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from al_paths import resolve_path, resolve_module_output, resolve_module_dir


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def manifest_path(module):
    output = resolve_module_output(module)
    if not output:
        print(json.dumps({"status": "error", "message": "Cannot resolve .al/ root"}))
        sys.exit(2)
    return os.path.join(output, "manifest.json")


def read_manifest(module):
    path = manifest_path(module)
    with open(path, encoding="utf-8") as f:
        return json.load(f), path


def write_manifest(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def cmd_init(args):
    path = manifest_path(args.module)
    # Schema can be absolute or relative to module dir
    schema_path = args.schema
    if not os.path.isabs(schema_path):
        mod_dir = resolve_module_dir(args.module)
        if mod_dir:
            schema_path = os.path.join(mod_dir, schema_path)
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    ts = now_iso()
    manifest = {
        "schema": "agent-lattice-v1",
        "module": args.module,
        "project": {"name": "", "created": ts, "lastUpdated": ts},
        "config": {"autoExemptSteps": []},
        "phases": {},
    }
    phase_ids = list(schema.get("properties", {}).get("phases", {}).get("properties", {}).keys())
    phases_schema = schema.get("properties", {}).get("phases", {}).get("properties", {})
    for pid in phase_ids:
        step_ids = list(phases_schema.get(pid, {}).get("properties", {}).get("steps", {}).get("properties", {}).keys())
        steps = {sid: {"status": "not_started"} for sid in step_ids}
        manifest["phases"][pid] = {
            "status": "not_started", "startedAt": None, "completedAt": None,
            "files": [], "prerequisites": {"phases": [], "files": []}, "steps": steps,
        }
    if phase_ids:
        manifest["phases"][phase_ids[0]]["status"] = "in_progress"
        manifest["phases"][phase_ids[0]]["startedAt"] = ts
    for i, pid in enumerate(phase_ids):
        if i > 0:
            manifest["phases"][pid]["prerequisites"]["phases"] = [phase_ids[i - 1]]
    write_manifest(path, manifest)
    print(json.dumps({"status": "ok", "path": path, "phases": phase_ids}))


def cmd_update_step(args):
    manifest, path = read_manifest(args.module)
    ts = now_iso()
    phase = manifest["phases"].get(args.phase)
    if not phase:
        print(json.dumps({"status": "error", "message": f"Phase '{args.phase}' not found"}))
        sys.exit(1)
    if "steps" not in phase:
        phase["steps"] = {}
    valid_keys = list(phase["steps"].keys())
    if valid_keys and args.step not in phase["steps"]:
        print(json.dumps({"status": "error",
                          "message": f"Unknown step '{args.step}' in phase '{args.phase}'. Valid steps: {valid_keys}"}))
        sys.exit(1)
    step = phase["steps"].get(args.step, {})
    step["status"] = args.status
    if args.status == "user_confirmed":
        step["confirmedAt"] = ts
    if args.roles:
        step["roles"] = json.loads(args.roles)
    if args.mode:
        step["mode"] = args.mode
    if args.metadata:
        step["metadata"] = json.loads(args.metadata)
    phase["steps"][args.step] = step
    manifest["project"]["lastUpdated"] = ts
    write_manifest(path, manifest)
    print(json.dumps({"status": "ok", "phase": args.phase, "step": args.step, "stepStatus": args.status}))


def cmd_update_phase(args):
    manifest, path = read_manifest(args.module)
    ts = now_iso()
    phase = manifest["phases"].get(args.phase)
    if not phase:
        print(json.dumps({"status": "error", "message": f"Phase '{args.phase}' not found"}))
        sys.exit(1)
    if args.status == "completed":
        incomplete = [k for k, v in phase.get("steps", {}).items()
                      if v.get("status") != "completed"]
        if incomplete:
            print(json.dumps({"status": "error",
                              "message": f"Cannot complete phase '{args.phase}': steps not completed: {incomplete}"}))
            sys.exit(1)
    phase["status"] = args.status
    if args.status == "in_progress" and not phase.get("startedAt"):
        phase["startedAt"] = ts
    if args.status == "completed":
        phase["completedAt"] = ts
    manifest["project"]["lastUpdated"] = ts
    write_manifest(path, manifest)
    print(json.dumps({"status": "ok", "phase": args.phase, "phaseStatus": args.status}))


def cmd_check_prereqs(args):
    manifest, _ = read_manifest(args.module)
    phase = manifest["phases"].get(args.phase)
    if not phase:
        print(json.dumps({"status": "error", "message": f"Phase '{args.phase}' not found"}))
        sys.exit(1)
    prereqs = phase.get("prerequisites", {})
    missing_phases = []
    missing_files = []
    for req_phase in prereqs.get("phases", []):
        p = manifest["phases"].get(req_phase, {})
        if p.get("status") != "completed":
            missing_phases.append(req_phase)
    for req_file in prereqs.get("files", []):
        full = resolve_path(args.module, req_file)
        if full and not os.path.exists(full):
            missing_files.append(req_file)
    if missing_phases or missing_files:
        print(json.dumps({"status": "fail", "missingPhases": missing_phases, "missingFiles": missing_files}))
        sys.exit(1)
    print(json.dumps({"status": "pass"}))


def cmd_validate(args):
    manifest, _ = read_manifest(args.module)
    schema_path = args.schema
    if not os.path.isabs(schema_path):
        mod_dir = resolve_module_dir(args.module)
        if mod_dir:
            schema_path = os.path.join(mod_dir, schema_path)
    try:
        import jsonschema
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=manifest, schema=schema)
        print(json.dumps({"status": "pass"}))
    except ImportError:
        print(json.dumps({"status": "error", "message": "jsonschema not installed"}))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"status": "fail", "message": str(e)}))
        sys.exit(1)


def cmd_resume(args):
    path = manifest_path(args.module)
    if not os.path.exists(path):
        print(json.dumps({"action": "init", "step": None, "message": "No manifest found. Initialize first."}))
        return
    manifest, _ = read_manifest(args.module)
    phase = manifest["phases"].get(args.phase)
    if not phase:
        print(json.dumps({"status": "error", "message": f"Phase '{args.phase}' not found"}))
        sys.exit(1)
    ps = phase.get("status", "not_started")
    if ps == "not_started":
        print(json.dumps({"action": "start", "step": None}))
    elif ps == "completed":
        print(json.dumps({"action": "warn-completed", "step": None}))
    else:
        for sid, sdata in phase.get("steps", {}).items():
            if sdata.get("status") != "completed":
                print(json.dumps({"action": "resume", "step": sid}))
                return
        print(json.dumps({"action": "start", "step": None}))


def cmd_check_exempt(args):
    manifest, _ = read_manifest(args.module)
    exempt = manifest.get("config", {}).get("autoExemptSteps", [])
    full_id = f"{args.phase}.{args.step}"
    is_exempt = full_id in exempt or args.step in exempt
    print(json.dumps({"exempt": is_exempt, "phase": args.phase, "step": args.step, "mode": args.mode}))


def cmd_steps(args):
    manifest, _ = read_manifest(args.module)
    phase = manifest["phases"].get(args.phase)
    if not phase:
        print(json.dumps({"status": "error", "message": f"Phase '{args.phase}' not found"}))
        sys.exit(1)
    steps = phase.get("steps", {})
    print(json.dumps({"status": "ok", "phase": args.phase, "steps": list(steps.keys())}))


def cmd_status(args):
    path = manifest_path(args.module)
    if not os.path.exists(path):
        print(json.dumps({"status": "ok", "module": args.module, "message": "No manifest. Not started."}))
        return
    manifest, _ = read_manifest(args.module)
    phases_status = {}
    current_phase = None
    current_step = None
    for pid, pdata in manifest.get("phases", {}).items():
        ps = pdata.get("status", "not_started")
        phases_status[pid] = ps
        if ps == "in_progress":
            current_phase = pid
            for sid, sdata in pdata.get("steps", {}).items():
                if sdata.get("status") != "completed":
                    current_step = sid
                    break
    print(json.dumps({"status": "ok", "module": args.module, "project": manifest.get("project", {}).get("name", ""), "currentPhase": current_phase, "currentStep": current_step, "phases": phases_status}))


def main():
    parser = argparse.ArgumentParser(description="Agent Lattice manifest operations")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init"); p.add_argument("--module", required=True); p.add_argument("--schema", required=True)
    p = sub.add_parser("update-step"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True); p.add_argument("--step", required=True); p.add_argument("--status", required=True); p.add_argument("--roles"); p.add_argument("--mode"); p.add_argument("--metadata")
    p = sub.add_parser("update-phase"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True); p.add_argument("--status", required=True)
    p = sub.add_parser("check-prereqs"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True)
    p = sub.add_parser("validate"); p.add_argument("--module", required=True); p.add_argument("--schema", required=True)
    p = sub.add_parser("resume"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True)
    p = sub.add_parser("check-exempt"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True); p.add_argument("--step", required=True); p.add_argument("--mode", required=True)
    p = sub.add_parser("steps"); p.add_argument("--module", required=True); p.add_argument("--phase", required=True)
    p = sub.add_parser("status"); p.add_argument("--module", required=True)

    args = parser.parse_args()
    cmds = {"init": cmd_init, "update-step": cmd_update_step, "update-phase": cmd_update_phase, "check-prereqs": cmd_check_prereqs, "validate": cmd_validate, "resume": cmd_resume, "check-exempt": cmd_check_exempt, "steps": cmd_steps, "status": cmd_status}
    cmds[args.command](args)


if __name__ == "__main__":
    main()
