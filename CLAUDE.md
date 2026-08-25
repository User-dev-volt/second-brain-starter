# Repository pointer

## Project Chimera does not live on `main`

If you were asked to work on **Project Chimera** — the worldbuilding project with gates, `HANDOFF.md`
and `decisions.md` — those files are **not on this branch** and never have been. They are on
`claude/greatest-story-narrative-xx8w8o`, under `chimera/`.

Fresh containers check out `main`, so `chimera/` will be missing and `git log --all` will look empty.
**That is a fetch problem, not lost work.** `--all` only walks refs that already exist locally, and
that branch has not been fetched yet.

Run this first:

```bash
git fetch origin claude/greatest-story-narrative-xx8w8o
git checkout claude/greatest-story-narrative-xx8w8o
ls chimera/
```

Then read `chimera/HANDOFF.md`, then `chimera/decisions.md`, then the gate you were asked to work on.

**Do not** report the Chimera files as missing, unrecoverable, or in another repo until you have run
the fetch above. Two sessions have already lost time to this.

### State as of this pointer

- **Gate 1 — the system:** closed and approved (`chimera/gate-1-system.md`)
- **Gate 2 — the traditions:** closed and approved (`chimera/gate-2-traditions.md`)
- **Gate 3 — the loophole and the atrocity:** open, and the next thing to build
