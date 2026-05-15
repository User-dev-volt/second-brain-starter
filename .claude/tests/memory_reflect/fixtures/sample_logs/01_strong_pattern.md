## [SessionEnd] 10:30

Project: second-brain-starter
Session goal: Implement local JSONL audit trail for Claude API calls
Session type: building

**Critical moments:**
(none)

**AI choices + responses:**
- Offered: LangChain abstractions vs. direct Anthropic SDK → Chose: direct Anthropic SDK — "I want to see exactly what's being sent"
  Tradeoff: control vs. convenience

**AI gaps:**
(none)

**Scope expansions:**
(none)

**Scope constraints:**
(none)

**Decisions:**
- Chose to log all Claude API calls to a local JSONL file rather than rely on Anthropic's dashboard — want full audit trail under my control
- Rejected using LangChain abstractions in favor of direct Anthropic SDK calls — LangChain hides too much of what's actually being sent

**Lessons:**
- Direct SDK calls are more verbose but you always know exactly what's being sent and received
- JSONL append is better than SQLite for audit logs — simpler, grep-able, no schema lock-in

**Next Actions:**
- Add request/response logging to session-end-flush.py

## [SessionEnd] 15:45

Project: second-brain-starter
Session goal: Design proposal schema for identity documents
Session type: designing

**Critical moments:**
(none)

**AI choices + responses:**
- Offered: pre-built memory framework (MemGPT) vs. custom build → Chose: custom build — "prefer to understand and own every layer of the memory system"
  Tradeoff: ownership vs. delegation
- Offered: database vs. markdown for proposals file → Chose: markdown — "stays human-readable and auditable in git without tooling"
  Tradeoff: control vs. convenience

**AI gaps:**
(none)

**Scope expansions:**
(none)

**Scope constraints:**
(none)

**Decisions:**
- Decided against using a pre-built memory framework (MemGPT, etc.) — prefer to understand and own every layer of the memory system
- Chose markdown over a database for the proposals file — stays human-readable and auditable in git without tooling

**Lessons:**
- Owning the stack means slower start but no surprise behavior at 2am when something breaks
- Markdown-first design keeps the system inspectable without requiring any special tooling

**Next Actions:**
- Draft the proposal block schema

## [SessionEnd] 21:15

Project: second-brain-starter
Session goal: Build identity proposal review gate
Session type: building

**Critical moments:**
(none)

**AI choices + responses:**
- Offered: auto-approval for identity proposals vs. manual review gate → Chose: manual review gate — "want a manual review gate on anything touching soul.md or user.md"
  Tradeoff: explicit vs. implicit
- Offered: separate approved/rejected folders vs. status field in proposal → Chose: status field — "keeps rejection reason co-located with the proposal itself"
  Tradeoff: explicit vs. implicit

**AI gaps:**
(none)

**Scope expansions:**
(none)

**Scope constraints:**
(none)

**Decisions:**
- Rejected auto-approval for identity proposals — want a manual review gate on anything touching soul.md or user.md
- Chose explicit status field over separate approved/rejected folders — keeps rejection reason co-located with the proposal itself

**Lessons:**
- Manual gates on identity changes are worth the friction; the cost of a wrong auto-approval is high
- Co-located context (rejection reason next to the proposal) is easier to audit than split file structures

**Next Actions:**
- Build test fixtures for proposal extractor
