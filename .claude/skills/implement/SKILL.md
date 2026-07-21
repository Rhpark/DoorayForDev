---
name: implement
description: "Implement a piece of work based on its SPEC.md in a work folder under docs/agents/plan/."
disable-model-invocation: true
---

Implement the work described in `SPEC.md` in the work folder (`docs/agents/plan/<YYYYMMDD>-<work-id>/`) the user points at — a Dooray task number alone is enough: locate `docs/agents/plan/*-<work-id>/` and use the `SPEC.md` inside. **A spec is required** — if the user didn't point at one or it doesn't exist, do not start implementing; ask them to run `/to-spec` first. (Work too small to deserve a spec shouldn't go through /implement at all — the user can just ask for it directly.)

Read the spec fully before touching code. Honor its PRD part (especially Out of Scope) and its SPEC part (Implementation Decisions, Testing Decisions).

## Plan first

Before touching code, write `PLAN.md` in the same work folder, in Korean (keep technical terms in English): the implementation steps as a markdown checklist (`- [ ]`), ordered, each step small enough to verify. Check items off (`- [x]`) as you complete them — if the session dies mid-implementation, the next session reads PLAN.md and resumes from the first unchecked item.

If PLAN.md already exists, resume from it instead of starting over — but first check whether SPEC.md changed after PLAN.md was written; if it did, reconcile PLAN.md with the current spec before resuming.

## Implement

Use /tdd where practical, at the seams the spec pre-agreed.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

Commit your work — code and the work-folder documents — to the current branch.
