# Kiro Module

Service module for Kiro integration. Provides spec generation and creation as functions that other modules consume.

This module does not have its own ideation workflow. It provides:
1. A spec plan contract that any ideation module follows to produce a `spec-plan.json`
2. A script to manipulate the spec plan (create, validate, update status)
3. A workflow for creating individual Kiro specs from the plan

## Steering

| Doc | File | Purpose |
|-----|------|---------|
| Generate Spec List | `steering/generate-specs.md` | Contract: how to produce a spec-plan.json from ideation artifacts |

## Workflows

| Workflow | File | Purpose |
|----------|------|---------|
| Create Spec | `workflows/create-spec.md` | Create a single Kiro spec from the plan |

## Scripts

| Script | File | Purpose |
|--------|------|---------|
| Spec Plan | `scripts/al-kiro-specs.py` | Spec plan CRUD, validation, filesystem-based status detection |

## Roles

None. This is a service module.

## Skills

None currently.
