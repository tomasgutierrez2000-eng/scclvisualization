#!/bin/bash
# Quick script to parse PDF with your API key

export GOOGLE_API_KEY="AIzaSyAC3e1d0nzry0OYNCNXGFjylkw-ngIQGVI"

cd /Users/tomas

echo "Parsing PDF with Gemini API..."
python3 parse_report.py FR_259020240930_f.pdf --gemini --api-key "$GOOGLE_API_KEY"

echo ""
echo "If that worked, now run:"
echo "  python3 generate_data_model.py"
echo "  python3 sccl_multi_view.py"
