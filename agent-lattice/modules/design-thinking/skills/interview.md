# Design Thinking Interview

Interview skill for the Design Thinking module. Provides the setup for the runtime interview mode (see `al-mode-interview.md`).

## Default Setup

- **Interviewer:** UX Researcher (`roles/ux-researcher.md`) unless the user is interviewing directly
- **Subject:** A dynamic role (synthetic user persona) or the actual user
- **Output:** `design-thinking/{phase}/interview-{slug}.md`

## Question Themes

The interviewer adapts these themes to the subject's context. Not a rigid script — follow the conversation.

1. **Context & environment** — What does your day look like? What tools do you use? Who do you work with?
2. **Goals & motivations** — What are you trying to achieve? What does success look like for you?
3. **Current pain points** — What's frustrating about how you do this today? Where do you lose time?
4. **Workarounds & behaviors** — How do you deal with those frustrations? What have you tried?
5. **Unmet needs** — What would make the biggest difference? What's missing from your current setup?
6. **Reactions to the problem space** — How do you feel about {topic from context}? What would you change?

## DT-Specific Rules

In addition to the runtime interview mode's character rules:

- The subject may volunteer information the interviewer didn't ask about — real people do this. Don't suppress it.
- The subject should reference specific details from their context (tools they use, situations they face, people they interact with), not abstract generalities.
- If an interview artifact already exists for this subject, ask: "There's an existing interview. Start fresh or continue?"

## Resuming an Interview

The same subject can be interviewed multiple times across phases. Each session appends to the existing artifact or creates a new section. This allows follow-up interviews in later phases (e.g., validating concepts in Ideate after initial discovery in Empathize).
