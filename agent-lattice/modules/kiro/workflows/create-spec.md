---
phase: create-spec
order: 2
prerequisites: []
output-dir: ""
---

# Create Spec

## Purpose

Create a single Kiro spec from the spec plan. Takes one spec entry from `spec-plan.json`, gathers the relevant context from source files, and hands off to Kiro's spec-driven development system.

## Prerequisites

1. `spec-plan.json` must exist. If not → "No spec plan found. Run generate-specs first."
2. The requested slug must exist in the plan:
   ```bash
   python3 {self}/scripts/al-kiro-specs.py get --module {caller-module} --slug {slug}
   ```
   If not found, the script returns available slugs.
3. Source files referenced in `spec-plan.json` must be readable.

## Workflow

### Step 1: Show Spec Context
**Role:** None

Read the spec entry and display:
- Name and description from the plan
- Feature groups it maps to
- Requirement IDs it will implement
- Priority level
- Current status (should be "planned")

Check if the spec already exists at the `specPath`. If it does, warn the user.

**GATE: Confirm to proceed with this spec.**

### Step 2: Prepare Context
**Role:** None

Gather the relevant subset of ideation artifacts for this specific spec:

1. Extract the relevant requirements from the source requirements document — only the IDs listed in the spec entry
2. Extract relevant user flows related to this spec's requirements
3. Extract relevant personas referenced in user stories
4. Extract relevant non-functional requirements

The consumer module is responsible for knowing how to extract this information from its own artifacts. This step describes what to extract, not where from — the source file paths come from `spec-plan.json`.

**INFO-GATE: "Context prepared for {spec name}."**

### Step 3: Initiate Spec Session
**Role:** None

Hand off to Kiro's spec session. Frame the gathered context as:

```
Create a spec for "{spec name}" with the following context:

**Description:** {description from spec plan}

**Requirements to implement:**
{Full requirement text for each ID, including user story and acceptance criteria}

**Relevant user flows:**
{Related user flow descriptions}

**Personas:**
{Relevant persona summaries}

**Relevant non-functional requirements:**
{Applicable NFRs}

**Important:**
- User stories should reference the actual personas
- Acceptance criteria should trace back to requirement IDs (FR-x.x)
- Include relevant non-functional requirements where they apply
```

The spec session takes over from here — it creates the directory, `.config.kiro`, `requirements.md` in its own format, and manages its own workflow.

**INFO-GATE: "Spec session initiated for {spec name}. The spec session manages its own workflow from here."**

### Step 4: Update Status
**Role:** None (deterministic operation)

Once the spec session creates the requirements, verify it was created:
```bash
python3 {self}/scripts/al-kiro-specs.py get \
  --module {caller-module} \
  --slug {slug}
```

The `detected_status` field will show `created` if the spec directory exists.

**INFO-GATE: "Spec '{name}' created. Check remaining specs with list --filter pending."**

## Autoflow Defaults
- All gates are exempt — autoflow pauses at each gate for user input, then resumes

## Key Principles

- **Do NOT write requirements directly.** Gather context and hand off. The spec session owns the format.
- **One spec at a time.** Each invocation handles exactly one spec.
- **Context bridge.** Extract the right subset and present it.
- **Trace to source.** Pass requirement IDs for traceability.
- **User confirms via spec session.** The spec session has its own gates — don't duplicate them.
- **Script tracks status.** The spec-plan.json status field is updated via script, not hand-edited.

## What NOT to Do

- Do NOT create `.kiro/specs/{slug}/requirements.md` directly
- Do NOT create `.kiro/specs/{slug}/.config.kiro` — the spec session handles this
- Do NOT define a requirements format — the spec session has its own
- Do NOT bypass the spec session workflow
