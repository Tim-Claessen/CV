# Tim Claessen — CV site

A lightweight, CSV-driven CV that builds into a static site and exports to PDF. Edit the CSVs in `/data`, push, and the site rebuilds. Deployed at [cv.timclaessen.com](https://cv.timclaessen.com).

## Features

- **Single source of truth** — plain CSV files in `/data` open in Excel or Sheets and diff cleanly in git.
- **Persona views** — three lenses (`all`, `business`, `data`) filter roles, bullets, projects, skills, and the profile summary. The active lens is chosen at build time.
- **Visibility toggles** — every record has a `visible` flag so content can be hidden without deleting it.
- **Skills with verbal levels** — Expert / Proficient / Familiar, each with a subtle 3-segment indicator, grouped by domain.
- **PDF export** — a Python script renders the built page to PDF and archives a dated copy (one per day).

## Stack

| Layer | Choice |
| --- | --- |
| Site | [Astro](https://docs.astro.build) (static output) |
| Hosting | [Cloudflare Pages](https://pages.cloudflare.com/) |
| Data | CSV parsed at build time with [papaparse](https://www.papaparse.com/) |
| PDF | [Playwright](https://playwright.dev/python/) (Python) |
| Interactivity | Vanilla JS (print button only) — no React or UI kit |

Node **22+** (see `.node-version` and `package.json` engines).

## Quick start

```sh
npm install
npm run dev       # http://localhost:4321
npm run build     # output to dist/
npm run preview   # serve the production build locally
```

## Project structure

```text
data/                   # SOURCE OF TRUTH — edit these day to day
  config.csv
  personas.csv
  roles.csv
  role_bullets.csv
  projects.csv
  skills.csv
scripts/
  export_pdf.py         # render built site → PDF, archive dated copy
cv/                   # committed PDF output (created on first export)
  cv-latest.pdf
  archive/cv-YYYY-MM-DD.pdf
src/
  lib/data.ts           # load + parse CSVs, filter by lens, expose typed records
  components/         # Header, Profile, Experience, Projects, Skills, Education, …
  pages/index.astro     # single page
  styles/cv-theme.css
public/                 # favicons and static assets
astro.config.mjs
package.json
```

## Updating content

| Task | What to do |
| --- | --- |
| Add a role | Row in `roles.csv` + bullets in `role_bullets.csv` |
| Add a project or skill | One row in the relevant CSV |
| Hide anything | Set `visible` to `FALSE` |
| Re-tag for a persona | Edit the `personas` cell (`business`, `data`, or `business\|data`) |
| Change which lens the site shows | Set `publish_lens` in `config.csv` to `all`, `business`, or `data` |
| Refresh the PDF | `npm run pdf` (or `python scripts/export_pdf.py --lens business`) |

Do not hard-code CV content in components. If a field is missing from the CSVs, add it to the data model first.

## Data model

Lens keys are `all`, `business`, and `data`.

### Persona tagging

Applies to roles, role bullets, projects, and skills. The `personas` column is a pipe-delimited subset of `{business, data}`.

- `all` view shows every visible record.
- A persona view shows records whose `personas` list includes that persona.
- `business|data` means the record appears in both persona views.
- An empty `personas` value means the record only appears in the `all` view.

`visible` is `TRUE`/`FALSE`. `FALSE` excludes the record everywhere, including PDF output.

### config.csv — `key,value`

Single-row-per-key settings: `name`, `tagline`, `location`, `email`, `phone`, `linkedin`, `linkedin_url`, `github`, `github_url`, `publish_lens`, `earlier` (a one-line footnote of pre-2017 roles).

### personas.csv — `key,label,description,profile`

One row per lens. `label` is display text, `description` the sub-label, `profile` the summary paragraph shown for that lens.

### roles.csv — `role_id,title,company,location,start,end,clients,summary,personas,visible`

Career history, newest first by file order. `clients` is an optional inline list. `summary` is the role's opening line; bullet points live in `role_bullets.csv`.

### role_bullets.csv — `role_id,order,text,personas,visible`

One row per bullet. Joined to roles on `role_id`, sorted by `order`. A bullet is hidden if its own `personas` does not match the active lens, even when its parent role is shown.

### projects.csv — `project_id,client,title,summary,systems,personas,featured,visible`

Selected projects. `systems` is a `|`-separated list rendered as tags/chips.

### skills.csv — `skill_id,domain,category,skill,description,proficiency,personas,featured,visible`

`proficiency` is one of `Expert`, `Proficient`, or `Familiar`. Grouped by `domain` then `category`. `featured = Y` skills can surface in a compact strip; the full grouped set appears in the Capabilities section.

## Persona / lens behaviour

The site renders **one lens per build**. Filtering happens in `src/lib/data.ts` at build time — there is no client-side lens switcher.

1. Set `publish_lens` in `config.csv` (`all`, `business`, or `data`).
2. Or override for a single build with the `CV_LENS` environment variable (used by the PDF script's `--lens` flag).

The profile paragraph, roles, bullets, projects, and skills all reflect the chosen lens. To produce persona-specific PDFs, run `python scripts/export_pdf.py --lens business`.

## Page layout

Single page, in order:

1. Header (name, contact, links)
2. Profile (per-lens summary)
3. Experience (roles + bullets)
4. Selected projects
5. Capabilities (skills grouped by domain)
6. Education (static: UWA, Bachelor of Commerce, Economics and Finance, GPA 6.5 / WAM 78.9)
7. Earlier roles footnote (from `config.earlier`)

A print button in the web chrome triggers the browser print dialog. Print CSS hides controls and fits cleanly to A4.

## Design

- **Type** — Fraunces (display), IBM Plex Sans (body), IBM Plex Mono (meta, dates, tags).
- **Palette** — warm off-white background, near-black ink, restrained teal accent. Single column, max width ~820px.
- **Skills** — verbal level plus a 3-segment indicator: Expert = 3/3, Proficient = 2/3, Familiar = 1/3.
- **Print** — lens bar and controls hidden; content fits A4 with the selected lens preserved.

## Commands

| Command | Action |
| --- | --- |
| `npm install` | Install dependencies |
| `npm run dev` | Start dev server at `localhost:4321` |
| `npm run build` | Build production site to `./dist/` |
| `npm run preview` | Preview the build locally |
| `npm run pdf` | Build and export `cv/cv-latest.pdf` |
| `npm run astro -- --help` | Astro CLI help |

## PDF export

One-time Playwright setup:

```sh
pip install -r requirements.txt
python -m playwright install chromium
```

Then:

```sh
npm run pdf
```

- Always overwrites `cv/cv-latest.pdf`.
- Also writes `cv/archive/cv-YYYY-MM-DD.pdf` (one file per calendar day; re-running overwrites today's file).
- Persona-specific: `python scripts/export_pdf.py --lens business`
- Skip rebuild: `python scripts/export_pdf.py --no-build`

On push to `main`, a GitHub Action builds the site, exports the PDF, and commits updated files under `cv/` back to the repo (pushes that only change `cv/` do not retrigger the workflow). Those bot commits use `[skip ci]` so Cloudflare Pages does not rebuild for PDF-only updates.

## TODO: Set up auto-publish (GitHub → Cloudflare)

Do this once. When it is done, every time you push changes to GitHub, Cloudflare will rebuild your CV and put it live on the web. You will not need to upload files by hand.

### Part 2 — Connect Cloudflare Pages to GitHub

- [ ] **5. Create a free Cloudflare account** (if you do not have one) at [dash.cloudflare.com](https://dash.cloudflare.com/).

- [ ] **6. Open Workers & Pages.** In the left menu, click **Workers & Pages**.

- [ ] **7. Create a Pages project.** Click **Create** → **Pages** → **Connect to Git**.

- [ ] **8. Authorise GitHub.** Cloudflare will ask to connect to your GitHub account. Click **Connect GitHub** and approve access. You can limit access to just this one repo if you prefer.

- [ ] **9. Select your repository.** Pick the CV repo you created in Part 1. Click **Begin setup**.

- [ ] **10. Fill in the build settings** exactly like this:

  | Setting | Value |
  | --- | --- |
  | **Production branch** | `main` |
  | **Framework preset** | None (or Astro if offered) |
  | **Build command** | `npm run build` |
  | **Build output directory** | `dist` |

  Cloudflare should pick up Node 22 from the `.node-version` file in this repo. You do not need to change anything else.

- [ ] **11. Skip builds for non-site changes.** In your Pages project, go to **Settings → Build → Build watch paths**. Keep **Include paths** as `*` and add these **Exclude paths**:
  - `cv/*` — PDF archive commits from GitHub Actions
  - `.github/*` — workflow-only changes

- [ ] **12. Click Save and Deploy.** Cloudflare will install packages, run the build, and publish your site. The first build takes a few minutes.

- [ ] **13. Check the live site.** When the build finishes, Cloudflare shows a link like `https://something.pages.dev`. Click it — your CV should appear.

### Part 3 — Use your own domain (optional)

Skip this if you are happy with the `.pages.dev` link for now.

- [ ] **14. Add a custom domain.** In your Pages project, go to **Custom domains** → **Set up a custom domain**.

- [ ] **15. Enter your domain.** For example: `cv.timclaessen.com`.

- [ ] **16. Follow Cloudflare’s DNS instructions.**
  - If your domain is already on Cloudflare, it usually sets up DNS for you.
  - If not, you add a **CNAME** record: name `cv`, target the `.pages.dev` address Cloudflare gives you.

- [ ] **17. Wait for DNS.** It can take a few minutes (sometimes up to an hour) before `cv.timclaessen.com` works.

### After setup — how updates work

Once the steps above are done:

1. Edit a file (usually something in `data/`).
2. Save and push to GitHub:

   ```sh
   git add .
   git commit -m "Update CV"
   git push
   ```

3. Cloudflare notices the push, runs `npm run build` again, and updates the live site. No extra steps needed.

You can watch builds in the Cloudflare dashboard under your Pages project → **Deployments**. If a build fails, open the build log — it usually shows what went wrong (often a typo in a CSV file).

### Notes

- The site is **static** — Cloudflare just hosts the built files in `dist/`. There is no server to manage.
- To publish a specific persona view on the live site, set `publish_lens` in `config.csv` before you push (`all`, `business`, or `data`).

## For AI agents

When working on this repo:

- **Do not invent CV content.** Everything renders from `/data`. If a field is missing, stop and ask rather than hard-coding.
- **Keep dependencies minimal** — Astro, papaparse, and TypeScript only. Static output (`output: 'static'`).
- **Respect the persona tagging rules** above when adding or filtering records.
- **Match existing conventions** — read surrounding components and `data.ts` before changing structure.

### Development server

When starting the dev server in an agent session, prefer background mode:

```sh
astro dev --background
```

Manage it with `astro dev stop`, `astro dev status`, and `astro dev logs`.

### Astro reference

Full documentation: https://docs.astro.build

Useful guides:

- [Routing](https://docs.astro.build/en/guides/routing/)
- [Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Framework components](https://docs.astro.build/en/guides/framework-components/)
- [Content collections](https://docs.astro.build/en/guides/content-collections/)
- [Styling](https://docs.astro.build/en/guides/styling/)
- [Internationalization](https://docs.astro.build/en/guides/internationalization/)
