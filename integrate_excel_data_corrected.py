"""
Integrate corrected FR2590 Data Library into visualization.
Reads from FR2590_Data_Library_COMPLETE_CORRECTED.xlsx with MASTER_LINEAGE sheet.
"""

import pandas as pd
import numpy as np
import os

def create_nodes_from_corrected_excel(excel_file='FR2590_Data_Library_COMPLETE_CORRECTED.xlsx'):
    """
    Create nodes from the corrected Excel file using MASTER_LINEAGE sheet.
    Optimized for speed with progress indicators.
    """
    print(f"📖 Reading corrected Excel file: {excel_file}")
    
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    # Read all sheets at once for efficiency
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
    
    # 1b. DATABASE/TABLE NODES (for database view layer)
    print("    → Database tables", end="", flush=True)
    # Group by Source_System and Source_Table
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
                'title': f"Database Table: {table_name}\nSource System: {source_sys}\nContains source fields for Atomic CDEs"
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
            table = str(row['Source_Table']).strip() if pd.notna(row['Source_Table']) else 'Unknown'
            
            nodes_list.append({
                'id': f"Atomic_{atomic_id}",
                'label': f"{atomic_id}\n{atomic_name}",
                'group': 'Atomic',
                'data_element': atomic_name,
                'source_system': source,
                'source_table': table,
                'title': f"Atomic CDE: {atomic_name}\nID: {atomic_id}\nType: {data_type}\nSource: {source}\nTable: {table}"
            })
    print(" ✓")
    
    # 3. TRANSFORMATION LOGIC NODES
    print("    → Transformations", end="", flush=True)
    transforms = master_df[['Transform_ID', 'Transform_Type', 'Transform_Logic', 'Enriched_CDE_Name']].drop_duplicates()
    for _, row in transforms.iterrows():
        if pd.notna(row['Transform_ID']):
            transform_id = str(row['Transform_ID']).strip()
            transform_type = str(row['Transform_Type']).strip() if pd.notna(row['Transform_Type']) else 'Unknown'
            transform_logic = str(row['Transform_Logic']).strip() if pd.notna(row['Transform_Logic']) else 'N/A'
            enriched_name = str(row['Enriched_CDE_Name']).strip() if pd.notna(row['Enriched_CDE_Name']) else transform_id
            
            nodes_list.append({
                'id': f"Logic_{transform_id}",
                'label': f"{transform_id}\n{enriched_name}",
                'group': 'Logic',
                'data_element': enriched_name,
                'title': f"Transformation: {enriched_name}\nID: {transform_id}\nType: {transform_type}\nLogic: {transform_logic}"
            })
    print(" ✓")
    
    # 4. ENRICHED CDE NODES (CDEs after transformation)
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
                'title': f"CDE: {cde_name}\nID: {cde_id}\nEnriched from transformation"
            })
    print(" ✓")
    
    # 5. MDRM NODES - Include all from catalog, not just those in MASTER_LINEAGE
    print("    → MDRMs", end="", flush=True)
    # First add MDRMs from MASTER_LINEAGE
    mdrm_data = master_df[['MDRM_Code', 'MDRM_Name', 'Schedule']].drop_duplicates()
    mdrm_codes_added = set()
    
    for _, row in mdrm_data.iterrows():
        if pd.notna(row['MDRM_Code']):
            mdrm_code = str(row['MDRM_Code']).strip()
            mdrm_name = str(row['MDRM_Name']).strip() if pd.notna(row['MDRM_Name']) else mdrm_code
            schedule = str(row['Schedule']).strip() if pd.notna(row['Schedule']) else 'Unknown'
            
            # Get additional info from MDRM_CATALOG
            mdrm_info = mdrm_catalog[mdrm_catalog['MDRM_Code'] == mdrm_code]
            if not mdrm_info.empty:
                formula = mdrm_info.iloc[0].get('Formula_Logic', 'N/A')
                business_def = mdrm_info.iloc[0].get('Business_Definition', 'N/A')
            else:
                formula = 'N/A'
                business_def = 'N/A'
            
            nodes_list.append({
                'id': f"MDRM_{mdrm_code}",
                'label': f"{mdrm_code}\n{mdrm_name}",
                'group': 'Report',
                'data_element': mdrm_name,
                'title': f"MDRM: {mdrm_name}\nCode: {mdrm_code}\nSchedule: {schedule}\nFormula: {formula}\nDefinition: {business_def}"
            })
            mdrm_codes_added.add(mdrm_code)
    
    # Add MDRMs from catalog that aren't in MASTER_LINEAGE
    for _, row in mdrm_catalog.iterrows():
        mdrm_code = str(row['MDRM_Code']).strip()
        if mdrm_code not in mdrm_codes_added:
            mdrm_name = str(row['Data_Element_Name']).strip() if pd.notna(row['Data_Element_Name']) else mdrm_code
            schedule = str(row['Schedule']).strip() if pd.notna(row['Schedule']) else 'Unknown'
            formula = str(row['Formula_Logic']).strip() if pd.notna(row['Formula_Logic']) else 'N/A'
            business_def = str(row['Business_Definition']).strip() if pd.notna(row['Business_Definition']) else 'N/A'
            
            nodes_list.append({
                'id': f"MDRM_{mdrm_code}",
                'label': f"{mdrm_code}\n{mdrm_name}",
                'group': 'Report',
                'data_element': mdrm_name,
                'title': f"MDRM: {mdrm_name}\nCode: {mdrm_code}\nSchedule: {schedule}\nFormula: {formula}\nDefinition: {business_def}"
            })
            mdrm_codes_added.add(mdrm_code)
    print(" ✓")
    
    # 6. SCHEDULE NODES - Include all from catalog
    print("    → Schedules", end="", flush=True)
    schedules_from_master = set(master_df['Schedule'].dropna().unique())
    schedules_from_catalog = set(mdrm_catalog['Schedule'].dropna().unique())
    all_schedules = schedules_from_master.union(schedules_from_catalog)
    
    for schedule in all_schedules:
        if pd.notna(schedule) and str(schedule).strip():
            schedule_id = f"Schedule_{str(schedule).strip()}"
            # Get schedule info from SCHEDULE_MAP
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
        'title': 'FR 2590 Final Regulatory Report Submission\nContains all schedules and MDRMs'
    })
    print(" ✓")
    
    nodes_df = pd.DataFrame(nodes_list)
    print(f"\n  ✅ Created {len(nodes_df)} nodes total:")
    print(f"  Source: {len(nodes_df[nodes_df['group'] == 'Source'])}")
    print(f"  Atomic: {len(nodes_df[nodes_df['group'] == 'Atomic'])}")
    print(f"  Logic: {len(nodes_df[nodes_df['group'] == 'Logic'])}")
    print(f"  CDE: {len(nodes_df[nodes_df['group'] == 'CDE'])}")
    print(f"  MDRM: {len(nodes_df[nodes_df['id'].str.startswith('MDRM_', na=False)])}")
    print(f"  (Total MDRMs from catalog: {len(mdrm_codes_added)})")
    print(f"  Schedule: {len(nodes_df[nodes_df['id'].str.startswith('Schedule_', na=False)])}")
    print(f"  Final Report: 1")
    
    return nodes_df


