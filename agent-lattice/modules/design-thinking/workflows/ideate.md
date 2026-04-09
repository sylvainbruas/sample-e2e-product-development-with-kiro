# Ideate

## Purpose

Generate solution ideas, evaluate them, and select concepts for prototyping.

## Prerequisites

`phases.define.status` must be `"completed"`. Read input artifacts listed in the phase definition (`module.json`).

## Workflow

### Step 1: Brainstorming Setup
**Role:** None (user interaction)

Confirm: which HMW questions (top 3-5), any changed constraints, ambition level (moonshot/feasible/mix).

**GATE: Confirm HMW selection, constraints, ambition level.**

### Step 2: Divergent Brainstorming
**Role:** Designer (solo)

For each selected HMW, generate ideas using:
- Direct ideation (5-8), analogous inspiration (3-5), constraint removal (3-5), worst possible idea reversed (2-3)

Each idea: name, description, HMW addressed, personas served, technique used.
Save to `{output}/03-ideate/brainstorm.md` (type: `brainstorm`).

**GATE: Which ideas excite you? Kill any? Spark new ones? Combine any?**

### Step 3: Concept Review
**Caucus:**
- **Topic:** Evaluating brainstormed ideas
- **Closer:** Product Manager
- **Participants:**
  - Designer — focus: user experience quality — challenges: which ideas sound good but would be confusing to use?
  - Engineer — focus: technical feasibility — challenges: which ideas hide exponential complexity? Real build cost?
  - Product Manager — focus: business alignment — challenges: which don't move the needle? Where's scope creep?
  - Market Researcher — focus: differentiation — challenges: which are undifferentiated? What do competitors already do better?
  - Dynamic roles (synthetic users, discovered per `al-roles.md`) — focus: would you actually use this? — challenges: which solve a problem you don't have? What's missing?
- **Input:** `{output}/03-ideate/brainstorm.md`

**GATE: Review team assessment. Adjust idea set.**

### Step 4: Evaluation Criteria
**Role:** Product Manager (solo)

Default criteria: User Impact (3x), Feasibility (3x), Alignment (2x), Novelty (1x), Risk inverse (1x).

**SOFT-GATE: "Default criteria. Adjust weights or add/remove?"**

After confirmation, save the criteria to `{output}/03-ideate/criteria.json` (type: `criteria`):
```json
{
  "criteria": [
    {"name": "User Impact", "weight": 3},
    {"name": "Feasibility", "weight": 3},
    {"name": "Alignment", "weight": 2},
    {"name": "Novelty", "weight": 1},
    {"name": "Risk inverse", "weight": 1}
  ]
}
```

### Step 5: Evaluation Matrix
**Role:** Product Manager (solo)

Score each idea 1-5 against confirmed criteria. The scores JSON must use the exact criterion name as the key.

Save to `{output}/03-ideate/scores.json` (type: `scores`):
```json
{
  "items": [
    {
      "name": "Idea Name",
      "scores": {
        "User Impact": 4,
        "Feasibility": 3,
        "Alignment": 5,
        "Novelty": 2,
        "Risk inverse": 4
      }
    }
  ]
}
```

Then run:
```bash
python3 {self}/scripts/al-dt-evaluate.py score \
  --module design-thinking \
  --scores 03-ideate/scores.json \
  --criteria 03-ideate/criteria.json \
  --output 03-ideate/evaluation-matrix.md
```

Present the ranked results to the user.

**INFO-GATE: "Evaluation matrix complete. Top ideas ranked."**

### Step 6: Concept Selection
**Panel:**
- **Topic:** Selecting concepts to move forward
- **Participants:**
  - Product Manager — focus: value vs scope — challenges: too many concepts? Is MVP clear?
  - Designer — focus: best user experience — challenges: sacrificing UX for feasibility? Concepts too fragmented?
  - Engineer — focus: buildable in reasonable timeframe — challenges: underestimating integration complexity? Technical risk?
  - Dynamic roles (synthetic users, discovered per `al-roles.md`) — focus: which would change your life? — challenges: would you switch from your current solution for this?
- **Input:** `{output}/03-ideate/evaluation-matrix.md`, `{output}/03-ideate/brainstorm.md`

Develop 2-5 concepts from top-ranked ideas. Each: name, elevator pitch, ideas included, target personas, value prop, HMW addressed, scope (in/out), open questions, risks.
Save to `{output}/03-ideate/selected-concepts.md` (type: `selected-concepts`).

**GATE: Select concepts to move forward. May merge, adjust scope, or drop.**

### Step 7: Phase Summary
**Role:** None

Write `{output}/03-ideate/phase-summary.md` (type: `phase-summary`). Next: invoke `prototype` workflow.
Update manifest to mark phase as completed (see `al-manifest.md`).

## Autoflow Defaults
- Brainstorming Setup: auto-select top 3-5 HMW
- Brainstorming: auto-confirm ideas
- Concept Review: caucus runs internally
- Evaluation Criteria: use defaults
- Concept Selection: auto-select top 2-3 concepts; panel runs internally

## Completion Criteria
1. HMW selection confirmed
2. `brainstorm.md` reviewed
3. Evaluation criteria confirmed
4. `evaluation-matrix.md` exists
5. `selected-concepts.md` confirmed
6. `phase-summary.md` exists
7. Manifest: `phases.ideate.status: "completed"`
