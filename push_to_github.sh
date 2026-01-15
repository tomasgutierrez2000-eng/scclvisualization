#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Push to GitHub - Step by Step"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /Users/tomas

# Check if git repo
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Initializing..."
    git init
    git branch -M main
fi

# Add important files
echo "📝 Adding files..."
git add index.html 2>/dev/null
git add sccl_unified_view.py 2>/dev/null
git add integrate_excel_data_complete_catalog.py 2>/dev/null
git add integrate_excel_data_corrected.py 2>/dev/null
git add validate_data.py 2>/dev/null
git add diagnose_mdrm_connections.py 2>/dev/null
git add README.md 2>/dev/null
git add *.md 2>/dev/null
git add *.sh 2>/dev/null

# Check what's staged
echo ""
echo "📋 Files staged:"
git status --short | grep "^A\|^M" | head -20

# Commit if there are changes
if [ -n "$(git status --porcelain | grep '^A\|^M')" ]; then
    echo ""
    echo "💾 Committing changes..."
    git commit -m "Add SCCL visualization files and documentation"
fi

# Set remote
echo ""
echo "🔗 Setting up remote..."
git remote remove origin 2>/dev/null
git remote add origin https://github.com/tomasgutierrez2000-eng/scclvisualization.git

# Check current branch
git branch -M main 2>/dev/null

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Ready to Push!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Now run this command:"
echo ""
echo "  git push -u origin main"
echo ""
echo "When prompted:"
echo "  Username: tomasgutierrez2000-eng"
echo "  Password: [Your Personal Access Token]"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔑 Need a token?"
echo "   → https://github.com/settings/tokens/new"
echo "   → Name: 'SCCL Visualization'"
echo "   → Check: repo (full control)"
echo "   → Generate and copy token"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Push now? (y/n): " push_now

if [ "$push_now" = "y" ]; then
    echo ""
    echo "🚀 Pushing to GitHub..."
    git push -u origin main
    echo ""
    echo "✅ Done! Check: https://github.com/tomasgutierrez2000-eng/scclvisualization"
    echo ""
    echo "Next: Enable GitHub Pages at:"
    echo "  https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages"
else
    echo ""
    echo "Run 'git push -u origin main' when ready!"
fi
