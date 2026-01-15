#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 GitHub Pages Deployment Helper"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if file exists
if [ ! -f "_unified_view.html" ] && [ ! -f "sccl_unified_view.html" ]; then
    echo "❌ Error: Visualization file not found"
    echo "   Looking for: _unified_view.html or sccl_unified_view.html"
    exit 1
fi

# Determine which file to use
if [ -f "_unified_view.html" ]; then
    SOURCE_FILE="_unified_view.html"
elif [ -f "sccl_unified_view.html" ]; then
    SOURCE_FILE="sccl_unified_view.html"
fi

# Prepare index.html
echo "📝 Preparing index.html..."
cp "$SOURCE_FILE" index.html
echo "✅ Created index.html"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  📋 MANUAL STEPS (5 minutes):"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Go to: https://github.com/new"
echo "   (Create account if needed: https://github.com/signup)"
echo ""
echo "2. Create new repository:"
echo "   • Name: sccl-lineage (or anything you want)"
echo "   • Make it PUBLIC"
echo "   • Check 'Add a README file'"
echo "   • Click 'Create repository'"
echo ""
echo "3. Upload index.html:"
echo "   • Click 'Add file' → 'Upload files'"
echo "   • Drag index.html from this folder"
echo "   • Click 'Commit changes'"
echo ""
echo "4. Enable GitHub Pages:"
echo "   • Go to: Settings → Pages (left sidebar)"
echo "   • Source: Select 'main' branch"
echo "   • Folder: Select '/ (root)'"
echo "   • Click 'Save'"
echo ""
echo "5. Wait 1-2 minutes, then visit:"
echo "   https://yourusername.github.io/sccl-lineage/"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if git is available
if command -v git &> /dev/null; then
    echo "💡 TIP: If you have git installed, you can also:"
    echo ""
    echo "   git init"
    echo "   git add index.html"
    echo "   git commit -m 'Initial commit'"
    echo "   git branch -M main"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/sccl-lineage.git"
    echo "   git push -u origin main"
    echo ""
    echo "   Then enable Pages in Settings → Pages"
    echo ""
fi

echo "Opening GitHub in browser..."
sleep 1
open "https://github.com/new" 2>/dev/null || xdg-open "https://github.com/new" 2>/dev/null || echo "   → Go to: https://github.com/new"

echo ""
echo "✅ File ready: index.html"
echo "   Follow the steps above to deploy!"
echo ""
