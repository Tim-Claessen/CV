/**
 * Job applications: one tailored CV per record, rendered at /apply/<slug>.
 *
 * A record lives outside this repo, in lore's knowledge/job-applications/ folder, because it
 * names the employer and holds the job description, and this repo is public.
 * Each record is a folder with an application.yaml; the folder name is the slug.
 *
 * Records are point in time. Only `status: drafting` renders: once a CV is sent,
 * its PDF is the record, and it is never rebuilt against data that has moved on.
 *
 * Tailored wording may reframe, never invent. Every bullet names the lore project
 * or role it rests on in `evidence:`, and the build fails if a name doesn't
 * resolve. Project, skill and technology selections are checked the same way.
 *
 * Private mode only. In public mode this module returns nothing, so the route
 * produces no pages and the deployed site cannot carry an application.
 */

import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { load as loadYaml } from 'js-yaml';
import {
  allCapabilities,
  capabilities,
  deDash,
  meta,
  persona,
  projects,
  resolveMode,
  roles,
  type CapabilityGroup,
  type Project,
  type Role,
} from './career';

interface RawBullet {
  text: string;
  evidence?: string[];
}

interface RawApplication {
  employer: string;
  role: string;
  status: 'drafting' | 'sent' | 'closed';
  /** career.json `generated` date the record was drafted against. */
  builtAgainst?: string;
  /** Persona supplying the defaults: bullets for unlisted roles, profile fallback. */
  basePersona?: string;
  /** Replaces config.yaml's tagline under the name. */
  tagline?: string;
  profile?: string;
  /** Community entries to leave off this CV, by lore name. */
  hideCommunity?: string[];
  roles?: Record<string, { title?: string; summary?: string; bullets?: RawBullet[] }>;
  hideRoles?: string[];
  /**
   * `client` and `technologies` are the card's labels, not facts: they let a
   * long client name fit one line, name a confidential one, or print a tool
   * the way the reader knows it. The facts stay in lore.
   */
  projects?: (
    | string
    | { name: string; title?: string; summary?: string; client?: string; technologies?: string[] }
  )[];
  skills?: string[];
  technologies?: string[];
}

/**
 * A cover letter, from cover-letter.md beside the record: a YAML block for the
 * letter's furniture, then paragraphs separated by blank lines. Rendered at
 * /apply/<slug>/letter. Free text, so nothing here is validated against lore.
 */
export interface Letter {
  date: string;
  recipient: string[];
  subject: string;
  salutation: string;
  closing: string;
  paragraphs: string[];
}

export interface Application {
  slug: string;
  employer: string;
  role: string;
  builtAgainst: string | null;
  /** True when lore has been re-synced since the record was drafted. */
  stale: boolean;
  tagline: string | null;
  profile: string;
  hideCommunity: string[];
  roles: Role[];
  projects: Project[];
  capabilities: CapabilityGroup[];
  letter: Letter | null;
}

export function applicationsDir(): string {
  return resolve(process.env.CV_APPLICATIONS ?? join(process.cwd(), '..', 'lore', 'knowledge', 'job-applications'));
}

function readLetter(folder: string): Letter | null {
  const file = join(folder, 'cover-letter.md');
  if (!existsSync(file)) return null;
  const text = readFileSync(file, 'utf-8').replace(/^﻿/, '').replace(/\r\n/g, '\n');
  const match = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  const head = (match ? loadYaml(match[1]) : {}) as Record<string, unknown> | null;
  const body = match ? match[2] : text;
  const field = (key: string): string => deDash(String(head?.[key] ?? '').trim());
  return {
    date: field('date'),
    recipient: String(head?.recipient ?? '').split('\n').map((line) => line.trim()).filter(Boolean),
    subject: field('subject'),
    salutation: field('salutation'),
    closing: field('closing'),
    // One paragraph per blank-line-separated block; line wraps inside it are joined.
    paragraphs: body
      .split(/\n\s*\n/)
      .map((block) => deDash(block.replace(/\s*\n\s*/g, ' ').trim()))
      .filter(Boolean),
  };
}

