# Intent System PRD — Second Brain Overhaul
**Project:** second-brain-starter
**Created:** 2026-05-14
**Updated:** 2026-05-15
**Status:** Finalized — ready to build

---

## Vision

Overhaul the existing second brain memory system into a **behavioral intent engine** — not a note archive, not a preference list, but a living model of how Alec makes decisions. The end goal is Dark Factory-like agent behavior: agents that don't ask clarifying questions because they already know how Alec would answer, built from watching him answer the same *type* of question across enough sessions.

This is not a new parallel system. Every change described here modifies or extends the existing structure in `second-brain-starter` and the vault at `D:\Obsidian Brain\Brain\`.

The north star:
> "The system should model decision-making patterns, not just store decisions."

---

## What We're Overhauling and Why

The current system captures:
- **Decisions** — what was chosen (no tradeoff structure)
- **Lessons** — technical patterns (stripped of context intentionally)
- **Next Actions** — task tracking

These are correct for what they were built for. They are insufficient for intent modeling because they record the *what* and discard the *how you decided* — which is the only part that matters for the Dark Factory goal.

The overhaul adds intent-bearing signal capture at every stage of the pipeline without breaking what already works.

---

## Document Structure — Vault Additions

Three documents exist today: `soul.md`, `user.md`, `MEMORY.md`. Two are being added:

| Document | Location | Captures | Used for |
|---|---|---|---|
| `soul.md` | `00_Meta/` | Stable identity values — who Alec is | Tone, philosophy, long-term alignment |
| `user.md` | `00_Meta/` | Profile facts — stack, projects, communication style | Context injection at session start |
| `MEMORY.md` | `00_Meta/` | Promoted decisions and facts | Existing — unchanged |
| **`intent.md`** | `00_Meta/` | Decision heuristics, tradeoff patterns — how Alec decides | Agent decision prediction → Dark Factory |
| **`workflow.md`** | `00_Meta/` | Procedural patterns — how Alec structures and executes work | Agent execution calibration |

`intent.md` is the core new document. `workflow.md` is the procedural layer — separate from values/preferences because *how you work* is distinct from *what you believe*.

### intent.md entry structure

```markdown
## Decision Patterns

### [Pattern Name]
**Heuristic:** One-sentence rule that predicts future behavior.
**Tradeoff type:** What is being weighed against what.
**Observed:** How this manifests in behavior.
**Context modifiers:** When does this apply strongly vs. relax?
**Confirmed:** N times across N sessions
**Confidence:** low | medium | high
**Last confirmed:** YYYY-MM-DD
**Sessions:** [list of source log dates]
**Standing order:** no | proposed | active
```

### workflow.md entry structure

```markdown
## Workflow Patterns

### [Workflow Name]
**Pattern:** What Alec consistently does when facing this type of work.
**Observed:** Specific behavioral examples.
**Confirmed:** N times across N sessions
**Confidence:** medium | high
**Last confirmed:** YYYY-MM-DD
```

---

## Evidence Model

### The core principle

Evidence is not a surface decision with a quoted reason. Evidence is the **tradeoff structure** — what was offered, what was chosen, what type of choice it was, and where the choice came from.

```
Project: second-brain-starter (goal: own every layer of the memory system)
Choice offered: LangChain (convenience) vs. direct SDK (transparent, verbose)
Choice made: direct SDK
Reason: "I want to see exactly what's being sent"
Tradeoff type: control vs. convenience
Choice origin: AI clarifying question — instinctive, not deliberated
```

### Evidence quality tiers

| Tier | Source | Signal strength |
|---|---|---|
| **Critical** | "Actually", "wait", "stop" — mid-session self-correction | Non-negotiable preference overriding stated intent. Highest quality. |
| **Highest** | Response to AI clarifying question — instinctive choice | Revealed preference, no self-presentation, mild pressure |
| **High** | Unprompted scope expansion — adding something not requested | Interest and value leak through behavior |
| **High** | AI gap — Claude default diverged from Alec's choice | Systematic divergence from AI defaults reveals stable preference |
| **Medium** | Unprompted mid-session redirection | Intent expressed through correction |
| **Medium** | Explicit rejection of AI suggestion with stated reason | Conscious preference, possibly performed |
| **Low** | Single mention, no decision attached | Accumulate only — never promote alone |

### Evidence confidence thresholds

- **Cross-session** (2+ different days, same tradeoff type) → qualifies for `medium`
- **Single-session** with 4+ evidence points of same tradeoff type → `medium` (same-day bias flagged)
- **Cross-session** with 4+ confirmed instances → `high`
- **Single-session single mention** → never promotes, accumulates only

### Tradeoff types to track

- Control vs. convenience
- Ownership vs. delegation
- Speed vs. durability
- Depth vs. breadth *(context-dependent — exploration phase vs. execution phase)*
- Manual vs. automated
- Local vs. cloud *(nuanced: data sovereignty vs. infrastructure pragmatism)*
- Explicit vs. implicit

---

## Pipeline — Full Overhaul

```
Raw transcript (JSONL)
    ↓
