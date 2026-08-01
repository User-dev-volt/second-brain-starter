# Opus 5 Transition Plan

**Date:** 2026-08-01
**Method:** Boris Cherny's ablation doctrine (YC Startup School 2026, *"We Cut 80% of Claude Code's Prompt"*) + Anthropic's official Opus 5 prompting guide.
**Evidence base:** 20 audit agents across 2 workflows, ~2.1M tokens, 821 tool calls. Every deletion recommendation was adversarially verified by an independent agent instructed to refute it. 23 of 85 recommendations were refuted or corrected — those corrections are reflected below.

---

## 0. The headline: your hypothesis was half right, and the half that's wrong matters more

You suspected the second brain is hobbling Opus 5. Here's what the evidence actually says.

**The second brain is not hobbling Opus 5. It is disconnected from it.**

Your `UserPromptSubmit` hook builds a real context payload every session:

| Project | Payload built | Tokens |
|---|---|---|
| Project_Chimera | 37,706 B | ~9,400 |
| LEBOv2 | 35,957 B | ~9,000 |
| second-brain-starter | 32,547 B | ~8,100 |
| Stocks | 17,603 B | ~4,400 |

It emits that payload as a **top-level `additionalContext` key**. Claude Code requires it nested under `hookSpecificOutput`:

```jsonc
// what your hooks print — ignored
{"additionalContext": "...9,000 tokens..."}

// what Claude Code reads
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
```

Empirical confirmation: if ~9k tokens were landing in every session across 24 projects, the injected markers would appear in hundreds of transcripts. They appear in **two** — one from 2026-07-13, one from today's audit.

So the machine spends CPU building 9,000 tokens of memory on every fresh session, and Claude Code throws it away. `SOUL.md`, `USER.md`, `LEARNINGS.md`, your daily logs, the project snapshot — none of it has been reaching the model.

**Three consequences:**

1. Your mental model ("my brain feeds Claude context") has been false for some time. Every judgment you've made about Claude's behavior was made against a model that never saw the brain.
2. The `PreCompact` hook has the **same bug** at line 91. The BMAD state snapshot you believe survives compaction has been delivering nothing. That's a safety mechanism failing silently.
3. The real cost of the hooks is latency, not tokens — two Python interpreter spawns per assistant turn, measured mean **739 ms**, in all 24 projects.

**The actual hobbling is BMAD** — but the evidence there needs a caveat, see §3.

---

## 1. Do you need to reinstall Claude?

**No.** CLI 2.1.220 is current and healthy. Nothing about the installation is broken.

What needs resetting is the **config layer** — and Cherny's prescription is specific: don't hand-tune it, *ablate* it. Delete to baseline, run, and re-add only what repeatedly fails. That's Phase 1.

---

## 2. Phase 0 — Safety, today (~20 minutes)

These are live problems, not optimizations. Ordered by urgency.

### 2.1 An archived repo will auto-commit and **push** staged deletions on your next Stop
`D:\Archive projects\LastEpochBuildOptimizer\.gitaccount` is still active. AutoSave is a **global Stop hook**, so it fires there. The working tree has staged deletions that would be committed and pushed to `origin/main`.

```powershell
Remove-Item "D:\Archive projects\LastEpochBuildOptimizer\.gitaccount"
# also review — same unguarded config:
Get-Content "D:\Projects\Video Gen\.gitaccount"
```

### 2.2 Rotate two credentials
Neither is publicly exposed — I verified the public repo contains only a truncated `ghp_Z3dU...` reference. But both are live on disk.

| Credential | Where | Exposure |
|---|---|---|
| GitHub PAT `ghp_Z3dUP6gX…` | commits `ce160ba`, `1c8aaff` | **Local git history only** — never pushed |
| Anthropic key `sk-ant-api03-5C29bw…` | `settings.local.json`, `.env`, and **4 transcript files on disk** | Never committed |

The Anthropic key is also **redundant** — it's byte-identical to a Windows user env var that's already set, and nothing live reads it. Rotate, then delete the whole `env` block from `settings.local.json`.

### 2.3 Delete a stale home backup containing OAuth credentials
`D:\Drive Return\UserMD_killerx\.claude` — a copied `.claude` home directory with live OAuth tokens in it.

### 2.4 Fix a contradiction your own rules encode
`SOUL.md` line 26 lists under *"Hard blocks (never do, no exceptions)"*: **"Run `git push` without explicit approval."** AutoSave pushes automatically on every Stop. One of these has to go — and since AutoSave is genuinely useful, it's the rule that's wrong.

