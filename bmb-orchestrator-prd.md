# PRD: BMB Orchestration for BMAD Orchestrator Skill

**Status:** Draft  
**Author:** Alec  
**Date:** 2026-05-17

---

## 1. Overview

The BMAD Orchestrator skill currently handles BMM (standard software projects) and GDS (game dev) with full autonomous proxy behavior. This PRD defines the addition of **BMB (BMAD Builder) orchestration** — enabling the orchestrator to build complete, installable BMAD modules (bundles of agents + workflows) using the same full-proxy model.

**Motivation:**  
Alec builds domain-specific BMAD modules (e.g. MovieBuilder, an interior design module) that help users plan and execute real-world creative projects. These modules are substantial artifacts — multiple agents, multiple workflows, coordinated step architecture. Building them requires navigating BMB's 4-mode workflow (Brief → Create → Edit → Validate) with many discovery questions. Full orchestrator proxy removes that friction.

---

## 2. Goals

- Add all 4 BMB modes to the orchestrator: **Brief, Create, Edit, Validate**
- Orchestrator acts as **full user proxy** throughout BMB (same model as BMM) — user sees only status narration and milestone check-ins
- Context comes from a **per-module intent doc** (e.g. `moviebuilder-intent.md`) built via brief doc + interview before BMB launches
- Built modules are output into the **current project directory**
- Supports building modules that contain **agents and workflows** together (not just one or the other)

---

## 3. Non-Goals (Out of Scope)

- Building standalone agents or workflows in isolation (BMB agent/workflow workflows) — module-first only in v1
- Auto-installing built modules globally — user handles installation after output
- BMB for project-specific micro-artifacts (e.g. a one-off agent for LEBO) — this is for reusable, full modules

---

## 4. User Stories

**US-1 — Module Brief**  
As Alec, when I say "use BMAD to brief a [name] module", the orchestrator should interview me about my vision (what the module enables users to do, what agents and workflows it needs), synthesize a `{module-name}-intent.md`, then act as proxy through BMB's Brief mode to produce a complete `module-brief-{code}.md`.

**US-2 — Module Create**  
As Alec, when I say "use BMAD to create the [name] module", the orchestrator should load the existing `{module-name}-intent.md` brief, act as proxy through BMB's Create mode, and output the full module directory structure (agents, workflows, module.yaml, README, TODO) into the current project.

**US-3 — Module Edit**  
As Alec, when I say "use BMAD to edit the [name] module", the orchestrator should load the existing intent doc and module artifacts, act as proxy through BMB's Edit mode, and apply changes to the module in place.

**US-4 — Module Validate**  
As Alec, when I say "use BMAD to validate the [name] module", the orchestrator should act as proxy through BMB's Validate mode and produce a compliance + completeness report. If issues are found, offer to fix them via Edit mode.

**US-5 — Fresh Module (no brief yet)**  
As Alec, when I mention building a new module with no prior brief or intent doc, the orchestrator should detect this and offer to run the Brief mode first before offering Create.

---

## 5. Functional Requirements

### 5.1 Trigger Phrases

The orchestrator must activate the BMB flow (instead of normal BMM startup) when it detects phrases like:

- "use BMAD to build a [X] module"
- "use BMAD to brief a [X] module"
- "use BMAD to create the [X] module"
- "use BMAD to edit the [X] module"
- "use BMAD to validate the [X] module"
- "BMAD build module", "build BMAD module", "build a new module with BMAD"
- Any phrase combining BMAD + module + (build/create/brief/edit/validate)

### 5.2 Intent Doc Per Module

- Each module gets its own intent doc: `_bmad-output/bmb/{module-name}-intent.md`
- On first run (no intent doc found): orchestrator runs the **Module Intent Interview** (see §5.3) before launching BMB
- On subsequent runs: orchestrator loads the existing intent doc as its proxy source
- Intent doc is separate from `project-intent.md` (keeps BMM and BMB concerns cleanly separated)

### 5.3 Module Intent Interview

Before launching BMB, the orchestrator must gather:

1. **Module name and code** — what is this module called? (e.g. "MovieBuilder", code: `cpm`)
2. **What does it enable users to do?** — the core user journey (e.g. "plan, write, and produce a movie with AI agents")
3. **Who is the target user?** — skill level, context, goals
4. **What agents are needed?** — roles, personas, specialties
5. **What workflows are needed?** — key processes the module needs to support
6. **Domain knowledge** — specialized terminology, external resources, constraints
7. **Module scope** — MVP vs full, what's explicitly excluded

Orchestrator uses multiple-choice format (A/B/C/D) for each domain. Saves answers to `{module-name}-intent.md` before launching BMB.

### 5.4 BMB Mode Routing

| User intent | BMB mode | Orchestrator action |
|-------------|----------|---------------------|
| Brief / vision / explore | Brief | Load intent doc → proxy through Brief mode → output `module-brief-{code}.md` |
| Create / build / make | Create | Load intent doc + brief → proxy through Create mode → output module directory |
| Edit / change / update | Edit | Load intent doc + existing module → proxy through Edit mode |
| Validate / check / review | Validate | Proxy through Validate mode → produce report → offer Edit if issues found |
| Ambiguous | — | Ask: "Would you like to Brief, Create, Edit, or Validate?" |

### 5.5 Full Proxy Behavior

The orchestrator acts as user proxy inside BMB exactly as it does inside BMM:

- Answers all discovery questions from `{module-name}-intent.md`
- Selects Continue at every step automatically
- Never shows BMB menus to the human user
- Prints `◆ [BMB] ...` status narration before each step
- Outputs the Autonomous Mode Declaration before invoking BMB via the Skill tool
- Escalates to the human only when BMB asks something not covered by the intent doc

### 5.6 Output Location

- All BMB output goes into the current project directory under the path BMB specifies (typically `_bmad/bmb/` or a configured `bmb_creations_output_folder`)
- After Create mode completes, orchestrator prints the full output path and a summary of what was created (agents, workflows, module.yaml)
- Orchestrator does NOT auto-install the module globally — it presents installation instructions and lets Alec decide

### 5.7 BMB Installation Check

Before launching any BMB workflow, the orchestrator must check that BMB is installed in the current project:

- Check for `.claude/skills/bmad-bmb-agent/` or `_bmad/bmb/` directory
- If not found: offer to install BMB — `npx bmad-method install --modules bmb`
- If install fails: report and stop

### 5.8 Milestone Check-ins (BMB-specific)

| Milestone | What to show | What to ask |
|-----------|-------------|-------------|
| Intent interview complete | Module intent summary | "Does this capture your vision?" |
| Brief mode complete | Brief doc path + key decisions | "Ready to move to Create?" |
| Create mode complete | Output directory + artifact list | "Review the output. Install globally or continue editing?" |
| Validate report complete | Issue count + severity | "N issues found. Apply fixes via Edit mode?" |

---

## 6. Non-Functional Requirements

- **Status narration:** Every BMB action gets a `◆ [BMB] ...` status line — same discipline as BMM phases
- **Autonomous Mode Declaration:** Required before every BMB Skill tool call
- **Proxy fidelity:** Orchestrator must not generate module content from its own knowledge — all content comes from BMB's step files guided by the intent doc
- **Intent doc format:** Same frontmatter convention as `project-intent.md` — readable by future orchestrator sessions for recovery

---

## 7. Open Questions

1. **BMB as skills vs commands:** The moviebuilder project uses BMB as slash commands; LEBO and newer projects use skills. The orchestrator needs to detect which architecture is installed and invoke accordingly. Does Alec want the orchestrator to enforce skills-only, or support both?

2. **Agent and workflow sub-builds within a module:** BMB's module Create mode generates agent and workflow *specs/placeholders*, not fully built artifacts. Should the orchestrator then chain into `bmad-bmb-agent` and `bmad-bmb-workflow` to flesh out each component, or leave that to a follow-up session?

3. **Module versioning:** When editing an existing module, how should the orchestrator handle version tracking? Increment a version field in `module.yaml`, or leave that to BMB?

---

## 8. Success Criteria

- Alec can say "use BMAD to build a [name] module" and the orchestrator handles the full Brief → Create flow without Alec having to navigate BMB menus manually
- The per-module intent doc captures enough context that subsequent sessions (Edit, Validate) need no re-interview
- A completed module directory is output, valid, and installable with `npx bmad-method install`
- The orchestrator does not generate any module content from its own knowledge — BMB's step files produce everything