session-end-flush.py  [OVERHAUL]
    → Enriched daily log with:
        - Project + session goal + session type
        - AI choices presented + user responses (tradeoff type classified)
        - "Actually" / "wait" / "stop" moments (flagged as Critical tier)
        - AI gaps (Claude default → Alec choice)
        - Scope expansions (unprompted additions)
        - Scope constraints (explicit deferrals)
        - Decisions / Lessons / Next Actions (existing — unchanged)
    ↓
Daily log: 00_Meta/daily/YYYY-MM-DD.md
    ↓
memory_reflect.py  [OVERHAUL — daily at 8 AM]
    → Reads yesterday's enriched log
    → Reads last 30 days of logs (raw preservation window)
    → Calls proposal_extractor.py
    → Runs consistency check on intent.md
    → Archives HABITS / resets for today
    ↓
proposal_extractor.py  [OVERHAUL]
    → Targets: soul.md, user.md, intent.md, workflow.md
    → Evidence structured as tradeoff pairs, not surface decisions
    → Suppresses implemented and rejected proposals
    → Writes to 00_Meta/proposals/identity_proposals.md
    ↓
weekly_dream.py  [NEW — weekly, Sonnet + High thinking]
    → Reads 7 days of enriched logs
    → Runs cross-session pattern synthesis
    → Identifies patterns invisible to daily cycle
    → Generates higher-confidence proposals
    → Runs double monotonicity consistency check across intent.md
    ↓
identity_proposals.md  [Obsidian — manual review]
    → Alec reviews: pending → implemented | rejected — <reason>
    → Implemented: manually copied to target document
    → Rejected: reason fed back as constraint on future extraction
    ↓
intent.md matures → entries promoted to Standing Orders
    ↓
Agents read intent.md + Standing Orders before acting
    → Only escalates when confidence < threshold or novel situation
    ↓
Dark Factory
```

---

## Files Being Modified or Created

### `session-end-flush.py` — OVERHAUL

**Current extraction prompt (Haiku, 512 tokens):**
Produces Decisions / Lessons / Next Actions.

**New extraction prompt — two-stage:**

Stage 1 — intent signals (new, runs first):
```
Project: [name from cwd or session mention]
Session goal: [what this session was trying to accomplish]
Session type: designing | building | debugging | exploring

**Critical moments:**
(Capture any instance of "actually", "wait", "stop", or equivalent self-correction)
- [what Claude was doing] → [what Alec corrected to] — "[words used]"

**AI choices + responses:**
- Offered: [A] vs [B] → Chose: [choice] — "[reason if stated]"
  Tradeoff: [type]

**AI gaps (Claude default → Alec preference):**
- Claude heading toward: [X] → Alec redirected to: [Y]
  Gap type: [tradeoff type]

**Scope expansions (unprompted additions):**
- Added: [what] — [context]

