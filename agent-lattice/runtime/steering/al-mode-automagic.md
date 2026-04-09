# Agent Lattice — Automagic Mode

## When to Use This

Load this when the user's entire message is exactly "automagic" — orchestrate the module lifecycle from its current position to completion.

## How It Works

Automagic executes all remaining phases of a module in order. Within each workflow, it behaves identically to autoflow: all gates auto-confirmed, all multi-role interactions internal, progress lines and file paths only.

The difference from autoflow is scope: autoflow covers one workflow, automagic covers all remaining phases in the module.

## Scope

All remaining phases in the module lifecycle, in order. After each workflow completes, automagic reads the manifest, checks prerequisites for the next phase, and continues.

## Activation

- The user's entire message is exactly "automagic" — the keyword alone, not part of a longer message
- Always user-initiated — never inferred from previous sessions

## Module Resolution

When the user says "automagic", determine which module to orchestrate:

1. **Ongoing process in context:** If the current session has an active workflow for a module (manifest loaded, steps in progress), automagic that module. No need to ask.
2. **Multiple active processes:** If the session has context about multiple modules, ask: "Which module? {list of active modules}"
3. **No context:** If there's no ongoing module process in the session, ask: "Which module do you want to run? Use `automagic {module-slug}`."

The user can also say `automagic {module-slug}` to be explicit — this is NOT a keyword-only activation (the slug is an argument). In this case, skip resolution and use the specified module.

## Orchestration Loop

```
1. Inspect module: python3 {runtime}/scripts/al-modules.py inspect --module {name}
2. Read module.json to get phase order
3. Read manifest: python3 {runtime}/scripts/al-manifest.py status --module {name}
4. For each phase (in order):
   a. Skip if status is "completed"
   b. Check prerequisites: python3 {runtime}/scripts/al-manifest.py check-prereqs --module {name} --phase {id}
   c. Resume position: python3 {runtime}/scripts/al-manifest.py resume --module {name} --phase {id}
   d. Load the workflow file
   e. Execute in autoflow behavior (all gates auto-confirmed, multi-role internal, progress + files only)
   f. At exempt steps: pause, present gate, wait for user, resume
   g. After workflow completes, update phase status and continue to next phase
5. When all phases are complete, report final status
```

## Behavior

Identical to autoflow within each workflow:

### Gates
All GATEs and SOFT-GATEs become INFO-GATEs. No waiting.

### Multi-Role Interactions
Run internally — full deliberation happens, only the outcome informs the artifact.

### Output to User
For each phase transition:
1. One-line: "Phase {N}: {Name}"

For each step within a phase:
1. One-line progress: "Step {N}: {Name}"
2. File paths created or updated

Do NOT show: gate questions, outcomes, summaries, role dialogue, caucus rounds.

### Quality
Same as autoflow — no reduction. Every artifact meets full format and depth requirements.

## Auto-Exempt Steps

Same as autoflow. Exempt steps (declared in `config.autoExemptSteps`) pause automagic:

1. Stop and present the gate to the user
2. Wait for the user's response
3. Resume automagic for subsequent steps and phases

Exempt steps are never skipped.

## Error Handling

- Prerequisites not met: report which prerequisites are missing, stop
- Workflow errors: surface the error, stop (user can say "automagic" again to resume)
- Blockers from internal deliberation: surface and stop

Automagic is re-entrant — saying "automagic" again picks up from the current manifest position.

## Rules

- `automagic` = all remaining phases in the module, in order
- Within each phase, behaves identically to autoflow
- Keyword-activated (like auto and autoflow)
- Re-entrant: safe to invoke multiple times, picks up from current position
- The user can interrupt at any time
- Exempt steps pause, then resume
- Errors and blockers are always surfaced
- No reduction in output quality
