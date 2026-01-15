# Data Update & Visualization Modification - Complete Overview

## 🎯 Purpose

This document provides a **high-level overview** of how to update your SCCL data lineage visualization system.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXCEL FILE                                │
│  FR2590_Data_Library_COMPLETE_CORRECTED.xlsx                │
│                                                              │
│  Sheets:                                                     │
│  • MASTER_LINEAGE (data flow)                               │
│  • MDRM_CATALOG (all MDRMs)                                 │
│  • SCHEDULE_MAP (schedule info)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Edit here
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              DATA EXTRACTION SCRIPT                          │
│  integrate_excel_data_complete_catalog.py                    │
│                                                              │
│  Reads Excel → Creates nodes.csv & edges.csv                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Auto-generated
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    CSV FILES                                 │
│  nodes.csv (494 nodes)                                      │
│  edges.csv (634 edges)                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Read by
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           VISUALIZATION GENERATION SCRIPT                   │
│  sccl_unified_view.py                                        │
│                                                              │
│  Reads CSV → Creates interactive HTML                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Auto-generated
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    HTML FILE                                 │
│  sccl_unified_view.html                                      │
│                                                              │
│  Interactive visualization in browser                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Standard Update Workflow

```
1. EDIT EXCEL FILE
   ↓
2. SAVE EXCEL FILE
   ↓
3. RUN: python3 integrate_excel_data_complete_catalog.py
   ↓
4. RUN: python3 validate_data.py
   ↓
5. RUN: python3 sccl_unified_view.py
   ↓
6. OPEN: sccl_unified_view.html
   ↓
7. VERIFY CHANGES
```

---

## 📝 What Can Be Updated

### ✅ Excel Data (Source of Truth)

| What | Where | How Often |
|------|-------|-----------|
| **Add MDRM** | MDRM_CATALOG + MASTER_LINEAGE | As needed |
| **Update MDRM name** | MDRM_CATALOG | When names change |
| **Add source system** | MASTER_LINEAGE | When new systems added |
| **Change transformation** | MASTER_LINEAGE | When logic changes |
| **Update schedule** | MASTER_LINEAGE + MDRM_CATALOG | When schedules change |

### ✅ Visualization Appearance

| What | File | Location |
|------|------|----------|
| **Node colors** | sccl_unified_view.py | color_map dictionary |
| **Node sizes** | sccl_unified_view.py | size parameter |
| **Layout spacing** | sccl_unified_view.py | levelSeparation, nodeSpacing |
| **Filters** | sccl_unified_view.py | Control panel HTML |
| **Labels** | sccl_unified_view.py | label parameter |

---

## 🎯 Common Update Scenarios

### Scenario 1: Data Changes
**When:** Excel data changes (new MDRMs, updated names, etc.)

**Process:**
1. Edit Excel
2. Regenerate: `python3 integrate_excel_data_complete_catalog.py`
3. Visualize: `python3 sccl_unified_view.py`

**Time:** 2-5 minutes

### Scenario 2: Appearance Changes
**When:** Want different colors, sizes, layout

**Process:**
1. Edit `sccl_unified_view.py`
2. Regenerate: `python3 sccl_unified_view.py`

**Time:** 1-2 minutes

### Scenario 3: Both Data + Appearance
**When:** Making multiple changes

**Process:**
1. Edit Excel
2. Edit `sccl_unified_view.py` (if needed)
3. Regenerate data: `python3 integrate_excel_data_complete_catalog.py`
4. Regenerate visualization: `python3 sccl_unified_view.py`

**Time:** 3-7 minutes

---

## 📚 Documentation Structure

### Quick Start
- **QUICK_UPDATE_REFERENCE.md** - One-page cheat sheet

### Detailed Guides
- **DATA_UPDATE_GUIDE.md** - Complete instructions (read this first!)
- **UPDATE_WORKFLOW_EXAMPLES.md** - Step-by-step examples

### Reference
- **COMPLETE_CATALOG_GUIDE.md** - Catalog coverage explanation
- **VALIDATION_FINDINGS.md** - Why 123 MDRMs have no inputs

---

## 🔍 Validation & Testing

### After Every Update:

```bash
# 1. Validate structure
python3 validate_data.py

# 2. Check MDRM connections
python3 diagnose_mdrm_connections.py

# 3. Test visualization
open sccl_unified_view.html
```