**Scope constraints (explicit deferrals):**
- Deferred: [what] — "[reason]"
```

Stage 2 — existing capture (unchanged):
```
**Decisions:** key choices made
**Lessons:** reusable technical patterns
**Next Actions:** single most important next step
```

**Model:** Keep Haiku for cost. The prompt is more structured, not more expensive.

---

### `memory_reflect.py` — SPLIT INTO TWO MODES

The daily synthesis and weekly dream **do not make API calls**. Instead they become prompt assemblers — Python scripts that read files and structure context, then hand off to Claude Code running in a manual terminal session. This routes the expensive AI work through the subscription rather than the API.

#### Token routing decision

| Job | Mechanism | Model | Tokens |
|---|---|---|---|
| Session flush | Automated hook — must be headless | Haiku API | API (cheap, keep as-is) |
| Daily reflect | Manual: `/daily-reflect` slash command | Sonnet (subscription) | Subscription |
| Weekly dream | Manual: `/weekly-dream` slash command | Sonnet + High thinking | Subscription |

Session flush stays as API because hooks run headless — there is no Claude Code session available. Daily and weekly synthesis require you to open a terminal and trigger them manually, which is intentional.

**Optional fallback:** The Task Scheduler jobs (`SecondBrain\DailyReflect`, `SecondBrain\WeeklyDream`) can remain as lower-quality Haiku API fallbacks for days when the manual command isn't run. On days you run the slash command, it supersedes the scheduled job.

---

#### `memory_reflect_loader.py` — NEW (replaces the AI call in memory_reflect.py)

A pure Python file-reader. No AI call. Assembles and prints the full synthesis prompt to stdout so Claude Code can consume it.

**What it loads:**
- Yesterday's enriched daily log
- Last 30 days of daily logs (raw preservation window)
- Current `intent.md`, `workflow.md`, `soul.md`, `user.md`
- Existing `identity_proposals.md` (implemented + rejected — for suppression context)

**Output:** Structured prompt text piped into the `/daily-reflect` slash command context.

---

#### `/daily-reflect` slash command (`.claude/commands/daily-reflect.md`)

```markdown
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
```

Claude Code reads this, calls the loader script (file reads only), receives the assembled context, and processes everything using subscription tokens. Writes proposals directly using its Write tool.

---

#### `/weekly-dream` slash command (`.claude/commands/weekly-dream.md`)

Same pattern but loads 7 days and instructs Claude to use deeper cross-session synthesis. Claude Code's extended thinking is available through the subscription — no separate API configuration needed.

```markdown
Run the weekly dream synthesis for the second brain intent system.

This is a deep cross-session analysis. Take your time — look for patterns
that don't appear in any single day but emerge across the full week.

1. Execute: python "D:\second-brain-starter\.claude\scripts\weekly_dream_loader.py"
2. Using the 7-day assembled context, identify:
   - Tradeoff patterns that resolved the same way 3+ times this week
   - AI gap patterns — where Claude's defaults consistently diverged from Alec's choices
   - Scope expansion patterns — what Alec kept adding unprompted
   - Procedural workflow patterns for workflow.md
   - Cross-session signals invisible to the daily cycle
3. Suppress duplicates against existing proposals.
4. Write proposals to identity_proposals.md.
5. Run full double monotonicity consistency check across all of intent.md.
   Flag any logical contradictions as 'contradiction' proposals.
```

**Changes to memory_reflect.py (remaining automated portion):**
1. Remove the Claude API call — synthesis moves to the slash commands.
2. Keep: HABITS archive + reset (no AI needed).
3. Keep: project snapshot timestamp update (no AI needed).
4. Keep: git auto-commit trigger.
5. Optional: run Haiku fallback synthesis if manual command hasn't run today (check for today's proposals in identity_proposals.md as a marker).

---

### `proposal_extractor.py` — OVERHAUL

**Changes:**
1. Add `intent.md` and `workflow.md` as valid proposal targets alongside `soul.md` and `user.md`.
2. Rewrite Claude prompt to extract tradeoff patterns and procedural patterns, not surface preferences.
3. Evidence format uses tradeoff structure (offered/chosen/type/origin) not quoted reasons.
4. Read and pass existing `intent.md` entries to Claude so it knows what's already captured.
5. Suppression checks extended to cover all four target documents.

**New extraction prompt focus:**
```
For each session, identify:
1. What project was active and what was the session goal?
2. What binary or multiple-choice questions did the AI ask? What did the user pick?
   Classify the tradeoff type for each.
