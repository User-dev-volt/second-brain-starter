# Intent System PRD
**Project:** second-brain-starter
**Created:** 2026-05-14
**Status:** In progress — picking up in fresh context

---

## Vision

Build a **behavioral memory system** — not a note archive, not a preference list, but a living model of how Alec makes decisions. The end goal is Dark Factory-like agent behavior: agents that don't ask clarifying questions because they already know how Alec would answer, built from watching him answer the same *type* of question across enough sessions.

The north star principle:
> "The system should model decision-making patterns, not just store decisions."

---

## The Core Shift

Most second brain systems optimize for storage and retrieval. This system optimizes for **intent modeling**. The distinction:

- Storage asks: "What did he decide?"
- Intent modeling asks: "How does he consistently decide — and what does that reveal about his heuristics?"

The highest-quality evidence is not what Alec explicitly states he values. It is how he answers when the AI offers him a choice — because those answers are revealed preferences, not performed ones. Instinctive choices under mild pressure show more than deliberate design docs.

---

## Three-Document Structure

| Document | Captures | Used for |
|---|---|---|
| `soul.md` | Stable identity values — who he is | Tone, philosophy, long-term alignment |
| `user.md` | Profile facts — stack, projects, communication style | Context injection at session start |
| `intent.md` | Decision heuristics and tradeoff patterns — how he decides | Agent decision prediction (Dark Factory) |

`intent.md` is the new document and the most critical for the Dark Factory goal. It is not a list of traits. It is a living behavioral model.

---

## The Five-Layer Architecture (long-term)

1. **Raw Memory Layer** — everything: conversations, commits, decisions, session logs. Mostly immutable event log.
2. **Semantic Extraction Layer** — converts raw sessions into structured understanding. Tradeoff patterns, choice history, project context.
3. **Intent Graph Layer** — the soul of the system. Stable heuristics, dynamic intent, taste models, decision patterns. This becomes `intent.md` initially; evolves into a graph later.
4. **Simulation Layer** — "What would Alec decide?" Agents answer as a continuity of intent, not by querying memory.
5. **Governance / Drift Layer** — confidence scores, contradiction tracking, temporal weighting, versioned identity. Prevents fossilized outdated assumptions.

We are currently building Layers 1–2, with Layer 3 (`intent.md`) starting now.

---

## Evidence Model

### What evidence must capture

Evidence is not a surface decision with a quoted reason. Evidence is the **tradeoff structure**:

```
Project: second-brain-starter (goal: own every layer of the memory system)
Choice offered: LangChain (convenience, abstraction) vs. direct SDK (verbose, transparent)
Choice made: direct SDK
Reason: "I want to see exactly what's being sent"
Tradeoff type: control vs. convenience
Choice origin: AI clarifying question (instinctive, not deliberated)
```

### Evidence quality tiers

| Tier | Source | Quality |
|---|---|---|
| Highest | Response to AI clarifying question — instinctive choice between options | Revealed preference, no self-presentation |
| High | Unprompted mid-session decision that redirects work | Intent leak through behavior |
| Medium | Explicit decision with stated reasoning | Conscious preference, possibly performed |
| Low | Single mention, no decision attached | Accumulate only — never promote alone |

### Evidence minimum thresholds

- Cross-session pattern (2+ different days, same tradeoff type) → qualifies for `medium` confidence
- Single-session with 4+ evidence points of same tradeoff type → qualifies for `medium` (same-day bias noted — less reliable than cross-session)
- Cross-session with 4+ instances → `high` confidence
- Single-session single mention → never promotes, accumulates only

### Tradeoff types to track

- Control vs. convenience
- Ownership vs. delegation
- Speed vs. durability
- Depth vs. breadth (context-dependent — see pattern notes)
- Manual vs. automated
- Local vs. cloud (nuanced — see intent.md)
- Explicit vs. implicit (prefers things stated clearly vs. inferred)

---

## Intent Document Structure (`intent.md`)

```markdown
# Intent Document

## Decision Patterns

### [Pattern Name]
**Heuristic:** One-sentence rule that predicts future behavior.
**Tradeoff type:** What is being weighed against what.
**Observed:** How this manifests in behavior.
**Context modifiers:** When does this apply strongly vs. relax?
**Confirmed:** N times across N sessions
**Confidence:** low / medium / high
**Last seen:** YYYY-MM-DD
**Sessions:** [list of source log dates]
```

---

## Session Log Format (enriched — to be implemented in session-end-flush.py)

Current logs only capture summarized decisions. The new format must also capture:

```markdown
# Session: YYYY-MM-DD
**Project:** [project name]
**Session goal:** [what was being accomplished]

## [SessionEnd] HH:MM

**AI choices presented + responses:**
- Offered: [option A] vs. [option B]
  → Chose: [choice] — "[reason if stated]"
  → Tradeoff type: [control vs. convenience / etc.]

**Unprompted decisions:**
- [Decision made without being asked, with context]

**Decisions:**
- [Summarized key decisions]

**Lessons:**
- [Reusable patterns]

**Next Actions:**
- [Single most important next step]
```

This enriched format is what the extractor reads. Without project context and AI choice capture, the extraction quality degrades to surface-level.

---

## Proposal System

### How proposals reach documents

