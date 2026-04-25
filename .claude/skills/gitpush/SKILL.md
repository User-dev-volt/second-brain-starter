---
name: gitpush
description: Commit and push the current project to the correct GitHub account, routed via .gitaccount config. Supports SSH setup, custom messages, and account listing.
argument-hint: [--setup | --list | --message "text" | --commit-only | --account <alias>]
---

# Git Push (Multi-Account)

Routes commits and pushes to the correct GitHub account based on the project's `.gitaccount` config.

## Parameters

- `--setup` — One-time project setup: update `~/.ssh/config` from detected keys, rewrite remote URL to use SSH alias
- `--list` — List all GitHub accounts detected from `~/.ssh/github_*` keys
- `--message "text"` (or `-m "text"`) — Custom commit message (default: `[AutoSave] YYYY-MM-DD HH:MM`)
- `--commit-only` — Stage and commit but do not push
- `--account <alias>` — Override account for this push (ignores .gitaccount)

## Workflow

### --setup (first-time project configuration)

1. Run SSH manager to detect keys and update config:
   ```
   python .claude/scripts/git/ssh_manager.py --no-validate
   ```
2. Show the user which accounts are available (aliases).
3. Ask: "Which account alias should this project use? (e.g. `alec-personal`)"
4. Ask: "What branch? (default: `main`)"
5. Ask: "Enable auto_commit and auto_push on SessionEnd? (yes/no, default: yes)"
6. Write `.gitaccount` at the project root with the user's answers.
7. Run setup to rewrite remote and validate:
   ```
   python .claude/scripts/git/auto_commit.py --cwd . --setup
   ```
8. Confirm: "Project configured. Future sessions will auto-commit and push to `github-<alias>`."

### --list

Run:
```
python .claude/scripts/git/ssh_manager.py --list
```
Display each detected account: alias, SSH host, and GitHub username from the public key.

### Default (commit + push)

1. Build the command from args:
   ```
   python .claude/scripts/git/auto_commit.py --cwd <cwd> --verbose [--message "..."] [--commit-only]
   ```
   Use the current working directory for `--cwd`.

2. If `--account <alias>` was provided:
   - Temporarily load the project config, override the account field, and pass `--message` if not set.
   - Inform the user: "Overriding account to `<alias>` for this push."

3. Report the result in one line:
   - Success: `Pushed to github-<alias>/<branch> — "<commit message>"`
   - Commit-only: `Committed (not pushed) — "<commit message>"`
   - No changes: `Nothing to commit.`
   - Error: show the error message from stderr and suggest `/gitpush --setup` if the remote URL may be wrong.

## .gitaccount Format

When creating `.gitaccount`, write it as JSON:

```json
{
  "account": "<alias>",
  "auto_commit": true,
  "auto_push": true,
  "branch": "main",
  "commit_prefix": "[AutoSave]"
}
```

Place at the project root (same level as `.git/`). This file should be committed to the repo.

## Notes

- SSH keys must be named `~/.ssh/github_<alias>` (private) and `~/.ssh/github_<alias>.pub` (public)
- The managed block in `~/.ssh/config` is between `=== second-brain: git accounts ===` markers — do not edit manually
- After `--setup`, the remote URL is permanently rewritten to `git@github-<alias>:user/repo.git`
- Auto-commit runs on every SessionEnd for projects with `auto_commit: true` in `.gitaccount`
