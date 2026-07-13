"""
proposal_extractor.py — Extracts identity proposals from daily session logs.

Targets: soul.md, user.md, intent.md, workflow.md
Evidence is structured as tradeoff pairs (offered/chosen/type/tier), not surface decisions.
Called by the /daily-reflect slash command and testable via test_runner.py.
When mock_response is passed to extract(), skips the Claude API call entirely.
"""

import json
import os
import re
import sys
from pathlib import Path

PROP_ID_RE = re.compile(r"PROP-\d{4}-\d{2}-\d{2}-\d{3}")

VALID_TARGETS = {"soul.md", "user.md", "intent.md", "workflow.md"}
VALID_TYPES = {"add", "update", "deprecate", "strengthen", "contradiction", "standing-order"}


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
            ("Source", "source"),
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
    Extracts identity proposals from daily session logs.
    Targets: soul.md, user.md, intent.md, workflow.md

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
        self._intent = self._load_doc("intent.md")
        self._workflow = self._load_doc("workflow.md")

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

        intent_section = f"\n## Current intent.md\n{self._intent}" if self._intent else ""
        workflow_section = f"\n## Current workflow.md\n{self._workflow}" if self._workflow else ""

        prompt = f"""You are reviewing a session log from {log_date} to extract behavioral intent proposals.

## Current soul.md
{self._soul}

## Current user.md
{self._user_profile}
{intent_section}
{workflow_section}

## Existing proposals — do NOT re-propose anything on this list
{self._existing_summary()}

## Session log to analyze
{log_text}

---

Identify tradeoff patterns and behavioral signals that belong in one of these documents:
- **intent.md**: How Alec makes decisions — heuristics, tradeoff resolutions, revealed preferences
- **workflow.md**: How Alec structures and executes work — procedural patterns
- **soul.md**: Stable identity values — who Alec is
- **user.md**: Profile facts — stack, projects, communication style

Evidence tiers (rank each piece of evidence before assessing thresholds):
- **Critical**: "actually", "wait", "stop", or mid-session self-correction. One instance
  qualifies for proposal if the tradeoff type matches an existing intent.md pattern.
- **Highest**: Response to an AI clarifying question — instinctive, unguarded choice.
- **High (AI gap)**: Claude heading toward X → Alec redirected to Y. The strongest
  *passive* signal — no self-reflection required. AI gaps from the **AI gaps** section
  of the log are automatically High tier. Two gaps resolving the same tradeoff type
  the same way qualify for a proposal even without other evidence.
- **High**: Unprompted scope expansion — adding something not requested.
- **Medium**: Explicit rejection of AI suggestion with stated reason.
- **Low**: Single mention, no decision attached — accumulate only, never promote alone.

For each session, identify:
1. What binary or multiple-choice questions did the AI ask? What did the user pick?
   Classify the tradeoff type (control vs. convenience, ownership vs. delegation,
   speed vs. durability, depth vs. breadth, manual vs. automated, local vs. cloud, explicit vs. implicit).
2. Were there any "actually", "wait", "stop" moments? What was corrected?
3. Check the **AI gaps** section: for each gap, classify the tradeoff type and resolution
   direction. This is the most reliable signal in the log — prioritize it.
4. Did the user expand scope unprompted? In what direction?
5. Do these signals confirm an existing intent.md pattern or suggest a new one?

Proposal rules:
- Require 2+ evidence points of the same tradeoff type (same session), OR 1+ confirming an existing intent.md pattern
- Two AI gap instances resolving the same tradeoff type the same way → qualifies regardless of other evidence
- Do not re-propose anything already listed above (implemented or rejected)
- type "add": new entry that does not exist in the current document
- type "update": meaningfully more accurate than current — not a rewording
- type "deprecate": strong evidence current entry is consistently wrong
- type "strengthen": adds a confirming instance to an existing intent.md pattern (no text change to heuristic)
- type "contradiction": two intent.md entries that produce contradictory predictions for the same scenario
- confidence "high" = 4+ evidence points; confidence "medium" = 2–3 evidence points
- source is always "daily-reflect"
- Return empty proposals array if nothing meets the threshold

For intent.md proposals that include AI gap evidence: include a **Gap accumulation:** line
in the proposed text to track gap instances:
  **Gap accumulation:** N gaps — [tradeoff type] → [direction] each time (YYYY-MM-DD, ...)
Omit this line for proposals with no AI gap evidence.

Evidence format for intent.md proposals:
  "YYYY-MM-DD [project] [tradeoff type] [tier]: [offered] → [chosen] — \\"reason\\""
  Tiers: Critical | Highest | High (AI gap) | High | Medium | Low

Respond ONLY with valid JSON:
{{
  "proposals": [
    {{
      "target": "intent.md",
      "type": "add",
      "source": "daily-reflect",
      "proposed": "...",
      "current_value": null,
      "evidence": [
        "{log_date} [project] [tradeoff type] [tier]: [offered] → [chosen] — \\"reason\\""
      ],
      "source_logs": ["{log_date}"],
      "confidence": "medium"
    }}
  ]
}}

For update, deprecate, strengthen, or contradiction: current_value must be the exact text being replaced or the entry being strengthened/contradicted."""

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

    def format_proposals(
        self, proposals: list[dict], log_date: str, source: str = "daily-reflect"
    ) -> str:
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
            prop_source = p.get("source") or source
            block = f"""---

### {prop_id}
**Target:** {p["target"]}
**Type:** {p["type"]}
**Source:** {prop_source}
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