3. Were there any "actually", "wait", or "stop" moments? What was being corrected?
4. Where did Claude's default direction diverge from what the user chose?
5. Did the user expand scope unprompted? In what direction?
6. Do these signals, across the session, confirm an existing intent.md pattern
   or suggest a new one?

Only propose if:
- 2+ evidence points of the same tradeoff type (same session)
- OR 1+ evidence point confirming an existing intent.md pattern
  (cross-session confirmation)
```

---

### `weekly_dream.py` — NEW

**Purpose:** Cross-session pattern synthesis. Finds patterns invisible to the daily cycle — things that appear 2-3 times per week but never 4 times in one day.

**Schedule:** Weekly, Sundays at 6 AM (via Windows Task Scheduler, `SecondBrain\WeeklyDream`)

**Model:** `claude-sonnet-4-6` with extended thinking enabled, `budget_tokens: 10000` (High thinking)

**Why High thinking:** Cross-session synthesis requires holding 7 days of signal simultaneously, finding non-obvious patterns, and checking logical consistency across the entire intent.md. This is exactly the task extended thinking was designed for.

**What it does:**
1. Loads all daily logs from the past 7 days
2. Loads current `intent.md`, `workflow.md`, `soul.md`, `user.md`
3. Loads all pending and implemented proposals from the past 30 days
4. Calls Claude Sonnet with High thinking to:
   - Identify patterns across sessions that didn't surface in daily reflects
   - Find tradeoff types that resolved the same way 3+ times across the week
   - Identify procedural workflow patterns across multiple session types
   - Run double monotonicity check on intent.md (see below)
5. Writes proposals to `identity_proposals.md` with source `weekly-dream`
6. Writes consistency check results — contradictions become `update` proposals

**API call structure:**
```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000
    },
    messages=[{"role": "user", "content": weekly_prompt}]
)
```

---

### `consistency_check.py` — NEW (called by both memory_reflect and weekly_dream)

**Purpose:** Double monotonicity check on `intent.md` entries. Prevents the intent model from accumulating logically contradictory heuristics.

**What double monotonicity means here:**
If intent.md says:
- A: "Prefers control over convenience"
- B: "Prefers speed over setup cost"

These can contradict for the same decision scenario. The check identifies pairs of entries that would produce contradictory predictions for the same tradeoff type and surfaces them as `update` proposals for Alec to resolve manually.

**Output:** Contradiction pairs written to `identity_proposals.md` as `update` type with target `intent.md`.

---

### `identity_proposals.md` — EXTENDED

**New proposal types for intent.md and workflow.md:**

```markdown
---

### PROP-YYYY-MM-DD-NNN
**Target:** intent.md | workflow.md | soul.md | user.md
**Type:** add | update | deprecate | strengthen | contradiction
**Source:** daily-reflect | weekly-dream | consistency-check
**Proposed:** [exact text to add or replace with]
**Current value:** [exact text being replaced, or _(none — new addition)_]
**Evidence:**
- YYYY-MM-DD [project] [tradeoff type] [tier]: [offered] → [chosen] — "[reason]"
**Source logs:** YYYY-MM-DD, YYYY-MM-DD
**Confidence:** medium | high
**Status:** pending
```

**New type: `strengthen`**
For intent.md — adds a new confirming instance to an existing pattern without changing the heuristic text. Increases confirmation count and updates `last confirmed` date.

**New type: `contradiction`**
Generated by consistency_check.py when two intent.md entries produce contradictory predictions. Alec resolves which version is current.

**New source field:** Tracks whether the proposal came from daily-reflect, weekly-dream, or consistency-check. Weekly-dream proposals carry higher cross-session confidence.

---

## Gap Tracking — Implementation

Gap tracking captures the systematic divergence between Claude's default behavior and Alec's actual preferences. This is the highest-quality signal for building the intent model because it requires no self-reflection from Alec — the preference is revealed purely through correction.

**How it flows in:**

1. `session-end-flush.py` captures AI gaps in the enriched daily log:
```
**AI gaps (Claude default → Alec preference):**
- Claude heading toward: pre-built framework → Alec chose: custom build
  Gap type: ownership vs. convenience
