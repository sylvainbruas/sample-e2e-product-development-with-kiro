#!/usr/bin/env python3
"""
Agent Lattice Installer

Install, uninstall, and manage AL runtime and modules.

Everything goes under .al/ in the target project:
  .al/runtime/    — runtime steering, scripts, skills
  .al/modules/    — installed modules
  .al/output/     — module output

Skills are installed to .kiro/skills/ for Kiro integration.
RUNTIME.md is installed to .kiro/steering/al-runtime.md.

Usage:
  installer.py install --target DIR [--modules MOD1,MOD2,...] [--all]
  installer.py uninstall --target DIR [--keep-output]
  installer.py list
"""

import argparse
import json
import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RUNTIME_SRC = os.path.join(SCRIPT_DIR, "runtime")
MODULES_SRC = os.path.join(SCRIPT_DIR, "modules")

# --- Discovery ---

def discover_available_modules():
    modules = []
    if not os.path.isdir(MODULES_SRC):
        return modules
    for name in sorted(os.listdir(MODULES_SRC)):
        mod_dir = os.path.join(MODULES_SRC, name)
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
            "dependencies": deps,
            "folder": name,
            "source": mod_dir,
        })
    return modules


def check_dependencies(selected_names, all_modules):
    all_available = {m["name"]: m for m in all_modules}
    issues = []
    for name in selected_names:
        mod = all_available.get(name)
        if not mod:
            issues.append({"module": name, "issue": "not found"})
            continue
        for dep in mod["dependencies"]:
            if dep not in selected_names:
                if dep in all_available:
                    issues.append({"module": name, "issue": f"depends on '{dep}' which is not selected", "dependency": dep, "available": True})
                else:
                    issues.append({"module": name, "issue": f"depends on '{dep}' which is not available", "dependency": dep, "available": False})
    return issues


def get_skill_names_from_install_json(install_json_path):
    """Read install.json and return list of skill names."""
    if not os.path.exists(install_json_path):
        return []
    with open(install_json_path, encoding="utf-8") as f:
        config = json.load(f)
    return [s["name"] for s in config.get("skills", [])]


# --- Config ---

def prompt_config(schema_path, label):
    """Read a config schema and prompt the user for values. Returns config dict."""
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    props = schema.get("properties", {})
    if not props:
        return None
    interactive = sys.stdin.isatty()
    config = {}
    if interactive:
        print(f"\n  Configuration for {label}:\n")
    for key, prop in props.items():
        ptype = prop.get("type", "string")
        default = prop.get("default")
        desc = prop.get("description", "")
        if not interactive:
            config[key] = default
            continue
        default_str = json.dumps(default) if isinstance(default, bool) else str(default) if default is not None else ""
        print(f"    {key}")
        print(f"    {desc}")
        raw = input(f"    ({ptype}) [{default_str}]: ").strip()
        if not raw:
            config[key] = default
        elif ptype == "boolean":
            config[key] = raw.lower() in ("true", "1", "yes")
        elif ptype == "integer":
            try:
                config[key] = int(raw)
            except ValueError:
                config[key] = default
        else:
            config[key] = raw
        print()
    return config


def write_config(config, config_path):
    """Write a config dict to a JSON file."""
    os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


# --- Install ---

def install_skills(install_json_path, source_label, target_kiro_skills):
    """Read install.json and generate Kiro SKILL.md wrappers. Returns count."""
    if not os.path.exists(install_json_path):
        return 0
    with open(install_json_path, encoding="utf-8") as f:
        config = json.load(f)
    count = 0
    for skill in config.get("skills", []):
        skill_name = skill["name"]
        skill_dst = os.path.join(target_kiro_skills, skill_name)
        os.makedirs(skill_dst, exist_ok=True)
        source = skill["source"]
        mod_ref = re.match(r'\{module:(\w[\w-]*)\}/(.+)', source)
        if mod_ref:
            source_path = os.path.join(".al", "modules", mod_ref.group(1), mod_ref.group(2))
        else:
            source_path = os.path.join(source_label, source)
        desc = skill.get("description", "")
        hint = skill.get("argument-hint", "")
        steering = skill.get("steering", [])
        if steering:
            lines = "\n".join(f"- `.al/runtime/steering/{s}`" for s in steering)
            steering_block = (
                f"Before starting, read these runtime steering docs:\n{lines}\n\n"
                "Load additional steering from `.al/runtime/steering/` as steps require them (roles, modes, config)."
            )
        else:
            steering_block = "For runtime mechanics, load docs from `.al/runtime/steering/` as needed."
        skill_md = f'---\nname: {skill_name}\ndescription: "{desc}"\nargument-hint: "{hint}"\n---\n\n# {skill_name}\n\nRead and follow the instructions at `{source_path}`.\n\n{steering_block}\n'
        with open(os.path.join(skill_dst, "SKILL.md"), "w", encoding="utf-8") as sf:
            sf.write(skill_md)
        count += 1
    return count


