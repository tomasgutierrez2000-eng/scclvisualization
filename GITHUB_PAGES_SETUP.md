# GitHub Pages Setup - Quick Guide

## 🚀 Fastest Way (Automated Script)

Run this in your terminal:

```bash
./setup_github.sh
```

This script will:
1. Initialize git
2. Create README.md
3. Add all files
4. Commit and push to GitHub
5. Show you next steps

---

## 📋 Manual Steps (If Script Doesn't Work)

### Step 1: Initialize Git
```bash
cd /Users/tomas
git init
```

### Step 2: Add Files
```bash
git add README.md
git add index.html
git add sccl_unified_view.py
git add integrate_excel_data_complete_catalog.py
git add integrate_excel_data_corrected.py
git add validate_data.py
git add *.md *.sh
```

### Step 3: Commit
```bash
git commit -m "first commit"
```

### Step 4: Set Branch
```bash
git branch -M main
```

### Step 5: Add Remote
```bash
git remote add origin https://github.com/tomasgutierrez2000-eng/scclvisualization.git
```

### Step 6: Push
```bash
git push -u origin main
```

---

## 🎯 Enable GitHub Pages

After pushing, enable Pages:

1. **Go to:** https://github.com/tomasgutierrez2000-eng/scclvisualization/settings/pages

2. **Under "Source":**
   - Branch: Select `main`
   - Folder: Select `/ (root)`
   - Click **Save**

3. **Wait 1-2 minutes**

4. **Visit:** https://tomasgutierrez2000-eng.github.io/scclvisualization/

---

## ✅ Your Site Will Be Live At:

```
https://tomasgutierrez2000-eng.github.io/scclvisualization/
```

**Share this URL with anyone!**

---

## 🔄 Updating Your Site

After making changes:

```bash
# 1. Regenerate visualization
python3 integrate_excel_data_complete_catalog.py
python3 sccl_unified_view.py

# 2. Update index.html
cp _unified_view.html index.html

# 3. Commit and push
git add index.html
git commit -m "Update visualization"
git push
```

**GitHub Pages updates automatically in 1-2 minutes!**

---

## 🆘 Troubleshooting

### "Repository not found"
- Check repository name: `scclvisualization`
- Verify you have access to: `tomasgutierrez2000-eng/scclvisualization`

### "Authentication failed"
- You may need to use a personal access token
- Or use GitHub Desktop app instead

### "Pages not working"
- Make sure `index.html` is in root directory
- Check Settings → Pages shows "Published"
- Wait 2-3 minutes for first deployment

### "File not found"
- Make sure `index.html` exists
- Check it's in the root of the repository

---

## 💡 Pro Tips

1. **Always name it `index.html`** - GitHub Pages looks for this
2. **Keep it in root** - Don't put in subfolder
3. **Wait 1-2 minutes** - Pages takes time to deploy
4. **Check Settings → Pages** - Should show "Published" status

---

**Your visualization will be live and shareable!** 🎉
