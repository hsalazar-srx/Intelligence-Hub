#!/usr/bin/env python3
"""
IT Strategy Intelligence Hub — Static Site Builder (Python version)
Reads markdown files from /signals, /projects, /sources, /concepts
Generates filterable HTML site in /docs
"""

import os, re, yaml
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
DIRS = {
    'signals':  ROOT / 'signals',
    'projects': ROOT / 'projects',
    'sources':  ROOT / 'sources',
    'concepts': ROOT / 'concepts',
}
DOCS = ROOT / 'docs'
DOCS.mkdir(exist_ok=True)

PROJECT_META = {
    'digital-transformation': {'label': 'Digital Transformation', 'color': '#0ea5e9'},
    'ai-platform':            {'label': 'AI Platform',            'color': '#8b5cf6'},
    'm3-erp-integration':     {'label': 'M3 / ERP Integration',   'color': '#10b981'},
    'general':                {'label': 'General',                'color': '#6b7280'},
}
RELEVANCE_COLORS = {'high': '#ef4444', 'medium': '#f59e0b', 'low': '#6b7280'}

# ── Simple Markdown → HTML ────────────────────────────────────
def md_to_html(text):
    # Remove frontmatter
    text = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
    # Headers
    for i in range(6, 0, -1):
        text = re.sub(rf'^{"#"*i} (.+)$', rf'<h{i}>\1</h{i}>', text, flags=re.MULTILINE)
    # Bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Checkboxes
    text = re.sub(r'- \[x\] (.+)', r'<li><input type="checkbox" checked disabled> \1</li>', text)
    text = re.sub(r'- \[ \] (.+)', r'<li><input type="checkbox" disabled> \1</li>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    # Tables
    def table_replace(m):
        lines = [l.strip() for l in m.group(0).strip().split('\n') if l.strip() and not re.match(r'^\|[-| :]+\|$', l.strip())]
        rows = []
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            rows.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
        return '<table>' + ''.join(rows) + '</table>'
    text = re.sub(r'(\|.+\|\n)+', table_replace, text)
    # Unordered lists
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*</li>\n?)+', lambda m: '<ul>' + m.group(0) + '</ul>', text)
    # Code blocks
    text = re.sub(r'```[a-z]*\n(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
    # Paragraphs (simple)
    paras = re.split(r'\n\n+', text)
    result = []
    for p in paras:
        p = p.strip()
        if p and not p.startswith('<'):
            p = '<p>' + p.replace('\n', ' ') + '</p>'
        result.append(p)
    return '\n'.join(result)

# ── Read markdown dir ─────────────────────────────────────────
def read_dir(d):
    if not d.exists(): return []
    files = []
    for f in sorted(d.glob('*.md'), reverse=True):
        raw = f.read_text(encoding='utf-8')
        fm = {}
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw, re.DOTALL)
        if m:
            try: fm = yaml.safe_load(m.group(1)) or {}
            except: fm = {}
        html = md_to_html(raw)
        files.append({'filename': f.name, 'fm': fm, 'html': html})
    return files

def tag_badge(tag):
    p = PROJECT_META.get(tag, {'label': tag, 'color': '#6b7280'})
    return f'<span class="tag" style="background:{p["color"]}22;color:{p["color"]};border:1px solid {p["color"]}44">{p["label"]}</span>'

def relevance_badge(r):
    if not r: return ''
    color = RELEVANCE_COLORS.get(r, '#6b7280')
    return f'<span class="relevance" style="color:{color}">● {r.upper()}</span>'

def signal_card(s):
    fm = s['fm']
    project = fm.get('project', 'general')
    tags = fm.get('tags', [])
    title = fm.get('title', s['filename'].replace('.md','').replace('-',' ').title())
    tags_str = ','.join(str(t) for t in tags)
    extra_tags = [t for t in tags if str(t) != project]
    return f'''
<article class="signal-card" data-project="{project}" data-tags="{tags_str}" data-relevance="{fm.get('relevance','')}">
  <div class="card-header">
    <div class="card-meta">
      <span class="date">{fm.get('date','')}</span>
      {relevance_badge(fm.get('relevance',''))}
    </div>
    <div class="card-tags">
      {tag_badge(project)}
      {''.join(tag_badge(str(t)) for t in extra_tags)}
    </div>
  </div>
  <h3 class="card-title">{title}</h3>
  <div class="card-source">📡 {fm.get('source','Unknown source')}</div>
  <div class="card-content">{s['html']}</div>
</article>'''