---

## 3. Phase 1 — The ablation baseline (this week)

This is the core of Cherny's method and the single highest-value thing in this plan. **Do not skip to Phase 2.** You cannot tell what's load-bearing until you've run without it.

### Step 1: Disable all three hooks

Remove the `hooks` block from `C:\Users\MD_Ki\.claude\settings.json` — **except** keep the Stop hook if you want AutoSave (see below). Recommended: comment out `UserPromptSubmit` and `PreCompact` entirely; they are provably delivering nothing.

### Step 2: Cut global settings to a minimum

```jsonc
{
  "model": "opus[1m]",
  "permissions": { "defaultMode": "acceptEdits" },
  "theme": "dark",
  "tui": "fullscreen"
}
```

Everything else — the 86-entry allowlist, the plugin, the notification flags — comes back only if you miss it.

### Step 3: Run normally for one week. Keep a running note of what actually breaks.

Cherny's bar is *"the model repeatedly fails without it."* Not "I felt uneasy." Repeatedly fails.

### Step 4: Re-add only what failed.

**Two settings worth changing regardless**, per Anthropic's official guide:

- **`effortLevel`** — you're globally at `high`. The guide says use `low`/`medium` "liberally as your primary control for token cost and response time wherever quality holds," and reserve `xhigh` for demanding agentic work. Try `medium` as your default and step up per-session with `/effort`.
- **`session_manager/config.json` pins `"default_model": "claude-opus-4-8"` and `"default_effort": "max"`.** Every session you launch from your phone runs **Opus 4.8**, not Opus 5. This is a live divergence from your global config and it's probably been shaping your impression of "how Opus 5 behaves."

---

## 4. Phase 2 — Delete what is provably dead

All verified. Nothing here is load-bearing.

| Item | Evidence | Size |
|---|---|---|
| `UserPromptSubmit` + `PreCompact` hooks | Schema bug — output discarded | ~9k tok/session wasted CPU |
| `scripts/memory/` (db, chunker, embeddings, index, search) | `memory.db` has **0 rows**; `chunks_vec` raises *"no such module: vec0"* — the vector index never worked | whole subsystem |
| `scripts/security/` (guardrails, sanitize) | Opus 5 has 3-layer native prompt-injection resistance | whole subsystem |
| `session_manager/` FastAPI panel | **Not running** — zero listeners on the box | whole subsystem |
| `excalidraw-diagram` skill | Vendored `.venv` inside `references/` | **113 MB** |
| 44+ dead permission entries (of 86) | Zero hits across 8,437 Bash calls in 1,544 transcripts | — |
| `settings.local.json` allowlist | Duplicates 64 of 67 entries from global | — |
| Never-invoked skills: `capture-idea`, `research`, `grab-snippet`, `create-second-brain-prd`, `gitpush` | 0–1 lifetime invocations | — |
| `rip` skill | Every command path in it is dead | — |
| `D:\Obsidian Brain\Brain` | Dead vault, migration completed 2026-06-02 | — |
| 6 dead MovieBuilder clones | 36 custom slash commands each | — |
| 5 empty container-level `.claude` dirs | Contain only `{}` | — |
| 98 orphaned marker files in `%TEMP%` | `second-brain-injected-*`, all 0 bytes | — |

### Corrections — do **not** delete these (auditors were wrong, verifiers caught it)

- **`token_report.py` — KEEP.** The auditor claimed its scheduled task doesn't exist. It does: `\SecondBrain\TokenReport`, State Enabled, **last run 8/1**. It's your only token-spend instrumentation.
- **`git/auto_commit.py` + `pre_commit_gate.py` — KEEP.** AutoSave works and the baseline-aware gate is real protection.
- **`.claude.json` at 104 KB — KEEP.** Not bloat; the CLI rewrites it on every startup. Never hand-edit it — use `claude mcp remove` and `/config`.
- **`D:\Brain` knowledge store — KEEP.** This is the distinction that matters: the **notes** have durable value; the **engine** that indexes and injects them does not. Deleting the engine does not touch the brain.
- **Project `settings.json` `{"hooks": {}}` — leave it.** It's a session-manager trust marker that gets recreated.

### One genuinely broken file
`D:\Projects\Stocks\.claude\settings.json` is **zero bytes** — invalid JSON, parsed on every session there. It won't self-heal because the preseed only writes when the file is absent.

---

## 5. Phase 3 — BMAD, with one important caveat

Your instinct — keep brainstorming/PRD/GDD, cut the rest — is **directionally right but wrong at the unit of analysis.** What has value is not three *skills*; it's five *data files*.

