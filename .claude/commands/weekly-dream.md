Run the weekly dream synthesis for the second brain intent system.

This is a deep cross-session analysis. Take your time — look for patterns
that don't appear in any single day but emerge across the full week.

1. Execute: python "D:\second-brain-starter\.claude\scripts\weekly_dream_loader.py"
1b. Execute: python "D:\second-brain-starter\.claude\scripts\transcript_intent_loader.py" --mode weekly
   This prints the RAW INTENT LEDGER — Alec's VERBATIM user turns for the whole week
   across ALL projects, with flagged (⚑) questioning/redirect/rejection turns and their
   before→after causal context. It is the PRIMARY source for the two cross-session bullets
   in step 4: a deliberate habit like "one deep-dive per fresh session" is visible ONLY
   here — the per-session digested logs structurally cannot show an across-session pattern.
   Count repeated same-direction turns across sessions AND projects toward pattern and
   Standing-Order thresholds (cross-project recurrence raises confidence). Always confirm
   the digested logs didn't already capture a turn before counting it as newly surfaced.
   The ledger ends with a **RECURRING CORRECTIONS** block that already does this clustering
   for you: each ⟳ entry is a repeated correction with its session/project spread. Treat a
   cross-project ⟳⟳ cluster as a near-anchor — it is prime Standing-Order evidence (a value
   you re-assert across unrelated work), not a project-local tactic.
2. Execute: python "D:\second-brain-starter\.claude\scripts\consistency_check.py"
3. Read D:\Brain\00_Meta\bmad_rituals.md — the BMAD ritual whitelist. Whitelisted
   patterns are prescribed methodology, never behavioral evidence: never propose
   them, and ritual-execution instances count toward no proposal's gap/confirmation
   totals. From BMAD-mode sessions only deviations, methodology-open choices,
   redirections of agents, and edits to BMAD itself are signal.
4. Using the 7-day assembled context and consistency check input, identify:

   - **Tradeoff patterns** that resolved the same way 3+ times this week across
     any combination of evidence tiers (Critical, Highest, High, Medium).

   - **AI gap patterns** — the primary signal for Standing Order candidacy.
     A gap is *systematic* when the same tradeoff type resolves the same way
     3+ times across the week regardless of project context.
     For each systematic gap:
       - Name the tradeoff type and consistent resolution direction
       - Count total gap instances this week vs. all-time (from intent.md Gap accumulation)
       - Determine whether to add a new intent.md entry, strengthen an existing one,
         or propose a Standing Order if confidence is high and count ≥ threshold
     Systematic gaps with 4+ all-time instances at high confidence are Standing Order candidates.
     For Standing Order proposals: type "standing-order", current_value is the entry name,
     proposed text is the exact **Agent instruction:** directive (one actionable sentence).
     Evidence needs only 1 line referencing the promoted entry and its confirmation count.

   - **Scope expansion patterns** — what Alec kept adding unprompted across sessions.
     Recurring expansions in the same direction indicate deep values, not tactical choices.

   - **Procedural workflow patterns** for workflow.md — consistent session structure,
     sequencing choices, or execution habits that appear across 2+ sessions.
     Mine the RAW INTENT LEDGER (step 1b) for these — session-scoping habits, "new
     session" / "commit then new session" closers, and interrupts live only there.

   - **Cross-session signals** invisible to the daily cycle — things that appear
     2-3 times per week but never 4 times in a single day. The RAW INTENT LEDGER
     (step 1b) is the primary source; a same-direction turn recurring across 2+
     projects is stronger evidence than the same count within one project.

   - **intent.md contradictions** flagged by the consistency check.

5. Suppress duplicates against all existing proposals (pending, implemented, rejected).
   Proposals with status `deferred` may be strengthened but never re-proposed as new adds.

6. Write new proposals to:
   D:\Brain\00_Meta\proposals\identity_proposals.md
   using the PROP-YYYY-MM-DD-NNN schema and source "weekly-dream".

7. Write contradiction proposals as type 'contradiction' targeting intent.md.
