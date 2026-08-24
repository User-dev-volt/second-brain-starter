# PROJECT CHIMERA — HANDOFF

**Read this, then `decisions.md`. Then the gate you are working on.**

Everything is committed and pushed to **`claude/greatest-story-narrative-xx8w8o`** in
`User-dev-volt/second-brain-starter`, under `chimera/`.

---

## THIS IS A STORY FIRST

Standing instruction from the human, and the single most important line in this file:

> *"While this story is for a game, the important part is that it is a story ultimately. The game can
> be built around the story later... So the world is of utmost importance, how it works, how
> individuals have lived in this world, traditions passed on in the world and what it has culminated
> to. All of it."*

Build the **world**. A campaign gets built from it afterwards, the way one could be built from *Full
Metal Alchemist*. Anything that reads as balance, kits, playability, classes or matchups is the wrong
altitude and will be rejected — this already happened once and cost three attempts at Gate 2.

---

## Where things stand

| Gate | Status |
|---|---|
| **Gate 1 — the system** | **CLOSED AND APPROVED.** Do not reopen. |
| **Gate 2 — the traditions** | **CLOSED AND APPROVED.** |
| **Gate 3 — the loophole and the atrocity** | **OPEN. START HERE.** |
| Gates 4–6 | Untouched. |

## The files

| File | What it is |
|---|---|
| `chimera-prompt-v3.md` | The human's original brief. The gate protocol is §0. |
| `decisions.md` | **Every decision the human has made, and why. The source of truth.** |
| `gate-1-system.md` | The approved system. 16,051 words, 13 sections. |
| `gate-1-system.html` · `bedrock.html` | Reading edition, and the Gate 1 visual summary. |
| `gate-2-traditions.md` | The approved Gate 2. 4,449 words, ten sections. |
| `gate-2-traditions.html` · `gate-2-glance.html` | Reading edition, and the Gate 2 visual summary. |
| `build_md_html.py`, `shell_template.html` | Turns a gate markdown file into a styled reading edition. |
| `gate-2-schools.md/.html`, `gate-2-decision.md` | **REJECTED attempt 3, historical.** Never quote its names or prose. |
| `three-ways-to-cast.html` | The Gate 1 decision board. Historical. |

---

## HOW TO WORK WITH THIS HUMAN — read before writing anything

Learned the hard way across two gates. Violating these is what caused three rejected attempts.

**1. Plain names. Always.** Every term must be ordinary English a reader parses on first contact.
Rejected sub-agent inventions: *pinch hand, hafter, bookhand, ground-walker, carrier.* The human's
verbatim response: *"the names are terrible... No one will understand the hafter."* **If a name needs
explaining, it is wrong.** Ten coinages for the entire world. Spent so far: **zero**. Keep it that way.

**2. Less granularity, not more.** Verbatim rejection: *"they are too granular and abstract."* A
rejected draft ran 9,526 words of trade ethnography. Brevity is the deliverable, not a constraint on it.

**3. Visual TL;DR first, always.** Standing instruction: *"when you make the gate, always make a TL DR
for me with SVGs that help me picture what we're going with so I can be certain that I like the
direction we're heading."* `bedrock.html` and `gate-2-glance.html` are the format. **Build the summary,
get it approved, and only then write the long document.** Make the summary cover every section of the
document it summarises.

**4. Check direction early and cheaply.** Put the shape in a short message *before* spending a build.
Every time this project went wrong it went wrong for a long time before anyone noticed.

**5. They are right about direction, consistently.** When they say it feels wrong, stop and ask rather
than defend. Every course correction they have made improved the work — including the one that threw
out a finished Gate 2 and got a better one.

**6. Keep the gates.** §0 of the prompt: present options, stop, let them decide. Nothing is built on an
unapproved foundation.

### The method that actually worked

Sub-agents wrote **none** of the prose and none of the names. They were used to mine
`gate-1-system.md` for facts, to propose structures, to draw SVGs from label text supplied verbatim,
and — most valuable by far — to **audit the draft adversarially**, one agent per rejection reason.
That audit caught eleven fatal contradictions across two rounds, six of them in copy that read
perfectly well. **Write the prose yourself. Use agents to check it and to draw.**

And **render the page and look at it** before showing the human. Chromium is at
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; `pip install playwright`, screenshot the page,
and read your own diagrams. Three real layout bugs were caught this way that no amount of reasoning
about coordinates would have found.

---

## The world in one paragraph, for a cold start

Matter is **grain** — fine particles in **families** that never become one another, listed on **the
Table**, which is published, disputed and incomplete. Every working is two motions: **SOLVE** parts the
hold that keeps an arrangement together, **SET** re-ties it. The charge you spend is the hold itself,
and it is called **sap**. Sap comes from the unrest of living matter, released at death into the
ground, which refines it over about nine days and gathers it into **pools** — so the politics are
hydraulic, and a battlefield is the best ground in the country. You perceive what things are made of
**by touch**, on a two-axis scale: **acuity**, largely natal and ceilinged, and **library**, purely
earned and uncapped. A working takes what is inside the boundary you laid; if that is not enough, it
finishes out of whatever is nearest, and **there is always something nearest.**

