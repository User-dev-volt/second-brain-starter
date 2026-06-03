# Token Usage Tracking

Track and analyze Claude Code token consumption to reduce costs and eventually
build a Sonnet/Haiku triage agent.

---

## Run it now (manual)

```powershell
python "D:\second-brain-starter\.claude\scripts\token_report.py"
```

Report saves to: `D:\Brain\Reports\Token Usage\YYYY-MM-DD_HH00.md`

---

## How it works

```
~/.claude/projects/          ← Claude Code writes JSONL session files here automatically
        ↓
token-dashboard (scanner)    ← reads + deduplicates JSONL, caches to SQLite
        ↓
~/.claude/token-dashboard.db ← local SQLite database
        ↓
token_report.py              ← queries DB, builds markdown report, calls Claude API for analysis
        ↓
Obsidian vault / Reports/Token Usage/   ← final report with data + AI analysis
```

### Scheduled task
`SecondBrain\TokenReport` runs every 4 hours via Windows Task Scheduler (registered alongside
Heartbeat and DailyReflect in `setup_scheduler.bat`).

---

## Files

| File | Purpose |
|------|---------|
| `C:\Users\MD_Ki\tools\token-dashboard\` | token-dashboard repo (cloned from github.com/nateherkai/token-dashboard) |
| `.claude\scripts\token_report.py` | Main report + analysis script |
| `.claude\scripts\setup_scheduler.bat` | Registers all 3 Task Scheduler tasks (run as Admin to re-register) |

---

## Current status (as of 2026-04-23)

### Blocker
The Claude analysis section requires Anthropic API credits.
- Add credits at: https://console.anthropic.com/settings/billing
- Everything else (data collection, report tables, trend tracking) works without credits.
- Once credits are added, re-run the script and the `## Analysis Notes` section will populate.

### Task Scheduler
- `SecondBrain\TokenReport` — registered, fires every 4 hours from midnight
- Verify in Task Scheduler UI: `taskschd.msc` → Task Scheduler Library → SecondBrain

---

## Key findings so far

From the first report run on 2026-04-23:

- **`LastEpochBuildOptimizer-LEBOv2`** is the top consumer: **96M tokens in 7 days**, 99% from cache reads
- The `_bmad-output/` planning files are being read 20–51 times each per week across 5–12 sessions
- Top offenders:
  - `epics.md` — 51 reads, 12 sessions
  - `sprint-status.yaml` — 48 reads, 12 sessions
  - `prd.md` — 39 reads, 5 sessions
- **Quick win**: summarize these files into the LEBO project's `CLAUDE.md` so they're loaded once per session instead of re-read on every task

---

## Next steps

### Immediate
- [ ] Add API credits so the Claude analysis section auto-populates
- [ ] Add a summary of `epics.md`, `sprint-status.yaml`, and `prd.md` to `LEBOv2/CLAUDE.md`
- [ ] Run the report daily for a week to build a baseline trend

### Phase 2 — Triage agent
Goal: automatically route tasks to Haiku vs Sonnet based on task type and project.

Data needed (collecting now):
- Which projects/task types generate long sessions (→ Sonnet)
- Which tool calls dominate (Read/Glob/Grep with no reasoning → Haiku candidates)
- Model breakdown per project (already in report)

Design sketch:
- A pre-task classifier prompt (cheap Haiku call) that reads the user's intent and routes to Sonnet or Haiku
- Rules seeded from this report data (e.g. "file scan tasks in LEBO → Haiku", "architecture/planning → Sonnet")
- Can be built as a Claude Code hook or a wrapper script

### Phase 3 — Dashboard
The token-dashboard web UI is available any time:
```powershell
python "C:\Users\MD_Ki\tools\token-dashboard\cli.py" dashboard
# Opens at http://127.0.0.1:8080
```
Tabs: Overview, Prompts, Sessions, Projects, Skills, Tips, Settings.
