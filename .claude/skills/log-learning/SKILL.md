---
name: log-learning
description: Log a code pattern, solution, or insight from the current session to the permanent knowledge base. Triggers on /log-learning <learning text> or when the SessionEnd hook detects a reusable pattern.
argument-hint: <learning text> [--category godot-csharp|comfyui|unity|product|general]
---

# Learning Logger

Accumulate game dev and product knowledge from every AI-assisted session. Anything you figure out, keep.

## Parameters

- **`$0`** (required) — The learning, pattern, or solution to log
- `--category` (optional) — Which knowledge area to file it under. Auto-detected from CWD if not provided.

## Categories and Their Files

| Category | File |
|----------|------|
| `godot-csharp` | `20_Reference/GameDev/learnings/godot-csharp.md` |
| `comfyui` | `20_Reference/GameDev/learnings/comfyui.md` |
| `unity` | `20_Reference/GameDev/learnings/unity.md` |
| `product` | `20_Reference/Products/learnings/product.md` |
| `general` | `20_Reference/GameDev/learnings/general.md` |

## Workflow

1. **Parse the learning** — Extract text from `$0`. If nothing provided, ask: "What's the learning?"

2. **Infer category from CWD** if `--category` not specified:
   - Godot/game engine dirs → `godot-csharp`
   - ComfyUI dirs → `comfyui`
   - Unity dirs → `unity`
   - MovieBuilder/product dirs → `product`
   - Else → `general`

3. **Log the learning** — Run:
   ```
   python .claude/scripts/query.py obsidian learning "<learning text>" --category <category>
   ```

4. **Confirm:** `Logged to <category> → <file path>`

## Format Written to Learning File

```markdown
## 2026-04-08
<learning text>
```

## What Makes a Good Learning

Log it when:
- You solved something that took >10 minutes to figure out
- You found a pattern that will apply to future work
- Claude gave you a solution you'd want to find again
- Something failed in a non-obvious way and you found the fix

Don't log:
- One-off fixes that won't recur
- Things that are obvious from the docs
- Project-specific decisions (those go in the project snapshot)

## Auto-trigger from SessionEnd Hook

The SessionEnd hook calls this skill automatically when it detects:
- A code snippet with an explanatory comment
- A "the fix was..." or "what worked was..." statement
- A Godot/ComfyUI/Unity-specific pattern
