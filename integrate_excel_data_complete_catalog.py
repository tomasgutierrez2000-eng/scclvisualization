"""
Complete Catalog Integration - Shows ALL MDRMs (196+)
Enhanced version that includes catalog-only MDRMs for comprehensive coverage
"""

import pandas as pd
import numpy as np
import os

def create_nodes_from_corrected_excel_complete(excel_file='FR2590_Data_Library_COMPLETE_CORRECTED.xlsx'):
    """
    Create nodes including ALL MDRMs from catalog.
    Distinguishes between MDRMs with lineage vs catalog-only.
    """
    print(f"📖 Reading complete catalog from: {excel_file}")
    
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    # Read all sheets at once
    print("  Loading Excel sheets...")
    excel_data = pd.read_excel(excel_file, sheet_name=['MASTER_LINEAGE', 'MDRM_CATALOG', 'SCHEDULE_MAP'])
    
    master_df = excel_data['MASTER_LINEAGE']
    mdrm_catalog = excel_data['MDRM_CATALOG']
    schedule_map = excel_data['SCHEDULE_MAP']
    
    print(f"  ✓ Loaded {len(master_df)} lineage rows, {len(mdrm_catalog)} MDRMs, {len(schedule_map)} schedules")
    
    nodes_list = []
    
    print("\n  Creating nodes...")
    
    # 1. SOURCE SYSTEMS
    print("    → Source systems", end="", flush=True)
    source_systems = master_df['Source_System'].dropna().unique()
    for source in source_systems:
        if pd.notna(source) and str(source).strip():
            source_id = f"Source_{str(source).replace(' ', '_').replace('/', '_')}"
            nodes_list.append({
                'id': source_id,
                'label': str(source).replace('_', ' '),
                'group': 'Source',
                'title': f"Source System: {source}\nProvides data for Atomic CDEs"
            })
    print(" ✓")
    
    # 1b. DATABASE/TABLE NODES
    print("    → Database tables", end="", flush=True)
    db_tables = master_df[['Source_System', 'Source_Table']].drop_duplicates()
    for _, row in db_tables.iterrows():
        if pd.notna(row['Source_System']) and pd.notna(row['Source_Table']):
            source_sys = str(row['Source_System']).strip()
            table_name = str(row['Source_Table']).strip()
            db_id = f"DB_{source_sys.replace(' ', '_').replace('/', '_')}_{table_name}"
            nodes_list.append({
                'id': db_id,
                'label': f"{source_sys}\n{table_name}",
                'group': 'Database',
                'database': source_sys,
                'table': table_name,
                'title': f"Database Table: {table_name}\nSource System: {source_sys}"
            })
    print(" ✓")
    
    # 2. ATOMIC CDE NODES
    print("    → Atomic CDEs", end="", flush=True)
    atomic_cdes = master_df[['Atomic_CDE_ID', 'Atomic_CDE_Name', 'Source_System', 'Source_Table', 'Data_Type']].drop_duplicates()
    for _, row in atomic_cdes.iterrows():
        if pd.notna(row['Atomic_CDE_ID']):
            atomic_id = str(row['Atomic_CDE_ID']).strip()
            atomic_name = str(row['Atomic_CDE_Name']).strip() if pd.notna(row['Atomic_CDE_Name']) else atomic_id
            data_type = str(row['Data_Type']).strip() if pd.notna(row['Data_Type']) else 'Unknown'
            source = str(row['Source_System']).strip() if pd.notna(row['Source_System']) else 'Unknown'
            
            nodes_list.append({
                'id': f"Atomic_{atomic_id}",
                'label': f"{atomic_id}\n{atomic_name}",
                'group': 'Atomic',
                'data_element': atomic_name,
                'source_system': source,
                'title': f"Atomic CDE: {atomic_name}\nID: {atomic_id}\nType: {data_type}"
            })
    print(" ✓")
    
    # 3. TRANSFORMATION LOGIC NODES
    print("    → Transformations", end="", flush=True)
    transforms = master_df[['Transform_ID', 'Transform_Type', 'Transform_Logic', 'Enriched_CDE_Name']].drop_duplicates()
    for _, row in transforms.iterrows():
        if pd.notna(row['Transform_ID']):
            transform_id = str(row['Transform_ID']).strip()
            transform_type = str(row['Transform_Type']).strip() if pd.notna(row['Transform_Type']) else 'Unknown'
            enriched_name = str(row['Enriched_CDE_Name']).strip() if pd.notna(row['Enriched_CDE_Name']) else transform_id
            
            nodes_list.append({
                'id': f"Logic_{transform_id}",
                'label': f"{transform_id}\n{enriched_name}",
                'group': 'Logic',
                'data_element': enriched_name,
                'title': f"Transformation: {enriched_name}\nID: {transform_id}\nType: {transform_type}"
            })
    print(" ✓")
    
    # 4. ENRICHED CDE NODES
    print("    → Enriched CDEs", end="", flush=True)
    enriched_cdes = master_df[['Enriched_CDE_ID', 'Enriched_CDE_Name']].drop_duplicates()
    for _, row in enriched_cdes.iterrows():
        if pd.notna(row['Enriched_CDE_ID']):
            cde_id = str(row['Enriched_CDE_ID']).strip()
            cde_name = str(row['Enriched_CDE_Name']).strip() if pd.notna(row['Enriched_CDE_Name']) else cde_id
            
            nodes_list.append({
                'id': f"CDE_{cde_id}",
                'label': f"{cde_id}\n{cde_name}",
                'group': 'CDE',
                'data_element': cde_name,
                'title': f"CDE: {cde_name}\nID: {cde_id}"
            })
    print(" ✓")
    
    # 5. ALL MDRM NODES - Include everything from catalog
    print("    → MDRMs (complete catalog)", end="", flush=True)
    
    # Track which MDRMs have lineage (including range codes from MASTER_LINEAGE)
    mdrms_with_lineage = set(master_df['MDRM_Code'].dropna().unique())
    
    # First, add any range codes from MASTER_LINEAGE that aren't in catalog
    for _, row in master_df.iterrows():
        if pd.notna(row['MDRM_Code']):
            mdrm_code = str(row['MDRM_Code']).strip()
            # Check if this is a range code (contains hyphen)
            if '-' in mdrm_code:
                mdrm_name = str(row.get('MDRM_Name', mdrm_code))
                schedule = str(row.get('Schedule', 'Unknown'))
                
                nodes_list.append({
                    'id': f"MDRM_{mdrm_code}",
                    'label': f"{mdrm_code}\n{mdrm_name}",
                    'group': 'Report',
                    'data_element': mdrm_name,
                    'has_lineage': True,  # Range codes have lineage by definition
                    'color': '#da3633',
                    'opacity': 1.0,
                    'title': f"✓ Active MDRM Range: {mdrm_name}\nCode: {mdrm_code}\nSchedule: {schedule}\nRepresents multiple MDRMs"
                })
    
    # Add ALL MDRMs from catalog
    for _, row in mdrm_catalog.iterrows():
        if pd.notna(row['MDRM_Code']):
            mdrm_code = str(row['MDRM_Code']).strip()
            mdrm_name = str(row.get('Data_Element_Name', mdrm_code)).strip()
            schedule = str(row.get('Schedule', 'Unknown')).strip()
            formula = str(row.get('Formula_Logic', 'N/A'))
            business_def = str(row.get('Business_Definition', 'N/A'))
            
            # Determine if this MDRM has lineage
            has_lineage = mdrm_code in mdrms_with_lineage
            
            # Visual distinction
            if has_lineage:
                # Regular red for MDRMs with lineage
                color = '#da3633'
                opacity = 1.0
                label_suffix = ""
                title_prefix = "✓ Active MDRM"
            else:
                # Faded/gray for catalog-only MDRMs
                color = '#8b6f6f'  # Brownish-gray
                opacity = 0.6
                label_suffix = "\n(Catalog)"
                title_prefix = "⊘ Catalog-Only MDRM"
            
            nodes_list.append({
                'id': f"MDRM_{mdrm_code}",
                'label': f"{mdrm_code}\n{mdrm_name}{label_suffix}",
                'group': 'Report',
                'data_element': mdrm_name,
                'has_lineage': has_lineage,
                'color': color,
                'opacity': opacity,
                'title': f"{title_prefix}: {mdrm_name}\nCode: {mdrm_code}\nSchedule: {schedule}\n{'Has full lineage' if has_lineage else 'Catalog reference only'}"
            })
    print(" ✓")
    
    # 6. SCHEDULE NODES
    print("    → Schedules", end="", flush=True)
    schedules_from_master = set(master_df['Schedule'].dropna().unique())
    schedules_from_catalog = set(mdrm_catalog['Schedule'].dropna().unique())
    all_schedules = schedules_from_master.union(schedules_from_catalog)
    
    for schedule in all_schedules:
        if pd.notna(schedule) and str(schedule).strip():
            schedule_id = f"Schedule_{str(schedule).strip()}"
            schedule_info = schedule_map[schedule_map['Schedule_ID'] == str(schedule).strip()]
            if not schedule_info.empty:
                schedule_name = schedule_info.iloc[0].get('Schedule_Name', str(schedule))
                purpose = schedule_info.iloc[0].get('Primary_Purpose', 'N/A')
            else:
                schedule_name = str(schedule)
                purpose = 'N/A'
            
            nodes_list.append({
                'id': schedule_id,
                'label': f"Schedule {schedule}\n{schedule_name}",
                'group': 'Schedule',
                'title': f"Schedule: {schedule_name}\nID: {schedule}\nPurpose: {purpose}"
            })
    print(" ✓")
    
    # 7. FINAL REPORT ENDPOINT
    print("    → Final report endpoint", end="", flush=True)
    nodes_list.append({
        'id': 'FR2590_Final_Report',
        'label': 'FR 2590\nFinal Report\nSubmission',
        'group': 'Report',
        'title': 'FR 2590 Final Regulatory Report Submission\nContains all schedules'
    })
    print(" ✓")
    
    nodes_df = pd.DataFrame(nodes_list)
    
    # Summary
    total_mdrms = len(nodes_df[nodes_df['id'].str.startswith('MDRM_', na=False)])
    mdrms_with_lineage_count = len(nodes_df[(nodes_df['id'].str.startswith('MDRM_', na=False)) & (nodes_df['has_lineage'] == True)])
    mdrms_catalog_only = total_mdrms - mdrms_with_lineage_count
    
    print(f"\n  ✅ Created {len(nodes_df)} nodes total:")
    print(f"  Source: {len(nodes_df[nodes_df['group'] == 'Source'])}")
    print(f"  Atomic: {len(nodes_df[nodes_df['group'] == 'Atomic'])}")
    print(f"  Logic: {len(nodes_df[nodes_df['group'] == 'Logic'])}")
    print(f"  CDE: {len(nodes_df[nodes_df['group'] == 'CDE'])}")
    print(f"  MDRMs: {total_mdrms} ({mdrms_with_lineage_count} with lineage, {mdrms_catalog_only} catalog-only)")
    print(f"  Schedule: {len(nodes_df[nodes_df['id'].str.startswith('Schedule_', na=False)])}")
    print(f"  Final Report: 1")
    
    return nodes_df


