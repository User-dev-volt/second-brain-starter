# AutoSave — what it is, where it lives, and how it's gated

The `[AutoSave] <timestamp>` commits in projects like LEBOv2 are **not** a Scheduled Task,
a file-watcher, a timer, or a git hook. They are produced by a **global Claude Code `Stop`
hook** that is part of this Second Brain repo.

## The chain

```
C:\Users\MD_Ki\.claude\settings.json   ("Stop" hook, user-global -> applies to every project)
  -> D:\second-brain-starter\.claude\hooks\session-end-flush.py   (main() -> run_git_auto_commit(cwd))
       -> D:\second-brain-starter\.claude\scripts\git\auto_commit.py   (auto_commit_push)
            git add -A  ->  git commit -m "[AutoSave] <YYYY-MM-DD HH:MM>"  ->  git push origin <branch>
       config per repo: <repo>\.gitaccount   (auto_commit / auto_push / branch / commit_prefix)
       account routing/defaults: git_router.py
```

**Cadence is per-response, not a clock.** The `Stop` hook fires after *every* assistant
response; `auto_commit.py` no-ops when `git status` is clean. During active dev that lands
roughly every 10–30 min — which is why it *looked* like a timer. The commit **author**
(`Alec <projectchimeraue5@gmail.com>`) comes from the repo's local/global git config, not
`.gitaccount`.

> Because the hook is user-global, a project's own `.git/hooks` and `.claude/` can be empty
> and it will still autosave. `auto_commit.py` is **shared by every repo** that has a
> `.gitaccount` with `auto_commit: true`, so anything you change in it affects them all —
> keep per-project behavior in that project's `.gitaccount`.

## The safety gate (`pre_commit_check`)

Without a gate the hook commits **and pushes** whatever is on disk at the tick, so a
transient/mid-edit broken state can become a permanent commit on `main` (and `origin/main`).

`auto_commit.py` now supports an **optional, per-project** `pre_commit_check` command in
`.gitaccount`. Before staging, it runs that command in the repo; **only exit 0 allows the
commit.** On non-zero/timeout the commit is skipped and the changes are left uncommitted in
the working tree, to be retried on the next `Stop` (nothing is lost). Repos without the key
are completely unaffected.

```jsonc
// <repo>\.gitaccount
"pre_commit_check": "<command that exits 0 = safe, non-0 = block>",
"pre_commit_check_timeout": 240   // seconds; default 240
```

### LEBOv2's gate — `pre_commit_gate.py`

LEBOv2's `.gitaccount` points `pre_commit_check` at `pre_commit_gate.py --dir D:/Projects/LEBOv2/lebo`,
which gates on:

1. **Fast skip** — if no `lebo/src/**` source or build config (`package.json`,
   `tsconfig*.json`, `vite|vitest.config.*`) changed, the commit is allowed without running
   anything (doc/asset-only autosaves stay instant).
2. **Typecheck** — `pnpm -C <dir> exec tsc --noEmit` must pass (~6s).
3. **Tests, baseline-aware** — `pnpm -C <dir> exec vitest run` must introduce **no _new_
   failures** vs. a recorded baseline (~28s). LEBOv2's suite is not fully green today (see
   below), so a strict "all green" gate would freeze autosave; instead the baseline tolerates
   already-failing tests and **ratchets**: whenever the current failure set is a strict subset
   of the baseline, the baseline is rewritten to the smaller set, so a once-failing test that
   gets fixed becomes protected against regressions too.

Exit codes: `0` allow · `2` typecheck failed · `3` no test results · `4` new test failure(s).

**Baseline file:** `.autosave-baselines/<repo-name>.json` (next to the gate script). Delete it
to re-seed from the current state; edit it to hand-curate the tolerated set.

**Current LEBOv2 baseline (8 pre-existing failures — predate the gate; fixing them tightens it):**
`ProviderSelector.test.tsx` (×5) + `Settings.test.tsx` "renders the ProviderSelector" + 
`SkillTreeCanvas.test.tsx` "onContextMenu…" + `TreeControls.test.tsx` "RESET button calls onReset".

### Timeouts

A gate adds its runtime to the `Stop` hook. The relevant ceilings were raised so a ~35s gate
fits (they are only ceilings — no-gate repos finish in <1s, so nothing else is slowed):

| where | was | now |
|---|---|---|
| `settings.json` Stop hook `timeout` | 60 | 300 |
| `session-end-flush.py` `run_git_auto_commit` subprocess | 30 | 270 |
| `.gitaccount` `pre_commit_check_timeout` | — | 240 |
| `pre_commit_gate.py` `TSC_TIMEOUT` / `VITEST_TIMEOUT` | — | 45 / 150 |

> The `settings.json` hook timeout may require restarting a Claude session to take full effect.
> A normal ~35s gate fits under the old 60s too; only an unusually slow cold run could be
> clipped pre-restart (harmless — that checkpoint is just retried next tick).

## Operating it

- **Tune what LEBOv2 gates on** — edit the `pre_commit_check` command in `D:\Projects\LEBOv2\.gitaccount`
  (e.g. drop `vitest` for a faster typecheck-only gate, or add `&& pnpm -C … build`).
- **Disable the gate for a repo** — remove `pre_commit_check` from its `.gitaccount`.
- **Add the gate to another TS/Vite repo** — add a `pre_commit_check` line pointing at
  `pre_commit_gate.py --dir <that app dir>`; it self-seeds a baseline on first run.
- **Reset the baseline** — delete `.autosave-baselines/<repo>.json`.
