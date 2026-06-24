#!/usr/bin/env python3
"""
transcript_intent_loader.py — Raw-transcript intent audit for /daily-reflect and /weekly-dream.

The reflect/dream loaders read only the Stop-hook DIGESTED daily logs. Two intent
signals never survive that digestion:
  1. Cross-session patterns — the extractor runs once per session, so a deliberate
     across-session habit (e.g. "one deep-dive per fresh session") is invisible.
  2. Boundary questions on autonomous runs — an autonomous session digests as an
     agent monologue and logs "AI gaps: none" even when Alec questioned things.

This script goes to ground truth: Alec's VERBATIM user turns in the raw Claude Code
transcripts (~/.claude/projects/<encoded>/*.jsonl), across ALL projects, for a
date window. It flags questioning / redirect / rejection turns and attaches the
adjacent assistant turns (before -> question -> after) so causality is visible.

Usage:
  python transcript_intent_loader.py --mode daily     # yesterday only (default)
  python transcript_intent_loader.py --mode weekly    # last 7 days
  python transcript_intent_loader.py --days N          # explicit lookback window

Pure file reader — no API calls. Prints a structured ledger to stdout for Claude
Code to fold into the synthesis, alongside the digested-log loaders.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import json
import re
from datetime import datetime, timedelta, date
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/New_York")   # Alec is EST/EDT
except Exception:  # pragma: no cover
    TZ = None

PROJECTS_ROOT = Path.home() / ".claude" / "projects"

# ── turns that are NOT Alec speaking (harness/tool/command noise) ───────────────
NOISE_PREFIXES = (
    "<task-notification>", "<command-name>", "<command-message>", "<local-command",
    "<system-reminder>", "caveat: the messages below", "<user-prompt-submit-hook>",
    "<bash-", "<post-tool", "[automated", "this session is being continued",
)

# ── questioning / redirect / rejection markers (case-insensitive) ───────────────
FLAG_PATTERNS = [
    r"\bwhy\b", r"\bwait\b", r"\bhold on\b", r"\bactually\b", r"on second thought",
    r"\bare we\b", r"\bdo we (have|need|still)\b", r"is there a reason", r"are you sure",
    r"just to (be sure|make sure|confirm|check)", r"\bshould(n'?t| we| i)\b",
    r"\bmissing\b", r"\binstead\b", r"\brather\b", r"\bstop\b", r"\bundo\b",
    r"that'?s (not|wrong|off)", r"not what", r"go back", r"\bno,? ", r"don'?t we",
    r"new session", r"is this a workflow", r"why (branch|are|is|do|would|did|not)",
    # quality-bar rejections
    r"\bhorrible\b", r"too bad", r"looks? like a typical", r"\bgeneric\b",
    r"missing character", r"\bugly\b", r"not (great|good|right|quite)",
    r"\[request interrupted",
]
FLAG_RE = re.compile("|".join(FLAG_PATTERNS), re.IGNORECASE)


def _local_dt(ts: str):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if TZ is not None:
            return dt.astimezone(TZ)
        return dt - timedelta(hours=4)
    except Exception:
        return None


def _clip(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n] + " …"


def _user_text(content):
    """Return Alec's typed text, or None if this 'user' message is a tool result."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content) and not parts:
            return None
        return " ".join(parts) if parts else None
    return None


def _assistant_brief(content) -> str:
    """One-line gist of an assistant turn: first text block, else its tool calls."""
    txt, tools = [], []
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                txt.append(b.get("text", ""))
            elif b.get("type") == "tool_use":
                name = b.get("name", "?")
                inp = b.get("input", {})
                hint = ""
                if isinstance(inp, dict):
                    hint = inp.get("description") or inp.get("subagent_type") or inp.get("command") or ""
                tools.append(f"{name}({_clip(str(hint), 60)})" if hint else name)
    elif isinstance(content, str):
        txt.append(content)
    t = " ".join(" ".join(txt).split())
    if t:
        return _clip(t, 240)
    if tools:
        return "[" + ", ".join(tools[:5]) + ("…" if len(tools) > 5 else "") + "]"
    return ""


def _is_noise(text: str) -> bool:
    low = text.strip().lower()
    return any(low.startswith(p) for p in NOISE_PREFIXES)


