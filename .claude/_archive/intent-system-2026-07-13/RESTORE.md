# Intent System — Archived 2026-07-13

The second-brain **intent system** was archived on 2026-07-13. It aimed to learn
Alec's decision preferences (Standing Orders / Decision Patterns), capture per-session
"intent signals," and synthesize them nightly into proposals for promotion. In practice
the loop never closed: `/daily-reflect` generated corroborations every morning but the
pending queue sat "9 deep and nine cycles overdue" for `/review-proposals`, and the
per-session intent modeling wasn't reliably capturing intent. It was also adding
~1–2k tokens of Standing Orders to every session injection across all projects.

**Everything here was moved, not deleted — this is fully reversible.**

## What was archived

| Item | Original location |
|------|-------------------|
| `scripts/*.py` (run_daily_reflect, memory_reflect, memory_reflect_loader, weekly_dream_loader, transcript_intent_loader, proposal_extractor, proposal_ranker, consistency_check) | `.claude/scripts/` |
| `scripts/standing_order_reader.py` | `.claude/scripts/utils/` |
| `commands/daily-reflect.md`, `commands/weekly-dream.md` | `.claude/commands/` |
| `skills/review-proposals/` | `.claude/skills/` |
| `skills-global/review-proposals/` | `C:\Users\MD_Ki\.claude\skills\` |
| `tests/memory_reflect/` | `.claude/tests/` |
| `intent.md`, `workflow.md`, `bmad_rituals.md` | `D:\Brain\30_Archive\intent-system-2026-07-13\` (data) |

## What was KEPT (not part of the intent system)
- **AutoSave** — the git auto-commit + snapshot "Last Touched" update. It lived inside
  `session-end-flush.py`; that hook was rewritten to do *only* AutoSave.
- **BMAD compaction-recovery** — `pre-compact-flush.py` was reduced to only its
  `snapshot_bmad_state` (emits BMAD state as additionalContext across compaction).
- SOUL.md, USER.md, Snapshots, LEARNINGS.md, daily logs, session-start context injection.

## Wiring that was severed (restore these to revive the system)
1. **`.claude/scripts/utils/context_builder.py`** — removed `from standing_order_reader
   import get_standing_orders_context` and the block that appended Standing Orders to the
   session injection.
2. **`.claude/hooks/session-end-flush.py`** — rewritten to AutoSave-only. The removed
   Claude-extraction logic (intent signals + SECTION 2 summary → daily log / Snapshot
   Next Action / LEARNINGS) is in git history.
3. **`.claude/hooks/pre-compact-flush.py`** — rewritten to BMAD-snapshot-only. The removed
   Claude daily-log extraction is in git history.
4. **Windows scheduled task `SecondBrainDailyReflect`** (daily 08:00 → run_daily_reflect.py)
   was unregistered.

## To restore
```bash
A=".claude/_archive/intent-system-2026-07-13"
# code
mv "$A"/scripts/standing_order_reader.py .claude/scripts/utils/
mv "$A"/scripts/*.py .claude/scripts/
mv "$A"/commands/*.md .claude/commands/
mv "$A"/skills/review-proposals .claude/skills/
mv "$A"/skills-global/review-proposals "$USERPROFILE/.claude/skills/"
mv "$A"/tests/memory_reflect .claude/tests/
# data
mv "D:/Brain/30_Archive/intent-system-2026-07-13/"*.md "D:/Brain/00_Meta/"
```
Then: restore the `context_builder.py` import + Standing Orders block, restore the two
hook files from git history (they were rewritten in the archival commit — `git log`
around 2026-07-13), and re-run `python .claude/scripts/setup/register_tasks.py` to
re-create the scheduled task.
