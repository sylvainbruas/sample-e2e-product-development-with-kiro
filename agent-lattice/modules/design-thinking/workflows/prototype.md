# Prototype

## Purpose

Transform selected concepts into concrete requirements and user flows for implementation.

This phase transitions from exploration to implementation. Requirements must be concrete, testable, implementable. Do NOT generate spec files, technical architecture, or code.

## Prerequisites

`phases.ideate.status` must be `"completed"`. Read input artifacts listed in the phase definition (`module.json`).

## Workflow

### Step 1: Concept Scoping
**Role:** Product Manager (solo)
**May consult:** Engineer (feasibility)

For each selected concept: review scope, clarify MVP boundaries (must-have/nice-to-have/out-of-scope), identify feature groups (independently implementable where possible).

**GATE: Confirm feature breakdown.**

### Step 2: User Flows
**Role:** Designer (solo)

For each feature group: flow name, preconditions, numbered steps, success outcome, error scenarios, edge cases, and a `**Personas:**` field listing which synthetic users are actors in this flow.

Save to `{output}/04-prototype/user-flows.md` (type: `user-flows`).

Then enrich role files with user flows:
```bash
python3 {self}/scripts/al-dt-roles.py enrich-role \
  --module design-thinking --source user-flows
```

**INFO-GATE: "User flows complete."**

### Step 3: Requirements
**Role:** Product Manager (solo)

Structure:
- Project overview, target users, concepts being implemented
- Feature breakdown table (group, concept, description, priority)
- Functional requirements per group (FR-{group}.{number}) with user stories referencing actual personas, testable acceptance criteria, MoSCoW priority, and a `**Personas:**` field listing which synthetic users this requirement serves
- Non-functional requirements
- Out of scope, open questions, assumptions

Save to `{output}/04-prototype/requirements.md` (type: `requirements`).

Then enrich role files with requirements:
```bash
python3 {self}/scripts/al-dt-roles.py enrich-role \
  --module design-thinking --source requirements
```

**INFO-GATE: "Requirements drafted. Proceeding to review."**

### Step 4: Requirements Review
**Panel:**
- **Topic:** Requirements review
- **Reviewing:** `{output}/04-prototype/requirements.md`
- **Participants:**
  - Product Manager — focus: completeness and business alignment — challenges: any requirements vague or untestable? Scope realistic for MVP?
  - Engineer — focus: technical implementability — challenges: which requirements hide complexity? What's ambiguous to build?
  - Designer — focus: UX completeness — challenges: error states covered? Edge cases? User journey coherent?
- **Input:** `{output}/04-prototype/requirements.md`, `{output}/04-prototype/user-flows.md`

**GATE: Review team assessment. Revise, annotate, or proceed?**

### Step 5: Phase Summary
**Role:** None

Write `{output}/04-prototype/phase-summary.md` (type: `phase-summary`). Next: invoke `generate-specs` (see kiro/specs).
Update manifest to mark phase as completed (see `al-manifest.md`).

## Autoflow Defaults
- Concept Scoping: auto-confirm (one group per concept)
- Requirements Review: auto-annotate; panel runs internally

## Completion Criteria
1. Feature breakdown confirmed
2. `user-flows.md` exists
3. `requirements.md` reviewed
4. `phase-summary.md` exists
5. Manifest: `phases.prototype.status: "completed"`
