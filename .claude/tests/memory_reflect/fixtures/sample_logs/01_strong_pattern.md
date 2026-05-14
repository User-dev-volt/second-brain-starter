## [SessionEnd] 10:30

**Decisions:**
- Chose to log all Claude API calls to a local JSONL file rather than rely on Anthropic's dashboard — want full audit trail under my control
- Rejected using LangChain abstractions in favor of direct Anthropic SDK calls — LangChain hides too much of what's actually being sent

**Lessons:**
- Direct SDK calls are more verbose but you always know exactly what's being sent and received
- JSONL append is better than SQLite for audit logs — simpler, grep-able, no schema lock-in

**Next Actions:**
- Add request/response logging to session-end-flush.py

## [SessionEnd] 15:45

**Decisions:**
- Decided against using a pre-built memory framework (MemGPT, etc.) — prefer to understand and own every layer of the memory system
- Chose markdown over a database for the proposals file — stays human-readable and auditable in git without tooling

**Lessons:**
- Owning the stack means slower start but no surprise behavior at 2am when something breaks
- Markdown-first design keeps the system inspectable without requiring any special tooling

**Next Actions:**
- Draft the proposal block schema

## [SessionEnd] 21:15

**Decisions:**
- Rejected auto-approval for identity proposals — want a manual review gate on anything touching soul.md or user.md
- Chose explicit status field over separate approved/rejected folders — keeps rejection reason co-located with the proposal itself

**Lessons:**
- Manual gates on identity changes are worth the friction; the cost of a wrong auto-approval is high
- Co-located context (rejection reason next to the proposal) is easier to audit than split file structures

**Next Actions:**
- Build test fixtures for proposal extractor