def load_events(path: Path):
    """Ordered list of (local_dt, role, text/gist). role in {user, assistant}."""
    evs = []
    try:
        f = path.open("r", encoding="utf-8", errors="replace")
    except Exception:
        return evs
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            typ = obj.get("type")
            msg = obj.get("message") or {}
            ldt = _local_dt(obj.get("timestamp", ""))
            if typ == "user" and msg.get("role") == "user" and not obj.get("isMeta"):
                t = _user_text(msg.get("content"))
                if t is None:
                    continue
                evs.append((ldt, "user", " ".join(t.split())))
            elif typ == "assistant" and msg.get("role") == "assistant":
                evs.append((ldt, "assistant", _assistant_brief(msg.get("content"))))
    return evs


def project_label(folder_name: str) -> str:
    """'D--Projects-Project-Chimera' -> 'Project-Chimera'; '...-TabletopMagic-TabletopMagic' -> 'TabletopMagic'."""
    name = folder_name
    for tok in ("D--Projects-", "C--Projects-", "D--", "C--Users-MD_Ki-"):
        if name.startswith(tok):
            name = name[len(tok):]
            break
    # collapse duplicated trailing segment (Foo-Foo -> Foo)
    parts = name.split("-")
    if len(parts) >= 2 and parts[-1] == parts[-2]:
        parts = parts[:-1]
    return "-".join(parts) or folder_name


# ── recurrence: corrections that repeat across sessions/projects ─────────────
# A flagged turn is one correction. The SAME correction recurring across sessions
# (and especially across PROJECTS) is the strongest preference signal available —
# the nearest thing to ground truth in a system with no objective outcome. The
# per-session digested logs structurally cannot surface this; the ledger can.
_SIG_STOP = {
    "the", "and", "for", "that", "this", "with", "you", "your", "are", "was",
    "but", "not", "have", "has", "had", "just", "like", "what", "when", "why",
    "how", "its", "it's", "i'm", "can", "could", "would", "should", "did",
    "does", "don't", "didn't", "isn't", "were", "they", "them", "then", "than",
    "there", "here", "into", "out", "off", "get", "got", "let", "yeah", "okay",
    "new", "one", "use", "using", "make", "made", "want", "need", "know",
    "think", "see", "look", "now", "also", "still", "really",
}


def _sig_tokens(text: str) -> set:
    toks = re.findall(r"[a-z][a-z']+", text.lower())
    return {t for t in toks if len(t) > 2 and t not in _SIG_STOP}


def recurring_corrections(flagged):
    """Greedy Jaccard clustering. flagged: list of (date, proj, sid, text)."""
    clusters = []  # each: {"tokens": set, "members": [(date, proj, sid, text)]}
    for row in flagged:
        toks = _sig_tokens(row[3])
        if len(toks) < 2:
            continue
        best, best_j = None, 0.0
        for c in clusters:
            inter = len(toks & c["tokens"])
            union = len(toks | c["tokens"])
            j = inter / union if union else 0.0
            if j > best_j:
                best, best_j = c, j
        if best is not None and best_j >= 0.45:
            best["members"].append(row)
            best["tokens"] |= toks
        else:
            clusters.append({"tokens": set(toks), "members": [row]})
    return clusters


