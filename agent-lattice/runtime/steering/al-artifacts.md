# Agent Lattice — Artifact Operations

## When to Use This

Load this when you need to create, update, or query artifacts.

## Core Rule

All artifact file operations go through scripts. NEVER edit artifact files directly — always use the artifact script.

When a workflow says "Save to {path} (type: typename)", this means:
1. Pipe content into the script via heredoc using the specified type:
   ```bash
   python3 {runtime}/scripts/al-write.py write \
     --module {name} --path {relative-path} --type {typename} << 'CONTENT_EOF'
   {content here}
   CONTENT_EOF
   ```

The script validates content against the schema for that type before writing. If validation fails (critical/high findings), it exits non-zero and the content is NOT written. Fix the content and retry.

Do NOT attempt to write or edit artifact files directly — always use the script.

## Script Interface

All paths are module-relative. The script resolves them to `.al/output/{module}/`.

```bash
# Check the schema before first write of a type
python3 {runtime}/scripts/al-write.py schema \
  --module {module-name} --type {typename}

# Write a typed artifact (creates or overwrites)
python3 {runtime}/scripts/al-write.py write \
  --module {module-name} --path {relative-path} --type {typename} << 'CONTENT_EOF'
{content}
CONTENT_EOF

# Append to an existing artifact
python3 {runtime}/scripts/al-write.py write \
  --module {module-name} --path {relative-path} --type {typename} --mode append << 'CONTENT_EOF'
{content}
CONTENT_EOF

# List artifacts in a directory
python3 {runtime}/scripts/al-write.py list \
  --module {module-name} --dir {relative-dir}
```

## Schema Resolution

The `--type` parameter selects a validation schema. Schemas are searched in order:
1. Module schemas: `.al/modules/{module}/schemas/{type}.json`
2. Runtime schemas: `.al/runtime/schemas/{type}.json`

Module-specific types (e.g., `persona`, `archetype`, `prfaq`) live in the module's `schemas/` folder. Shared types (`generic`, `role`, `phase-summary`, `context`) live in `runtime/schemas/`.

Every workflow step specifies the type in parentheses: `Save to {path} (type: typename)`. Use that type.

## Before Writing

Before the first write of each artifact type in a phase, check its schema:

```bash
python3 {runtime}/scripts/al-write.py schema \
  --module {module-name} --type {typename}
```

The schema defines the exact patterns, sections, and fields the validator will check. Use this to structure the content correctly the first time. Once you've seen a type's schema, you don't need to check it again for subsequent writes of the same type.

## Operations

### Writing Content

Pipe content directly into the script via heredoc:

```bash
python3 {runtime}/scripts/al-write.py write \
  --module {module-name} --path {relative-path} --type {typename} << 'CONTENT_EOF'
{content}
CONTENT_EOF
```

Use `--mode append` to add content to an existing file rather than overwrite it:

```bash
python3 {runtime}/scripts/al-write.py write \
  --module {module-name} --path {relative-path} --type {typename} --mode append << 'CONTENT_EOF'
{content}
CONTENT_EOF
```

`--content "short text"` is available for very brief content (one line), but prefer the heredoc pipe for reliability.
