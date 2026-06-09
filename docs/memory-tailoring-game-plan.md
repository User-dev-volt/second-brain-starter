# Memory Tailoring Game Plan — 2026-06-09

Goal: make the second brain genuinely learn how Alec decides (Intent), separate BMAD's
deliberate rituals from real behavioral signal, and give the AI eyes (Playwright for web,
Godot MCP for games) so it can verify its own work.

---

## Findings (current state audit)

1. **The Intent loop has never closed.** Capture works beautifully — the Stop hook extracts
   intent signals (critical moments, AI gaps, scope expansions) into rich daily logs, and
   daily-reflect/weekly-dream have generated **31 proposals**. But **all 31 are `pending`**,
   and `intent.md` + `workflow.md` are completely empty. No review step exists, so nothing
   ever gets promoted, no Standing Orders activate, and the agent never actually changes
   behavior. The whole back half of the pipeline is unbuilt.

2. **BMAD methodology is contaminating the proposal stream.** Proposals like "BMAD
   Story-First Workflow," "Adversarial Code Review Gate," and "Pre-existing Failure
   Baseline" are *BMAD's scripted process*, not Alec's personal heuristics. Gap counts are
   inflated by BMAD ritual repetition (e.g., "Exhaustive Artifact Analysis" at ~23
   confirmations, mostly from story-design sessions where exhaustive analysis is the
   prescribed step). The extractor has no concept of "this session was running a
   methodology on purpose."

3. **No session-mode awareness.** BMAD story loops, freeform dev, and Excel/work sessions
   all go through the identical Haiku extraction prompt and the same learnings routing.

4. **Godot MCP is dead.** It's registered only under the deleted
   `D:/Obsidian Brain/Brain/10_Active_Projects/Project_Chimera` path. Since the migration
   to `D:\Projects\Project_Chimera`, no session can reach it.

5. **Playwright MCP is minimal.** Pinned to `@playwright/mcp@0.0.70`, headless,
   default caps only — no vision, devtools, testing assertions, traces, video, or
   persistent profile. No skills wrap it, so every "check this site" session reinvents
   the procedure.

6. **Hygiene:** a GitHub PAT sits in plaintext inside a permission allow-rule in the
   global `settings.json` / project `settings.local.json` (rotate it); the Anthropic API
   key lives in `settings.local.json` (untracked — fine — but rotate-aware); stale
   "Obsidian Brain" permission rules and `.claude.json` project entries linger.

---

## Pillar 1 — Close the Intent loop (review → promote → act → propose)

This is the highest-leverage work. Everything else feeds it.

### 1a. `/review-proposals` skill (the missing back half)
Interactive triage of `00_Meta/proposals/identity_proposals.md`:
- Present pending proposals one at a time (or batched by target) with evidence summary.
- Per proposal: **approve / reject (with reason) / defer / edit-then-approve**.
- On approve: write the entry into `intent.md` or `workflow.md` in the documented format,
  set proposal `Status: implemented`.
- On reject: `Status: rejected` + reason (daily-reflect already suppresses rejected
  duplicates — this finally makes that suppression do something).