### What to Check:
- ✅ Node counts correct
- ✅ No orphaned nodes
- ✅ All references valid
- ✅ Visualization loads
- ✅ Filters work
- ✅ Colors correct
- ✅ Layout appropriate

---

## ⚠️ Important Rules

### ✅ DO:
- Edit Excel file directly
- Save Excel before regenerating
- Run validation after changes
- Test in browser after regeneration
- Backup before major changes

### ❌ DON'T:
- Edit CSV files directly (they're auto-generated)
- Edit HTML file directly (it's auto-generated)
- Skip validation
- Make changes without testing
- Regenerate after every tiny change (batch changes)

---

## 🎓 Learning Path

### Beginner:
1. Read: **QUICK_UPDATE_REFERENCE.md**
2. Try: Example 1 (Adding a New MDRM)
3. Practice: Make a small change and regenerate

### Intermediate:
1. Read: **DATA_UPDATE_GUIDE.md**
2. Try: Multiple examples from **UPDATE_WORKFLOW_EXAMPLES.md**
3. Practice: Bulk updates, appearance changes

### Advanced:
1. Read: All documentation
2. Customize: Add filters, metadata, custom styling
3. Optimize: Performance tuning, custom layouts

---

## 📊 File Editability Matrix

| File | Can Edit? | When | How |
|------|-----------|------|-----|
| **Excel** | ✅ YES | Always | Excel app |
| **integrate_excel_data_*.py** | ⚠️ Advanced | Excel structure changes | Text editor |
| **sccl_unified_view.py** | ⚠️ Advanced | Appearance changes | Text editor |
| **nodes.csv** | ❌ NO | Never | Auto-generated |
| **edges.csv** | ❌ NO | Never | Auto-generated |
| **sccl_unified_view.html** | ❌ NO | Never | Auto-generated |

---

## 🚀 Quick Commands Reference

```bash
# Regenerate everything (after Excel changes)
python3 integrate_excel_data_complete_catalog.py && \
python3 validate_data.py && \
python3 sccl_unified_view.py

# Just visualization (after appearance changes)
python3 sccl_unified_view.py

# Validate only
python3 validate_data.py

# Diagnose issues
python3 diagnose_mdrm_connections.py

# Deploy
./deploy.sh
```

---

## 🎯 Decision Tree

```
Need to update visualization?
│
├─ Data changed? (new MDRMs, sources, etc.)
│  └─ YES → Edit Excel → Regenerate data → Regenerate visualization
│
├─ Appearance changed? (colors, sizes, layout)
│  └─ YES → Edit sccl_unified_view.py → Regenerate visualization
│
└─ Both?
   └─ YES → Edit Excel → Edit sccl_unified_view.py → 
            Regenerate data → Regenerate visualization
```

---

## 📞 Getting Help

### If Something Goes Wrong:

1. **Check validation:**
   ```bash
   python3 validate_data.py
   ```

2. **Check diagnostics:**
   ```bash
   python3 diagnose_mdrm_connections.py
   ```

3. **Review error messages:**
   - Read full output
   - Check line numbers
   - Verify file paths

4. **Check documentation:**
   - `DATA_UPDATE_GUIDE.md` - Troubleshooting section
   - `UPDATE_WORKFLOW_EXAMPLES.md` - Similar examples

---

## ✅ Summary

### Key Points:

1. **Excel is source of truth** - Edit here for data changes
2. **Python scripts generate** - Don't edit CSV/HTML directly
3. **Always validate** - Run validation after changes
4. **Test in browser** - Verify changes appear correctly
5. **Document changes** - Keep track of what you modified

### Typical Workflow:

```
Edit → Save → Regenerate → Validate → Test → Deploy
```

### Time Estimates:

- Small change (1 MDRM): 2-3 minutes
- Medium change (10 MDRMs): 5-10 minutes
- Large change (bulk update): 15-30 minutes
- Appearance change: 1-2 minutes

---

## 📖 Next Steps

1. **Read:** `DATA_UPDATE_GUIDE.md` for complete instructions
2. **Try:** Examples in `UPDATE_WORKFLOW_EXAMPLES.md`
3. **Reference:** `QUICK_UPDATE_REFERENCE.md` for quick lookups
4. **Practice:** Make a small change and regenerate

---

**You're ready to make updates! Start with the quick reference, then dive into detailed guides as needed.** 🚀
