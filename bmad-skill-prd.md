---
project_name: "BMAD Method Skill Integration"
version: "1.0"
date: "2026-04-10"
status: "Final"
track: "BMad Method"
---

# Product Requirements Document: BMAD Method Skill Integration

## 1. Overview

### 1.1 Problem Statement

Using the BMAD Method today requires manual knowledge of which workflows to run, in what order, with which agents, and how to manage context between sessions. A developer must remember the full phase progression (Analysis → Planning → Solutioning → Implementation), understand each module's capabilities, manually invoke skills, and handle fresh-session transitions — all while keeping artifacts organized and progress tracked. This cognitive overhead defeats the purpose of having a structured methodology.

### 1.2 Product Vision

A Claude Code skill that serves as an intelligent BMAD workflow conductor — a "second brain" that knows the entire BMAD ecosystem. When a user says "utilize BMAD to build me X," the skill takes over orchestration: it fetches the latest BMAD documentation, detects (or installs) the framework, auto-detects installed modules, and invokes the correct BMAD workflows and agents in the right order with high autonomy, checking in with the user only at major milestones.

**Critical design principle:** The skill is a pure orchestrator. It never generates artifacts (PRDs, architecture, stories, code) itself. It always delegates artifact creation to BMAD's native workflows and agents. The skill's role is to know what to invoke next, provide the right inputs and answers to keep BMAD agents on task, manage session transitions, and track progress.

### 1.3 Target Users

Developers using Claude Code (in any environment, including but not limited to Antigravity or VS Code) who want to leverage the BMAD Method without memorizing its workflows, commands, or phase structure.

### 1.4 Success Criteria

- User can go from "utilize BMAD to build a task manager" to working, code-reviewed implementation with minimal manual intervention
- Skill orchestrates all 4 BMAD phases end-to-end by invoking native BMAD workflows and agents — never generating artifacts itself
- Context is preserved across fresh sessions using BMAD's own artifact and tracking system
- Skill stays current with BMAD updates via auto-fetch of latest documentation
- Works in any Claude Code environment
- BMAD agents stay on task because the skill provides the right context, answers, and inputs at each step

---

## 2. Functional Requirements

### FR-001: Intent Interview and Project Scoping

Before invoking any BMAD workflow, the skill conducts a thorough intent interview to extract enough information to act as the user's proxy throughout the entire BMAD pipeline. The goal is to front-load discovery so the skill can answer BMAD agents' questions without returning to the user except for truly unexpected situations.

**Interview Domains:**
- **Product vision** — What is this? What problem does it solve? Who is it for?
- **Target audience** — End users, their skill level, their pain points
- **Platform and delivery** — Web, mobile, desktop, CLI, API, game engine, etc.
- **Core features** — Must-have functionality, nice-to-haves, explicit exclusions
- **Differentiation** — What exists today? What makes this different or better?
- **Technical preferences** — Preferred stack, frameworks, languages, hosting, constraints
- **Scope and scale** — MVP vs full product, expected complexity, user volume
- **Monetization/business model** — If applicable
- **Design and UX preferences** — Visual style, reference apps, accessibility requirements
- **Domain knowledge** — Key terminology, rules, data sources, APIs the product depends on (e.g., game data, industry regulations)

**Interview Behavior:**
- Asks targeted, specific questions — not a generic questionnaire
- Adapts follow-up questions based on previous answers (e.g., if user says "game tool," probe for which game, what data sources, what the community uses today)
- **Each question presents 3 generated answer options (A, B, C) plus a "D: Type your own answer" option**
- Generated options are contextually relevant to the project idea — not generic (e.g., for a Last Epoch build optimizer: "A: Web app with responsive design, B: Desktop app (Electron), C: Browser extension that overlays in-game")
- After selecting A, B, or C, the user can optionally add comments to refine or expand on their choice (e.g., selecting "A: Web app" and adding "but also needs to work well on mobile")
- Option D allows fully free-form input when none of the generated options fit
- Continues until it has enough context to confidently answer questions a PM, Architect, or Developer agent would ask during BMAD workflows
- Summarizes its understanding back to the user for confirmation before proceeding

**Output:**
- A structured intent document saved to `_bmad-output/project-intent.md`
- Contains all interview responses organized by domain
- Serves as the skill's reference throughout all subsequent BMAD workflow invocations
- Loaded by the skill at the start of every new session to maintain continuity

