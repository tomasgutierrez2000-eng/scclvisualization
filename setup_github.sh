#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  🐙 GitHub Repository Setup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if already a git repo
if [ -d ".git" ]; then
    echo "⚠️  Git repository already exists"
    read -p "Continue anyway? (y/n): " continue
    if [ "$continue" != "y" ]; then
        exit 0
    fi
fi

# Initialize git
echo "1. Initializing git repository..."
git init

# Create/update README
echo ""
echo "2. Creating README.md..."
cat > README.md << 'EOFREADME'
# SCCL Data Lineage Visualization

Interactive data lineage visualization for FR 2590 SCCL regulatory reporting.

## Quick Start

1. Generate data: `python3 integrate_excel_data_complete_catalog.py`
2. Create visualization: `python3 sccl_unified_view.py`
3. Open: `sccl_unified_view.html`

## View Online

After enabling GitHub Pages, view at:
`https://tomasgutierrez2000-eng.github.io/scclvisualization/`

## Features

- Complete FR 2590 catalog (198 MDRMs)
- Interactive network visualization
- Source-to-report lineage tracing
- Filters and search
- Professional UI/UX

## Documentation

See `DOCUMENTATION_INDEX.md` for complete guides.
EOFREADME

# Add files
echo ""
echo "3. Adding files to git..."
git add README.md

# Essential files to add
FILES_TO_ADD=(
    "index.html"
    "sccl_unified_view.py"
    "integrate_excel_data_complete_catalog.py"
    "integrate_excel_data_corrected.py"
    "validate_data.py"
    "diagnose_mdrm_connections.py"
    "deploy.sh"
    "deploy_github_pages.sh"
    "start_local_server.sh"
)

for file in "${FILES_TO_ADD[@]}"; do
    if [ -f "$file" ]; then
        echo "   Adding: $file"
        git add "$file"
    fi
done

# Add documentation (optional)
echo ""
echo "4. Adding documentation files..."
git add *.md 2>/dev/null || true

# Commit
echo ""
echo "5. Creating initial commit..."
git commit -m "Initial commit: SCCL data lineage visualization"

# Set branch
echo ""
echo "6. Setting branch to main..."
git branch -M main

# Add remote
echo ""
echo "7. Adding remote repository..."
git remote add origin https://github.com/tomasgutierrez2000-eng/scclvisualization.git

# Check if remote already exists
if [ $? -ne 0 ]; then
    echo "   Remote already exists, updating..."
    git remote set-url origin https://github.com/tomasgutierrez2000-eng/scclvisualization.git
fi

# Push
echo ""
echo "8. Pushing to GitHub..."
echo "   (You may need to enter GitHub credentials)"
git push -u origin main

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Setup Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Enable GitHub Pages:"
echo "   → Go to: https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages"
echo "   → Source: Select 'main' branch"
echo "   → Folder: Select '/ (root)'"
echo "   → Click 'Save'"
echo ""
echo "2. Wait 1-2 minutes, then visit:"
echo "   → https://tomasgutierrez2000-eng.github.io/scclvisualization/"
echo ""
echo "3. Your visualization will be live!"
echo ""
