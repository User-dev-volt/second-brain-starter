"""
proposal_extractor.py — Extracts soul.md / user.md proposals from daily session logs.

Called by memory_reflect.py (daily at 8 AM) and testable via test_runner.py.
When mock_response is passed to extract(), skips the Claude API call entirely.
"""

import json
import os
import re
import sys
from pathlib import Path

PROP_ID_RE = re.compile(r"PROP-\d{4}-\d{2}-\d{2}-\d{3}")


def parse_proposal_blocks(text: str) -> list[dict]:
    """Parse all ### PROP-... blocks from a markdown string into dicts."""
    proposals = []
    blocks = re.split(r"\n---\n", "\n" + text)
    for block in blocks:
        block = block.strip()
        if not block or "### PROP-" not in block:
            continue
        p = {}

        id_match = re.search(r"### (PROP-[\d-]+)", block)
        if id_match:
            p["id"] = id_match.group(1)

        for label, key in [
            ("Target", "target"),
            ("Type", "type"),
            ("Proposed", "proposed"),
            ("Current value", "current_value"),
            ("Confidence", "confidence"),
            ("Status", "status"),
        ]:
            m = re.search(
                rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?=\n\*\*|\Z)",
                block,
                re.DOTALL,
            )
            if m:
                val = m.group(1).strip()
                if val != "_(none — new addition)_":
                    p[key] = val

        ev_match = re.search(r"\*\*Evidence:\*\*\n(.*?)(?=\n\*\*|\Z)", block, re.DOTALL)
        if ev_match:
            lines = [
                l.strip()
                for l in ev_match.group(1).strip().splitlines()
                if l.strip().startswith("-")
            ]
            p["evidence"] = lines

        src_match = re.search(r"\*\*Source logs:\*\*\s*(.+)", block)
        if src_match:
            p["source_logs"] = [s.strip() for s in src_match.group(1).split(",")]

        proposals.append(p)
    return proposals


