"""
Comprehensive data validation for SCCL lineage
Tests data accuracy, completeness, and relationships
"""

import pandas as pd
import sys

def validate_nodes_edges():
    """Validate that nodes and edges are correctly formed."""
    print("=" * 70)
    print("DATA VALIDATION REPORT")
    print("=" * 70)
    
    # Load data
    try:
        nodes_df = pd.read_csv('nodes.csv')
        edges_df = pd.read_csv('edges.csv')
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return False
    
    errors = []
    warnings = []
    
    # Test 1: Check expected node counts
    print("\n1. NODE COUNT VALIDATION")
    print("-" * 70)
    
    expected_counts = {
        'Source': 20,
        'Atomic': 75,
        'Logic': 75,
        'CDE': 75,
        'Schedule': 14,
    }
    
    for group, expected in expected_counts.items():
        actual = len(nodes_df[nodes_df['group'] == group])
        status = "✅" if actual == expected else "⚠️"
        print(f"  {status} {group}: Expected {expected}, Got {actual}")
        
        if actual != expected:
            warnings.append(f"{group} count mismatch: expected {expected}, got {actual}")
    
    # Check MDRMs separately
    mdrms = len(nodes_df[nodes_df['id'].str.startswith('MDRM_', na=False)])
    expected_mdrms = 198
    status = "✅" if mdrms == expected_mdrms else "⚠️"
    print(f"  {status} MDRMs: Expected {expected_mdrms}, Got {mdrms}")
    if mdrms != expected_mdrms:
        warnings.append(f"MDRM count: expected {expected_mdrms}, got {mdrms}")
    
    print(f"  ✅ Total nodes: {len(nodes_df)}")
    
    # Test 2: Check for orphaned nodes
    print("\n2. ORPHANED NODE CHECK")
    print("-" * 70)
    
    all_node_ids = set(nodes_df['id'])
    referenced_nodes = set(edges_df['source']).union(set(edges_df['target']))
    endpoint_id = 'FR2590_Final_Report'
    
    orphaned = all_node_ids - referenced_nodes - {endpoint_id}
    
    if orphaned:
        print(f"  ⚠️  Found {len(orphaned)} orphaned nodes:")
        for node_id in list(orphaned)[:5]:
            print(f"      - {node_id}")
        if len(orphaned) > 5:
            print(f"      ... and {len(orphaned) - 5} more")
        warnings.append(f"{len(orphaned)} orphaned nodes found")
    else:
        print(f"  ✅ No orphaned nodes (all nodes have connections)")
    
    # Test 3: Check for invalid edge references
    print("\n3. EDGE REFERENCE VALIDATION")
    print("-" * 70)
    
    invalid_sources = set(edges_df['source']) - all_node_ids
    invalid_targets = set(edges_df['target']) - all_node_ids
    
    if invalid_sources:
        print(f"  ❌ Found {len(invalid_sources)} invalid source references:")
        for ref in list(invalid_sources)[:5]:
            print(f"      - {ref}")
        errors.append(f"{len(invalid_sources)} invalid source references")
    else:
        print(f"  ✅ All source references valid")
    
    if invalid_targets:
        print(f"  ❌ Found {len(invalid_targets)} invalid target references:")
        for ref in list(invalid_targets)[:5]:
            print(f"      - {ref}")
        errors.append(f"{len(invalid_targets)} invalid target references")
    else:
        print(f"  ✅ All target references valid")
    
    # Test 4: Check MDRM connectivity
    print("\n4. MDRM CONNECTIVITY CHECK")
    print("-" * 70)
    
    mdrm_nodes = nodes_df[nodes_df['id'].str.startswith('MDRM_', na=False)]
    total_mdrms = len(mdrm_nodes)
    
    mdrms_with_input = set()
    for _, edge in edges_df.iterrows():
        if str(edge['target']).startswith('MDRM_'):
            mdrms_with_input.add(edge['target'])
    
    mdrms_without_input = set(mdrm_nodes['id']) - mdrms_with_input
    
    print(f"  Total MDRMs: {total_mdrms}")
    print(f"  MDRMs with inputs: {len(mdrms_with_input)}")
    print(f"  MDRMs without inputs: {len(mdrms_without_input)}")
    
    if mdrms_without_input:
        print(f"  ⚠️  MDRMs without input connections:")
        for mdrm in list(mdrms_without_input)[:5]:
            print(f"      - {mdrm}")
        if len(mdrms_without_input) > 5:
            print(f"      ... and {len(mdrms_without_input) - 5} more")
        warnings.append(f"{len(mdrms_without_input)} MDRMs have no input connections")
    else:
        print(f"  ✅ All MDRMs have input connections")
    
    # Test 5: Check for duplicate edges
    print("\n5. DUPLICATE EDGE CHECK")
    print("-" * 70)
    
    edge_pairs = list(zip(edges_df['source'], edges_df['target']))
    unique_pairs = set(edge_pairs)
    duplicates = len(edge_pairs) - len(unique_pairs)
    
    if duplicates > 0:
        print(f"  ⚠️  Found {duplicates} duplicate edges")
        warnings.append(f"{duplicates} duplicate edges")
    else:
        print(f"  ✅ No duplicate edges")
    
    # Test 6: Edge count
    print("\n6. EDGE COUNT VALIDATION")
    print("-" * 70)
    print(f"  Total edges: {len(edges_df)}")
    print(f"  Expected: ~634 edges")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ ALL TESTS PASSED - Data is valid!")
        return True
    elif not errors:
        print(f"\n⚠️  PASSED with {len(warnings)} warnings")
        return True
    else:
        print(f"\n❌ FAILED with {len(errors)} errors")
        return False

if __name__ == '__main__':
    success = validate_nodes_edges()
    sys.exit(0 if success else 1)
