Run the daily memory synthesis for the second brain intent system.

1. Execute: python "D:\second-brain-starter\.claude\scripts\memory_reflect_loader.py"
2. Using the assembled context output, identify intent proposals following
   the tradeoff-structured evidence model in INTENT_SYSTEM_PRD.md.
3. For each proposal, check against existing implemented and rejected proposals
   — suppress duplicates.
4. Write new proposals to:
   D:\Obsidian Brain\Brain\00_Meta\proposals\identity_proposals.md
   using the PROP-YYYY-MM-DD-NNN schema.
5. Run a double monotonicity consistency check on the current intent.md.
   Write any contradictions as 'contradiction' type proposals.
