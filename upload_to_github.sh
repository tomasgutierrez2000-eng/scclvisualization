#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 Upload to GitHub - Alternative Methods"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /Users/tomas

# Method 1: Try with token in URL
echo "📦 Method 1: Using token in remote URL..."
git remote remove origin 2>/dev/null
git remote add origin https://tomasgutierrez2000-eng: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@github.com/tomasgutierrez2000-eng/scclvisualization.git

echo "Pushing..."
if git push -u origin main 2>&1; then
    echo ""
    echo "✅ SUCCESS! Pushed to GitHub!"
    echo ""
    echo "Next steps:"
    echo "1. Enable GitHub Pages: https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages"
    echo "2. Visit: https://tomasgutierrez2000-eng.github.io/scclvisualization/"
    exit 0
fi

echo ""
echo "❌ Method 1 failed. Trying Method 2..."
echo ""

# Method 2: Use GIT_ASKPASS
echo "📦 Method 2: Using GIT_ASKPASS..."
cat > /tmp/git-askpass.sh << 'ASKPASS'
#!/bin/bash
case "$1" in
    Username*) echo "tomasgutierrez2000-eng" ;;
    Password*) echo "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" ;;
esac
ASKPASS
chmod +x /tmp/git-askpass.sh

export GIT_ASKPASS=/tmp/git-askpass.sh
export GIT_TERMINAL_PROMPT=0

if git push -u origin main 2>&1; then
    echo ""
    echo "✅ SUCCESS! Pushed to GitHub!"
    echo ""
    echo "Next steps:"
    echo "1. Enable GitHub Pages: https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages"
    echo "2. Visit: https://tomasgutierrez2000-eng.github.io/scclvisualization/"
    exit 0
fi

echo ""
echo "❌ Both methods failed."
echo ""
echo "🔍 Troubleshooting:"
echo "1. Check if repository exists: https://github.com/tomasgutierrez2000-eng/scclvisualization"
echo "2. Verify token permissions: https://github.com/settings/tokens"
echo "3. Token might need 'repo' scope"
echo ""
echo "💡 Alternative: Use GitHub Desktop or web interface"
echo "   → Go to: https://github.com/tomasgutierrez2000-eng/scclvisualization"
echo "   → Click 'uploading an existing file'"
echo "   → Drag and drop your files"
