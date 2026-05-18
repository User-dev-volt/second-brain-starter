# PRD: BMB Orchestration for BMAD Orchestrator Skill

**Status:** Ready for Implementation  
**Author:** Alec  
**Date:** 2026-05-18

---

## 1. Overview

The BMAD Orchestrator skill currently handles BMM (standard software projects) and GDS (game dev) with full autonomous proxy behavior. This PRD defines the addition of **BMB (BMAD Builder) orchestration** — enabling the orchestrator to build complete, installable BMAD modules (bundles of agents + workflows) using the same full-proxy model.

**Motivation:**  
Alec builds domain-specific BMAD modules (e.g. MovieBuilder, an interior design module) that help users plan and execute real-world creative projects. These modules are substantial artifacts — multiple agents, multiple workflows, coordinated step architecture. Building them requires navigating BMB's 4-mode workflow (Brief → Create → Edit → Validate) with many discovery questions. Full orchestrator proxy removes that friction.

---

## 2. Goals

- Add all 4 BMB modes to the orchestrator: **Brief, Create, Edit, Validate**
- Orchestrator acts as **full user proxy** throughout BMB (same model as BMM) — user sees only status narration and milestone check-ins
- Context comes from a **per-module intent doc** built via interview before BMB launches, used alongside any existing module brief
- Built modules are output into the **current project directory** — no cross-project work ever
- Full module build includes chained sessions for each agent and workflow (same session isolation model as BMM stories)
- BMB's step-file workflows are followed exactly — orchestrator only deviates by answering questions from the intent doc on Alec's behalf

---

## 3. Non-Goals (Out of Scope for v1)

- Building standalone agents or workflows outside the context of a module build
- Auto-installing built modules globally — Alec handles installation after output
- Auto-updating the orchestrator routing table after a module is built — manual step
- Cross-project orchestration — orchestrator is strictly scoped to the project directory it runs from
- Module versioning — left entirely to BMB's own Edit flow

---

## 4. User Stories

**US-1 — Module Brief**  
As Alec, when I say "use BMB to brief a [name] module", the orchestrator should interview me about my vision, synthesize a `{module-name}-intent.md`, then act as proxy through BMB's Brief mode to produce a complete `module-brief-{code}.md`.

**US-2 — Module Create**  
As Alec, when I say "use BMB to create the [name] module", the orchestrator should load the existing intent doc + brief, act as proxy through BMB's Create mode to scaffold the module, then chain into individual agent and workflow build sessions until all components are complete.

**US-3 — Module Edit**  
As Alec, when I say "use BMB to edit the [name] module", the orchestrator should load the intent doc and module artifacts, act as proxy through BMB's Edit mode, and apply changes in place.

**US-4 — Module Validate**  
As Alec, when I say "use BMB to validate the [name] module", the orchestrator should act as proxy through BMB's Validate mode, produce a compliance + completeness report, and automatically launch Edit mode to fix any issues found — reporting a summary of fixes made.

**US-5 — Fresh Module (no brief yet)**  
As Alec, when I invoke BMB for a module with no prior intent doc or brief, the orchestrator should detect this and run the Brief mode before offering Create.

**US-6 — Agent/Workflow Build within a Module**  
As Alec, when Create mode has scaffolded the module and agents/workflows remain unbuilt, the orchestrator should offer logical next steps (e.g. "Create [Agent Name]", "Create [Workflow] for [Agent]") and execute each as a new isolated session.

**US-7 — Refine Existing Module (MovieBuilder)**  
As Alec, the orchestrator should support refining or updating an existing module (like MovieBuilder) using Edit and Validate modes, not just new module creation.

---

## 5. Functional Requirements

### 5.1 Trigger Phrases

BMB flows activate on the **"use BMB"** prefix (distinct from "use BMAD" which routes to BMM/GDS). This is the primary disambiguation rule — "use BMAD" is never BMB.

Trigger phrases:
- "use BMB to build/brief/create/edit/validate a [name] module"
- "use BMB to create the next agent"
- "use BMB to create the [name] workflow"
- "BMB build module", "BMB brief [name]", "run BMB"
- Any phrase starting with "use BMB" or "run BMB"

**Disambiguation rule:** If the user says "use BMAD to build a MovieBuilder" (ambiguous — software project or module?), the orchestrator asks. If they say "use BMB to build a MovieBuilder module", it routes directly to BMB without asking.

### 5.2 Project Scope Lock (CRITICAL)

The orchestrator **must never cross project directory boundaries** for BMB work.

- All BMB operations are scoped strictly to the directory where the orchestrator session was launched
- If Alec asks to work on a different module than the one in the current project, the orchestrator responds: "I'm running inside [current project] — I can only work on modules in this directory. Start a new session from the [other project] folder to work on that module."
- No reading, writing, or installing to any path outside the current project root

