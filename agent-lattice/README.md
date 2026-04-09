# Agent Lattice (AL)

A document-driven framework for building structured, LLM-executed AI workflows. The LLM follows steering documents that define roles, workflows, modes, and gates. Scripts handle all deterministic operations. Modules are plugins that provide domain-specific processes.

Named **AL** — a nod to HAL 9000 from *2001: A Space Odyssey*.

---

## Table of Contents

- [Architecture](#architecture)
- [Core Concepts](#core-concepts)
  - [Roles](#roles)
  - [Workflows](#workflows)
  - [Gates](#gates)
  - [Modes](#modes)
  - [Scripts](#scripts)
  - [Artifacts](#artifacts)
- [Runtime](#runtime)
  - [Steering Router](#steering-router)
  - [Steering Documents](#steering-documents)
  - [Runtime Scripts](#runtime-scripts)
  - [Schemas](#schemas)
  - [Configuration](#configuration)
  - [Path Conventions](#path-conventions)
- [Modules](#modules)
  - [Module Types](#module-types)
  - [Module Structure](#module-structure)
  - [Design Thinking Module](#design-thinking-module)
  - [Kiro Module (Service)](#kiro-module-service)
- [Installer](#installer)
- [Design Principles](#design-principles)

---

## Architecture

### How It Works

1. `installer.py` copies the runtime and selected modules into a target project's `.al/` directory, and registers Kiro skills under `.kiro/skills/`
2. Kiro loads `al-runtime.md` (always-on steering) which acts as a router — telling the LLM which docs to load for any given task
3. When the user invokes a skill (e.g., `/al-dt-workflow-empathize`), the LLM reads the corresponding workflow file
4. The workflow defines a sequence of steps, each with a role to adopt, artifacts to produce, and a gate to hit
5. Scripts handle all file mutations — the LLM decides *what*, scripts do *how*
6. Artifacts accumulate in `.al/output/{module}/` as the workflow progresses
7. The Kiro module bridges ideation output to Kiro's native spec creation system

### Step Execution Flow

```
0. Load configuration (runtime + module) — once per workflow invocation
1. Read manifest → determine current position
2. Validate prerequisites
3. Load role definition (if step has one)
4. Execute step (produce artifacts)
5. Hit gate
6. Update manifest
7. Next step
```

### Source Layout

```
agent-lattice/
├── installer.py              # Install/uninstall CLI
├── runtime/
│   ├── RUNTIME.md            # Always-loaded steering router
│   ├── install.json          # Runtime skill definitions
│   ├── config-schema.json    # Runtime configuration schema
│   ├── steering/             # 17 steering documents
│   ├── schemas/              # Shared validation schemas
│   ├── scripts/              # Runtime scripts
│   └── skills/               # Runtime skills (impersonate)
└── modules/
    ├── design-thinking/      # Runnable: 5-phase design thinking
    └── kiro/                 # Service: spec generation bridge
```

### Installed Layout

```
project/
├── .kiro/
│   ├── steering/al-runtime.md    # Runtime router (always loaded by Kiro)
│   └── skills/                   # All installed Kiro skills
└── .al/
    ├── runtime/                  # Steering, scripts, schemas, skills
    ├── modules/                  # Installed modules
    ├── output/{module}/          # Artifacts, manifest, dynamic roles
    ├── tmp/{module}/             # Temporary files (auto-cleaned)
    └── config.json               # Runtime + module configuration
```

---

## Core Concepts

### Roles

Roles are personality and expertise definitions the LLM adopts. The LLM reads a role file and role-plays that identity — no separate session, no tool activation.

A role file is a markdown document starting with an H1 heading (the display name), followed by required sections:

- **Expertise** — at least 2 items describing domain knowledge
- **Principles** — at least 2 non-generic operating principles
- **Skeptical of** — at least 2 non-generic things this role pushes back on

**Static roles** ship with a module in `modules/{name}/roles/`. **Dynamic roles** (e.g., synthetic user personas) are created at runtime and written to `{output}/roles/`. Any `.md` file in a roles directory is a role — no registration needed.

Role files are living documents. As a workflow progresses, new sections (interview insights, empathy maps, requirements perspectives) are appended directly to the role file via `al-roles.py append-section`.

### Workflows

Workflows are step-by-step processes defined in markdown. Each step declares:

- A **role** to adopt (or multiple roles for a mode)
- A **gate** to hit when the step is complete
- What **artifacts** to produce

Phase metadata (order, prerequisites, output directories, input files) lives in `module.json`. Workflow files contain only execution instructions — no frontmatter.

### Gates

Decision points in workflows that control the pace of execution:

| Gate | Behavior |
|------|----------|
| **GATE** | Hard stop — user must respond before continuing |
| **SOFT-GATE** | Easy continue — "looks good?" prompt, defaults to proceed |
| **INFO-GATE** | Auto-continue — user can interrupt but doesn't have to |

Every non-final step in a workflow must end with a gate.

### Modes

Multi-role interactions are structured through modes, each with its own steering document:

| Mode | What happens |
|------|-------------|
| **Panel** | User + roles take turns interactively |
| **Caucus** | Roles deliberate among themselves; a closer summarizes the outcome |
| **Interview** | A prepared question script applied to a subject (another role or the user) |
| **Collaborative** | Roles contribute in order to build a shared artifact |
| **Consultation** | One role leads, pulls in others for focused input on specific questions |

All discussions happen in the chat. Artifacts receive only the summary or result.

Three commands enable unattended execution:

| Command | Scope |
|---------|-------|
| `auto` | Complete the current step, stop at the next gate |
| `autoflow` | Complete the entire current workflow, then stop |
| `automagic` | Complete the full module lifecycle with minimal output — multi-role interactions run internally, only outcomes are shown |

### Scripts

All deterministic operations go through Python scripts. Scripts accept `--module {name}` and resolve paths internally — callers never construct `.al/output/...` paths manually. Every script outputs JSON to stdout and uses non-zero exit codes on failure.

| Script | Purpose |
|--------|---------|
| `al-manifest.py` | Workflow state — init, update-step, update-phase, resume, status, steps |
| `al-write.py` | Artifact writing with schema validation, listing |
| `al-roles.py` | Role validation, discovery, section management, profile reading |
| `al-modules.py` | Installed module metadata — inspect --all / --module |
| `al-config.py` | Configuration init, read, and validate |

### Artifacts

Artifacts are markdown (or JSON) files produced by workflow steps. They are written through `al-write.py`, which validates content against type-specific schemas before writing.

```bash
python3 .al/runtime/scripts/al-write.py write \
  --module design-thinking \
  --path 01-empathize/context.md \
  --type context << 'CONTENT_EOF'
# Project Context
...
CONTENT_EOF
```

Schema resolution order: module schemas (`modules/{name}/schemas/`) first, then runtime schemas (`runtime/schemas/`).

---

## Runtime

### Steering Router

`RUNTIME.md` is the always-loaded document that acts as a routing table. When the LLM needs to do something, it looks up which steering document to load:

| Task | Steering document |
|------|------------------|
| Executing workflows (phases, steps, resume) | `al-workflows.md` |
| Manifest operations | `al-manifest.md` |
| Artifact operations | `al-artifacts.md` |
| Handling gates | `al-gates.md` |
| Role mechanics | `al-roles.md` |
| Module discovery | `al-modules.md` |
| Configuration | `al-config.md` |
| Panel mode | `al-mode-panel.md` |
| Caucus mode | `al-mode-caucus.md` |
| Interview mode | `al-mode-interview.md` |
| Collaborative mode | `al-mode-collaborative.md` |
| Consultation mode | `al-mode-consultation.md` |
| Auto mode | `al-mode-auto.md` |
| Autoflow mode | `al-mode-autoflow.md` |
| Automagic mode | `al-mode-automagic.md` |

This deferred-loading approach means the LLM only reads what it needs for the current task — keeping context lean.

### Steering Documents

The runtime ships 17 steering documents organized by concern:

**Workflow execution:** `al-workflows.md`, `al-manifest.md`, `al-artifacts.md`, `al-gates.md`

**Role system:** `al-roles.md`

**Module system:** `al-modules.md`, `al-config.md`

**Multi-role modes:** `al-mode-panel.md`, `al-mode-caucus.md`, `al-mode-interview.md`, `al-mode-collaborative.md`, `al-mode-consultation.md`

**Automation modes:** `al-mode-auto.md`, `al-mode-autoflow.md`, `al-mode-automagic.md`

### Runtime Scripts

| Script | Commands | Description |
|--------|----------|-------------|
| `al-manifest.py` | `init`, `update-step`, `update-phase`, `check-prereqs`, `validate`, `resume`, `check-exempt`, `steps`, `status` | The manifest is the single source of truth for workflow state |
| `al-write.py` | `write`, `schema`, `list` | Write artifacts with structural validation against named schemas |
| `al-roles.py` | `validate`, `discover`, `append-section`, `read-profile` | Role file CRUD — validate format, discover available roles, enrich with new sections |
| `al-modules.py` | `inspect` (`--all` / `--module`) | Read module metadata, check dependency health |
| `al-config.py` | `init`, `get`, `get-all`, `validate` | Read/write runtime and module configuration |
| `al_paths.py` | *(library)* | Shared path resolution — finds `.al/` root by walking up, resolves path prefixes |

### Schemas

The runtime provides four shared validation schemas:

| Schema | Validates |
|--------|----------|
| `role.json` | Role files — requires H1, Expertise (2+), Principles (2+), Skeptical of (2+) |
| `context.json` | Context artifacts — requires H1, minimum 300 characters |
| `phase-summary.json` | Phase summaries — min 200 chars, requires What Was Accomplished, Key Decisions, Files Created |
| `generic.json` | Minimal validation fallback |

Modules extend these with their own schemas (e.g., `persona.json`, `requirements.json`, `user-flows.json`).

### Configuration

Runtime configuration is defined in `config-schema.json`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `projectName` | string | — | Display name for the project |
| `showRoleInteractions` | boolean | `true` | Show multi-role deliberations in chat, or only outcomes |

Modules can define their own config schemas. All configuration is merged into `.al/config.json` at install time.

### Path Conventions

Steering documents and workflows use path prefixes that resolve at runtime:

| Prefix | Resolves to |
|--------|------------|
| `{runtime}/` | `.al/runtime/` |
| `{self}/` | `.al/modules/{current-module}/` |
| `{module:name}/` | `.al/modules/{name}/` |
| `{output}/` | `.al/output/{current-module}/` |
| Bare filename | Sibling file in same directory |

---

## Modules

### Module Types

- **Runnable** — has workflows, roles, manifest schema, output directory, and `install.json`. The user interacts with it directly through skills.
- **Service** — provides functions that other modules consume. No own workflow state or output directory.

### Module Structure

```
modules/{name}/
├── module.json              # Metadata: name, type, prefix, output dir, phases, dependencies
├── MODULE.md                # Documentation
├── manifest-schema.json     # Manifest schema (runnable only)
├── install.json             # Skills to register in .kiro/skills/ (runnable only)
├── roles/                   # Role definition files
├── workflows/               # Step-by-step process files
├── skills/                  # Shared protocols referenced by workflows
├── steering/                # Module-specific guidance and contracts
├── schemas/                 # Validation schemas for module-specific artifact types
└── scripts/                 # Module-specific deterministic operations
```

### Design Thinking Module

**Type:** Runnable | **Prefix:** `dt` | **Output:** `design-thinking/` | **Depends on:** `kiro`

A five-phase design thinking process that takes a product idea from empathy research through validated, traceable requirements.

#### Phases

| # | Phase | Workflow | Lead Role | Key Output |
|---|-------|----------|-----------|------------|
| 1 | **Empathize** | `empathize.md` | UX Researcher | Context, synthetic personas, interviews, empathy maps |
| 2 | **Define** | `define.md` | UX Researcher | Affinity map, insights, problem statements, HMW questions |
| 3 | **Ideate** | `ideate.md` | Designer | Brainstorm, evaluation matrix, selected concepts |
| 4 | **Prototype** | `prototype.md` | Product Manager | User flows, requirements (FR-x.x with traceability) |
| 5 | **Test** | `test.md` | UX Researcher | Test plan, questionnaires, metrics framework |
| 6 | **Generate Specs** | `generate-specs.md` | *(via kiro module)* | `spec-plan.json` with spec breakdown |

After Generate Specs, individual specs are created with `/al-dt-workflow-create-spec {slug}`, which delegates to the Kiro module.

#### Roles

Five static roles ship with the module:

| Role | File | Focus |
|------|------|-------|
| UX Researcher | `ux-researcher.md` | User research, personas, interviews, empathy mapping |
| Product Manager | `product-manager.md` | Business alignment, scope, priorities, requirements |
| Designer | `designer.md` | User experience, interaction design, information architecture |
| Engineer | `engineer.md` | Technical feasibility, architecture, build cost |
| Market Researcher | `market-researcher.md` | Competitive landscape, market trends, differentiation |

**Dynamic roles** are created during the Empathize phase. The workflow generates 3-5 synthetic user personas, then `al-dt-roles.py create-from-personas` converts each one into a full role file. These personas participate in interviews, caucuses, and reviews throughout subsequent phases.

#### Multi-Role Interactions by Phase

- **Empathize:** UX Researcher interviews each persona (interview mode), consults PM + Market Researcher
- **Define:** Caucus with UX Researcher, PM, Market Researcher, and dynamic personas for insight validation
- **Ideate:** Full caucus (all static + dynamic roles) for brainstorming; evaluation via weighted scoring
- **Prototype:** PM leads with Designer + Engineer consultation for requirements review
- **Test:** UX Researcher leads; PM + Designer panel for test plan review

#### Scripts

| Script | Commands | Purpose |
|--------|----------|---------|
| `al-dt-roles.py` | `validate-personas`, `create-from-personas`, `enrich-role` | Parse persona artifacts, create dynamic role files, append phase-specific sections |
| `al-dt-evaluate.py` | *(single command)* | Weighted scoring for concept evaluation matrix |

#### Schemas

The module defines validation schemas for its artifact types: `persona.json` (strict persona format with required fields like Goals, Frustrations, Behaviors), `requirements.json`, `user-flows.json`, `interview.json`, and others.

#### Installed Skills

The module installs 13 Kiro skills covering workflow phases, role impersonation, interviews, and spec creation.

### Kiro Module (Service)

**Type:** Service | **Prefix:** `kiro` | **No output directory**

Bridges any ideation module's output to Kiro's spec-driven development system. This module does not have its own workflow — it provides services that other modules consume.

#### What It Provides

1. **`steering/generate-specs.md`** — A contract that any ideation module follows to produce a `spec-plan.json`. Takes a requirements document with FR-x.x IDs and feature groups, proposes a spec breakdown to the user, and writes the plan via `al-kiro-specs.py`.

2. **`workflows/create-spec.md`** — Creates a single Kiro spec from the plan. Shows context, gathers the relevant requirement subset, then hands off to Kiro's native spec session (the module initiates the session, it doesn't write requirements directly).

3. **`scripts/al-kiro-specs.py`** — CRUD for `spec-plan.json`:

   | Command | Purpose |
   |---------|---------|
   | `init` | Initialize a new spec plan |
   | `add-spec` | Add a spec entry to the plan |
   | `validate` | Validate the plan structure |
   | `list` | List specs, optionally filtered by status |
   | `get --slug {slug}` | Get details for a specific spec |

   Status is filesystem-detected: if `.kiro/specs/{slug}/` exists → `"created"`, otherwise → `"pending"`.

#### Integration Flow

```
Ideation Module                    Kiro Module                    Kiro IDE
     │                                  │                            │
     │  requirements.md (FR-x.x)        │                            │
     ├─────────────────────────────────►│                            │
     │                                  │  generate-specs steering   │
     │                                  │  ───────────────────────►  │
     │                                  │  al-kiro-specs.py init     │
     │                                  │  al-kiro-specs.py add-spec │
     │                                  │         │                  │
     │                                  │  spec-plan.json            │
     │                                  │◄────────┘                  │
     │                                  │                            │
     │  /al-dt-workflow-create-spec     │  create-spec workflow      │
     ├─────────────────────────────────►│  ─────────────────────────►│
     │                                  │  Kiro native spec session  │
     │                                  │                  ┌─────────┤
     │                                  │                  │ .kiro/  │
     │                                  │                  │ specs/  │
     │                                  │                  │ {slug}/ │
     │                                  │                  └─────────┤
```

---

## Installer

The installer is a single Python CLI that manages the full lifecycle:

```bash
# List all available modules with descriptions and dependencies
python3 agent-lattice/installer.py list

# Install runtime + selected modules
python3 agent-lattice/installer.py install --target /path/to/project --modules design-thinking,kiro

# Install everything
python3 agent-lattice/installer.py install --target /path/to/project --all

# Uninstall but keep output artifacts
python3 agent-lattice/installer.py uninstall --target /path/to/project --keep-output

# Full uninstall
python3 agent-lattice/installer.py uninstall --target /path/to/project
```

During installation, the installer:

1. Copies the runtime to `.al/runtime/`
2. Copies selected modules to `.al/modules/`
3. Reads each module's `install.json` to generate Kiro `SKILL.md` files under `.kiro/skills/`
4. Installs `RUNTIME.md` as `.kiro/steering/al-runtime.md` (always-loaded by Kiro)
5. Prompts for configuration values from JSON schemas
6. Creates output directories for runnable modules
7. Resolves and validates module dependencies

---

## Design Principles

1. **Documents are the API.** Phases communicate through artifact files, not LLM memory. The output document is the cache.
2. **Lean context.** Load only what the current step needs. Role definitions when referenced, steering when applicable. Never preload.
3. **User is the director.** The AI facilitates. Gates enforce human control at every critical decision point.
4. **Roles are role-play.** Read the definition, adopt the identity. No separate context window, no tool activation.
5. **Scripts for determinism.** Requires judgment? Steering. Same input always produces same output? Script.
6. **Modules are plugins.** Filesystem presence = available. No registry beyond directory scanning.
7. **Discussions in chat.** Multi-role interactions happen in the conversation. Artifacts receive only summaries and results.
8. **Modes are per-workflow.** No automation mode carries over between workflows or sessions.
