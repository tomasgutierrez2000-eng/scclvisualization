# Update Workflow - Step-by-Step Examples

## 📚 Example 1: Adding a New MDRM (Complete Walkthrough)

### Scenario
You need to add a new MDRM "SCCL_NEW001" for a new regulatory requirement.

### Step-by-Step

#### Step 1: Open Excel File
```bash
# On Mac:
open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx

# Or double-click in Finder
```

#### Step 2: Add to MDRM_CATALOG Sheet
1. Click on **MDRM_CATALOG** tab
2. Scroll to bottom or find empty row
3. Add new row:
   ```
   MDRM_Code: SCCL_NEW001
   Data_Element_Name: New Regulatory Field for Derivatives
   Schedule: G-2
   Formula_Logic: SUM(CDE_001, CDE_002)
   Business_Definition: Total derivative exposure
   ```
4. **Save** (Cmd+S or File → Save)

#### Step 3: Add Lineage to MASTER_LINEAGE Sheet
1. Click on **MASTER_LINEAGE** tab
2. Find existing rows that feed into similar MDRMs
3. Copy a similar row structure
4. Modify to create your lineage:
   ```
   Source_System: Trade Repository
   Source_Table: DERIVATIVES_TABLE
   Atomic_CDE_ID: ATOMIC_001
   Atomic_CDE_Name: Derivative Notional
   Transform_ID: TRANSFORM_001
   Transform_Type: Aggregation
   Transform_Logic: SUM(Atomic_CDE_ID)
   Enriched_CDE_ID: CDE_001
   Enriched_CDE_Name: Total Derivative Exposure
   MDRM_Code: SCCL_NEW001
   MDRM_Name: New Regulatory Field for Derivatives
   Schedule: G-2
   ```
5. **Save** (Cmd+S)

#### Step 4: Regenerate Data Files
```bash
cd /Users/tomas
python3 integrate_excel_data_complete_catalog.py
```

**Expected Output:**
```
======================================================================
COMPLETE CATALOG INTEGRATION - ALL INSTITUTIONS
======================================================================
...
  ✅ Created 495 nodes total:
  ...
  MDRMs: 199 (76 with lineage, 123 catalog-only)
...
```

#### Step 5: Validate
```bash
python3 validate_data.py
```

**Check for:**
- ✅ Node count increased by 1
- ✅ No errors
- ✅ New MDRM appears in validation

#### Step 6: Generate Visualization
```bash
python3 sccl_unified_view.py
```

**Expected Output:**
```
============================================================
Creating Unified SCCL Data Lineage View
============================================================
...
✓ SUCCESS!
  • Saved to: sccl_unified_view.html
```

#### Step 7: Verify in Browser
```bash
open sccl_unified_view.html
```

**What to check:**
1. New MDRM appears (should be red if has lineage)
2. Connections are correct
3. Search for "SCCL_NEW001" works
4. Clicking highlights correct path

---

## 📚 Example 2: Updating MDRM Name

### Scenario
MDRM "SCCL_JG17" name changed from "Repo: Sovereign" to "Repo: Sovereign Securities"

### Step-by-Step

#### Step 1: Open Excel
```bash
open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
```

#### Step 2: Update MDRM_CATALOG
1. Go to **MDRM_CATALOG** sheet
2. Find row with `MDRM_Code = SCCL_JG17`
3. Change `Data_Element_Name`:
   ```
   Old: Repo: Sovereign 0% ≤1yr Transferred
   New: Repo: Sovereign Securities 0% ≤1yr Transferred
   ```
4. **Save**

#### Step 3: Update MASTER_LINEAGE (if needed)
1. Go to **MASTER_LINEAGE** sheet
2. Find row(s) with `MDRM_Code = SCCL_JG17`
3. Update `MDRM_Name` to match:
   ```
   MDRM_Name: Repo: Sovereign Securities 0% ≤1yr Transferred
   ```
4. **Save**

#### Step 4: Regenerate
```bash
python3 integrate_excel_data_complete_catalog.py
python3 sccl_unified_view.py
```

#### Step 5: Verify
```bash
open sccl_unified_view.html
# Search for "SCCL_JG17"
# Verify new name appears
```

---

## 📚 Example 3: Adding New Source System

### Scenario
Your institution adds "Credit Risk System" as a new data source.

### Step-by-Step

#### Step 1: Open Excel
```bash
open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
```