# ── Load content ──────────────────────────────────────────────
signals  = read_dir(DIRS['signals'])
projects = read_dir(DIRS['projects'])
sources  = read_dir(DIRS['sources'])
concepts = read_dir(DIRS['concepts'])

filter_buttons = '<button class="filter-btn active" data-filter="all" style="--accent:#8b949e">All Signals</button>\n'
for k, v in PROJECT_META.items():
    filter_buttons += f'<button class="filter-btn" data-filter="{k}" style="--accent:{v["color"]}">{v["label"]}</button>\n'

signal_cards_html = '\n'.join(signal_card(s) for s in signals) if signals else '''
<div class="empty-state">
  <div class="empty-icon">📡</div>
  <h3>No signals yet</h3>
  <p>Add your first signal by creating a <code>.md</code> file in <code>/signals</code> using the Obsidian template.</p>
</div>'''

sources_html = '\n'.join(f'<div class="source-content">{s["html"]}</div>' for s in sources)
projects_html = '<hr style="border-color:var(--border);margin:2rem 0">'.join(f'<div>{p["html"]}</div>' for p in projects) if projects else '<div class="empty-state"><div class="empty-icon">🗂️</div><h3>No project pages yet</h3></div>'
concepts_html = '<hr style="border-color:var(--border);margin:2rem 0">'.join(f'<div>{c["html"]}</div>' for c in concepts) if concepts else '<div class="empty-state"><div class="empty-icon">💡</div><h3>No concept notes yet</h3></div>'
build_date = date.today().isoformat()

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IT Strategy — Intelligence Hub</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{
      --bg:#0d1117;--surface:#161b22;--border:#21262d;
      --text:#e6edf3;--muted:#8b949e;
      --font-sans:'IBM Plex Sans',sans-serif;
      --font-mono:'IBM Plex Mono',monospace;
    }}
    body{{font-family:var(--font-sans);background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}}
    .shell{{display:grid;grid-template-columns:240px 1fr;min-height:100vh}}
    .sidebar{{background:var(--surface);border-right:1px solid var(--border);padding:2rem 1.5rem;position:sticky;top:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column;gap:2rem}}
    .logo{{font-family:var(--font-mono);font-size:.75rem;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;border-bottom:1px solid var(--border);padding-bottom:1.5rem}}
    .logo strong{{display:block;font-size:1rem;color:var(--text);letter-spacing:.05em;margin-bottom:.25rem}}
    .nav-section h4{{font-family:var(--font-mono);font-size:.65rem;text-transform:uppercase;letter-spacing:.15em;color:var(--muted);margin-bottom:.75rem}}
    .nav-links{{display:flex;flex-direction:column;gap:.25rem}}
    .nav-link{{padding:.4rem .75rem;border-radius:6px;font-size:.875rem;color:var(--muted);cursor:pointer;transition:all .15s;border:none;background:none;text-align:left;width:100%}}
    .nav-link:hover,.nav-link.active{{background:var(--border);color:var(--text)}}
    .stats{{margin-top:auto;padding-top:1.5rem;border-top:1px solid var(--border)}}
    .stat{{display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:.75rem;color:var(--muted);padding:.2rem 0}}
    .stat span:last-child{{color:var(--text)}}
    .main{{padding:2.5rem 3rem;max-width:1100px}}
    .page{{display:none}}.page.active{{display:block}}
    .page-header{{margin-bottom:2.5rem;padding-bottom:1.5rem;border-bottom:1px solid var(--border)}}
    .page-header h1{{font-size:1.75rem;font-weight:600;letter-spacing:-.02em;margin-bottom:.5rem}}
    .page-header p{{color:var(--muted);font-size:.9rem}}
    .filters{{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:2rem;align-items:center}}
    .filters-label{{font-family:var(--font-mono);font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-right:.5rem}}
    .filter-btn{{padding:.35rem .9rem;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--muted);font-size:.8rem;cursor:pointer;transition:all .2s;font-family:var(--font-sans)}}
    .filter-btn:hover{{border-color:var(--accent,#8b949e);color:var(--text)}}
    .filter-btn.active{{background:color-mix(in srgb,var(--accent,#8b949e) 15%,transparent);border-color:var(--accent,#8b949e);color:var(--text)}}
    .search-bar{{display:flex;align-items:center;gap:.75rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.6rem 1rem;margin-bottom:1.5rem}}
    .search-bar input{{background:none;border:none;outline:none;color:var(--text);font-family:var(--font-sans);font-size:.9rem;width:100%}}
    .search-bar input::placeholder{{color:var(--muted)}}
    .signals-grid{{display:grid;gap:1rem}}
    .signal-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.5rem;transition:border-color .2s}}
    .signal-card:hover{{border-color:#30363d}}
    .card-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.75rem;gap:1rem}}
    .card-meta{{display:flex;align-items:center;gap:1rem}}
    .date{{font-family:var(--font-mono);font-size:.75rem;color:var(--muted)}}
    .relevance{{font-family:var(--font-mono);font-size:.7rem;font-weight:500;letter-spacing:.05em}}
    .card-tags{{display:flex;gap:.4rem;flex-wrap:wrap}}
    .tag{{padding:.2rem .6rem;border-radius:20px;font-size:.7rem;font-weight:500;letter-spacing:.03em;white-space:nowrap}}
    .card-title{{font-size:1rem;font-weight:600;margin-bottom:.35rem;letter-spacing:-.01em}}
    .card-source{{font-size:.8rem;color:var(--muted);margin-bottom:1rem;font-family:var(--font-mono)}}
    .card-content{{font-size:.875rem;color:#c9d1d9;line-height:1.7}}
    .card-content h2,.card-content h3{{font-size:.85rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin:1rem 0 .4rem;font-weight:600}}
    .card-content p{{margin-bottom:.5rem}}
    .card-content ul{{padding-left:1.2rem}}
    .card-content li{{margin-bottom:.25rem}}
    .card-content code{{background:#1f2937;padding:.1rem .3rem;border-radius:3px;font-family:var(--font-mono);font-size:.8rem}}
    .card-content pre{{background:#1f2937;padding:1rem;border-radius:6px;overflow-x:auto;margin:.75rem 0}}
    .card-content pre code{{background:none;padding:0}}
    .card-content table{{width:100%;border-collapse:collapse;font-size:.82rem;margin:.75rem 0}}
    .card-content th{{background:var(--bg);padding:.5rem .7rem;text-align:left;color:var(--muted);font-size:.75rem;text-transform:uppercase;border-bottom:1px solid var(--border)}}
    .card-content td{{padding:.6rem .7rem;border-bottom:1px solid var(--border);vertical-align:top}}
    .card-content a{{color:#0ea5e9;text-decoration:none}}
    .card-content a:hover{{text-decoration:underline}}
    .empty-state{{text-align:center;padding:4rem 2rem;color:var(--muted)}}
    .empty-icon{{font-size:3rem;margin-bottom:1rem}}
    .empty-state h3{{color:var(--text);margin-bottom:.5rem}}
    .empty-state code{{background:var(--surface);padding:.1rem .4rem;border-radius:4px;font-family:var(--font-mono);font-size:.85rem}}
    .content-page{{max-width:800px}}
    .content-page h1{{font-size:1.5rem;font-weight:600;margin-bottom:1rem;letter-spacing:-.02em}}
    .content-page h2{{font-size:1.1rem;margin:2rem 0 .75rem;color:var(--text);border-bottom:1px solid var(--border);padding-bottom:.5rem}}
    .content-page h3{{font-size:.95rem;margin:1.5rem 0 .5rem}}
    .content-page table{{width:100%;border-collapse:collapse;font-size:.85rem;margin-bottom:2rem}}
    .content-page th{{background:var(--surface);padding:.6rem .8rem;text-align:left;font-weight:600;color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--border)}}
    .content-page td{{padding:.7rem .8rem;border-bottom:1px solid var(--border);vertical-align:top;color:#c9d1d9}}
    .content-page tr:hover td{{background:var(--surface)}}
    .content-page a{{color:#0ea5e9;text-decoration:none}}
    .content-page a:hover{{text-decoration:underline}}
    .content-page p{{font-size:.875rem;color:#c9d1d9;margin-bottom:.75rem}}
    .content-page ul,.content-page ol{{padding-left:1.4rem;margin-bottom:1rem}}
    .content-page li{{font-size:.875rem;color:#c9d1d9;margin-bottom:.3rem}}
    .content-page code{{background:var(--surface);padding:.1rem .3rem;border-radius:3px;font-family:var(--font-mono);font-size:.82rem}}
    .content-page pre{{background:#1f2937;padding:1rem;border-radius:6px;overflow-x:auto;margin:.75rem 0}}
    .content-page pre code{{background:none}}
    .content-page strong{{color:var(--text)}}
    .source-content{{margin-bottom:3rem}}
    .build-info{{font-family:var(--font-mono);font-size:.7rem;color:var(--muted);margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border)}}
    .build-info a{{color:var(--muted)}}
    @media(max-width:768px){{.shell{{grid-template-columns:1fr}}.sidebar{{position:static;height:auto}}.main{{padding:1.5rem}}}}
  </style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="logo"><strong>IT Strategy</strong>Intelligence Hub</div>
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
      <h4>Jump to Project</h4>
      <div class="nav-links">
        <button class="nav-link" data-page="signals" data-filter="digital-transformation">Digital Transformation</button>
        <button class="nav-link" data-page="signals" data-filter="ai-platform">AI Platform</button>
        <button class="nav-link" data-page="signals" data-filter="m3-erp-integration">M3 / ERP</button>
      </div>
    </div>
    <div class="stats">
      <div class="stat"><span>Signals</span><span>{len(signals)}</span></div>
      <div class="stat"><span>Projects</span><span>{len(projects)}</span></div>
      <div class="stat"><span>Concepts</span><span>{len(concepts)}</span></div>
      <div class="stat"><span>Built</span><span>{build_date}</span></div>
    </div>
  </aside>
  <main class="main">
    <div class="page active" id="page-signals">
      <div class="page-header">
        <h1>📡 Signal Tracker</h1>
        <p>Curated insights filtered for manufacturing IT, ERP integration, and enterprise AI — tagged by project relevance.</p>
      </div>
      <div class="search-bar">
        <span>🔍</span>
        <input type="text" id="signal-search" placeholder="Search by keyword, source, or topic…">
      </div>
      <div class="filters">
        <span class="filters-label">Project</span>
        {filter_buttons}
      </div>
      <div class="signals-grid" id="signals-grid">
        {signal_cards_html}
      </div>
    </div>
    <div class="page" id="page-sources">
      <div class="page-header">
        <h1>📚 Sources & Accounts</h1>
        <p>Curated Twitter/X accounts and YouTube channels for AI/LLM research, system design, and enterprise AI.</p>
      </div>
      <div class="content-page">{sources_html}</div>
    </div>
    <div class="page" id="page-projects">
      <div class="page-header">
        <h1>🗂️ Projects</h1>
        <p>Active initiatives connected to the signal tracker via project tags.</p>
      </div>
      <div class="content-page">{projects_html}</div>
    </div>
    <div class="page" id="page-concepts">
      <div class="page-header">
        <h1>💡 Concepts</h1>
        <p>Evergreen technical patterns and frameworks for your AI platform work.</p>
      </div>
      <div class="content-page">{concepts_html}</div>
    </div>
    <div class="build-info">
      Auto-generated from markdown · Built {build_date} · Push to main → auto-deploys via GitHub Actions
    </div>
  </main>
</div>
<script>
  const navLinks = document.querySelectorAll('.nav-link');
  const pages = document.querySelectorAll('.page');
  function showPage(id) {{
    pages.forEach(p => p.classList.remove('active'));
    navLinks.forEach(l => l.classList.remove('active'));
    const t = document.getElementById('page-' + id);
    if (t) t.classList.add('active');
    navLinks.forEach(l => {{ if (l.dataset.page === id) l.classList.add('active'); }});
  }}
  navLinks.forEach(l => l.addEventListener('click', () => {{
    showPage(l.dataset.page);
    if (l.dataset.filter) setTimeout(() => {{
      const b = document.querySelector(`.filter-btn[data-filter="${{l.dataset.filter}}"]`);
      if (b) b.click();
    }}, 50);
  }}));
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.signal-card');
  let activeFilter = 'all', searchTerm = '';
  function applyFilters() {{
    cards.forEach(c => {{
      const proj = c.dataset.project || '', tags = c.dataset.tags || '', text = c.textContent.toLowerCase();
      const matchF = activeFilter === 'all' || proj === activeFilter || tags.includes(activeFilter);
      const matchS = !searchTerm || text.includes(searchTerm.toLowerCase());
      c.style.display = matchF && matchS ? 'block' : 'none';
    }});
  }}
  filterBtns.forEach(b => b.addEventListener('click', () => {{
    filterBtns.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    activeFilter = b.dataset.filter;
    applyFilters();
  }}));
  document.getElementById('signal-search').addEventListener('input', e => {{
    searchTerm = e.target.value;
    applyFilters();
  }});
</script>
</body>
</html>'''

(DOCS / 'index.html').write_text(HTML, encoding='utf-8')
print(f"✅ Site built → docs/index.html ({len(signals)} signals, {len(projects)} projects, {len(concepts)} concepts)")
