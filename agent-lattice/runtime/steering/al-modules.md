# Agent Lattice — Modules

## When to Use This

Load this when you need to discover installed modules or inspect module metadata.

## How Modules Work

Modules are plugins to the runtime. They live inside `.al/modules/` when installed. Each module is a folder with a `module.json` metadata file and a `MODULE.md` documentation entry point.

There are two types:
- **Runnable** — has its own workflow phases, manifest schema, output directory, and `install.json` for skill installation. The user interacts with it directly.
- **Service** — provides functions that runnable modules consume. No own workflow state, no manifest, no output directory. Not directly invoked by the user.

The `type` field in `module.json` declares which one it is.

Installed = available. If the folder exists, the module is there. No separate activation state.

## Script Interface

```bash
python3 {runtime}/scripts/al-modules.py inspect --all
python3 {runtime}/scripts/al-modules.py inspect --module {name}
```

## Path Conventions

| Prefix | Resolves to | Example |
|--------|------------|---------|
| `{runtime}/` | `.al/runtime/` | `{runtime}/scripts/al-manifest.py` |
| `{self}/` | `.al/modules/{current-module}/` | `{self}/scripts/al-dt-roles.py` |
| `{module:name}/` | `.al/modules/{name}/` | `{module:kiro}/workflows/create-spec.md` |
| `{output}/` | `.al/output/{current-module}/` | `{output}/manifest.json` |
| Bare filename | Sibling file in same folder | `al-manifest.md` |

## Module Metadata

Each module has a `module.json` file that contains runtime metadata:
- `name`, `description`, `type`, `prefix`
- `output` — output directory name (runnable only)
- `schema` — manifest schema filename (runnable only)
- `dependencies` — list of required modules
- `phases` — array of phase definitions with `id`, `order`, `workflow`, `prerequisites`, `output-dir`, `inputs` (runnable only)

Phase metadata (prerequisites, input files, output directories) lives in `module.json`, not in workflow files. Workflow files contain only the step-by-step execution instructions.

## How the Runtime Loads Modules

1. Runtime router (`RUNTIME.md`) is always loaded
2. When a workflow is invoked, discover modules via the script
3. Read the target module's `module.json` for metadata and phase definitions
4. Load the workflow file for step-by-step execution
5. Execute the workflow per runtime mechanics