- First run = clear the 31-proposal backlog (~30 min of Alec's time, one-time).

### 1b. Standing Orders actually injected at session start
- `session-start-context.py` (UserPromptSubmit hook) should inject: active Standing
  Orders + top high-confidence Decision Patterns (compact, ~10 lines max) into every
  session, tagged by relevance to the current project/mode.
- `standing_order_reader.py` already exists — wire it in and verify output format.

### 1c. Propose-then-act behavior ("it knows how I'd answer")
- Add a section to SOUL.md: when a decision matches a Decision Pattern at high
  confidence, the agent states *"Per your [pattern name], I'd do X — proceeding unless
  you say otherwise"* and continues. Medium confidence → propose and wait for go-ahead.
  Standing Orders → just act, cite the order.
- Every time Alec accepts a proposal-in-the-moment, that's a **Confirmed** instance;
  every override is counter-evidence. Add both to the extraction prompt so the
  confidence numbers feed themselves.

### 1d. Automate the reflect cadence
- The scheduled task only prints a reminder. Use the bmad-story-loop pattern (headless
  `claude -p "/daily-reflect"`) via Task Scheduler or the Session Manager so synthesis
  runs nightly without Alec.
- Add to Boot Up protocol: report "N proposals pending review" so the queue is visible
  and review happens weekly instead of never.

## Pillar 2 — BMAD-aware memory (separate ritual from signal)

### 2a. Session mode detection at capture time
In `session-end-flush.py`, detect mode before calling Haiku:
- **bmad** — cwd has `_bmad/` or `_bmad-output/`, or transcript contains BMAD/story-loop
  markers (`/bmad-`, story file paths, `gds-` commands).
- **work** — cwd outside `D:\Projects` (e.g., Amentum/Excel work), or Excel/file-type
  markers in transcript.
- **freeform** — everything else.
Stamp `Session mode:` into the daily-log entry header.

### 2b. Mode-specific extraction prompts
- **BMAD mode prompt addition:** "This session executed the BMAD methodology. Story-first
  authoring, adversarial multi-LLM review, baseline-failure cataloguing, and artifact
  loading are *prescribed steps* — do NOT report them as intent signals. Report only:
  (1) deviations from BMAD, (2) choices BMAD leaves open (architecture, scope, naming),
  (3) Alec redirecting an agent, (4) edits to the BMAD workflow itself (these are
  workflow.md gold — e.g., the HALT removal)."
- **Work mode prompt:** extract data-handling decisions, formatting/reporting
  preferences, recurring Excel patterns → route lessons to `20_Reference/Work/LEARNINGS.md`
  (new domain in `vault_router.py`).

### 2c. BMAD ritual whitelist
- New file `D:\Brain\00_Meta\bmad_rituals.md`: the known deliberate patterns (story-first,
  adversarial review gate, failure baseline, exhaustive artifact loading, different-LLM
  review). daily-reflect/weekly-dream read it and suppress matching proposals.
- One-time: promote those rituals into `workflow.md` under a **"BMAD Methodology
  (deliberate — not learned)"** section so they're documented once and never re-proposed.
- Evidence weighting rule in daily-reflect: gap/confirmation instances from BMAD-mode
  sessions count at reduced weight for *intent* proposals (the loop repeats by design),
  full weight for *deviation* evidence.

## Pillar 3 — Playwright MCP: checking, researching, snippet-grabbing

### 3a. Server upgrade (global `.claude.json`)
- `@playwright/mcp@0.0.70` → `@latest`; add `--caps=vision,pdf,devtools,testing`,
  `--output-dir=D:\Brain\Reports\web-checks`, `--user-data-dir` (persistent profile for
  logged-in sites). Keep headless default; add a non-headless variant for watching.
- `testing` caps add `browser_verify_*` assertion tools; `devtools` adds console/network/
  perf (Core Web Vitals); traces/video available via `--save-trace` / `--save-video`.

### 3b. Three thin skills
- **/check-site `<url>` [expectations]** — navigate → snapshot → console errors → failed
  network requests → screenshot → verdict vs expectations. Saves evidence to output dir.
  This becomes the verification step for LEBOv2 UI stories (formalizing the lebo-*.png
  screenshot habit) and plugs into bmad-story-loop as the web "see what you built" gate.
- **/research `<topic|url>`** — fetch/browse → extract key content + code → write a
  sourced note to `20_Reference/<domain>/` with URL citations and date.
- **/grab-snippet `<url> [what]`** — extract a specific code block/pattern → feed the
  existing /log-learning pipeline with source attribution.

## Pillar 4 — Godot MCP: give the AI eyes in the engine

### 4a. Fix registration (broken since migration)
- Remove the dead `D:/Obsidian Brain/...` project entry; add `godot-mcp` via a
  **checked-in `.mcp.json` in `D:\Projects\Project_Chimera`** so it survives future moves
  and applies to any clone.

### 4b. Editor addon for full visibility
- `@satelliteoflove/godot-mcp` ships a Godot editor addon — install it in the Chimera
  project, enable in Project Settings → Plugins. That unlocks: scene-tree inspection,
  **screenshots of the editor and the running game**, error reading, perf data, and
  direct scene/node/script modification — the see-adjust-rerun loop.
- Evaluate `Coding-Solo/godot-mcp` as a complement: launches the project headlessly and
  captures debug output (good for the story loop's automated runs).

### 4c. `/godot-verify` skill (the game equivalent of /check-site)
- `dotnet build` the C# solution → surface build errors → run the target scene →
  capture screenshot + debug output/errors → compare against the story's acceptance
  criteria → verdict. Wire into bmad-story-loop so game stories get the same
  dev → run → look → fix cycle web stories get.
- Append engine learnings to `20_Reference/GameDev/godot-csharp/LEARNINGS.md` (already
  exists and is healthy at ~13KB).

## Pillar 5 — Hygiene (do alongside Week 1)

1. **Rotate the GitHub PAT** (`ghp_Z3dU...` in settings allow-rules) and scrub the rule;
   rotate the Anthropic key in `settings.local.json` at convenience (untracked, but it
   has appeared in transcripts).
2. Purge stale "Obsidian Brain" permission rules and dead `.claude.json` project entries.
3. Consolidate duplicate skill registrations (capture-idea etc. appear twice: global +
   project).

---

## Sequencing

| Phase | Work | Outcome |
|-------|------|---------|
| **Week 1** | 1a review skill + backlog triage; 4a Godot re-registration; 3a Playwright upgrade; Pillar 5 hygiene | Loop closes; intent.md gets its first real entries; both MCPs alive |
| **Week 2** | 2a–2c BMAD-aware capture + ritual whitelist; 1b Standing Order injection; 1d automated nightly reflect | Proposal stream turns high-signal; sessions start with Alec's heuristics loaded |
| **Week 3** | 3b web skills; 4b/4c Godot addon + /godot-verify; story-loop integration | AI verifies its own web and game output |
| **Ongoing** | 1c propose-then-act with confirm/override feedback | "It already knows how I'd answer" |

**Recommended first move:** build `/review-proposals` and triage the 31-item backlog —
until intent.md has content, nothing downstream can work.
