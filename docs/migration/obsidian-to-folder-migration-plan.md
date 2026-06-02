# Migration Plan: Dissolve Obsidian → Plain Folder Brain at `D:\Brain\`

**Created:** 2026-06-02
**Status:** READY TO IMPLEMENT (execute in a fresh session)
**Author:** Phase-A reorg session

---

## 0. Goal

Remove Obsidian from the second-brain entirely and run the *same system* as a plain
folder structure. Obsidian (the app) was only a viewer Alec never used; the brain is
**markdown files + Python automation**, neither of which needs Obsidian.

Keep **every current capability**: session capture hooks, daily logs, the intent system
(daily-reflect / weekly-dream → proposals → intent.md/workflow.md), domain learnings,
the Dashboard, the capture-idea / log-learning / project-context skills, and the
session manager. Drop only: the `.obsidian/` config, the "vault" framing, and the
now-empty `10_Active_Projects/` inside the old vault.

### Target architecture (3 homes)

| Home | Holds |
|------|-------|
| `D:\Projects\<name>\` | Project **code + that project's `Snapshot.md`** (already moved here) |
| `D:\Brain\` | **Cross-project memory**: SOUL, USER, daily logs, intent/workflow, Dashboard, learnings, archive, proposals, ideas, Templates, Reports |
| `D:\second-brain-starter\` | **The engine** (hooks, reflect scripts, skills, session manager) |

**Per-project notes now live WITH the code** (Model A / "reroute") — this is correct now
that Obsidian is gone. No copy-back, no duplication.

---

## 1. Current state (verified 2026-06-02)

- ✅ `D:\Projects\` contains all 6 projects, each with its `Snapshot.md` (moved with code):
  `LEBOv2`, `moviebuilder - BMAD MODULE Update`, `poe2_optimizer_v6`,
  `Practice local model`, `Project_Chimera`, `Video Gen`. Also a stray `_index.md`.
- ✅ Old vault `10_Active_Projects/` is now **empty**.
- ✅ Old vault still holds the keepers: `00_Meta/`, `20_Reference/`, `30_Archive/`, `Reports/`,
  plus `CLAUDE.md`, `Welcome.md`, `.obsidian/`, `.claude/`.
- ✅ `D:\Brain\` does **not** exist yet.

### Already done in the Phase-A session (do NOT redo)
- Heartbeat scheduled task deleted; `register_tasks.py` no longer defines it.
- Duplicate `\SecondBrain\DailyReflect` task deleted (kept root `SecondBrainDailyReflect`).
- `memory.db` (75 MB) deleted; `scripts/memory/` left dormant.
- `HABITS.md`, `HEARTBEAT.md`, `MEMORY.md`, `Game_Save.md` archived → `30_Archive/…_retired_2026-06-02.md`.
- `vault_router.py`: `MEMORY.md` removed from `CORE_MEMORY_FILES`; `practice`/`video` → AI routes added.
- `SOUL.md` + `CLAUDE.md` rewritten (daily-logs canonical, Dashboard = active pointer).
- `Dashboard.md` + `10_Active_Projects/_index.md` rebuilt for the 6 projects (in old vault).
- Stub `Snapshot.md` created for Practice local model + Video Gen (these moved to D:\Projects with the rest).

---

## 2. Path centralization strategy (do this FIRST — it shrinks everything else)

There is already a `VAULT_ROOT` env var in `.env` (`VAULT_ROOT=D:/Obsidian Brain/Brain`)
but **most scripts ignore it and hardcode the path**. The clean fix:

1. **Edit `.env` and `.env.example`:** set `BRAIN_ROOT=D:/Brain` (keep `VAULT_ROOT=D:/Brain`
   as an alias for back-compat). Add `PROJECTS_ROOT=D:/Projects`.
2. **Make the hot path read the env var.** In `scripts/utils/vault_router.py`, change:
   ```python
   VAULT_ROOT = Path(r"D:\Obsidian Brain\Brain")
   ```
   to:
   ```python
   import os
   VAULT_ROOT = Path(os.environ.get("BRAIN_ROOT") or os.environ.get("VAULT_ROOT") or r"D:\Brain")
   PROJECTS_ROOT = Path(os.environ.get("PROJECTS_ROOT") or r"D:\Projects")
   ```
   Everything that imports `vault_router.VAULT_ROOT` cascades automatically
   (`context_builder.py`, `memory_reflect.py`, `standing_order_reader.py`, `heartbeat.py`).

> NOTE: hooks may not have `.env` loaded into the environment. Confirm `shared.py` /
> hook startup loads `.env` (python-dotenv or manual). If not, either (a) add a tiny
> `load_dotenv()` at the top of `vault_router.py`, or (b) accept the `D:\Brain` literal
> fallback. Test with `vault_router.py` CLI after the change.

---

## 3. The move (filesystem)

1. Create `D:\Brain\`.
2. Move these from `D:\Obsidian Brain\Brain\` → `D:\Brain\`:
   - `00_Meta\` (entire tree: SOUL, USER, daily/, intent.md, workflow.md, Dashboard.md,
     proposals/, ideas/, Templates/)
   - `20_Reference\` (all LEARNINGS + _market/_backlog/_asset_catalog)
   - `30_Archive\`
   - `Reports\`
   - `CLAUDE.md`  → becomes `D:\Brain\CLAUDE.md` (brain operating instructions)
3. **Do NOT move:** `.obsidian\` (delete or ignore), `Welcome.md` (delete), empty
   `10_Active_Projects\` (delete), the old `.claude\` (review first — `.claude/skills/obsidian`
   is Obsidian-specific; safe to drop).
4. Delete the stray `D:\Projects\_index.md` (regenerated in step 6).
5. After verifying `D:\Brain\` is complete, the old `D:\Obsidian Brain\` can be deleted
   (per SOUL guardrails: confirm with Alec before deleting; consider zipping as a backup first).

---

## 4. Reroute per-project Snapshots to the code folder

In `scripts/utils/vault_router.py`, `get_project_snapshot(cwd)` currently looks in
`VAULT_ROOT/10_Active_Projects/<name>/Snapshot.md`. Change it to resolve the snapshot
**next to the code**:

- New behavior: walk up from `cwd`; if a `Snapshot.md` exists at that directory (or at the
  matched `PROJECTS_ROOT/<name>/`), return it. Practically: look for `Snapshot.md` at the
  project root under `PROJECTS_ROOT`.
- `session-end-flush.py` `update_snapshot_timestamp` / `update_snapshot_next_action` use
  `get_project_snapshot()`, so they follow automatically.
- `get_context_area()` and `get_learnings_file()` keep pointing at `D:\Brain\20_Reference`
  (cross-project) — only the *project snapshot* moves to the code folder.

Verify with: `python vault_router.py "D:\Projects\LEBOv2"` → snapshot should resolve to
`D:\Projects\LEBOv2\Snapshot.md`.

---

## 5. Update remaining hardcoded path references

After step 2's centralization, these still hardcode the old path and must be pointed at
`BRAIN_ROOT` (or `D:\Brain`):

| File | Line | Change |
|------|------|--------|
| `scripts/security/guardrails.py` | 83 | `_VAULT_ROOT` → read `BRAIN_ROOT`; **also add `D:\Projects` to `_ALLOWED_WRITE_DIRS`** so hooks can write Snapshots into project folders |
| `scripts/security/guardrails.py` | 146-147 | CLI test strings (cosmetic) |
| `scripts/clean_error_sessions.py` | 4 | `daily_dir` → `BRAIN_ROOT/00_Meta/daily` |
| `scripts/token_report.py` | 27 | `REPORT_DIR` → `BRAIN_ROOT/Reports/Token Usage` |
| `scripts/integrations/shared.py` | 65 | default → `D:\Brain` |
| `scripts/integrations/obsidian.py` | 5 + code | docstring + verify `update_project_snapshot` path (used by retired heartbeat; low risk) — consider renaming file `obsidian.py` → `vault_io.py` |
| `scripts/integrations/asset_cataloger.py` | 5 | docstring path |
| `scripts/memory/memory_index.py` | 27 | retired — update for consistency or leave |
| `skills/capture-idea/scripts/capture.py` | 15 | `VAULT_ROOT` → `BRAIN_ROOT` |
| `skills/capture-idea/SKILL.md` | 30, 54 | `D:\Brain\00_Meta\ideas\_backlog.md` |
| `skills/log-learning/scripts/log_learning.py` | 15 | `VAULT_ROOT` → `BRAIN_ROOT` |
| `skills/project-context/scripts/get_context.py` | 21 | `VAULT_ROOT` → `BRAIN_ROOT`; **snapshot lookup → `D:\Projects\<slug>\Snapshot.md`** |
| `skills/project-context/SKILL.md` | 20 | snapshot path → `D:\Projects\<slug>\Snapshot.md` |
| `skills/project-context/references/project-list.md` | 17 + project list | update to `D:\Projects\…`; refresh the 6-project list |
| `commands/daily-reflect.md` | 34 | `D:\Brain\00_Meta\proposals\…` |
| `commands/weekly-dream.md` | 40 | `D:\Brain\00_Meta\proposals\…` |
| `docs/token-tracking/README.md` | 14 | path doc |
| `docs/memory-system/intent-system-prd.md` | 13, 270, 543-545 | path docs (historical PRD — optional) |
| `.env` / `.env.example` | 18 | `BRAIN_ROOT=D:/Brain` |

---

## 6. Clean the HABITS leftover in the reflect pipeline

`scripts/memory_reflect.py` (the LIVE daily-reflect) still reads/writes
`VAULT_ROOT/00_Meta/HABITS.md` (line ~33). HABITS was retired. **Remove the HABITS
read/append logic** from `memory_reflect.py` so daily-reflect stops trying to touch the
archived file. (This is why HABITS history kept growing after Heartbeat died.)
Check `weekly_dream_loader.py` and `memory_reflect_loader.py` for the same.

---

## 7. Make capture hooks fire everywhere (hooks → user-global)

Currently the capture hooks live ONLY in `D:\second-brain-starter\.claude\settings.json`
with **relative** commands (`.venv/Scripts/python .claude/hooks/...`). They only fire when
Claude is launched from the starter repo — so working in `D:\Projects\LEBOv2` captures
nothing.

Fix: add the hooks block to **user-global** `C:\Users\MD_Ki\.claude\settings.json`
(which already exists, currently permissions-only) using **absolute** paths:

```json
"hooks": {
  "UserPromptSubmit": [{"hooks": [{"type": "command",
    "command": "D:\\second-brain-starter\\.venv\\Scripts\\python.exe D:\\second-brain-starter\\.claude\\hooks\\session-start-context.py",
    "timeout": 15}]}],
  "Stop": [{"hooks": [{"type": "command",
    "command": "D:\\second-brain-starter\\.venv\\Scripts\\python.exe D:\\second-brain-starter\\.claude\\hooks\\session-end-flush.py",
    "timeout": 60}]}],
  "PreCompact": [{"hooks": [{"type": "command",
    "command": "D:\\second-brain-starter\\.venv\\Scripts\\python.exe D:\\second-brain-starter\\.claude\\hooks\\pre-compact-flush.py",
    "timeout": 30}]}]
}
```
Then remove (or keep as redundant) the project-level hooks in the starter repo.
**Watch out:** ensure `.env` (with `BRAIN_ROOT`, API key) is loaded by the hooks when
they run from an arbitrary cwd — see step 2 NOTE. Set `SECOND_BRAIN_API_KEY` / `BRAIN_ROOT`
as **user environment variables** (registry) so hooks have them regardless of cwd.

---

## 8. Session manager update

Edit `session_manager/config.json` — repoint the 6 project paths and the brain entry:

| id | old path | new path |
|----|----------|----------|
| `chimera` | …/10_Active_Projects/Project_Chimera | `D:/Projects/Project_Chimera` |
| `moviebuilder-bmad` | …/moviebuilder - BMAD MODULE Update | `D:/Projects/moviebuilder - BMAD MODULE Update` |
| `poe2-optimizer` | …/poe2_optimizer_v6 | `D:/Projects/poe2_optimizer_v6` |
| `lebo` | …/LEBOv2 | `D:/Projects/LEBOv2` |
| `last-epoch` (v1, archived) | …/LastEpochBuildOptimizer | **remove** (archived) |
| `10-active-projects` | …/10_Active_Projects | repoint → `D:/Projects` (rename "Projects") |
| `obsidian-brain` | …/Obsidian Brain/Brain | repoint → `D:/Brain` (rename "Brain") |

Add new entries if desired: `practice-local-model` → `D:/Projects/Practice local model`,
`video-gen` → `D:/Projects/Video Gen`.

Then **restart the service** (NSSM) so it reloads config:
```
nssm restart SecondBrainSessionManager   # confirm exact service name first
```

---

## 9. Regenerate Dashboard + index

- `D:\Brain\00_Meta\Dashboard.md`: update the **Code Locations** table from "(pending)"
  to live `D:\Projects\<name>` paths. Wikilinks become plain references (no Obsidian) — fine.
- Create `D:\Brain\10_Active_Projects\_index.md`? **No** — there's no `10_Active_Projects`
  in `D:\Brain` anymore. Instead keep a project index at `D:\Brain\00_Meta\projects-index.md`
  (or fold into Dashboard) listing the 6 projects + their `D:\Projects\` paths.
- Update `_load_project_index()` / `_get_project_last_touched()` in `heartbeat.py` (retired)
  and anything that scanned `10_Active_Projects` to scan `PROJECTS_ROOT` instead — for the
  future Dashboard generator.

---

## 10. Verification checklist (run after implementation)

- [ ] `python scripts/utils/vault_router.py "D:\Projects\LEBOv2"` → snapshot = `D:\Projects\LEBOv2\Snapshot.md`, learnings = `D:\Brain\20_Reference\Products\LEARNINGS.md`, core_memory points at `D:\Brain\00_Meta\{SOUL,USER}.md`
- [ ] `python scripts/utils/context_builder.py "D:\Projects\Project_Chimera"` → builds context, reads recent daily logs from `D:\Brain`
- [ ] Trigger a real session from `D:\Projects\LEBOv2` → confirm Stop hook writes to `D:\Brain\00_Meta\daily\<today>.md` AND updates `D:\Projects\LEBOv2\Snapshot.md`
- [ ] `python scripts/memory_reflect.py` → runs without touching HABITS; appends proposals to `D:\Brain\00_Meta\proposals\identity_proposals.md`
- [ ] `python scripts/token_report.py` → writes to `D:\Brain\Reports\Token Usage\`
- [ ] capture-idea / log-learning / project-context skills resolve to `D:\Brain` and `D:\Projects`
- [ ] Session manager lists projects at `D:\Projects\…` and can launch one
- [ ] `grep -rn "Obsidian Brain"` in the repo returns only historical docs (or nothing)

---

## 11. Rollback / safety

- Zip `D:\Obsidian Brain\` before deleting it (one-time backup).
- The path change is centralized via `BRAIN_ROOT` — reverting = change one env var back
  (plus the snapshot-reroute and guardrails edits).
- Do the **filesystem move** and **path edits** together, then verify, before deleting the
  old `D:\Obsidian Brain\` tree.

---

## 12. Open questions to confirm at implementation time

1. Delete old `D:\Obsidian Brain\` after verify, or keep zipped? (SOUL says confirm before delete.)
2. Should `BRAIN_ROOT` + `SECOND_BRAIN_API_KEY` be set as **user environment variables**
   (registry) so global hooks always see them? (Recommended yes.)
3. Reports rotation (226 token files) — fold into this migration or defer? (Defer OK.)
4. Rename `integrations/obsidian.py` → `vault_io.py`/`brain_io.py`? (Cosmetic; nice-to-have.)