### 5.3 Intent Doc Per Module

- **Location:** `_bmad-output/bmb/{module-name}-intent.md`
- **First run** (no intent doc found): orchestrator runs the Module Intent Interview (§5.4) and saves the result before launching BMB
- **Subsequent runs:** orchestrator loads existing intent doc as proxy source, combined with any existing `module-brief-{code}.md` if present
- **Precedence when both exist:** intent doc provides context (what Alec wants), brief doc drives structure (what BMB produces) — orchestrator uses both together, not one over the other
- Intent doc is always separate from `project-intent.md`

### 5.4 Module Intent Interview

Run before the first BMB session for a new module. Uses multiple-choice A/B/C/D format for each domain.

Domains to cover:

1. **Module name and code** — orchestrator suggests 2–3 clever short codes based on the name, asks Alec to confirm or provide his own
2. **Core user journey** — what does this module enable users to do? (e.g. "plan, write, and produce a movie with AI agents")
3. **Target user** — skill level, context, goals
4. **Agents needed** — roles, personas, specialties (orchestrator proposes candidates based on the domain)
5. **Workflows needed** — key processes the module must support
6. **Domain knowledge** — specialized terminology, external resources, data sources, constraints
7. **Module scope** — MVP vs full; what is explicitly out of scope

Save result to `_bmad-output/bmb/{module-name}-intent.md` before launching any BMB workflow.

### 5.5 BMB Mode Routing

| User intent | BMB mode | Orchestrator action |
|-------------|----------|---------------------|
| Brief / vision / explore | Brief | Load/create intent doc → proxy through Brief mode → output `module-brief-{code}.md` |
| Create / build / make | Create | Load intent doc + brief → proxy through Create mode → chain agent/workflow sessions |
| Edit / change / update | Edit | Load intent doc + existing module → proxy through Edit mode |
| Validate / check / review | Validate | Proxy through Validate → produce report → auto-launch Edit to fix issues |
| Ambiguous | — | Ask: "Would you like to Brief, Create, Edit, or Validate?" |

### 5.6 Full Proxy Behavior

The orchestrator follows BMB's step-file workflows exactly — it does not skip, reorder, or shortcut any step. The only deviation from standard BMB behavior is that the orchestrator answers questions on Alec's behalf using the intent doc.

Proxy rules:
- Answers all discovery questions from `{module-name}-intent.md` (primary) + `module-brief-{code}.md` (structural context)
- Selects Continue at every step automatically
- **Never shows BMB menus to Alec**
- Prints `◆ [BMB Mode] Step N/Total — [what's happening]` status narration before every step
- After each step, prints a **one-line summary of the key answer/decision made** so Alec can see the direction the orchestrator is heading
- Outputs the Autonomous Mode Declaration before every BMB Skill tool call

**Inference logging rule (for subjective questions):**  
When BMB asks a subjective question (e.g. agent communication style, personality) that the intent doc doesn't explicitly answer, the orchestrator:
1. Makes a reasonable creative judgment aligned with the module's domain and tone
2. Logs the inference: `  ↳ [Inferred] Agent communication style set to "warm, expert, encouraging" — not in intent doc, derived from module's target audience`
3. Continues without escalating

**Escalation rule:**  
When BMB asks a domain-specific question about the module's actual use case (e.g. "What data sources does this agent reference?", "What is the output format of this workflow?") that cannot be answered from the intent doc or brief, the orchestrator escalates to Alec, appends the answer to the intent doc, and continues.

### 5.7 Session Architecture for Module Builds

BMB module builds follow the same session isolation model as BMM story development:

```
SESSION 1 — Brief
  Proxy through BMB Brief mode (13 steps)
  Output: module-brief-{code}.md
  Milestone check-in: "Brief complete. Ready to move to Create?"

[FRESH SESSION]

SESSION 2 — Module Scaffold (Create mode)
  Proxy through BMB Create mode (8 steps)
  Output: module directory, module.yaml, agent specs, workflow specs, README, TODO
  Milestone check-in: "Module scaffolded. N agents and M workflows to build."

[FRESH SESSION PER AGENT — or parallel if context allows]

SESSION 3..N — Agent Builds
  Proxy through bmad-bmb-agent (Create mode) for each agent
  One session per agent (or parallel batch if agents are independent)
  Milestone: summary of agent built

[FRESH SESSION PER WORKFLOW]

SESSION N+1..M — Workflow Builds
  Proxy through bmad-bmb-workflow (Create mode) for each workflow
  One session per workflow
  Milestone: summary of workflow built

[FRESH SESSION]

SESSION FINAL — Validate
  Proxy through BMB Validate mode
  Auto-launch Edit if issues found
  Run test install
  Print completion summary
```

