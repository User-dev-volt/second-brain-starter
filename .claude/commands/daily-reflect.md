Run the daily memory synthesis for the second brain intent system.

1. Execute: python "D:\second-brain-starter\.claude\scripts\memory_reflect_loader.py"
2. Execute: python "D:\second-brain-starter\.claude\scripts\consistency_check.py"
3. Using the assembled context and consistency check output, identify intent proposals.

   Evidence tier ranking (highest to lowest signal quality):
   - **Critical** — "actually", "wait", "stop", or any mid-session self-correction.
     Overrides stated intent. One instance qualifies for proposal if pattern exists in intent.md.
   - **Highest** — Response to an AI clarifying question. Instinctive, unguarded choice.
   - **High (AI gap)** — Claude heading toward X, Alec redirected to Y.
     AI gaps are the strongest *passive* signal — no self-reflection required, no performance.
     When the **AI gaps** section has entries, treat each as High-tier evidence.
     Two gaps resolving the same tradeoff type the same way → qualifies for proposal.
   - **High** — Unprompted scope expansion. Reveals what Alec can't resist adding.
   - **Medium** — Explicit rejection of AI suggestion with stated reason.
   - **Low** — Single mention, no decision attached. Accumulate only, never promote alone.

4. For intent.md proposals: if AI gap instances exist for the same tradeoff type as
   an existing entry, propose type "strengthen" rather than a new "add".
   Include a **Gap accumulation:** line in the proposed text:
     **Gap accumulation:** N gaps — [tradeoff type] → [direction] each time (YYYY-MM-DD, ...)

   If an existing intent.md entry has confidence "high" and 10+ confirmed instances
   (check **Confirmed:** and **Gap accumulation:** fields combined), propose
   type "standing-order" instead of "strengthen". The proposed text is the exact
   **Agent instruction:** directive Alec should add to the entry — a single
   actionable sentence an agent can follow without asking. Set current_value to
   the entry name being promoted. Evidence needs only 1 line referencing the entry.

5. Suppress implemented and rejected duplicates.

6. Write new proposals to:
   D:\Brain\00_Meta\proposals\identity_proposals.md
   using the PROP-YYYY-MM-DD-NNN schema.

7. Use the consistency check output to flag contradictions.
   Write any as type 'contradiction' targeting intent.md.
