---
name: wayfinder
description: Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets in a work folder under docs/agents/plan/, and resolve them one at a time until the way to the destination is clear.
disable-model-invocation: true
---

A loose idea has arrived — too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way, not charging at the destination. This skill charts the way as a **shared map** of local markdown files, then works its **decision tickets** — questions whose resolution is a decision, not slices of a build to execute — one at a time until the route is clear.

The destination varies per effort, and naming it is the first act of charting — it shapes every ticket. It might be a spec to hand off and iterate on, a decision to lock before planning starts, or a change made in place like a data-structure migration.

## Plan, don't do

Wayfinder is **planning** by default: each ticket resolves a decision, and the map is done when the way is clear — nothing left to decide before someone goes and does the thing. The pull to just do the work is usually the signal you've reached the edge of the map and it's time to hand off. An effort can override this in its **Notes** — carrying execution into the map itself — but absent that, produce decisions, not deliverables.

## Where things live

Everything for one effort lives in its work folder — `<work-id>` is the Dooray task number (ask if not given; if the user says there is none, a short kebab-case topic slug takes its place); look for an existing `docs/agents/plan/*-<work-id>/` folder and reuse it — only if none exists, create `docs/agents/plan/<YYYYMMDD>-<work-id>/` dated today:

- `GRILL_ME.md` — the pre-map record: initial understanding, sources read, and the escalation decision if this effort grew out of a grilling session. Written by `/grilling`; the charting session's grilling produces it if it doesn't exist yet.
- `MAP.md` — the map, the canonical artifact. Link GRILL_ME.md from its Notes section.
- `tickets/NNN-<slug>.md` — one file per ticket, numbered in creation order (`001-`, `002-`, …), slug in short kebab-case.

Write MAP.md and ticket bodies in Korean (keep technical terms in English). Once the map exists, decision Q&A is recorded in tickets' Answer sections — never appended back into GRILL_ME.md.

All files are plain markdown the user can open and edit directly. Refer to maps and tickets **by their title**, never by a bare number — wrap the title in a relative markdown link to the file.

## The map (`MAP.md`)

The map is an **index**, not a store. It lists the decisions made and points at the tickets that hold their detail; a decision lives in exactly one place — its ticket — so the map never restates it, only gists it and links.

```markdown
# <Effort title>

## Destination

<what reaching the end of this map looks like — the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

<!-- the index — one line per closed ticket -->

- [<closed ticket title>](tickets/NNN-slug.md) — <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet -->

## Out of scope

<!-- work ruled beyond the destination; closed, never graduates -->
```

Open tickets are **not** listed in the map — they are found by scanning `tickets/` for `status: open`.

## Tickets

Each ticket is a file in `tickets/`, sized to one agent session:

```markdown
---
status: open            # open | closed
type: grilling          # research | prototype | grilling | task
assignee:               # empty = unclaimed; a name = claimed
blocked-by: []          # ticket filenames, e.g. [001-pick-database.md]
---

## Question

<the decision or investigation this ticket resolves>
```

A session **claims** a ticket by setting `assignee` **first**, before any work, so concurrent sessions skip it. A ticket is **unblocked** when every ticket in `blocked-by` has `status: closed`; the **frontier** is the open, unblocked, unclaimed tickets — the edge of the known.

The answer isn't part of the body — on resolution, append an `## Answer` section and set `status: closed`. Assets created while resolving a ticket are linked from the ticket file, not pasted in.

## Ticket Types

Every ticket is either **HITL** — human in the loop, worked *with* a human who speaks for themselves — or **AFK**, driven by the agent alone. A HITL ticket only resolves through that live exchange; the agent never stands in for the human's side of it (a grilling agent that answers its own questions has broken this).

- **Research** (AFK): Reading documentation, third-party APIs, or local resources to surface a fact a decision waits on. Resolved by a research **subagent** (via the Agent tool). Use when knowledge outside the current working directory is required.
- **Prototype** (HITL): Raise the fidelity of the discussion by making a cheap, rough, concrete artifact to react to — an outline, a rough take, a stub. Link the prototype from the ticket. Use when "how should it look" or "how should it behave" is the key question.
- **Grilling** (HITL): Conversation via the /grilling skill, one question at a time. The default case.
- **Task** (HITL or AFK): Manual work that must happen before a *decision* can be made — nothing to decide, prototype, or research, but the discussion is blocked until it's done. The agent drives it alone where it can (AFK); otherwise it hands the human a precise checklist (HITL). Resolved when the work is done; the answer records what was done and any resulting facts later tickets depend on.