def install_runtime(target):
    al_dir = os.path.join(target, ".al")
    runtime_dst = os.path.join(al_dir, "runtime")
    if os.path.exists(runtime_dst):
        shutil.rmtree(runtime_dst)
    shutil.copytree(RUNTIME_SRC, runtime_dst)
    os.makedirs(os.path.join(al_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(al_dir, "tmp"), exist_ok=True)
    os.makedirs(os.path.join(al_dir, "modules"), exist_ok=True)

    # Install RUNTIME.md as .kiro/steering/al-runtime.md
    steering_dir = os.path.join(target, ".kiro", "steering")
    os.makedirs(steering_dir, exist_ok=True)
    shutil.copy2(os.path.join(RUNTIME_SRC, "RUNTIME.md"), os.path.join(steering_dir, "al-runtime.md"))

    # Install runtime skills
    kiro_skills = os.path.join(target, ".kiro", "skills")
    count = install_skills(os.path.join(RUNTIME_SRC, "install.json"), ".al/runtime", kiro_skills)
    if count:
        print(f"  Installed {count} runtime skill(s)")

    # Configure runtime
    runtime_config_path = os.path.join(al_dir, "config.json")
    if not os.path.exists(runtime_config_path):
        schema = os.path.join(RUNTIME_SRC, "config-schema.json")
        config = prompt_config(schema, "Runtime")
        if config is not None:
            write_config(config, runtime_config_path)
            print(f"  Runtime config written to .al/config.json")
    else:
        print(f"  Runtime config preserved (.al/config.json exists)")

    print(f"  Runtime installed to {al_dir}")


def install_module(mod, target):
    dst = os.path.join(target, ".al", "modules", mod["folder"])
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(mod["source"], dst)
    print(f"  Module '{mod['name']}' installed")

    kiro_skills = os.path.join(target, ".kiro", "skills")
    source_label = os.path.join(".al", "modules", mod["folder"])
    count = install_skills(os.path.join(dst, "install.json"), source_label, kiro_skills)
    if count:
        print(f"  Installed {count} skill(s) for '{mod['name']}'")

    mod_json = os.path.join(dst, "module.json")
    if os.path.exists(mod_json):
        with open(mod_json, encoding="utf-8") as f:
            meta = json.load(f)
        output_name = meta.get("output", "")
        if output_name and isinstance(output_name, str):
            os.makedirs(os.path.join(target, ".al", "output", output_name), exist_ok=True)
            os.makedirs(os.path.join(target, ".al", "tmp", output_name), exist_ok=True)

            # Configure module
            config_schema = os.path.join(dst, "config-schema.json")
            config_path = os.path.join(target, ".al", "output", output_name, "config.json")
            if os.path.exists(config_schema) and not os.path.exists(config_path):
                config = prompt_config(config_schema, mod["name"])
                if config is not None:
                    write_config(config, config_path)
                    print(f"  Module config written to .al/output/{output_name}/config.json")
            elif os.path.exists(config_path):
                print(f"  Module config preserved (.al/output/{output_name}/config.json exists)")


# --- Uninstall ---

def uninstall_skills(install_json_path, target_kiro_skills):
    """Remove Kiro skills listed in an install.json."""
    names = get_skill_names_from_install_json(install_json_path)
    removed = 0
    for name in names:
        skill_dir = os.path.join(target_kiro_skills, name)
        if os.path.exists(skill_dir):
            shutil.rmtree(skill_dir)
            removed += 1
    return removed


def uninstall(target, keep_output=False):
    al_dir = os.path.join(target, ".al")
    kiro_skills = os.path.join(target, ".kiro", "skills")
    kiro_steering = os.path.join(target, ".kiro", "steering")

    if not os.path.exists(al_dir):
        print("Nothing to uninstall — .al/ not found.")
        return

    # Remove runtime skills from .kiro/skills/
    runtime_install = os.path.join(al_dir, "runtime", "install.json")
    count = uninstall_skills(runtime_install, kiro_skills)
    if count:
        print(f"  Removed {count} runtime skill(s)")

    # Remove RUNTIME.md from .kiro/steering/
    runtime_steering = os.path.join(kiro_steering, "al-runtime.md")
    if os.path.exists(runtime_steering):
        os.remove(runtime_steering)
        print("  Removed .kiro/steering/al-runtime.md")

    # Remove module skills from .kiro/skills/
    modules_dir = os.path.join(al_dir, "modules")
    if os.path.isdir(modules_dir):
        for mod_name in sorted(os.listdir(modules_dir)):
            mod_install = os.path.join(modules_dir, mod_name, "install.json")
            count = uninstall_skills(mod_install, kiro_skills)
            if count:
                print(f"  Removed {count} skill(s) for '{mod_name}'")

    # Remove .al/runtime and .al/modules
    runtime_dir = os.path.join(al_dir, "runtime")
    if os.path.exists(runtime_dir):
        shutil.rmtree(runtime_dir)
        print("  Removed .al/runtime/")

    if os.path.exists(modules_dir):
        shutil.rmtree(modules_dir)
        print("  Removed .al/modules/")

    # Handle output and tmp
    output_dir = os.path.join(al_dir, "output")
    tmp_dir = os.path.join(al_dir, "tmp")
    if keep_output:
        if os.path.exists(output_dir):
            print(f"  Kept .al/output/ (use --all to remove)")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            print("  Removed .al/tmp/")
    else:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            print("  Removed .al/output/")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            print("  Removed .al/tmp/")

    # Remove .al/ if empty
    if os.path.exists(al_dir) and not os.listdir(al_dir):
        os.rmdir(al_dir)
        print("  Removed .al/")
    elif os.path.exists(al_dir) and keep_output:
        print(f"  .al/ kept (contains output)")

    # Clean up empty .kiro/ dirs
    if os.path.exists(kiro_steering) and not os.listdir(kiro_steering):
        os.rmdir(kiro_steering)
    if os.path.exists(kiro_skills) and not os.listdir(kiro_skills):
        os.rmdir(kiro_skills)
    kiro_dir = os.path.join(target, ".kiro")
    if os.path.exists(kiro_dir) and not os.listdir(kiro_dir):
        os.rmdir(kiro_dir)

    print("\nUninstall complete.")


# --- Interactive ---

def interactive_select(modules):
    print("\nAvailable modules:\n")
    for i, mod in enumerate(modules, 1):
        deps = f" (depends on: {', '.join(mod['dependencies'])})" if mod["dependencies"] else ""
        print(f"  {i}. {mod['name']} — {mod['description']}{deps}")
    print(f"\n  a. All modules")
    print(f"  q. Cancel\n")
    choice = input("Select modules (comma-separated numbers, 'a' for all, 'q' to cancel): ").strip()
    if choice.lower() == 'q':
        return []
    if choice.lower() == 'a':
        return [m["name"] for m in modules]
    selected = []
    for part in choice.split(","):
        try:
            idx = int(part.strip()) - 1
            if 0 <= idx < len(modules):
                selected.append(modules[idx]["name"])
        except ValueError:
            pass
    return selected


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Agent Lattice Installer")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("install", help="Install runtime and modules")
    p.add_argument("--target", required=True)
    p.add_argument("--modules", help="Comma-separated module names")
    p.add_argument("--all", action="store_true", help="Install all modules")

    p = sub.add_parser("uninstall", help="Uninstall runtime and modules")
    p.add_argument("--target", required=True)
    p.add_argument("--keep-output", action="store_true", help="Keep .al/output/")

    p = sub.add_parser("list", help="List available modules")

    args = parser.parse_args()

    if args.command == "list":
        available = discover_available_modules()
        print("\nAvailable modules:\n")
        for mod in available:
            deps = f" (depends on: {', '.join(mod['dependencies'])})" if mod["dependencies"] else ""
            print(f"  {mod['name']} — {mod['description']}{deps}")
        print()
        sys.exit(0)

    if args.command == "uninstall":
        target = os.path.abspath(args.target)
        if not os.path.isdir(target):
            print(f"Error: '{target}' does not exist")
            sys.exit(1)
        print(f"\nUninstalling Agent Lattice from {target}\n")
        uninstall(target, keep_output=args.keep_output)
        sys.exit(0)

    # Install
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        print(f"Error: '{target}' does not exist")
        sys.exit(1)

    available = discover_available_modules()

    if args.all:
        selected = [m["name"] for m in available]
    elif args.modules:
        selected = [m.strip() for m in args.modules.split(",")]
    else:
        selected = interactive_select(available)

    if not selected:
        print("No modules selected. Exiting.")
        sys.exit(0)

    issues = check_dependencies(selected, available)
    if issues:
        print("\nDependency issues:\n")
        for issue in issues:
            print(f"  {issue['module']}: {issue['issue']}")
            if issue.get("available"):
                print(f"    -> Add '{issue['dependency']}' to your selection")
        print()
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            sys.exit(1)

    print(f"\nInstalling Agent Lattice to {target}\n")
    print("Installing runtime...")
    install_runtime(target)

    available_by_name = {m["name"]: m for m in available}
    print(f"\nInstalling {len(selected)} module(s)...")
    for name in selected:
        mod = available_by_name.get(name)
        if mod:
            install_module(mod, target)
        else:
            print(f"  Warning: module '{name}' not found, skipping")

    print(f"\nDone. Agent Lattice installed with: {', '.join(selected)}")


if __name__ == "__main__":
    main()