def create_edges_from_corrected_excel(excel_file='FR2590_Data_Library_COMPLETE_CORRECTED.xlsx', nodes_df=None):
    """
    Create edges from the corrected Excel file using MASTER_LINEAGE sheet.
    Optimized for speed with progress indicators.
    """
    print(f"\n🔗 Creating edges from lineage data...")
    
    master_df = pd.read_excel(excel_file, sheet_name='MASTER_LINEAGE')
    
    edges_list = []
    total_rows = len(master_df)
    progress_interval = max(1, total_rows // 10)  # Show progress every 10%
    
    for idx, row in master_df.iterrows():
        # Show progress
        if idx % progress_interval == 0:
            progress = int((idx / total_rows) * 100)
            print(f"  Processing... {progress}%", end="\r", flush=True)
        # 1. SOURCE → DATABASE TABLE (for database view)
        if pd.notna(row['Source_System']) and pd.notna(row['Source_Table']):
            source_id = f"Source_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}"
            db_id = f"DB_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}_{str(row['Source_Table']).strip()}"
            # Only add if not already in edges_list
            if not any(e['source'] == source_id and e['target'] == db_id for e in edges_list):
                edges_list.append({
                    'source': source_id,
                    'target': db_id,
                    'label': 'Contains',
                    'layer': 'database'
                })
        
        # 1b. DATABASE TABLE → ATOMIC CDE (for database view)
        if pd.notna(row['Source_System']) and pd.notna(row['Source_Table']) and pd.notna(row['Atomic_CDE_ID']):
            db_id = f"DB_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}_{str(row['Source_Table']).strip()}"
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            edges_list.append({
                'source': db_id,
                'target': atomic_id,
                'label': 'Extracts',
                'layer': 'database'
            })
        
        # 1c. SOURCE → ATOMIC CDE (standard view)
        if pd.notna(row['Source_System']) and pd.notna(row['Atomic_CDE_ID']):
            source_id = f"Source_{str(row['Source_System']).replace(' ', '_').replace('/', '_')}"
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            edges_list.append({
                'source': source_id,
                'target': atomic_id,
                'label': 'Extracts',
                'layer': 'standard'
            })
        
        # 2. ATOMIC CDE → TRANSFORMATION
        if pd.notna(row['Atomic_CDE_ID']) and pd.notna(row['Transform_ID']):
            atomic_id = f"Atomic_{str(row['Atomic_CDE_ID']).strip()}"
            transform_id = f"Logic_{str(row['Transform_ID']).strip()}"
            edges_list.append({
                'source': atomic_id,
                'target': transform_id,
                'label': 'Input'
            })
        
        # 3. TRANSFORMATION → ENRICHED CDE
        if pd.notna(row['Transform_ID']) and pd.notna(row['Enriched_CDE_ID']):
            transform_id = f"Logic_{str(row['Transform_ID']).strip()}"
            enriched_id = f"CDE_{str(row['Enriched_CDE_ID']).strip()}"
            edges_list.append({
                'source': transform_id,
                'target': enriched_id,
                'label': 'Output'
            })
        
        # 4. ENRICHED CDE → MDRM
        if pd.notna(row['Enriched_CDE_ID']) and pd.notna(row['MDRM_Code']):
            enriched_id = f"CDE_{str(row['Enriched_CDE_ID']).strip()}"
            mdrm_id = f"MDRM_{str(row['MDRM_Code']).strip()}"
            edges_list.append({
                'source': enriched_id,
                'target': mdrm_id,
                'label': 'Feeds Into'
            })
        
        # 5. MDRM → SCHEDULE
        if pd.notna(row['MDRM_Code']) and pd.notna(row['Schedule']):
            mdrm_id = f"MDRM_{str(row['MDRM_Code']).strip()}"
            schedule_id = f"Schedule_{str(row['Schedule']).strip()}"
            edges_list.append({
                'source': mdrm_id,
                'target': schedule_id,
                'label': 'Belongs To'
            })
    
    # Also add MDRM → Schedule connections from MDRM_CATALOG for MDRMs not in MASTER_LINEAGE
    mdrm_catalog = pd.read_excel(excel_file, sheet_name='MDRM_CATALOG')
    for _, row in mdrm_catalog.iterrows():
        if pd.notna(row['MDRM_Code']) and pd.notna(row['Schedule']):
            mdrm_id = f"MDRM_{str(row['MDRM_Code']).strip()}"
            schedule_id = f"Schedule_{str(row['Schedule']).strip()}"
            # Only add if not already in edges_list
            if not any(e['source'] == mdrm_id and e['target'] == schedule_id for e in edges_list):
                edges_list.append({
                    'source': mdrm_id,
                    'target': schedule_id,
                    'label': 'Belongs To'
                })
    
    # 6. SCHEDULE → FINAL REPORT - Connect all schedules from both sources
    schedules_from_master = set(master_df['Schedule'].dropna().unique())
    mdrm_catalog = pd.read_excel(excel_file, sheet_name='MDRM_CATALOG')
    schedules_from_catalog = set(mdrm_catalog['Schedule'].dropna().unique())
    all_schedules = schedules_from_master.union(schedules_from_catalog)
    
    for schedule in all_schedules:
        if pd.notna(schedule) and str(schedule).strip():
            schedule_id = f"Schedule_{str(schedule).strip()}"
            # Only add if not already in edges_list
            if not any(e['source'] == schedule_id and e['target'] == 'FR2590_Final_Report' for e in edges_list):
                edges_list.append({
                    'source': schedule_id,
                    'target': 'FR2590_Final_Report',
                    'label': 'Populates'
                })
    
    print(f"  Processing... 100%")  # Final progress update
    
    edges_df = pd.DataFrame(edges_list)
    
    # Remove duplicates
    edges_df = edges_df.drop_duplicates(subset=['source', 'target'])
    
    print(f"\n  ✅ Created {len(edges_df)} edges total")
    print(f"  Extracts (Source→Atomic): {len(edges_df[edges_df['label'] == 'Extracts'])}")
    print(f"  Input (Atomic→Transform): {len(edges_df[edges_df['label'] == 'Input'])}")
    print(f"  Output (Transform→CDE): {len(edges_df[edges_df['label'] == 'Output'])}")
    print(f"  Feeds Into (CDE→MDRM): {len(edges_df[edges_df['label'] == 'Feeds Into'])}")
    print(f"  Belongs To (MDRM→Schedule): {len(edges_df[edges_df['label'] == 'Belongs To'])}")
    print(f"  Populates (Schedule→Report): {len(edges_df[edges_df['label'] == 'Populates'])}")
    
    return edges_df


def main():
    """Main function to generate nodes and edges from corrected Excel file."""
    excel_file = 'FR2590_Data_Library_COMPLETE_CORRECTED.xlsx'
    
    print("=" * 60)
    print("INTEGRATING CORRECTED FR2590 DATA LIBRARY")
    print("=" * 60)
    
    # Create nodes
    nodes_df = create_nodes_from_corrected_excel(excel_file)
    
    # Create edges
    edges_df = create_edges_from_corrected_excel(excel_file, nodes_df)
    
    # Save to CSV
    nodes_df.to_csv('nodes.csv', index=False)
    edges_df.to_csv('edges.csv', index=False)
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS!")
    print("=" * 60)
    print(f"  • Saved nodes.csv with {len(nodes_df)} nodes")
    print(f"  • Saved edges.csv with {len(edges_df)} edges")
    print("\n  Next step: Run 'python3 sccl_unified_view.py' to generate visualization")


if __name__ == '__main__':
    main()