## Fog of war

The map is _deliberately_ incomplete: don't chart what you can't yet see. Beyond the live tickets lies the **fog of war** — the dim view of decisions and investigations you can tell are coming but can't yet pin down, because they hang on questions still open. Resolving a ticket clears the fog ahead of it, graduating whatever's now specifiable into fresh tickets — one at a time, until the way to the destination is clear and no tickets remain.

The map's **Not yet specified** section is where that dim view is written down. Everything here is in scope, just not sharp enough to ticket. Don't pre-slice the fog into ticket-sized pieces: one patch may graduate into several tickets, or none, once the frontier reaches it.

**Fog or ticket?** The test is whether you can state the question precisely now — _not_ whether you can answer it now.

- **Ticket when** the question is already sharp — even if it's blocked and you can't act on it yet.
- **Not yet specified when** you can't yet phrase it that sharply.

## Out of scope

Fog only ever gathers _toward_ the destination. Work beyond the destination is **out of scope** — it gets its own **Out of scope** section on the map: work you've consciously ruled out of _this_ effort.

When a ticket that already exists turns out to sit past the destination, **close it** and leave one line in the **Out of scope** section: the gist plus why it's out of scope, linking the closed ticket. It stays out of **Decisions so far**, which records the route actually walked.

## Invocation

Two modes. Either way, **never resolve more than one ticket per session** — with the exception of research tickets.

### Chart the map

User invokes with a loose idea.

1. **Name the destination.** Run a `/grilling` session to pin down what this map is finding its way to — the spec, decision, or change. The destination fixes the scope, so it's settled first.
2. **Map the frontier.** Grill again, **breadth-first** this time: fan out across the whole space rather than deep on any one thread, surfacing the open decisions and the first steps takeable now. **If this surfaces no fog** — the way to the destination is already clear, the whole journey small enough for one session — you don't need a map. Save GRILL_ME.md first (per the grilling skill's rules) so the grillings that just happened are recorded, then stop and ask the user how they'd like to proceed — usually running `/to-spec`.
3. **Save GRILL_ME.md first** (per the grilling skill's rules) covering both grillings above — the destination and the frontier Q&A — then **create the map** as `MAP.md` in the work folder (locate or create it per [Where things live](#where-things-live); if this effort was escalated from an earlier grilling session, the folder and GRILL_ME.md already exist — reuse and append): Destination and Notes filled in, Decisions-so-far empty, the fog sketched into **Not yet specified**.
4. **Create the tickets you can specify now** in `tickets/` — then wire `blocked-by` edges in a **second pass**. Everything you can't yet specify stays in the fog.
5. **Fire the research subagents.** For each `research` ticket you just created, spin up a research subagent to resolve it in parallel, recording its findings in the ticket's Answer section.
6. Stop — charting is one session's work; it hand-resolves nothing.

### Work through the map

User invokes with a map (path or effort name). A ticket is **optional** — without one, you pick the next decision, not the user.

1. Load the **map** — the low-res view, not every ticket body.
2. Choose the ticket. If the user named one, use it. Otherwise take the first frontier ticket in order. **Claim it**: set `assignee` to the user's name — read it from `git config user.name`; ask once only if that's unavailable — before any work.
3. Resolve it — **zoom as needed**: read the full body of any related or closed ticket on demand; invoke the skills the `## Notes` block names. If in doubt, use `/grilling`.
4. Record the resolution: append the answer as an `## Answer` section, set `status: closed`, and add a one-line entry to the map's Decisions-so-far.
5. Add newly-surfaced tickets (create-then-wire); graduate any fog the answer has made specifiable, clearing each graduated patch from **Not yet specified** so it lives only as its new ticket. If the answer reveals a ticket sits beyond the destination, **rule it out of scope** rather than resolving it. If the decision invalidates other parts of the map, update or delete those tickets.

The user may run unblocked tickets in parallel sessions, so expect the files to change concurrently — re-read before writing.

### Reaching the destination

When no open tickets remain and no fog is left, the way is clear — the map is done. If the destination is a spec, ask the user to run `/to-spec` (you cannot invoke it yourself) — it will produce `SPEC.md` in the same work folder, and from there the normal pipeline takes over (the user runs `/implement`). Otherwise hand off however the Destination section describes.
