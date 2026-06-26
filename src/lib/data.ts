import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import Papa from 'papaparse';

const DATA_DIR = join(process.cwd(), 'data');

export type LensKey = 'all' | 'business' | 'data';
export type Proficiency = 'Expert' | 'Proficient' | 'Familiar';

export interface Config {
  name: string;
  tagline: string;
  location: string;
  email: string;
  phone: string;
  linkedin: string;
  linkedin_url: string;
  github: string;
  github_url: string;
  publish_lens: LensKey;
  earlier: string;
}

export interface CvView {
  lens: LensKey;
  profile: string;
  roles: Role[];
  projects: Project[];
  skillDomains: SkillDomain[];
}

export interface Persona {
  key: LensKey;
  label: string;
  description: string;
  profile: string;
}

export interface RoleBullet {
  order: number;
  text: string;
  personas: string[];
}

export interface Role {
  roleId: string;
  title: string;
  company: string;
  location: string;
  start: string;
  end: string;
  clients: string;
  summary: string;
  personas: string[];
  bullets: RoleBullet[];
}

export interface Project {
  projectId: string;
  client: string;
  title: string;
  summary: string;
  systems: string[];
  personas: string[];
  featured: boolean;
}

export interface Skill {
  skillId: string;
  domain: string;
  category: string;
  skill: string;
  description: string;
  proficiency: Proficiency;
  personas: string[];
  featured: boolean;
}

export interface SkillDomain {
  domain: string;
  categories: {
    category: string;
    skills: Skill[];
  }[];
}

function readCsv(filename: string): Record<string, string>[] {
  const raw = readFileSync(join(DATA_DIR, filename), 'utf-8');
  const { data } = Papa.parse<Record<string, string>>(raw, {
    header: true,
    skipEmptyLines: true,
  });
  return data;
}

function isVisible(value: string | undefined): boolean {
  return value?.toUpperCase() === 'TRUE';
}

export function parsePersonas(raw: string | undefined): string[] {
  if (!raw?.trim()) return [];
  return raw.split('|').map((p) => p.trim()).filter(Boolean);
}

export function matchesLens(lens: LensKey, personas: string[]): boolean {
  if (lens === 'all') return true;
  if (!personas.length) return false;
  return personas.includes(lens);
}

export function proficiencySegments(proficiency: Proficiency): number {
  switch (proficiency) {
    case 'Expert':
      return 3;
    case 'Proficient':
      return 2;
    case 'Familiar':
      return 1;
  }
}

function loadConfig(): Config {
  const rows = readCsv('config.csv');
  const map = Object.fromEntries(rows.map((r) => [r.key, r.value]));
  return {
    name: map.name ?? '',
    tagline: map.tagline ?? '',
    location: map.location ?? '',
    email: map.email ?? '',
    phone: map.phone ?? '',
    linkedin: map.linkedin ?? '',
    linkedin_url: map.linkedin_url ?? '',
    github: map.github ?? '',
    github_url: map.github_url ?? '',
    publish_lens: ((map.publish_lens ?? map.default_lens) as LensKey) ?? 'all',
    earlier: map.earlier ?? '',
  };
}

const LENS_KEYS: LensKey[] = ['all', 'business', 'data'];

export function resolveBuildLens(configPublishLens: LensKey): LensKey {
  const fromEnv = process.env.CV_LENS as LensKey | undefined;
  if (fromEnv && LENS_KEYS.includes(fromEnv)) return fromEnv;
  return configPublishLens;
}

function profileForLens(lens: LensKey, personaList: Persona[]): string {
  const persona = personaList.find((p) => p.key === lens) ?? personaList.find((p) => p.key === 'all');
  return persona?.profile ?? '';
}

function filterRolesForLens(lens: LensKey, roleList: Role[]): Role[] {
  return roleList
    .filter((role) => matchesLens(lens, role.personas))
    .map((role) => ({
      ...role,
      bullets: role.bullets.filter((bullet) => matchesLens(lens, bullet.personas)),
    }));
}

