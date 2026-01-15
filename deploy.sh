#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  🚀 SCCL Data Lineage Visualization - Deployment Helper"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check if file exists
if [ ! -f "sccl_unified_view.html" ]; then
    echo "❌ Error: sccl_unified_view.html not found"
    echo "   Please run this script from the project directory"
    exit 1
fi

# Copy and rename for deployment
cp sccl_unified_view.html index.html
echo "✅ File prepared: index.html (ready for deployment)"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "  Choose your deployment method:"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1) 🐙 GitHub Pages (RECOMMENDED - 5 minutes) ⭐"
echo "   → Professional hosting"
echo "   → Get URL like: yourusername.github.io/repo-name"
echo "   → Free with version control"
echo "   → Most reliable option"
echo ""
echo "2) 💻 Local Server (INSTANT - 5 seconds)"
echo "   → Quick local testing"
echo "   → Share on local network"
echo "   → Great for demos"
echo "   → No signup needed"
echo ""
echo "3) 🌐 Vercel (EASY - 2 minutes)"
echo "   → Fast deployment"
echo "   → Get URL like: your-project.vercel.app"
echo "   → Free forever"
echo ""
echo "4) 📦 Create ZIP for sharing"
echo "   → Email or drive sharing"
echo "   → No hosting needed"
echo "   → Offline capable"
echo ""
echo "5) 🌐 Netlify Drop (Alternative - 30 seconds)"
echo "   → Drag & drop deployment"
echo "   → Get instant URL like: your-site.netlify.app"
echo "   → Free forever"
echo ""
echo "6) ℹ️  Show detailed instructions"
echo ""

read -p "Enter your choice (1-5): " choice
echo ""

case $choice in
    1)
        echo "════════════════════════════════════════════════════════════════"
        echo "  🐙 GitHub Pages Deployment"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Opening GitHub Pages helper..."
        sleep 1
        ./deploy_github_pages.sh
        ;;
    
    2)
        echo "════════════════════════════════════════════════════════════════"
        echo "  💻 Starting Local Server"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        ./start_local_server.sh
        ;;
    
    3)
        echo "════════════════════════════════════════════════════════════════"
        echo "  🌐 Vercel Deployment Guide"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Steps:"
        echo "1. Go to: https://vercel.com/new"
        echo "   (Sign up with GitHub or email - free)"
        echo ""
        echo "2. Deploy:"
        echo "   • Click 'Add New' → 'Project'"
        echo "   • Or drag and drop 'index.html'"
        echo "   • Wait 10 seconds"
        echo ""
        echo "3. Get your URL:"
        echo "   → https://your-project.vercel.app"
        echo ""
        echo "Opening Vercel..."
        sleep 1
        open "https://vercel.com/new" 2>/dev/null || xdg-open "https://vercel.com/new" 2>/dev/null || echo "   → Go to: https://vercel.com/new"
        echo ""
        ;;
    
    4)
        echo "════════════════════════════════════════════════════════════════"
        echo "  🐙 GitHub Pages Deployment Guide"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Manual Steps:"
        echo ""
        echo "1. Go to GitHub: https://github.com/new"
        echo "   → Create a new repository (e.g., 'sccl-data-lineage')"
        echo "   → Make it Public"
        echo "   → Check 'Add a README file'"
        echo "   → Click 'Create repository'"
        echo ""
        echo "2. Upload your file:"
        echo "   → Click 'Add file' → 'Upload files'"
        echo "   → Drag 'index.html' (created in this directory)"
        echo "   → Click 'Commit changes'"
        echo ""
        echo "3. Enable GitHub Pages:"
        echo "   → Go to Settings → Pages"
        echo "   → Source: select 'main' branch"
        echo "   → Click 'Save'"
        echo "   → Wait 1-2 minutes"
        echo ""
        echo "4. Access your site:"
        echo "   → https://yourusername.github.io/sccl-data-lineage/"
        echo ""
        echo "Opening GitHub..."
        sleep 1
        open "https://github.com/new" 2>/dev/null || xdg-open "https://github.com/new" 2>/dev/null || echo "   → Go to: https://github.com/new"
        echo ""
        ;;
    
    3)
        echo "════════════════════════════════════════════════════════════════"
        echo "  💻 Starting Local Server"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        
        # Get local IP
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
        
        echo "Server starting on port 8080..."
        echo ""
        echo "✅ Access locally:"
        echo "   → http://localhost:8080/index.html"
        echo ""
        
        if [ ! -z "$LOCAL_IP" ]; then
            echo "✅ Share on your network:"
            echo "   → http://$LOCAL_IP:8080/index.html"
            echo ""
        fi
        
        echo "📝 Instructions for others:"
        echo "   1. Connect to the same WiFi network"
        echo "   2. Open the URL above in their browser"
        echo "   3. No downloads or extensions needed!"
        echo ""
        echo "⚠️  Server will stop when you close this terminal"
        echo "   Press Ctrl+C to stop the server"
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        
        python3 -m http.server 8080
        ;;
    
    4)
        echo "════════════════════════════════════════════════════════════════"
        echo "  📦 Creating ZIP Package"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        
        ZIP_NAME="sccl-visualization-$(date +%Y%m%d).zip"
        
        # Create zip with relevant files
        zip -q "$ZIP_NAME" index.html README.md 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅ Created: $ZIP_NAME"
            echo ""
            echo "📝 What's included:"
            echo "   • index.html - The visualization"
            echo "   • README.md - User guide"
            echo ""
            echo "📤 How to share:"
            echo "   1. Email the ZIP file, or"
            echo "   2. Upload to Google Drive / Dropbox / OneDrive, or"
            echo "   3. Use WeTransfer for large files"
            echo ""
            echo "📝 Instructions for recipients:"
            echo "   1. Unzip the file"
            echo "   2. Double-click 'index.html'"
            echo "   3. Opens in their default browser"
            echo "   4. No installation required!"
            echo ""
        else
            echo "❌ Error creating ZIP file"
            echo "   Manual option: Right-click index.html → Compress"
        fi
        ;;
    
    5)
        echo "════════════════════════════════════════════════════════════════"
        echo "  🌐 Netlify Drop (Alternative)"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Steps:"
        echo "1. Opening Netlify Drop in your browser..."
        sleep 1
        open "https://app.netlify.com/drop" 2>/dev/null || xdg-open "https://app.netlify.com/drop" 2>/dev/null || echo "   → Go to: https://app.netlify.com/drop"
        echo ""
        echo "2. Drag and drop the file 'index.html' onto the page"
        echo "3. Wait 5 seconds for deployment"
        echo "4. Netlify will give you a URL to share!"
        echo ""
        echo "💡 Tip: Click 'Change site name' to customize your URL"
        echo ""
        echo "⚠️  If Netlify doesn't work, try GitHub Pages (option 1)"
        echo ""
        ;;
    
    6)
        echo "════════════════════════════════════════════════════════════════"
        echo "  ℹ️  Detailed Hosting Instructions"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "Opening HOSTING_GUIDE.md..."
        
        if command -v code &> /dev/null; then
            code HOSTING_GUIDE.md
        elif command -v open &> /dev/null; then
            open HOSTING_GUIDE.md
        else
            cat HOSTING_GUIDE.md
        fi
        
        echo ""
        echo "📖 For detailed instructions, see: HOSTING_GUIDE.md"
        echo ""
        ;;
    
    *)
        echo "❌ Invalid choice. Please run the script again and choose 1-6."
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ Done!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "💡 Need help? Check HOSTING_GUIDE.md for detailed instructions"
echo ""
