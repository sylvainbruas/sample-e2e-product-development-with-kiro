# Test

## Purpose

Prepare materials for real user testing. Does NOT simulate testing. No fake scores, no simulated results. Output is preparation materials for real testing with real users.

## Prerequisites

`phases.prototype.status` must be `"completed"`. Read input artifacts listed in the phase definition (`module.json`).

## Workflow

### Step 1: Test Planning Context
**Role:** UX Researcher (solo)

Gather from the user: development status, testing resources (participants, timeline, budget), testing environment (in-person/remote, tools), testing goals (what to validate, what decisions results inform).

**GATE: Do NOT proceed without testing context.**

### Step 2: Test Plan
**Role:** UX Researcher (solo)

Objectives, test types (usability, interviews, survey), participant recruitment (criteria, screening per persona segment), schedule, facilitator guide.

Save to `{output}/05-test/test-plan.md` (type: `test-plan`).

**INFO-GATE: "Test plan drafted."**

### Step 3: Questionnaires
**Role:** UX Researcher (solo)

Pre-test questionnaire, task scenarios (per user flow), post-task (SEQ), post-test (SUS + NPS), interview guide.

Save to `{output}/05-test/questionnaires.md` (type: `questionnaires`).

**INFO-GATE: "Questionnaires drafted."**

### Step 4: Metrics Framework
**Role:** UX Researcher (solo)

Usability metrics (task success, completion time, error rate, SEQ), satisfaction (SUS, NPS), business metrics, qualitative metrics. Each with formula and target.

Save to `{output}/05-test/metrics-framework.md` (type: `metrics-framework`).

**INFO-GATE: "Metrics framework drafted."**

### Step 5: Evaluation Rubric
**Role:** UX Researcher (solo)

Per-task thresholds, overall evaluation, issue severity classification, decision framework (Launch/Iterate/Rethink), reporting template.

Save to `{output}/05-test/evaluation-rubric.md` (type: `evaluation-rubric`).

**INFO-GATE: "Evaluation rubric drafted."**

### Step 6: Test Plan Review
**Panel:**
- **Topic:** Test plan review
- **Participants:**
  - UX Researcher — focus: methodological rigor — challenges: are we measuring the right things?
  - Product Manager — focus: priority alignment — challenges: testing what matters most to the business?
  - Designer — focus: UX coverage — challenges: testing flows where users most likely struggle?
- **Input:** `{output}/05-test/test-plan.md`, `{output}/05-test/questionnaires.md`, `{output}/05-test/metrics-framework.md`, `{output}/05-test/evaluation-rubric.md`

**SOFT-GATE: "Panel review complete. Any adjustments?"**

### Step 7: Phase Summary
**Role:** None

Write `{output}/05-test/phase-summary.md` (type: `phase-summary`). Design thinking process complete.
Update manifest to mark phase as completed (see `al-manifest.md`).

## Autoflow Defaults
- Test Planning Context: exempt — pauses autoflow/automagic until user provides context, then resumes
- Remaining steps: use defaults (5-8 participants, 2-week timeline, remote, standard tools)
- Test Plan Review: panel runs internally

## Completion Criteria
1. Testing context gathered
2. `test-plan.md` exists
3. `questionnaires.md` exists
4. `metrics-framework.md` exists
5. `evaluation-rubric.md` exists
6. Panel reviewed
7. `phase-summary.md` exists
8. Manifest: `phases.test.status: "completed"`
