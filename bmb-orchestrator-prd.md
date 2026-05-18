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

*These need answers before implementation begins. Please answer each one.*

---

**Q1 — BMB as skills vs commands:**
The moviebuilder project uses BMB as slash commands; LEBO and newer projects use skills. Should the orchestrator enforce skills-only (requiring BMB to be installed as skills), or detect the installed architecture and support both?

> Well, BMB is a similar system to BMM in a sense that it is a process and we must follow the workflow processes the way BMAD BMB wants us to. This is important to make sure that we are building a brief through Bmad BMB the way it wants us to and that goes for each of the other workflows for building agents and workflows and modules. We must not stray from the BMAD method, however in the way that we do stray is that me and the orchestrator get the project-intent document squared away and then it works its way through the different flows of BMB. Get it? That way the Orchestrator can act on my behalf and answer questions that BMB asks the user(me) on my behalf also.

---

**Q2 — Agent and workflow sub-builds within a module:**
BMB's module Create mode outputs agent and workflow *specs/placeholders*, not fully built artifacts. Should the orchestrator then chain into `bmad-bmb-agent` and `bmad-bmb-workflow` to flesh out each component automatically — or stop after module scaffolding and let you do sub-builds in a follow-up session?

> **Your answer:**

---

**Q3 — Module versioning:**
When editing an existing module, should the orchestrator handle version tracking (incrementing a version field in `module.yaml`), or leave that entirely to BMB's own Edit flow?

> **Your answer:**

---

**Q4 — Trigger disambiguation:**
If you say "use BMAD to build a MovieBuilder", the orchestrator can't tell if you mean a software project (BMM) or a BMAD module (BMB). What should the rule be? Always ask when ambiguous? Assume module if the word "module" is present? Or treat anything that sounds like a domain tool (not a software app) as a module?

> **Your answer:**

---

**Q5 — Intent doc location:**
The PRD proposes `_bmad-output/bmb/{module-name}-intent.md`. Does that path feel right, or do you want intent docs somewhere else — e.g. directly in the project root, or in a dedicated `_bmb-output/` folder separate from `_bmad-output/`?

> **Your answer:**

---

**Q6 — Brief doc precedence:**
If a prior BMB session already produced a `module-brief-{code}.md`, and you also have a `{module-name}-intent.md`, which should the orchestrator treat as authoritative when proxying? Intent doc only? Brief doc only? Merge both?

> **Your answer:**

---

**Q7 — Compaction recovery during long BMB runs:**
BMB Brief mode has 13 steps; Create mode has 8. These are long proxy runs that can trigger context compaction mid-flow. Should the orchestrator use the same disk-based state recovery as BMM (reading step frontmatter to detect where it left off), or is a simpler "restart from the top of the current mode" acceptable?

> **Your answer:**

---

**Q8 — Proxy creativity for subjective BMB questions:**
BMB asks creative and subjective questions — e.g. "What communication style should this agent have?", "What's the agent's personality?" — that a dry intent doc may not fully answer. When the intent doc is silent on something subjective, should the orchestrator: (a) make a reasonable creative judgment and continue, (b) always escalate to you, or (c) make a judgment but log every inference it makes so you can review?

> **Your answer:**

---

**Q9 — Multi-module projects:**
If the current project has multiple modules in progress (e.g. both MovieBuilder and an interior design module), how should the orchestrator identify which one to Edit or Validate? Scan the intent docs and ask you to pick? Or require you to name it in the trigger phrase?

> **Your answer:**

---

**Q10 — Auto-fix after validation:**
When Validate mode finds issues, should the orchestrator automatically launch Edit mode to fix them — or present the report and ask you first?

> **Your answer:**

---

**Q11 — Orchestrator routing table auto-update:**
After a module is successfully built and output, should the orchestrator automatically add a routing entry for it into its own `SKILL.md` (e.g. "if user says 'run MovieBuilder', invoke the moviebuilder module") — or leave that as a manual step?

> **Your answer:**

---

**Q12 — Rebuilding moviebuilder:**
MovieBuilder already exists as a working module in its own project. Do you want to use this new orchestrator flow to rebuild or refine it eventually — or is moviebuilder "done" and this orchestrator flow is for new modules going forward?

> **Your answer:**

---

**Q13 — Output staging vs immediate:**
The PRD says output goes into the current project. But since these are reusable modules, do you want the option to output to a staging/review folder first (so you can inspect before it lands in the final location) — or is "dump it in the project, I'll review in place" fine?

> **Your answer:**

---

**Q14 — BMB not installed — auto-install behavior:**
If the orchestrator detects BMB is not installed in the current project, should it auto-install silently (running `npx bmad-method install --modules bmb`), ask for confirmation first, or stop and tell you to install manually?

> **Your answer:**

---

**Q15 — Session isolation for BMB vs BMM:**
If you're mid-way through a BMM software build (e.g. working on LEBO stories) and you say "use BMAD to brief an interior design module," should the orchestrator: handle both in the same session (switching context), recommend starting a fresh session for the BMB work, or hard-block until the BMM work is paused/completed?

> **Your answer:**

---

**Q16 — Status narration granularity during long runs:**
BMB Brief mode's 13 steps could take 20–40 minutes as a full proxy run. Do you want a status line before every step (`◆ [BMB Brief] Step 4/13 — defining agent personas`), or just at major milestones (e.g. after each mode phase)?

> **Your answer:**

---

**Q17 — "Done" definition for Create mode:**
BMB Create mode outputs a module directory with agent specs, workflow specs, `module.yaml`, README, and TODO. Is that output sufficient for you to consider the module "done" (ready to be fleshed out further separately) — or does the orchestrator need to verify the output is actually installable (e.g. run a test install) before declaring success?

> **Your answer:**

---

**Q18 — Partial module builds:**
If Create mode fails or is interrupted mid-run (e.g. BMB hits an escalation blocker), should the orchestrator preserve whatever partial output was written and offer to resume — or clean it up and start fresh?

> **Your answer:**

---

**Q19 — Module naming and code conventions:**
BMB uses a short module code (e.g. `cpm` for Cinematic Production Module). Should the orchestrator ask you to define the code during the intent interview, suggest one based on the module name, or let BMB's own discovery steps handle it?

> **Your answer:**

---

**Q20 — Post-build handoff:**
After a module is built, what should the orchestrator offer next? Options like: "Run validate now", "Open the module in Edit mode", "Get installation instructions", "Done — nothing more needed"? Or just print a summary and stop?

> **Your answer:**

---

## 8. Success Criteria

- Alec can say "use BMAD to build a [name] module" and the orchestrator handles the full Brief → Create flow without Alec having to navigate BMB menus manually
- The per-module intent doc captures enough context that subsequent sessions (Edit, Validate) need no re-interview
- A completed module directory is output, valid, and installable with `npx bmad-method install`
- The orchestrator does not generate any module content from its own knowledge — BMB's step files produce everything
