#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  IT-Strategy Intelligence Hub — One-time Setup
#  Run once after cloning: bash setup.sh
# ─────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Setting up IT Strategy Intelligence Hub..."

# 1. Install pre-commit hook
echo ""
echo "🔐 Installing sensitive data pre-commit hook..."
cp .github/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo -e "${GREEN}✅ Pre-commit hook installed${NC}"

# 2. Install node dependencies
echo ""
echo "📦 Installing build dependencies..."
npm install
echo -e "${GREEN}✅ Dependencies installed${NC}"

# 3. Build site locally
echo ""
echo "🏗️  Building site..."
npm run build
echo -e "${GREEN}✅ Site built → open docs/index.html to preview${NC}"

# 4. Obsidian template reminder
echo ""
echo -e "${YELLOW}📝 Obsidian setup:${NC}"
echo "   1. Open this folder as your Obsidian vault"
echo "   2. Go to Settings → Core Plugins → Enable 'Templates'"
echo "   3. Set template folder to: .obsidian/templates"
echo "   4. Use Cmd/Ctrl+P → 'Insert Template' → signal-entry"
echo "      to create new signals with the correct structure"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup complete!                      ║${NC}"
echo -e "${GREEN}║  Push to main → GitHub Actions builds ║${NC}"
echo -e "${GREEN}║  and deploys to GitHub Pages auto.    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Create GitHub repo: it-strategy"  
echo "  2. Enable GitHub Pages in repo Settings → Pages → Source: GitHub Actions"
echo "  3. git push origin main"
echo "  4. Share the Pages URL in your Teams channel"
