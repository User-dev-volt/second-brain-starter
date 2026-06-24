---
name: review-proposals
description: Walk Alec through pending intent/workflow proposals for approve/reject/defer decisions, promote approved entries into intent.md/workflow.md, and update statuses. Triggers on /review-proposals, "review my proposals", "what's pending in the intent system", or when Boot Up reports pending proposals.
argument-hint: [--target intent|workflow] [--quick]
---

# Proposal Review

Close the intent loop: turn pending proposals in `D:\Brain\00_Meta\proposals\identity_proposals.md` into accepted entries in `intent.md` / `workflow.md`, or reject them so reflect stops re-proposing.

## Files

| File | Role |
|------|------|
| `D:\Brain\00_Meta\proposals\identity_proposals.md` | Proposal queue (PROP-YYYY-MM-DD-NNN sections with `**Status:**` lines) |
| `D:\Brain\00_Meta\intent.md` | Standing Orders + Decision Patterns + Rejected Heuristics + Deferred |
| `D:\Brain\00_Meta\workflow.md` | BMAD Methodology (deliberate) + Workflow Patterns |
| `D:\Brain\00_Meta\bmad_rituals.md` | BMAD ritual whitelist — rejected-as-ritual patterns get a row here |
| `.claude\scripts\proposal_ranker.py` | Active-learning triage: scores pending proposals by readiness × impact, surfaces the few worth deciding, auto-defers the rest |

## Workflow

1. **Rank the queue (active-learning triage).** Run:
   `python "D:\second-brain-starter\.claude\scripts\proposal_ranker.py"`
   (add `--include-deferred` for a full sweep, `--all` to disable the evidence-floor
   suppression, `--top N` to widen the round). It parses every `pending` proposal,
   scores each by *readiness × impact*, and prints three groups:
   - **SURFACE** — the few highest-value decisions, best first. **This is the queue.**
   - **HOLD** — ready but outside this round's top-N; re-surfaces as evidence grows.
   - **AUTO-DEFER** — below the evidence floor (low confidence + <2 confirmations);
     not worth a decision yet.

   Present ONLY the SURFACE families. Report HOLD / AUTO-DEFER as one-line counts —
   never ask Alec about them. Skip `REFLECT-*` / `DREAM-*` markers. If SURFACE is
   empty, report "Queue clear" with the status counts the script prints, and stop.

   *Why this exists:* the loop stalls when proposals pile up faster than Alec reviews
   them. He is the only ground truth here, so the job is to spend his attention on the
   decisions that teach the system the most per click — not to make him triage noise.

2. **Collapse chains.** Within the SURFACE set, group `strengthen` / `standing-order`
   proposals with the base proposal they reference (`Strengthens:` / `Current value:`
   fields). Present each *pattern family* once, with the combined confirmation count
   and the newest evidence.

3. **Present for decision.** For each family, show: name, target file, heuristic/pattern
   text, tradeoff type, confidence, confirmation count, and the 2–3 strongest evidence
   lines. Then ask via AskUserQuestion (batch up to 4 families per call) with options:
   - **Accept** (at proposed confidence) — promote into the target file
   - **Accept as Standing Order** — only offer when confidence is high and 10+ confirmations
   - **Defer** — keep accumulating evidence
   - **Reject** — never re-propose; if the reason is "BMAD-prescribed", also add a row
     to `bmad_rituals.md`
   Recommend an option per family.

   **A/B framing for split decisions (preferred when the call isn't obvious).** When a
   family is a `contradiction`, or two credible phrasings/directions genuinely compete
   (a real tradeoff with evidence both ways), do NOT present a flat accept/reject. Use
   AskUserQuestion with two options **A** and **B**, each carrying `preview` text that
   shows the candidate side by side, and let Alec pick the better one. A two-way
   comparison is a faster, more reliable judgment than rating a single naked assertion —
   he reacts instead of reconstructing. The chosen side is promoted; for a contradiction
   the losing side is recorded under Rejected, otherwise the unchosen phrasing is dropped.

   `--quick` mode: layer on the ranker — present only the top 3 SURFACE families and
   auto-defer the rest.

4. **Apply decisions.**
   - **Accepted intent entries** → `intent.md` → Decision Patterns, using the entry
     format already in the file (Heuristic, Tradeoff type, Confidence, Confirmed,
     Standing order, Source proposals, Last confirmed).
   - **Standing Orders** → `intent.md` → Standing Orders with the exact
     **Agent instruction:** directive and **Active since:** today.
   - **Accepted workflow entries** → `workflow.md` → Workflow Patterns.
   - **Rejected** → add to `intent.md` → Rejected Heuristics with date + reason
     (+ `bmad_rituals.md` row when the reason is methodology).
   - **Deferred** → list under `intent.md` → Deferred.

5. **Update statuses.** Rewrite each decided proposal's `**Status:**` line:
   - `implemented YYYY-MM-DD → <file> (<section>)`
   - `rejected YYYY-MM-DD — <reason>`
   - `deferred YYYY-MM-DD — accumulate more evidence before encoding`
   Use a Python script over the file (match `### PROP-` headers, replace the Status
   line inside each section) rather than hand-editing when more than ~3 statuses change.

6. **Confirm.** Report: N accepted (list names + destinations), N rejected, N deferred,
   and remind that Standing Orders take effect next session via the session-start hook.

## Rules

- Never decide for Alec — every promotion/rejection goes through the question flow.
- Surfacing is bounded by `proposal_ranker.py` (active learning): never present more
  than the SURFACE list. Auto-deferred items are not *decided*, only not *asked* this
  round — they re-surface automatically once new evidence raises their score.
- Never delete proposal sections; statuses are the history.
- A `strengthen` of an already-implemented entry updates that entry's Confirmed count,
  Last confirmed date, and (if proposed) confidence — it does not create a duplicate.
- A `contradiction` proposal presents both sides and asks which way to resolve;
  resolution edits the existing entry and records the losing side under Rejected.
