#!/bin/bash
# Quick push script - adds all files and pushes

cd /Users/tomas

echo "🚀 Adding all visualization files..."
git add index.html sccl_unified_view.py integrate_excel_data_complete_catalog.py integrate_excel_data_corrected.py validate_data.py diagnose_mdrm_connections.py README.md *.md *.sh 2>/dev/null

echo "💾 Committing..."
git commit -m "Add complete SCCL visualization system" 2>/dev/null || echo "No new changes"

echo ""
echo "✅ Ready to push!"
echo ""
echo "Run: git push -u origin main"
echo ""
echo "Username: tomasgutierrez2000-eng"
echo "Password: [Your Personal Access Token from https://github.com/settings/tokens/new]"
