#!/bin/bash

echo "🚀 Pushing to GitHub with your token..."
echo ""

cd /Users/tomas

# Set remote with token
git remote set-url origin https://tomasgutierrez2000-eng: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@github.com/tomasgutierrez2000-eng/scclvisualization.git

# Push
echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Done! Check: https://github.com/tomasgutierrez2000-eng/scclvisualization"
echo ""
echo "Next: Enable GitHub Pages at:"
echo "  https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages"
