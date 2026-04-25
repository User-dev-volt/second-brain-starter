---
name: project-context
description: Surface full context for any of Alec's projects — where he left off, what's in progress, what's next, recent GitHub activity. Triggers on /project-context <project-name>.
argument-hint: <project-name>
---

# Project Context Recovery

Instantly orient Alec on any project — what phase it's in, last action, decisions in flight, and recent GitHub activity.

## Parameters

- **`$0`** (required) — Project name or slug (e.g., `moviebuilder`, `Project_Chimera`, `poe2_optimizer_v6`)

## Workflow

1. **Resolve the project name** — If no argument provided, list available projects from `${CLAUDE_SKILL_DIR}/references/project-list.md` and ask which one. Fuzzy-match the argument against known slugs (case-insensitive, partial match OK).

2. **Load the project snapshot** — Read the file directly:
   `D:\Obsidian Brain\Brain\10_Active_Projects\<slug>\Snapshot.md`
   If no snapshot exists, say so and offer to create one by reading the folder contents.

3. **Search memory for recent learnings** — Run:
   ```
   D:\second-brain-starter\.venv\Scripts\python D:\second-brain-starter\.claude\scripts\memory\memory_search.py "<project-name>" --top 5
   ```
   If memory search fails (index not built), skip gracefully — do not error out.

4. **Fetch recent GitHub activity** — Run:
   ```
   D:\second-brain-starter\.venv\Scripts\python D:\second-brain-starter\.claude\scripts\query.py github activity --days 7
   ```
   Filter the output to only the repo matching this project (use the repo mapping in `${CLAUDE_SKILL_DIR}/references/project-list.md`). If GITHUB_PAT is not set, skip this step and note it.

5. **Present a consolidated context brief** in this format:

```
## <Project Name> — Context Brief
_<date>_

**Phase:** <current phase>
**Momentum:** <health/status>
**Last Touched:** <date>

### Where You Left Off
<current focus / last action from snapshot>

### Next Action
<the single next step>

### Mental RAM
<key decisions and context from snapshot>

### Recent GitHub Activity (last 7 days)
<commits for this repo, or "No activity / not tracked">

### Related Learnings
<top 2-3 memory search results, or "No indexed learnings yet">
```

6. **Update last-touched timestamp** — Append to or update `Last Touched` in the `Snapshot.md` file directly.

## Notes

- Project slugs with spaces should be quoted: `project-context "Video Gen"`
- If memory search hasn't been indexed yet, remind Alec to run `python .claude/scripts/memory/memory_index.py` once
- Always lead with the Next Action — that's the most useful thing