function filterSkillDomainsForLens(lens: LensKey, domains: SkillDomain[]): SkillDomain[] {
  return domains
    .map((domain) => ({
      domain: domain.domain,
      categories: domain.categories
        .map((cat) => ({
          category: cat.category,
          skills: cat.skills.filter((skill) => matchesLens(lens, skill.personas)),
        }))
        .filter((cat) => cat.skills.length > 0),
    }))
    .filter((domain) => domain.categories.length > 0);
}

export function buildCvView(lens: LensKey, personaList: Persona[], roleList: Role[], projectList: Project[], domains: SkillDomain[]): CvView {
  return {
    lens,
    profile: profileForLens(lens, personaList),
    roles: filterRolesForLens(lens, roleList),
    projects: projectList.filter((project) => matchesLens(lens, project.personas)),
    skillDomains: filterSkillDomainsForLens(lens, domains),
  };
}

function loadPersonas(): Persona[] {
  return readCsv('personas.csv').map((row) => ({
    key: row.key as LensKey,
    label: row.label,
    description: row.description,
    profile: row.profile,
  }));
}

function loadRoleBullets(): Map<string, RoleBullet[]> {
  const byRole = new Map<string, RoleBullet[]>();
  for (const row of readCsv('role_bullets.csv')) {
    if (!isVisible(row.visible)) continue;
    const bullet: RoleBullet = {
      order: Number(row.order),
      text: row.text,
      personas: parsePersonas(row.personas),
    };
    const list = byRole.get(row.role_id) ?? [];
    list.push(bullet);
    byRole.set(row.role_id, list);
  }
  for (const bullets of byRole.values()) {
    bullets.sort((a, b) => a.order - b.order);
  }
  return byRole;
}

function loadRoles(bulletsByRole: Map<string, RoleBullet[]>): Role[] {
  return readCsv('roles.csv')
    .filter((row) => isVisible(row.visible))
    .map((row) => ({
      roleId: row.role_id,
      title: row.title,
      company: row.company,
      location: row.location,
      start: row.start,
      end: row.end,
      clients: row.clients ?? '',
      summary: row.summary,
      personas: parsePersonas(row.personas),
      bullets: bulletsByRole.get(row.role_id) ?? [],
    }));
}

function loadProjects(): Project[] {
  return readCsv('projects.csv')
    .filter((row) => isVisible(row.visible))
    .map((row) => ({
      projectId: row.project_id,
      client: row.client,
      title: row.title,
      summary: row.summary,
      systems: row.systems ? row.systems.split('|').map((s) => s.trim()) : [],
      personas: parsePersonas(row.personas),
      featured: row.featured?.toUpperCase() === 'TRUE',
    }));
}

function loadSkills(): Skill[] {
  return readCsv('skills.csv')
    .filter((row) => isVisible(row.visible))
    .map((row) => ({
      skillId: row.skill_id,
      domain: row.domain,
      category: row.category,
      skill: row.skill,
      description: row.description,
      proficiency: row.proficiency as Proficiency,
      personas: parsePersonas(row.personas),
      featured: row.featured?.toUpperCase() === 'Y',
    }));
}

export function groupSkills(skills: Skill[]): SkillDomain[] {
  const domainMap = new Map<string, Map<string, Skill[]>>();
  for (const skill of skills) {
    if (!domainMap.has(skill.domain)) domainMap.set(skill.domain, new Map());
    const catMap = domainMap.get(skill.domain)!;
    if (!catMap.has(skill.category)) catMap.set(skill.category, []);
    catMap.get(skill.category)!.push(skill);
  }
  return [...domainMap.entries()].map(([domain, catMap]) => ({
    domain,
    categories: [...catMap.entries()].map(([category, items]) => ({
      category,
      skills: items,
    })),
  }));
}

const bulletsByRole = loadRoleBullets();

export const config = loadConfig();
export const personas = loadPersonas();
export const roles = loadRoles(bulletsByRole);
export const projects = loadProjects();
export const skills = loadSkills();
export const skillDomains = groupSkills(skills);
export const buildLens = resolveBuildLens(config.publish_lens);
export const cv = buildCvView(buildLens, personas, roles, projects, skillDomains);
