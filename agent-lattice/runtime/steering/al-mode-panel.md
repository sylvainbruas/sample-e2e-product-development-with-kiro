# Agent Lattice — Panel

## When to Use This

Load this when executing a panel step — an interactive discussion where the user and invited roles take turns.

## How It Works

The LLM reads all participating role definitions. Roles open with their perspectives on the topic, then the user joins the conversation — asking questions, challenging, steering. Each role responds from their expertise and pushes back where their "Skeptical of" applies.

This is an interactive mode. The user is a participant, not a spectator. When the user isn't actively directing, roles engage with each other until the user jumps in.

## Setup

A panel needs: participants (which roles), topic (what to discuss), and optionally input artifacts and per-role challenges.

- **From a workflow step:** The workflow declares participants, topic, inputs, and challenges before invoking the panel.
- **Ad-hoc (no predefined setup):** The panel lists available roles (via role discovery — see `al-roles.md`) and asks the user to pick participants and topic.

The panel does not read configuration files. It receives its setup from the caller.

### Per-Role Challenges

When the caller provides `challenges` per participant, this tells the role what to actively push back on in this specific discussion. Combined with the role's "Skeptical of" section, this produces genuine adversarial critique.

- `focus` = "what I'm looking at" (descriptive)
- `challenges` = "what I'm going to push back on" (adversarial)

When no `challenges` are provided (ad-hoc case), roles fall back to their "Skeptical of" only.

## Starting a Panel

1. Read all participating role definitions and input artifacts (if any)
2. If participants and topic are provided → roles open with perspectives
3. If invoked without explicit context → assume the topic is the previous conversation context, roles open on that
4. If there is no previous context and no setup → list available roles, ask the user to pick participants and topic

Roles always open first. The user responds when ready.

## Once Running

1. The user responds — asks questions, challenges, steers, or says nothing and lets roles continue engaging with each other
2. Roles respond to the user and to each other
3. Continue until the user is satisfied or calls it

## How Roles Contribute

Throughout the panel (not just the opening), each role MUST:
- Reference specific content from input artifacts, not generalities
- Raise concrete concerns grounded in their "Skeptical of" and any provided `challenges`
- Not simply agree — find something to push back on
- Propose alternatives when disagreeing, not just criticize
- Respond to what other roles and the user have said, not just repeat their opening

If a role genuinely has no concerns (rare), state what they checked and why it passed scrutiny.

## Output

All role perspectives and discussion happen in the chat — the user sees every contribution as it happens.

When the panel concludes, produce a summary artifact (see `al-artifacts.md` for the script interface):

```markdown
## 📋 Panel: {topic}

### Participants
- **{Role 1}** — {focus}
- **{Role 2}** — {focus}

### Key Points
{Summary of what was discussed, what the user decided, what remains open}

### Contested Points
- **{Point 1}:** {Role A} argues X, {Role B} counters Y. User decided: {decision or "deferred"}

### Outcome
{What was agreed, what was deferred, what needs more work}
```

## Revision Protocol

When a panel reviews an existing artifact and surfaces issues, the user chooses:

- **Revise:** Re-adopt the role that originally produced the artifact, revise incorporating feedback. Replaces original.
- **Annotate:** Panel's contested points appended as "Review Notes" section in the artifact. Original content unchanged.
- **Override:** User disagrees with concerns, proceeds without changes.

## Display Mode

Controlled by runtime config `showRoleInteractions` (loaded at workflow start):

- **`true` (default):** Show all role perspectives and discussion in chat as they happen. The artifact gets the summary.
- **`false`:** Run role exchanges internally. Show only the summary artifact in chat. The user still participates when the panel needs their input.

## Rules

- Roles open first, user joins when ready
- Each role's perspective MUST be grounded in their Expertise, Principles, and Skeptical of
- Each role MUST raise at least one concrete concern
- Roles reference specific artifacts, not generalities
- Contested points are valuable — surface them, don't smooth over
- The user drives the conversation — but roles keep engaging with each other when the user is quiet
