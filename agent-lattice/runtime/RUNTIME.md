# Agent Lattice — Runtime

Framework runtime for executing structured AI-assisted workflows.

## Runtime Principles

1. **Manifest is source of truth.** All workflow state lives in `manifest.json`. Read before acting, update after acting. Use scripts for mutations.
2. **Deferred loading.** Load only what the current step needs. Role definitions when the step references them. Never preload.
3. **Documents are the API.** Phases communicate through artifact files. The output document is the cache.
4. **Gates are contracts.** GATE = stop and wait. SOFT-GATE = easy continue. INFO-GATE = auto-continue.
5. **Fail loud.** Missing prerequisites, invalid state, missing files — stop and tell the user.
6. **Scripts for mutations.** Manifest edits, validation, structure checks — always scripts.
7. **Roles are role-play.** Read the definition, adopt the identity. No separate context.
8. **Modes are scoped.** `auto` = current step. `autoflow` = current workflow. `automagic` = full module lifecycle (skill). No mode carries over from a previous session.
9. **Discussions happen in chat by default.** All multi-role interactions (panel, caucus, interview, collaborative) show the role-play in the conversation unless runtime config `showRoleInteractions` is `false`, in which case only the outcome is shown. Artifacts get the summary or result, not the discussion.

## When to Load What

### Steering

| You're doing... | Load this doc |
|-----------------|--------------|
| Executing a workflow (phases, steps, resume) | `{runtime}/steering/al-workflows.md` |
| Manifest operations (init, update, status) | `{runtime}/steering/al-manifest.md` |
| Artifact operations (write, validate, list) | `{runtime}/steering/al-artifacts.md` |
| Handling gates | `{runtime}/steering/al-gates.md` |
| Roles and role-play mechanics | `{runtime}/steering/al-roles.md` |
| Module discovery | `{runtime}/steering/al-modules.md` |
| Running a panel step | `{runtime}/steering/al-mode-panel.md` |
| Running a caucus step | `{runtime}/steering/al-mode-caucus.md` |
| Conducting an interview | `{runtime}/steering/al-mode-interview.md` |
| Running a collaborative step | `{runtime}/steering/al-mode-collaborative.md` |
| Running a consultation step | `{runtime}/steering/al-mode-consultation.md` |
| Running in auto mode (current step only) | `{runtime}/steering/al-mode-auto.md` |
| Running in autoflow mode (current workflow, autonomous) | `{runtime}/steering/al-mode-autoflow.md` |
| Running in automagic mode (full module lifecycle) | `{runtime}/steering/al-mode-automagic.md` |
| Reading or applying configuration | `{runtime}/steering/al-config.md` |

### Scripts

| Script | Purpose |
|--------|---------|
| `{runtime}/scripts/al-manifest.py` | **Workflow state** — init, update-step, update-phase, resume, status, steps |
| `{runtime}/scripts/al-roles.py` | Role validation, discovery, section management, read sections |
| `{runtime}/scripts/al-write.py` | Artifact writing with schema validation, listing |
| `{runtime}/scripts/al-modules.py` | Installed module metadata (not workflow state) — inspect --all / --module |
| `{runtime}/scripts/al-config.py` | Config init, read, and validate |

### Skills

| Skill | Purpose |
|-------|---------|
| `al-impersonate` | Impersonate a role from a definition file |

## Quick Reference

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

### Role-Play

When a step declares a role, read the role definition file and adopt that perspective:
- Solo: read one role, produce output from that lens
- Panel: user and roles take turns interactively
- Caucus: roles deliberate among themselves, closer summarizes
- Interview: read both roles, alternate voices exchange by exchange
