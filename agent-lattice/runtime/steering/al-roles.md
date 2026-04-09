# Agent Lattice — Roles & Role-Play

## When to Use This

Load this when executing a step that involves roles, creating dynamic roles, or understanding role-play mechanics.

## What Roles Are

A role is a personality and expertise definition that the LLM adopts. When a workflow step says "Role: UX Researcher (solo)", the LLM reads the UX Researcher role definition and responds from that perspective.

There is no separate context, no separate session. The LLM reads the role file and role-plays. That's it.

## Role Definition Format

Role files are plain markdown. No frontmatter. The structure has two parts:

1. **Header block** — H1 display name + metadata lines (before the first `##`)
2. **Body sections** — module-defined `##` sections for LLM consumption

### Header Block (Runtime Contract)

Every role file must have:

```markdown
# {Display Name}

- **Type:** {role type}
- **Role:** {one-line description}
```

- **H1 heading** — the display name. Required.
- **Type** — the kind of role. Each module defines its types (e.g., `specialist`, `persona`, `archetype`). Required.
- **Role** — a one-line description of what this role does or who they are. Required.

These metadata lines live between H1 and the first `##`. They use the standard bold-key format (`- **Key:** value`).

### Body Sections (Module-Defined)

Everything after the header is `##` sections. The runtime does not prescribe which sections a role must have — that is the module's job, defined in the module's `schemas/role.json`.

Examples of module-defined sections:
- **Specialists** (designer module): `## Expertise`, `## Principles`, `## Skeptical of`
- **Personas** (design-thinking): `## Context` with demographics/goals/frustrations, plus enrichment sections added during the process
- **Archetypes** (working-backwards): `## Context` with JTBD/pain/values, plus enrichment sections added during the process

The runtime validates the header block. Module-specific section validation uses `al-roles.py validate --schema {path}`.

### Example: Specialist

```markdown
# UX Researcher

- **Type:** specialist
- **Role:** Drives user research methodology and persona validation

## Expertise
- User research methodology
- Persona development and validation

## Principles
- Never assume you know what users want
- Synthetic research is hypothesis generation, not ground truth

## Skeptical of
- Solutions proposed without user evidence
- Assumptions about user behavior based on team intuition
```

### Example: Persona (Dynamic)

```markdown
# Rachel Dominguez

- **Type:** persona
- **Role:** Senior Fund Controller at a mid-market PE firm

## Context
- **Age:** 38
- **Occupation:** Senior Fund Controller
- **Goals:**
  - Automate quarterly distribution calculations
  - Eliminate spreadsheet errors
- **Frustrations:**
  - Manual processes take days per fund
  - Vendor tools can't handle multi-class structures
- **Quote:** "I need penny-perfect accuracy, not pretty dashboards."

## Skeptical of
- Tools that prioritize UI over calculation accuracy
- Vendors who can't demonstrate multi-class LP support

## Interview Insights
(added during Empathize phase)

## Validated Insights
(added during Define phase)
```

## Role-Play Modes

Workflows assign roles to steps in a mode. The mode determines how the LLM uses the role definitions. When you encounter a mode in a workflow step, load the corresponding doc:

| Mode | Trigger in workflow | Doc |
|------|-------------------|-----|
| Solo | `**Role:** X (solo)` | (inline — just read the role and produce output) |
| Panel | `**Panel:**` block | `al-mode-panel.md` |
| Caucus | `**Caucus:**` block | `al-mode-caucus.md` |
| Interview | `**Interview:**` block | `al-mode-interview.md` |
| Collaborative | `**Roles (collaborative):**` | `al-mode-collaborative.md` |
| Consultation | `**May consult:**` | `al-mode-consultation.md` |
| None | No role declared | LLM works as itself |

Solo is simple enough to not need its own doc: read one role definition, adopt the identity, produce the step's output from that perspective.

## How to Role-Play

When a workflow step declares a role and input artifacts:

1. Read the role definition file (path provided by the workflow step)
2. Read the input artifacts (paths declared in the workflow step)
3. Internalize the role: adopt the identity defined in the file — expertise, principles, context, whatever sections the role has
4. Produce output from that role's perspective on those inputs — not as a neutral assistant, but as that character
5. When the role has "Skeptical of" entries, actively look for things to challenge in the inputs. This is permission and instruction to push back.
6. Reference specific content from the input artifacts, not generalities
7. Stay in character for the duration of the step (or exchange, in multi-role modes)

When switching between roles in multi-role modes:
- Each role's perspective must be distinct. If two roles say the same thing, one of them isn't adding value.
- Roles should disagree where their expertise leads to different conclusions. Don't smooth over tensions.
- The synthesis or final output acknowledges where roles diverged.

## Static vs Dynamic Roles

### Static Roles

Defined at module design time. They exist for the lifetime of the workflow.

Stored in the module's `roles/` folder. These are source files, not runtime artifacts.

### Dynamic Roles

Created at runtime by the workflow. Used when the workflow generates entities that should have a perspective: synthetic personas, customer archetypes, simulated users.

Dynamic roles use the same header format as static roles (H1 + metadata + body sections) and are written to the module's workspace output directory:

```
{output}/roles/{slug}.md
```

Workflows discover available dynamic roles by scanning this folder. The H1 heading provides the name. No manifest registration needed — the file system is the registry.

### Creating a Dynamic Role

A workflow step creates a dynamic role by:

1. Generating the role definition with H1 heading, metadata lines, and body sections
2. Writing it to `{output}/roles/{slug}.md` using `al-write.py write --type role` for structural validation

Quality requirements:
- H1 = display name, metadata must include `Type` and `Role`
- Body must have module-required sections (validated by module schema)
- No entry that is a single generic sentence (e.g., "Wants things to be better" — too shallow)

If the definition doesn't meet these, enrich it before writing. Shallow definitions produce shallow interactions.

### Enriching Dynamic Roles

Dynamic roles can be enriched during the workflow by appending sections. As the process progresses, new data (interview insights, validated findings, requirements) is added directly to the role file:

```bash
# Add or replace a section in the role file
python3 {runtime}/scripts/al-roles.py append-section \
  --module {name} --slug {slug} \
  --section "Interview Insights" << 'CONTENT_EOF'
{content}
CONTENT_EOF
```

This keeps everything about a role in one file. The module's schema declares which sections are required (present at creation) and which are optional (added during enrichment).

## Role Discovery

To find available roles:

1. **Static roles:** List files in the module's `roles/` folder. Every `.md` file is a role — discovery is by directory convention.
2. **Dynamic roles:** Scan `{output}/roles/` folder. Every `.md` file is a role.
3. **All roles:** Combine both lists.

Use the script: `{runtime}/scripts/al-roles.py discover --module {name}`

Note: the command is `discover`, not `list`.
