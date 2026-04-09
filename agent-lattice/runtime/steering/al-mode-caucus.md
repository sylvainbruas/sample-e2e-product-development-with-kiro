# Agent Lattice — Caucus

## When to Use This

Load this when executing a caucus step — roles deliberate among themselves without the user until they reach consensus or a designated role summarizes the tensions.

## How It Works

The LLM reads all participating role definitions and generates multiple rounds of argument. Roles challenge each other, defend positions, and work toward resolution. The user is not part of the conversation — they receive the result.

A designated role (the closer, typically the one with scope/priority expertise) either declares consensus or summarizes the unresolved tensions and blockers.

## Setup

A caucus needs: participants (which roles, with optional `focus` and `challenges`), a closer (which role summarizes), a topic, and optionally input artifacts or an artifact being reviewed.

- **From a workflow step:** The workflow declares all of the above before invoking the caucus.
- **Ad-hoc (no predefined setup):** The caucus lists available roles (via role discovery — see `al-roles.md`), asks the user to pick participants, closer, and topic.

The caucus does not read configuration files. It receives its setup from the caller.

## Caucus Flow

1. Read all participating role definitions and input artifacts (if any)
2. **Round 1:** Each role states their position (grounded in their expertise and "Skeptical of")
3. **Round 2+:** Roles respond to each other — challenge, concede, refine. Each round should narrow the disagreements.
4. **Close:** The closer either:
   - Declares consensus and states the agreed position
   - Summarizes remaining tensions: what's agreed, what's blocked, what needs the user's decision

Rounds continue until consensus is reached or the discussion stops advancing (typically 2-3 rounds). If consensus is reached early, stop. Don't fill rounds for the sake of it.

## Generating Arguments

Each role in each round MUST:
- Reference specific points from previous rounds (not repeat their opening)
- Respond to challenges raised by other roles
- Concede when another role makes a valid point — don't be stubborn for the sake of it
- Sharpen their position based on the discussion, not just restate it
- Propose compromises where possible

The goal is convergence, not endless debate. If a role's concern has been addressed, they should acknowledge it and move on.

## Output

The deliberation is shown to the user in the chat — each round is visible, each role's arguments are presented as they happen. The artifact gets the resolution summary.

```markdown
## 🏛️ Caucus: {topic}

### Participants
- **{Role 1}** — {focus}
- **{Role 2}** — {focus}
- **Closer:** {Closer Role}

### Deliberation

#### Round 1
**{Role 1}:** {opening position}
**{Role 2}:** {opening position}

#### Round 2
**{Role 1}:** {response to Role 2, refined position}
**{Role 2}:** {response to Role 1, concessions or sharpened pushback}

### Resolution
**Status:** Consensus reached | Tensions remain
**Agreed:** {What all roles converged on}
**Unresolved:** {What couldn't be resolved — needs user decision}
**Blockers:** {Hard constraints that prevent agreement}
**Recommendation:** {Closer's recommended path forward}
```

## Revision Protocol

When a caucus reviews an existing artifact and the closer's resolution surfaces issues, the user chooses:

- **Revise:** Re-adopt the role that originally produced the artifact, revise incorporating the caucus outcome. Replaces original.
- **Annotate:** Caucus resolution appended as "Caucus Notes" section. Original unchanged.
- **Override:** User disagrees, proceeds without changes.

## Display Mode

Controlled by runtime config `showRoleInteractions` (loaded at workflow start):

- **`true` (default):** Show all rounds of deliberation in chat as they happen. The artifact gets the resolution summary.
- **`false`:** Run the full deliberation internally. Show only the Resolution section in chat. The artifact gets the full deliberation.

## Rules

- When `showRoleInteractions` is true, the user sees the full deliberation — rounds are shown, not hidden
- Roles argue with each other, not with the user
- Each round must advance the discussion — no circular repetition
- The closer synthesizes, they don't dictate
- Concessions are good — they show the deliberation is working
- If consensus is reached early, stop
