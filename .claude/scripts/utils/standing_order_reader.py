"""
standing_order_reader.py — Extracts active Standing Orders from intent.md and
formats them as agent directives with escalation protocol.

Called by context_builder.py at session start. Returns a formatted string
injected into session context. Returns empty string if no Standing Orders
are active — no noise in context when nothing is promoted yet.
"""
import re
from pathlib import Path


def load_standing_orders(intent_path: Path) -> list[dict]:
    """Parse intent.md and return all entries with **Standing order:** active."""
    if not intent_path.exists():
        return []

    text = intent_path.read_text(encoding="utf-8")
    orders = []

    blocks = re.split(r"\n(?=### )", text)
    for block in blocks:
        block = block.strip()
        if not block.startswith("### "):
            continue

        so_match = re.search(r"\*\*Standing order:\*\*\s*(.+)", block)
        if not so_match or so_match.group(1).strip().lower() != "active":
            continue

        entry: dict = {}

        name_match = re.match(r"### (.+)", block)
        entry["name"] = name_match.group(1).strip() if name_match else "unknown"

        for label, key in [
            ("Heuristic", "heuristic"),
            ("Tradeoff type", "tradeoff_type"),
            ("Agent instruction", "agent_instruction"),
            ("Active since", "active_since"),
            ("Context modifiers", "context_modifiers"),
        ]:
            m = re.search(
                rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\*\*|\Z)", block, re.DOTALL
            )
            entry[key] = m.group(1).strip() if m else ""

        orders.append(entry)

    return orders


def format_standing_orders(orders: list[dict]) -> str:
    """Format active Standing Orders as agent directive context."""
    if not orders:
        return ""

    count = len(orders)
    lines = [
        "## Standing Orders",
        f"({count} active directive{'s' if count != 1 else ''} — "
        "follow without asking for covered tradeoff types)\n",
    ]

    for o in orders:
        lines.append(f"### {o['name']}")
        if o.get("tradeoff_type"):
            lines.append(f"**Tradeoff type:** {o['tradeoff_type']}")
        if o.get("agent_instruction"):
            lines.append(f"**Directive:** {o['agent_instruction']}")
        if o.get("context_modifiers"):
            lines.append(f"**Applies when:** {o['context_modifiers']}")
        if o.get("active_since"):
            lines.append(f"**Active since:** {o['active_since']}")
        lines.append("")

    lines += [
        "## Escalation Protocol",
        "Override a Standing Order and ask Alec instead when:",
        "1. **Novel context** — tradeoff type matches but the situation is unlike any prior instance in the entry's session history",
        "2. **Conflicting orders** — two Standing Orders give opposite advice for the same decision",
        "3. **Critical override** — Alec says 'actually', 'wait', or 'stop'; treat as a non-negotiable correction and do not apply the order",
        "4. **Ambiguous tradeoff** — you cannot confidently identify which tradeoff type applies to this decision",
        "",
        "When escalating: name the Standing Order you would have followed and explain in one sentence why you're not.",
    ]

    return "\n".join(lines)


def load_decision_patterns(intent_path: Path) -> list[dict]:
    """Parse intent.md Decision Patterns (entries without an active Standing order)."""
    if not intent_path.exists():
        return []

    text = intent_path.read_text(encoding="utf-8")
    # Limit to the Decision Patterns section (stop at next ## heading)
    m = re.search(r"## Decision Patterns\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return []

    patterns = []
    blocks = re.split(r"\n(?=### )", m.group(1))
    for block in blocks:
        block = block.strip()
        if not block.startswith("### "):
            continue
        entry: dict = {"name": re.match(r"### (.+)", block).group(1).strip()}
        for label, key in [
            ("Heuristic", "heuristic"),
            ("Tradeoff type", "tradeoff_type"),
            ("Confidence", "confidence"),
        ]:
            fm = re.search(
                rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\*\*|\Z)", block, re.DOTALL
            )
            entry[key] = " ".join(fm.group(1).split()) if fm else ""
        patterns.append(entry)
    return patterns


def format_decision_patterns(patterns: list[dict]) -> str:
    """Format Decision Patterns as compact propose-then-act priors."""
    if not patterns:
        return ""

    lines = [
        "## Alec's Decision Patterns (propose-then-act)",
        "Learned heuristics for how Alec resolves tradeoffs. When a decision matches one:",
        "- **high confidence** → state \"Per your [pattern], doing X\" and proceed",
        "- **medium** → propose the pattern-consistent option and wait for the go-ahead",
        "- **low / low-medium** → treat as a weak prior; mention it only if relevant",
        "Every acceptance confirms the pattern; every override is counter-evidence — both get logged.",
        "",
    ]
    for p in patterns:
        conf = p.get("confidence", "?")
        tt = f" [{p['tradeoff_type']}]" if p.get("tradeoff_type") else ""
        lines.append(f"- **{p['name']}** ({conf}){tt}: {p.get('heuristic', '')}")
    return "\n".join(lines)


def get_standing_orders_context(vault_root: Path) -> str:
    """Main entry point for context_builder.py."""
    intent_path = vault_root / "00_Meta" / "intent.md"
    orders = load_standing_orders(intent_path)
    parts = [format_standing_orders(orders)]
    parts.append(format_decision_patterns(load_decision_patterns(intent_path)))
    return "\n\n".join(p for p in parts if p)
