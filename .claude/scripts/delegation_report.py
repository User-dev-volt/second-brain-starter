"""
delegation_report.py — is the subagent routing actually working?

Reads the token-dashboard SQLite DB and reports spend split by main-loop vs
subagent (is_sidechain) and by model, so the effect of pinning subagents to
cheaper models is visible as a number rather than a feeling.

Usage:
    python delegation_report.py [--days N] [--project SLUG] [--since YYYY-MM-DD]

Baseline note: subagent model routing was changed 2026-09-15 (scout=haiku,
implementer/reviewer=sonnet, CLAUDE_CODE_SUBAGENT_MODEL=sonnet). Compare a
window before that date against one after.
"""

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "token-dashboard.db"

# $ per 1M tokens: (input, output). Cache reads bill at ~0.1x input,
# 5m cache writes at ~1.25x input.
PRICING = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-opus-5": (5.00, 25.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-fable-5-1": (10.00, 50.00),
    "claude-fable-5": (10.00, 50.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def price(model: str):
    if not model:
        return None
    for key, rates in PRICING.items():
        if model.startswith(key):
            return rates
    return None


def cost(model, inp, out, cache_read, cache_5m, cache_1h):
    rates = price(model)
    if rates is None:
        return None
    pin, pout = rates
    return (
        inp * pin
        + out * pout
        + cache_read * pin * 0.10
        + (cache_5m * 1.25 + cache_1h * 2.00) * pin
    ) / 1_000_000


def fmt(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}k"
    return str(int(n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--since", help="YYYY-MM-DD; overrides --days")
    ap.add_argument("--project", help="project_slug filter, e.g. D--second-brain-starter")
    ap.add_argument(
        "--out", nargs="?", const="DEFAULT", default=None,
        help="also write a dated markdown report; bare flag uses "
             "$BRAIN_ROOT/Reports/Token Usage/",
    )
    args = ap.parse_args()

    if not DB_PATH.exists():
        raise SystemExit(f"token-dashboard DB not found at {DB_PATH}")

    where = ["model IS NOT NULL", "model != ''"]
    params = []
    if args.since:
        where.append("timestamp >= ?")
        params.append(args.since)
    else:
        where.append("timestamp >= datetime('now', ?)")
        params.append(f"-{args.days} days")
    if args.project:
        where.append("project_slug = ?")
        params.append(args.project)

    sql = f"""
        SELECT COALESCE(is_sidechain, 0) AS side, model,
               COUNT(*) AS msgs,
               SUM(COALESCE(input_tokens,0)),
               SUM(COALESCE(output_tokens,0)),
               SUM(COALESCE(cache_read_tokens,0)),
               SUM(COALESCE(cache_create_5m_tokens,0)),
               SUM(COALESCE(cache_create_1h_tokens,0))
        FROM messages
        WHERE {' AND '.join(where)}
        GROUP BY side, model
        ORDER BY side, 4 DESC
    """

    db = sqlite3.connect(str(DB_PATH))
    rows = db.execute(sql, params).fetchall()
    if not rows:
        raise SystemExit("no rows in that window")

    window = args.since or f"last {args.days} days"
    proj = args.project or "all projects"

    out = []
    def emit(line=""):
        out.append(line)

    emit(f"Delegation report — {window}, {proj}")
    emit(f"generated {datetime.now():%Y-%m-%d %H:%M}")
    emit()

    totals = {0: 0.0, 1: 0.0}
    mix = {0: {}, 1: {}}
    unpriced = set()

    for side_label, side in (("MAIN LOOP", 0), ("SUBAGENTS", 1)):
        subset = [r for r in rows if r[0] == side]
        if not subset:
            continue
        emit(f"  {side_label}")
        emit(f"    {'model':<22}{'msgs':>7}{'in':>9}{'out':>9}{'cache rd':>10}{'cost':>10}")
        for _, model, msgs, inp, o, crd, c5, c1 in subset:
            c = cost(model, inp, o, crd, c5, c1)
            if c is None:
                unpriced.add(model)
                cstr = "    n/a"
            else:
                totals[side] += c
                mix[side][model] = mix[side].get(model, 0.0) + c
                cstr = f"${c:,.2f}"
            emit(f"    {model:<22}{msgs:>7}{fmt(inp):>9}{fmt(o):>9}{fmt(crd):>10}{cstr:>10}")
        emit(f"    {'':<22}{'':>7}{'':>9}{'':>9}{'subtotal':>10}{f'${totals[side]:,.2f}':>10}")
        emit()

    grand = totals[0] + totals[1]
    if grand > 0:
        share = 100 * totals[1] / grand
        emit(f"  TOTAL ${grand:,.2f}   —   subagents {share:.1f}% of spend")
        emit()
        # the headline: what share of SUBAGENT spend is on cheap models
        cheap = sum(v for k, v in mix[1].items()
                    if k.startswith(("claude-sonnet", "claude-haiku")))
        if totals[1] > 0:
            emit(f"  Subagent spend on sonnet/haiku: ${cheap:,.2f} "
                 f"({100*cheap/totals[1]:.1f}% of subagent spend)")
            emit("    baseline 2026-09-15 was 0.0% — routing pinned scout=haiku,")
            emit("    implementer/reviewer=sonnet, CLAUDE_CODE_SUBAGENT_MODEL=sonnet")
        emit()
        emit("  Working:     cheap-model share up, TOTAL down, no rework.")
        emit("  Not working: subagent share up but TOTAL flat/up = rework;")
        emit("               move the delegation boundary, don't blame the model.")
    if unpriced:
        emit()
        emit(f"  (unpriced models, excluded from cost: {', '.join(sorted(unpriced))})")

    text = "\n".join(out)
    print("\n" + text)

    if args.out is not None:
        if args.out == "DEFAULT":
            root = Path(os.environ.get("BRAIN_ROOT", r"D:\Brain"))
            dest_dir = root / "Reports" / "Token Usage"
        else:
            dest_dir = Path(args.out)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"delegation-{datetime.now():%Y-%m-%d}.md"
        dest.write_text(f"# Delegation report\n\n```\n{text}\n```\n", encoding="utf-8")
        print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
