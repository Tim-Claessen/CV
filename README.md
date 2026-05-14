# Tim Claessen — Resume

A single-file, code-driven resume. One `index.html` contains the structure, styles, content and render logic. Interactive on the web with three lens filters; prints cleanly to a 2-page A4 PDF, with each lens producing what feels like a tailored CV.

---

## Quick start

```bash
git clone <repo-url>
cd resume
open index.html        # macOS — or just double-click
```

No build step. No dependencies. No framework.

---

## The lens model

Three lenses, each producing a distinct CV variant:

| Lens | Audience |
|---|---|
| **People Analytics** | Workforce, payroll, HR analytics and compliance roles |
| **Data Management** | Data platform, engineering, governance roles |
| **Business Analytics** | Risk, controls, audit, decision intelligence roles |
| **All** | Full view for browsing (not intended for print) |

When a lens is active, the resume changes in three ways:

1. **Profile paragraph** — completely different opener for that audience
2. **Role bullets** — bullets tagged for that lens are shown; others are hidden
3. **Projects and skills** — filtered to those tagged for that lens

Roles themselves are always shown — career chronology should not have unexplained gaps.

---

## Editing content

All content lives in a single JSON block near the top of `index.html`:

```html
<script id="resume-data" type="application/json">
{ ... }
</script>
```

Edit, save, reload.

### Schema

```
person        — name, tagline, contact details
lenses        — for each lens: label, description, profile paragraph
roles[]       — career history, newest first
  ├─ bullets[].lenses[]  ← which lenses this bullet should show under
  └─ clients              ← optional "key clients" line
earlierRoles  — single-line earlier history string
projects[]    — project cards, each tagged with lenses[]
skillGroups[] — your 5 skill groups:
                  • Data Technical (alwaysVisible: true)
                  • Risk (alwaysVisible: false)
                  • Systems (alwaysVisible: false)
                  • Domain Expertise (alwaysVisible: false)
                  • Solutions & Automation (alwaysVisible: true)
education[]
community[]
```

### Lens tagging

Three values: `people`, `data`, `business`.

```json
{ "lenses": ["people", "data"] }   // shows under People and Data
{ "lenses": ["business"] }          // shows under Business only
```

Items in **always-visible skill groups** (Data Technical, Solutions & Automation) don't need a `lenses` array — they show under every lens. Tag only the items in **lens-filtered groups** (Risk, Systems, Domain Expertise).

### Skill levels

Dots are 1–5. `1` = familiar, `3` = proficient, `5` = expert. Detail subtitles (the small grey text under the skill name) show on web only; print hides them automatically.

---

## Generating the PDF

1. Open `index.html` in **Chrome or Edge** (best print fidelity).
2. Select your lens. Profile, bullets, projects and lens-filtered skills all update.
3. `Cmd/Ctrl + P` → Destination: *Save as PDF*.
4. Settings:
   - Layout: **Portrait**
   - Paper size: **A4**
   - Margins: **Default** (the `@page` CSS rule controls actual margins — 14mm all round)
   - Scale: **100%** (not "Fit to page")
   - **Uncheck** "Headers and footers"
   - **Check** "Background graphics"
5. Save.

Verified page counts:
- **People** lens: 2 pages ✓
- **Data** lens: 2 pages ✓
- **Business** lens: 2 pages ✓
- **All** lens: 4 pages (browse view — not intended for print)

The print layout forces a page break before *Selected projects*, so page 1 = header + profile + experience, page 2 = projects + capabilities + education/community. Identical structure across lenses.

---

## Hosting on GitHub Pages

1. Push `index.html` to a GitHub repo.
2. Settings → Pages → Source: *Deploy from branch* → `main` → `/ (root)`.
3. Live at `https://<username>.github.io/<repo>/`.

Custom domain optional. Nothing to build.

---

## VS Code workflow

- Install **Live Server** (Ritwick Dey) — auto-reload on save.
- Right-click `index.html` → *Open with Live Server*.

---

## Customising

### Colour

In `index.html`, the `:root` block:

```css
--accent: #0F766E;        /* deep teal */
--accent-soft: #d9eae8;
--accent-dark: #0a544e;
```

Change all three together to recolour. The greyscale base (`--ink`, `--mid`, `--paper`) is intentionally restrained.

### Fonts

- **Fraunces** — display serif for name, drop cap, section titles
- **IBM Plex Sans** — body
- **IBM Plex Mono** — labels, dates, meta

Swap by changing the Google Fonts URL and the `--font-display` / `--font-body` / `--font-mono` variables in `:root`.

---

## Troubleshooting

### A lens overflows to 3 pages

Most likely culprits:

1. You added a long new role bullet — split or shorten it.
2. You added a new project — check whether to demote an older one.
3. You expanded the profile paragraph — keep around 5 sentences.

To tighten globally, in the `@media print` block:
- Reduce `.role { margin-bottom }` from `7pt` to `5pt`
- Reduce `.section { margin-bottom }` from `10pt` to `8pt`

### Print colours look washed out

Make sure **Background graphics** is checked in the print dialog.

### Dates overlapping role titles

If you add a longer date range, widen the date column. In the `@media print` block, increase the first value in `.role { grid-template-columns: 92pt 1fr; }`.

### Different browsers render differently

Chrome/Edge most consistent. Use Chrome for the canonical PDF.

---

## Roadmap / parked ideas

Things considered but deliberately not built — listed so they're not lost:

### Profile-based "named exports"
Beyond the three lenses, define named configs (e.g. "MinRes Senior Analyst", "Snowflake Native App PM") that pick a lens plus an override profile paragraph plus a curated project subset.

### Filter-aware PDF export button
A dedicated *Export* button that takes the current lens, locks state, optionally adds a target-role-specific opening line, then triggers print — making the PDF a deliberate artifact rather than a snapshot of browsing state.

### Client logos
Quiet logo strip under the "Key clients" line on web only. Source from a `logos/` folder, grayscale by default, full colour on hover. Skipped for portability and ATS safety.

### ATS-friendly export mode
A second print stylesheet that strips colour, columns and decorative elements — pure single-column text — for ATS pipelines. Toggle via `?ats` query parameter.

### Per-role skill highlights
Optional `highlightSkills: ["SAP ECP", "Power BI"]` per role — renders as small chips below the role summary. Tailoring without rewriting bullets.

### Paged.js for advanced print
If pagination ever gets fiddly, [Paged.js](https://pagedjs.org/) gives proper print typography in-browser. Adds ~50KB.

### Theme variants
Light + dark for web, print always light. Currently light only.

### Auto-sync from Google Sheets
A small Python script pulling from the Skills_and_Experience spreadsheet to regenerate the JSON block. Useful if the sheet becomes the source of truth.

### Multiple targets in one repo
Folder per target (`/minres/`, `/snowflake/`, `/in-house/`) sharing an extracted `style.css`. Trade-off: loses single-file portability.

---

## File structure

```
resume/
├── index.html      ← everything: HTML, CSS, JSON data, JS render logic
└── README.md       ← this file
```

Deliberately flat.

---

## Credits

- Fonts: [Fraunces](https://fonts.google.com/specimen/Fraunces) by Undercase Type · [IBM Plex](https://www.ibm.com/plex/) by IBM
- Hosting: GitHub Pages
- Built with Claude