> **"Name your source, or it'll name one for you."**

**Who can do this at all:** almost nobody. Everybody has some acuity, it is not hereditary and no
bloodline owns it, but the low end is a slope so steep that most people never cast anything. Ordinary
people call the top of that slope **the gift**; the trade says *she reads well and started young*.
**Keep both vocabularies** — which one a character uses tells the reader whose head they are in.

**And the class fact:** the sap economy is **not** a casters' economy. Extractor men, mill hands,
channel gangs, sinkers, gate crews, hauliers, drawing floors and the layers-out who handle the dead are
all ordinary labour done by people with no gift, and there are vastly more of them.

---

## GATE 3 — START HERE

**The loophole, and the atrocity built on it.** Gate 1 §9 describes the Law's crack and deliberately
does not walk through it. Gate 1's own leave-open list: *"The loophole, and the atrocity built on it —
the Law's crack is described and left standing open; nothing in this document walks through it."*

### The crack, in Gate 1's exact words

> The Law commands you to name your source. **It does not say what a source may be.** A caster who
> names a person and lays the boundary on them has followed it exactly, and the working proceeds
> correctly. **Correct procedure and atrocity are the same act, performed with the same hands, in the
> same order.**

### What Gate 1 already hands you, so do not re-invent it

- **A reach takes water and lime** — the two things a body holds in bulk. A body holds about one nail's
  worth of iron; the arithmetic must survive a reader checking it.
- **The selection is dumb; the consequence is personal.** Same physics every time — but take water and
  lime from a young labourer and he is sick for a month; from an old woman and her hip goes and never
  comes back; from a reader and her acuity drops, because the read runs through tissue.
- **Reaching is aimable.** A caster can deliberately lay a bad boundary so the shortfall is taken from
  a source of her choosing. It is a *method*, not only an accident — while still happening by accident
  to people who did not intend it. **Whose method it is, is Gate 4, not Gate 3.**
- **The aimed reach is readable in advance** — the line laid slack, laid past the material, laid
  *behind* the caster, and she is looking at a person instead of at her work. Two full seconds to act.
- **A fresh body is the densest thing in most rooms** for water and lime, for the first two days. This
  is why nothing is worked in a house with a body in it. And *"soldiers who have been in one bad fight
  work beside their own dead on purpose, and everyone understands why, and the men who arrange it
  deliberately are a different kind of person and are known to be."*
- **The surrounding speech already exists:** *"Who's downstream?"* · *"Nothing goes short."* ·
  *"That's a nail's worth."* · *"Set it or shift it."*
- **The dead do not come back.** No astral layer, no spirits, nothing reads or moves **the difference**.
  Gate 3 must not open that door.

### What Gate 3 is for

Not *what is the atrocity* in the abstract — Gate 1 already states the mechanism. Gate 3 is **how a
world that knows this lives with it**: what is done about it, what is said about it, what is never said,
what the trade's own discipline is, who has walked through the crack and what happened to them, and what
it costs to be the person standing next to somebody who might.

**Do not name the antagonist.** That is Gate 4.

---

## Standing rules later gates must not break

- **Gate 1 and Gate 2 are closed.** If an idea requires amending either, the idea is wrong. Check
  against `gate-1-system.md` before writing, not after.
- **No astral layer.** The physical layer is the only one. *The difference* is an observed absence with
  no mechanism, and nothing ever gets one.
- **The gift is a folk word, not a mechanic.** The read is a scale, not a door, and never hereditary.
- **The credential is a name.** Casting is unlicensed; *who taught you* is the whole of a caster's
  standing, and it is why the self-taught body caster is excluded.
- **Coinages: zero of ten spent.** Every term in two closed gates is ordinary English doing new work.

---

## Historical — the three rejected Gate 2 attempts

Kept only so the mistakes are not repeated. Attempts 1 and 2 pinned schools to reading doctrine and were
rejected as too abstract to feel: *"Nobody picks a class because of their filing method."* Attempt 3
re-pinned to *what you cast with*, which was right, but sub-agents replaced the agreed plain names with
invented jargon and buried each school in thousands of words of ethnography.

Attempt 4 was audited before the human saw it and was rebuilt as a **class system** — playable schools,
protagonist start, a who-beats-whom counter graph. The human stopped it, and the record backed them:
Gate 1 scopes Gate 2 as *"how the trade organises its teaching, and what different traditions do
differently with the same two strokes."* Teaching and tradition. The class framing was drift and is
struck. What shipped is the fifth attempt.