#### Step 2: Add to MASTER_LINEAGE
1. Go to **MASTER_LINEAGE** sheet
2. Add new rows for each atomic CDE from this source:
   ```
   Row 1:
   Source_System: Credit Risk System
   Source_Table: CREDIT_EXPOSURES
   Atomic_CDE_ID: ATOMIC_CREDIT_001
   Atomic_CDE_Name: Credit Exposure Amount
   Transform_ID: TRANSFORM_CREDIT_001
   Transform_Type: Calculation
   Transform_Logic: Calculate exposure
   Enriched_CDE_ID: CDE_CREDIT_001
   Enriched_CDE_Name: Total Credit Exposure
   MDRM_Code: SCCL_JG17
   MDRM_Name: [existing MDRM]
   Schedule: G-2
   
   Row 2:
   [Similar structure for next atomic CDE]
   ...
   ```
3. **Save**

#### Step 3: Regenerate
```bash
python3 integrate_excel_data_complete_catalog.py
python3 validate_data.py
python3 sccl_unified_view.py
```

#### Step 4: Verify
```bash
open sccl_unified_view.html
# Look for new green "Credit Risk System" node
# Verify connections to atomic CDEs
```

---

## 📚 Example 4: Changing Visualization Appearance

### Scenario
You want to make MDRM nodes larger and change their color to purple.

### Step-by-Step

#### Step 1: Open Python File
```bash
# Use your preferred editor
code sccl_unified_view.py
# or
nano sccl_unified_view.py
# or
open -a "TextEdit" sccl_unified_view.py
```

#### Step 2: Find MDRM Node Creation
Search for: `# 5. MDRM NODES` (around line 273)

#### Step 3: Modify Size
Find this section:
```python
net.add_node(
    row['id'],
    label=label,
    title=simple_title,
    color=color_map['Report'],
    shape='box',
    size=26,  # ← Change this
    ...
)
```

Change to:
```python
size=40,  # Increased from 26
```

#### Step 4: Modify Color
Find `color_map` dictionary (around line 134):
```python
color_map = {
    'Source': '#238636',
    'Atomic': '#6e7681',
    'Logic': '#1f6feb',
    'CDE': '#d29922',
    'Report': '#da3633',  # ← Change this
}
```

Change to:
```python
'Report': '#bc8cff',  # Purple color
```

#### Step 5: Save and Regenerate
```bash
# Save the file first!
python3 sccl_unified_view.py
```

#### Step 6: Verify
```bash
open sccl_unified_view.html
# MDRMs should now be larger and purple
```

---

## 📚 Example 5: Making Layout More Compact

### Scenario
Visualization is too spread out, want it more compact.

### Step-by-Step

#### Step 1: Open sccl_unified_view.py
```bash
code sccl_unified_view.py
```

#### Step 2: Find Physics Settings
Search for: `"levelSeparation"` (around line 47)

#### Step 3: Reduce Spacing
Find:
```python
"levelSeparation": 800,
"nodeSpacing": 500,
"treeSpacing": 900,
```

Change to:
```python
"levelSeparation": 400,  # Half the original
"nodeSpacing": 250,      # Half the original
"treeSpacing": 450,      # Half the original
```

#### Step 4: Save and Regenerate
```bash
python3 sccl_unified_view.py
```

#### Step 5: Verify
```bash
open sccl_unified_view.html
# Layout should be more compact
```

---

## 📚 Example 6: Bulk Update - Multiple MDRMs

### Scenario
You need to update 10 MDRMs at once (name changes, schedule changes).

### Step-by-Step

#### Step 1: Plan Your Changes
Create a list:
```
MDRM_Code: SCCL_JG17 → New Name: "Repo: Updated Name"
MDRM_Code: SCCL_JG18 → Schedule: G-2 → G-3
MDRM_Code: SCCL_JG19 → Formula: "SUM" → "SUM + Adjustment"
...
```

#### Step 2: Open Excel
```bash
open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
```

