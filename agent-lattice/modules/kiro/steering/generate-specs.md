# Generate Spec List

## Purpose

Produce a `spec-plan.json` from ideation artifacts. This is a function — consumer modules call it after their ideation workflow completes.

This workflow does NOT know where the artifacts come from. The consumer module provides the source file paths and the requirement/feature group structure. This workflow handles the spec breakdown, user confirmation, and plan file creation.

## Input Contract

The consumer module must provide:
- A requirements document with identifiable requirement IDs (e.g., FR-1.1, FR-1.2)
- Feature groups or logical groupings of requirements
- Priority information per group or requirement
- Source file paths (requirements, user flows, personas, etc.)

## Workflow

### Step 1: Propose Spec Breakdown
**Role:** None (user interaction)

Based on the feature groups in the requirements, propose how to split into individual specs:

| Spec Name | Slug | Feature Group(s) | Requirements | Priority | Description |
|-----------|------|-------------------|-------------|----------|-------------|
| {name} | {slug} | {groups} | FR-1.1, FR-1.2 | P0/P1/P2 | {what this spec delivers} |

Guidelines:
- Each spec should be a coherent, independently deliverable unit of work
- Prefer smaller, focused specs over large monolithic ones
- A spec should map to one or a small number of related feature groups
- Slug must be lowercase, hyphenated, suitable for a directory name

**GATE: Confirm or adjust the spec breakdown.**

### Step 2: Write Spec Plan
**Role:** None (deterministic operation)

Initialize the spec plan and add each confirmed spec using the script:

```bash
python3 {self}/scripts/al-kiro-specs.py init \
  --module {caller-module} \
  --sources '{"requirements": "...", "userFlows": "...", "personas": "..."}'

python3 {self}/scripts/al-kiro-specs.py add-spec \
  --module {caller-module} \
  --name "{Spec Name}" --slug "{slug}" \
  --description "{description}" \
  --feature-groups '["group-1"]' \
  --requirement-ids '["FR-1.1", "FR-1.2"]' \
  --priority P0
```

Repeat `add-spec` for each confirmed spec.

Validate the plan:
```bash
python3 {self}/scripts/al-kiro-specs.py validate --module {caller-module}
```

**INFO-GATE: "Spec plan created with {N} specs."**

### Step 3: Summary
**Role:** None

Present the plan:
```
Spec plan created with {N} specs:

1. {Spec Name 1} — {priority} — {description}
2. {Spec Name 2} — {priority} — {description}

Next: Use create-spec {slug} to create each spec individually.
```

## Key Principles

- **Plan only.** This produces a plan, not actual specs.
- **Module-agnostic.** Works with any ideation process that provides the input contract.
- **User controls the breakdown.** Confirmed before anything is written.
- **Small specs.** Prefer focused, independently deliverable specs.
- **Trace to source.** Every spec references its requirement IDs.
- **Script enforces format.** The spec plan is always created via `al-kiro-specs.py`, never hand-written.
