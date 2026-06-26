# The Ledger — CV Theme Guide

A self-contained CV system for **Tim Claessen**. Three files, no build step, no
dependencies. Open the HTML in any browser; print it straight to a 2-page A4 PDF.

```
cv-theme/
├── cv-theme.css            ← the theme: design tokens + every component + print rules
├── Tim Claessen — CV.html  ← the worked example: your real content as editable JSON
└── CV-THEME-GUIDE.md       ← this file
```

The golden rule: **content lives in the HTML's JSON blocks, styling lives in the
CSS.** You never touch CSS to update the CV, and you never touch markup to
re-skin it.

---

## 1 · The look, in one paragraph

Editorial single column. A large **Fraunces** serif name over a monospace
tagline, sitting on a heavy ink rule. Sections are numbered (`01 · Profile`)
with an italic display title and a hairline. The profile opens with a drop cap.
Experience runs down a fixed date column marked with a small accent tick.
Selected projects are cards with an accent keyline and monospace tech chips.
**Capabilities are the centrepiece** — each skill scored 1–5 on a segmented
meter with a proficiency word (Expert / Advanced / Proficient / Working /
Familiar). Warm off-white paper, a single clay accent, three typefaces doing
distinct jobs.

**Type roles**
- `Fraunces` (display serif) — name, section titles, role titles, project & education headings
- `IBM Plex Sans` (body) — all running text and bullets
- `IBM Plex Mono` (mono) — labels, dates, contact, chips, capability detail, level words

---

## 2 · The lens system (the clever bit)

The top bar filters the whole CV to a **lens**: `All · People · Data · Business`.
Choosing a lens swaps the profile paragraph and hides every experience bullet,
project, and (non-core) skill that isn't tagged for that lens. It's how one
file becomes four targeted CVs.

Tag any bullet / project / skill with a `"lenses"` array:

- `"lenses": ["people", "business"]` → shows under People, Business, and All
- **no `lenses` key** → always visible (use for universal, must-keep content)

Skill *groups* can also be pinned with `"alwaysVisible": true` (the core
technical groups), so they appear under every lens; groups without it only
surface their lens-matched items.

> The lens bar and Print button are screen-only — they never appear in the PDF.

---

## 3 · Editing the content

Every block is a `<script type="application/json" id="resume-…">` in the
HTML `<head>`. Edit the JSON, save, refresh. Schemas:

**Person**
```json
{ "name": "...", "tagline": "...", "phone": "...",
  "email": "...", "linkedin": "...", "linkedinUrl": "https://..." }
```

**A role** (in `resume-roles`)
```json
{ "id": "ey-director", "title": "Director, Risk Analytics", "company": "EY",
  "location": "Perth", "start": "Mar 2022", "end": "Present",
  "summary": "One-line framing of the role.",
  "bullets": [ { "text": "Achievement…", "lenses": ["people","data"] } ],
  "clients": "South32 · Fortescue · Rio Tinto"   // optional footer line
}
```

**A project** (in `resume-projects`)
```json
{ "id": "P003", "client": "Fortescue", "title": "Payroll CCM",
  "description": "What you built and the outcome.",
  "stack": ["SAP ECP", "Power BI"], "lenses": ["people","business"] }
```

**A capability** (inside a group in `resume-skills`) — `level` drives the meter
```json
{ "name": "Power BI", "level": 5, "detail": "DAX · Power Query · RLS",
  "lenses": ["data"] }     // omit lenses inside an alwaysVisible group
```
`level`: **5** Expert · **4** Advanced · **3** Proficient · **2** Working · **1** Familiar.

`resume-earlier` is a single string; `resume-education` and `resume-community`
are simple arrays. Nothing else is required — add or remove items freely and the
layout reflows.

---

## 4 · Re-skinning (colour & type)

Open `cv-theme.css`, change the tokens at the top in `:root`. The whole CV
follows. To swap the accent, change three values:

```css
/* Default — clay / burnt sienna */
--accent: #A14A33;  --accent-soft: #F2E2D9;  --accent-dark: #7C3621;

/* Alt — deep teal (cooler, the original palette) */
--accent: #0F766E;  --accent-soft: #D9EAE8;  --accent-dark: #0A544E;

/* Alt — ink navy (most conservative) */
--accent: #2A4D69;  --accent-soft: #DCE6EE;  --accent-dark: #1C3447;
```

Paper, ink and hairline are tokens too (`--paper`, `--ink`, `--line`, …). Keep
white/ink saturation low so it stays editorial rather than loud. Swapping a
font means changing the Google Fonts `<link>` in the HTML and the
`--font-*` tokens — keep the three-role split (display serif / sans body / mono
labels) and it stays coherent.

---

## 5 · Printing to PDF

Click **↓ Print / PDF** (or Cmd/Ctrl-P) → *Save as PDF*. The theme:
- forces **A4** with even margins,
- forces a **page break before Selected Projects** so page 2 starts cleanly,
- rescales every element to print points and hides the web chrome.

A **lens-filtered** view (People / Data / Business) is tuned to land on **2
pages**. The **All** view is the master superset and will run slightly longer —
pick a lens before saving the PDF you send.

---

## 6 · How to prompt Claude with this theme

Paste both `cv-theme.css` and `Tim Claessen — CV.html` into the chat (or attach
them), then steer with plain instructions. Claude edits **only the JSON** unless
you ask it to touch the design. Useful openers:

> *"Here's my CV theme — a CSS file and an HTML file. The content is in the
> JSON `<script>` blocks in the HTML head; styling is in the CSS. Keep that
> separation. Don't change the structure or class names."*

Then, things you can ask for:
- **Tailor to a job:** *"Here's a job ad for an in-house People Analytics Lead.
  Rewrite my profile and re-tag bullets/projects/skills so the `people` lens
  tells the strongest story for it."*
- **Add experience:** *"Add a new role at the top of `resume-roles`: [details].
  Tag the bullets across the right lenses."*
- **Add / re-score skills:** *"Add 'Microsoft Fabric' at level 3 to Data
  Technical with a one-line detail."*
- **Re-skin:** *"Switch the accent token to the teal palette in the guide."*
- **Tighten to 2 pages:** *"In the People lens this runs to 3 pages — trim the
  weakest bullets and drop level-3 skills until it fits two."*

Guardrails worth repeating to Claude: keep `id` values stable, keep the
`"lenses"` tags consistent (`people` / `data` / `business`), keep `level` between
1–5, and don't introduce new CSS classes — the theme already has one for every
piece.

---

*Built as a reusable system: the same CSS will dress any future content you pour
into the JSON. The HTML example is just one filling of the mould.*