### 5.8 Compaction Recovery

Same disk-based recovery as BMM:
- Before launching each step, check the output file frontmatter for `stepsCompleted`
- On post-compaction startup, read step frontmatter to detect where the run left off
- Print: `◆ [Recovery] Post-compaction — resuming from step N of [mode] (detected from frontmatter)`
- Never restart a mode from the beginning if partial progress exists on disk

### 5.9 BMB Installation Check

Before launching any BMB workflow:

1. Check for `_bmad/bmb/` directory in the current project
2. If not found: "BMB is not installed in this project. Install it now? (runs `npx bmad-method install --modules bmb`)" — **wait for confirmation**
3. If confirmed: install, then continue
4. If declined or install fails: report and stop

### 5.10 Status Narration Format (BMB-specific)

```
◆ [BMB Brief] Step 4/13 — defining agent personas
  ↳ Answered: 3 agents proposed — Showrunner, Script Supervisor, Cinematographer
◆ [BMB Brief] Step 5/13 — establishing workflow structure
  ↳ Answered: 4 workflows — script development, shot planning, scene generation, production review
◆ [BMB Create] Step 2/8 — generating module.yaml
  ↳ [Inferred] Module code set to "cpm" (Cinematic Production Module) — confirmed by user
```

Every step gets: a status line before it fires, and a one-line answer summary after it completes.

### 5.11 Milestone Check-ins (BMB-specific)

| Milestone | What to show | What to ask |
|-----------|-------------|-------------|
| Intent interview complete | Module name, code, agent list, workflow list, scope | "Does this capture your vision?" |
| Brief mode complete | Brief doc path + key decisions made | "Ready to move to Create?" |
| Module scaffold complete | Output directory + agent specs + workflow specs listed | "N agents and M workflows to build. Start building?" |
| Each agent complete | Agent name + key traits | (no check-in — continue to next) |
| Each workflow complete | Workflow name + step count | (no check-in — continue to next) |
| All components built | Full component inventory | "All components built. Run validation now?" |
| Validate complete | Issue count + severity + fixes applied | "Validation complete. [Summary of fixes]. Run test install?" |
| Test install complete | Pass/fail + output path | "Module is ready. What's next?" |

### 5.12 Post-Build Handoff Menu

After all components are built and validated, present a context-aware next-step menu:

```
◆ [BMB] Module [Name] — build complete

  What's next?
  A: Run validation now
  B: Create [Next Agent Name] — [description]
  C: Create [Workflow Name] for [Agent Name]
  D: Get installation instructions
  E: Done — print summary and stop
```

Options B and C are dynamically generated based on what agents/workflows remain in the module spec but haven't been built yet. If all components are built, B and C are omitted.

### 5.13 Completion Definition

A module is **not considered done** until:
1. All agents in the module spec have been built (proxied through `bmad-bmb-agent`)
2. All workflows in the module spec have been built (proxied through `bmad-bmb-workflow`)
3. BMB Validate mode passes (or all found issues have been fixed via Edit mode)
4. A test install completes without errors
5. Alec confirms he has tested the module himself

The orchestrator tracks completion state in `_bmad-output/bmb/{module-name}-status.md`.

---

## 6. Non-Functional Requirements

- **Proxy fidelity:** Orchestrator must not generate module content from its own knowledge — all content comes from BMB's step files guided by the intent doc
- **Step compliance:** BMB workflows are followed in exact sequence — no steps skipped, no shortcuts
- **Inference transparency:** Every creative judgment made without explicit intent doc guidance must be logged with `↳ [Inferred]` prefix
- **Autonomous Mode Declaration:** Required before every BMB Skill tool call
- **Project isolation:** Zero reads or writes outside the current project root — hard rule, no exceptions
- **Status granularity:** Step-level narration (not just milestone-level) — Alec must be able to see the direction at every step

---

## 7. Success Criteria

- Alec says "use BMB to build a [name] module" and the orchestrator handles the full Brief → Create → Agent builds → Workflow builds → Validate flow without Alec navigating any BMB menus
- The per-module intent doc captures enough context that all subsequent sessions (agent builds, workflow builds, Edit, Validate) need no re-interview
- Each agent and workflow gets its own isolated session — same discipline as BMM story → review → fix cycles
- Test install completes successfully on the built module
- The orchestrator never generates module content from its own knowledge — BMB step files produce everything
- Alec can see exactly what direction the orchestrator is heading at every step via narration + answer summaries
- The orchestrator never touches files outside the current project directory
