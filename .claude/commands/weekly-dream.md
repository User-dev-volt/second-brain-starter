Run the weekly dream synthesis for the second brain intent system.

This is a deep cross-session analysis. Take your time — look for patterns
that don't appear in any single day but emerge across the full week.

1. Execute: python "D:\second-brain-starter\.claude\scripts\weekly_dream_loader.py"
2. Execute: python "D:\second-brain-starter\.claude\scripts\consistency_check.py"
3. Using the 7-day assembled context and consistency check input, identify:

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

   - **Cross-session signals** invisible to the daily cycle — things that appear
     2-3 times per week but never 4 times in a single day.

   - **intent.md contradictions** flagged by the consistency check.

4. Suppress duplicates against all existing proposals (pending, implemented, rejected).

5. Write new proposals to:
   D:\Brain\00_Meta\proposals\identity_proposals.md
   using the PROP-YYYY-MM-DD-NNN schema and source "weekly-dream".

6. Write contradiction proposals as type 'contradiction' targeting intent.md.
