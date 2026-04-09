# Generate Specs (Design Thinking)

## Purpose

Read the requirements from the Prototype phase and produce a structured spec plan using the kiro module's generate-specs function.

This is the DT-specific consumer of the kiro module's spec generation. It knows which artifacts to read and how to extract the information the kiro module needs.

## Prerequisites

`phases.prototype.status` must be `"completed"`. Read input artifacts listed in the phase definition (`module.json`).

## Workflow

This workflow delegates to the kiro module's `steering/generate-specs.md` with DT-specific source files.

Resolve the module's output directory:
```bash
python3 {runtime}/scripts/al-modules.py inspect --module design-thinking
```
Use the `output` field from the result as `{output}` below.

The spec plan is written to `{output}/spec-plan.json`.

Source files:
- **Requirements:** `{output}/04-prototype/requirements.md`
- **User flows:** `{output}/04-prototype/user-flows.md`
- **Personas:** `{output}/01-empathize/personas.md`

### Step 1: Extract Feature Groups
**Role:** None

Read the requirements document. Identify the feature groups and their requirement IDs. This is the input the kiro module needs to propose a spec breakdown.

**INFO-GATE: "Feature groups identified. Proceeding to spec breakdown."**

### Step 2: Spec Breakdown
**Role:** None

Using the feature groups from Step 1, propose a spec breakdown to the user (see `{module:kiro}/steering/generate-specs.md` Step 1 for the table format and guidelines).

After user confirms the breakdown, write the spec plan using the kiro module's script:

```bash
python3 {module:kiro}/scripts/al-kiro-specs.py init \
  --module design-thinking \
  --sources '{"requirements": "{output}/04-prototype/requirements.md", "userFlows": "{output}/04-prototype/user-flows.md", "personas": "{output}/01-empathize/personas.md"}'

python3 {module:kiro}/scripts/al-kiro-specs.py add-spec \
  --module design-thinking \
  --name "{Spec Name}" --slug "{slug}" \
  --description "{description}" \
  --feature-groups '["group-1"]' \
  --requirement-ids '["FR-1.1", "FR-1.2"]' \
  --priority P0
```

Repeat `add-spec` for each confirmed spec. Then validate:
```bash
python3 {module:kiro}/scripts/al-kiro-specs.py validate --module design-thinking
```

**GATE: Confirm or adjust the spec breakdown.**

### Step 3: Summary
**Role:** None

```
Spec plan created at {output}/spec-plan.json.

Next: Use create-spec {slug} to create each spec individually.
```

## Autoflow Defaults
- Extract Feature Groups: auto-confirm
- Spec Breakdown: auto-confirm; breakdown decided internally based on feature groups and requirements

## Completion Criteria

1. `spec-plan.json` exists and passes validation
2. All specs have status "planned"
