# PROJECT CHIMERA — HANDOFF

**Read this first. Then `decisions.md`. Then `gate-1-system.md`.**

Everything is committed and pushed to branch **`claude/greatest-story-narrative-xx8w8o`**
in `User-dev-volt/second-brain-starter`, under `chimera/`.

---

## Where things stand

| Gate | Status |
|---|---|
| **Gate 1 — the system** | **CLOSED AND APPROVED.** Do not reopen. |
| **Gate 2 — the schools** | **OPEN. Attempt 4 built and awaiting your decision.** See `gate-2-glance.html`. Three earlier attempts rejected. |
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


---

## ATTEMPT 4 — BUILT, AWAITING DECISION

The glance sheet is rebuilt: `gate-2-glance.html`, also published at
https://claude.ai/code/artifact/df238764-9ff1-460a-92a6-f8055331ea17

**Nothing here is decided.** The long document has NOT been written, and must not be until the
human approves the sheet. That ordering is rule 3 above and it is the whole reason attempt 4 exists.

What changed from attempt 3: the five locked names are used as written, each school is four beats
(casts with / looks like / great at / what kills it), and the sheet carries four SVGs — the five at a
glance, the acuity/library plot, the body's two clocks, and the counter graph.

**Five questions are open on the sheet** and are the human's to answer: which schools are playable;
where the protagonist starts; whether the attuned is the weakest design (and whether to pay her in
*the reach* instead of in perception, which would be a new mechanic); how much of the attuned belongs
to Gate 5; and whether the counter graph holds.

### GATE 1 READINGS THAT KILLED SIX DRAFT SENTENCES — do not re-make these

These are not new decisions. They are what `gate-1-system.md` already says, found by auditing a draft
against it. Every one of them was written wrong first.

- **There is no sap-through-flesh conduit.** Sap lives in a pool, a flask or an implant, and nowhere
  else. The body caster is not a channel. She is simply always *inside her own boundary*, and §2's
  rule is that anything inside the line is a source.
- **The body's cost is NOT overdraw.** §3's own row for spending her own body is a substance ladder —
  cramps, then teeth, then bone — and it says outright *"This is not overdraw — overdraw is a sap
  failure and it hardens; this does not."* A creeping mark that advances on every ordinary stroke also
  deletes §7's central line: *"The third is a decision. It is always a decision."*
- **Her map shrinks for a geometric reason.** A scored line is permanent, and a new line crossing an
  old one breaks the run before it closes (§2 — a boundary must be a closed run). Not because
  "hardened tissue won't carry", which is conduit thinking and has no Gate 1 basis.
- **An instrument never buys sap.** It buys a line that cannot be smudged (§2 PREPARED) and a
  pre-loaded charge of *substance* (§3). The flask is the sap magazine and anyone may carry one.
  Welding a sap topology to a school is §1's named "classic apprentice error".
- **Frost and heat at the seam is the IMPLANT's tell**, not the instrument school's — the implant is a
  sap topology (§4), so that silhouette belongs to how a caster carries charge, not to what she casts with.
- **The bag is FAST because carried stock is pre-read stock** — it is already in library. Having the
  right family buys *certainty*, not seconds. And run dry she is *"a novice in her own room"* (§3's
  exact words), never a civilian: her library cannot be taken from her.
- **The attuned can name what she is holding.** That is what high acuity does — it is her strength,
  never her weakness. Her cap is no library, therefore no chaining, therefore no large working.
- **Nobody senses a pool or a basin at range.** The read is contact-only; *"a read run into open air
  returns nothing at all."* Pools are found with sinking-rods. And §11 publishes the rich/thin ground
  tells for anyone with eyes, so "nobody else sees it" is false.

### The method that worked, for whoever picks this up next

Sub-agents wrote none of the prose and none of the names. They mined `gate-1-system.md` for facts,
proposed the counter graph, drew the SVGs from label text supplied verbatim, and — most valuable —
audited the draft adversarially, one agent per rejection reason. That audit caught eleven fatal
contradictions across two rounds, six of which were in copy that already read perfectly well.
**Write the copy yourself; use the agents to check it against the bedrock and to draw.**