**Mid-Workflow Escalation:**
- If a BMAD agent asks something the intent document doesn't cover and the skill cannot reasonably infer an answer, the skill pauses and asks the user directly
- The user's answer is appended to `project-intent.md` so the question is never asked twice
- This should be rare if the upfront interview was thorough

**Acceptance Criteria:**
- Interview always runs before the first BMAD workflow invocation on a new project
- Resuming an existing project loads the intent document instead of re-interviewing
- The skill can answer at least 90% of BMAD agent questions using the intent document alone
- Mid-workflow escalations to the user are persisted to the intent document
- User confirms the interview summary before any BMAD workflow begins

### FR-002: Natural Language Invocation

The skill activates when the user invokes it with natural language containing phrases like "utilize BMAD," "use BMAD," "BMAD build," or similar intent signals. No rigid command syntax required. The skill interprets the user's intent and routes to the appropriate starting point in the BMAD workflow.

**Acceptance Criteria:**
- Recognizes natural language triggers referencing BMAD
- Extracts the project concept/intent from the user's message
- Routes to the correct phase based on project state (new project → Phase 1, existing artifacts → resume from last phase)

### FR-002: Auto-Fetch Latest BMAD Documentation

On each invocation, the skill fetches the latest `llms-full.txt` from `https://docs.bmad-method.org/llms-full.txt` (or the GitHub raw equivalent) to ensure it has current knowledge of all BMAD workflows, agents, modules, and conventions.

**Acceptance Criteria:**
- Fetches latest docs at the start of each session
- Gracefully handles fetch failures (falls back to embedded/cached knowledge)
- Parses the documentation to understand available workflows, agents, and module capabilities

### FR-003: BMAD Installation Management

The skill detects whether BMAD is installed in the current project. If not installed, it runs `npx bmad-method install` with appropriate configuration. If installed, it proceeds to orchestration.

**Acceptance Criteria:**
- Detects presence of `_bmad/` directory and `_bmad/_config/manifest.yaml`
- Runs installer interactively or with sensible defaults when BMAD is missing
- Detects installed modules from the manifest
- Offers to install missing modules when a workflow requires one that isn't present

### FR-004: Module Auto-Detection and Management

The skill reads the BMAD manifest to determine which modules are installed (BMM, BMad Builder, Game Dev Studio, TEA, CIS) and tailors its available workflows accordingly. When a workflow requires a module that isn't installed, the skill offers to install it.

**Acceptance Criteria:**
- Parses `_bmad/_config/manifest.yaml` for installed modules
- Only offers workflows from installed modules
- Prompts user before installing additional modules
- Updates its available workflow set after new module installation

### FR-005: Full Phase 1 — Analysis Workflows

The skill can drive all optional Analysis phase workflows with high autonomy:

- **Brainstorming** (`bmad-brainstorming`) — Facilitate guided ideation sessions
- **Research** (`bmad-market-research`, `bmad-domain-research`, `bmad-technical-research`) — Conduct market, domain, and technical research
- **Product Brief** (`bmad-product-brief`) — Create product brief when concept is clear
- **PRFAQ** (`bmad-prfaq`) — Working Backwards challenge to stress-test the concept

**Acceptance Criteria:**
- Recommends appropriate Analysis workflows based on the user's stated intent and confidence level
- Runs workflows autonomously, checking in at completion of each
- Writes all artifacts to `_bmad-output/planning-artifacts/`
- Offers to skip Analysis if user wants to jump to Planning

### FR-006: Full Phase 2 — Planning Workflows

The skill drives the Planning phase:

- **Create PRD** (`bmad-create-prd`) — Define requirements with FRs/NFRs
- **Create UX Design** (`bmad-create-ux-design`) — Design UX when applicable

**Acceptance Criteria:**
- Uses Analysis artifacts as input when available
- Produces `PRD.md` in standard BMAD output location
- Asks user whether UX design is needed based on project type
- Checks in with user for approval of the completed PRD before moving to Solutioning

### FR-007: Full Phase 3 — Solutioning Workflows

The skill drives the Solutioning phase:

- **Create Architecture** (`bmad-create-architecture`) — Technical design decisions
- **Create Epics and Stories** (`bmad-create-epics-and-stories`) — Work breakdown
- **Implementation Readiness Check** (`bmad-check-implementation-readiness`) — Gate check

**Acceptance Criteria:**
- Loads PRD as input for architecture
- Produces `architecture.md` with ADRs
- Creates epic files with stories informed by both PRD and architecture
- Runs implementation readiness check and reports PASS/CONCERNS/FAIL
- Pauses for user approval at readiness check before proceeding to implementation

