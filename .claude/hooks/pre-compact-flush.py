#!/usr/bin/env python3
"""
pre-compact-flush.py — Preserve BMAD project state across compaction.

Claude Code hook: PreCompact. If a BMAD project is active in cwd, emit a
structured state snapshot as additionalContext so the compaction summary retains
enough for the BMAD orchestrator to reconstruct its state on the next turn.

The Claude API extraction that also wrote a [PreCompact] summary to the daily log
was removed 2026-07-13 with the intent-system archival (consistent with dropping
the same per-session extraction from the Stop hook). Only the BMAD-recovery
snapshot remains — see .claude/_archive/intent-system-2026-07-13/.
"""
import json
import os
import re
import sys
from pathlib import Path


def snapshot_bmad_state(cwd: str) -> str:
    """
    If a BMAD project is active in cwd, return a structured state snapshot
    to inject into the compaction summary so the orchestrator can recover.
    Returns empty string if no BMAD project detected.
    """
    cwd_path = Path(cwd)
    bmad_output = cwd_path / "_bmad-output"
    if not bmad_output.exists():
        return ""

    lines = ["=== BMAD_STATE_SNAPSHOT (survive compaction) ==="]
    lines.append(f"project_root: {cwd}")

    # project-intent.md
    intent = bmad_output / "project-intent.md"
    if intent.exists():
        lines.append("project_intent: PRESENT")

    # planning artifacts — read frontmatter stepsCompleted from each
    planning = bmad_output / "planning-artifacts"
    if planning.exists():
        for artifact in sorted(planning.glob("*.md")):
            try:
                text = artifact.read_text(encoding="utf-8", errors="replace")
                # Extract stepsCompleted or workflowStatus from frontmatter
                steps = re.search(r"stepsCompleted:\s*(.+)", text)
                status = re.search(r"workflowStatus:\s*(.+)", text)
                info = []
                if steps:
                    info.append(f"steps={steps.group(1).strip()}")
                if status:
                    info.append(f"status={status.group(1).strip()}")
                lines.append(f"artifact: {artifact.name} [{', '.join(info) if info else 'present'}]")
            except Exception:
                lines.append(f"artifact: {artifact.name}")

    # sprint-status.yaml
    sprint = bmad_output / "implementation-artifacts" / "sprint-status.yaml"
    if sprint.exists():
        try:
            sprint_text = sprint.read_text(encoding="utf-8", errors="replace")
            # Extract in-progress story if any
            in_progress = re.findall(r"(\S+):\s*in-progress", sprint_text)
            ready = re.findall(r"(\S+):\s*ready-for-dev", sprint_text)
            if in_progress:
                lines.append(f"sprint_in_progress: {in_progress}")
            if ready:
                lines.append(f"sprint_ready_for_dev: {ready[:3]}")  # first 3
        except Exception:
            lines.append("sprint_status: present")

    lines.append("RECOVERY_INSTRUCTION: On next turn, the BMAD Orchestrator must read")
    lines.append("project-intent.md and all planning artifact frontmatter to reconstruct")
    lines.append("state before continuing. Do NOT assume prior conversation memory is intact.")
    lines.append("=== END BMAD_STATE_SNAPSHOT ===")

    return "\n".join(lines)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd", os.getcwd())

    bmad_snapshot = snapshot_bmad_state(cwd)
    if bmad_snapshot:
        print(json.dumps({"additionalContext": bmad_snapshot}))


if __name__ == "__main__":
    main()