- Claude drafted: auto-approval logic → Alec redirected: manual gate
  Gap type: automation vs. oversight
```

2. `proposal_extractor.py` treats AI gap evidence as `High` tier — one tier above explicit decisions, one tier below critical self-corrections.

3. Over time, recurring gap types with consistent resolution direction → `intent.md` entry with high confidence.

4. `weekly_dream.py` synthesizes gap patterns across 7 days — identifies which gap types are *systematic* (Claude consistently defaults away from Alec's preference in this category).

**Long-term use:** When enough gap data accumulates for a tradeoff type, agents can pre-correct — stop defaulting to the Claude baseline and default instead to the Alec-pattern baseline. That is the Dark Factory shift: the agent's default becomes Alec's preference, not the model's.

---

## Standing Orders — Promotion Path

The explicit promotion path from evidence to autonomous agent behavior:

```
Evidence (tradeoff instances)
    ↓
Pattern confirmed in intent.md (medium confidence)
    ↓
Pattern strengthened across sessions (high confidence)
    ↓
Promoted to Standing Order (proposal type: standing-order)
    ↓
Alec approves: implemented as Standing Order in intent.md
    ↓
Agents read Standing Orders before acting
    → Skip clarification for this tradeoff type
    → Only escalate if confidence < threshold or situation is novel
