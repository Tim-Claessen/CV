# Tim Claessen - CV site

A CV site fed from [lore](https://github.com/Tim-Claessen/lore), Tim's knowledge base. lore holds the career facts; this repo holds how they read on a CV. Deployed at [cv.timclaessen.com](https://cv.timclaessen.com).

## How the data flows

```text
lore/knowledge/  ──/cv-sync──▶  content/career.json  ──┐
(source of truth)               (generated, committed)  ├──▶  site + PDF
                                overrides/*.yaml     ──┘
                                (yours, hand-edited)
```

**The direction is one-way.** lore is the source of truth; this repo is downstream. Nothing here is imported back into lore. If the CV needs a fact lore doesn't have, fix lore.

| Layer | Owner | What lives there |
| --- | --- | --- |
| `content/career.json` | generated | Facts: clients, dates, technologies, skills, outcomes. Never hand-edit - `/cv-sync` rewrites it wholesale |
| `overrides/*.yaml` | you | Presentation: CV wording, role bullets, ordering, anonymised titles. Survives every sync |
| `config.yaml` | you | Contact details. Deliberately not in lore - there is no person entity for Tim, and `people/` is private |

To refresh from lore, run `/cv-sync` in the lore repo. It writes `content/career.json` here and reports what changed.

## Features

- **Fed from lore** - 59 projects, 9 roles, 19 skills and 32 technologies, with their full link graph, instead of hand-maintained CSVs.
- **Persona views** - lenses (`all`, `business`, `data`) filter roles, bullets, projects and skills. A persona is a saved selection of lore entity names, so one list drives both the skills shown and the projects selected.
- **Client anonymisation** - the public site never names a client marked `public: false` in lore. See below.
- **Published write-ups** - lore's project bodies render on the public site with client names swapped for "the client" and `[[wikilinks]]` resolved into real links, rather than being withheld.
- **Skills with verbal levels** - Expert / Proficient / Familiar, each with a 3-segment indicator.
- **PDF export** - a Python script renders the built page to PDF and archives a dated copy.

## Client anonymisation

lore marks each client `public: true` (employers and partners) or `public: false` with a `public-name:` descriptor. This site has two build modes:

| Mode | Clients | Use |
| --- | --- | --- |
| `public` (default) | Anonymised descriptors | The deployed site |
| `private` (`CV_MODE=private`) | Real names | A CV going to one named recipient |

The hard part isn't the client node - it's that lore names projects after their clients ("Silverchain Payroll Analytics & Remediation"). So `/cv-sync` flags those, and the build **fails closed**: a flagged project doesn't render publicly until `overrides/projects.yaml` supplies a `publicTitle`.

Four separate mechanisms have to agree for anonymisation to hold - lore's `public:` flags,
cv-sync's leak detection, this repo's overrides, and the prose scrubber below - so there's
a backstop that reads the built HTML:

```sh
npm run build && npm run check:public
```

It fails on any non-public client name in the output, whatever the upstream logic thought. It also runs in CI.

### Publishing lore prose

Project write-ups and capability descriptions are lore bodies. They are written for lore,
not for the web: they name clients outright, cross-reference other entities as
`[[wikilinks]]`, and carry lore's own margin notes. `renderProse()` in
[`src/lib/career.ts`](src/lib/career.ts) resolves all three, so the write-up publishes
instead of being withheld:

| In lore | On the public site |
| --- | --- |
| The project's own non-public client, by name | `the client` - "analytics into Worley's audits" becomes "analytics into the client's audits" |
| Any other non-public client, by name | Its public descriptor, with an article - `a global energy major` |
| `[[Another Project]]` | A link, titled with that project's public wording. Plain text where the target isn't publishable |
| `[[Snowflake]]` | A link to `/capabilities/snowflake` |
| A wholly italicised paragraph | Dropped. These are lore's ingest bookkeeping ("P003 - the 2026 extraction entry was folded in here"), not the engagement |

Identifier matching mirrors `check_public.py` exactly: full client names and aliases of
four characters or more, on word boundaries. Anything shorter is left alone, because
"VIA" would match the word "via" - which means a *fragment* of an alias can survive
(`Transurban NSW` is scrubbed; a bare "NSW" is not). `check_public.py` defines the policy;
the scrubber implements it, and the check is the backstop if it misses one.

## Stack

| Layer | Choice |
| --- | --- |
| Site | [Astro](https://docs.astro.build) (static output) |
| Hosting | [Cloudflare Pages](https://pages.cloudflare.com/) |
| Data | JSON from lore + YAML overrides ([js-yaml](https://github.com/nodeca/js-yaml)) |
| PDF | [Playwright](https://playwright.dev/python/) (Python) |
| Interactivity | Vanilla JS (print button only) - no React or UI kit |

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
content/
  career.json           # GENERATED by lore's /cv-sync - never hand-edit
overrides/              # YOURS - presentation layer, survives every sync
  projects.yaml         # publicTitle, headline, bullet, weight per project
  roles.yaml            # CV bullets and client lines per role
  personas.yaml         # saved selections + profile paragraphs
config.yaml             # contact details
scripts/
  seed_overrides.py     # draft public wording for newly withheld projects
  check_public.py       # fail the build on a leaked client name
  export_pdf.py         # render built site → PDF, archive dated copy
cv/                     # committed PDF output
src/
  lib/career.ts         # merge career.json + overrides, expose typed records
  components/           # Header, Profile, Experience, Projects, Skills, Education
  layouts/Site.astro    # shared shell: nav, footer, unlisted-route handling
  pages/
    index.astro         # homepage
    work.astro          # the full filterable record
    cv.astro            # printable CV (unlisted)
    build.astro         # CV builder (unlisted)
  styles/
    cv-theme.css        # the printable CV - print-first
    portfolio.css       # tokens + site chrome, shared by every screen page
    home.css            # the homepage only
    builder.css
public/
```

## Updating content

| Task | What to do |
| --- | --- |
| Add a role, project, skill or client | Add it in **lore**, then run `/cv-sync` |
| Reword something for the CV | Edit `overrides/projects.yaml` or `overrides/roles.yaml` |
| Hide a project from the CV | `hidden: true` in `overrides/projects.yaml` |
| Promote a project | `weight:` in `overrides/projects.yaml` - higher sorts earlier |
| Re-tag for a persona | Edit the entity lists in `overrides/personas.yaml` |
| Pick the lens for a build | `CV_LENS=business npm run build` |
| Draft wording for new withheld projects | `npm run seed:overrides` |
| Refresh the PDF | `npm run pdf` |

Do not hard-code CV content in components, and do not edit `content/career.json` - both get overwritten. Content lives in lore; wording lives in `overrides/`.

## Data model

`content/career.json` carries lore's professional layer with its links resolved and reverse
edges derived, so the site can answer "which projects evidence this skill?" without lore
hand-maintaining both directions.

| Key | What |
| --- | --- |
| `projects` | Client, dates, skills, technologies, outcome, plus `leaks` / `publicSafe` for anonymisation |
| `roles` | Employment history with employer and dates |
| `skills`, `technologies` | Kept separate, as lore models them - practices vs tools |
| `clients` | With `public`, `publicName` and a `publicSlug` that never encodes a real name |
| `evidence` | Reverse index: skill / technology / client / role → project slugs |
| `warnings` | Unresolved links and data notes from the sync |

Private layers are absent by construction: `/cv-sync` uses a hard allowlist, and `team:`
(which points at people) is stripped at the boundary.

### Overrides

`overrides/projects.yaml`, keyed by lore project name:

| Field | Effect |
| --- | --- |
| `publicTitle` | Replaces the lore name publicly - required where the name quotes a non-public client. Say what the work *was*, not who it was for: every surface prints the client descriptor beside the title, so "Rostering review for an ASX-listed fuel and convenience retailer" reads it back twice. Titles therefore repeat across clients, and the public URL is composed from the title plus the client's `publicSlug` to stay unique |
| `publicOutcome` | Same, for the outcome line |
| `headline` | Short label, any mode |
| `bullet` | CV wording, overriding lore's `outcome:` |
| `weight` | Higher sorts earlier |
| `hidden` | Excluded everywhere |
| `draft` | Auto-drafted, not yet reviewed |

`overrides/roles.yaml` holds `summary`, `bullets` (with per-persona tags), `clients`
(private mode only - it names organisations outright) and `publicClients`.

## Routes

| Route | What it is |
| --- | --- |
| `/` | **Homepage** - nameplate, track record, then selected work beside what the work adds up to, capabilities, contact |
| `/work` | **The full record** - every project, filterable by client, industry, type of work, technology, skill and year, plus every capability. Filters are reflected in the URL, so a filtered view can be linked |
| `/projects/<slug>` | Project detail: the write-up, facts, what it used, related work sharing a skill or technology |
| `/capabilities/<slug>` | A skill or technology, with the projects that evidence it - derived from lore's backlinks, not hand-maintained |
| `/cv` | *Unlisted.* The printable two-page CV. Carries lore's `featured:` projects only |
| `/build` | *Unlisted.* **CV builder** - tick roles, projects and capabilities, edit the preview inline, print to PDF |

### Unlisted routes

`/cv` and `/build` still build and deploy, but no public page links to either and both
send `noindex, nofollow`. The nav offers them only once you are already on one of them,
so the two stay navigable between each other without the homepage or `/work` advertising
them.

**Unlisted is not private.** Anyone with the URL can read either page. `/cv` is anonymised
and passes `check:public` like everything else; `/build` embeds the whole project payload
in the page, still anonymised but complete. If these ever need to be genuinely private,
the fix is to stop emitting them - move both out of `src/pages/` and inject the routes
from `astro.config.mjs` only when a local env flag is set - not to obscure them further.

### The builder

A persona is a saved tick-list, so "choose a persona" and "tick what you want" are one
mechanism: pick a starting point, then adjust. Everything runs client-side against a JSON
payload embedded in the page - no server, no framework.

- Selections persist in `localStorage` and encode into the URL (`?s=…`), so the exact CV
  sent to a given employer can be recovered later.
- Any text in the preview is `contenteditable`. Edits apply to that printout only and are
  never written back to lore - put wording you want to keep in `overrides/`.
- **Print** produces the sheet alone: picker, nav and chrome are hidden, and roles and
  projects never split across a page break.

The builder inherits the build's mode, so the deployed one can only ever offer anonymised
clients. For a real application, run it locally:

```sh
CV_MODE=private npm run dev    # then open /build
```

## Page layout (the `/cv` page)

1. Header (name, contact, links)
2. Profile (per-lens summary)
3. Experience (roles + bullets)
4. Selected projects (`featured:` in lore)
5. Capabilities (skills, then technologies, grouped by category)
6. Education and community (from lore's `credentials/` and `community/`)
7. Earlier roles footnote (from `config.earlier`)

A print button triggers the browser print dialog. Print CSS hides controls and fits A4.

## Design

One visual language across the site, in three stylesheets that layer rather than compete:

| Stylesheet | Owns |
| --- | --- |
| `cv-theme.css` | The printable CV. Print-first, A4, its own token layer |
| `portfolio.css` | The `:root` tokens and the site chrome - header, nav, footer, cards, chips, meters |
| `home.css` | The homepage alone |

The homepage borrows the CV's voice - display type, numbered sections, the 2px ink rule
under the masthead, the accent tick beside a date - at web scale. It deliberately uses its
own class names (`.home-title`, not `.section-title`), because `portfolio.css` already
means something else by `.section-title` and both load on the same page.

- **Type** - Fraunces (display), IBM Plex Sans (body), IBM Plex Mono (meta, dates, tags).
- **Palette** - warm off-white paper, near-black ink, a single clay accent.
- **Skills** - verbal level plus a 3-segment indicator: Expert = 3/3, Proficient = 2/3, Familiar = 1/3.
- **Homepage copy is never invented.** The hero is the nameplate, the tagline from `config.yaml` and the `all` persona's profile paragraph. No slogan. Everything else on the page is lore data.
- **No em dashes.** Repo-authored copy is written without them. lore's prose has 70-odd, so `deDash()` in `career.ts` converts them on the way out: a dash introducing a list becomes a colon, one introducing a clause becomes a comma. The character survives in exactly one place, the regex that removes it.
- **No nav bar.** The header carries the name and nothing else. Every destination is reachable from the page body: hero buttons, "All N projects", "View N projects" per focus area, breadcrumbs on detail pages. A bar mixing page links with same-page anchors behaved two different ways depending on where you already were, and a bar with one link in it was doing less than the buttons already on the page.
- **The nameplate folds up.** On the homepage the name is the hero, so the header would say it twice. The header goes sticky and its brand fades in only once the hero nameplate leaves the viewport, watched by an `IntersectionObserver` rather than a scroll handler. The hidden state applies only to a scripted document (`html.js`, set before first paint), so without JS the brand simply stays visible rather than becoming a dead link home.
- **No footer on the homepage** (`bareFoot`), which ends in its own contact section and would otherwise repeat it.
- **Capabilities are a counted cloud, not meters.** Nearly every capability is Expert, so three identical segments carried no information. The homepage lists all of them as chips with the number of projects behind each; the meters stay on `/work` and the CV where they sit next to a mixed set.
- **Print** - lens bar and controls hidden; content fits A4 with the selected lens preserved.

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

Renders `/cv`, not `/`.

- Always overwrites `cv/cv-latest.pdf`.
- Also writes `cv/archive/cv-YYYY-MM-DD.pdf` (one file per calendar day; re-running overwrites today's file).
- Persona-specific: `python scripts/export_pdf.py --lens business`
- Skip rebuild: `python scripts/export_pdf.py --no-build`
- Refuses to run when `CV_MODE=private`. These PDFs are committed to a public repo, so a
  CV naming real clients must come from `/build` locally and stay out of git.

On push to `main`, a GitHub Action builds the site, exports the PDF, and commits updated files under `cv/` back to the repo (pushes that only change `cv/` do not retrigger the workflow). Those bot commits use `[skip ci]` so Cloudflare Pages does not rebuild for PDF-only updates.

## Deployment

Live at [cv.timclaessen.com](https://cv.timclaessen.com) on Cloudflare Pages, connected to
this repo's `main` branch. Push and it rebuilds - there is nothing to upload by hand.

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node | 22, picked up from `.node-version` |

Two things are worth knowing if you touch the Pages project:

- **Build watch paths.** Include `*`, exclude `cv/*` (PDF commits from the GitHub Action)
  and `.github/*` (workflow-only changes). Without those excludes the PDF bot triggers a
  site rebuild on every push.
- **Environment variables.** `CV_LENS` picks the persona to publish (`all`, `business`,
  `data`); leave it unset for the full view. **Leave `CV_MODE` unset.** The default is
  `public`, which anonymises clients. `private` is for local CV exports only and must
  never be set on the deployed site.

The site is static - Cloudflare just hosts the files in `dist/`. There is no server. If a
build fails, open the build log: it is usually a YAML syntax error in `overrides/`, or the
npm lockfile problem described in [CLAUDE.md](CLAUDE.md).

## For AI agents

When working on this repo:

- **Do not invent CV content.** Facts render from `content/career.json` (owned by lore); wording from `overrides/`. If a fact is missing, it's a gap in lore - stop and ask.
- **Keep dependencies minimal** - Astro, js-yaml, and TypeScript only. Static output (`output: 'static'`).
- **Never import CV content back into lore.** The flow is one-way. Where lore lacks something the CV wants, say so; don't backfill it from here.
- **Respect the persona tagging rules** above when adding or filtering records.
- **Match existing conventions** - read surrounding components and `data.ts` before changing structure.

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
