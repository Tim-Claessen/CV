---
description: Tailor a CV to a job description as a point-in-time application record
argument-hint: <job description, or the slug of an application in progress>
---

# /tailor

Produce a CV for one job application. The job is mostly **rewording**: take what lore
already says and phrase it in the job description's terms. A short interview feeds that
rewording; it doesn't replace it. Nothing is invented to fill a gap.

Input: $ARGUMENTS

## Where things live

| What | Where | Why |
| --- | --- | --- |
| The application record | `../lore/knowledge/job-applications/<yyyy-mm-employer-role>/` | Names the employer and holds the JD. lore is private; this repo is public |
| Durable career facts | `../lore/knowledge/` | Only via additive edits, then lore's `/cv-sync` |
| The renderer | `src/lib/applications.ts`, `src/pages/apply/[slug].astro` | Private mode only |

**Never write an employer name, JD text or application content into this repo.**

## Rules

- **Point in time.** The record is a snapshot. It stamps `builtAgainst` with `career.json`'s
  `generated` date. Once `status: sent`, it is frozen: its `cv.pdf` is the record, and the
  build no longer renders it.
- **Light in lore.** `knowledge/job-applications/` is private and skipped by lore's own
  skills, so they never see it. Name lore entities in plain text, **never `[[wikilinks]]`**,
  so Obsidian backlinks stay clean. Links run from the application to lore, never back.
- **Embellish additively.** Application wording lives only in `application.yaml`. Never
  overwrite lore bodies or this repo's `overrides/` for one application.
- **The routing test** for anything the interview surfaces: *would it still be true and worth
  knowing in a year, whatever happens with this job?* Yes: propose a lore addition (new
  entity, or a paragraph appended to an existing one), show Tim the wording, apply it, re-run
  `/cv-sync`. No: it stays in the application's `notes.md`.
- Confidential clients stay unnamed in lore bodies, because bodies publish with a descriptor.

## Steps

### 1. Read the JD (no questions)
Create the folder and write `jd.md`: the JD as given, the requirements, **their vocabulary**,
and anything they say they don't want. Put the date at the top.

### 2. Evidence map (no questions)
Read `content/career.json` and the relevant lore bodies. Write `notes.md` with a table:
requirement, lore evidence (plain names), strength (strong / adjacent / gap). Tim skims it.
It decides what the interview asks; most rows need nothing.

### 3. Interview (about 10 questions at most, in small batches)
Label every question with its kind, so Tim knows where the answer goes:

| Kind | Ask when | Answer goes to |
| --- | --- | --- |
| **[P] Positioning** | Always, 2 to 4: identity line, what to lead with, how to handle the gap, tone | `notes.md` only |
| **[D] Depth** | Evidence the pitch rests on is thin on record | Facts: lore (additive). Framing: `notes.md` |
| **[G] Gap probe** | A requirement with no evidence | Real and durable: lore addition. Nothing: accept the gap |

"Skip" is always a fine answer. Don't push for material Tim says isn't CV content.
Record the answers and any lore additions in `notes.md`, then revise the evidence map.

### 4. Rewording pass (the main event)
Draft, then show Tim a side-by-side table per item and let him accept, edit or reject each line:

| Lore says | Proposed CV wording | Serves JD requirement | Evidence |
| --- | --- | --- | --- |

Cover the tagline, profile, bullets per role, project choice, order, titles and one-line
summaries, and which skills and technologies to show. Allowed: emphasis, their vocabulary,
leading with a different outcome, reordering. Not allowed: facts that aren't in lore.
No em dashes.

What the wording is for, learned from the first run:

- **Role bullets carry the shape of the job; the cards carry the detail.** Detail in both
  reads as repetition. Three or four bullets on the current role, none on the older ones.
- **Cards lead with the problem, then the solution.** A list of what was built, with no
  problem in front of it, is the most common note back.
- **The profile is not a cover letter.** It says what he does and who for, lightly. The
  evidence is the rest of the page.
- **Quantify where lore can.** One hard number beats three adjectives, and benefit reads as
  time freed, never headcount.

Then write `application.yaml`:

```yaml
employer: <name>
role: <title>
status: drafting            # drafting renders; sent and closed never do
builtAgainst: "YYYY-MM-DD"  # career.json generated date
basePersona: business       # defaults for anything not set below
tagline: <line under the name>
profile: >-
  <paragraph>
hideCommunity: [<lore community entry>]   # optional, buys space
roles:                      # keyed by lore role name; unlisted roles keep persona bullets
  "<lore role name>":
    title: <optional>       # overrides lore's role title on this CV only
    summary: >-             # optional
    bullets:                # replaces the role's bullets; [] leaves the summary alone
      - text: <bullet>
        evidence: ["<lore project or role name>"] # required, validated at build.
                                                  # Quote names: role names contain commas
hideRoles: [<lore role name>]
projects:                   # ordered; plain names or objects
  - name: <lore project name>
    title: <optional>       # keep to one line, and consistent across cards
    client: <optional>      # label only: one line, "Confidential client" where unnameable
    summary: <optional>     # problem, then solution
    technologies: [<optional display labels>]   # chips only; the facts stay in lore
skills: [<lore skill names>]
technologies: [<lore technology names>]
```

`client` and `technologies` on a card are **labels, not facts**: they exist so a long client
name fits one line, a confidential one can still be named, and a tool can read the way the
employer knows it ("EY VIA"). Everything else validates against lore and fails the build.

### 5. Render, review and export
- **Review in the page: `npm run edit -- <slug>`.** It builds, serves and opens the sheet at
  `/apply/<slug>/?edit=1` with its text editable, and Save writes back into the record. Start
  the server for Tim and give him the URL rather than handing him a command to run.
- Preview only, no editing: `CV_MODE=private npm run dev`, then open `/apply/<slug>`.
- Export: `python scripts/export_pdf.py --application <slug>`. It builds privately into
  `dist-private/` and writes `cv.pdf` into the application folder.
- **Read the PDF back every time.** Page count alone doesn't show a clipped name or a
  ragged column.
- **Target two A4 pages.** "Selected projects" starts page two, so everything before it
  fills page one. Levers, cheapest first: cut a role's bullets to `[]`, trim a card summary
  by a line, drop a card (six fit as three even rows), `hideCommunity`, then wording.
- An invalid `evidence:`, project or capability name fails the build with a list. Fix the
  record; never loosen the check.

### 6. Cover letter (optional)
`cover-letter.md`, built from the evidence map. The biggest gap gets one honest sentence.

When Tim sends it, set `status: sent`.

## The review loop
Tim reviews in the page, not in the file:

```sh
npm run edit -- <slug>      # builds, serves, opens /apply/<slug>/?edit=1
```

The text on the sheet is editable. Save writes the changed values straight back into
`application.yaml` (comments and folding survive, because the write is line-level) and
rebuilds, so the page always shows the record rather than the browser's copy. "Save and PDF"
also re-exports and reports the page count, which is the fastest way to see a change spill to
three pages.

Editable: tagline, profile, role summaries and bullets, project client, title, summary and
tool chips. Fixed: names, dates, employers, capabilities, education, and `evidence:`, since
re-pointing a bullet at a different lore project is a tailoring decision, not a wording one.

Editing the YAML by hand still works and is the right move for structural changes: adding or
removing a bullet or a card, reordering, or changing which capabilities show. Don't build a
Word or Markdown copy to mark up.

## Gotchas, each one hit on the first run
- **Close the PDF before exporting.** Windows locks an open PDF and the export fails; the
  script says so rather than throwing a stack trace. Saving from the editor is unaffected;
  only "Save and PDF" needs the file closed.
- **An editor holding the file can write a stale buffer back over it.** After Tim edits,
  re-read the record before assuming your own last edit survived, and say so if it didn't.
- **YAML splits inline lists on commas**, so `[EY Director, Risk Analytics]` is two names and
  fails validation. Quote every evidence name.
- **A formatting change belongs to the application page.** Scope CSS to `.page--apply` so the
  public `/cv` keeps its own look, unless Tim asks for the change everywhere.

## Before finishing
`npm run build && npm run check:public` must pass. It also fails if a public build ever
contains `apply/`.
