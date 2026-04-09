# Agent Lattice — Consultation

## When to Use This

Load this when executing a consultation step — one role leads the work and pulls in other roles for focused input on specific concerns.

## How It Works

The LLM adopts the lead role and produces the step's output from that perspective. When a specific concern arises that falls outside the lead's expertise, the LLM switches to a consulted role for focused input, then returns to the lead.

The lead drives the work. Consulted roles provide targeted input — they don't take over.

## Setup

A consultation step needs: a lead role, consultants (with their areas of concern), a topic, and an output path. Optionally input artifacts for starting context.

- **From a workflow step:** The workflow declares the lead, consultants with their concerns, and the output path.
- **Ad-hoc:** Not currently supported — consultation requires a declared lead and consultant mapping.

The mode does not read configuration files. It receives its setup from the caller.

## Consultation Flow

1. Read the lead role definition and input artifacts
2. The lead begins producing the step's output
3. When a concern arises that matches a consultant's area:
   - Read the consultant's role definition
   - Switch to the consultant's perspective for focused input on that specific concern
   - The consultant responds from their expertise — brief, targeted, not a full analysis
   - Return to the lead role, incorporating the consultant's input
4. Continue until the step's output is complete

Consultants are loaded on demand — only when the lead encounters their area of concern, not upfront.

## How Roles Contribute

The lead role:
- Drives the work from start to finish
- Recognizes when a concern falls outside their expertise
- Incorporates consultant input into their output — they don't just append it

Each consultant:
- Responds to a specific question or concern, not the whole topic
- Keeps it brief and targeted — not a full analysis
- Responds from their expertise and "Skeptical of" lens
- May flag concerns the lead didn't ask about, if they're significant

## Output

The lead's work and consultant exchanges are shown in the chat — the user sees when a consultant is pulled in and what they contribute.

The artifact is produced by the lead, enriched by consultant input (see `al-artifacts.md` for the script interface). Include a participation section in the document body to track who was consulted and on what.

## Display Mode

Controlled by runtime config `showRoleInteractions` (loaded at workflow start):

- **`true` (default):** Show the lead's work and consultant exchanges in chat as they happen. The artifact is produced by the lead.
- **`false`:** Run all exchanges internally. Show only the completed artifact in chat.

## Rules

- The lead drives — consultants advise, they don't take over
- Consultants are loaded on demand, not upfront
- Consultant input is brief and targeted
- The lead incorporates input — the final artifact is cohesive, not a patchwork
- Consultants may flag unsolicited concerns if significant
