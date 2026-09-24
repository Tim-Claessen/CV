/**
 * In-page editing for an application CV, active only at /apply/<slug>?edit=1.
 *
 * Text only. Each editable node is tagged with the path of the value it shows in
 * application.yaml, and Save posts those paths to the local edit server, which
 * writes them back into the record and rebuilds. Nothing here changes layout,
 * and nothing is kept in the browser: the record is the only copy.
 *
 * Without the edit server (a plain private build, or the deployed site, which
 * has no /apply routes at all) the toolbar says so and refuses, rather than
 * letting edits pile up in a page that cannot keep them.
 */
type Path = (string | number)[];
interface Edit { path: Path; value: string; index?: number }

const params = new URLSearchParams(location.search);
if (params.get('edit') === '1') setup();

function setup(): void {
  const raw = document.getElementById('edit-map')?.textContent;
  if (!raw) return;
  const map = JSON.parse(raw) as { slug: string; roles: string[]; projects: number };

  const originals = new Map<HTMLElement, string>();

  const mark = (node: Element | null, path: Path, index?: number): void => {
    if (!(node instanceof HTMLElement)) return;
    node.contentEditable = 'true';
    node.spellcheck = true;
    node.dataset.path = JSON.stringify(path);
    if (index !== undefined) node.dataset.index = String(index);
    node.classList.add('is-editable');
    originals.set(node, node.innerText.trim());
  };

  mark(document.querySelector('.tagline'), ['tagline']);
  mark(document.querySelector('.profile'), ['profile']);

  document.querySelectorAll('.role').forEach((role, i) => {
    const name = map.roles[i];
    if (name === undefined) return;
    mark(role.querySelector('.role-summary'), ['roles', name, 'summary']);
    role.querySelectorAll('.role-bullets li').forEach((li, b) => {
      mark(li, ['roles', name, 'bullets', b, 'text']);
    });
  });

  document.querySelectorAll('.project-card').forEach((card, i) => {
    mark(card.querySelector('.project-client'), ['projects', i, 'client']);
    mark(card.querySelector('.project-title'), ['projects', i, 'title']);
    mark(card.querySelector('.project-desc'), ['projects', i, 'summary']);
    card.querySelectorAll('.stack-chip').forEach((chip, c) => {
      mark(chip, ['projects', i, 'technologies'], c);
    });
  });

  const bar = document.createElement('div');
  bar.className = 'edit-bar no-print';
  bar.innerHTML =
    '<span class="edit-hint">Editing text. Headings, dates and capabilities are fixed.</span>' +
    '<span class="edit-status" role="status"></span>' +
    '<button type="button" data-act="revert">Revert</button>' +
    '<button type="button" data-act="save">Save</button>' +
    '<button type="button" data-act="export">Save and PDF</button>';
  document.body.appendChild(bar);

  const status = bar.querySelector('.edit-status') as HTMLElement;
  const say = (text: string, tone = ''): void => {
    status.textContent = text;
    status.dataset.tone = tone;
  };

  const changed = (): Edit[] =>
    [...originals.entries()]
      .filter(([node, was]) => node.innerText.trim() !== was)
      .map(([node]) => ({
        path: JSON.parse(node.dataset.path as string) as Path,
        value: node.innerText.trim(),
        ...(node.dataset.index ? { index: Number(node.dataset.index) } : {}),
      }));

  const post = async (route: string, body: unknown): Promise<any> => {
    const response = await fetch(route, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error ?? String(response.status));
    return data;
  };

  const save = async (thenExport: boolean): Promise<void> => {
    const edits = changed();
    if (edits.length === 0 && !thenExport) {
      say('nothing changed');
      return;
    }
    say(edits.length ? `saving ${edits.length}...` : 'exporting...');
    try {
      if (edits.length) await post('/api/save', { slug: map.slug, edits });
      if (thenExport) {
        const result = await post('/api/export', { slug: map.slug });
        say(`saved. PDF is ${result.pages} pages`, result.pages === 2 ? 'ok' : 'bad');
        return;
      }
      say('saved, reloading...', 'ok');
      location.reload();
    } catch (error) {
      say(`not saved: ${(error as Error).message}. Is the edit server running?`, 'bad');
    }
  };

  bar.addEventListener('click', (event) => {
    const act = (event.target as HTMLElement).closest('button')?.dataset.act;
    if (act === 'save') void save(false);
    if (act === 'export') void save(true);
    if (act === 'revert') location.reload();
  });

  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
      event.preventDefault();
      void save(false);
    }
  });

  // A pasted paragraph brings its own markup; the record holds plain text.
  document.addEventListener('paste', (event) => {
    const target = event.target as HTMLElement;
    if (!target.isContentEditable) return;
    event.preventDefault();
    const text = event.clipboardData?.getData('text/plain') ?? '';
    document.execCommand('insertText', false, text.replace(/\s+/g, ' '));
  });

  window.addEventListener('beforeunload', (event) => {
    if (changed().length > 0) event.preventDefault();
  });
}
