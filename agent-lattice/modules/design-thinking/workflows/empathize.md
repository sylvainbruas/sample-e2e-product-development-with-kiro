# Empathize

## Purpose

Ground the design thinking process in context. Gather information, generate synthetic personas, create them as dynamic roles, and conduct interviews.

## Prerequisites

None (first phase).

## Workflow

### Step 1: Context Discovery
**Role:** UX Researcher (solo)
**May consult:** Product Manager (business context), Market Researcher (competitive landscape)

UX Researcher leads a conversation to gather context in natural groupings:
- Team & Company: who, what business, team's role
- Goal: what triggered this, specific problem or open exploration
- Market & Users: target users, industry, competitors, known pain points
- Constraints: technical, budget, timeline, regulatory, success criteria

Product Manager contributes business framing when relevant. Market Researcher contributes competitive landscape.

Save to `{output}/01-empathize/context.md` (type: `context`).

**GATE: Confirm the context summary is accurate and complete.**

### Step 2: Persona Generation
**Role:** UX Researcher (solo)

Generate 3-5 synthetic personas grounded in Step 1 context, following the strict format defined in `{self}/steering/persona-format.md`. Each persona starts with `## Persona: {Full Name}` and uses the exact field structure specified.

Required fields per persona: Age, Occupation, Location, Goals (2+), Frustrations (2+), Behaviors (2+), Skeptical of (2+), Quote.

Save to `{output}/01-empathize/personas.md` (type: `persona`).

**GATE: Review personas. User may adjust, add, or remove.**

### Step 3: Dynamic Role Creation
**Role:** None (deterministic operation)

For each confirmed persona, create a dynamic role definition per `al-roles.md`.

Convert personas to role definitions using the module script:
```bash
python3 {self}/scripts/al-dt-roles.py validate-personas \
  --module design-thinking --personas 01-empathize/personas.md

python3 {self}/scripts/al-dt-roles.py create-from-personas \
  --module design-thinking --personas 01-empathize/personas.md
```

Then validate each generated role:
```bash
python3 {runtime}/scripts/al-roles.py validate \
  --module design-thinking --slug {slug}
```

If validation fails, enrich the definition before proceeding.

**INFO-GATE: "{N} synthetic user roles created: {names}. Starting interviews..."**

### Step 4: Interviews
**Interview:** UX Researcher interviews each synthetic user

For each dynamic role, conduct an interview per `skills/interview.md`.

Setup per interview:
- **Interviewer:** `roles/ux-researcher.md`
- **Subject:** `{output}/roles/{slug}.md`
- **Script:** Question themes from `skills/interview.md`
- **Output:** `{output}/01-empathize/interview-{slug}.md` (type: `interview`)

Each interview must surface 2-3 insights NOT in the persona definition.

After all interviews are complete, enrich role files with interview insights:
```bash
python3 {self}/scripts/al-dt-roles.py enrich-role \
  --module design-thinking --source interviews
```

**INFO-GATE: "Interviews complete. {total} key insights extracted."**

### Step 5: Empathy Maps
**Role:** UX Researcher (solo)

For each persona, create an empathy map with four quadrants:
- **Says** — quotes from interview (3-5 points)
- **Thinks** — inferred from behavior and context (3-5 points)
- **Does** — observed behaviors (3-5 points)
- **Feels** — emotions with explanation (3-5 points)

Save to `{output}/01-empathize/empathy-maps.md` (type: `empathy-map`).

After creating empathy maps, enrich role files with empathy data:
```bash
python3 {self}/scripts/al-dt-roles.py enrich-role \
  --module design-thinking --source empathy-maps
```

**INFO-GATE: "Empathy maps complete."**

### Step 6: Phase Summary
**Role:** None

Write `{output}/01-empathize/phase-summary.md` (type: `phase-summary`) containing:
- Key findings (top 5 insights across interviews)
- Personas created as dynamic roles
- Files created
- Next: invoke `define` workflow

Update manifest to mark phase as completed (see `al-manifest.md`).

## Autoflow Defaults
- Context Discovery: infer from workspace files (README, package.json, etc.)
- Persona Generation: auto-confirm
- Interviews: run internally, output artifact only
- Exempt steps: pause and resume (do not block the run)

## Completion Criteria
1. `context.md` confirmed
2. `personas.md` confirmed
3. Dynamic role files exist in `{output}/roles/` and pass validation
4. One `interview-{slug}.md` per dynamic role with key insights
5. `empathy-maps.md` exists
6. `phase-summary.md` exists
7. Manifest: `phases.empathize.status: "completed"`