### FR-008: Full Phase 4 — Implementation Workflows

The skill drives the Implementation phase:

- **Sprint Planning** (`bmad-sprint-planning`) — Initialize tracking
- **Create Story** (`bmad-create-story`) — Prepare story files
- **Dev Story** (`bmad-dev-story`) — Implement stories
- **Code Review** (`bmad-code-review`) — Validate implementation
- **Retrospective** (`bmad-retrospective`) — Review after epic completion

**Acceptance Criteria:**
- Creates and maintains `sprint-status.yaml`
- Implements stories one at a time with code review after each
- Runs retrospective after completing all stories in an epic
- Checks in with user between epics (not between every story)

### FR-014: Independent Validation — Anti-Gaming Guardrails

The skill enforces strict separation between code generation and code validation to prevent the AI from gaming its own tests or rubber-stamping its own implementation. This is critical given the skill's high-autonomy design.

**Code Review Isolation:**
- Code review MUST run in a fresh session, never in the same session that wrote the implementation
- The review session has no access to the implementation session's reasoning — it evaluates the code and artifacts cold
- The review session adopts an adversarial review stance by default (assume problems exist, find them)

**Mandatory vs. Adaptive Review Depth:**
- All stories receive standard code review (`bmad-code-review`) in a fresh adversarial session
- High-complexity stories additionally receive `bmad-review-adversarial-general` AND `bmad-review-edge-case-hunter`
- The skill assesses story complexity based on: number of files touched, cross-module changes, new public APIs, security-sensitive logic, and database schema changes

**Test Generation Isolation:**
- Tests MUST be written in a separate session from the implementation that produced the code
- The test session reads the story spec and the implemented code but has no access to the implementation session's reasoning or intent
- This prevents the AI from writing tests that mirror its own assumptions rather than testing actual behavior

**Implementation Cycle Per Story:**
```
Session A: Dev Story → implement code → write to disk
  ↓ [fresh session]
Session B: Test Generation → write tests from spec + code → write to disk
  ↓ [fresh session]
Session C: Code Review (adversarial) → review code + tests cold
  ↓ [if high-complexity: also run edge-case hunter]
  ↓ [findings written to disk]
  ↓ [if FAIL: return to Session A with findings as input]
```

**Acceptance Criteria:**
- Implementation, test generation, and code review never share a session
- Review sessions always start with adversarial stance
- High-complexity stories are auto-detected and receive enhanced review
- Review findings are persisted to disk so fix sessions have full context
- Failed reviews loop back to implementation with specific, actionable findings

### FR-009: Quick Flow Support

The skill recognizes when a request is small enough for Quick Flow and offers `bmad-quick-dev` as an alternative to the full pipeline.

**Acceptance Criteria:**
- Assesses scope from user's description
- Suggests Quick Flow for bug fixes, small features, and well-scoped changes
- Can run `bmad-quick-dev` end-to-end with high autonomy
- Falls back to full workflow if Quick Flow proves insufficient

### FR-010: Session Management and Context Continuity

The skill enforces fresh sessions between major workflow phases to prevent context degradation. It uses BMAD's existing artifact system (`_bmad-output/`, `sprint-status.yaml`, planning artifacts) as the handoff mechanism between sessions.

**Acceptance Criteria:**
- Recommends starting a fresh session before context compaction occurs
- Writes all progress to disk (artifacts, sprint status) before suggesting a session break
- New sessions can read existing artifacts and sprint status to determine where to resume
- The skill's first action in a new session is to scan `_bmad-output/` and `sprint-status.yaml` to determine project state
- Provides clear guidance on what was completed and what's next when resuming

### FR-011: BMAD Builder Integration

When the user's intent involves creating custom agents, workflows, or modules, the skill leverages BMad Builder workflows.

**Acceptance Criteria:**
- Detects when user intent maps to module/agent/workflow creation
- Uses BMad Builder's agent builder, workflow builder, and module builder
- Follows BMad Builder conventions for output structure

### FR-012: Cross-Module Workflow Support

The skill understands and can orchestrate workflows from all BMAD modules:

- **BMad Method (BMM)** — Core agile workflow
- **BMad Builder (BMB)** — Module/agent/workflow creation
- **Game Dev Studio (GDS)** — Game development with GDD generation
- **Test Architect (TEA)** — Enterprise test strategy and automation
- **Creative Intelligence Suite (CIS)** — Structured creativity and ideation