function build(slug: string, raw: RawApplication, letter: Letter | null): Application {
  const mode = 'private';
  const lens = raw.basePersona ?? 'all';
  const errors: string[] = [];

  const allRoles = roles(lens, mode);
  const allProjects = projects(mode);
  const projectByName = new Map(allProjects.map((p) => [p.loreName, p]));
  const roleNames = new Set(roles('all', mode).map((r) => r.loreName));
  const capabilityNames = new Set(allCapabilities(mode).map((c) => c.name));

  if (raw.basePersona && !persona(raw.basePersona)) {
    errors.push(`basePersona '${raw.basePersona}' is not in overrides/personas.yaml`);
  }

  for (const [roleName, role] of Object.entries(raw.roles ?? {})) {
    if (!roleNames.has(roleName)) errors.push(`roles: '${roleName}' is not a lore role`);
    for (const bullet of role.bullets ?? []) {
      const evidence = bullet.evidence ?? [];
      if (evidence.length === 0) {
        errors.push(`roles['${roleName}']: bullet has no evidence: "${bullet.text.slice(0, 60)}..."`);
      }
      for (const name of evidence) {
        if (!projectByName.has(name) && !roleNames.has(name)) {
          errors.push(`roles['${roleName}']: evidence '${name}' is not a lore project or role`);
        }
      }
    }
  }

  const picks = (raw.projects ?? []).map((item) => (typeof item === 'string' ? { name: item } : item));
  for (const pick of picks) {
    if (!projectByName.has(pick.name)) errors.push(`projects: '${pick.name}' is not a lore project`);
  }
  for (const name of [...(raw.skills ?? []), ...(raw.technologies ?? [])]) {
    if (!capabilityNames.has(name)) errors.push(`skills/technologies: '${name}' is not in lore`);
  }

  if (errors.length > 0) {
    throw new Error(`application '${slug}' is invalid:\n  - ${errors.join('\n  - ')}`);
  }

  const hidden = new Set(raw.hideRoles ?? []);
  const tailoredRoles = allRoles
    .filter((role) => !hidden.has(role.loreName))
    .map((role) => {
      const tailored = raw.roles?.[role.loreName];
      if (!tailored) return role;
      return {
        ...role,
        title: tailored.title ?? role.title,
        summary: tailored.summary ? deDash(tailored.summary) : role.summary,
        bullets: tailored.bullets
          ? tailored.bullets.map((b) => ({ text: deDash(b.text), personas: [] }))
          : role.bullets,
      };
    });

  // No explicit list falls back to what /cv shows: lore's featured projects.
  const selected = picks.length
    ? picks.map((pick) => {
        const project = projectByName.get(pick.name)!;
        return {
          ...project,
          title: pick.title ? deDash(pick.title) : project.title,
          summary: pick.summary ? deDash(pick.summary) : project.summary,
          client: pick.client ?? project.client,
          technologies: pick.technologies ?? project.technologies,
        };
      })
    : allProjects.filter((project) => project.featured);

  const builtAgainst = raw.builtAgainst ?? null;
  return {
    slug,
    employer: raw.employer,
    role: raw.role,
    builtAgainst,
    stale: builtAgainst !== null && builtAgainst !== meta.generated,
    tagline: raw.tagline ? deDash(raw.tagline) : null,
    hideCommunity: raw.hideCommunity ?? [],
    profile: deDash(raw.profile ?? persona(lens)?.profile ?? persona('all')?.profile ?? ''),
    roles: tailoredRoles,
    projects: selected,
    capabilities: capabilities(lens, {
      skills: raw.skills?.length ? raw.skills : undefined,
      technologies: raw.technologies?.length ? raw.technologies : undefined,
    }),
    letter,
  };
}

/** Drafting applications, private mode only. Throws on an invalid record. */
export function applications(): Application[] {
  if (resolveMode() !== 'private') return [];
  const dir = applicationsDir();
  if (!existsSync(dir)) return [];

  return readdirSync(dir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && existsSync(join(dir, entry.name, 'application.yaml')))
    .map((entry) => ({
      slug: entry.name,
      // Windows editors can save UTF-8 with a byte-order mark, which js-yaml rejects.
      raw: loadYaml(
        readFileSync(join(dir, entry.name, 'application.yaml'), 'utf-8').replace(/^﻿/, ''),
      ) as RawApplication,
    }))
    .filter(({ raw }) => raw?.status === 'drafting')
    .map(({ slug, raw }) => build(slug, raw, readLetter(join(dir, slug))));
}
