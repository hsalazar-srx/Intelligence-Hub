# IT Strategy — Intelligence Hub

> A living signal tracker and curated resource list for the IT/Digital Transformation team.
> Focused on enterprise AI, MES modernization, M3/ERP integration, and AI platform strategy.

**🌐 Live site:** `https://[your-github-username].github.io/it-strategy`  
**🔒 Security:** Pre-commit hook + GitHub Actions scan on every push

---

## 🗂️ Repository Structure

```
it-strategy/
│
├── 📁 signals/          ← Captured insights (one .md per signal)
├── 📁 sources/          ← Curated accounts, channels, newsletters
├── 📁 projects/         ← Active project pages (MES, AI Platform, M3)
├── 📁 concepts/         ← Evergreen technical concept notes
│
├── 📁 docs/             ← Auto-generated GitHub Pages site (don't edit manually)
├── 📁 scripts/          ← build.js — site generator
├── 📁 .obsidian/        ← Obsidian vault config + templates
│   └── templates/
│       └── signal-entry.md  ← Use this for every new signal
│
├── 📁 .github/
│   ├── workflows/deploy.yml  ← Scan + Build + Deploy pipeline
│   └── hooks/pre-commit      ← Local sensitive data guard
│
├── setup.sh             ← Run once after cloning
└── .gitignore           ← Protects secrets, .env, private drafts
```

---

## 🚀 Getting Started

### 1. Clone and setup
```bash
git clone https://github.com/[your-username]/it-strategy.git
cd it-strategy
bash setup.sh
```

### 2. Enable GitHub Pages
- Go to your GitHub repo → **Settings → Pages**
- Source: **GitHub Actions**
- Push to `main` → site auto-deploys

### 3. Share with colleagues
- Add the GitHub Pages URL as a tab in your Teams channel
- Or embed in a SharePoint page using the **Embed** web part

---

## 📡 Adding a New Signal (Your Daily Workflow)

**In Obsidian:**
1. `Cmd/Ctrl + P` → "Create new note from template" → `signal-entry`
2. Name the file: `YYYY-MM-DD-short-title` (e.g., `2026-03-15-rag-for-mes-data`)
3. Fill in the frontmatter and sections
4. Save to `/signals/`

**Publish:**
```bash
git add signals/
git commit -m "signal: [brief description]"
git push origin main
# → GitHub Actions builds and deploys automatically (~2 min)
```

---

## 🔐 Security Rules

### What's blocked automatically

| Check | Where | Blocks |
|-------|-------|--------|
| Credential patterns (passwords, tokens, API keys) | Pre-commit hook + CI | Commit |
| Private IP addresses (10.x, 192.168.x) | Pre-commit hook + CI | Commit |
| Database connection strings | Pre-commit hook + CI | Commit |
| `.env` files | .gitignore + CI | Push |
| Private key files (.pem, .key, etc.) | .gitignore + CI | Push |

### What you control

Add your org's specific sensitive terms to the pre-commit hook:
```bash
# .github/hooks/pre-commit → ORG_KEYWORDS array
ORG_KEYWORDS=(
  'YourCompanyName'
  'PROD_SERVER_NAME'
  # add more as needed
)
```

### Private drafts
Prefix any file with `_` to keep it local-only (it's in `.gitignore`):
```
signals/_draft-sensitive-project.md  ← never committed
```

---

## 🏷️ Project Tags

| Tag | Use for |
|-----|---------|
| `digital-transformation` | MES modernization, org change, process digitization |
| `ai-platform` | LLM research, RAG, ML patterns, AI platform architecture |
| `m3-erp-integration` | Infor M3, ERP integration patterns, data contracts |
| `general` | Relevant but not project-specific |

---

## 👥 For Colleagues

You don't need GitHub access to read the intelligence hub — just visit the GitHub Pages URL.

If you want to **contribute signals:**
1. Clone the repo
2. Run `bash setup.sh`
3. Follow the "Adding a New Signal" workflow above
4. Submit a Pull Request — it will be reviewed before merging

---

## 🔄 Update Log

| Date | Update | By |
|------|--------|----|
| 2026-03-09 | Initial setup — signal tracker, 3 projects, curated sources | Hector |
