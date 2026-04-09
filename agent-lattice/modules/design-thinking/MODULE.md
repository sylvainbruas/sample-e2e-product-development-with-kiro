# Design Thinking Module

A five-phase design thinking process: Empathize → Define → Ideate → Prototype → Test. Produces validated requirements and user flows, ready for spec generation.

## Roles

| Role | File | Expertise |
|------|------|-----------|
| UX Researcher | `roles/ux-researcher.md` | User research, personas, interviews, empathy mapping |
| Product Manager | `roles/product-manager.md` | Business alignment, scope, priorities, requirements |
| Designer | `roles/designer.md` | User experience, interaction design, information architecture |
| Engineer | `roles/engineer.md` | Technical feasibility, architecture, build cost |
| Market Researcher | `roles/market-researcher.md` | Competitive landscape, market trends, differentiation |

Dynamic roles (synthetic user personas) are created during the Empathize phase and written to `design-thinking/roles/`.

## Steering

| Doc | File | Purpose |
|-----|------|---------|
| Persona Format | `steering/persona-format.md` | Strict format for the personas artifact |

## Workflows

| Workflow | File | Roles Involved |
|----------|------|---------------|
| Empathize | `workflows/empathize.md` | UX Researcher (lead), PM + Market Researcher (consultation), dynamic personas |
| Define | `workflows/define.md` | UX Researcher, PM, Market Researcher, dynamic personas |
| Ideate | `workflows/ideate.md` | Designer (lead), all static + dynamic |
| Prototype | `workflows/prototype.md` | PM (lead), Designer + Engineer (consultation) |
| Test | `workflows/test.md` | UX Researcher (lead), PM + Designer (panel review) |
| Generate Specs | `workflows/generate-specs.md` | None (uses kiro module) |

## Skills

| Skill | File | Purpose |
|-------|------|---------|
| Interview | `skills/interview.md` | Prepared question script applied to a subject (role or user) |

## Scripts

| Script | File | Purpose |
|--------|------|---------|
| Role Creation | `scripts/al-dt-roles.py` | Convert personas to dynamic role definitions |
| Evaluation | `scripts/al-dt-evaluate.py` | Calculate weighted scores and rank ideas |

Also uses framework scripts: `al-manifest.py`, `al-roles.py`, `al-write.py`.
