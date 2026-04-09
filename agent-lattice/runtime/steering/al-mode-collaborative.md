# Agent Lattice — Collaborative

## When to Use This

Load this when executing a collaborative step — roles contribute in order to a shared artifact, each building on what the previous role produced.

## How It Works

The LLM reads all participating role definitions upfront. Each role adds to or refines the artifact from their perspective, building on the previous role's contribution. The result is a single artifact shaped by multiple lenses.

This is an additive mode — each role enriches, not debates.

## Setup

A collaborative step needs: participants (ordered), topic, and an output path. Optionally input artifacts for starting context.

- **From a workflow step:** The workflow declares the ordered list of roles and the output path.
- **Ad-hoc:** Not currently supported — collaborative mode requires a declared sequence.

The mode does not read configuration files. It receives its setup from the caller.

## Collaborative Flow

1. Read all participating role definitions and input artifacts (if any)
2. Create the artifact (see `al-artifacts.md`)
3. **First role:** Produces the initial contribution from their perspective
4. **Each subsequent role:** Reads the artifact so far, adds their perspective, refines or extends (see `al-artifacts.md` for append operations)
5. After the last role contributes, the artifact is complete

## How Roles Contribute

Each role in their turn MUST:
- Read the full artifact as it stands (including previous roles' contributions)
- Add from their expertise — what the previous roles missed or couldn't see
- Refine where their expertise gives them a better lens
- Reference specific content from input artifacts where relevant

If a role finds a problem with an earlier contribution (e.g., Engineer finds Designer's proposal technically impossible), they annotate it — noting the issue and proposing an alternative alongside the original. The earlier content is not revised in this pass; revisions happen in subsequent iterations.

## Output

Each role's contribution is shown in the chat as it's produced — the user sees each role building on the previous.

The shared artifact is written progressively (see `al-artifacts.md`). Include a contributors section in the document body to track which roles contributed.

## Display Mode

Controlled by runtime config `showRoleInteractions` (loaded at workflow start):

- **`true` (default):** Show each role's contribution in chat as it's produced. The artifact is written progressively.
- **`false`:** Run all contributions internally. Show only the completed artifact in chat.

## Rules

- Order matters — the sequence is intentional, not arbitrary
- Each role builds on previous contributions, not from scratch
- Disagreements are annotated, not argued — revisions happen in subsequent iterations
- The artifact grows progressively — each role appends or refines
- The final artifact reflects all perspectives, layered
