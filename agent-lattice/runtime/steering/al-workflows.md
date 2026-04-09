# Agent Lattice — Workflows

## When to Use This

Load this when executing a workflow — starting a phase, resuming, transitioning between steps.

## When a Workflow Is Invoked

Determine current position and resume accordingly:

```bash
# 1. Check overall status
python3 {runtime}/scripts/al-manifest.py status --module {name}
# Returns: currentPhase, currentStep, per-phase statuses

# 2. If a manifest exists, check resume position for the target phase
python3 {runtime}/scripts/al-manifest.py resume --module {name} --phase {phase}
# Returns: start | resume (with step ID) | warn-completed
```

If no manifest exists, initialize first:
```bash
python3 {runtime}/scripts/al-manifest.py init \
  --module {name} --schema manifest-schema.json
```

## Step 0: Load Configuration

At workflow start (once per invocation, not per phase), load both runtime and module config:

```bash
python3 {runtime}/scripts/al-config.py get-all --runtime
python3 {runtime}/scripts/al-config.py get-all --module {module}
```

Hold both config objects in context for the duration of the workflow. These values drive conditional behavior in steps and modes.

If either call fails with "not initialized", run `init` first, then retry:

```bash
python3 {runtime}/scripts/al-config.py init --runtime
python3 {runtime}/scripts/al-config.py init --module {module}
```

See `al-config.md` for full config conventions.

## Before Starting a Phase

Validate prerequisites:
1. All prerequisite phases must have `status: "completed"` in the manifest
2. All prerequisite files must exist on disk
3. If anything is missing → STOP. Tell the user exactly what's missing. Do not proceed.

See `al-manifest.md` for how to validate and update the manifest.

## Step IDs

Step IDs are the kebab-case of the step name in the workflow heading. For example, `### Step 1: Extract Feature Groups` has step ID `extract-feature-groups`. Use the `steps` command to list valid IDs for a phase:

```bash
python3 {runtime}/scripts/al-manifest.py steps --module {name} --phase {phase}
```

## During Step Execution

- Update the manifest at every step transition (see `al-manifest.md`)
- Load role definitions only when the step that needs them is reached — not when the phase starts
- Load skill protocols only when the step references them
- Save artifacts to the declared output paths (see `al-artifacts.md`)
- Hit the declared gate after producing output (see `al-gates.md`)
- Read only the specific prerequisite files listed — not "everything from the previous phase"

### Step Status Flow

| Gate Type | Status Flow |
|-----------|------------|
| GATE | `in_progress` → (wait for user) → `user_confirmed` → `completed` |
| SOFT-GATE | `in_progress` → (wait, easy continue) → `user_confirmed` → `completed` |
| INFO-GATE | `in_progress` → `completed` |
| none | `in_progress` → `completed` |

When a gated step is confirmed, record the confirmation and timestamp in the manifest. See `al-manifest.md` for the update interface.

## Ending a Phase

1. Write `phase-summary.md` containing:
   - What was accomplished
   - Key decisions made
   - Which roles participated and how
   - Files created with descriptions
   - Instructions for the next phase
2. Update the manifest to mark the phase as completed (see `al-manifest.md`)

## Document-as-Cache

Artifacts serve as persistent cache between sessions. The next phase reads previous phase outputs rather than re-deriving them. If a file is manually edited between sessions, the next phase picks up the edited version.

For artifact write conventions, see `al-artifacts.md`.

## Workflow File Constraints

- Workflow files must be self-contained. Do not reference other workflow files mid-execution.
- Role definitions must be loadable independently.
- Artifact reading must be explicit — the workflow lists exact file paths to read.
- Scripts are invoked on demand, never loaded into context.
