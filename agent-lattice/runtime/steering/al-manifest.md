# Agent Lattice — Manifest Operations

## When to Use This

Load this when you need to create, update, validate, or query the manifest.

## Core Rule

All manifest mutations go through scripts. The LLM decides what transition to make. The script performs the JSON mutation.

All operations take `--module {name}`. The manifest lives at `.al/output/{module}/manifest.json`.

## Script Interface

```bash
# Init (schema is relative to module dir)
python3 {runtime}/scripts/al-manifest.py init \
  --module {name} --schema manifest-schema.json

# Update step
python3 {runtime}/scripts/al-manifest.py update-step \
  --module {name} --phase {id} --step {id} --status completed \
  [--roles '["Role"]'] [--mode solo] [--metadata JSON]

# Update phase
python3 {runtime}/scripts/al-manifest.py update-phase \
  --module {name} --phase {id} --status in_progress

# Validate prerequisites
python3 {runtime}/scripts/al-manifest.py check-prereqs \
  --module {name} --phase {id}

# Validate against schema
python3 {runtime}/scripts/al-manifest.py validate \
  --module {name} --schema manifest-schema.json

# Resume position
python3 {runtime}/scripts/al-manifest.py resume \
  --module {name} --phase {id}

# Check mode exemption
python3 {runtime}/scripts/al-manifest.py check-exempt \
  --module {name} --phase {id} --step {id} --mode {mode}

# List valid step IDs for a phase
python3 {runtime}/scripts/al-manifest.py steps \
  --module {name} --phase {id}

# Status
python3 {runtime}/scripts/al-manifest.py status --module {name}
```

## Operational Rules

### Creating a Manifest

Use the init command with the module's schema file. It sets all phases to `not_started` except the first (`in_progress`), creates timestamps, and builds the prerequisite chain.

### Updating Step Status

Status flow:
- Ungated: `not_started` → `in_progress` → `completed`
- Gated: `not_started` → `in_progress` → `user_confirmed` → `completed`

Record roles and mode per step.

### Resuming from Manifest

When a workflow is invoked, determine where to resume:

1. Call `status` to find the current phase:
   ```bash
   python3 {runtime}/scripts/al-manifest.py status --module {name}
   ```
   Returns `currentPhase` and `currentStep`. If no manifest exists, initialize first.

2. Call `resume` with the current phase to determine the action:
   ```bash
   python3 {runtime}/scripts/al-manifest.py resume \
     --module {name} --phase {currentPhase}
   ```
   Returns: `start` (phase not started), `resume` (with step ID to continue from), or `warn-completed` (phase already done).

## Schema

Each module provides a `manifest-schema.json`. The init command reads it to build the manifest structure. The validate command checks against it.

Base fields (framework-mandated):
- `schema` — `"agent-lattice-v1"`
- `module` — module name
- `project` — `{ name, created, lastUpdated }`
- `config` — `{ autoExemptSteps[] }`
- `phases.<id>` — `{ status, startedAt, completedAt, files[], prerequisites, steps }`
- `phases.<id>.steps.<id>` — `{ status, confirmedAt, gate, roles[], mode, metadata{} }`
