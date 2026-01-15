# Quick Update Reference Card

## 🚀 Most Common Tasks

### Adding a New MDRM

```bash
1. Open: FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
2. Go to: MDRM_CATALOG sheet
3. Add row: MDRM_Code, Data_Element_Name, Schedule
4. Go to: MASTER_LINEAGE sheet
5. Add row: Connect Source → Atomic → Transform → CDE → MDRM
6. Save Excel
7. Run: python3 integrate_excel_data_complete_catalog.py
8. Run: python3 sccl_unified_view.py
9. Open: sccl_unified_view.html
```

### Updating Existing MDRM

```bash
1. Open Excel
2. Find MDRM in MDRM_CATALOG sheet
3. Update: Data_Element_Name, Schedule, Formula_Logic
4. If lineage changes: Update MASTER_LINEAGE sheet
5. Save
6. python3 integrate_excel_data_complete_catalog.py
7. python3 sccl_unified_view.py
```

### Adding New Source System

```bash
1. Open Excel → MASTER_LINEAGE sheet
2. Add rows with new Source_System name
3. Connect to Atomic CDEs
4. Save
5. python3 integrate_excel_data_complete_catalog.py
6. python3 sccl_unified_view.py
```

### Changing Colors

```bash
1. Open: sccl_unified_view.py
2. Find: color_map dictionary (line ~134)
3. Change hex codes
4. Save
5. python3 sccl_unified_view.py
```

### Changing Layout Spacing

```bash
1. Open: sccl_unified_view.py
2. Find: "levelSeparation" (line ~47)
3. Change values:
   - levelSeparation: 800 → 400 (more compact) or 1200 (more spread)
   - nodeSpacing: 500 → 250 or 750
4. Save
5. python3 sccl_unified_view.py
```

---

## 📋 Standard Workflow

```bash
# After ANY Excel changes:
python3 integrate_excel_data_complete_catalog.py
python3 validate_data.py
python3 sccl_unified_view.py
open sccl_unified_view.html
```

---

## 🔍 Validation Commands

```bash
# Check data structure
python3 validate_data.py

# Diagnose MDRM connections
python3 diagnose_mdrm_connections.py

# Check Excel structure
python3 -c "import pandas as pd; df = pd.read_excel('FR2590_Data_Library_COMPLETE_CORRECTED.xlsx', sheet_name='MASTER_LINEAGE'); print(df.columns.tolist())"
```

---

## ⚠️ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `File not found` | Check file name and location |
| `Sheet not found` | Verify sheet names: MASTER_LINEAGE, MDRM_CATALOG, SCHEDULE_MAP |
| `KeyError: 'Source_System'` | Check column names in Excel |
| `Invalid references` | Run `python3 validate_data.py` to find issues |
| Visualization not updating | Hard refresh browser (Cmd+Shift+R) |

---

## 📁 Key Files

| File | Edit? | Purpose |
|------|-------|---------|
| `FR2590_Data_Library_COMPLETE_CORRECTED.xlsx` | ✅ YES | Source data |
| `integrate_excel_data_*.py` | ⚠️ Advanced | Data extraction |
| `sccl_unified_view.py` | ⚠️ Advanced | Visualization settings |
| `nodes.csv` | ❌ NO | Auto-generated |
| `edges.csv` | ❌ NO | Auto-generated |
| `sccl_unified_view.html` | ❌ NO | Auto-generated |

---

## 🎯 Two Scripts Available

**Complete Catalog (198 MDRMs):**
```bash
python3 integrate_excel_data_complete_catalog.py
```

**Institution-Specific (75 MDRMs):**
```bash
python3 integrate_excel_data_corrected.py
```

---

## 📖 Full Documentation

- **Complete Guide:** `DATA_UPDATE_GUIDE.md`
- **Catalog Guide:** `COMPLETE_CATALOG_GUIDE.md`
- **Testing:** `TESTING_STRATEGY.md`
- **Hosting:** `HOSTING_GUIDE.md`