#### Step 3: Make All Changes
1. Go to **MDRM_CATALOG** sheet
2. Update all 10 MDRMs
3. Go to **MASTER_LINEAGE** sheet
4. Update corresponding rows
5. **Save once** (don't save after each change)

#### Step 4: Regenerate Once
```bash
python3 integrate_excel_data_complete_catalog.py
python3 validate_data.py
python3 sccl_unified_view.py
```

#### Step 5: Verify All Changes
```bash
open sccl_unified_view.html
# Check each of the 10 MDRMs
# Use search to find them
```

---

## 📚 Example 7: Removing/Deactivating an MDRM

### Scenario
You stop offering a product, so MDRM "SCCL_JG50" is no longer used.

### Step-by-Step

#### Option A: Keep in Catalog (Recommended)

1. **Open Excel**
2. **Go to MASTER_LINEAGE sheet**
3. **Find all rows with `MDRM_Code = SCCL_JG50`**
4. **Delete those rows** (or mark as inactive)
5. **Keep in MDRM_CATALOG** (don't delete)
6. **Save**
7. **Regenerate:**
   ```bash
   python3 integrate_excel_data_complete_catalog.py
   python3 sccl_unified_view.py
   ```

**Result:** MDRM becomes gray "catalog-only" node (no lineage)

#### Option B: Remove Completely

1. **Open Excel**
2. **Delete from MASTER_LINEAGE** (all rows with that MDRM_Code)
3. **Delete from MDRM_CATALOG** (the row)
4. **Save**
5. **Regenerate**

**Result:** MDRM completely removed from visualization

---

## 📚 Example 8: Fixing Data Errors

### Scenario
Validation shows "Invalid source references: MDRM_XXX"

### Step-by-Step

#### Step 1: Run Validation
```bash
python3 validate_data.py
```

**Output shows:**
```
❌ Found 2 invalid source references:
    - MDRM_SCCL_JG16-JG65
    - MDRM_SCCL_JG70-JH22
```

#### Step 2: Check Excel
```bash
# Open Excel
open FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
```

#### Step 3: Find the Issue
1. Go to **MASTER_LINEAGE** sheet
2. Search for "JG16-JG65" or "JG70-JH22"
3. Check if MDRM_Code exists in **MDRM_CATALOG**

#### Step 4: Fix
**If MDRM missing from catalog:**
- Add to MDRM_CATALOG sheet

**If typo in code:**
- Fix the MDRM_Code in MASTER_LINEAGE

**If range code (contains hyphen):**
- This is OK - range codes are valid
- Script should handle them (already fixed in complete catalog version)

#### Step 5: Regenerate and Re-validate
```bash
python3 integrate_excel_data_complete_catalog.py
python3 validate_data.py
# Should show no errors now
```

---

## 📚 Example 9: Switching Between Views

### Scenario
You want to show complete catalog to regulators, but use focused view internally.

### Step-by-Step

#### For Regulators (198 MDRMs):
```bash
python3 integrate_excel_data_complete_catalog.py
python3 sccl_unified_view.py
cp sccl_unified_view.html sccl_complete_catalog.html
```

#### For Internal Use (75 MDRMs):
```bash
python3 integrate_excel_data_corrected.py
python3 sccl_unified_view.py
cp sccl_unified_view.html sccl_internal.html
```

#### Deploy Both:
```bash
# Deploy complete catalog version
cp sccl_complete_catalog.html index.html
# Deploy to Netlify/GitHub Pages

# Deploy internal version separately
# Or use different file names
```

---

## 📚 Example 10: Adding Custom Metadata

### Scenario
You want to show "Business Owner" for each MDRM.

### Step-by-Step

#### Step 1: Add Column to Excel
1. Open Excel
2. Go to **MASTER_LINEAGE** sheet
3. Add new column: `Business_Owner`
4. Fill in values for each row
5. **Save**

#### Step 2: Update Python Script
Open `integrate_excel_data_complete_catalog.py`

Find MDRM node creation (around line 200):
```python
nodes_list.append({
    'id': f"MDRM_{mdrm_code}",
    'label': f"{mdrm_code}\n{mdrm_name}",
    ...
})
```

Add:
```python
nodes_list.append({
    'id': f"MDRM_{mdrm_code}",
    'label': f"{mdrm_code}\n{mdrm_name}",
    'business_owner': row.get('Business_Owner', 'N/A'),  # ← Add this
    ...
})
```

#### Step 3: Update Visualization
Open `sccl_unified_view.py`

Find MDRM node creation, update title:
```python
title=f"MDRM: {mdrm_name}\nCode: {mdrm_code}\nBusiness Owner: {row.get('business_owner', 'N/A')}"
```

#### Step 4: Regenerate
```bash
python3 integrate_excel_data_complete_catalog.py
python3 sccl_unified_view.py
```

#### Step 5: Verify
```bash
open sccl_unified_view.html
# Hover over MDRM nodes
# Should see "Business Owner: [Name]" in tooltip
```

---

## ✅ Best Practices Checklist

Before making changes:
- [ ] Backup Excel file
- [ ] Understand what you're changing
- [ ] Plan all changes first

While making changes:
- [ ] Make all Excel changes before regenerating
- [ ] Save Excel frequently
- [ ] Don't edit CSV files directly

After making changes:
- [ ] Save Excel file
- [ ] Run validation: `python3 validate_data.py`
- [ ] Regenerate: `python3 integrate_excel_data_complete_catalog.py`
- [ ] Generate visualization: `python3 sccl_unified_view.py`
- [ ] Test in browser
- [ ] Verify all changes appear
- [ ] Document what changed

---

## 🆘 Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| Changes not showing | Hard refresh browser (Cmd+Shift+R) |
| Validation errors | Check Excel column names match exactly |
| Missing nodes | Verify data in Excel, check for typos |
| Wrong colors | Check color_map in sccl_unified_view.py |
| Layout issues | Adjust levelSeparation, nodeSpacing values |

---

**For complete details, see: `DATA_UPDATE_GUIDE.md`**