def create_edges_from_corrected_excel_complete(excel_file='FR2590_Data_Library_COMPLETE_CORRECTED.xlsx', nodes_df=None):
    """
    Create edges for all MDRMs (including catalog-only).
    Catalog-only MDRMs only connect to schedules, not to CDEs.
    """
    print(f"\n🔗 Creating edges (including catalog-only MDRM connections)...")
    
    master_df = pd.read_excel(excel_file, sheet_name='MASTER_LINEAGE')
    mdrm_catalog = pd.read_excel(excel_file, sheet_name='MDRM_CATALOG')
    
    edges_list = []
    total_rows = len(master_df)
    progress_interval = max(1, total_rows // 10)
    
    # Track which MDRMs get CDE connections
    mdrms_with_cde_connections = set()
    
    for idx, row in master_df.iterrows():
        if idx % progress_interval == 0:
            progress = int((idx / total_rows) * 100)
            print(f"  Processing lineage... {progress}%", end="\r", flush=True)
        
        # 1. SOURCE → DATABASE TABLE
        if pd.notna(row['Source_System']) and pd.notna(row['Source_Table']):
            source_id = f"Source_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}"
            db_id = f"DB_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}_{str(row['Source_Table']).strip()}"
            if not any(e['source'] == source_id and e['target'] == db_id for e in edges_list):
                edges_list.append({
                    'source': source_id,
                    'target': db_id,
                    'label': 'Contains',
                    'layer': 'database'
                })
        
        # 2. DATABASE TABLE → ATOMIC CDE
        if pd.notna(row['Source_System']) and pd.notna(row['Source_Table']) and pd.notna(row['Atomic_CDE_ID']):
            db_id = f"DB_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}_{str(row['Source_Table']).strip()}"
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            edges_list.append({
                'source': db_id,
                'target': atomic_id,
                'label': 'Extracts',
                'layer': 'database'
            })
        
        # 3. SOURCE → ATOMIC CDE
        if pd.notna(row['Source_System']) and pd.notna(row['Atomic_CDE_ID']):
            source_id = f"Source_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}"
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            edges_list.append({
                'source': source_id,
                'target': atomic_id,
                'label': 'Extracts',
                'layer': 'standard'
            })
        
        # 4. ATOMIC CDE → TRANSFORMATION
        if pd.notna(row['Atomic_CDE_ID']) and pd.notna(row['Transform_ID']):
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            transform_id = f"Logic_{str(row['Transform_ID']).strip()}"
            edges_list.append({
                'source': atomic_id,
                'target': transform_id,
                'label': 'Input'
            })
        
        # 5. TRANSFORMATION → ENRICHED CDE
        if pd.notna(row['Transform_ID']) and pd.notna(row['Enriched_CDE_ID']):
            transform_id = f"Logic_{str(row['Transform_ID']).strip()}"
            enriched_id = f"CDE_{str(row['Enriched_CDE_ID']).strip()}"
            edges_list.append({
                'source': transform_id,
                'target': enriched_id,
                'label': 'Output'
            })
        
        # 6. ENRICHED CDE → MDRM
        if pd.notna(row['Enriched_CDE_ID']) and pd.notna(row['MDRM_Code']):
            enriched_id = f"CDE_{str(row['Enriched_CDE_ID']).strip()}"
            mdrm_id = f"MDRM_{str(row['MDRM_Code']).strip()}"
            edges_list.append({
                'source': enriched_id,
                'target': mdrm_id,
                'label': 'Feeds Into'
            })
            mdrms_with_cde_connections.add(str(row['MDRM_Code']).strip())
        
        # 7. MDRM → SCHEDULE (from lineage)
        if pd.notna(row['MDRM_Code']) and pd.notna(row['Schedule']):
            mdrm_id = f"MDRM_{str(row['MDRM_Code']).strip()}"
            schedule_id = f"Schedule_{str(row['Schedule']).strip()}"
            edges_list.append({
                'source': mdrm_id,
                'target': schedule_id,
                'label': 'Belongs To'
            })
    
    print(f"  Processing lineage... 100%")
    
    # 8. Add MDRM → Schedule connections for catalog-only MDRMs
    print(f"  Adding catalog-only MDRM connections...", end="", flush=True)
    catalog_only_count = 0
    
    for _, row in mdrm_catalog.iterrows():
        if pd.notna(row['MDRM_Code']) and pd.notna(row['Schedule']):
            mdrm_code = str(row['MDRM_Code']).strip()
            mdrm_id = f"MDRM_{mdrm_code}"
            schedule_id = f"Schedule_{str(row['Schedule']).strip()}"
            
            # Only add if not already connected
            if not any(e['source'] == mdrm_id and e['target'] == schedule_id for e in edges_list):
                # Use dashed line style for catalog-only connections
                is_catalog_only = mdrm_code not in mdrms_with_cde_connections
                edges_list.append({
                    'source': mdrm_id,
                    'target': schedule_id,
                    'label': 'Belongs To (Catalog)' if is_catalog_only else 'Belongs To',
                    'dashes': is_catalog_only  # Visual indicator
                })
                if is_catalog_only:
                    catalog_only_count += 1
    
    print(f" ✓ ({catalog_only_count} catalog-only connections)")
    
    # 9. SCHEDULE → FINAL REPORT
    schedules_from_master = set(master_df['Schedule'].dropna().unique())
    schedules_from_catalog = set(mdrm_catalog['Schedule'].dropna().unique())
    all_schedules = schedules_from_master.union(schedules_from_catalog)
    
    for schedule in all_schedules:
        if pd.notna(schedule) and str(schedule).strip():
            schedule_id = f"Schedule_{str(schedule).strip()}"
            if not any(e['source'] == schedule_id and e['target'] == 'FR2590_Final_Report' for e in edges_list):
                edges_list.append({
                    'source': schedule_id,
                    'target': 'FR2590_Final_Report',
                    'label': 'Populates'
                })
    
    edges_df = pd.DataFrame(edges_list)
    edges_df = edges_df.drop_duplicates(subset=['source', 'target'])
    
    print(f"\n  ✅ Created {len(edges_df)} edges total")
    print(f"  Extracts (Source→Atomic): {len(edges_df[edges_df['label'] == 'Extracts'])}")
    print(f"  Input (Atomic→Transform): {len(edges_df[edges_df['label'] == 'Input'])}")
    print(f"  Output (Transform→CDE): {len(edges_df[edges_df['label'] == 'Output'])}")
    print(f"  Feeds Into (CDE→MDRM): {len(edges_df[edges_df['label'] == 'Feeds Into'])}")
    print(f"  Belongs To (MDRM→Schedule): {len(edges_df[edges_df['label'].str.contains('Belongs To')])}")
    print(f"    • With lineage: {len(edges_df[edges_df['label'] == 'Belongs To'])}")
    print(f"    • Catalog-only: {len(edges_df[edges_df['label'] == 'Belongs To (Catalog)'])}")
    print(f"  Populates (Schedule→Report): {len(edges_df[edges_df['label'] == 'Populates'])}")
    
    return edges_df


def main():
    """Generate complete catalog visualization with all MDRMs."""
    excel_file = 'FR2590_Data_Library_COMPLETE_CORRECTED.xlsx'
    
    print("=" * 70)
    print("COMPLETE CATALOG INTEGRATION - ALL INSTITUTIONS")
    print("=" * 70)
    
    # Create nodes
    nodes_df = create_nodes_from_corrected_excel_complete(excel_file)
    
    # Create edges
    edges_df = create_edges_from_corrected_excel_complete(excel_file, nodes_df)
    
    # Save to CSV
    nodes_df.to_csv('nodes.csv', index=False)
    edges_df.to_csv('edges.csv', index=False)
    
    print("\n" + "=" * 70)
    print("✓ SUCCESS!")
    print("=" * 70)
    print(f"  • Saved nodes.csv with {len(nodes_df)} nodes")
    print(f"  • Saved edges.csv with {len(edges_df)} edges")
    print(f"  • Includes ALL {len(nodes_df[nodes_df['id'].str.startswith('MDRM_')])} MDRMs from catalog")
    print("\n  Visual indicators:")
    print("  • ✓ Red nodes = MDRMs with full lineage")
    print("  • ⊘ Gray nodes = Catalog-only MDRMs")
    print("  • Solid lines = Lineage connections")
    print("  • Dashed lines = Catalog-only connections")
    print("\n  Next step: Run 'python3 sccl_unified_view.py' to generate visualization")


if __name__ == '__main__':
    main()