class ProposalExtractor:
    """
    Extracts soul.md / user.md proposals from daily session logs.

    Interface compatible with StubExtractor in test_runner.py:
      extractor = ProposalExtractor(vault_path, proposals_path)
      proposals = extractor.extract(log_text, log_date, mock_response=None)
      formatted  = extractor.format_proposals(proposals, log_date)
      extractor.write_proposals(formatted)
    """

    def __init__(self, vault_path: Path, proposals_path: Path):
        self.vault_path = Path(vault_path)
        self.proposals_path = Path(proposals_path)
        self._existing = self._load_existing()
        self._soul = self._load_doc("SOUL.md")
        self._user_profile = self._load_doc("user.md")

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def _load_existing(self) -> list[dict]:
        if not self.proposals_path.exists():
            return []
        return parse_proposal_blocks(self.proposals_path.read_text(encoding="utf-8"))

    def _load_doc(self, filename: str) -> str:
        path = self.vault_path / "00_Meta" / filename
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _api_key(self) -> str:
        key = os.environ.get("SECOND_BRAIN_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                    try:
                        key, _ = winreg.QueryValueEx(reg, "SECOND_BRAIN_API_KEY")
                    except FileNotFoundError:
                        key, _ = winreg.QueryValueEx(reg, "ANTHROPIC_API_KEY")
            except Exception:
                pass
        return key

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def _is_suppressed(self, proposal: dict) -> tuple[bool, str]:
        """Return (suppressed, reason). Checks against implemented and rejected proposals."""
        candidate = proposal.get("proposed", "").lower().strip()
        for existing in self._existing:
            status = existing.get("status", "")
            existing_text = existing.get("proposed", "").lower().strip()
            if existing_text == candidate:
                if status == "implemented":
                    return True, f"already implemented ({existing['id']})"
                if status.startswith("rejected"):
                    return True, f"previously rejected ({existing['id']}): {status}"
        return False, ""

    # ------------------------------------------------------------------
    # Claude call
    # ------------------------------------------------------------------

    def _existing_summary(self) -> str:
        if not self._existing:
            return "None."
        lines = []
        for p in self._existing:
            status = p.get("status", "unknown")
            target = p.get("target", "?")
            proposed = p.get("proposed", "")[:120]
            lines.append(f"- [{status.upper()}] ({target}) {proposed}")
        return "\n".join(lines)

    def _call_claude(self, log_text: str, log_date: str) -> dict:
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError("No API key found (SECOND_BRAIN_API_KEY or ANTHROPIC_API_KEY)")

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are reviewing a session log from {log_date} to identify additions or updates worth making to two identity documents: soul.md and user.md.

## Current soul.md
{self._soul}

## Current user.md
{self._user_profile}

## Existing proposals — do NOT re-propose anything on this list
{self._existing_summary()}

## Session log to analyze
{log_text}

---

Identify patterns that represent stable identity traits, preferences, or behavioral tendencies.

Rules:
- Require at least 2 distinct evidence points from this log — single mentions do not qualify
- Do not re-propose anything already listed above (implemented or rejected)
- type "add": new entry that does not exist in the current document
- type "update": meaningfully more accurate than the current entry — not a rewording
- type "deprecate": only if there is strong evidence the current entry is now consistently wrong
- confidence "high" = 4+ evidence points; confidence "medium" = 2–3 evidence points
- Return an empty proposals array if nothing meets the threshold

Respond ONLY with valid JSON in this exact shape:
{{
  "proposals": [
    {{
      "target": "soul.md",
      "type": "add",
      "proposed": "...",
      "current_value": null,
      "evidence": ["{log_date}: observation", "{log_date}: observation"],
      "source_logs": ["{log_date}"],
      "confidence": "medium"
    }}
  ]
}}

For update or deprecate, current_value must be the exact text from the document being replaced or removed."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        return json.loads(text)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(
        self, log_text: str, log_date: str, mock_response: dict | None = None
    ) -> list[dict]:
        """
        Process a log and return filtered proposals.
        Pass mock_response to skip the Claude API call (used by test_runner).
        """
        if mock_response is not None:
            raw = mock_response.get("proposals", [])
        else:
            try:
                result = self._call_claude(log_text, log_date)
                raw = result.get("proposals", [])
            except Exception as e:
                print(f"[proposal_extractor] Claude call failed: {e}", file=sys.stderr)
                return []

        accepted = []
        for p in raw:
            suppressed, reason = self._is_suppressed(p)
            if suppressed:
                print(
                    f"    [suppressed] {p.get('proposed', '')[:60]}... — {reason}",
                    file=sys.stderr,
                )
                continue
            accepted.append(p)
        return accepted

    def _next_id_start(self, log_date: str) -> int:
        """Find the next available sequence number for proposals on log_date."""
        pattern = re.compile(rf"PROP-{re.escape(log_date)}-(\d{{3}})")
        nums = [
            int(m.group(1))
            for p in self._existing
            for m in [pattern.search(p.get("id", ""))]
            if m
        ]
        return max(nums, default=0) + 1

    def format_proposals(self, proposals: list[dict], log_date: str) -> str:
        """Format accepted proposals as markdown blocks ready to append."""
        if not proposals:
            return ""
        start = self._next_id_start(log_date)
        blocks = []
        for i, p in enumerate(proposals):
            prop_id = f"PROP-{log_date}-{start + i:03d}"
            current_val = p.get("current_value") or "_(none — new addition)_"
            evidence_lines = "\n".join(f"- {e}" for e in p.get("evidence", []))
            source_logs = ", ".join(p.get("source_logs", [log_date]))
            block = f"""---

### {prop_id}
**Target:** {p["target"]}
**Type:** {p["type"]}
**Proposed:** {p["proposed"]}
**Current value:** {current_val}
**Evidence:**
{evidence_lines}
**Source logs:** {source_logs}
**Confidence:** {p["confidence"]}
**Status:** pending"""
            blocks.append(block)
        return "\n\n".join(blocks)

    def write_proposals(self, formatted: str) -> None:
        """Append formatted proposal blocks to the proposals file."""
        if not formatted.strip():
            return
        self.proposals_path.parent.mkdir(parents=True, exist_ok=True)
        with self.proposals_path.open("a", encoding="utf-8") as f:
            f.write("\n\n" + formatted)
        count = formatted.count("### PROP-")
        print(f"[proposal_extractor] Wrote {count} proposal(s).", file=sys.stderr)
