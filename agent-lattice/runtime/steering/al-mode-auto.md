# Agent Lattice — Auto Mode

## When to Use This

Load this when the user's entire message is exactly "auto" — complete the current step without waiting for confirmation.

## How It Works

Auto mode completes the current step with sensible defaults. The user is not removed from the loop — they can interrupt at any time. Auto mode removes the waiting, not the quality.

## Scope

`auto` completes the current step, including any active mode (panel, caucus, etc.). It stops at the next gate — the user is back in control.

Use when: you want to skip one confirmation and keep going.

## Activation

- The user's entire message is exactly "auto" — the keyword alone, not part of a longer message
- Always user-initiated — never inferred from previous sessions or workflows
- Each workflow starts in normal mode regardless of what happened before
- The user can interrupt at any time, which cancels auto mode

## Behavior

- At each decision point, state what was assumed (one line per assumption)
- Quality and depth of output are NOT reduced
- If a decision has no reasonable default and can't be inferred from context, stop and ask — don't guess
- Auto-exempt steps are always respected

## Auto-Exempt Steps

The manifest can declare specific steps as exempt from auto mode. If the user says "auto" during an exempt step:

> "Auto mode isn't available for this step — it requires your input at key decision points."

Mode exemptions are the workflow's responsibility — the manifest declares exemptions, the runtime enforces them. See `al-gates.md`.

## Assumption Log

When auto mode is active, the workflow summary includes an "Auto Mode Assumptions" section listing every assumption made and the default used at each decision point.

## Rules

- `auto` = current step only, stops at next gate
- Always user-initiated
- Never carries over from previous workflows or sessions
- The user can interrupt at any time
- Each assumption is logged for traceability
- Exempt steps are respected
- No reduction in output quality — only in waiting time
