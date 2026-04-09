# Agent Lattice — Gates

## When to Use This

Load this when handling gates in a workflow — decision points where the user confirms, adjusts, or is informed before the workflow continues.

## Gate Types

### GATE (Hard Stop)

The workflow stops. Present output and ask a specific question. Do NOT proceed until the user responds. The workflow waits indefinitely — there is no timeout, no fallback.

Use for: decisions that change workflow direction, outputs the user must validate, points where domain knowledge is essential.

### SOFT-GATE (Easy Continue)

Present output and ask "Want to adjust anything, or should I continue?" Affirmative responses (yes, continue, looks good, lgtm) proceed immediately.

Use for: outputs likely correct but user should have a chance to tweak.

### INFO-GATE (Auto-Continue)

Present output for awareness, then auto-continue. User can interrupt if needed.

Use for: progress updates, intermediate outputs that don't need approval.

## Declaring Gates

Gates are inline in step definitions within workflow files:

```markdown
### Step 2: {Name}

{... step instructions ...}

Save to `{output}/{phase}/{artifact}.md`.

**GATE: {Specific question to ask the user}**
```

## Mandatory Manifest Update

After every GATE or SOFT-GATE is confirmed — whether by user response, or auto-confirmed by autoflow/automagic — update the manifest for that step before proceeding to the next step. This applies even if the step produces no artifact. No step is complete until its manifest entry reflects the confirmation.

```bash
python3 {runtime}/scripts/al-manifest.py update-step \
  --module {name} --phase {phase} --step {step} --status completed
```

This is a universal rule. Workflow files do not need to repeat it at each gate.

## Mode Exemptions

The manifest can declare specific steps as exempt from auto modes via `config.autoExemptSteps`.

- **`auto`:** Exempt steps reject activation: "{Mode} isn't available for this step — it requires your input at key decision points."
- **`autoflow` / `automagic`:** Exempt steps are pause points. The workflow stops, presents the gate to the user, waits for their response, then resumes the active mode for subsequent steps. They are never skipped.

## Gates and Modes

Modes affect gates differently:

- **`auto`:** Complete the current step, then STOP at the gate. Present the gate output and wait for the user. The gate is NOT auto-confirmed.
- **`autoflow`:** All GATEs and SOFT-GATEs become INFO-GATEs. Multi-role interactions run internally. Output is progress lines and file paths only — no outcomes, no summaries.
- **`automagic`:** Same behavior as autoflow. The only difference is scope: autoflow covers one workflow, automagic covers the entire module lifecycle.

If the user said "auto" (not "autoflow" or "automagic"), the gate MUST stop and wait. Do NOT auto-confirm gates in auto mode.

**Mode activation:**
- `auto` — the user's full message is "auto" and nothing else
- `autoflow` — the user's full message is "autoflow" and nothing else
- `automagic` — the user's full message is "automagic" and nothing else (or "automagic {module-slug}" to be explicit)

If the keyword appears inside a longer message (e.g., "go ahead and autoflow this", "let's do auto"), it does NOT activate the mode. The user must send the keyword as a standalone message. No other user instruction — including "use your judgment", "do what makes sense", "drive the project", or any similar phrasing — changes gate behavior. A GATE is a hard stop regardless of how much autonomy the user grants elsewhere.
