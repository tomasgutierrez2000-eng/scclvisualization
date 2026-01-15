# How to Host Your SCCL Data Lineage Visualization

## 🎯 Quick Answer

Your visualization is a **single HTML file** that can be hosted anywhere! No server-side code needed.

---

## 🚀 Option 1: GitHub Pages (Recommended - FREE & EASY)

**Best for:** Sharing with team, permanent hosting, version control

### Steps:

1. **Create a GitHub account** (if you don't have one)
   - Go to https://github.com/signup

2. **Create a new repository**
   - Click "+" → "New repository"
   - Name it: `sccl-data-lineage` (or anything you want)
   - Make it **Public** (or Private if you have Pro)
   - Check "Add a README file"
   - Click "Create repository"

3. **Upload your file**
   - Click "Add file" → "Upload files"
   - Drag and drop: `sccl_unified_view.html`
   - Rename it to: `index.html` (important!)
   - Click "Commit changes"

4. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Under "Source", select: `main` branch
   - Click "Save"
   - Wait 1-2 minutes

5. **Share the link!**
   - Your site will be at: `https://yourusername.github.io/sccl-data-lineage/`
   - Anyone can access it with this URL

### Pros:
- ✅ Completely free
- ✅ Custom domain possible
- ✅ Version control
- ✅ Easy updates (just upload new file)
- ✅ Professional URL

### Cons:
- ⚠️ Public by default (upgrade to Pro for private repos with Pages)
- ⚠️ 1GB file size limit (your file is ~600KB, so no issue)

---

## 🌐 Option 2: Netlify Drop (EASIEST - FREE)

**Best for:** Instant deployment, drag & drop

### Steps:

1. **Go to Netlify Drop**
   - Visit: https://app.netlify.com/drop

2. **Rename your file**
   - Rename `sccl_unified_view.html` to `index.html`

3. **Drag and drop**
   - Drag `index.html` onto the Netlify Drop page
   - Wait 5 seconds

4. **Get your link**
   - Netlify generates a URL like: `https://random-name-123456.netlify.app`
   - Click "Change site name" to customize it
   - Share this URL with anyone!

### Pros:
- ✅ Absolutely easiest (30 seconds total)
- ✅ Completely free
- ✅ Instant deployment
- ✅ Custom domain possible
- ✅ Free SSL/HTTPS

### Cons:
- ⚠️ Random URL by default (can customize)
- ⚠️ Need to drag new file to update

---

## ⚡ Option 3: Vercel (EASY - FREE)

**Best for:** Modern deployment, GitHub integration

### Steps:

1. **Install Vercel CLI** (optional)
   ```bash
   npm install -g vercel
   ```

2. **Or use the website**
   - Go to: https://vercel.com/new
   - Sign up with GitHub
   - Click "Deploy" and select your file

3. **Or deploy via CLI**
   ```bash
   cd /Users/tomas
   vercel deploy sccl_unified_view.html
   ```

4. **Share the link**
   - Vercel gives you: `https://your-project.vercel.app`

### Pros:
- ✅ Free for personal use
- ✅ Instant deployment
- ✅ Great performance
- ✅ Custom domains
- ✅ GitHub integration

---

## 🏢 Option 4: AWS S3 + CloudFront (PROFESSIONAL)

**Best for:** Enterprise, high security, compliance

### Steps:

1. **Create S3 bucket**
   ```bash
   aws s3 mb s3://sccl-data-lineage --region us-east-1
   ```

2. **Upload file**
   ```bash
   aws s3 cp sccl_unified_view.html s3://sccl-data-lineage/index.html --acl public-read
   ```

3. **Enable static website hosting**
   - In AWS Console: S3 → Your Bucket → Properties → Static Website Hosting
   - Set index document: `index.html`

4. **Optional: Add CloudFront CDN**
   - For HTTPS and faster global access

5. **Access via**
   - `http://sccl-data-lineage.s3-website-us-east-1.amazonaws.com`

### Pros:
- ✅ Enterprise-grade
- ✅ Highly scalable
- ✅ Custom domain + SSL
- ✅ Global CDN
- ✅ Fine-grained access control

### Cons:
- ⚠️ Requires AWS account
- ⚠️ Small cost (usually < $1/month)
- ⚠️ More complex setup

---

## 💻 Option 5: Share via Local Network (QUICK TESTING)

**Best for:** Internal team, temporary sharing, demos

### Using Python (Simplest):

```bash
cd /Users/tomas
python3 -m http.server 8080
```

Then share: `http://YOUR_IP_ADDRESS:8080/sccl_unified_view.html`

### Find your IP:
```bash
# Mac/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Or
ipconfig getifaddr en0
```

### Pros:
- ✅ Instant (5 seconds)
- ✅ No signup needed
- ✅ Works on local network

### Cons:
- ⚠️ Only works while your computer is on
- ⚠️ Only accessible on same network
- ⚠️ Not suitable for external sharing

---

## 🔒 Option 6: Password-Protected Hosting

**Best for:** Sensitive data, internal only

### Using Netlify with Password Protection:

1. **Deploy to Netlify** (Option 2 above)

2. **Add password protection**
   - Upgrade to Netlify Pro ($19/month)
   - Enable password protection in site settings

### Using Vercel with Authentication:

1. **Deploy to Vercel** (Option 3 above)

2. **Add Vercel Password Protection**
   - In project settings → Protection
   - Enable password protection

### Using GitHub Pages + CloudFlare:

1. **Deploy to GitHub Pages** (Option 1)

2. **Add CloudFlare Access**
   - Add your site to CloudFlare (free)
   - Enable CloudFlare Access
   - Set up authentication rules

---

## 📦 Option 7: Share as ZIP File (NO HOSTING)

**Best for:** One-time sharing, offline use

### Steps:

1. **Create a package**
   ```bash
   cd /Users/tomas
   zip sccl-visualization.zip sccl_unified_view.html README.md
   ```

2. **Share via**
   - Email
   - Google Drive
   - Dropbox
   - WeTransfer

3. **Recipient instructions**
   - Unzip the file
   - Double-click `sccl_unified_view.html`
   - Opens in default browser

### Pros:
- ✅ No hosting needed
- ✅ Works offline
- ✅ Complete control

### Cons:
- ⚠️ Manual distribution
- ⚠️ No automatic updates
- ⚠️ Each person needs the file

---

## 🎯 My Recommendation

### For Quick Sharing (< 5 minutes)
**Use Netlify Drop:**
1. Rename file to `index.html`
2. Drag to https://app.netlify.com/drop
3. Share the URL

### For Professional/Long-term (10 minutes)
**Use GitHub Pages:**
1. Create GitHub repo
2. Upload as `index.html`
3. Enable Pages
4. Share `https://yourusername.github.io/repo-name/`

### For Enterprise/Sensitive Data
**Use AWS S3 + CloudFront with IAM:**
- Full control over access
- Enterprise-grade security
- Compliance-ready

---

## 🔧 Quick Deployment Script

Save this as `deploy.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying SCCL Data Lineage Visualization"
echo ""

# Check if file exists
if [ ! -f "sccl_unified_view.html" ]; then
    echo "❌ Error: sccl_unified_view.html not found"
    exit 1
fi

# Copy and rename for deployment
cp sccl_unified_view.html index.html

echo "✅ File prepared: index.html"
echo ""
echo "Choose deployment option:"
echo "1) GitHub Pages (recommended)"
echo "2) Netlify (easiest)"
echo "3) Local server (testing)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "📝 Manual steps for GitHub Pages:"
        echo "   1. Create repo on GitHub"
        echo "   2. Upload index.html"
        echo "   3. Enable Pages in Settings"
        echo "   4. Access at: https://yourusername.github.io/repo-name/"
        ;;
    2)
        echo "🌐 Opening Netlify Drop..."
        open "https://app.netlify.com/drop"
        echo "   → Drag and drop index.html to deploy"
        ;;
    3)
        echo "💻 Starting local server..."
        echo "   → Access at: http://localhost:8080/index.html"
        echo "   → Press Ctrl+C to stop"
        python3 -m http.server 8080
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac
```

Make it executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📊 Comparison Table

| Option | Ease | Speed | Cost | Best For |
|--------|------|-------|------|----------|
| **Netlify Drop** | ⭐⭐⭐⭐⭐ | 30 sec | Free | Quick share |
| **GitHub Pages** | ⭐⭐⭐⭐ | 5 min | Free | Long-term |
| **Vercel** | ⭐⭐⭐⭐ | 2 min | Free | Modern teams |
| **AWS S3** | ⭐⭐ | 15 min | ~$1/mo | Enterprise |
| **Local Server** | ⭐⭐⭐⭐⭐ | 5 sec | Free | Testing |
| **ZIP File** | ⭐⭐⭐⭐⭐ | 1 min | Free | Offline |

---

## 🔄 Updating Your Hosted Site

### GitHub Pages:
1. Upload new `index.html` to repo
2. Commit changes
3. Wait 1-2 minutes for deployment

### Netlify:
1. Drag new `index.html` to existing site
2. Instant update

### Vercel:
```bash
vercel deploy sccl_unified_view.html --prod
```

### AWS S3:
```bash
aws s3 cp sccl_unified_view.html s3://your-bucket/index.html
```

---

## 🔐 Security Considerations

### For Sensitive Data:

1. **Use Authentication**
   - Netlify/Vercel password protection
   - AWS IAM policies
   - CloudFlare Access

2. **Private Repository**
   - GitHub Private repo + Pages (requires Pro)

3. **Internal Hosting**
   - Host on company intranet
   - Use VPN for external access

4. **Data Obfuscation**
   - Remove sensitive labels before deployment
   - Use codes instead of real names
   - Add authentication layer

---

## ✅ Post-Deployment Checklist

- [ ] File renamed to `index.html`
- [ ] Deployed to chosen platform
- [ ] URL works in browser
- [ ] All interactions work (zoom, filter, search)
- [ ] Loading screen disappears correctly
- [ ] Shared URL with team
- [ ] Documented URL for future reference
- [ ] Set up update process
- [ ] (Optional) Custom domain configured
- [ ] (Optional) Analytics added

---

## 🆘 Troubleshooting

### Issue: "File not found" error
**Solution:** Make sure file is named `index.html`

### Issue: Visualization doesn't load
**Solution:** Check browser console (F12) for errors

### Issue: Can't access from other computers
**Solution:** Check firewall settings, use public hosting

### Issue: Slow loading for remote users
**Solution:** Use CDN (CloudFront, Netlify, or Vercel)

### Issue: Need to restrict access
**Solution:** Use password protection or AWS IAM

---

## 📞 Need Help?

1. Check browser console (F12) for errors
2. Verify HTML file is valid
3. Try different hosting option
4. Test in incognito mode (rules out extensions)

---

**Status: Ready to Deploy! 🚀**

Choose your preferred option above and your visualization will be live in minutes!
