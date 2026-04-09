# Define

## Purpose

Synthesize research into clear problem definitions, actionable problem statements, and HMW questions.

## Prerequisites

`phases.empathize.status` must be `"completed"`. Read input artifacts listed in the phase definition (`module.json`).

## Workflow

### Step 1: Affinity Mapping
**Role:** UX Researcher (solo)

Extract all observations, pain points, quotes, behaviors, insights from empathy artifacts. Group into themes:
- Extract atomic data points with source attribution
- Cluster into natural groups
- Name each cluster
- Identify cross-cutting themes across personas

Save to `{output}/02-define/affinity-map.md` (type: `affinity-map`).

**GATE: Do these groupings make sense? Anything missing or miscategorized?**

### Step 2: Insight Validation
**Caucus:**
- **Topic:** Validating insights from affinity mapping
- **Reviewing:** `{output}/02-define/affinity-map.md`
- **Closer:** UX Researcher
- **Participants:**
  - UX Researcher — focus: evidence grounding — challenges: flag insights that are assumed rather than evidenced, challenge confirmation bias
  - Market Researcher — focus: market reality alignment — challenges: flag insights that ignore competitive context or market trends
  - Dynamic roles (synthetic users, discovered per `al-roles.md`) — focus: lived experience validation — challenges: push back on insights that don't ring true from your perspective
- **Input:** `{output}/02-define/affinity-map.md`, `{output}/01-empathize/interview-*.md`

Derive validated insights. Each: statement, evidence, implication, confidence (High/Medium/Low), personas (which synthetic users this insight relates to).

Format per insight:
```markdown
## Insight: {title}
- **Statement:** ...
- **Evidence:** ...
- **Implication:** ...
- **Confidence:** High/Medium/Low
- **Personas:** {Name 1}, {Name 2}
```

Save to `{output}/02-define/insights.md` (type: `insights`).

Then enrich role files with validated insights:
```bash
python3 {self}/scripts/al-dt-roles.py enrich-role \
  --module design-thinking --source insights
```

**GATE: Any insights to challenge? Anything from real-world experience that contradicts?**

### Step 3: Problem Statements
**Role:** Product Manager (solo)

Create POV statements: **[User]** needs **[need]** because **[insight]**.
Each: POV, linked insights, impact assessment, alignment with project goals.
3-7 statements, ranked by impact and alignment.

Save to `{output}/02-define/problem-statements.md` (type: `problem-statements`).

**INFO-GATE: "Problem statements generated."**

### Step 4: HMW Questions
**Panel:**
- **Topic:** How Might We questions
- **Participants:**
  - Product Manager — focus: business-aligned HMW questions — challenges: are any too broad to be actionable? Too narrow to inspire?
  - Designer — focus: experience-oriented reframes — challenges: do any imply a solution? Are we missing emotional needs?
  - Market Researcher — focus: differentiation angles — challenges: are we asking questions that lead to undifferentiated solutions?
  - UX Researcher — focus: user-evidence grounding — challenges: are these grounded in what we heard, or what we wish we heard?
- **Input:** `{output}/02-define/problem-statements.md`, `{output}/02-define/insights.md`

For each POV, 2-4 HMW questions at different scope levels (broad, narrow, reframed).
Save to `{output}/02-define/hmw-questions.md` (type: `hmw-questions`).

**GATE: Rank or select priority HMW questions. These drive Ideate.**

### Step 5: Phase Summary
**Role:** None

Write `{output}/02-define/phase-summary.md` (type: `phase-summary`). Next: invoke `ideate` workflow.
Update manifest to mark phase as completed (see `al-manifest.md`).

## Autoflow Defaults
- Affinity Mapping: auto-confirm groupings
- Insight Validation: auto-confirm insights; caucus runs internally
- HMW Questions: auto-select top HMW by cross-persona impact; panel runs internally

## Completion Criteria
1. `affinity-map.md` confirmed
2. `insights.md` validated via caucus and confirmed
3. `problem-statements.md` exists
4. `hmw-questions.md` ranked
5. `phase-summary.md` exists
6. Manifest: `phases.define.status: "completed"`
