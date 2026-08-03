# Opus 5 Reset — Step-by-Step Runbook

**Scope:** Everything *outside* official BMAD. (BMAD you're handling manually.)
**Rule for every step:** WHY → DO → VERIFY → UNDO. Don't skip VERIFY.
**Shell:** PowerShell 7 (pwsh). All paths are absolute.

---

## The one distinction that drives this whole plan

> **The ablation surface is anything that puts text in front of the model.**

- **In scope for ablation:** `CLAUDE.md`, skills, context-injecting hooks. These are *instructions* — Boris's "delete and re-add only what repeatedly fails."
- **Not in scope:** AutoSave, `pre_commit_gate`, `token_report`. These never touch model context. They're safety nets and instrumentation. Judge them on whether they work, not on whether the model needs them.

Getting this wrong is how people delete their git safety net in the name of "unhobbling."

---

# PHASE 0 — Safety first (~20 min)

Do this before anything else. These are live problems, not optimizations.

### ☐ 0.1 — Back up everything you're about to touch

**WHY:** Every later step is reversible only if you do this one.

```powershell
$stamp = Get-Date -Format "yyyy-MM-dd"
$bak = "D:\Brain\90_Backups\claude-reset-$stamp"
New-Item -ItemType Directory -Force $bak

Copy-Item "C:\Users\MD_Ki\.claude\settings.json"      "$bak\global-settings.json"
Copy-Item "C:\Users\MD_Ki\.claude\CLAUDE.md"          "$bak\global-CLAUDE.md"
Copy-Item "C:\Users\MD_Ki\.claude\skills"             "$bak\skills" -Recurse
Copy-Item "D:\second-brain-starter\.claude"           "$bak\sbs-dot-claude" -Recurse
schtasks /query /fo LIST /v > "$bak\scheduled-tasks-before.txt"
```

**VERIFY:** `Get-ChildItem $bak` shows 5 entries.

---

### ☐ 0.2 — Defuse the auto-push landmine

**WHY:** AutoSave is a **global** Stop hook, so it fires in *any* directory with a `.gitaccount`. `D:\Archive projects\LastEpochBuildOptimizer` has staged deletions queued that would be committed and pushed to `origin/main` on your next Stop there.

```powershell
# Look before you delete
Get-Content "D:\Archive projects\LastEpochBuildOptimizer\.gitaccount"
git -C "D:\Archive projects\LastEpochBuildOptimizer" status --short | Select-Object -First 20

Remove-Item "D:\Archive projects\LastEpochBuildOptimizer\.gitaccount"

# Same unguarded config — review, decide separately
Get-Content "D:\Projects\Video Gen\.gitaccount"
```

**VERIFY:** `Test-Path "D:\Archive projects\LastEpochBuildOptimizer\.gitaccount"` → `False`
**UNDO:** Restore the one-line file from `$bak` or retype it.

---

### ☐ 0.3 — Rotate two credentials

**WHY:** Neither is publicly exposed (the public repo has only a truncated `ghp_Z3dU...` reference), but both are live on disk, and the Anthropic key has already been written into 4 transcript files.

1. **GitHub PAT** — revoke `ghp_Z3dUP6gX…` at https://github.com/settings/tokens, issue a new one.
2. **Anthropic key** — rotate `sk-ant-api03-5C29bw…` at https://console.anthropic.com/settings/keys.

Then delete the redundant copy. It's byte-identical to a Windows user env var that's already set, and **nothing live reads it**:

```powershell
# Confirm the env var exists first
[Environment]::GetEnvironmentVariable("SECOND_BRAIN_API_KEY","User").Length
```

Now edit `D:\second-brain-starter\.claude\settings.local.json` and **delete the entire `"env"` block.**

**VERIFY:** `Select-String "sk-ant" "D:\second-brain-starter\.claude\settings.local.json"` → no matches.

---

### ☐ 0.4 — Delete a stale home backup holding OAuth tokens

```powershell
Get-ChildItem "D:\Drive Return\UserMD_killerx\.claude" | Select-Object Name, Length
Remove-Item "D:\Drive Return\UserMD_killerx\.claude" -Recurse -Force
```

---

### ☐ 0.5 — Unpin your phone sessions from the old model

**WHY:** `session_manager/config.json` pins `"default_model": "claude-opus-4-8"` and `"default_effort": "max"`. Every remote session you've launched has run the *previous* model.

Edit `D:\second-brain-starter\session_manager\config.json`:

```jsonc
"default_model": "opus[1m]",
"default_effort": "medium"
```

*(If you retire session_manager in Phase 3, this becomes moot — but fix it now in case you keep it.)*

---

### ☐ 0.6 — Resolve the rule/automation contradiction

**WHY:** `SOUL.md` lists *"run `git push` without explicit approval"* under **hard blocks, no exceptions** — while AutoSave pushes on every Stop. Your rules and your automation disagree.

```powershell
Get-ChildItem -Path "D:\Brain" -Filter "SOUL.md" -Recurse | Select-Object FullName
Select-String -Path "<path from above>" -Pattern "push"
```

Pick one: soften the rule to match AutoSave, or scope AutoSave to commit-only. **Don't leave both.**

---

### ☐ 0.7 — Fix one genuinely broken file

**WHY:** `D:\Projects\Stocks\.claude\settings.json` is **zero bytes** — invalid JSON, parsed every session there. It won't self-heal because the preseed only writes when the file is *absent*.

```powershell
Set-Content "D:\Projects\Stocks\.claude\settings.json" -Value "{}"
```

---

# PHASE 1 — Kill the provably-dead hooks (~10 min)

**No ablation needed here.** These deliver nothing to the model, so there's no "does the model need it" question to answer.

### ☐ 1.1 — See the bug yourself

```powershell
cd D:\second-brain-starter
'{"session_id":"probe","cwd":"D:/Projects/LEBOv2"}' | .\.venv\Scripts\python.exe .\.claude\hooks\session-start-context.py | Measure-Object -Character
```

You'll get **~36,000 characters** (~9,000 tokens). Now look at the shape:

```powershell
Select-String -Path ".\.claude\hooks\session-start-context.py",".\.claude\hooks\pre-compact-flush.py" -Pattern "additionalContext"
```

Both print `{"additionalContext": ...}` at the **top level**. Claude Code only reads it nested:

```jsonc
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}
```

So: 9,000 tokens built, then discarded. Every session. In all 24 projects.

---

### ☐ 1.2 — Remove the two dead hooks

Edit `C:\Users\MD_Ki\.claude\settings.json`. **Delete the `UserPromptSubmit` and `PreCompact` entries. Keep `Stop`** (that's AutoSave — it never touches model context).

```jsonc
"hooks": {
  "Stop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "\"D:/second-brain-starter/.venv/Scripts/python.exe\" \"D:/second-brain-starter/.claude/hooks/session-end-flush.py\"",
          "timeout": 300,
          "statusMessage": "Flushing session learnings..."
        }
      ]
    }
  ]
}
```

**VERIFY:** Start a new session. It should feel *faster* — you've removed a Python spawn from every prompt (~739 ms/turn floor).
**UNDO:** Restore `$bak\global-settings.json`.

> **Decision point:** you already disabled AutoSave in your most active repo. That's a revealed preference. If you don't miss it during Phase 2, drop the `Stop` hook too.

---

### ☐ 1.3 — Sweep the orphaned marker files

```powershell
Get-ChildItem "$env:TEMP\second-brain-injected-*" | Measure-Object   # ~98 files, 0 bytes each
Remove-Item "$env:TEMP\second-brain-injected-*" -Force
```

---

# PHASE 2 — The ablation week

**This is the actual method. Don't skip to Phase 3.** You can't tell what's load-bearing until you've run without it.

### ☐ 2.1 — Cut global settings to baseline

Replace `C:\Users\MD_Ki\.claude\settings.json` with:

```jsonc
{
  "env": { "CLAUDE_CODE_USE_POWERSHELL_TOOL": "1" },
  "permissions": { "defaultMode": "acceptEdits" },
  "model": "opus[1m]",
  "effortLevel": "medium",
  "theme": "dark",
  "tui": "fullscreen",
  "skipDangerousModePermissionPrompt": true,
  "remoteControlAtStartup": true
}
```

**What you dropped:** the 86-entry allowlist (44+ never matched anything), the `rust-analyzer-lsp` plugin, and assorted notification flags.
**What changed deliberately:** `effortLevel` `high` → `medium`. Anthropic's guide calls low/medium *"your primary control for token cost and response time."* Step up per-session with `/effort` when you actually need it.

---

### ☐ 2.2 — Move your instructions aside (don't delete)

```powershell
$abl = "D:\Brain\90_Backups\ablation-$(Get-Date -Format yyyy-MM-dd)"
New-Item -ItemType Directory -Force $abl

Move-Item "C:\Users\MD_Ki\.claude\CLAUDE.md" "$abl\CLAUDE.md"
Move-Item "C:\Users\MD_Ki\.claude\skills"    "$abl\skills"
Move-Item "D:\Brain\CLAUDE.md"               "$abl\Brain-CLAUDE.md"   # 7,463 B of 7 step-by-step protocols
```

**Expect the clarity-view rule to be the first thing you miss** — that one's a genuine preference, not scaffolding. When it fails, that's a legitimate re-add.

---

### ☐ 2.3 — Run one week. Log only *repeated* failures.

Boris's bar is **"the model repeatedly fails without it"** — not "I felt uneasy." Keep a scratch file:

```markdown
# Ablation log — week of 2026-08-03

| Date | What I wanted | What Claude did | Failed before? | Re-add? |
|------|---------------|-----------------|----------------|---------|
|      |               |                 |                |         |
```

**Rule:** one occurrence = note it. **Two occurrences = re-add.** One-offs are noise.

---

### ☐ 2.4 — Re-add only what failed twice

Restore individual files from `$abl` — not the whole directory.

```powershell
Copy-Item "$abl\skills\godot-verify" "C:\Users\MD_Ki\.claude\skills\godot-verify" -Recurse
```

**Realistic expectation: 2–4 items, not 20.** Likely survivors: `godot-verify` (22 uses, live), `project-context`, `clarify`, and a much shorter `CLAUDE.md`.

When you rewrite `CLAUDE.md`, keep it **goal-shaped, not procedural**. `D:\Brain\CLAUDE.md`'s seven step-by-step protocols are exactly the shape Anthropic says to drop.

---

# PHASE 3 — Delete the confirmed-dead (after the ablation week)

### ⚠️ ORDERING RULE — read before deleting anything

**`\SecondBrain\TokenReport` is a live scheduled task.** Deregister it *before* deleting `scripts/setup/`, or you orphan a task pointing at a missing script.

```powershell
schtasks /query /tn "SecondBrain\TokenReport" /fo LIST /v
```

Decide: **keep it** (it's your only token-spend instrumentation) or **remove it first**:

```powershell
schtasks /delete /tn "SecondBrain\TokenReport" /f
```

---

### ☐ 3.1 — Second-brain engine subsystems

```powershell
cd D:\second-brain-starter\.claude\scripts

Remove-Item .\memory      -Recurse -Force   # memory.db has 0 rows; chunks_vec: "no such module: vec0"
Remove-Item .\security    -Recurse -Force   # Opus 5 has native 3-layer injection resistance
Remove-Item .\heartbeat.py, .\clean_error_sessions.py -Force
Remove-Item .\utils\snapshot.py, .\utils\notifications.py -Force
Remove-Item .\integrations\comfyui_integration.py, .\integrations\asset_cataloger.py -Force
Remove-Item .\integrations\github_integration.py -Force   # gh CLI does this natively
```

**Delete `context_builder.py` only after Phase 1 is confirmed stable** — it's the dead hook's only consumer.

**KEEP:** `git/` (auto_commit, git_router, ssh_manager, pre_commit_gate) · `token_report.py` · `query.py` · `utils/vault_router.py` *(still imported by `session-end-flush.py`)*.

---

### ☐ 3.2 — Retire session_manager

**WHY:** It isn't running — zero listeners on the box. Remote Control (already on via `remoteControlAtStartup: true`) covers phone→desktop.

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.OwningProcess -in (Get-Process python -EA SilentlyContinue).Id }
```

Empty output confirms it. Then archive `D:\second-brain-starter\session_manager\` and drop the `session-manager` skill.

---

### ☐ 3.3 — Skills that didn't survive the week

```powershell
cd "C:\Users\MD_Ki\.claude\skills"
Remove-Item .\excalidraw-diagram -Recurse -Force   # 113 MB — vendored .venv; Artifacts render mermaid natively
Remove-Item .\rip -Recurse -Force                  # every command path in it is dead
Remove-Item .\research, .\grab-snippet, .\capture-idea, .\create-second-brain-prd -Recurse -Force
Remove-Item .\check-site -Recurse -Force           # native browser tools cover it
```

Project duplicates (byte-identical to global) at `D:\second-brain-starter\.claude\skills`: `capture-idea`, `create-second-brain-prd`, `log-learning`, `project-context`, plus `gitpush`.

---

### ☐ 3.4 — Permissions

Already handled by the Phase 2 baseline. Also strip `settings.local.json` — it duplicates 64 of 67 entries from global.

---

### ☐ 3.5 — Dead directories

```powershell
Remove-Item "D:\Obsidian Brain\Brain" -Recurse -Force   # migration completed 2026-06-02 — CHECK IT FIRST
```

Then: the 6 dead MovieBuilder clones, 5 empty container-level `.claude` dirs holding only `{}`, and 2 dead project entries in `.claude.json`.

> **Never hand-edit `.claude.json`** — the CLI rewrites it on every startup. Use `/config` and `claude mcp`.

---

### ☐ 3.6 — MCP + plugin

```powershell
claude mcp list                                    # playwright is registered twice
cd C:\Users\MD_Ki; claude mcp remove playwright    # drop the home-dir-scoped duplicate
```

**Leave `godot-mcp` alone** — 1,167 calls, your dominant MCP by a factor of 8.
`rust-analyzer-lsp` is already gone via the Phase 2 baseline. Re-add only if you write Rust.

---

# PHASE 4 — Fill the space (optional, ongoing)

Deleting is half of Boris's point. The other half is *give the model harder work.*

### ☐ 4.1 — Autonomous maintenance routines

Anthropic runs 20–30 daily. You have 15 active projects and **zero**. Start with one:

```
/schedule daily 07:00 — In <project>: find dead code and unused exports, remove them,
run the test suite, and open a PR. Skip anything with a TODO referencing active work.
```

Cherny's three starters: **dead-code removal, test generation, abstraction unification.**

### ☐ 4.2 — Install Claude Code Desktop

Not currently installed. Prerequisite for durable local scheduled work.
*Caveat:* Desktop tasks are "local + durable" only while the app is open and the machine is awake — weaker than Task Scheduler for true unattended runs.

### ☐ 4.3 — Change how you prompt

The largest available win, and it costs nothing:

| Stop | Start |
|---|---|
| "double-check your answer" / "add a verification step" / "use a subagent to verify" | Nothing — Opus 5 self-verifies; these compound into over-verification |
| "only report high-severity issues" | "Report everything" — then filter in a second pass |
| Drip-feeding steps | Complete spec up front, then leave it to run |
| Step-by-step decomposition | Goal + a real verification mechanism (a script with an exit code) |

---

# Rollback

```powershell
$bak = "D:\Brain\90_Backups\claude-reset-<date>"
Copy-Item "$bak\global-settings.json" "C:\Users\MD_Ki\.claude\settings.json" -Force
Copy-Item "$bak\global-CLAUDE.md"     "C:\Users\MD_Ki\.claude\CLAUDE.md" -Force
Copy-Item "$bak\skills\*"             "C:\Users\MD_Ki\.claude\skills\" -Recurse -Force
```

Phases 0–2 are fully reversible. Phase 3 is reversible from `$bak` **except** the credential rotations (intentional) and `D:\Obsidian Brain\Brain` (verify before deleting).

---

# The cadence

At every model launch, re-run **Phase 2 only** (steps 2.1 → 2.4). Takes 15 minutes plus a week of noticing.

> Your config is a hypothesis about the model's weaknesses. It expires when the model changes.

---

## Quick checklist

```
PHASE 0 — SAFETY (today, ~20 min)
  ☐ 0.1 Back up
  ☐ 0.2 Defuse auto-push landmine
  ☐ 0.3 Rotate 2 credentials + drop env block
  ☐ 0.4 Delete OAuth backup dir
  ☐ 0.5 Unpin phone sessions from opus-4-8
  ☐ 0.6 Resolve SOUL.md / AutoSave contradiction
  ☐ 0.7 Fix zero-byte Stocks settings.json

PHASE 1 — DEAD HOOKS (~10 min)
  ☐ 1.1 Reproduce the schema bug
  ☐ 1.2 Remove UserPromptSubmit + PreCompact (keep Stop)
  ☐ 1.3 Sweep %TEMP% markers

PHASE 2 — ABLATION (15 min + 1 week)
  ☐ 2.1 Baseline settings.json
  ☐ 2.2 Move CLAUDE.md + skills aside
  ☐ 2.3 Run a week, log repeated failures
  ☐ 2.4 Re-add only what failed twice

PHASE 3 — DELETE (after week 1)
  ⚠️  Deregister TokenReport BEFORE deleting setup/
  ☐ 3.1 Engine subsystems    ☐ 3.4 Permissions
  ☐ 3.2 session_manager      ☐ 3.5 Dead directories
  ☐ 3.3 Skills               ☐ 3.6 MCP + plugin

PHASE 4 — REBUILD (ongoing)
  ☐ 4.1 /schedule routines   ☐ 4.2 Desktop app   ☐ 4.3 Prompting habits
```
