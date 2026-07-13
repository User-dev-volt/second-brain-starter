# Intent Model

How Alec makes decisions — not what he decided, but the heuristics he uses when facing tradeoffs.

## Standing Orders

### Pure Function Contracts
**Heuristic:** Library and utility functions should be synchronous, side-effect-free, and unbounded — the caller owns orchestration.
**Tradeoff type:** explicit vs. implicit
**Observed:** Consistent choice to define clean single-responsibility API boundaries.
**Confirmed:** 6 times across 3 sessions
**Gap accumulation:** 2 gaps — explicit vs. implicit → explicit each time (2026-05-14, 2026-05-21)
**Confidence:** high
**Last confirmed:** 2026-05-21
**Sessions:** 2026-05-14, 2026-05-21, 2026-05-28
**Standing order:** active
**Active since:** 2026-05-28
**Agent instruction:** When designing utility or library functions, default to synchronous, side-effect-free, unbounded contracts. Surface debounce, caching, and rate-limiting to the caller. Do not embed UX orchestration concerns inside utility functions. Apply this without asking.
**Context modifiers:** Relaxes for top-level application entry points (e.g. App.tsx event handlers) where orchestration ownership is intentionally co-located.

## Decision Patterns

### Adversarial Code Review Gate
**Heuristic:** Implementation is always followed by a separate review pass using a different LLM than the implementer.
**Tradeoff type:** speed vs. durability
**Observed:** Every story in the LEBO project follows: implement → adversarial review → merge.
**Confirmed:** 4 times across 2 sessions
**Confidence:** medium
**Last confirmed:** 2026-05-14
**Sessions:** 2026-05-13, 2026-05-14
**Standing order:** no
