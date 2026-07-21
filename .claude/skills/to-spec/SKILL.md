---
name: to-spec
description: Turn the current conversation into a spec (PRD part + SPEC part) and save it as SPEC.md in the work folder under docs/agents/plan/ — no interview, just synthesis of what you've already discussed.
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a spec document with two clearly separated parts: a **PRD part** (what & why, the user's perspective) and a **SPEC part** (how, the engineering perspective). Do NOT interview the user — just synthesize what you already know. The one exception: the seam confirmation in step 2 below. (Operational questions — e.g. asking for the Dooray task number — are not an interview and are always fine.)

If the conversation and available sources lack enough substance to synthesize a real spec, say so and suggest running `/grill-me` first — never invent requirements to fill the template.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. If the project has a domain glossary, use its vocabulary throughout the spec; if it has ADRs, respect those decisions in the area you're touching. (If neither exists, don't hunt for them or ask — just proceed.)

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

3. Locate the work folder and guarantee `GRILL_ME.md` — before writing any spec. `<work-id>` is the Dooray task number (ask if not given; if the user says there is none, a short kebab-case topic slug takes its place); look for an existing `docs/agents/plan/*-<work-id>/` folder and reuse it — only if none exists, create `docs/agents/plan/<YYYYMMDD>-<work-id>/` dated today. `GRILL_ME.md` must exist in that folder — no exceptions; it is the record of how the requirements were understood, even when no interview happened. If it's missing, create it in Korean using the template in `.claude/skills/grilling/SKILL.md` (read that file for the template), recording the sources you read (Dooray post number/title, key-content summary, your interpretations and assumptions) and any Q&A that arose — including the seam confirmation from step 2. If it already exists, append this session's new Q&A following that skill's dated-section rule.

4. Write the spec in Korean using the template below — keep technical terms in English, and keep the template's section headings exactly as written (in English). Save it as `SPEC.md` in the work folder. Tell the user the file path so they can review and edit it directly.

If `SPEC.md` already exists, revise it in place — it always holds the single current agreed spec; git history keeps the old versions, so never leave stale sections alongside new ones. Whenever you revise, check the PRD part and the SPEC part against each other and resolve any contradiction between them.

<spec-template>

## PRD

<!-- What & why — the product view, from the user's perspective. -->

### Problem Statement

The problem that the user is facing, from the user's perspective.

### Solution

The solution to the problem, from the user's perspective.

### User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

### Out of Scope

A description of the things that are out of scope for this spec.

## SPEC

<!-- How — the engineering view. Must never contradict the PRD part above. -->

### Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

### Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Further Notes

Any further notes about the feature.

</spec-template>
