# PROJECT CHIMERA — HANDOFF

**Read this first. Then `decisions.md`. Then `gate-1-system.md`.**

Everything is committed and pushed to branch **`claude/greatest-story-narrative-xx8w8o`**
in `User-dev-volt/second-brain-starter`, under `chimera/`.

---

## Where things stand

| Gate | Status |
|---|---|
| **Gate 1 — the system** | **CLOSED AND APPROVED.** Do not reopen. |
| **Gate 2 — the schools** | **OPEN. Three attempts, all rejected.** Start from the names below. |
| Gates 3–6 | Untouched. |

---

## The files

| File | What it is |
|---|---|
| `chimera-prompt-v3.md` | The human's original brief. The gate protocol lives in §0. |
| `decisions.md` | **Every decision the human has made, and why.** The source of truth. |
| `gate-1-system.md` | The approved system, 16,205 words, 13 sections. |
| `gate-1-system.html` | Reading edition of the above. |
| `bedrock.html` | Gate 1 summarised with diagrams. The format the human likes. |
| `gate-1-brief.md` | The round-3 options brief that produced the Gate 1 decisions. |
| `three-ways-to-cast.html` | The Gate 1 decision board. Historical. |
| `gate-2-schools.md` | **REJECTED.** Attempt 3. Mine for mechanics, not for names or prose. |
| `gate-2-decision.md` | **REJECTED.** Attempt 3's decision brief. |
| `gate-2-glance.html` | **REJECTED.** Attempt 3 visual sheet. |
| `build_md_html.py`, `shell_template.html` | Turns a Gate markdown file into a styled reading edition. |

---

## HOW TO WORK WITH THIS HUMAN — read before writing anything

These were all learned the hard way in session one. Violating them is what caused three
rejected attempts at Gate 2.

**1. Plain names. Always.** The names that worked were agreed in conversation and are ordinary
English a person understands instantly: *the bag, the instrument, the body, the scholar, the
attuned.* The names that got rejected were trade jargon invented by sub-agents: *pinch hand,
hafter, bookhand, ground-walker, carrier.* If a name needs explaining, it is wrong.

**2. Less granularity, not more.** Rejected feedback, verbatim: *"they are too granular and
abstract."* Sub-agents produce beautiful, exhaustively specified prose that buries the idea.
A school needs: what you cast with, what it looks like, what's great about it, what kills it.
Four things. Not a 2,000-word trade ethnography.

**3. The human reads summaries, not documents.** They asked twice for a visual TL;DR with SVG
diagrams. `bedrock.html` is the format that works: short cards, a diagram where a picture beats a
paragraph, decisions at the bottom with recommendations marked. **Build the summary first, and
only write the long document once the summary is approved.**

**4. Check direction early and cheaply.** Every time this session went wrong, it went wrong for
40 minutes of workflow before anyone noticed. Put the shape in front of them in a short message
*before* spending a build.

**5. They are right about direction, consistently.** When they say "we might be going the wrong
way," stop and ask rather than defend. Every single course correction they made improved the work.

**6. Keep the gates.** §0 of the prompt: present options, stop, let them decide. Nothing gets
built on an unapproved foundation.

---

## GATE 2 — where to resume

### The axis is decided and correct

**A school is what you cast with.** This is the locked bedrock's own answer — §2.2 lists the four
substance sources and ends *"they are different answers with different risks, **and they are how
casters differ from each other.**"*

A school is the **class system** — playstyle, silhouette, what beats you. Not a faction, not a
culture, not a nation. Those are Gate 5.

How a caster *reads* is personal style inside a school, never the thing that defines it.

### The five schools — USE THESE NAMES

| Name | Casts with | Core idea, in one line |
|---|---|---|
| **The bag** | Carried reagents | A grab bag she assembled — flint, carbon, salts, filings. **It spends down and deletes**, and she restocks by crafting from what she scavenges. Inventory-and-crafting school. |
| **The instrument** | Objects | A rod, a gauntlet, armour — and at the far end, metal that has replaced a limb. Casts through the thing, not the hands. |
| **The body** | Herself | The boundary is **scribed into her skin** (reference: Scar, FMA), and sap crosses her flesh to reach the work. The channel path hardens, and **the mark creeps** — slowly, visibly, permanently. Every use is a choice. |
| **The scholar** | Memory | Knows the substances and sequences by heart. Disciplined and vast — and the possibilities are infinite, so she can never know them all. That gap is the weakness. |
| **The attuned** | Instinct | A **people**, not a trade. In tune with sap the way someone is in tune with country. High acuity, almost no library: **she feels without knowing.** Feels sap itself — rich ground, thin ground, a basin upstream quietly taking what used to come here. |

### What survived the rejected attempt and is worth keeping

Mechanics only — rewrite all of it in plain language, much shorter.

- **The body's two clocks.** The *creep* is a measurable distance up the limb, advanced by every
  passage (a set is small, a solve is large, a chain is largest) and it moves while you watch.
  Ordinary *overdraw* is the second, separate clock. Hardened tissue will not carry, so her working
  skin is a map that only shrinks: forearm, other forearm, thigh, back. **Nobody lets it past the
  collarbone, because past the collarbone is the throat.** This landed well — keep it, shorten it.
- **A chain contains a solve.** There is no cheap fast tier; every school's FAST costs a full solve
  and a quarter. Most work is done on the plain set.
- **Paper is an index, not a library.** A record tells you *which* of the things you have already
  touched this is. It cannot enter library on its own.
- **No instrument reads.** An implant is a sap topology; a rod is a boundary and a magazine.
  Acuity is not for sale.

### Still to decide with the human at Gate 2

- Which schools are playable, which are enemy-only, which one the protagonist starts in.
- Whether the attuned are a school, a culture, or both — and how much of them belongs to Gate 5.
  *(An earlier draft de-mystified them into a trade of well-siters. The human asked for a people.
  Do not make them mystics, but do not flatten them into a job either.)*
- The counter graph: who beats whom and why, in plain mechanical terms.

---

## The one-paragraph version of the world, for a cold start

Matter is **grain** — fine particles in **families** that never become one another. Every working is
two motions: **SOLVE** parts the hold that keeps an arrangement together, **SET** re-ties it. The
charge you spend is the hold itself, and it is called **sap**. Sap comes from the unrest of living
matter, released at death into the ground, which refines it over about nine days and gathers it into
**pools** — so the politics are hydraulic, and a battlefield is the best ground in the country.
You perceive what things are made of **by touch**, and that sense is a scale everyone sits somewhere
on. A working takes what is inside the boundary you laid; if that is not enough, it finishes out of
whatever is nearest, and **there is always something nearest**.

> **"Name your source, or it'll name one for you."**

The Law commands you to name where it is coming from. It never says what a source may be. Correct
procedure and atrocity are the same act.

**Coinages spent: zero of ten.** Every term above is ordinary English doing new work. Keep it that way.
