"""
test_runner.py — Validates proposal extractor output against expected fixtures.

Uses stubbed Claude responses so tests are deterministic and free (no API calls).

Usage:
    python test_runner.py              # run all tests
    python test_runner.py --test 01    # run specific test by number
    python test_runner.py --list       # list available tests
    python test_runner.py --verbose    # show full diffs on failure
"""

import sys
import re
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
SAMPLE_LOGS_DIR = FIXTURES_DIR / "sample_logs"
CLAUDE_RESPONSES_DIR = FIXTURES_DIR / "claude_responses"
VAULT_DIR = FIXTURES_DIR / "vault"
PROPOSALS_PATH = VAULT_DIR / "00_Meta" / "proposals" / "identity_proposals.md"
EXPECTED_DIR = TESTS_DIR / "expected_outputs"

PROP_ID_RE = re.compile(r"PROP-\d{4}-\d{2}-\d{2}-\d{3}")
REQUIRED_FIELDS = {"target", "type", "source", "proposed", "confidence", "status"}
UPDATE_DEPRECATE_FIELDS = {"current_value"}  # additionally required for update/deprecate
VALID_TYPES = {"add", "update", "deprecate", "strengthen", "contradiction"}


# ---------------------------------------------------------------------------
# Proposal parser — shared by runner and extractor
# ---------------------------------------------------------------------------

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

        ev_match = re.search(
            r"\*\*Evidence:\*\*\n(.*?)(?=\n\*\*|\Z)", block, re.DOTALL
        )
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


# ---------------------------------------------------------------------------
# Extractor stub — replaced by real extractor once built
# ---------------------------------------------------------------------------

class StubExtractor:
    """
    Stands in for the real ProposalExtractor.
    Loads a pre-recorded Claude response from fixtures instead of calling the API.
    Implements the same interface the real extractor will expose.
    """

    def __init__(self, vault_path: Path, proposals_path: Path):
        self.vault_path = vault_path
        self.proposals_path = proposals_path
        self._existing = self._load_existing()

    def _load_existing(self) -> list[dict]:
        if not self.proposals_path.exists():
            return []
        return parse_proposal_blocks(self.proposals_path.read_text(encoding="utf-8"))

    def _is_suppressed(self, proposal: dict) -> tuple[bool, str]:
        """Return (suppressed, reason) for a candidate proposal."""
        candidate_text = proposal.get("proposed", "").lower()
        for existing in self._existing:
            status = existing.get("status", "")
            existing_text = existing.get("proposed", "").lower()
            if existing_text == candidate_text:
                if status == "implemented":
                    return True, f"already implemented ({existing['id']})"
                if status.startswith("rejected"):
                    return True, f"previously rejected ({existing['id']}): {status}"
        return False, ""

    def extract(self, log_text: str, log_date: str, mock_response: dict) -> list[dict]:
        """
        Process a log and return filtered proposals.
        mock_response: the dict that would come back from Claude (injected in tests).
        """
        raw = mock_response.get("proposals", [])
        accepted = []
        for p in raw:
            suppressed, reason = self._is_suppressed(p)
            if suppressed:
                print(f"    [suppressed] {p.get('proposed', '')[:60]}... — {reason}")
                continue
            accepted.append(p)
        return accepted

    def format_proposals(self, proposals: list[dict], log_date: str, source: str = "daily-reflect") -> str:
        """Format accepted proposals as markdown blocks ready to append."""
        if not proposals:
            return ""
        lines = []
        for i, p in enumerate(proposals, start=1):
            prop_id = f"PROP-{log_date}-{i:03d}"
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
            lines.append(block)
        return "\n\n".join(lines)


def load_extractor():
    """Try to import the real extractor; fall back to stub with a warning."""
    try:
        scripts_dir = Path(__file__).parent.parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))
        from proposal_extractor import ProposalExtractor
        return ProposalExtractor, False
    except ImportError:
        return StubExtractor, True


# ---------------------------------------------------------------------------
# Test comparison
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    skipped: bool = False
    message: str = ""
    details: list[str] = field(default_factory=list)


def normalize_id(text: str) -> str:
    """Replace any PROP-YYYY-MM-DD-NNN with {{PROP_ID}} for comparison."""
    return PROP_ID_RE.sub("{{PROP_ID}}", text)


def validate_proposal_fields(p: dict, idx: int) -> list[str]:
    """Return list of field validation errors for a single proposal."""
    errors = []
    if not PROP_ID_RE.match(p.get("id", "")):
        errors.append(f"  proposal {idx}: invalid or missing ID format")
    for f in REQUIRED_FIELDS:
        if f not in p:
            errors.append(f"  proposal {idx}: missing required field '{f}'")
    if p.get("type") not in VALID_TYPES:
        errors.append(f"  proposal {idx}: invalid type '{p.get('type')}'; expected one of {VALID_TYPES}")
    if p.get("type") in ("update", "deprecate"):
        if "current_value" not in p:
            errors.append(f"  proposal {idx}: update/deprecate must include 'current_value'")
    if p.get("status") != "pending":
        errors.append(f"  proposal {idx}: new proposals must have status 'pending', got '{p.get('status')}'")
    evidence = p.get("evidence", [])
    if len(evidence) < 2:
        errors.append(f"  proposal {idx}: too few evidence entries ({len(evidence)}); minimum 2")
    return errors


