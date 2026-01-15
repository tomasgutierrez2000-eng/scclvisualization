"""
Diagnose why MDRMs lack input connections
Analyzes the Excel data to categorize disconnected MDRMs
"""

import pandas as pd

def diagnose_mdrm_connections(excel_file='FR2590_Data_Library_COMPLETE_CORRECTED.xlsx'):
    """Diagnose why MDRMs lack input connections."""
    
    print("=" * 70)
    print("MDRM CONNECTION DIAGNOSIS")
    print("=" * 70)
    
    try:
        master_df = pd.read_excel(excel_file, sheet_name='MASTER_LINEAGE')
        mdrm_catalog = pd.read_excel(excel_file, sheet_name='MDRM_CATALOG')
    except Exception as e:
        print(f"❌ Error loading Excel: {e}")
        return None
    
    # All MDRMs from catalog
    catalog_mdrms = set(str(row['MDRM_Code']).strip() 
                        for _, row in mdrm_catalog.iterrows() 
                        if pd.notna(row['MDRM_Code']))
    
    # MDRMs in lineage with CDE connections
    lineage_with_cde = set(str(row['MDRM_Code']).strip() 
                           for _, row in master_df.iterrows() 
                           if pd.notna(row.get('MDRM_Code')) and pd.notna(row.get('Enriched_CDE_ID')))
    
    # MDRMs in lineage without CDE connections
    lineage_no_cde = set(str(row['MDRM_Code']).strip() 
                         for _, row in master_df.iterrows() 
                         if pd.notna(row.get('MDRM_Code')) and pd.isna(row.get('Enriched_CDE_ID')))
    
    # MDRMs only in catalog (not in lineage at all)
    catalog_only = catalog_mdrms - (lineage_with_cde | lineage_no_cde)
    
    print(f"\n📊 SUMMARY:")
    print("-" * 70)
    print(f"  Total MDRMs in catalog:              {len(catalog_mdrms)}")
    print(f"  MDRMs with CDE connections:          {len(lineage_with_cde)} ✓")
    print(f"  MDRMs in lineage but no CDE:         {len(lineage_no_cde)} ⚠️")
    print(f"  MDRMs only in catalog (no lineage):  {len(catalog_only)} ⚠️")
    print(f"  Total disconnected:                  {len(lineage_no_cde) + len(catalog_only)}")
    
    # Analyze formulas to see if we can derive connections
    print(f"\n🔍 FORMULA ANALYSIS:")
    print("-" * 70)
    
    import re
    mdrm_pattern = re.compile(r'\b([A-Z]{4}\d{4})\b')  # Matches RCON1234, SCCL1234, etc.
    
    derivable_mdrms = set()
    for _, row in mdrm_catalog.iterrows():
        mdrm_code = str(row['MDRM_Code']).strip()
        if mdrm_code not in lineage_with_cde:
            formula = str(row.get('Formula_Logic', ''))
            if formula and formula != 'nan':
                referenced_mdrms = mdrm_pattern.findall(formula)
                if referenced_mdrms:
                    derivable_mdrms.add(mdrm_code)
    
    print(f"  MDRMs with formulas (derivable):     {len(derivable_mdrms)} 💡")
    print(f"  Still truly disconnected:            {len(lineage_no_cde) + len(catalog_only) - len(derivable_mdrms)}")
    
    # Show examples
    print(f"\n📋 EXAMPLES:")
    print("-" * 70)
    
    if lineage_no_cde:
        print(f"\n  MDRMs in lineage but no CDE (first 5):")
        for mdrm in sorted(lineage_no_cde)[:5]:
            print(f"    - {mdrm}")
    
    if catalog_only:
        print(f"\n  MDRMs only in catalog (first 5):")
        for mdrm in sorted(catalog_only)[:5]:
            # Get details
            mdrm_row = mdrm_catalog[mdrm_catalog['MDRM_Code'] == mdrm]
            if not mdrm_row.empty:
                name = mdrm_row.iloc[0].get('Data_Element_Name', 'N/A')
                formula = str(mdrm_row.iloc[0].get('Formula_Logic', ''))[:50]
                print(f"    - {mdrm}: {name}")
                if formula and formula != 'nan':
                    print(f"      Formula: {formula}...")
    
    if derivable_mdrms:
        print(f"\n  MDRMs derivable from formulas (first 5):")
        for mdrm in sorted(derivable_mdrms)[:5]:
            mdrm_row = mdrm_catalog[mdrm_catalog['MDRM_Code'] == mdrm]
            if not mdrm_row.empty:
                formula = str(mdrm_row.iloc[0].get('Formula_Logic', ''))
                referenced = mdrm_pattern.findall(formula)
                print(f"    - {mdrm} ← {', '.join(referenced[:3])}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 70)
    
    if len(derivable_mdrms) > 0:
        print(f"  1. ✅ Implement MDRM→MDRM derivation logic")
        print(f"     This will connect {len(derivable_mdrms)} additional MDRMs")
    
    if len(catalog_only) > 50:
        print(f"  2. ⚠️  Review catalog-only MDRMs")
        print(f"     {len(catalog_only)} MDRMs have no lineage data at all")
        print(f"     Are these placeholders or missing data?")
    
    if len(lineage_no_cde) > 0:
        print(f"  3. 📝 Check Excel data for lineage MDRMs with null Enriched_CDE_ID")
        print(f"     {len(lineage_no_cde)} rows have MDRM but no CDE connection")
    
    print("\n" + "=" * 70)
    
    return {
        'connected': lineage_with_cde,
        'lineage_no_cde': lineage_no_cde,
        'catalog_only': catalog_only,
        'derivable': derivable_mdrms
    }

if __name__ == '__main__':
    result = diagnose_mdrm_connections()
    if result:
        print(f"\n✅ Diagnosis complete!")
        print(f"   Run enhanced version to fix: python3 integrate_excel_data_enhanced.py")
