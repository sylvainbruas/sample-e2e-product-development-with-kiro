# Agent Lattice — Interview

## When to Use This

Load this when executing an interview step — a structured conversation following a prepared script of questions, applied to a subject.

## How It Works

An interview takes a prepared script of questions and applies them to a subject. The subject can be:

- **A dynamic role** (e.g., a synthetic user persona) — the LLM role-plays both the interviewer and the subject
- **A static role** (e.g., the Engineer) — same, the LLM role-plays both sides
- **The actual user** — the LLM asks the questions, the user answers

The interview script guides the conversation, but the interviewer adapts based on responses — following up on interesting threads, probing deeper where needed.

## Setup

The caller provides:
- **Interview script** — the prepared questions or question themes (from a skill protocol or workflow step)
- **Subject** — which role to interview, or "user" if interviewing the actual user
- **Interviewer role** (optional) — which role conducts the interview. Shapes the questioning style. If not specified, questions follow the script neutrally.
- **Output path** — where to write the interview artifact

The interview does not read configuration files. It receives its setup from the caller. Ad-hoc invocation (without a workflow context) is not currently supported — interviews require a prepared script and a declared subject.

## Interview Flow

### When the subject is a role (synthetic)

1. Read the subject's role definition and the interviewer's role definition (if specified)
2. The interviewer asks a question from the script, adapted to the subject's context
3. The subject responds in character
4. The interviewer follows up based on the response — probing, clarifying, going deeper
5. Move to the next script question when the thread is exhausted
6. Continue until the script is covered or a natural conclusion is reached

Each question should be informed by previous answers. Do not pre-generate the full transcript — simulate it exchange by exchange.

### When the subject is the user

1. Read the interviewer's role definition (if specified) and the interview script
2. Ask the first question
3. Wait for the user's response
4. Follow up based on the response, then move to the next script question
5. Continue until the script is covered or the user ends it

## Staying in Character

When the subject is a role:
- They answer from their defined context — goals, frustrations, behaviors, environment
- They do NOT break character or provide meta-commentary
- They respond as a real person would — sometimes vague, sometimes emotional, sometimes contradictory
- They push back when something doesn't fit their reality

When an interviewer role is specified:
- They ask questions shaped by their expertise and style
- They follow up based on what their role would find interesting or concerning

## Progressive Capture

Each exchange is shown in the chat — the user sees the interviewer's questions and the subject's responses as they happen.

The conversation is also written progressively to the output path declared by the caller (see `al-artifacts.md` for the script interface).

Format: `**Interviewer:** {question}` / `**{Subject name}:** {response}`

## Insight Extraction

At session end:
- Extract 3-5 key insights from the conversation
- Each insight: statement + supporting quote from the interview
- Append insights section to the artifact

When the subject is a role, insights must surface things NOT already in the role definition. If the interview only confirms what's already written, it's not adding value. When the subject is the user, insights capture what was learned — patterns, priorities, constraints, surprises.

## Multiple Interviews

One artifact file per subject. Not combined. Each interview stands alone as a self-contained document. The same subject can be interviewed multiple times — each session appends or creates a new section.

## Interview Quality

The interviewer should:
- Follow up on unexpected responses
- Ask "why" and "tell me about a time when..."
- Probe contradictions between stated goals and described behaviors
- Explore adjacent topics the script didn't anticipate
- Adapt the script order based on conversation flow — don't rigidly follow the sequence if a natural thread emerges