**Acceptance Criteria:**
- Routes to the correct module's workflows based on project type
- Can combine modules (e.g., BMM for planning + GDS for game-specific architecture + TEA for test strategy)
- Understands module-specific agents and their roles

### FR-013: Core Tool Access

The skill can invoke any of BMAD's core tools when appropriate during workflows:

- Advanced elicitation, adversarial review, edge case hunting
- Party mode for multi-perspective decisions
- Distillator for document compression
- Editorial reviews for document quality

**Acceptance Criteria:**
- Offers advanced elicitation at key decision points
- Can run adversarial review on generated artifacts when quality matters
- Uses party mode when multi-agent perspective would benefit a decision

### FR-015: Error Recovery and Retry Logic

When a BMAD workflow fails, produces incoherent output, or breaks the build, the skill diagnoses the failure layer and responds appropriately rather than blindly retrying.

**Failure Diagnosis:**
- **Workflow crash or incomplete output** — Retry the workflow in a fresh session with the same inputs
- **Low-quality artifact** (incoherent PRD, weak architecture) — Re-run the workflow with additional context from the intent document and explicit guidance on what was wrong
- **Build-breaking implementation** — Revert changes, analyze the failure, and re-run `bmad-dev-story` with the failure analysis as additional input
- **Test failures after implementation** — Distinguish between bad code (re-implement) and bad tests (re-generate tests in fresh session)

**Behavior:**
- Maximum 2 automatic retries per workflow before escalating to the user
- Each retry uses a fresh session to avoid compounding context issues
- Failure details are logged to `_bmad-output/implementation-artifacts/error-log.md` for debugging
- After 2 failed retries, the skill pauses and presents the user with: what failed, what it tried, and options (retry with different approach, skip, or manual intervention)

**Acceptance Criteria:**
- Skill never silently retries more than twice
- Retries always use fresh sessions
- User is informed of all failures and retries
- Error log is maintained on disk for troubleshooting

### FR-016: Track Selection Logic

The skill defaults to the BMad Method track but allows the user to override to a different track at any time.

**Default Behavior:**
- New projects default to BMad Method (full pipeline: Analysis → Planning → Solutioning → Implementation)
- The skill presents the track choice during the intent interview with contextual options
- Quick Flow is suggested when the skill detects small scope (bug fix, single feature, clear implementation path)

**Available Tracks:**
- **Quick Flow** — Bug fixes, simple features, clear scope (1-15 stories). Uses `bmad-quick-dev`
- **BMad Method** — Products, platforms, complex features (10-50+ stories). Full 4-phase pipeline
- **Enterprise** — Compliance, multi-tenant, regulated systems (30+ stories). Full pipeline + security + DevOps considerations

**Override:**
- User can change tracks at any point by telling the skill (e.g., "switch to Quick Flow" or "this needs Enterprise track")
- Track change triggers the skill to reassess which workflows and artifacts are needed
- Already-completed artifacts are preserved and reused where applicable

**Acceptance Criteria:**
- Default track is BMad Method unless scope clearly indicates Quick Flow
- Track choice is recorded in `project-intent.md`
- User can override at any time with natural language
- Track change does not discard completed work

### FR-017: Multi-Module Routing

The skill intelligently combines modules based on project type, using signals from the intent interview and installed module manifest.

**Routing Logic:**
- **Game projects** → GDS (Game Dev Studio) + BMM for workflow structure
- **Projects requiring test strategy** → TEA (Test Architect) alongside BMM
- **Projects needing creative ideation** → CIS (Creative Intelligence Suite) for Phase 1
- **Custom agent/workflow/module creation** → BMad Builder
- **Standard software projects** → BMM alone

**Combination Rules:**
- BMM is always the backbone — other modules augment specific phases
- GDS replaces BMM's architecture workflow with game-specific architecture when a game project is detected
- TEA augments Phase 4 with enterprise test workflows when the project has compliance, security, or complex testing needs
- CIS augments Phase 1 with additional ideation frameworks beyond core brainstorming
- BMad Builder is invoked when the user's intent is to create BMAD extensions rather than end-user software

**Detection Signals:**
- Project type keywords from the intent interview (e.g., "game," "roguelike," "multiplayer" → GDS)
- Complexity and compliance mentions (e.g., "HIPAA," "multi-tenant," "audit trail" → Enterprise track + TEA)
- Creative exploration emphasis (e.g., "not sure what to build," "explore ideas" → CIS)
- Meta-development intent (e.g., "build a BMAD module," "create a custom agent" → Builder)

