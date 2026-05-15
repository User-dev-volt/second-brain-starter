Run the weekly dream synthesis for the second brain intent system.

This is a deep cross-session analysis. Take your time — look for patterns
that don't appear in any single day but emerge across the full week.

1. Execute: python "D:\second-brain-starter\.claude\scripts\weekly_dream_loader.py"
2. Execute: python "D:\second-brain-starter\.claude\scripts\consistency_check.py"
3. Using the 7-day assembled context and consistency check input, identify:
   - Tradeoff patterns that resolved the same way 3+ times this week
   - AI gap patterns — where Claude's defaults consistently diverged from Alec's choices
   - Scope expansion patterns — what Alec kept adding unprompted
   - Procedural workflow patterns for workflow.md
   - Cross-session signals invisible to the daily cycle
   - Any intent.md contradictions flagged by the consistency check
4. Suppress duplicates against all existing proposals (pending, implemented, rejected).
5. Write new proposals to:
   D:\Obsidian Brain\Brain\00_Meta\proposals\identity_proposals.md
   using the PROP-YYYY-MM-DD-NNN schema and source "weekly-dream".
6. Write any contradiction proposals as type 'contradiction' targeting intent.md.
