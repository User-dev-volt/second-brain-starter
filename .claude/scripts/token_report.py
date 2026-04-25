"""
Token usage report generator — reads token-dashboard SQLite DB and outputs
a markdown report to the Obsidian vault Reports/Token Usage folder.
Calls Claude API to append intelligent analysis to the report.
Scheduled every 4 hours via Windows Task Scheduler (SecondBrain/TokenReport).
"""

import sqlite3
import subprocess
import sys
import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
_env_file = SCRIPTS_DIR.parent.parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

DB_PATH = Path.home() / ".claude" / "token-dashboard.db"
DASHBOARD_CLI = Path.home() / "tools" / "token-dashboard" / "cli.py"
REPORT_DIR = Path(r"D:\Obsidian Brain\Brain\Reports\Token Usage")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

PYTHON = sys.executable


def run_cli(*args):
    result = subprocess.run(
        [PYTHON, str(DASHBOARD_CLI), *args],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def query(db, sql, params=()):
    return db.execute(sql, params).fetchall()


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def generate_report():
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d_%H00")
    report_path = REPORT_DIR / f"{ts}.md"

    # Refresh the DB before querying
    run_cli("scan")

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    # ── Today summary ──────────────────────────────────────────────────────────
    today = query(db, """
        SELECT
            COUNT(DISTINCT session_id) AS sessions,
            COUNT(*) AS turns,
            COALESCE(SUM(input_tokens),0) AS input,
            COALESCE(SUM(output_tokens),0) AS output,
            COALESCE(SUM(cache_read_tokens),0) AS cache_read,
            COALESCE(SUM(cache_create_5m_tokens + cache_create_1h_tokens),0) AS cache_create
        FROM messages
        WHERE type='assistant' AND timestamp >= ?
    """, (today_start,))[0]

    # ── All-time summary ───────────────────────────────────────────────────────
    alltime = query(db, """
        SELECT
            COUNT(DISTINCT session_id) AS sessions,
            COUNT(*) AS turns,
            COALESCE(SUM(input_tokens),0) AS input,
            COALESCE(SUM(output_tokens),0) AS output,
            COALESCE(SUM(cache_read_tokens),0) AS cache_read,
            COALESCE(SUM(cache_create_5m_tokens + cache_create_1h_tokens),0) AS cache_create
        FROM messages WHERE type='assistant'
    """)[0]

    # ── 7-day model breakdown ──────────────────────────────────────────────────
    models = query(db, """
        SELECT
            COALESCE(model,'unknown') AS model,
            COUNT(*) AS turns,
            COALESCE(SUM(input_tokens),0) AS input,
            COALESCE(SUM(output_tokens),0) AS output,
            COALESCE(SUM(cache_read_tokens),0) AS cache_read
        FROM messages
        WHERE type='assistant' AND timestamp >= ?
        GROUP BY model ORDER BY (input+output+cache_read) DESC
    """, (week_ago,))

    # ── Top projects last 7 days ───────────────────────────────────────────────
    projects = query(db, """
        SELECT
            COALESCE(project_slug,'unknown') AS project,
            COUNT(DISTINCT session_id) AS sessions,
            COUNT(*) AS turns,
            COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens),0) AS total_tokens,
            COALESCE(SUM(cache_read_tokens),0) AS cache_read
        FROM messages
        WHERE type='assistant' AND timestamp >= ?
        GROUP BY project_slug ORDER BY total_tokens DESC LIMIT 10
    """, (week_ago,))

    # ── Hourly pattern today ───────────────────────────────────────────────────
    hourly = query(db, """
        SELECT
            CAST(substr(timestamp,12,2) AS INTEGER) AS hour,
            COALESCE(SUM(input_tokens + output_tokens + cache_read_tokens),0) AS total
        FROM messages
        WHERE type='assistant' AND timestamp >= ?
        GROUP BY hour ORDER BY hour
    """, (today_start,))

    # ── Top repeat-read files (last 7 days) ────────────────────────────────────
    repeat_reads = query(db, """
        SELECT
            target,
            COUNT(*) AS reads,
            COUNT(DISTINCT session_id) AS sessions,
            COALESCE(SUM(result_tokens),0) AS tokens
        FROM tool_calls
        WHERE tool_name='Read' AND timestamp >= ?
        GROUP BY target HAVING reads >= 3
        ORDER BY reads DESC LIMIT 15
    """, (week_ago,))

    # ── Top tool calls today ───────────────────────────────────────────────────
    tools_today = query(db, """
        SELECT tool_name, COUNT(*) AS calls, COALESCE(SUM(result_tokens),0) AS tokens
        FROM tool_calls WHERE timestamp >= ?
        GROUP BY tool_name ORDER BY calls DESC LIMIT 10
    """, (today_start,))

    # ── 30-day daily trend ─────────────────────────────────────────────────────
    daily_trend = query(db, """
        SELECT
            substr(timestamp,1,10) AS day,
            COALESCE(SUM(input_tokens + output_tokens),0) AS tokens,
            COALESCE(SUM(cache_read_tokens),0) AS cache_read,
            COUNT(DISTINCT session_id) AS sessions
        FROM messages
        WHERE type='assistant' AND timestamp >= ?
        GROUP BY day ORDER BY day DESC LIMIT 14
    """, (month_ago,))

    db.close()

    # ── Fetch tips from CLI ────────────────────────────────────────────────────
    tips_raw = run_cli("tips")

    # ── Build report ──────────────────────────────────────────────────────────
    lines = [
        f"# Token Usage Report — {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        "> Auto-generated every 4 hours by token-report script + token-dashboard",
        "",
        "---",
        "",
        "## Today at a Glance",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Sessions | {today['sessions']} |",
        f"| Turns | {today['turns']} |",
        f"| Input tokens | {fmt_tokens(today['input'])} |",
        f"| Output tokens | {fmt_tokens(today['output'])} |",
        f"| Cache READ | **{fmt_tokens(today['cache_read'])}** |",
        f"| Cache CREATE | {fmt_tokens(today['cache_create'])} |",
        f"| Total (input+output) | {fmt_tokens(today['input'] + today['output'])} |",
        "",
    ]

    # Cache efficiency note
    if today['cache_read'] > 0 and (today['input'] + today['cache_read']) > 0:
        cache_pct = today['cache_read'] / (today['input'] + today['cache_read']) * 100
        lines += [f"> Cache hit rate today: **{cache_pct:.1f}%** of context served from cache", ""]

    lines += [
        "## All-Time Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total sessions | {alltime['sessions']} |",
        f"| Total turns | {alltime['turns']} |",
        f"| Total input | {fmt_tokens(alltime['input'])} |",
        f"| Total output | {fmt_tokens(alltime['output'])} |",
        f"| Total cache read | {fmt_tokens(alltime['cache_read'])} |",
        "",
        "---",
        "",
        "## Model Usage (Last 7 Days)",
        "",
        "| Model | Turns | Input | Output | Cache Read |",
        "|-------|-------|-------|--------|------------|",
    ]
    for m in models:
        lines.append(
            f"| {m['model']} | {m['turns']} | {fmt_tokens(m['input'])} | {fmt_tokens(m['output'])} | {fmt_tokens(m['cache_read'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Top Projects by Token Consumption (Last 7 Days)",
        "",
        "| Project | Sessions | Turns | Total Tokens | Cache Read |",
        "|---------|----------|-------|--------------|------------|",
    ]
    for p in projects:
        slug = p['project'][-40:] if p['project'] else 'unknown'
        lines.append(
            f"| `{slug}` | {p['sessions']} | {p['turns']} | {fmt_tokens(p['total_tokens'])} | {fmt_tokens(p['cache_read'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Hourly Distribution (Today)",
        "",
        "| Hour | Tokens | Bar |",
        "|------|--------|-----|",
    ]
    if hourly:
        max_h = max(r['total'] for r in hourly) or 1
        for h in hourly:
            bar = "█" * int(h['total'] / max_h * 20)
            lines.append(f"| {h['hour']:02d}:00 | {fmt_tokens(h['total'])} | {bar} |")

    lines += [
        "",
        "---",
        "",
        "## 14-Day Daily Trend",
        "",
        "| Date | Sessions | Tokens | Cache Read |",
        "|------|----------|--------|------------|",
    ]
    for d in daily_trend:
        lines.append(
            f"| {d['day']} | {d['sessions']} | {fmt_tokens(d['tokens'])} | {fmt_tokens(d['cache_read'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Top Repeat-Read Files (Last 7 Days)",
        "",
        "These files are being re-read most often — prime candidates to summarize into CLAUDE.md.",
        "",
        "| File | Reads | Sessions | Tokens Read |",
        "|------|-------|----------|-------------|",
    ]
    for r in repeat_reads:
        fname = r['target'][-60:] if r['target'] else ''
        lines.append(f"| `...{fname}` | {r['reads']} | {r['sessions']} | {fmt_tokens(r['tokens'])} |")

    lines += [
        "",
        "---",
        "",
        "## Tool Call Breakdown (Today)",
        "",
        "| Tool | Calls | Result Tokens |",
        "|------|-------|---------------|",
    ]
    for t in tools_today:
        lines.append(f"| {t['tool_name']} | {t['calls']} | {fmt_tokens(t['tokens'])} |")

    lines += [
        "",
        "---",
        "",
        "## Optimization Tips (from token-dashboard)",
        "",
        "```",
        tips_raw,
        "```",
        "",
        "---",
        "",
        "## Analysis Notes",
        "",
        "_Pending Claude analysis..._",
        "",
        f"*Report generated: {now.isoformat()}*",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[token_report] Saved: {report_path}", file=sys.stderr)
    return str(report_path), "\n".join(lines)


def call_claude_analysis(report_markdown: str) -> str:
    """Call Claude API to analyze the token report and return analysis markdown."""
    try:
        import anthropic
    except ImportError:
        return "_anthropic package not installed — skipping analysis._"

    client = anthropic.Anthropic()

    prompt = f"""You are analyzing a Claude Code token usage report for a developer named Alec.
Read the report below and write a concise, actionable analysis covering:

1. **Top cost driver** — what single thing is consuming the most tokens and why
2. **Cache health** — is the cache hit rate healthy? Any patterns worth noting?
3. **Repeat-read hotspots** — list the 3 most wasteful files with a specific CLAUDE.md fix for each
4. **Sonnet → Haiku triage** — flag specific task types or projects that could safely switch to Haiku (e.g. file reads, simple transforms, status checks)
5. **Trend alert** — any concerning daily trend (spike, creep, anomaly)?
6. **One quick win** — the single change that would have the biggest token reduction impact

Be specific: use file names and numbers from the report. Keep each point to 2-3 sentences max.

---

{report_markdown}
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"[token_report] Claude call failed: {e}", file=sys.stderr)
        return f"_Claude analysis failed: {e}_"


def generate_and_analyze():
    report_path_str, report_markdown = generate_report()
    report_path = Path(report_path_str)

    print("[token_report] Calling Claude for analysis...", file=sys.stderr)
    analysis = call_claude_analysis(report_markdown)

    content = report_path.read_text(encoding="utf-8")
    content = content.replace("_Pending Claude analysis..._", analysis)
    report_path.write_text(content, encoding="utf-8")

    print(f"Analysis complete: {report_path_str}")
    return report_path_str


if __name__ == "__main__":
    path = generate_and_analyze()
    print(path)