**Acceptance Criteria:**
- Module routing decision is presented to user for confirmation during intent interview
- User can add or remove modules at any time
- Skill only routes to installed modules; offers to install missing ones
- Routing rationale is recorded in `project-intent.md`

### FR-018: User Override and Manual Control

The user can override any routing decision, skip workflows, re-run workflows, or redirect the skill at any time using natural language.

**Override Capabilities:**
- **Skip** — "skip brainstorming" or "skip analysis, go straight to PRD"
- **Re-run** — "re-run the architecture workflow" or "redo that"
- **Redirect** — "actually use Quick Flow instead" or "add TEA to this project"
- **Pause** — "stop here, I'll continue later"
- **Jump** — "go to Phase 3" or "start implementation"

**Behavior:**
- The skill acknowledges the override and adjusts its plan
- Skipped workflows are noted in the progress tracker so the skill doesn't re-suggest them
- Re-runs always use a fresh session
- Jumping forward triggers a warning if prerequisite artifacts are missing (e.g., jumping to implementation without a PRD) but allows the user to proceed if they insist

**Acceptance Criteria:**
- All overrides work via natural language — no special commands needed
- Skill warns about missing prerequisites but does not block the user
- Override decisions are logged so future sessions reflect the adjusted plan
- User can always ask "what are my options?" to see available actions

### FR-019: Progress Visibility

At the start of every session, the skill displays a concise progress summary so the user immediately knows where they are in the overall pipeline.

**Summary Format:**
```
BMAD Progress: [Project Name]
Phase: 3/4 — Solutioning
Track: BMad Method
Modules: BMM + GDS

Completed:
  ✓ Phase 1: Analysis (brainstorming, market research)
  ✓ Phase 2: Planning (PRD, UX design)
  ✓ Architecture
  ✓ Epics & Stories (5 epics, 23 stories)

Current:
  → Epic 2: Core Game Logic (3/5 stories complete)
  → Next: Story 2.4 — Skill Tree Dependency Resolver

Blockers: None
```

**Behavior:**
- Generated by scanning `_bmad-output/`, `sprint-status.yaml`, and `project-intent.md`
- Displayed automatically at session start — no user action needed
- Concise enough to read in seconds, detailed enough to orient the user
- Highlights blockers or stalls if detected

**Acceptance Criteria:**
- Progress summary appears at the start of every session after the initial intent interview
- Accurately reflects completed workflows, current phase, and next action
- Reads from on-disk artifacts only — no reliance on session memory
- Displays in under 10 lines for most projects

---

## 3. Non-Functional Requirements

### NFR-001: Portability

The skill must work in any Claude Code environment, not just Antigravity. No dependencies on specific terminal emulators, OS features, or proprietary integrations.

### NFR-002: High Autonomy with Milestone Check-ins

The skill operates with high autonomy — it drives workflows forward without asking for permission at every step. Check-ins occur at major milestones only: phase transitions, artifact approvals (PRD, architecture), readiness checks, and epic boundaries.

### NFR-003: Resilience to Documentation Changes

The skill's architecture (main orchestrator + separate module knowledge files) must tolerate BMAD documentation updates without breaking. The auto-fetch mechanism ensures the skill adapts to new workflows, agents, or conventions as they're added to BMAD.

### NFR-004: Context Window Awareness

The skill must be aware of context window limitations and proactively manage them. This means writing artifacts to disk early and often, recommending fresh sessions before compaction risk, and being able to fully reconstruct state from on-disk artifacts.

### NFR-005: Modular Knowledge Architecture

The skill is structured as a main orchestrator skill file plus separate module knowledge files. This allows updating knowledge for individual modules without touching the orchestrator, and keeps any single file from becoming too large for effective use.

### NFR-006: Graceful Degradation

If the documentation fetch fails, if a module isn't installed, or if an unexpected error occurs, the skill degrades gracefully — falling back to embedded knowledge, suggesting manual steps, or offering to skip the problematic workflow.

---

## 4. Skill Architecture

### 4.1 File Structure