### 5.1 Keep these five assets (~125 KB of 67.88 MB)

| Asset | Why Opus 5 can't self-supply it |
|---|---|
| `assets/brain-methods.csv` (108 techniques) | A forced category-diverse random draw is anti-mode-collapse machinery. Asked to brainstorm cold, the model converges on its own top-20 defaults. |
| `assets/prd-template.md` + validation checklist | Counter-metrics ("why this should NOT be optimized"), Glossary-verbatim discipline, FR↔UJ↔SM stable IDs — and one behavioral correction that fights Opus 5's strongest default: *"When you find yourself naming wedges or picking MVP cuts, stop — you have crossed from elicitation into authoring. Hand the pen back."* |
| `assets/gdd-template.md` + 22 genre guides + `genre-complexity.csv` | Forces measurability: *"❌ the jump feels good → ✅ jump height 3 tiles, air time 0.55s, coyote time 6 frames, buffer 8 frames."* Plus seed determinism, netcode model, rollback vs lockstep. |
| `lens-verification-gap.md` + edge-case lens (~12 KB) | **You are about to lose these by accident.** They're the only execution-loop content with irreplaceable methodology, and you invoke them 54 times *through deprecated forwarding shims*. A clean BMAD exit silently drops them. |
| `tools/verify-in-engine-gate.ps1` | Mechanical enforcement — see 5.3. |

