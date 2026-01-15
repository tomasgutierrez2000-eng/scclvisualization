#!/bin/bash

echo "📦 Creating zip file for easy GitHub upload..."
echo ""

cd /Users/tomas

# Create zip with all essential files
zip -r sccl_visualization.zip \
  index.html \
  sccl_unified_view.py \
  integrate_excel_data_complete_catalog.py \
  integrate_excel_data_corrected.py \
  validate_data.py \
  diagnose_mdrm_connections.py \
  README.md \
  *.md \
  *.sh \
  -x "*.xlsx" "*.pdf" "*.docx" "*.csv" "*unified_view.html" 2>/dev/null

echo ""
echo "✅ Created: sccl_visualization.zip"
echo ""
echo "📤 To upload:"
echo "1. Go to: https://github.com/tomasgutierrez2000-eng/scclvisualization"
echo "2. Click 'Add file' → 'Upload files'"
echo "3. Drag sccl_visualization.zip (or extract and upload files)"
echo ""