def compare(actual_text: str, expected_text: str, verbose: bool) -> tuple[bool, list[str]]:
    """Compare actual vs expected proposal output. Returns (passed, error_lines)."""
    if expected_text.strip().startswith("# EXPECT: no proposals"):
        if actual_text.strip():
            return False, [f"  expected no proposals, but got:\n{actual_text[:400]}"]
        return True, []

    actual_proposals = parse_proposal_blocks(actual_text)
    expected_proposals = parse_proposal_blocks(normalize_id(expected_text).replace(
        "{{PROP_ID}}", "PROP-0000-00-000"
    ))

    errors = []

    if len(actual_proposals) != len(expected_proposals):
        errors.append(
            f"  expected {len(expected_proposals)} proposal(s), got {len(actual_proposals)}"
        )
        return False, errors

    for i, (act, exp) in enumerate(zip(actual_proposals, expected_proposals), start=1):
        errors.extend(validate_proposal_fields(act, i))
        for key in ("target", "type", "source", "proposed", "current_value", "confidence"):
            if key not in exp:
                continue
            if act.get(key) != exp.get(key):
                errors.append(
                    f"  proposal {i} '{key}':\n"
                    f"    expected: {exp.get(key)}\n"
                    f"    actual:   {act.get(key)}"
                )
        exp_ev = exp.get("evidence", [])
        act_ev = act.get("evidence", [])
        if len(act_ev) != len(exp_ev):
            errors.append(
                f"  proposal {i} evidence count: expected {len(exp_ev)}, got {len(act_ev)}"
            )

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_test(test_num: str, extractor_class, using_stub: bool, verbose: bool) -> TestResult:
    log_files = sorted(SAMPLE_LOGS_DIR.glob(f"{test_num}_*.md"))
    if not log_files:
        return TestResult(test_num, False, message=f"no sample log matching '{test_num}_*.md'")
    log_path = log_files[0]
    name = log_path.stem

    expected_files = sorted(EXPECTED_DIR.glob(f"{test_num}_*_expected.md"))
    if not expected_files:
        return TestResult(name, False, message="no expected output file found")

    response_files = sorted(CLAUDE_RESPONSES_DIR.glob(f"{test_num}_*.json"))
    if not response_files:
        return TestResult(name, False, message="no claude_response fixture found")

    log_text = log_path.read_text(encoding="utf-8")
    expected_text = expected_files[0].read_text(encoding="utf-8")
    mock_response = json.loads(response_files[0].read_text(encoding="utf-8"))

    try:
        extractor = extractor_class(vault_path=VAULT_DIR, proposals_path=PROPOSALS_PATH)
        proposals = extractor.extract(log_text, log_date="2026-05-14", mock_response=mock_response)
        actual_text = extractor.format_proposals(proposals, log_date="2026-05-14")
    except Exception as e:
        return TestResult(name, False, message=f"extractor raised: {e}")

    passed, errors = compare(actual_text, expected_text, verbose)
    suffix = " (stub)" if using_stub else ""
    return TestResult(name, passed, message="OK" + suffix if passed else "FAIL", details=errors)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="Run specific test by number (e.g. 01)")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.list:
        for f in sorted(SAMPLE_LOGS_DIR.glob("*.md")):
            print(f"  {f.stem}")
        return

    extractor_class, using_stub = load_extractor()

    if args.test:
        test_nums = [args.test.zfill(2)]
    else:
        test_nums = sorted({f.name[:2] for f in SAMPLE_LOGS_DIR.glob("*.md")})

    results = [run_test(n, extractor_class, using_stub, args.verbose) for n in test_nums]

    print(f"\n{'='*55}")
    print(f"  Memory Reflect — Proposal Extractor Tests")
    if using_stub:
        print(f"  mode: STUB (real extractor not found — testing infrastructure only)")
    print(f"{'='*55}\n")

    n_passed = sum(1 for r in results if r.passed)
    n_failed = len(results) - n_passed

    for r in results:
        icon = "PASS" if r.passed else "FAIL"
        print(f"  {icon}  {r.name}")
        if not r.passed:
            print(f"       {r.message}")
        for line in r.details:
            print(f"       {line}")

    print(f"\n  {n_passed} passed · {n_failed} failed\n")
    sys.exit(0 if n_failed == 0 else 1)


if __name__ == "__main__":
    main()
