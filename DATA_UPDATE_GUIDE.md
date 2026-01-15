# Complete Data Update Guide - End-to-End Instructions

## 📋 Table of Contents

1. [Overview](#overview)
2. [Understanding the Data Structure](#understanding-the-data-structure)
3. [Updating the Excel Catalog](#updating-the-excel-catalog)
4. [Regenerating the Visualization](#regenerating-the-visualization)
5. [Changing What's Visualized](#changing-whats-visualized)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)
8. [Quick Reference](#quick-reference)

---

## 🎯 Overview

### What This Guide Covers

This guide provides **complete, step-by-step instructions** for:

1. **Updating the data catalog** (Excel file)
2. **Modifying visualization settings** (what's shown, how it looks)
3. **Regenerating visualizations** after changes
4. **Troubleshooting** common issues
5. **Best practices** for maintaining the system

### System Architecture

```
Excel File (FR2590_Data_Library_COMPLETE_CORRECTED.xlsx)
    ↓
Python Script (integrate_excel_data_*.py)
    ↓
CSV Files (nodes.csv, edges.csv)
    ↓
Visualization Script (sccl_unified_view.py)
    ↓
HTML File (sccl_unified_view.html)
    ↓
Browser (Interactive Visualization)
```

### Key Files

| File | Purpose | When to Edit |
|------|---------|--------------|
| `FR2590_Data_Library_COMPLETE_CORRECTED.xlsx` | **Source data** | When data changes |
| `integrate_excel_data_*.py` | **Data extraction** | When Excel structure changes |
| `sccl_unified_view.py` | **Visualization generation** | When changing appearance/behavior |
| `nodes.csv` | **Generated nodes** | Auto-generated, don't edit directly |
| `edges.csv` | **Generated edges** | Auto-generated, don't edit directly |
| `sccl_unified_view.html` | **Final output** | Auto-generated, don't edit directly |

---

## 📊 Understanding the Data Structure

### Excel File Structure

Your Excel file (`FR2590_Data_Library_COMPLETE_CORRECTED.xlsx`) contains **3 main sheets**:

#### 1. **MASTER_LINEAGE** Sheet
**Purpose:** Defines the complete data flow from sources to reports

**Key Columns:**
- `Source_System` - Where data originates (e.g., "Trade Repository")
- `Source_Table` - Database table name
- `Atomic_CDE_ID` - Unique identifier for atomic data element
- `Atomic_CDE_Name` - Human-readable name
- `Transform_ID` - Transformation logic identifier
- `Transform_Type` - Type of transformation
- `Transform_Logic` - Formula/description
- `Enriched_CDE_ID` - Output CDE identifier
- `Enriched_CDE_Name` - Output CDE name
- `MDRM_Code` - Regulatory report code (e.g., "SCCL_JG17")
- `MDRM_Name` - MDRM description
- `Schedule` - Report schedule (e.g., "G-2")

**Example Row:**
```
Source_System: Trade Repository
Atomic_CDE_ID: ATOMIC_001
Transform_ID: TRANSFORM_001
Enriched_CDE_ID: CDE_001
MDRM_Code: SCCL_JG17
Schedule: G-2
```

#### 2. **MDRM_CATALOG** Sheet
**Purpose:** Complete catalog of all possible MDRMs

**Key Columns:**
- `MDRM_Code` - Unique MDRM identifier
- `Data_Element_Name` - MDRM description
- `Schedule` - Which schedule it belongs to
- `Formula_Logic` - Calculation formula (if applicable)
- `Business_Definition` - Business meaning

**Example Row:**
```
MDRM_Code: SCCL_JG17
Data_Element_Name: Repo: Sovereign 0% ≤1yr Transferred
Schedule: G-2
Formula_Logic: SUM + Haircut
```

#### 3. **SCHEDULE_MAP** Sheet
**Purpose:** Schedule metadata

**Key Columns:**
- `Schedule_ID` - Schedule identifier (e.g., "G-2")
- `Schedule_Name` - Full schedule name
- `Primary_Purpose` - What the schedule reports

---

## ✏️ Updating the Excel Catalog

### Scenario 1: Adding a New Data Source

**When:** Your institution adds a new source system

**Steps:**

1. **Open Excel file:**
   ```bash
   open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
   ```

2. **Go to MASTER_LINEAGE sheet**

3. **Add new rows** with your new source:
   ```
   Source_System: [New System Name]
   Source_Table: [Table Name]
   Atomic_CDE_ID: [New ID]
   Atomic_CDE_Name: [Description]
   ... (fill in rest of columns)
   ```

4. **Save the file**

5. **Regenerate visualization:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

**Example:**
```
Adding "Credit Risk System" as new source:
- Add rows with Source_System = "Credit Risk System"
- Connect to appropriate Atomic CDEs
- Link through transformations to MDRMs
```

---

### Scenario 2: Adding a New MDRM

**When:** Regulatory requirement adds new MDRM, or you start using a catalog MDRM

**Steps:**

1. **Open Excel file**

2. **If MDRM already in catalog:**
   - Go to **MASTER_LINEAGE** sheet
   - Add row with the MDRM_Code from catalog
   - Fill in lineage: Source → Atomic → Transform → CDE → MDRM

3. **If MDRM is new:**
   - Go to **MDRM_CATALOG** sheet
   - Add new row with MDRM_Code, Data_Element_Name, Schedule
   - Go to **MASTER_LINEAGE** sheet
   - Add lineage row

4. **Save the file**

5. **Regenerate:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

**Example:**
```
Adding new MDRM "SCCL_NEW001":
1. Add to MDRM_CATALOG:
   MDRM_Code: SCCL_NEW001
   Data_Element_Name: New Regulatory Field
   Schedule: G-2

2. Add to MASTER_LINEAGE:
   [Connect through your data flow]
   MDRM_Code: SCCL_NEW001
```

---

### Scenario 3: Updating Existing MDRM Information

**When:** MDRM name changes, schedule changes, or formula updates

**Steps:**

1. **Open Excel file**

2. **Update MDRM_CATALOG sheet:**
   - Find the MDRM_Code row
   - Update Data_Element_Name, Schedule, Formula_Logic, etc.

3. **If lineage changes:**
   - Update **MASTER_LINEAGE** sheet
   - Modify the row(s) with that MDRM_Code

4. **Save the file**

5. **Regenerate:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

---

### Scenario 4: Removing/Deactivating an MDRM

**When:** You stop using an MDRM (product discontinued, etc.)

**Option A: Keep in Catalog (Recommended)**
- **Don't delete** from MDRM_CATALOG
- **Remove** from MASTER_LINEAGE
- Result: MDRM becomes "catalog-only" (gray node)

**Option B: Remove Completely**
- Delete from MASTER_LINEAGE
- Delete from MDRM_CATALOG (if truly obsolete)
- Regenerate visualization

**Steps:**
1. Open Excel
2. Remove row(s) from MASTER_LINEAGE with that MDRM_Code
3. (Optional) Remove from MDRM_CATALOG
4. Save
5. Regenerate

---

### Scenario 5: Changing Transformation Logic

**When:** Business rules change, formulas update

**Steps:**

1. **Open Excel file**

2. **Go to MASTER_LINEAGE sheet**

3. **Find the Transform_ID row(s)**

4. **Update:**
   - `Transform_Logic` - New formula/description
   - `Transform_Type` - If type changed
   - `Enriched_CDE_Name` - If output name changed

5. **Save the file**

6. **Regenerate:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

---

### Scenario 6: Bulk Updates

**When:** Multiple changes at once

**Best Practice:**
1. **Make all Excel changes first**
2. **Save once**
3. **Regenerate once:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

**Don't:**
- ❌ Regenerate after each small change
- ❌ Edit CSV files directly
- ❌ Edit HTML file directly

---

## 🔄 Regenerating the Visualization

### Standard Regeneration Process

**After ANY Excel changes:**

```bash
# Step 1: Regenerate data files
python3 integrate_excel_data_complete_catalog.py

# Step 2: Generate visualization
python3 sccl_unified_view.py

# Step 3: View result
open sccl_unified_view.html
```

### What Happens During Regeneration

1. **Data Extraction (`integrate_excel_data_*.py`):**
   - Reads Excel file
   - Parses all sheets
   - Creates nodes (sources, CDEs, MDRMs, etc.)
   - Creates edges (connections)
   - Saves to `nodes.csv` and `edges.csv`

2. **Visualization Generation (`sccl_unified_view.py`):**
   - Reads `nodes.csv` and `edges.csv`
   - Creates interactive network graph
   - Applies styling and colors
   - Adds filters and controls
   - Saves to `sccl_unified_view.html`

### Regeneration Checklist

Before regenerating:
- [ ] Excel file saved
- [ ] All changes complete
- [ ] Backup made (if major changes)

After regenerating:
- [ ] Check console for errors
- [ ] Validate: `python3 validate_data.py`
- [ ] Open HTML and verify changes
- [ ] Test filters and interactions

---

## 🎨 Changing What's Visualized

### Option 1: Switch Between Complete Catalog vs Institution-Specific

**Complete Catalog (198 MDRMs):**
```bash
python3 integrate_excel_data_complete_catalog.py
python3 sccl_unified_view.py
```

**Institution-Specific (75 MDRMs):**
```bash
python3 integrate_excel_data_corrected.py
python3 sccl_unified_view.py
```

---

### Option 2: Modify Node Colors

**File:** `sccl_unified_view.py`

**Location:** Around line 134-140

**Current Colors:**
```python
color_map = {
    'Source': '#238636',      # Green
    'Atomic': '#6e7681',      # Gray
    'Logic': '#1f6feb',       # Blue
    'CDE': '#d29922',         # Yellow
    'Report': '#da3633',      # Red
}
```

**To Change:**
1. Open `sccl_unified_view.py`
2. Find `color_map` dictionary
3. Change hex color codes
4. Save file
5. Regenerate: `python3 sccl_unified_view.py`

**Example:**
```python
color_map = {
    'Source': '#00ff00',      # Bright green
    'Atomic': '#808080',      # Medium gray
    'Logic': '#0000ff',       # Bright blue
    'CDE': '#ffff00',         # Bright yellow
    'Report': '#ff0000',      # Bright red
}
```

---

### Option 3: Change Node Sizes

**File:** `sccl_unified_view.py`

**Location:** In node creation sections (around lines 160-340)

**Current Sizes:**
```python
size=35,  # Source nodes
size=32,  # Atomic CDEs
size=36,  # Transformations
size=28,  # CDEs
size=26,  # MDRMs
size=40,  # Schedules
size=70,  # Final Report
```

**To Change:**
1. Find the node type you want to change
2. Modify the `size=` parameter
3. Save and regenerate

**Example:**
```python
# Make MDRMs larger
net.add_node(
    row['id'],
    ...
    size=40,  # Changed from 26
    ...
)
```

---

### Option 4: Show/Hide Database Layer

**File:** `sccl_unified_view.py`

**Location:** Around line 339-355

**To Hide Database Nodes:**
```python
# Change hidden=True to hidden=False
net.add_node(
    row['id'],
    ...
    hidden=True,  # Already hidden by default
    ...
)
```

**To Show by Default:**
```python
hidden=False,  # Change to False
```

**Or use the toggle in the visualization:**
- Right panel → "Database View" checkbox

---

### Option 5: Modify Physics/Layout

**File:** `sccl_unified_view.py`

**Location:** Around line 41-62

**Current Settings:**
```python
"levelSeparation": 800,    # Horizontal spacing between levels
"nodeSpacing": 500,        # Spacing between nodes
"treeSpacing": 900,        # Spacing between trees
```

**To Make More Compact:**
```python
"levelSeparation": 400,    # Reduce horizontal spacing
"nodeSpacing": 250,        # Reduce node spacing
"treeSpacing": 450,        # Reduce tree spacing
```

**To Make More Spread Out:**
```python
"levelSeparation": 1200,   # Increase horizontal spacing
"nodeSpacing": 750,        # Increase node spacing
"treeSpacing": 1350,       # Increase tree spacing
```

---

### Option 6: Change Filter Options

**File:** `sccl_unified_view.py`

**Location:** Around line 406-560 (control panel HTML)

**To Add New Filter:**
1. Find the filter section
2. Add new HTML input element
3. Add JavaScript handler
4. Update `applyFilters()` function

**Example - Add "Source System" filter:**
```javascript
// In control panel HTML
<select id="sourceFilter">
    <option value="all">All Sources</option>
    <option value="Trade Repository">Trade Repository</option>
    ...
</select>

// In JavaScript
var selectedSource = document.getElementById('sourceFilter').value;
// Add to filter logic
```

---

### Option 7: Customize Labels

**File:** `sccl_unified_view.py`

**Location:** In node creation sections

**Current Label Format:**
```python
label = str(row['label']).replace('Source_', '').replace('_', ' ')
```

**To Change Format:**
```python
# Show ID and name
label = f"{row['id']}\n{row['label']}"

# Show only name
label = str(row['label']).split('\n')[1] if '\n' in str(row['label']) else str(row['label'])

# Custom format
label = f"[{row['id']}] {row['label']}"
```

---

## 🔧 Troubleshooting

### Issue 1: "File not found" Error

**Error:**
```
FileNotFoundError: Excel file not found
```

**Solution:**
1. Check file name: `FR2590_Data_Library_COMPLETE_CORRECTED.xlsx`
2. Check location: Should be in same directory as script
3. Check spelling: Case-sensitive on some systems

```bash
# Verify file exists
ls -la FR2590_Data_Library_COMPLETE_CORRECTED.xlsx

# If not found, check current directory
pwd
```

---

### Issue 2: "Sheet not found" Error

**Error:**
```
KeyError: 'MASTER_LINEAGE'
```

**Solution:**
1. Open Excel file
2. Verify sheet names:
   - `MASTER_LINEAGE` (exact spelling)
   - `MDRM_CATALOG` (exact spelling)
   - `SCHEDULE_MAP` (exact spelling)
3. Fix sheet names if different

---

### Issue 3: Missing Columns

**Error:**
```
KeyError: 'Source_System'
```

**Solution:**
1. Open Excel file
2. Check column names in MASTER_LINEAGE sheet
3. Required columns:
   - `Source_System`
   - `Atomic_CDE_ID`
   - `Transform_ID`
   - `Enriched_CDE_ID`
   - `MDRM_Code`
   - `Schedule`
4. Fix column names if different

---

### Issue 4: Invalid Node References

**Error:**
```
Invalid source references: MDRM_XXX
```

**Solution:**
1. Run validation: `python3 validate_data.py`
2. Check which nodes are invalid
3. Verify Excel data:
   - MDRM codes match between sheets
   - No typos in MDRM_Code column
   - No special characters causing issues

---

### Issue 5: Visualization Not Updating

**Symptoms:**
- Changes made but HTML looks the same
- Old data still showing

**Solution:**
1. **Clear browser cache:**
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
   - Or open in incognito mode

2. **Verify regeneration:**
   ```bash
   # Check file modification time
   ls -la sccl_unified_view.html
   
   # Should be recent (just now)
   ```

3. **Regenerate again:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

---

### Issue 6: Performance Issues

**Symptoms:**
- Slow loading
- Laggy zooming
- Browser freezing

**Solutions:**

1. **Reduce node count:**
   - Use institution-specific script (75 MDRMs)
   - Filter out unused MDRMs

2. **Optimize physics:**
   - In `sccl_unified_view.py`, reduce iterations:
   ```python
   "iterations": 50,  # Reduce from 100
   ```

3. **Close other browser tabs**

4. **Use more powerful computer**

---

### Issue 7: Colors Not Showing Correctly

**Symptoms:**
- All nodes same color
- Custom colors not applied

**Solution:**
1. Check `color_map` dictionary in `sccl_unified_view.py`
2. Verify hex color codes are valid (6 characters, # prefix)
3. Check if node has custom color property:
   ```python
   # For catalog-only MDRMs
   color=row.get('color', color_map['Report'])
   ```

---

## ✅ Best Practices

### 1. Always Backup Before Major Changes

```bash
# Create backup
cp FR2590_Data_Library_COMPLETE_CORRECTED.xlsx \
   FR2590_Data_Library_COMPLETE_CORRECTED_BACKUP_$(date +%Y%m%d).xlsx
```

### 2. Validate After Every Change

```bash
# Always run validation
python3 validate_data.py
```

### 3. Test in Browser After Regeneration

```bash
# Don't just regenerate - actually check it
python3 sccl_unified_view.py
open sccl_unified_view.html
# Test filters, zoom, interactions
```

### 4. Document Changes

Keep a changelog:
```markdown
## 2026-01-15
- Added new source system: Credit Risk System
- Added 3 new MDRMs: SCCL_NEW001, SCCL_NEW002, SCCL_NEW003
- Updated transformation logic for TRANSFORM_001
```

### 5. Use Version Control

```bash
# If using git
git add FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
git commit -m "Added new MDRMs and source system"
```

### 6. Test Incrementally

- Make small changes
- Test each change
- Don't make 20 changes at once

### 7. Keep Excel Structure Consistent

- Don't rename columns
- Don't change sheet names
- Follow existing format

---

## 📋 Quick Reference

### Common Commands

```bash
# Regenerate complete catalog
python3 integrate_excel_data_complete_catalog.py && python3 sccl_unified_view.py

# Regenerate institution-specific
python3 integrate_excel_data_corrected.py && python3 sccl_unified_view.py

# Validate data
python3 validate_data.py

# Diagnose MDRM connections
python3 diagnose_mdrm_connections.py

# Deploy to web
./deploy.sh
```

### File Locations

```
/Users/tomas/
├── FR2590_Data_Library_COMPLETE_CORRECTED.xlsx  ← Edit this
├── integrate_excel_data_complete_catalog.py     ← Use for 198 MDRMs
├── integrate_excel_data_corrected.py            ← Use for 75 MDRMs
├── sccl_unified_view.py                         ← Edit for appearance
├── nodes.csv                                     ← Auto-generated
├── edges.csv                                     ← Auto-generated
└── sccl_unified_view.html                       ← Final output
```

### Excel Sheet Structure

```
MASTER_LINEAGE:
  Source_System | Source_Table | Atomic_CDE_ID | ... | MDRM_Code | Schedule

MDRM_CATALOG:
  MDRM_Code | Data_Element_Name | Schedule | Formula_Logic | ...

SCHEDULE_MAP:
  Schedule_ID | Schedule_Name | Primary_Purpose
```

### Typical Workflow

```
1. Edit Excel file
   ↓
2. Save Excel file
   ↓
3. Run: python3 integrate_excel_data_complete_catalog.py
   ↓
4. Run: python3 validate_data.py
   ↓
5. Run: python3 sccl_unified_view.py
   ↓
6. Open: sccl_unified_view.html
   ↓
7. Test and verify
```

---

## 🎓 Advanced Customization

### Custom Node Shapes

**File:** `sccl_unified_view.py`

**Current shapes:**
- Source: `ellipse`
- Atomic: `box`
- Logic: `diamond`
- CDE: `box`
- MDRM: `box`
- Schedule: `box`

**To change:**
```python
shape='triangle',  # Options: box, circle, diamond, dot, star, triangle, triangleDown, icon
```

### Custom Edge Styles

**File:** `sccl_unified_view.py`

**To make edges curved:**
```python
smooth={'type': 'continuous', 'roundness': 0.8}  # Higher = more curved
```

**To make edges straight:**
```python
smooth={'type': 'straight'}  # or False
```

### Add Custom Metadata

**In Excel:**
Add new columns to MASTER_LINEAGE:
- `Business_Owner`
- `Last_Updated`
- `Data_Quality_Score`

**In Python:**
```python
nodes_list.append({
    'id': ...,
    'label': ...,
    'business_owner': row.get('Business_Owner', 'N/A'),
    'last_updated': row.get('Last_Updated', 'N/A'),
    ...
})
```

**In Visualization:**
Metadata appears in tooltips and can be used in filters.

---

## 📞 Support

### If You Get Stuck

1. **Check validation:**
   ```bash
   python3 validate_data.py
   ```

2. **Check diagnostics:**
   ```bash
   python3 diagnose_mdrm_connections.py
   ```

3. **Review error messages:**
   - Read full error output
   - Check line numbers
   - Verify file paths

4. **Check documentation:**
   - `COMPLETE_CATALOG_GUIDE.md`
   - `VALIDATION_FINDINGS.md`
   - `TESTING_STRATEGY.md`

---

## ✅ Summary Checklist

Before making changes:
- [ ] Backup Excel file
- [ ] Understand current structure
- [ ] Plan your changes

After making changes:
- [ ] Save Excel file
- [ ] Regenerate data: `python3 integrate_excel_data_complete_catalog.py`
- [ ] Validate: `python3 validate_data.py`
- [ ] Generate visualization: `python3 sccl_unified_view.py`
- [ ] Test in browser
- [ ] Verify all changes appear correctly
- [ ] Test filters and interactions
- [ ] Document changes

---

**You're now equipped to make any updates to your data catalog and visualization!** 🚀