```

Standing Orders are the Dark Factory end state made explicit. An agent with enough Standing Orders stops asking — it operates on known intent until it encounters something genuinely outside the model.

**Standing Order format in intent.md:**
```markdown
### [Pattern Name]
...
**Standing order:** active
**Active since:** YYYY-MM-DD
**Agent instruction:** [Exact behavioral directive the agent follows without asking]
```

---

## Raw Log Preservation — 30-Day Window

Per the MemMachine ground-truth preservation principle: extraction is lossy. If the extraction logic improves, it should be possible to re-process raw logs.

**Implementation:**
- Daily logs in `00_Meta/daily/` are never deleted within 30 days
- `memory_reflect.py` loads the past 30 days of logs on each run (not just yesterday)
- If a new tradeoff type is added to the extractor, the 30-day window allows back-filling without lost signal
- After 30 days, logs remain in the vault as historical record but are no longer actively re-processed

---

## Governance — Non-Negotiable Rules

1. **Agents never write directly to intent/soul/user/workflow documents.** Always: evidence → proposal → manual review → implemented.
2. **Rejected proposals teach the system.** Rejection reason is fed back as constraint on future extraction runs.
3. **Confidence decays.** Intent.md entries not confirmed in 60 days are flagged for re-validation — not assumed stable.
4. **Contradictions are surfaced, never auto-resolved.** Consistency check generates `contradiction` proposals. Alec resolves.
5. **The system models intent trajectory, not a frozen snapshot.** 2026 Alec may reject 2025 heuristics. Temporal weighting is built into confidence decay.
6. **Standing Orders require explicit approval.** Never auto-promoted. Alec must review and mark `active`.

---

## What Has Already Been Built

### Test infrastructure (`/.claude/tests/memory_reflect/`)
- 6 scenario fixtures covering: strong pattern, single session, contradiction, rejected repeat, implemented repeat, deprecate trigger
- Deterministic stubbed Claude responses — no API calls in tests
- `test_runner.py` — auto-detects real vs stub extractor; validates field structure, suppression logic, confidence filtering

### `proposal_extractor.py` (`/.claude/scripts/`)
- Loads existing proposals, soul.md, user.md as Claude context
- Calls Claude Sonnet with extraction prompt
- Suppression: blocks re-proposal of implemented/rejected items
- `format_proposals()` — sequential IDs, no collisions with existing
- `write_proposals()` — appends to identity_proposals.md
- Mock injection interface for test compatibility

### `memory_reflect.py` (updated)
- Runs proposal extractor as step 4 after existing promotions
- Targets: `VAULT_ROOT/00_Meta/proposals/identity_proposals.md`

---

## Build Plan

### Phase 1 — Intent foundation
- [ ] Create `intent.md` and `workflow.md` in vault `00_Meta/`
- [ ] Overhaul `session-end-flush.py` extraction prompt — add enriched intent-signal sections
- [ ] Build `memory_reflect_loader.py` — file reader, no AI call, outputs structured prompt
- [ ] Build `/daily-reflect` slash command (`.claude/commands/daily-reflect.md`)
- [ ] Strip AI call from `memory_reflect.py` — keep HABITS, snapshot, git auto-commit
- [ ] Overhaul `proposal_extractor.py` — add intent.md/workflow.md targets, tradeoff-structured evidence, new prompt
- [ ] Update test fixtures — enriched log format, tradeoff-structured Claude responses
- [ ] Add `intent.md` and `workflow.md` to fixture vault

### Phase 2 — Weekly Dreaming
- [ ] Build `weekly_dream_loader.py` — 7-day file loader, no AI call, outputs structured prompt
- [ ] Build `/weekly-dream` slash command (`.claude/commands/weekly-dream.md`)
- [ ] Build `consistency_check.py` — double monotonicity check logic, contradiction proposals
- [ ] Wire consistency check into both slash commands
- [ ] Remove `SecondBrain\WeeklyDream` Task Scheduler job (replaced by manual slash command)
- [ ] Optional: keep `SecondBrain\DailyReflect` as Haiku fallback on days `/daily-reflect` isn't run manually

### Phase 3 — Gap tracking
- [ ] Add AI gap capture section to session-end-flush.py enriched prompt
- [ ] Add gap evidence tier to slash command synthesis instructions (High tier, below Critical)
- [ ] Add weekly gap pattern synthesis to `/weekly-dream` instructions
- [ ] Add gap accumulation tracking to intent.md entries

### Phase 4 — Standing Orders
- [ ] Add `standing-order` proposal type to proposal schema
- [ ] Add Standing Order section to intent.md format
- [ ] Build Standing Order reader — agents load Standing Orders at session start via context hook
- [ ] Define escalation logic — when does an agent override a Standing Order and ask

### Phase 5 — Dark Factory
- [ ] Agents default to Alec-preference baseline for known tradeoff types
- [ ] Escalation only for: confidence below threshold, novel tradeoff type, explicit override
- [ ] Full autonomous operation within defined intent boundaries

---

## Open Questions

1. Should `intent.md` start as flat markdown or structured YAML? Markdown is readable in Obsidian now; YAML is queryable later. Lean toward markdown with consistent headers that are parseable.
2. What is the right confidence decay window — 60 days? 90 days? Should it vary by heuristic type (stable values decay slower than tactical preferences)?
3. Should the weekly Dreaming pass also synthesize across `workflow.md` or focus on `intent.md` first?
4. At what confirmation count does an intent.md entry become eligible for Standing Order promotion — 10 instances? 20?
5. How does the agent escalation threshold work — is it per tradeoff-type confidence score, or global?

---

## Key Terminology

- **Behavioral memory** — storing how Alec decides, not what he decided
- **Revealed preference** — choices made in response to options, not explicitly stated values
- **Tradeoff type** — the category of choice being made (control vs. convenience, depth vs. breadth, etc.)
- **AI gap** — the divergence between Claude's default direction and Alec's actual choice; accumulated gaps reveal systematic preferences
- **Critical moment** — an "actually", "wait", or "stop" self-correction; highest-tier evidence because it reveals a non-negotiable preference overriding stated intent
- **Scope expansion** — unprompted addition of something not in scope; reveals what Alec can't resist building, indicating deep values
- **Dreaming** — weekly cross-session synthesis pass using Sonnet + High thinking; finds patterns invisible to the daily cycle
- **Double monotonicity** — logical consistency check on intent.md entries; ensures heuristics don't contradict each other across the same tradeoff type
- **Standing Order** — a mature intent.md entry promoted to an active agent directive; the agent follows it without asking
- **Dark Factory** — the end state: agents operating autonomously within Alec's intent boundaries, escalating only for genuinely novel situations
- **Intent trajectory** — the direction preferences are moving over time, not a frozen snapshot; the system tracks evolution, not just current state
- **Confidence decay** — heuristics not confirmed recently lose weight rather than persisting indefinitely; prevents fossilized outdated assumptions
