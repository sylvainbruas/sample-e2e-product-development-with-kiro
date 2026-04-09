"""
al_paths.py — Shared path resolution for Agent Lattice scripts.

Resolves module-relative paths to absolute paths within the .al/ directory structure.
"""

import os


def resolve_al_root():
    """Find the .al/ root directory. Scripts live at .al/runtime/scripts/."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # .al/runtime/scripts/ → .al/
    al_root = os.path.join(script_dir, "..", "..")
    al_root = os.path.normpath(al_root)
    if os.path.isdir(al_root) and os.path.basename(al_root) == ".al":
        return al_root
    # Fallback: search upward for .al/
    current = script_dir
    for _ in range(10):
        candidate = os.path.join(current, ".al")
        if os.path.isdir(candidate):
            return candidate
        current = os.path.dirname(current)
    return None


def resolve_module_output(module_name, al_root=None):
    """Resolve the output directory for a module: .al/output/{module}/"""
    if not al_root:
        al_root = resolve_al_root()
    if not al_root:
        return None
    return os.path.join(al_root, "output", module_name)


def resolve_module_dir(module_name, al_root=None):
    """Resolve the module directory: .al/modules/{module}/"""
    if not al_root:
        al_root = resolve_al_root()
    if not al_root:
        return None
    return os.path.join(al_root, "modules", module_name)


def resolve_path(module_name, relative_path, al_root=None):
    """Resolve a module-relative path to an absolute path in the output directory."""
    output_dir = resolve_module_output(module_name, al_root)
    if not output_dir:
        return None
    return os.path.join(output_dir, relative_path)
