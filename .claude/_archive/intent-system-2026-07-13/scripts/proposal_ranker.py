#!/usr/bin/env python3
"""
proposal_ranker.py — Active-learning triage for /review-proposals.

The intent loop stalls when proposals pile up faster than Alec reviews them
(the 31-proposal backlog of 2026-06 is the canonical failure). Reviewing every
pending item by hand is the bottleneck — and most items aren't worth a decision
yet. This applies the active-learning principle (uncertainty x impact sampling):
score each pending proposal by how READY it is for a decision and how much it
would change behavior (IMPACT), surface only the highest-value few, and auto-defer
the rest so they keep accruing evidence instead of demanding attention.

It decides NOTHING. It only ORDERS and SUPPRESSES, so Alec spends his attention
on the decisions that teach the system the most per click. /review-proposals
consumes the SURFACE list as its queue; HOLD items are not asked this round.

Pure file reader — no API calls. Reuses parse_proposal_blocks from
proposal_extractor.py so the parse stays consistent with the writer.

Usage:
  python proposal_ranker.py                     # rank pending; top 5 surface
  python proposal_ranker.py --top 8             # surface more per round
  python proposal_ranker.py --include-deferred  # also re-rank ripe deferred items
  python proposal_ranker.py --all               # surface everything (no suppression)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from proposal_extractor import parse_proposal_blocks

DEFAULT_PROPOSALS = Path(r"D:\Brain\00_Meta\proposals\identity_proposals.md")

# ── impact: how much does promoting this change agent behavior? ──────────────
def impact_base(ptype: str, target: str) -> float:
    t = (ptype or "").lower()
    tgt = (target or "").lower()
    if "standing-order" in t:
        return 5.0          # changes every-session agent behavior
    if "contradiction" in t:
        return 5.0          # blocks coherence until resolved
    if "deprecate" in t or "update" in t:
        return 3.5
    if "strengthen" in t:
        return 2.0          # ratification of an existing entry — low novelty
    if "add" in t:
        if "intent" in tgt:
            return 4.0
        if "workflow" in tgt:
            return 3.0
        return 3.5
    return 3.0


# ── readiness: is there enough signal that a decision is informative now? ────
def confidence_weight(confidence: str) -> float:
    c = (confidence or "").lower()
    if "high" in c and "medium" in c:   # medium-high
        return 0.9
    if "high" in c:
        return 1.0
    if "low" in c and "medium" in c:    # low-medium / medium-low
        return 0.5
    if "medium" in c:
        return 0.75
    if "low" in c:
        return 0.3
    return 0.6


def _first_int(raw: str, label: str) -> int:
    nums = [int(n) for n in re.findall(rf"\*\*{re.escape(label)}:\*\*\s*(\d+)", raw)]
    return max(nums) if nums else 0


def _arrow_int(raw: str, label_pattern: str) -> int:
    """Pull the *new* value from an upgrade line, e.g. '...count:** 3 → 11' -> 11."""
    m = re.search(rf"\*\*{label_pattern}:\*\*[^\d]*\d+\s*(?:→|->)\s*(\d+)", raw)
    return int(m.group(1)) if m else 0


def _derive_confidence(raw: str) -> str:
    """Strengthen proposals carry 'Proposed confidence upgrade: medium → high'."""
    m = re.search(r"\*\*Proposed confidence(?: upgrade)?:\*\*\s*(.+)", raw)
    if not m:
        return ""
    am = re.search(r"(?:→|->)\s*([A-Za-z-]+)", m.group(1))
    return (am.group(1) if am else m.group(1)).strip()


def display_name(raw: str, proposed: str) -> str:
    m = re.search(r"\*\*Proposed name:\*\*\s*(.+)", raw)
    if m:
        return m.group(1).strip()
    m = re.search(r"\*\*Proposed:\*\*\s*(?:###\s*)?(.+)", raw)
    if m:
        return m.group(1).strip()
    # strengthen proposals name the entry they reinforce
    m = re.search(r"\*\*(?:Strengthens|Current value):\*\*\s*(.+)", raw)
    if m and "none" not in m.group(1).lower():
        return "strengthen → " + m.group(1).strip()
    return (proposed or "(unnamed)")[:70]


def score(p: dict, raw: str) -> dict:
    ptype = p.get("type", "")
    target = p.get("target", "")
    status = (p.get("status", "") or "").lower()
    confirmed = max(
        _first_int(raw, "Confirmed"),
        _arrow_int(raw, r"Proposed new confirmed count"),
        _arrow_int(raw, r"Proposed addition to confirmed count"),
    )
    gaps = _first_int(raw, "Gap accumulation")
    evidence_n = len(p.get("evidence", []) or [])
    signal = max(confirmed, gaps, evidence_n)
    critical = bool(re.search(r"\bCritical\b", raw))
    confidence = p.get("confidence") or _derive_confidence(raw)

    imp = impact_base(ptype, target) + (1.0 if critical else 0.0)
    cw = confidence_weight(confidence)
    priority = imp * cw + 0.2 * signal

    deferred = status.startswith("deferred")
    if deferred:
        priority *= 0.85   # already parked once; needs a reason to jump the queue

    return {
        "id": p.get("id", "?"),
        "name": display_name(raw, p.get("proposed", "")),
        "target": target or "?",
        "type": ptype or "?",
        "confidence": confidence or "?",
        "signal": signal,
        "critical": critical,
        "deferred": deferred,
        "priority": round(priority, 2),
        "_ptype": ptype.lower(),
        "_cw": cw,
    }


def suppressed_reason(s: dict) -> str:
    """Return a reason string if this item is below the evidence floor, else ''."""
    if "contradiction" in s["_ptype"] or "standing-order" in s["_ptype"]:
        return ""                       # always worth resolving / high impact
    if s["critical"]:
        return ""                       # override-tier evidence present
    if s["_cw"] <= 0.3 and s["signal"] < 2:
        return "low confidence + <2 confirmations — not informative yet"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    ap.add_argument("--top", type=int, default=5, help="how many to SURFACE per round")
    ap.add_argument("--include-deferred", action="store_true",
                    help="also re-rank items whose status is deferred")
    ap.add_argument("--all", action="store_true",
                    help="surface everything; disable the evidence-floor suppression")
    args = ap.parse_args()

    print("=" * 70)
    print("PROPOSAL TRIAGE — active-learning queue (readiness x impact)")
    print("Surfaces the few decisions worth Alec's attention; auto-defers the rest.")
    print("=" * 70)

    if not args.proposals.exists():
        print(f"\n_(proposals file not found: {args.proposals})_")
        return

    blocks_raw = {}
    text = args.proposals.read_text(encoding="utf-8")
    for block in re.split(r"\n---\n", "\n" + text):
        m = re.search(r"### (PROP-[\d-]+)", block)
        if m:
            blocks_raw[m.group(1)] = block

    parsed = parse_proposal_blocks(text)
    counts = {}
    candidates = []
    for p in parsed:
        status = (p.get("status", "") or "").lower()
        key = status.split()[0] if status else "unknown"
        counts[key] = counts.get(key, 0) + 1
        is_pending = status.startswith("pending") or status == ""
        is_deferred = status.startswith("deferred")
        if is_pending or (args.include_deferred and is_deferred):
            candidates.append(score(p, blocks_raw.get(p.get("id", ""), "")))

    status_line = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"\nQueue: {status_line}")

    if not candidates:
        scope = "pending or ripe-deferred" if args.include_deferred else "pending"
        print(f"\n✓ Queue clear — no {scope} proposals to review.")
        if not args.include_deferred and counts.get("deferred"):
            print(f"  ({counts['deferred']} deferred — re-run with --include-deferred to reconsider them.)")
        return

    for s in candidates:
        s["hold"] = "" if args.all else suppressed_reason(s)

    live = [s for s in candidates if not s["hold"]]
    floored = [s for s in candidates if s["hold"]]
    live.sort(key=lambda s: s["priority"], reverse=True)

    surface = live[: args.top]
    overflow = live[args.top:]

    print(f"\n{'─' * 70}")
    print(f"SURFACE — ask Alec, highest value first ({len(surface)} of {len(candidates)} candidates)")
    print(f"{'─' * 70}")
    for i, s in enumerate(surface, 1):
        flags = []
        if s["critical"]:
            flags.append("CRITICAL-evidence")
        if s["deferred"]:
            flags.append("was-deferred")
        tag = f"  [{', '.join(flags)}]" if flags else ""
        print(f"\n {i}. ⟐ {s['name']}")
        print(f"      {s['id']} · {s['type']} → {s['target']} · confidence={s['confidence']} · "
              f"signal={s['signal']} · priority={s['priority']}{tag}")
        print(f"      why: {why(s)}")

    if overflow:
        print(f"\n{'─' * 70}")
        print(f"HOLD — outside the top-{args.top} this round ({len(overflow)}) — re-surface as evidence grows")
        print(f"{'─' * 70}")
        for s in overflow:
            print(f"  · {s['id']} {s['name'][:54]} (priority={s['priority']})")

    if floored:
        print(f"\n{'─' * 70}")
        print(f"AUTO-DEFER — below the evidence floor ({len(floored)}) — not asked, kept accruing")
        print(f"{'─' * 70}")
        for s in floored:
            print(f"  · {s['id']} {s['name'][:48]} — {s['hold']}")

    print(f"\nPresent only the SURFACE families. Report HOLD/AUTO-DEFER as counts; do not ask about them.")
    print("=" * 70)


def why(s: dict) -> str:
    bits = []
    if "standing-order" in s["_ptype"]:
        bits.append("standing order — changes agent behavior every session")
    elif "contradiction" in s["_ptype"]:
        bits.append("contradiction — must be resolved to keep intent coherent")
    elif "strengthen" in s["_ptype"]:
        bits.append("ratifies an existing entry — cheap to confirm")
    if s["critical"]:
        bits.append("override-tier (Critical) evidence present")
    if s["deferred"]:
        bits.append("previously deferred, now re-ranked")
    if not bits:
        bits.append(f"{s['confidence']} confidence with {s['signal']} confirmation(s)")
    return "; ".join(bits)


if __name__ == "__main__":
    main()