```
.claude/skills/
├── bmad-orchestrator/
│   └── SKILL.md                    # Main orchestrator — routing, state detection, session management
├── bmad-knowledge-bmm/
│   └── SKILL.md                    # BMad Method module knowledge
├── bmad-knowledge-builder/
│   └── SKILL.md                    # BMad Builder module knowledge
├── bmad-knowledge-gds/
│   └── SKILL.md                    # Game Dev Studio module knowledge
├── bmad-knowledge-tea/
│   └── SKILL.md                    # Test Architect module knowledge
├── bmad-knowledge-cis/
│   └── SKILL.md                    # Creative Intelligence Suite module knowledge
└── bmad-knowledge-core/
    └── SKILL.md                    # Core tools knowledge (elicitation, reviews, party mode, etc.)
```

### 4.2 Orchestrator Responsibilities

The orchestrator **does not generate any BMAD artifacts**. Its sole responsibilities are:

1. **Invocation parsing** — Interpret natural language intent from the user
2. **Documentation fetch** — Pull latest `llms-full.txt` on session start
3. **State detection** — Scan `_bmad/` and `_bmad-output/` to determine project state and what's been completed
4. **Module detection** — Read manifest, determine available workflows and agents
5. **Workflow routing** — Select and invoke the correct BMAD skill/workflow/agent for the current phase
6. **Context feeding** — Provide the invoked BMAD agent with the right inputs, answers, and guidance to stay on task
7. **Session management** — Track context usage, recommend fresh sessions, ensure artifacts are persisted before transitions
8. **Milestone check-ins** — Pause for user input at phase transitions and key approval points
9. **Progress tracking** — Monitor implementation progress and detect stalls, loops, or design-breaking decisions

**What the orchestrator delegates:**
- All artifact generation (PRD, architecture, epics, stories, code, tests) → BMAD native workflows and agents
- All creative/analytical work (brainstorming, research, review) → BMAD native workflows and agents
- All code implementation and testing → BMAD dev workflows

### 4.3 Knowledge File Responsibilities

Each module knowledge file contains the orchestrator's understanding of a module — enough to know **what to invoke and when**, not enough to do the module's work:

