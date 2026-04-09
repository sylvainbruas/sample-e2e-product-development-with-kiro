# Agent Lattice — Autoflow Mode

## When to Use This

Load this when the user's entire message is exactly "autoflow" — complete the entire current workflow autonomously with minimal output.

## How It Works

Autoflow completes all remaining steps in the current workflow file. All gates are auto-confirmed. All multi-role interactions (caucus, panel, interview, collaborative, consultation) run internally — full deliberation happens, only the outcome informs the artifact. The user sees progress markers and file paths, nothing else.

## Scope

All remaining steps in the current workflow file. The workflow runs to completion, then stops. The next workflow starts in normal mode.

## Activation

- The user's entire message is exactly "autoflow" — the keyword alone, not part of a longer message
- Always user-initiated — never inferred from previous sessions or workflows
- Each workflow starts in normal mode regardless of what happened before
- The user can interrupt at any time, which cancels autoflow

## Behavior

### Gates
All GATEs and SOFT-GATEs become INFO-GATEs. No waiting.

### Multi-Role Interactions
Caucuses, panels, interviews, collaborative steps, and consultations all run internally:
- The LLM still reads all role definitions
- The LLM still generates the full deliberation (positions, challenges, concessions, resolution)
- The LLM still produces the same quality outcome
- But the deliberation is NOT shown in chat — the outcome informs the artifact directly

### Output to User
For each step, show exactly:
1. One-line progress: "Step {N}: {Name}"
2. File paths created or updated

Do NOT show:
- Gate questions or answers
- Outcomes or summaries of what happened
- Assumption logs
- Role-play dialogue, caucus rounds, panel perspectives, interview exchanges
- Solo role reasoning

### Quality
Output quality is NOT reduced. The reasoning still happens — it's just silent. Every artifact must meet the same format and depth requirements as normal mode.

## Auto-Exempt Steps

Exempt steps (declared in `config.autoExemptSteps`) are pause points. When autoflow reaches an exempt step:

1. Stop and present the gate to the user
2. Wait for the user's response
3. Resume autoflow for subsequent steps

Exempt steps are never skipped or blocked — they pause the mode.

## Rules

- `autoflow` = all remaining steps in the current workflow file, then stops
- The next workflow starts in normal mode
- Always user-initiated
- Never carries over from previous workflows or sessions
- The user can interrupt at any time
- Exempt steps pause, then resume
- No reduction in output quality — reduction in output verbosity only
- Errors and blockers are always surfaced
