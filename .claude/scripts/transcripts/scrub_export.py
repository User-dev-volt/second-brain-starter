"""Copy Claude Code transcripts to an export folder with secrets redacted.

Usage: python scrub_export.py OUT_DIR [--top N]
Picks the N largest *.jsonl under ~/.claude/projects (all if --top omitted),
redacts anything that looks like a credential, and reports redaction counts.
"""
import argparse
import re
from pathlib import Path

PATTERNS = {
    "anthropic": r"sk-ant-[A-Za-z0-9_\-]{20,}",
    "openai": r"(?<![A-Za-z0-9_\-])sk-(?:proj-)?[A-Za-z0-9_\-]{20,}",
    "github": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}",
    "databricks": r"dapi[a-f0-9]{32}(?:-\d)?",
    "aws": r"AKIA[0-9A-Z]{16}",
    "google": r"AIza[0-9A-Za-z_\-]{35}",
    "huggingface": r"hf_[A-Za-z0-9]{30,}",
    "slack": r"xox[abprs]-[A-Za-z0-9\-]{10,}",
    "bearer": r"(?i)bearer\s+[A-Za-z0-9._\-]{20,}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    "assignment": r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b((?:\\?[\"'])?\s*[:=]\s*(?:\\?[\"'])?)[A-Za-z0-9._\-/+]{12,}",
}
COMPILED = {k: re.compile(v, re.S) for k, v in PATTERNS.items()}


def scrub(text, counts):
    for name, rx in COMPILED.items():
        if name == "assignment":
            text, n = rx.subn(lambda m: m.group(0)[: m.start(1) - m.start(0)] + m.group(1) + "[REDACTED]", text)
        else:
            text, n = rx.subn(f"[REDACTED:{name}]", text)
        counts[name] = counts.get(name, 0) + n
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--top", type=int)
    args = ap.parse_args()

    root = Path.home() / ".claude" / "projects"
    files = sorted(root.rglob("*.jsonl"),
                   key=lambda p: p.stat().st_size, reverse=True)
    if args.top:
        files = files[: args.top]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for f in files:
        # full relative path, e.g. <project>__<session>__subagents__agent-x.jsonl,
        # keeps projects distinct and ties subagent files to their parent session
        dest = out / "__".join(f.relative_to(root).parts)
        dest.write_text(scrub(f.read_text(encoding="utf-8", errors="replace"), counts), encoding="utf-8")

    total_mb = sum(p.stat().st_size for p in out.glob("*.jsonl")) / 1e6
    print(f"exported {len(files)} files, {total_mb:.0f} MB -> {out}")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        if v:
            print(f"  redacted {k}: {v}")


if __name__ == "__main__":
    main()
