# Agent Lattice — Configuration

## When to Use This

Load this when you need to understand or work with configuration values.

## Config Locations

| Scope | Config file | Schema file |
|-------|------------|-------------|
| Runtime | `.al/config.json` | `.al/runtime/config-schema.json` |
| Module | `.al/output/{module}/config.json` | `.al/modules/{module}/config-schema.json` |

Runtime config applies to all modules (e.g., display behavior). Module config applies only to that module's workflows.

## Reading Config

Use the config script. Never read config files directly.

```bash
# Runtime config
python3 {runtime}/scripts/al-config.py get-all --runtime

# Module config
python3 {runtime}/scripts/al-config.py get-all --module {module}

# Single value
python3 {runtime}/scripts/al-config.py get --runtime --key showRoleInteractions
python3 {runtime}/scripts/al-config.py get --module {module} --key generateProfiles
```

All commands output JSON to stdout.

## Core Rules

1. **Config is read-only at runtime.** The LLM reads config values — it never writes or modifies config files. All config writes happen through the installer.
2. **Load at workflow start.** Both runtime and module config are loaded once at the start of each workflow invocation (Step 0 in the workflow protocol). Hold the values in context for the duration.
3. **Config drives behavior, not scripts.** When a config value disables a feature, the LLM skips the related work entirely — it does not call scripts that would fail or produce unused output.
4. **No on-demand loading.** Do not re-read config mid-workflow. The values loaded at Step 0 are authoritative for the entire workflow.

## Recovery

If a config file is missing (e.g., deleted manually), initialize it from schema defaults:

```bash
python3 {runtime}/scripts/al-config.py init --runtime
python3 {runtime}/scripts/al-config.py init --module {module}
```

This writes default values from the schema. It does not overwrite an existing config file.
