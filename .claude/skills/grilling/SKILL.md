---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview me relentlessly about every aspect of this until we reach a shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. Asking multiple questions at once is bewildering.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.), look it up rather than asking me. The *decisions*, though, are mine — put each one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding. (Documenting the session per the rules below is not "acting on it" — save whenever its trigger fires.)

## Escalate to wayfinder when the session outgrows itself

If open questions keep accumulating, decisions are too interdependent to resolve one-by-one, or the work clearly won't fit one session, propose escalating to `/wayfinder`, with your reasons. The user decides — and may override in either direction (insist on wayfinder when you thought grilling was enough, or vice versa). Never invoke it yourself.

If the user accepts, save GRILL_ME.md immediately (see below) — record the escalation decision and its reasons in 결정사항, and everything still open in 미해결 질문 — then ask the user to run `/wayfinder`; you cannot invoke it yourself. From that point the map's tickets take over: decision Q&A after escalation is recorded in tickets, never appended back here.

## Document the session

Exception first: if this grilling is resolving a **wayfinder ticket** (the session is working a map and its tickets), do NOT write GRILL_ME.md — record the outcome in that ticket's `## Answer` section instead, per the wayfinder skill. The rules below apply to standalone grilling only.

Save the session as `GRILL_ME.md` in the work folder when we reach shared understanding — or immediately upon escalation to wayfinder. To locate the work folder: `<work-id>` is the Dooray task number (ask if not given; if the user says there is none — e.g. stress-testing an idea — use a short kebab-case topic slug in its place); look for an existing `docs/agents/plan/*-<work-id>/` folder and reuse it — only if none exists, create `docs/agents/plan/<YYYYMMDD>-<work-id>/` dated today (this date marks when the work's records began; never ask the user for a date). Write the document in Korean (keep technical terms in English).

If GRILL_ME.md already exists (re-grilling the same work), append a new dated section (`## YYYY-MM-DD`) below the existing content, with that session's 근거 자료/결정사항/Q&A/미해결 질문 nested under it as `###` subsections — never rewrite or delete past entries; past records are evidence. Resetting a work folder is the user's manual act of deleting it, never yours.

Then tell me the file path so I can edit it directly:

```markdown
# <주제>

## 근거 자료

- <읽은 자료: Dooray 게시글 번호/제목, 파일, 링크 등> — <핵심 내용 한 줄 요약>
- <에이전트가 한 해석이나 가정>

## 결정사항

- <결정> — <한 줄 이유>

## Q&A

<!-- 세션의 모든 질문과 답변을 순서대로, 의미를 보존해 기록 — 선별·요약하지 말 것 (단, 축어록이 아니라 내용 중심으로) -->

- **Q:** <질문>
  **A:** <답변>

## 미해결 질문

- <남은 것, 없으면 "없음">
```
