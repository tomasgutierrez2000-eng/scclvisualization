"""
SCCL Unified Data Lineage View
Single comprehensive view showing: Source → Atomic CDE → Transformation → CDE → MDRM → Schedule → FR 2590 Report
With interactive highlighting, filters, and improved readability
"""

import pandas as pd
from pyvis.network import Network
import webbrowser
import os
import sys

def create_unified_lineage_view():
    """Create a single unified view of the complete data lineage."""
    
    # Load data
    try:
        nodes_df = pd.read_csv('nodes.csv')
        edges_df = pd.read_csv('edges.csv')
    except FileNotFoundError:
        print("❌ Error: nodes.csv and edges.csv not found.")
        print("   Please run 'python3 integrate_excel_data.py' first.")
        sys.exit(1)
    
    print("=" * 60)
    print("Creating Unified SCCL Data Lineage View")
    print("=" * 60)
    
    # Create network
    net = Network(
        height='100vh',
        width='100%',
        bgcolor='#0d1117',
        font_color='#e6edf3',
        directed=True,
        filter_menu=True,
        cdn_resources='remote'
    )
    
    # Enhanced physics for hierarchical layout - optimized for performance
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "hierarchical": {
                "enabled": true,
                "levelSeparation": 800,
                "nodeSpacing": 500,
                "treeSpacing": 900,
                "blockShifting": true,
                "edgeMinimization": true,
                "parentCentralization": true,
                "direction": "LR",
                "sortMethod": "directed"
            },
            "stabilization": {
                "enabled": true,
                "iterations": 100,
                "updateInterval": 50,
                "fit": false
            },
            "adaptiveTimestep": true,
            "timestep": 0.5,
            "minVelocity": 1.0,
            "maxVelocity": 50,
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 200,
                "springConstant": 0.04,
                "damping": 0.09,
                "avoidOverlap": 0.1
            }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "hideEdgesOnDrag": true,
            "hideEdgesOnZoom": false,
            "selectConnectedEdges": true,
            "zoomView": true,
            "dragView": true,
            "navigationButtons": false,
            "keyboard": {
                "enabled": true,
                "speed": {
                    "x": 10,
                    "y": 10,
                    "zoom": 0.02
                },
                "bindToWindow": true
            },
            "multiselect": false,
            "zoomSpeed": 1.2,
            "hoverConnectedEdges": false
        },
        "nodes": {
            "font": {
                "size": 13,
                "face": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                "color": "#e6edf3"
            },
            "borderWidth": 2.5,
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10,
                "x": 2,
                "y": 2
            },
            "scaling": {
                "min": 8,
                "max": 50,
                "label": {
                    "enabled": true,
                    "min": 8,
                    "max": 20
                }
            }
        },
        "edges": {
            "smooth": {
                "type": "continuous",
                "roundness": 0.5
            },
            "font": {
                "size": 11,
                "face": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            },
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.3)"
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 1.3
                }
            },
            "width": 2.5
        }
    }
    """)
    
    # Color mapping
    color_map = {
        'Source': '#238636',
        'Atomic': '#6e7681',
        'Logic': '#1f6feb',
        'CDE': '#d29922',
        'Report': '#da3633',
    }
    
    # Count nodes by group
    node_counts = nodes_df['group'].value_counts().to_dict()
    
    # Get schedule list for filters
    schedule_nodes = nodes_df[nodes_df['id'].str.startswith('Schedule_', na=False)]
    schedule_list = [s.replace('Schedule_', '').replace('_', '-') for s in schedule_nodes['id'].values]
    
    # Add nodes with proper grouping and styling
    print("\nAdding nodes to visualization...")
    
    # 1. SOURCE NODES
    source_nodes = nodes_df[nodes_df['group'] == 'Source']
    for _, row in source_nodes.iterrows():
        # Simplify label for readability
        label = str(row['label']).replace('Source_', '').replace('_', ' ')
        # Simplify title
        simple_title = str(row['label']).replace('Source_', '').replace('_', ' ')
        
        net.add_node(
            row['id'],
            label=label,
            title=simple_title,
            color=color_map['Source'],
            shape='ellipse',
            size=35,
            font={'size': 15, 'color': '#ffffff'},
            borderWidth=3,
            scaling={'min': 20, 'max': 50, 'label': {'enabled': True, 'min': 10, 'max': 18}}
        )
    
    # 2. ATOMIC CDE NODES
    atomic_nodes = nodes_df[nodes_df['group'] == 'Atomic']
    for _, row in atomic_nodes.iterrows():
        # Extract just the name from data_element or label
        if pd.notna(row.get('data_element')) and str(row['data_element']).strip():
            label = str(row['data_element']).replace('_', ' ')[:32]
        else:
            # Extract from label - take second part after newline
            label_parts = str(row['label']).split('\n')
            if len(label_parts) > 1:
                name = label_parts[1].strip()
                label = name.replace('_', ' ')[:32]
            else:
                # Fallback: clean the label
                label = str(row['label']).replace('Atomic_', '').replace('CDE_', '').replace('_', ' ')[:32]
        
        # Count children (outgoing edges to transformations)
        child_count = len(edges_df[edges_df['source'] == row['id']])
        
        # Simplify title - just the name
        simple_title = label
        
        net.add_node(
            row['id'],
            label=label,
            title=simple_title,
            color=color_map['Atomic'],
            shape='box',
            size=32,
            font={'size': 14, 'color': '#ffffff'},
            borderWidth=2.5,
            scaling={'min': 16, 'max': 45, 'label': {'enabled': True, 'min': 9, 'max': 16}},
            atomic=True,
            childCount=child_count
        )
    
    # 3. TRANSFORMATION LOGIC NODES
    logic_nodes = nodes_df[nodes_df['group'] == 'Logic']
    for _, row in logic_nodes.iterrows():
        # Extract just the transformation name, remove ID
        if pd.notna(row.get('data_element')) and str(row['data_element']).strip():
            label = str(row['data_element']).replace('_', ' ')[:30]
        else:
            # Extract from label - take second part after newline
            label_parts = str(row['label']).split('\n')
            if len(label_parts) > 1:
                name = label_parts[1].strip()
                label = name.replace('_', ' ')[:30]
            else:
                label = str(row['label']).replace('Logic_', '').replace('_', ' ')[:30]
        # Simplify title
        simple_title = label
        
        net.add_node(
            row['id'],
            label=label,
            title=simple_title,
            color=color_map['Logic'],
            shape='diamond',
            size=36,
            font={'size': 14, 'color': '#ffffff'},
            borderWidth=2.5,
            scaling={'min': 18, 'max': 50, 'label': {'enabled': True, 'min': 9, 'max': 16}}
        )
    
    # 4. CDE NODES (aggregated) - These are derived
    cde_nodes = nodes_df[nodes_df['group'] == 'CDE']
    for _, row in cde_nodes.iterrows():
        # Extract just the name, remove CDE ID
        if pd.notna(row.get('data_element')) and str(row['data_element']).strip():
            label = str(row['data_element']).replace('_', ' ')[:30]
        else:
            # Extract from label - take second part after newline
            label_parts = str(row['label']).split('\n')
            if len(label_parts) > 1:
                name = label_parts[1].strip()
                label = name.replace('_', ' ')[:30]
            else:
                # Clean the label
                label = str(row['label']).replace('CDE_', '').replace('_', ' ')[:30]
        
        # Count children (outgoing edges to MDRMs)
        child_count = len(edges_df[edges_df['source'] == row['id']])
        
        # Simplify title - just the name
        simple_title = label
        
        net.add_node(
            row['id'],
            label=label,
            title=simple_title,
            color=color_map['CDE'],
            shape='box',
            size=28,
            font={'size': 13, 'color': '#ffffff'},
            borderWidth=2.5,
            scaling={'min': 14, 'max': 40, 'label': {'enabled': True, 'min': 8, 'max': 15}},
            atomic=False,
            childCount=child_count
        )
    
    # 5. MDRM NODES (Report level) - These are derived
    mdrm_nodes = nodes_df[nodes_df['id'].str.startswith('MDRM_', na=False)]
    for _, row in mdrm_nodes.iterrows():
        # Extract just the data element name, remove MDRM code
        if pd.notna(row.get('data_element')):
            label = str(row['data_element'])[:30]
        else:
            label_parts = str(row['label']).split('\n')
            if len(label_parts) > 1:
                # Take the second part (name)
                label = label_parts[1].strip()[:30]
            else:
                label = str(row['label']).replace('MDRM_', '').replace('SCCL_', '').replace('_', ' ')[:30]
        
        # Count children (outgoing edges to schedules)
        child_count = len(edges_df[edges_df['source'] == row['id']])
        
        # Simplify title - just the name
        simple_title = label
        
        net.add_node(
            row['id'],
            label=label,
            title=simple_title,
            color=color_map['Report'],
            shape='box',
            size=26,
            font={'size': 12, 'color': '#ffffff'},
            borderWidth=2,
            scaling={'min': 12, 'max': 38, 'label': {'enabled': True, 'min': 8, 'max': 14}},
            atomic=False,
            childCount=child_count
        )
    
    # 6. SCHEDULE NODES (aggregated report schedules)
    for _, row in schedule_nodes.iterrows():
        # Simplify title
        simple_title = str(row['label']).replace('Schedule ', '').split('\n')[0] if '\n' in str(row['label']) else str(row['label'])
        
        net.add_node(
            row['id'],
            label=row['label'],
            title=simple_title,
            color='#bc8cff',
            shape='box',
            size=40,
            font={'size': 15, 'color': '#ffffff', 'bold': True},
            borderWidth=4,
            scaling={'min': 25, 'max': 60, 'label': {'enabled': True, 'min': 12, 'max': 20}}
        )
    
    # 7. FINAL REPORT ENDPOINT - Make it highly visible
    net.add_node(
        'FR2590_Final_Report',
        label='FR 2590\nFinal Report\nSubmission',
        title='FR 2590 Final Report',
        color={'background': '#f85149', 'border': '#ff6b6b', 'highlight': {'background': '#ff4444', 'border': '#ff0000'}},
        shape='box',
        size=70,
        font={'size': 22, 'color': '#ffffff', 'bold': True},
        borderWidth=6,
        shadow={'enabled': True, 'color': 'rgba(248, 81, 73, 0.8)', 'size': 20, 'x': 3, 'y': 3},
        scaling={'min': 50, 'max': 90, 'label': {'enabled': True, 'min': 16, 'max': 28}}
    )
    
    # 8. DATABASE/TABLE NODES (for database view layer - hidden by default)
    db_nodes = nodes_df[nodes_df['group'] == 'Database']
    for _, row in db_nodes.iterrows():
            # Simplify title
            simple_title = str(row['label']).split('\n')[-1] if '\n' in str(row['label']) else str(row['label'])
            
            net.add_node(
            row['id'],
            label=row['label'],
            title=simple_title,
            color='#6e7681',
            shape='box',
            size=30,
            font={'size': 12, 'color': '#ffffff'},
            borderWidth=2,
            hidden=True,  # Hidden by default, shown when database layer is toggled
            scaling={'min': 18, 'max': 40, 'label': {'enabled': True, 'min': 9, 'max': 14}}
        )
    
    # Add edges - NO LABELS for cleaner view
    print("Adding edges (without labels for cleaner view)...")
    
    # Track edge types for legend
    edge_types = set()
    
    for _, row in edges_df.iterrows():
        edge_label = str(row.get('label', '')) if pd.notna(row.get('label')) else ''
        if edge_label and edge_label != 'nan':
            edge_types.add(edge_label)
        # Check if this is a database layer edge
        is_db_layer = str(row.get('layer', 'standard')).strip() == 'database'
        
        # Add edge without label parameter - pyvis will not add label
        # Start with thinner base width (will be adjusted dynamically)
        net.add_edge(
            row['source'],
            row['target'],
            arrows='to',
            color='#8b949e',
            width=1.0,  # Thinner base width
            smooth={'type': 'continuous', 'roundness': 0.5},
            hidden=is_db_layer  # Hide database layer edges by default
        )
    
    # Connect all schedules to final report
    for schedule_id in schedule_nodes['id'].values:
        net.add_edge(
            schedule_id,
            'FR2590_Final_Report',
            arrows='to',
            color='#f85149',
            width=2.5,  # Thinner base, will be adjusted dynamically
            smooth={'type': 'continuous', 'roundness': 0.5}
        )
        edge_types.add('Populates')
    
    # Save the network
    net.save_graph('_unified_view.html')
    
    # Add interactive highlighting, filters, and color key
    print("Adding interactivity, filters, and color key...")
    
    with open('_unified_view.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Create comprehensive control panel
    schedule_options = ''.join([f'<option value="{s}">{s}</option>' for s in sorted(set(schedule_list))])
    
    control_panel = f"""
    <div id="controlPanel" style="position: absolute; top: 15px; right: 15px; background: linear-gradient(135deg, rgba(13, 17, 23, 0.98) 0%, rgba(22, 27, 34, 0.98) 100%); 
                border: 1px solid #30363d; border-radius: 12px; padding: 20px; 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 12px; color: #e6edf3; 
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05) inset; 
                z-index: 1000; width: 280px;
                max-height: 90vh; overflow-y: auto; backdrop-filter: blur(10px); overflow-x: hidden;">
        <div style="font-weight: 700; margin-bottom: 18px; font-size: 18px; color: #f0f6fc; 
                    border-bottom: 2px solid #30363d; padding-bottom: 12px; letter-spacing: -0.3px;">
            🎛️ Controls
        </div>
        
        <!-- Database View Toggle -->
        <div style="margin-bottom: 16px;">
            <label style="display: flex; align-items: center; cursor: pointer; padding: 8px 0; transition: opacity 0.2s;" 
                   onmouseover="this.style.opacity='0.8'" 
                   onmouseout="this.style.opacity='1'">
                <input type="checkbox" id="databaseViewToggle" style="margin-right: 10px; cursor: pointer; width: 16px; height: 16px; accent-color: #58a6ff;"
                       onchange="toggleDatabaseView()">
                <span style="font-size: 12px; color: #c9d1d9;">Database View</span>
            </label>
        </div>
        
        <!-- Zoom Controls -->
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(48, 54, 61, 0.5);">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 6px;">
                <button onclick="network.moveTo({{scale: network.getScale() * 1.3}})" 
                        style="padding: 8px; background: rgba(31, 111, 235, 0.1); 
                               border: 1px solid rgba(31, 111, 235, 0.3); border-radius: 6px; color: #58a6ff; font-weight: 500; cursor: pointer; 
                               font-size: 11px; transition: all 0.2s;" 
                        onmouseover="this.style.background='rgba(31, 111, 235, 0.2)'; this.style.borderColor='rgba(31, 111, 235, 0.5)'" 
                        onmouseout="this.style.background='rgba(31, 111, 235, 0.1)'; this.style.borderColor='rgba(31, 111, 235, 0.3)'">Zoom In</button>
                <button onclick="network.moveTo({{scale: network.getScale() * 0.7}})" 
                        style="padding: 8px; background: rgba(31, 111, 235, 0.1); 
                               border: 1px solid rgba(31, 111, 235, 0.3); border-radius: 6px; color: #58a6ff; font-weight: 500; cursor: pointer; 
                               font-size: 11px; transition: all 0.2s;"
                        onmouseover="this.style.background='rgba(31, 111, 235, 0.2)'; this.style.borderColor='rgba(31, 111, 235, 0.5)'" 
                        onmouseout="this.style.background='rgba(31, 111, 235, 0.1)'; this.style.borderColor='rgba(31, 111, 235, 0.3)'">Zoom Out</button>
            </div>
            <button onclick="network.fit({{animation: true}})" 
                    style="width: 100%; padding: 8px; background: rgba(35, 134, 54, 0.1); 
                           border: 1px solid rgba(35, 134, 54, 0.3); border-radius: 6px; color: #3fb950; font-weight: 500; cursor: pointer; 
                           font-size: 11px; transition: all 0.2s;"
                    onmouseover="this.style.background='rgba(35, 134, 54, 0.2)'; this.style.borderColor='rgba(35, 134, 54, 0.5)'" 
                    onmouseout="this.style.background='rgba(35, 134, 54, 0.1)'; this.style.borderColor='rgba(35, 134, 54, 0.3)'">Fit to Screen</button>
        </div>
        
        <!-- Search Filter -->
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(48, 54, 61, 0.5);">
            <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #c9d1d9; font-size: 11px; text-transform: uppercase; opacity: 0.8;">Search</label>
            <input type="text" id="nodeSearch" placeholder="Search nodes..." 
                   style="width: 100%; padding: 8px 10px; background: rgba(22, 27, 34, 0.6); 
                          border: 1px solid rgba(48, 54, 61, 0.6); border-radius: 6px; color: #e6edf3; 
                          font-size: 12px; box-sizing: border-box; transition: all 0.2s; outline: none;"
                   onfocus="this.style.borderColor='#58a6ff'; this.style.background='rgba(22, 27, 34, 0.8)';"
                   onblur="this.style.borderColor='rgba(48, 54, 61, 0.6)'; this.style.background='rgba(22, 27, 34, 0.6)';">
        </div>
        
        <!-- Node Type Filter -->
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(48, 54, 61, 0.5);">
            <label style="display: block; margin-bottom: 10px; font-weight: 500; color: #c9d1d9; font-size: 11px; text-transform: uppercase; opacity: 0.8;">Node Types</label>
            <div style="display: flex; flex-direction: column; gap: 6px;">
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="Source" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #238636;">
                    <span style="font-size: 12px; color: #c9d1d9;">Source</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="Atomic" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #6e7681;">
                    <span style="font-size: 12px; color: #c9d1d9;">Atomic CDE</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="Logic" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #1f6feb;">
                    <span style="font-size: 12px; color: #c9d1d9;">Transform</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="CDE" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #d29922;">
                    <span style="font-size: 12px; color: #c9d1d9;">CDE</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="Report" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #da3633;">
                    <span style="font-size: 12px; color: #c9d1d9;">MDRM</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer; padding: 6px 0; transition: opacity 0.2s;" 
                       onmouseover="this.style.opacity='0.7'" 
                       onmouseout="this.style.opacity='1'">
                    <input type="checkbox" class="typeFilter" value="Schedule" checked style="margin-right: 10px; cursor: pointer; width: 14px; height: 14px; accent-color: #bc8cff;">
                    <span style="font-size: 12px; color: #c9d1d9;">Schedule</span>
                </label>
            </div>
        </div>
        
        <!-- Schedule Filter -->
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(48, 54, 61, 0.5);">
            <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #c9d1d9; font-size: 11px; text-transform: uppercase; opacity: 0.8;">Schedule</label>
            <select id="scheduleFilter" style="width: 100%; padding: 8px 10px; background: rgba(22, 27, 34, 0.6); 
                   border: 1px solid rgba(48, 54, 61, 0.6); border-radius: 6px; color: #e6edf3; font-size: 12px; 
                   cursor: pointer; transition: all 0.2s; outline: none;"
                   onfocus="this.style.borderColor='#58a6ff'; this.style.background='rgba(22, 27, 34, 0.8)';"
                   onblur="this.style.borderColor='rgba(48, 54, 61, 0.6)'; this.style.background='rgba(22, 27, 34, 0.6)';">
                <option value="all">All Schedules</option>
                {schedule_options}
            </select>
        </div>
        
        <!-- Legend -->
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(48, 54, 61, 0.5);">
            <label style="display: block; margin-bottom: 10px; font-weight: 500; color: #c9d1d9; font-size: 11px; text-transform: uppercase; opacity: 0.8;">Legend</label>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color_map['Source']}; border-radius: 50%; margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">Source</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color_map['Atomic']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">Atomic CDE</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color_map['Logic']}; transform: rotate(45deg); margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">Transform</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color_map['CDE']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">CDE</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color_map['Report']}; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">MDRM</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: #bc8cff; border-radius: 2px; margin-right: 8px;"></div>
                    <span style="font-size: 11px; color: #8b949e;">Schedule</span>
                </div>
            </div>
        </div>
        
        <!-- Keyboard Shortcuts & Tips -->
        <div style="margin-bottom: 0;">
            <div style="font-size: 10px; color: #6e7681; line-height: 1.5;">
                <div style="margin-bottom: 3px;">• <kbd style="background: rgba(48, 54, 61, 0.5); padding: 2px 5px; border-radius: 3px; font-size: 9px;">Scroll</kbd> to zoom</div>
                <div style="margin-bottom: 3px;">• <kbd style="background: rgba(48, 54, 61, 0.5); padding: 2px 5px; border-radius: 3px; font-size: 9px;">Click</kbd> to highlight paths</div>
                <div style="margin-bottom: 3px;">• <kbd style="background: rgba(48, 54, 61, 0.5); padding: 2px 5px; border-radius: 3px; font-size: 9px;">Double-click</kbd> to focus</div>
                <div>• <kbd style="background: rgba(48, 54, 61, 0.5); padding: 2px 5px; border-radius: 3px; font-size: 9px;">Drag</kbd> to pan</div>
            </div>
        </div>
    </div>
    
    <!-- Loading Indicator -->
    <div id="loadingIndicator" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
                                      background: rgba(13, 17, 23, 0.98); z-index: 2000; display: flex; 
                                      align-items: center; justify-content: center; flex-direction: column;">
        <div style="background: rgba(22, 27, 34, 0.9); border: 1px solid #30363d; border-radius: 12px; 
                    padding: 40px 60px; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);">
            <div style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #f0f6fc;">
                🚀 Loading Visualization
            </div>
            <div style="font-size: 13px; color: #8b949e; margin-bottom: 20px;">
                Preparing your data lineage view...
            </div>
            <div style="width: 200px; height: 4px; background: rgba(48, 54, 61, 0.5); border-radius: 2px; overflow: hidden;">
                <div style="width: 0%; height: 100%; background: linear-gradient(90deg, #58a6ff, #3fb950); 
                            border-radius: 2px; animation: loading 2s ease-in-out infinite;" id="loadingBar"></div>
            </div>
        </div>
    </div>
    <style>
        @keyframes loading {{
            0% {{ width: 0%; }}
            50% {{ width: 70%; }}
            100% {{ width: 100%; }}
        }}
    </style>
