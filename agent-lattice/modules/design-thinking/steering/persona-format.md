# Persona Format

The personas file (`{output}/01-empathize/personas.md`) uses a strict format. Every persona follows this exact structure. No variations.

## File Structure

```markdown
## Persona: {Full Name}

- **Age:** {number}
- **Occupation:** {text}
- **Location:** {text}
- **Demographics:** {text}
- **Devices:** {text}
- **Goals:**
  - {goal 1}
  - {goal 2}
- **Frustrations:**
  - {frustration 1}
  - {frustration 2}
- **Behaviors:**
  - {behavior 1}
  - {behavior 2}
- **Environment:** {text}
- **Skeptical of:**
  - {item 1}
  - {item 2}
- **Quote:** "{text}"
```

## Role Enrichment

Roles are enriched by script, not by the LLM. After each relevant step, the workflow calls `al-dt-roles.py enrich-role --source {source}` which reads the artifact, extracts per-persona data, and appends it as new sections directly to the role files in `{output}/roles/`. Do NOT call `al-roles.py append-section` directly for persona enrichment — use `enrich-role` which handles the extraction and persona attribution.

## Rules

- Each persona starts with `## Persona: {Full Name}`
- Every field starts with `- **Key:** value` (bullet, space, bold-open, key, colon, bold-close, space, value)
- Multi-value fields (Goals, Frustrations, Behaviors, Skeptical of) use `- **Key:**` on its own line, followed by indented sub-items (`  - value`)
- Single-value fields have the value on the same line as the key
- Required fields: Age, Occupation, Location, Goals (2+), Frustrations (2+), Behaviors (2+), Skeptical of (2+), Quote
- Optional fields: Demographics, Devices, Environment
- No other heading levels inside a persona (no ###)
- No blank bold keys, no bare text, no blockquotes
- Personas are separated by the next `## Persona:` heading
