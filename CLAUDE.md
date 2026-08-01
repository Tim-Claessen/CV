# CLAUDE.md

Context for AI tools working in this repo. [README.md](README.md) is the authority on the data flow (lore → `content/career.json` → site + PDF) and the override layers - read it before touching `content/`, `overrides/` or `src/lib/career.ts`.

## How Tim likes AI tools to work with him

At the start of a session, read `../lore/knowledge/agents/Claude Code.md` and follow it. It is the source of truth for these preferences; keep it updated there rather than duplicating the guidance here.

## House rules

Decisions already made. Breaking one of these is a regression, not a judgement call.

| Rule | Why |
| --- | --- |
| **No em dashes.** Not in copy, not in comments, not in the README | House style. lore's own prose has ~70, so `deDash()` in `src/lib/career.ts` converts them at render: a dash introducing a list becomes a colon, one introducing a clause becomes a comma. The character legitimately survives in exactly one place, the regex that removes it |
| **Never name lore on a rendered page**, or say when the data was generated | It is where the facts come from, not something a reader needs. No provenance line, no build stamp, no "generated from" footer |
| **`publicTitle` says what the work was, not who it was for** | Every surface prints the client descriptor beside the title, so "Rostering review for an ASX-listed fuel and convenience retailer" reads it back twice. Titles repeat across clients as a result, which is why public slugs are composed from title + the client's `publicSlug` |
| **No nav bar.** The header carries the name and nothing else | A bar mixing page links with same-page anchors behaved two ways depending on where you already were. Destinations live in the page body: hero buttons, "All N projects", "View N projects", breadcrumbs |
| **Do not link `/cv` or `/build` from a public page** | Both are unlisted and send `noindex`. The layout adds them to the nav only when you are already on one of them |
| **No proficiency meters where the set is uniform** | Nearly every skill is Expert, so three identical segments said nothing. `/capabilities` shows the level as a word plus the project count, which is what actually varies |
| **Run `npm run build && npm run check:public` before finishing** | It reads the built HTML and fails on any non-public client name, whatever the upstream logic thought. It is the last line of defence, and it runs in CI too |

`README.md` carries the reasoning behind these in full, plus the prose scrubber that makes
lore write-ups publishable (client names to "the client", `[[wikilinks]]` resolved, lore's
margin notes dropped).

## Gotchas

### npm drops `@emnapi/*` from the lockfile on Windows

**Symptom.** The Cloudflare build fails at the install step, before the build ever runs:

```
npm error `npm ci` can only install packages when your package.json and
npm error package-lock.json or npm-shrinkwrap.json are in sync.
npm error Missing: @emnapi/core@1.11.1 from lock file
npm error Missing: @emnapi/runtime@1.11.1 from lock file
```

**Cause.** `@emnapi/core` and `@emnapi/runtime` are dependencies of the wasm32-wasi native bindings (`@rolldown/binding-wasm32-wasi`, `@bruits/satteri-wasm32-wasi`, `@img/sharp-wasm32`). Those packages are optional and excluded on Windows, so when npm updates an existing `package-lock.json` in place it prunes the two `@emnapi/*` entries while leaving the references to them behind. The lockfile is then self-inconsistent. `npm install` on Windows doesn't care; `npm ci` on Cloudflare's Linux builder refuses.

It is a bug in npm's in-place lockfile update, not in this repo. A *fresh* resolve (no existing lockfile) includes the entries correctly.

**Fix.** Re-add both entries to `package-lock.json` under `packages`, alongside `node_modules/@emnapi/wasi-threads`:

```json
"node_modules/@emnapi/core": {
  "version": "1.11.1",
  "resolved": "https://registry.npmjs.org/@emnapi/core/-/core-1.11.1.tgz",
  "integrity": "sha512-RSvbQmHzdKzNsLYa/wHrbc3KN4sYLKAdPZxqiM2HATqv/SBk2/ENSHpvXGaLOMcsAyz0poEGqkmmKYG3OWiJEQ==",
  "license": "MIT",
  "optional": true,
  "peer": true,
  "dependencies": { "@emnapi/wasi-threads": "1.2.2", "tslib": "^2.4.0" }
},
"node_modules/@emnapi/runtime": {
  "version": "1.11.1",
  "resolved": "https://registry.npmjs.org/@emnapi/runtime/-/runtime-1.11.1.tgz",
  "integrity": "sha512-vgj7R3y3Wgx24IQaGPA/R6YFXLHVMOZ0uVEyIQPaWs+rd1AzfEMXlAC22FYwO1XkKR6NPsq7mUandH8oIRdZFw==",
  "license": "MIT",
  "optional": true,
  "peer": true,
  "dependencies": { "tslib": "^2.4.0" }
}
```

Don't "fix" it by deleting `package-lock.json` and regenerating. That produces a correct lockfile but drifts ~120 packages (astro compiler, sharp, workerd, miniflare), turning a build fix into an unreviewed dependency upgrade. Patch the two entries; upgrade deliberately and separately.

**Prevention.** Expect this after *any* dependency change made on Windows. Before committing a modified `package-lock.json`, verify every dependency reference resolves to an entry - `npm ci` in a scratch directory is the definitive check, and far cheaper than a failed Cloudflare build.

**History.** Hit 2026-06-27 (fixed in 81eb565) and again 2026-07-29 after the papaparse → js-yaml swap in e06b0be.