"""
    
    # Add interactive JavaScript with filters
    interactive_js = """
    <script>
        var originalNodes = null;
        var originalEdges = null;
        var databaseViewActive = false;
        var baseEdgeWidth = 3;
        var isInitialized = false;
        var nodeCache = {}; // Cache node lookups
        var edgeCache = {}; // Cache edge lookups
        
        // Hide loading indicator when visualization is ready
        function hideLoadingIndicator() {
            var loader = document.getElementById('loadingIndicator');
            if (loader) {
                loader.style.opacity = '0';
                loader.style.transition = 'opacity 0.3s';
                setTimeout(function() {
                    loader.style.display = 'none';
                    loader.remove(); // Remove from DOM completely
                }, 400);
            }
        }
        
        // Force hide loading after max 8 seconds (fallback)
        setTimeout(function() {
            hideLoadingIndicator();
        }, 8000);
        
        function getNodeGroup(nodeId) {
            if (nodeId.startsWith('Source_')) return 'Source';
            if (nodeId.startsWith('DB_')) return 'Database';
            if (nodeId.startsWith('Atomic_')) return 'Atomic';
            if (nodeId.startsWith('Logic_')) return 'Logic';
            if (nodeId.startsWith('CDE_')) return 'CDE';
            if (nodeId.startsWith('MDRM_')) return 'Report';
            if (nodeId.startsWith('Schedule_')) return 'Schedule';
            if (nodeId === 'FR2590_Final_Report') return 'Report';
            return 'Other';
        }
        
        function applyFilters() {
            if (!originalNodes) {
                originalNodes = nodes.get({returnType: 'Object'});
                originalEdges = edges.get({returnType: 'Object'});
            }
            
            var searchTerm = document.getElementById('nodeSearch').value.toLowerCase();
            var selectedTypes = Array.from(document.querySelectorAll('.typeFilter:checked')).map(cb => cb.value);
            var selectedSchedule = document.getElementById('scheduleFilter').value;
            
            var updateNodes = [];
            
            // Use cached nodes if available
            if (!nodeCache.allNodes) {
                nodeCache.allNodes = nodes.get();
            }
            var allNodes = nodeCache.allNodes;
            
            allNodes.forEach(function(node) {
                // Cache node group lookup
                if (!nodeCache[node.id]) {
                    nodeCache[node.id] = {
                        group: getNodeGroup(node.id),
                        labelLower: (node.label || '').toLowerCase(),
                        titleLower: (node.title || '').toLowerCase(),
                        idLower: node.id.toLowerCase()
                    };
                }
                var cached = nodeCache[node.id];
                
                // Check type filter
                var typeMatch = selectedTypes.includes(cached.group) || cached.group === 'Other';
                
                // Check search filter
                var searchMatch = !searchTerm || 
                    cached.labelLower.includes(searchTerm) || 
                    cached.titleLower.includes(searchTerm) || 
                    cached.idLower.includes(searchTerm);
                
                // Check schedule filter
                var scheduleMatch = true;
                if (selectedSchedule !== 'all' && cached.group === 'Report' && node.id.startsWith('MDRM_')) {
                    var nodeSchedule = '';
                    if (node.title) {
                        var scheduleMatchResult = node.title.match(/Schedule: ([^\\n]+)/);
                        if (scheduleMatchResult) nodeSchedule = scheduleMatchResult[1].replace(/-/g, '_');
                    }
                    scheduleMatch = nodeSchedule === selectedSchedule.replace(/-/g, '_') || selectedSchedule === 'all';
                }
                
                var shouldShow = typeMatch && searchMatch && scheduleMatch;
                
                updateNodes.push({
                    id: node.id,
                    hidden: !shouldShow,
                    opacity: shouldShow ? 1.0 : 0.0
                });
            });
            
            nodes.update(updateNodes);
        }
        
        // Early loader hide if network is ready quickly
        setTimeout(function() {
            if (typeof network !== 'undefined' && network.body && network.body.nodes) {
                console.log("Network initialized - hiding loader early");
                hideLoadingIndicator();
            }
        }, 2000);
        
        // Wait for network to be ready
        setTimeout(function() {
            if (typeof network !== 'undefined') {
                // Enhanced node selection highlighting with metadata display
                network.on("selectNode", function (params) {
                    if (params.nodes.length > 0) {
                        var selectedNode = params.nodes[0];
                        var selectedNodeData = nodes.get(selectedNode);
                        var connectedNodes = new Set();
                        var connectedEdges = new Set();
                        
                        // Get all connected nodes (both incoming and outgoing)
                        var allEdges = edges.get();
                        allEdges.forEach(function(edge) {
                            if (edge.from == selectedNode) {
                                connectedNodes.add(edge.to);
                                connectedEdges.add(edge.id);
                            }
                            if (edge.to == selectedNode) {
                                connectedNodes.add(edge.from);
                                connectedEdges.add(edge.id);
                            }
                        });
                        
                        // Show metadata panel for selected node
                        showNodeMetadata(selectedNodeData);
                        
                        // Highlight connected nodes
                        var updateNodes = [];
                        nodes.get().forEach(function(node) {
                            if (node.id == selectedNode) {
                                // Add metadata to label when selected
                                var metadataLabel = node.label || '';
                                if (node.atomic !== undefined) {
                                    var typeLabel = node.atomic ? 'Atomic' : 'Derived';
                                    var childCount = node.childCount || 0;
                                    metadataLabel += '\\n[' + typeLabel + ' | ' + childCount + ' children]';
                                }
                                updateNodes.push({
                                    id: node.id, 
                                    borderWidth: 5, 
                                    borderColor: '#f0f6fc',
                                    label: metadataLabel
                                });
                            } else if (connectedNodes.has(node.id)) {
                                updateNodes.push({id: node.id, opacity: 1.0, borderWidth: 3, borderColor: '#58a6ff'});
                            } else {
                                updateNodes.push({id: node.id, opacity: 0.15});
                            }
                        });
                        
                        var updateEdges = [];
                        edges.get().forEach(function(edge) {
                            if (connectedEdges.has(edge.id) || edge.from == selectedNode || edge.to == selectedNode) {
                                updateEdges.push({id: edge.id, color: '#58a6ff', width: 4, opacity: 1.0});
                            } else {
                                updateEdges.push({id: edge.id, opacity: 0.1});
                            }
                        });
                        
                        nodes.update(updateNodes);
                        edges.update(updateEdges);
                    }
                });
                
                network.on("deselectNode", function (params) {
                    // Hide metadata panel and restore labels
                    hideNodeMetadata();
                    applyFilters(); // Reapply filters to reset
                });
                
                // Function to show node metadata panel
                function showNodeMetadata(nodeData) {
                    var metadataPanel = document.getElementById('nodeMetadataPanel');
                    if (!metadataPanel) {
                        metadataPanel = document.createElement('div');
                        metadataPanel.id = 'nodeMetadataPanel';
                        metadataPanel.style.cssText = 'position: absolute; top: 20px; left: 20px; background: rgba(13, 17, 23, 0.95); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 12px; padding: 16px; font-family: "Inter", sans-serif; font-size: 13px; color: #e6edf3; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4); z-index: 1001; min-width: 250px; max-width: 350px; backdrop-filter: blur(20px); transition: opacity 0.3s;';
                        document.body.appendChild(metadataPanel);
                    }
                    
                    var typeLabel = nodeData.atomic ? 'Atomic' : 'Derived';
                    var childCount = nodeData.childCount || 0;
                    var connectionInfo = nodeConnectionCounts[nodeData.id] || {total: 0};
                    
                    var nodeName = (nodeData.label || nodeData.id).split('\\n')[0]; // Just first line
                    metadataPanel.innerHTML = '<div style="font-weight: 600; margin-bottom: 12px; font-size: 14px; color: #f0f6fc; border-bottom: 1px solid rgba(48, 54, 61, 0.5); padding-bottom: 8px;">' + 
                        nodeName + '</div>' +
                        '<div style="margin-bottom: 6px;"><span style="color: #8b949e;">Type:</span> <span style="color: #58a6ff;">' + typeLabel + '</span></div>' +
                        '<div style="margin-bottom: 6px;"><span style="color: #8b949e;">Children:</span> <span style="color: #58a6ff;">' + childCount + '</span></div>' +
                        '<div><span style="color: #8b949e;">Connections:</span> <span style="color: #58a6ff;">' + connectionInfo.total + '</span></div>';
                    
                    metadataPanel.style.opacity = '1';
                    metadataPanel.style.display = 'block';
                }
                
                function hideNodeMetadata() {
                    var metadataPanel = document.getElementById('nodeMetadataPanel');
                    if (metadataPanel) {
                        metadataPanel.style.opacity = '0';
                        setTimeout(function() {
                            metadataPanel.style.display = 'none';
                        }, 300);
                    }
                }
                
                
                // Setup filter event listeners
                document.getElementById('nodeSearch').addEventListener('input', applyFilters);
                document.querySelectorAll('.typeFilter').forEach(function(cb) {
                    cb.addEventListener('change', applyFilters);
                });
                document.getElementById('scheduleFilter').addEventListener('change', applyFilters);
            }
        }, 1000);
        
        // Add clean, minimal title
        setTimeout(function() {
            var titleDiv = document.createElement('div');
            titleDiv.style.cssText = 'position: absolute; top: 20px; left: 20px; background: rgba(13, 17, 23, 0.95); border: 1px solid rgba(48, 54, 61, 0.6); border-radius: 10px; padding: 14px 18px; font-family: "Inter", sans-serif; font-size: 14px; font-weight: 500; color: #c9d1d9; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3); z-index: 1000; backdrop-filter: blur(10px); letter-spacing: -0.2px;';
            titleDiv.innerHTML = 'SCCL Data Lineage';
            document.body.appendChild(titleDiv);
        }, 500);
        
        // Add double-click to center functionality
        network.on("doubleClick", function (params) {
            if (params.nodes.length > 0) {
                network.focus(params.nodes[0], {
                    scale: 1.5,
                    animation: {
                        duration: 500,
                        easingFunction: "easeInOutQuad"
                    }
                });
            }
        });
        
        // Toggle database view layer
        function toggleDatabaseView() {
            databaseViewActive = document.getElementById('databaseViewToggle').checked;
            var allNodes = nodes.get();
            var allEdges = edges.get();
            var updateNodes = [];
            var updateEdges = [];
            
            // Toggle database nodes
            allNodes.forEach(function(node) {
                if (node.id.startsWith('DB_')) {
                    updateNodes.push({
                        id: node.id,
                        hidden: !databaseViewActive
                    });
                }
            });
            
            // Toggle database edges
            allEdges.forEach(function(edge) {
                if (edge.from && (edge.from.startsWith('DB_') || edge.to && edge.to.startsWith('DB_'))) {
                    updateEdges.push({
                        id: edge.id,
                        hidden: !databaseViewActive
                    });
                }
            });
            
            if (updateNodes.length > 0) nodes.update(updateNodes);
            if (updateEdges.length > 0) edges.update(updateEdges);
        }
        
        // Dynamic zoom adjustments: font sizes, node sizes, edge widths, label visibility, connection counts, clustering
        var lastScale = 1.0;
        var nodeConnectionCounts = {}; // Cache connection counts per node
        var nodeGroups = {}; // Cache node groups for clustering
        var clusteredNodes = {}; // Track which nodes are clustered
        
        // Pre-calculate connection counts for all nodes
        function calculateConnectionCounts() {
            var allNodes = nodes.get();
            var allEdges = edges.get();
            nodeConnectionCounts = {};
            
            allNodes.forEach(function(node) {
                var count = 0;
                var sameTypeCount = 0;
                var nodeGroup = getNodeGroup(node.id);
                
                allEdges.forEach(function(edge) {
                    if (edge.from === node.id || edge.to === node.id) {
                        count++;
                        // Count same-type connections
                        var otherNodeId = edge.from === node.id ? edge.to : edge.from;
                        var otherNode = nodes.get(otherNodeId);
                        if (otherNode) {
                            var otherGroup = getNodeGroup(otherNodeId);
                            if (otherGroup === nodeGroup) {
                                sameTypeCount++;
                            }
                        }
                    }
                });
                
                nodeConnectionCounts[node.id] = {
                    total: count,
                    sameType: sameTypeCount,
                    group: nodeGroup
                };
            });
        }
        
        // Calculate counts on initialization
        setTimeout(function() {
            calculateConnectionCounts();
        }, 1500);
        
        // Throttle zoom updates for better performance
        var zoomTimeout;
        var lastZoomUpdate = 0;
        var isZoomUpdating = false;
        
        network.on("zoom", function (params) {
            if (isZoomUpdating) return; // Skip if already updating
            
            clearTimeout(zoomTimeout);
            var now = Date.now();
            var timeSinceLastUpdate = now - lastZoomUpdate;
            
            // Increase delay for smoother performance
            var delay = timeSinceLastUpdate < 300 ? 150 : 100;
            
            zoomTimeout = setTimeout(function() {
                isZoomUpdating = true;
                var scale = network.getScale();
                lastScale = scale;
                lastZoomUpdate = Date.now();
            
            // Calculate dynamic adjustments based on zoom level
            // Scale < 0.3 = very zoomed out, Scale > 2.0 = very zoomed in
            var fontScale = Math.max(0.5, Math.min(2.0, scale));
            var nodeSizeScale = Math.max(0.6, Math.min(1.5, scale));
            
            // Much thinner edges, especially at extreme zoom levels
            // Very zoomed out (< 0.3): 0.3px, Very zoomed in (> 2.0): 0.5px, Normal: 1px
            var edgeWidth;
            if (scale < 0.3) {
                edgeWidth = 0.3; // Very thin when zoomed out
            } else if (scale > 2.0) {
                edgeWidth = 0.5; // Very thin when zoomed in
            } else {
                edgeWidth = Math.max(0.4, Math.min(1.2, 1.0 / scale)); // Thinner overall
            }
            
            // Determine zoom level behavior (simplified)
            var isZoomedOut = scale < 0.5; // Show counts when zoomed out
            var isZoomedIn = scale >= 0.5; // Show names when zoomed in
            var showDetailedLabels = scale > 0.8; // Show full details when well zoomed in
            
            // Use cached nodes for better performance
            if (!nodeCache.allNodes) {
                nodeCache.allNodes = nodes.get();
            }
            var allNodes = nodeCache.allNodes;
            var updateNodes = [];
            var updateEdges = [];
            
            // Update nodes with simplified logic (no clustering)
            allNodes.forEach(function(node) {
                var baseSize = node.size || 25;
                var baseFontSize = (node.font && node.font.size) || 12;
                
                // Get node metadata
                var connectionInfo = nodeConnectionCounts[node.id] || {total: 0};
                var connectionCount = connectionInfo.total;
                
                // Simplified node display logic
                var newSize = baseSize * nodeSizeScale;
                var newFontSize = Math.max(8, Math.min(20, baseFontSize * fontScale));
                
                // Determine label based on zoom - SIMPLIFIED
                var labelText = '';
                
                if (isZoomedOut) {
                    // When zoomed out, just show connection count
                    labelText = connectionCount > 0 ? connectionCount.toString() : '';
                } else {
                    // When zoomed in, show node label/name
                    if (node.label) {
                        var parts = node.label.split('\\n');
                        labelText = showDetailedLabels ? node.label : parts[0];
                    } else {
                        labelText = node.id.replace(/^(Source_|Atomic_|Logic_|CDE_|MDRM_|Schedule_|DB_)/, '');
                    }
                }
                
                // Always show full label for endpoint
                if (node.id === 'FR2590_Final_Report') {
                    labelText = 'FR 2590';
                    newSize = Math.max(50, newSize);
                    newFontSize = Math.max(14, newFontSize);
                }
                
                updateNodes.push({
                    id: node.id,
                    label: labelText,
                    font: {size: newFontSize},
                    size: newSize
                });
            });
            
            // Simplified edge updates - just update width
            if (!edgeCache.allEdges) {
                edgeCache.allEdges = edges.get();
            }
            edgeCache.allEdges.forEach(function(edge) {
                var width = edgeWidth;
                if (edge.color === '#58a6ff') width = Math.max(1.5, edgeWidth * 2);
                if (edge.color === '#f85149') width = Math.max(2, edgeWidth * 3);
                updateEdges.push({id: edge.id, width: width});
            });
            
            // Batch update for better performance
            if (updateNodes.length > 0) nodes.update(updateNodes);
            if (updateEdges.length > 0) edges.update(updateEdges);
            
            isZoomUpdating = false; // Allow next zoom update
            }, delay);
        });
        
        // Also adjust on drag end (in case zoom changed during drag)
        network.on("dragEnd", function (params) {
            if (typeof lastScale !== 'undefined') {
                network.emit("zoom", {scale: lastScale});
            }
        });
        
        // Hide loading and initialize when stabilization completes
        network.on("stabilizationIterationsDone", function() {
            console.log("Stabilization complete - hiding loader");
            hideLoadingIndicator();
            
            if (!isInitialized) {
                isInitialized = true;
                calculateConnectionCounts();
                // Fit to screen on first load
                setTimeout(function() {
                    network.fit({animation: {duration: 800, easingFunction: 'easeInOutQuad'}});
                }, 300);
            }
        });
        
        // Additional trigger for stabilization end
        network.on("stabilized", function() {
            console.log("Network stabilized - ensuring loader is hidden");
            hideLoadingIndicator();
        });
        
        // Ensure FR 2590 endpoint is always visible and prominent
        setTimeout(function() {
            var endpointNode = nodes.get('FR2590_Final_Report');
            if (endpointNode) {
                // Make it always visible
                nodes.update([{
                    id: 'FR2590_Final_Report',
                    hidden: false,
                    opacity: 1.0
                }]);
                
                // Add a button to jump to endpoint
                var jumpButton = document.createElement('button');
                jumpButton.innerHTML = '🎯 Jump to FR 2590';
                jumpButton.style.cssText = 'position: absolute; bottom: 20px; right: 20px; padding: 12px 20px; background: linear-gradient(135deg, #f85149 0%, #da3633 100%); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer; font-size: 13px; box-shadow: 0 4px 12px rgba(248, 81, 73, 0.4); z-index: 1001; transition: all 0.2s;';
                jumpButton.onmouseover = function() { this.style.transform = 'scale(1.05)'; this.style.boxShadow = '0 6px 16px rgba(248, 81, 73, 0.6)'; };
                jumpButton.onmouseout = function() { this.style.transform = 'scale(1)'; this.style.boxShadow = '0 4px 12px rgba(248, 81, 73, 0.4)'; };
                jumpButton.onclick = function() {
                    network.focus('FR2590_Final_Report', {
                        scale: 1.2,
                        animation: {
                            duration: 800,
                            easingFunction: "easeInOutQuad"
                        }
                    });
                };
                document.body.appendChild(jumpButton);
            }
        }, 1500);
    </script>
"""
    
    # Insert control panel and JavaScript before closing body tag
    if '</body>' in html:
        html = html.replace('</body>', control_panel + interactive_js + '</body>')
    
    with open('_unified_view.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Create main HTML file
    main_html = """<!DOCTYPE html>
<html>
<head>
    <title>SCCL Unified Data Lineage</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            overflow: hidden;
        }
        iframe {
            width: 100%;
            height: 100vh;
            border: none;
        }
    </style>
</head>
<body>
    <iframe src="_unified_view.html"></iframe>
</body>
</html>"""
    
    with open('sccl_unified_view.html', 'w', encoding='utf-8') as f:
        f.write(main_html)
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS!")
    print("=" * 60)
    print("  • Saved to: sccl_unified_view.html")
    print("  • Interactive highlighting enabled")
    print("  • Filters: Search, Node Type, Schedule")
    print("  • Improved spacing and readability")
    print("=" * 60)
    
    webbrowser.open(f'file://{os.path.abspath("sccl_unified_view.html")}')
    print("\n✓ Opening in browser...\n")

if __name__ == '__main__':
    create_unified_lineage_view()