def print_recurring(flagged):
    clusters = [c for c in recurring_corrections(flagged) if len(c["members"]) >= 2]
    print(f"\n{'=' * 70}")
    print("RECURRING CORRECTIONS — flagged turns that repeat across sessions/projects")
    print("A correction given repeatedly is the closest thing to ground truth in a")
    print("preference system — weight these hardest toward proposals / Standing Orders.")
    print("Cross-PROJECT recurrence (>1 project) is the strongest signal of a deep value.")
    print("=" * 70)
    if not clusters:
        print("\n_(no repeated corrections this window — every flagged turn is a one-off)_")
        return
    clusters.sort(
        key=lambda c: (len({m[1] for m in c["members"]}), len(c["members"])),
        reverse=True,
    )
    for c in clusters:
        members = sorted(c["members"], key=lambda m: m[0])
        projs = sorted({m[1] for m in members})
        sids = {(m[1], m[2]) for m in members}
        rep = min((m[3] for m in members), key=len)  # shortest member = cleanest
        marker = "  ⟳⟳" if len(projs) > 1 else "  ⟳ "
        print(f"\n{marker} ×{len(members)} · {len(projs)} project(s) · {len(sids)} session(s) — "
              f"\"{_clip(rep, 160)}\"")
        for date, proj, sid, _text in members:
            print(f"        {date} · {proj} · {sid}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["daily", "weekly"], default="daily")
    ap.add_argument("--days", type=int, default=None,
                    help="explicit lookback window in days (overrides --mode)")
    args = ap.parse_args()

    today = datetime.now(TZ).date() if TZ else date.today()
    if args.days is not None:
        window = {today - timedelta(days=i) for i in range(1, args.days + 1)}
        label = f"last {args.days} day(s)"
    elif args.mode == "weekly":
        window = {today - timedelta(days=i) for i in range(1, 8)}
        label = "last 7 days"
    else:
        window = {today - timedelta(days=1)}
        label = "yesterday"
    window_lo = min(window)

    print("=" * 70)
    print("RAW INTENT LEDGER — verbatim user turns from raw transcripts (GROUND TRUTH)")
    print(f"Window: {label}  ({min(window).isoformat()} … {max(window).isoformat()})")
    print("=" * 70)
    print(
        "\nWhy this exists: the digested daily logs miss (1) cross-session patterns\n"
        "(the per-session extractor can't see them) and (2) Alec's questioning at the\n"
        "boundaries of autonomous runs (digested as 'AI gaps: none'). These are Alec's\n"
        "ACTUAL words. Treat flagged (⚑) turns as primary evidence; read the before→after\n"
        "context for AI-gap causality. Cross-reference repeated turns across sessions for\n"
        "workflow patterns (e.g. deliberate fresh-session habits).\n"
    )

    if not PROJECTS_ROOT.exists():
        print(f"_(projects root not found: {PROJECTS_ROOT})_")
        return

    # gather candidate transcripts: mtime >= window_lo - 1 day (catch midnight-spanning)
    cutoff = datetime.combine(window_lo - timedelta(days=1), datetime.min.time())
    rows = []  # (turn_date, project, sid, local_dt, flagged, text, before, after)
    sessions_seen, projects_seen = set(), set()

    for proj_dir in sorted(PROJECTS_ROOT.iterdir()):
        if not proj_dir.is_dir():
            continue
        for jf in proj_dir.glob("*.jsonl"):
            try:
                if datetime.fromtimestamp(jf.stat().st_mtime) < cutoff:
                    continue
            except Exception:
                continue
            evs = load_events(jf)
            if not evs:
                continue
            proj = project_label(proj_dir.name)
            sid = jf.stem[:8]
            for i, (ldt, role, text) in enumerate(evs):
                if role != "user" or ldt is None:
                    continue
                if ldt.date() not in window:
                    continue
                if _is_noise(text):
                    continue
                interrupted = text.strip().lower().startswith("[request interrupted")
                flagged = interrupted or bool(FLAG_RE.search(text))
                before = after = ""
                if flagged:
                    for j in range(i - 1, max(-1, i - 4), -1):
                        if evs[j][1] == "assistant" and evs[j][2]:
                            before = evs[j][2]
                            break
                    for j in range(i + 1, min(len(evs), i + 4)):
                        if evs[j][1] == "assistant" and evs[j][2]:
                            after = evs[j][2]
                            break
                rows.append((ldt.date().isoformat(), proj, sid, ldt, flagged, text, before, after))
                sessions_seen.add((proj, sid))
                projects_seen.add(proj)

    if not rows:
        print("_(no user turns found in raw transcripts for this window)_")
        print("\n## END OF RAW INTENT LEDGER")
        return

    flagged_n = sum(1 for r in rows if r[4])
    print(f"Found {len(rows)} user turns ({flagged_n} flagged ⚑) across "
          f"{len(sessions_seen)} sessions in {len(projects_seen)} project(s).\n")

    rows.sort(key=lambda r: (r[0], r[1], r[3]))
    cur_key = None
    for tdate, proj, sid, ldt, flagged, text, before, after in rows:
        key = (tdate, proj, sid)
        if key != cur_key:
            cur_key = key
            print(f"\n{'─'*78}\n### {tdate} · {proj} · session {sid}\n{'─'*78}")
        stamp = ldt.strftime("%H:%M")
        if flagged:
            print(f"\n  ⚑ [{stamp}] ALEC: {_clip(text, 700)}")
            if before:
                print(f"        before · claude: {before}")
            if after:
                print(f"        after  · claude: {after}")
        else:
            print(f"    [{stamp}] ALEC: {_clip(text, 500)}")

    flagged = [(r[0], r[1], r[2], r[5]) for r in rows if r[4]]
    print_recurring(flagged)

    print("\n## END OF RAW INTENT LEDGER")
    print("=" * 70)


if __name__ == "__main__":
    main()
