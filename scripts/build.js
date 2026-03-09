#!/usr/bin/env node
/**
 * IT Strategy Intelligence Hub — Static Site Builder
 * Reads all markdown files in /signals, /projects, /sources, /concepts
 * Generates a filterable, searchable HTML site in /docs
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { marked } = require('marked');

// ── Config ────────────────────────────────────────────────────
const ROOT = path.join(__dirname, '..');
const DOCS = path.join(ROOT, 'docs');
const DIRS = {
  signals:  path.join(ROOT, 'signals'),
  projects: path.join(ROOT, 'projects'),
  sources:  path.join(ROOT, 'sources'),
  concepts: path.join(ROOT, 'concepts'),
};

const PROJECT_LABELS = {
  'digital-transformation': { label: 'Digital Transformation', color: '#0ea5e9' },
  'ai-platform':            { label: 'AI Platform',            color: '#8b5cf6' },
  'm3-erp-integration':     { label: 'M3 / ERP Integration',   color: '#10b981' },
  'general':                { label: 'General',                color: '#6b7280' },
};

const RELEVANCE_COLORS = {
  high:   '#ef4444',
  medium: '#f59e0b',
  low:    '#6b7280',
};

// ── Helpers ───────────────────────────────────────────────────
function readMarkdownDir(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.md'))
    .map(f => {
      const raw = fs.readFileSync(path.join(dir, f), 'utf-8');
      const { data, content } = matter(raw);
      return { filename: f, frontmatter: data, content, html: marked(content) };
    })
    .sort((a, b) => {
      const da = a.frontmatter.date || '';
      const db = b.frontmatter.date || '';
      return db.localeCompare(da); // newest first
    });
}

function tagBadge(tag) {
  const p = PROJECT_LABELS[tag];
  const color = p ? p.color : '#6b7280';
  const label = p ? p.label : tag;
  return `<span class="tag" style="background:${color}22;color:${color};border:1px solid ${color}44">${label}</span>`;
}

function relevanceBadge(r) {
  const color = RELEVANCE_COLORS[r] || '#6b7280';
  return r ? `<span class="relevance" style="color:${color}">● ${r.toUpperCase()}</span>` : '';
}

function signalCard(s) {
  const f = s.frontmatter;
  const project = f.project || 'general';
  const tags = (f.tags || []).join(',');
  const title = f.title || s.filename.replace('.md','').replace(/-/g,' ');
  return `
<article class="signal-card" data-project="${project}" data-tags="${tags}" data-relevance="${f.relevance || ''}">
  <div class="card-header">
    <div class="card-meta">
      <span class="date">${f.date || ''}</span>
      ${relevanceBadge(f.relevance)}
    </div>
    <div class="card-tags">
      ${tagBadge(project)}
      ${(f.tags || []).filter(t => t !== project).map(tagBadge).join('')}
    </div>
  </div>
  <h3 class="card-title">${title}</h3>
  <div class="card-source">📡 ${f.source || 'Unknown source'}</div>
  <div class="card-content">${s.html}</div>
</article>`;
}

// ── Build ─────────────────────────────────────────────────────
if (!fs.existsSync(DOCS)) fs.mkdirSync(DOCS, { recursive: true });

const signals  = readMarkdownDir(DIRS.signals);
const projects = readMarkdownDir(DIRS.projects);
const sources  = readMarkdownDir(DIRS.sources);
const concepts = readMarkdownDir(DIRS.concepts);

const allProjects = [...new Set(signals.map(s => s.frontmatter.project || 'general'))];
const filterButtons = ['all', ...Object.keys(PROJECT_LABELS)]
  .map(p => {
    const info = PROJECT_LABELS[p];
    const label = p === 'all' ? 'All Signals' : (info ? info.label : p);
    const color = info ? info.color : '#6b7280';
    return `<button class="filter-btn ${p === 'all' ? 'active' : ''}" 
      data-filter="${p}" 
      style="--accent:${color}">${label}</button>`;
  }).join('');

const signalCards = signals.length > 0
  ? signals.map(signalCard).join('\n')
  : `<div class="empty-state">
      <div class="empty-icon">📡</div>
      <h3>No signals yet</h3>
      <p>Add your first signal by creating a <code>.md</code> file in the <code>/signals</code> folder using the Obsidian template.</p>
    </div>`;

const projectNav = projects.map(p => {
  const title = p.frontmatter.title || p.filename.replace('.md','').replace(/-/g,' ');
  return `<a href="#" class="project-link">${title}</a>`;
}).join('');

const sourcesList = sources.map(s => `<div class="source-content">${s.html}</div>`).join('');

const buildDate = new Date().toISOString().split('T')[0];

// ── HTML Template ─────────────────────────────────────────────
const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IT Strategy — Intelligence Hub</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:       #0d1117;
      --surface:  #161b22;
      --border:   #21262d;
      --text:     #e6edf3;
      --muted:    #8b949e;
      --accent-dt: #0ea5e9;
      --accent-ai: #8b5cf6;
      --accent-m3: #10b981;
      --font-sans: 'IBM Plex Sans', sans-serif;
      --font-mono: 'IBM Plex Mono', monospace;
    }

    body {
      font-family: var(--font-sans);
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      line-height: 1.6;
    }

    /* ── Layout ── */
    .shell { display: grid; grid-template-columns: 240px 1fr; min-height: 100vh; }

    /* ── Sidebar ── */
    .sidebar {
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 2rem 1.5rem;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }

    .logo {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--muted);
      letter-spacing: 0.15em;
      text-transform: uppercase;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.5rem;
    }
    .logo strong {
      display: block;
      font-size: 1rem;
      color: var(--text);
      letter-spacing: 0.05em;
      margin-bottom: 0.25rem;
    }

    .nav-section h4 {
      font-family: var(--font-mono);
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--muted);
      margin-bottom: 0.75rem;
    }

    .nav-links { display: flex; flex-direction: column; gap: 0.25rem; }
    .nav-link {
      padding: 0.4rem 0.75rem;
      border-radius: 6px;
      font-size: 0.875rem;
      color: var(--muted);
      cursor: pointer;
      transition: all 0.15s;
      border: none;
      background: none;
      text-align: left;
      width: 100%;
    }
    .nav-link:hover, .nav-link.active {
      background: var(--border);
      color: var(--text);
    }

    .stats {
      margin-top: auto;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
    }
    .stat {
      display: flex;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--muted);
      padding: 0.2rem 0;
    }
    .stat span:last-child { color: var(--text); }

    /* ── Main ── */
    .main { padding: 2.5rem 3rem; max-width: 1100px; }

    .page { display: none; }
    .page.active { display: block; }

    /* ── Page header ── */
    .page-header {
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    .page-header h1 {
      font-size: 1.75rem;
      font-weight: 600;
      letter-spacing: -0.02em;
      margin-bottom: 0.5rem;
    }
    .page-header p { color: var(--muted); font-size: 0.9rem; }

    /* ── Filters ── */
    .filters {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-bottom: 2rem;
      align-items: center;
    }
    .filters-label {
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-right: 0.5rem;
    }
    .filter-btn {
      padding: 0.35rem 0.9rem;
      border-radius: 20px;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--muted);
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.2s;
      font-family: var(--font-sans);
    }
    .filter-btn:hover {
      border-color: var(--accent, #8b949e);
      color: var(--text);
    }
    .filter-btn.active {
      background: color-mix(in srgb, var(--accent, #8b949e) 15%, transparent);
      border-color: var(--accent, #8b949e);
      color: var(--text);
    }

    /* ── Search ── */
    .search-bar {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.6rem 1rem;
      margin-bottom: 1.5rem;
    }
    .search-bar input {
      background: none;
      border: none;
      outline: none;
      color: var(--text);
      font-family: var(--font-sans);
      font-size: 0.9rem;
      width: 100%;
    }
    .search-bar input::placeholder { color: var(--muted); }
    .search-icon { color: var(--muted); font-size: 0.9rem; }

    /* ── Signal Cards ── */
    .signals-grid {
      display: grid;
      gap: 1rem;
    }

    .signal-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.5rem;
      transition: border-color 0.2s;
    }
    .signal-card:hover { border-color: #30363d; }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
      gap: 1rem;
    }
    .card-meta {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .date {
      font-family: var(--font-mono);
      font-size: 0.75rem;
      color: var(--muted);
    }
    .relevance {
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.05em;
    }
    .card-tags { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .tag {
      padding: 0.2rem 0.6rem;
      border-radius: 20px;
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.03em;
      white-space: nowrap;
    }

    .card-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.35rem;
      letter-spacing: -0.01em;
    }
    .card-source {
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 1rem;
      font-family: var(--font-mono);
    }
    .card-content {
      font-size: 0.875rem;
      color: #c9d1d9;
      line-height: 1.7;
    }
    .card-content h2, .card-content h3 {
      font-size: 0.85rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin: 1rem 0 0.4rem;
      font-weight: 600;
    }
    .card-content p { margin-bottom: 0.5rem; }
    .card-content ul { padding-left: 1.2rem; }
    .card-content li { margin-bottom: 0.25rem; }
    .card-content code {
      background: #1f2937;
      padding: 0.1rem 0.3rem;
      border-radius: 3px;
      font-family: var(--font-mono);
      font-size: 0.8rem;
    }
    .card-content input[type="checkbox"] { margin-right: 0.4rem; }

    /* ── Empty state ── */
    .empty-state {
      text-align: center;
      padding: 4rem 2rem;
      color: var(--muted);
    }
    .empty-icon { font-size: 3rem; margin-bottom: 1rem; }
    .empty-state h3 { color: var(--text); margin-bottom: 0.5rem; }
    .empty-state code {
      background: var(--surface);
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 0.85rem;
    }

    /* ── Sources / Concepts pages ── */
    .content-page { max-width: 800px; }
    .content-page h2 {
      font-size: 1.1rem;
      margin: 2rem 0 0.75rem;
      color: var(--text);
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.5rem;
    }
    .content-page table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      margin-bottom: 2rem;
    }
    .content-page th {
      background: var(--surface);
      padding: 0.6rem 0.8rem;
      text-align: left;
      font-weight: 600;
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      border-bottom: 1px solid var(--border);
    }
    .content-page td {
      padding: 0.7rem 0.8rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
      color: #c9d1d9;
    }
    .content-page tr:hover td { background: var(--surface); }
    .content-page a { color: var(--accent-dt); text-decoration: none; }
    .content-page a:hover { text-decoration: underline; }
    .content-page p { font-size: 0.875rem; color: #c9d1d9; margin-bottom: 0.75rem; }
    .content-page ul { padding-left: 1.2rem; margin-bottom: 1rem; }
    .content-page li { font-size: 0.875rem; color: #c9d1d9; margin-bottom: 0.3rem; }
    .content-page h3 { font-size: 0.95rem; margin: 1.5rem 0 0.5rem; }

    /* ── Build info ── */
    .build-info {
      font-family: var(--font-mono);
      font-size: 0.7rem;
      color: var(--muted);
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
      .shell { grid-template-columns: 1fr; }
      .sidebar { position: static; height: auto; }
      .main { padding: 1.5rem; }
    }
  </style>
</head>
<body>

<div class="shell">

  <!-- ── Sidebar ── -->
  <aside class="sidebar">
    <div class="logo">
      <strong>IT Strategy</strong>
      Intelligence Hub
    </div>

    <nav class="nav-section">
      <h4>Navigation</h4>
      <div class="nav-links">
        <button class="nav-link active" data-page="signals">📡 Signal Tracker</button>
        <button class="nav-link" data-page="sources">📚 Sources & Accounts</button>
        <button class="nav-link" data-page="projects">🗂️ Projects</button>
        <button class="nav-link" data-page="concepts">💡 Concepts</button>
      </div>
    </nav>

    <div class="nav-section">
      <h4>Projects</h4>
      <div class="nav-links">
        <button class="nav-link" data-page="signals" data-filter="digital-transformation">Digital Transformation</button>
        <button class="nav-link" data-page="signals" data-filter="ai-platform">AI Platform</button>
        <button class="nav-link" data-page="signals" data-filter="m3-erp-integration">M3 / ERP Integration</button>
      </div>
    </div>

    <div class="stats">
      <div class="stat"><span>Signals</span><span>${signals.length}</span></div>
      <div class="stat"><span>Projects</span><span>${projects.length}</span></div>
      <div class="stat"><span>Concepts</span><span>${concepts.length}</span></div>
      <div class="stat"><span>Built</span><span>${buildDate}</span></div>
    </div>
  </aside>

  <!-- ── Main Content ── -->
  <main class="main">

    <!-- SIGNALS PAGE -->
    <div class="page active" id="page-signals">
      <div class="page-header">
        <h1>📡 Signal Tracker</h1>
        <p>Curated insights filtered for manufacturing IT, ERP integration, and enterprise AI — tagged by project relevance.</p>
      </div>

      <div class="search-bar">
        <span class="search-icon">🔍</span>
        <input type="text" id="signal-search" placeholder="Search signals by keyword, source, or topic…">
      </div>

      <div class="filters">
        <span class="filters-label">Project</span>
        ${filterButtons}
      </div>

      <div class="signals-grid" id="signals-grid">
        ${signalCards}
      </div>
    </div>

    <!-- SOURCES PAGE -->
    <div class="page" id="page-sources">
      <div class="page-header">
        <h1>📚 Sources & Accounts</h1>
        <p>Curated Twitter/X accounts and YouTube channels relevant to AI/LLM research, system design, and enterprise AI.</p>
      </div>
      <div class="content-page">
        ${sourcesList}
      </div>
    </div>

    <!-- PROJECTS PAGE -->
    <div class="page" id="page-projects">
      <div class="page-header">
        <h1>🗂️ Projects</h1>
        <p>Active initiatives. Each page connects to relevant signals via project tags.</p>
      </div>
      <div class="content-page">
        ${projects.map(p => `<div>${p.html}</div>`).join('<hr style="border-color:var(--border);margin:2rem 0">')}
        ${projects.length === 0 ? '<div class="empty-state"><div class="empty-icon">🗂️</div><h3>No project pages yet</h3><p>Add <code>.md</code> files to the <code>/projects</code> folder.</p></div>' : ''}
      </div>
    </div>

    <!-- CONCEPTS PAGE -->
    <div class="page" id="page-concepts">
      <div class="page-header">
        <h1>💡 Concepts</h1>
        <p>Evergreen notes on technical patterns, architectures, and frameworks relevant to your AI platform work.</p>
      </div>
      <div class="content-page">
        ${concepts.map(c => `<div>${c.html}</div>`).join('<hr style="border-color:var(--border);margin:2rem 0">')}
        ${concepts.length === 0 ? '<div class="empty-state"><div class="empty-icon">💡</div><h3>No concept notes yet</h3><p>Add <code>.md</code> files to the <code>/concepts</code> folder.</p></div>' : ''}
      </div>
    </div>

    <div class="build-info">
      Auto-generated from markdown — last built ${buildDate} · <a href="https://github.com" style="color:inherit">View source on GitHub</a>
    </div>

  </main>
</div>

<script>
  // ── Navigation ────────────────────────────────────────────
  const navLinks = document.querySelectorAll('.nav-link');
  const pages = document.querySelectorAll('.page');

  function showPage(pageId) {
    pages.forEach(p => p.classList.remove('active'));
    navLinks.forEach(l => l.classList.remove('active'));
    const target = document.getElementById('page-' + pageId);
    if (target) target.classList.add('active');
    navLinks.forEach(l => { if (l.dataset.page === pageId) l.classList.add('active'); });
  }

  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      showPage(link.dataset.page);
      if (link.dataset.filter) {
        setTimeout(() => {
          const btn = document.querySelector(\`.filter-btn[data-filter="\${link.dataset.filter}"]\`);
          if (btn) btn.click();
        }, 50);
      }
    });
  });

  // ── Signal Filtering ──────────────────────────────────────
  const filterBtns = document.querySelectorAll('.filter-btn');
  const signalCards = document.querySelectorAll('.signal-card');
  let activeFilter = 'all';
  let searchTerm = '';

  function applyFilters() {
    signalCards.forEach(card => {
      const project = card.dataset.project || '';
      const tags = card.dataset.tags || '';
      const text = card.textContent.toLowerCase();

      const matchesFilter = activeFilter === 'all' || project === activeFilter || tags.includes(activeFilter);
      const matchesSearch = searchTerm === '' || text.includes(searchTerm.toLowerCase());

      card.style.display = matchesFilter && matchesSearch ? 'block' : 'none';
    });
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.dataset.filter;
      applyFilters();
    });
  });

  document.getElementById('signal-search').addEventListener('input', e => {
    searchTerm = e.target.value;
    applyFilters();
  });
</script>

</body>
</html>`;

fs.writeFileSync(path.join(DOCS, 'index.html'), html, 'utf-8');
console.log(`✅ Site built → docs/index.html (${signals.length} signals, ${projects.length} projects)`);