- The module's available workflows, agents, and their skill invocation names
- Phase mappings (which workflows belong to which phase)
- Input/output specifications for each workflow (what artifacts each workflow needs and produces)
- Trigger conditions (when to route to this module's workflows)
- Module-specific session management considerations

---

## 5. User Flows

### 5.1 New Project — Full Pipeline

```
User: "utilize BMAD to build a build optimizer for Last Epoch"
  ↓
Skill: Fetches latest BMAD docs
Skill: No _bmad/ found → runs npx bmad-method install
Skill: Detects modules needed → installs
  ↓
INTENT INTERVIEW:
Skill: "What platforms? Web app, desktop, mobile?"
Skill: "Who's the target user? Casual players, min-maxers, build theorycrafters?"
Skill: "What game data do you need? Skills, items, affixes, passives?"
Skill: "Are there existing tools? What's missing from them?"
Skill: "Tech stack preferences?"
  ... (continues until comprehensive)
Skill: "Here's my understanding: [summary]. Correct?"
User: "Yes" (or corrects)
  → Saves project-intent.md
  ↓
Phase 1: Invokes bmad-brainstorming/research → skill answers agent questions from intent doc
  ↓ [milestone check-in: "Analysis complete. Ready for PRD?"]
  ↓ [recommends fresh session]
  ↓
Phase 2: Invokes bmad-create-prd → skill feeds intent + analysis artifacts as context
  ↓ [milestone check-in: "PRD complete. Review and approve?"]
  ↓ [recommends fresh session]
  ↓
Phase 3: Invokes bmad-create-architecture → skill answers architect questions from intent + PRD
         Invokes bmad-create-epics-and-stories
         Auto-generates project-context.md
         Invokes bmad-check-implementation-readiness
  ↓ [milestone check-in: "Readiness: PASS. Begin implementation?"]
  ↓ [recommends fresh session]
  ↓
Phase 4: Invokes sprint planning → story creation → dev → test (separate session) → review (separate session)
         (repeats per story, checks in per epic)
  ↓ [milestone check-in after each epic]
  ↓
Phase 4: Invokes bmad-retrospective after final epic
  ↓
Done.
```

### 5.2 Existing Project — Resume

```
User: "utilize BMAD"
  ↓
Skill: Fetches latest BMAD docs
Skill: Finds _bmad/ → reads manifest
Skill: Loads project-intent.md → has full context of what we're building
Skill: Scans _bmad-output/ → finds PRD.md, architecture.md, sprint-status.yaml
Skill: "You're mid-implementation. Epic 2, Story 3 is next. Continue?"
  ↓
Resumes from exactly where the user left off, with full intent context.
```

### 5.3 Quick Fix

```
User: "utilize BMAD to fix the login validation bug"
  ↓
Skill: Assesses scope → small, well-defined
Skill: "This looks like a Quick Flow task. Running bmad-quick-dev."
  ↓
Quick Dev: clarify → plan → implement → review → done
```

---

## 6. Out of Scope (v1)

- GUI or visual workflow maps within the terminal
- Multi-user collaboration or shared session state
- Integration with external project management tools (Jira, Linear, etc.)
- Custom module creation workflows beyond what BMad Builder provides
- Automatic git operations (commits, branches, PRs) — left to the user or other tools

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Context window exhaustion during complex phases | Lost progress, degraded output | Aggressive artifact-to-disk writing; proactive fresh session recommendations |
| BMAD docs URL changes or goes down | Skill can't update knowledge | Fallback to embedded knowledge; configurable URL |
| Module workflows change between BMAD versions | Skill sends wrong commands | Auto-fetch ensures latest knowledge; modular knowledge files isolate blast radius |
| User intent misclassified (Quick Flow vs Full) | Wrong workflow chosen | Always confirm routing decision with user; allow override |
| Large projects exceed practical session limits | Implementation stalls | Per-story sessions with sprint-status.yaml as the source of truth for progress |

---

## 9. Implementation Guide for Claude

This section provides direct guidance for any Claude instance tasked with building this skill from the PRD above.

### 9.1 What You're Building

You are building a set of Claude Code skill files (markdown). There is no application code, no database, no API. The deliverables are `.claude/skills/` directories each containing a `SKILL.md` file. These files are pure instruction sets that tell Claude Code how to behave when invoked.

### 9.2 Build Order

Build files in this order — each one builds on the previous:

1. **`bmad-knowledge-core/SKILL.md`** — Core tools knowledge (elicitation, reviews, party mode, distillator). This is referenced by the orchestrator and other knowledge files.
2. **`bmad-knowledge-bmm/SKILL.md`** — BMad Method module knowledge. This is the most critical module — covers all 4 phases.
3. **`bmad-knowledge-builder/SKILL.md`** — BMad Builder module knowledge.
4. **`bmad-knowledge-gds/SKILL.md`** — Game Dev Studio module knowledge.
5. **`bmad-knowledge-tea/SKILL.md`** — Test Architect module knowledge.
6. **`bmad-knowledge-cis/SKILL.md`** — Creative Intelligence Suite module knowledge.
7. **`bmad-orchestrator/SKILL.md`** — The main orchestrator. Build this last because it references all knowledge files.

### 9.3 What Each Knowledge File Must Contain

Each module knowledge file is a reference sheet the orchestrator consults. Every knowledge file must include:

- **Module name and code** (e.g., BMad Method / `bmm`)
- **All available workflows** with their exact skill invocation names (e.g., `bmad-create-prd`)
- **Phase mapping** — which BMAD phase each workflow belongs to
- **Input requirements** — what artifacts or context each workflow needs before it can run
- **Output specifications** — what artifact each workflow produces and where it saves
- **Agent names and roles** — which agent runs each workflow (e.g., PM agent John for PRD)
- **Trigger conditions** — when the orchestrator should route to this module (e.g., game keywords → GDS)

Keep knowledge files concise and structured. Use tables and lists, not prose. The orchestrator needs to scan these quickly, not read essays.

### 9.4 Orchestrator SKILL.md Structure

The orchestrator file should be organized in this order:

1. **Identity and role** — "You are the BMAD Orchestrator. You are a pure conductor — you never generate artifacts yourself. You always delegate to BMAD workflows and agents."
2. **Invocation triggers** — Natural language patterns that activate this skill ("utilize BMAD," "use BMAD," etc.)
3. **Session startup sequence** — Fetch docs → detect installation → load intent → show progress → determine next action
4. **Intent interview protocol** — The full interview behavior including multiple-choice format (A/B/C generated options + D write your own), domains to cover, and save to `project-intent.md`
5. **Workflow routing logic** — Decision tree for which phase, workflow, and module to invoke based on project state and intent
6. **Track selection** — Default BMad Method, override rules
7. **Module routing** — Detection signals and combination rules
8. **Session management rules** — When to recommend fresh sessions, how to persist state, context compaction prevention
9. **Milestone check-in points** — Exactly when to pause for user input
10. **Anti-gaming rules** — Three-session separation for implement/test/review, adversarial stance requirements
11. **Error recovery protocol** — 2-retry max, fresh sessions, escalation behavior
12. **Correct course triggers** — Loop detection, stall detection, design-breaking detection
13. **User override handling** — Skip, re-run, redirect, pause, jump behaviors
14. **Progress summary format** — Template for session-start status display

### 9.5 Critical Implementation Rules

- **Never generate artifacts.** The orchestrator's job is to invoke BMAD skills. If you catch yourself writing PRD content, architecture decisions, story implementations, or any artifact — stop. Invoke the BMAD skill that produces that artifact instead.
- **Always fetch docs first.** Every session starts by fetching `https://docs.bmad-method.org/llms-full.txt`. If the fetch fails, state that you're working from cached/embedded knowledge and proceed.
- **Always load project-intent.md.** After the initial interview, every session reads this file before doing anything else. This is how you maintain continuity.
- **Always show progress.** After the first session, every session starts with a progress summary before asking what to do.
- **Fresh sessions are non-negotiable for validation.** Implementation, test generation, and code review must never share a session. Write this rule explicitly and prominently in the orchestrator.
- **Respect .customize.yaml if present.** Check for agent customization files before invoking workflows. Apply them if they exist. Don't fail if they don't.
- **Multiple-choice interview format.** Every interview question must present A/B/C contextual options plus D (write your own). After selecting A/B/C, offer the user a chance to add comments. This is a UX requirement, not optional.
- **Log errors.** All workflow failures and retries are appended to `_bmad-output/implementation-artifacts/error-log.md`.
- **The user can always override.** Any natural language instruction to skip, re-run, redirect, pause, or jump must be honored. Warn about missing prerequisites but never block.

### 9.6 File Output Locations

All files the skill creates or references:

| File | Location | Created By |
|------|----------|------------|
| `project-intent.md` | `_bmad-output/project-intent.md` | Orchestrator (intent interview) |
| `project-context.md` | `_bmad-output/project-context.md` | BMAD workflow (auto after architecture) |
| `error-log.md` | `_bmad-output/implementation-artifacts/error-log.md` | Orchestrator (on failures) |
| `sprint-status.yaml` | `_bmad-output/implementation-artifacts/sprint-status.yaml` | BMAD workflow |
| `PRD.md` | `_bmad-output/planning-artifacts/PRD.md` | BMAD workflow |
| `architecture.md` | `_bmad-output/planning-artifacts/architecture.md` | BMAD workflow |
| Epic/story files | `_bmad-output/planning-artifacts/epics/` | BMAD workflow |

### 9.7 Testing the Skill

After building all files, test with these scenarios:

1. **New project, no BMAD installed** — Say "utilize BMAD to build a weather app." Verify: docs fetched → installation triggered → intent interview runs with multiple choice → workflows invoked in correct order.
2. **Existing project, mid-implementation** — Set up a project with PRD and architecture already in `_bmad-output/`. Say "utilize BMAD." Verify: progress summary shown → resumes at correct point.
3. **Quick Flow routing** — Say "utilize BMAD to fix the login bug." Verify: scope assessed → Quick Flow suggested → `bmad-quick-dev` invoked.
4. **User override** — Mid-workflow, say "skip brainstorming." Verify: phase skipped, noted in progress, moves to next workflow.
5. **Session transition** — Run until the skill recommends a fresh session. Start a new session and say "utilize BMAD." Verify: progress loads from disk, resumes correctly.

1. **Customization persistence** — The skill respects `.customize.yaml` agent customizations when present but does not require them. If a user has customized the Architect to prioritize serverless patterns, the skill follows that during architecture workflows. If no customizations exist, default agent behaviors apply.

2. **Parallel workflows** — Yes. The skill suggests running independent workflows in parallel when beneficial (e.g., "You could run domain research and market research in separate sessions simultaneously"). It provides clear instructions for what to invoke in each session.

3. **Project context generation** — The skill auto-generates `project-context.md` immediately after architecture creation, no user confirmation needed. This ensures implementation agents have consistent technical guidance from the start.

4. **Correct course** — The skill proactively suggests `bmad-correct-course` when it detects:
   - Stories repeatedly failing tests in a loop without progress
   - A halt in forward progress during implementation
   - A design-breaking decision that conflicts with the architecture or PRD