Move them to `D:\Brain\20_Reference\methods\`. Wrap each in ~40 lines of goal-oriented prompt. Delete the skills.

### 5.2 Consolidate the 9 copies — divergence is fake

67.88 MB / 705 `SKILL.md` files across 9 project trees. Of 79 skills present in 4+ projects, **52 are byte-identical everywhere**, and the 27 that differ cluster by *install date*, not by project. Unrelated projects share identical bytes while related projects differ — that's drift, not customization.

Real per-project customization already lives where BMAD intended: `_bmad/custom/*.toml`, resolved at runtime. **Keep `_bmad/`. Delete the duplicated skill trees.** Target: ~1.3 MB / ~10 skills in the global dir. A 98% cut.

Also delete outright: the `.agent/` `.agents/` `agent/` mirror dirs, the `gds-*` tree (132 files), `wds-*` (13), `cpm-*`, and the dead project trees (`bmad-run`, `Drug Wars`, `poe2_optimizer_v6`, `moviebuilder`).

### 5.3 The execution loop — cut it, but **A/B it first**, and build the state layer before you do

The case against the loop is strong. Your own telemetry, from `Project_Chimera\.bmad-loop\runs\*\journal.jsonl`:

> 71 sessions across 30 stories. **987,088,824 raw tokens.** Mean 31.8M raw per story against your own configured budget of 2M. **29 of 30 stories over budget**, mean overshoot 2.5×. 8.5% of sessions stalled or timed out.

That's 32× the entire 1M context window spent per story — a loop re-reading the same context dozens of times, because the skills forbid the model from holding the whole job: `bmad-dev-auto` line 119, *"Do not skip, reorder, or pre-load steps"*; `bmad-code-review` line 82, *"NEVER skip steps or optimize the sequence."* That is exactly what the official Opus 5 guide says to remove, and exactly the opposite of *"performs best when given the complete task specification up front and left to run."*

**But two things must temper this:**

**Caveat 1 — every one of those tokens was burned by `claude-opus-4-8`.** I checked all 84 session-start records: 82 read `claude-opus-4-8`, 2 empty, **zero Opus 5**. So the 987M-token bill measures how a *previous model* behaved under these instructions. Using it to prove Opus 5 doesn't need the scaffolding is circular. It is the strongest possible argument for **re-measuring**, not for blind deletion.

→ **Run one story both ways on Opus 5** — BMAD loop vs. complete-spec-up-front — and compare tokens, wall-clock, and defect count. You already have the perfect instrument: `D:\Projects\vanilla-run` and `D:\Projects\bmad-run` were set up as a "BMad vs Vanilla" A/B with a **pre-registered rubric**. Harvest that before archiving.

**Caveat 2 — BMAD's real product is state, not knowledge.** This is the argument I'd have missed without adversarial verification, and it's the one that should shape your sequencing:

> story frontmatter carries `baseline_commit` → `sprint-status.yaml` carries the ready-for-dev/in-progress/review enum → the Review Triage Log carries what each pass decided and why → `deferred-work.md` carries what was consciously *not* done → git history carries DW-ids back to the ledger.

It ran this week: Chimera's HEAD reads `sweep dw-overlay-kit-bootstrap-consolidation: DW-23 via bmad-loop`, and `sprint-status.yaml` (190 KB) was written 7/30. **Nothing native replaces that layer.** Claude Code Tasks are per-session GUID-scoped, expose three states with no "review", and die on `/clear`. Cron is session-only with a 7-day expiry.

→ **Write the replacement state layer first** — a flat `BACKLOG.md` with story IDs, status, and baseline commit — and only then cut `sprint-status.yaml`. The acceptance test is concrete: *can I resume a half-finished story after a week, from a cold session?*

**Caveat 3 — enforcement beats instruction.** Chimera's epic-11 retrospective records the lesson directly: the dev/review agents were *instructed* to run the in-engine check, and *"instructions alone were optional for three epics running."* That's why `verify-in-engine-gate.ps1` stays. A script with an exit code is not scaffolding; it's a gate. Cherny's doctrine is about deleting **instructions**, not deleting **verification mechanisms** — and his own line is that verification is the thing people get most wrong.

---

## 6. Phase 4 — What to build in the space you free up

This is the "unhobbling" half. Deleting is only half of Cherny's point; the other half is *give the model harder work.*

1. **Autonomous maintenance routines via `/schedule`.** Anthropic runs 20–30 daily: dead-code removal, test generation, abstraction unification. You have 15 active projects and zero routines. Start with one per project.
2. **Install the Claude Code Desktop app.** Not installed. It's the prerequisite for durable local scheduled work. Caveat from verification: Desktop tasks are *"local + durable"* only while the app is open and the machine is awake — strictly weaker than Windows Task Scheduler for true unattended runs.
3. **Replace the `/clarify` HTML pipeline with Artifacts** for the rendering step — published to a private URL, updates in place, no local file for you to fail to open on your phone. **Keep the `CLAUDE.md` rule and keep the PNG-to-chat step**; those encode a real preference, and Artifacts doesn't satisfy the phone-review requirement on its own.
4. **Give Opus 5 the whole job.** The single largest behavior change available to you: stop drip-feeding. Complete spec up front, then leave it to run.

---

## 7. Prompting changes (free, immediate)

From Anthropic's official Opus 5 guide — these apply to how you write prompts, not to config:

| Stop doing | Why |
|---|---|
| "double-check your answer", "add a verification step", "use a subagent to verify" | Opus 5 self-verifies. These **compound into over-verification** and cost tokens with no quality gain. |
| "only report high-severity issues", "be conservative" in review prompts | Opus 5 follows it literally and reports *less*. Ask for everything, filter in a second pass. |
| Drip-feeding steps | Give the complete task up front and let it run. |
| Step-by-step decomposition | Replace with a goal plus a real verification mechanism. |

| Start doing | Why |
|---|---|
| Ask explicitly for shorter responses | Opus 5's default responses run longer; effort controls *thinking*, not *output length*. |
| Default to `medium` effort, step up deliberately | Primary lever for cost and latency. |
| Cap subagent delegation | Opus 5 delegates readily; it multiplies cost on small tasks. |

---

## 8. Sequencing

| Phase | When | Effort | Risk |
|---|---|---|---|
| 0 — Safety | Today | 20 min | none |
| 1 — Ablation baseline | This week | 15 min setup + 1 week observation | low, reversible |
| 2 — Delete dead weight | After Phase 1 | ~2 hours | low, all verified |
| 3a — BMAD asset extraction + dedup | Week 2 | half a day | low |
| 3b — Build `BACKLOG.md` state layer | Week 2 | 2 hours | — |
| 3c — A/B one story on Opus 5 | Week 2 | 1 story | none |
| 3d — Cut execution loop | **Only after 3b + 3c** | — | medium |
| 4 — Native routines | Week 3+ | ongoing | low |

---

## 9. What I am deliberately **not** recommending

- **Deleting `D:\Brain`.** The notes are the asset. Only the engine is obsolete.
- **Deleting BMAD's execution loop before the state layer exists.** You'd trade a working system for a token saving and lose resumability.
- **Trusting the 987M-token figure as an Opus 5 result.** It isn't one.
- **A full Claude reinstall.** Nothing is wrong with the install.
- **Hand-editing `.claude.json`.** The CLI rewrites it on every startup; use `/config` and `claude mcp`.
- **Mechanical skill pruning by `usageCount ≤ 3`.** Verification flagged this as unsafe — low-use skills include the verification lenses that are genuinely worth keeping.
