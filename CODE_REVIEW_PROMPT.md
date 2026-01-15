# Code Review and Optimization Prompt

Use this prompt with another GPT model to review and optimize the SCCL Data Lineage Visualization:

## Context
This is a Python-based data lineage visualization system for regulatory reporting (FR 2590). It uses:
- `pyvis` library for network visualization
- `pandas` for data processing
- Interactive HTML/JavaScript for user interface
- Excel file integration for data source

## Files to Review
1. `sccl_unified_view.py` - Main visualization script
2. `integrate_excel_data_corrected.py` - Data integration from Excel
3. `sccl_unified_view.html` - Generated output

## Review Focus Areas

### Performance Optimization
- JavaScript execution efficiency
- DOM manipulation optimization
- Event handler throttling/debouncing
- Memory management
- Rendering performance (especially with 400+ nodes)
- Network physics calculations

### Code Quality
- Code organization and modularity
- Error handling
- Code duplication
- Best practices for pyvis/vis.js
- Python/JavaScript best practices

### User Experience
- Loading times
- Interaction responsiveness
- Visual clarity
- Accessibility

### Specific Questions
1. Can the zoom event handler be optimized further?
2. Are there better ways to handle node clustering?
3. Can we reduce the number of DOM updates?
4. Are there memory leaks in the JavaScript?
5. Can the physics calculations be optimized?
6. Is the data structure optimal for 400+ nodes?

## Current Performance Metrics
- Nodes: ~500
- Edges: ~600
- Zoom updates: Throttled to 50ms
- Physics iterations: 200
- Stabilization: Adaptive timestep enabled

## Expected Improvements
- Faster initial load
- Smoother zoom/pan interactions
- Reduced memory usage
- Better handling of large datasets