1. `memory_reflect.py` runs daily at 8 AM
2. Reads yesterday's enriched session log
3. Calls `proposal_extractor.py` which:
   - Loads existing proposals, `soul.md`, `user.md`, `intent.md`
   - Sends to Claude with structured prompt focused on tradeoff patterns
   - Filters suppressed proposals (already implemented or rejected)
   - Writes new proposals to `00_Meta/proposals/identity_proposals.md`
4. Alec reviews proposals in Obsidian — edits status field
5. Implemented proposals: manually copied to target document
6. Rejected proposals: status includes reason — system will not re-propose

### Proposal block schema

```markdown
---

### PROP-YYYY-MM-DD-NNN
**Target:** soul.md | user.md | intent.md
**Type:** add | update | deprecate
**Proposed:** [exact text to add or replace with]
**Current value:** [exact text being replaced, or _(none — new addition)_]
**Evidence:**
- YYYY-MM-DD [project] [tradeoff type]: [choice offered] → [choice made] — "[reason]"
**Source logs:** YYYY-MM-DD, YYYY-MM-DD
**Confidence:** medium | high
**Status:** pending
```

### Status values

- `pending` — awaiting review
- `implemented` — Alec added to target document manually
- `rejected — [reason]` — Alec rejected with reason; system suppresses re-proposal

### Suppression rules

- Implemented proposals: never re-propose same text
- Rejected proposals: read rejection reason as constraint; suppress unless evidence crosses higher threshold after rejection
- Single-session low-confidence observations: never reach proposals, accumulate only

---

## Governance Principles (critical — prevents system from becoming dangerous)

1. **Agents never write directly to intent/soul/user documents.** Always proposals → manual review → implemented.
2. **Rejected proposals teach the system.** The rejection reason is fed back as context on future extraction runs.
3. **Confidence decays.** A heuristic not confirmed in 60+ days should be flagged for re-validation, not assumed stable.
4. **Contradictions are surfaced, not resolved automatically.** When new evidence contradicts an existing `intent.md` entry, a `update` proposal is generated — Alec decides which version is current.
5. **The system models intent trajectory, not a frozen snapshot.** The 2026 version of Alec may reject 2025 heuristics. Temporal weighting matters.

---

## What Has Been Built

### Test infrastructure (`/.claude/tests/memory_reflect/`)
- 6 scenario fixtures: strong pattern, single session, contradiction, rejected repeat, implemented repeat, deprecate trigger
- Stubbed Claude responses for deterministic testing (no API calls)
- `test_runner.py` — auto-detects real vs stub extractor; validates field structure, suppression logic, confidence filtering

### `proposal_extractor.py` (`/.claude/scripts/`)
- Loads existing proposals, soul.md, user.md as Claude context
- Calls Claude Sonnet with extraction prompt
- Suppression check: blocks re-proposal of implemented/rejected items
- `format_proposals()` generates valid proposal blocks with sequential IDs
- `write_proposals()` appends to `identity_proposals.md`
- Mock injection interface for test compatibility

### `memory_reflect.py` (updated)
- Now runs proposal extractor as step 4 after existing learning/decision/idea promotions
- Targets: `VAULT_ROOT/00_Meta/proposals/identity_proposals.md`

---

## What Needs to Be Built Next

### Immediate (Phase 1 completion)
- [ ] Rewrite sample log fixtures with enriched format (project context + AI choice capture)
- [ ] Rewrite Claude response fixtures with tradeoff-structured evidence
- [ ] Rewrite extractor prompt to target intent patterns, not surface preferences
- [ ] Add `intent.md` as valid proposal target alongside soul.md / user.md
- [ ] Add `intent.md` fixture to test vault

### Phase 2 — Enriched session capture
- [ ] Update `session-end-flush.py` to extract and log AI clarifying questions + user responses
- [ ] Update extraction prompt to pull project name and session goal from context
- [ ] Cross-session pattern detection: memory_reflect.py looks at last 7–14 days, not just yesterday

### Phase 3 — Governance layer
- [ ] Confidence decay: flag intent.md entries not confirmed in 60+ days
- [ ] Contradiction detection: when new evidence conflicts with existing intent.md entry, generate update proposal automatically
- [ ] Rejection memory: feed rejection reasons back as constraints to future extraction runs

### Phase 4 — Simulation
- [ ] Intent document becomes queryable: "given this decision context, what does intent.md predict?"
- [ ] Agent reads intent.md before asking clarifying questions — only escalates when confidence < threshold or situation is novel
- [ ] Dark Factory behavior: agents operate with minimal clarification needed

---

## Open Questions for Next Session

1. Should `intent.md` be a flat markdown file initially, or start as structured YAML for queryability?
2. How should cross-session pattern detection work — does memory_reflect.py load N days of logs each run, or does it maintain a running accumulation file?
3. What's the right confidence decay window — 60 days? 90 days? Should it vary by heuristic type?
4. Should the proposal system support a `strengthen` type for intent.md — adding a new confirming instance to an existing pattern without changing the heuristic text?
5. What additional tradeoff types should be tracked beyond the initial list?

---

## Key Terminology

- **Behavioral memory** — storing how Alec decides, not what he decided
- **Revealed preference** — choices made in response to options, not explicitly stated values
- **Intent trajectory** — the direction preferences are moving over time, not a frozen snapshot
- **Dark Factory** — autonomous agent behavior driven by modeled intent, minimal human clarification needed
- **Tradeoff type** — the category of choice being made (control vs. convenience, depth vs. breadth, etc.)
- **Confidence decay** — heuristics that haven't been confirmed recently should lose weight, not persist indefinitely
