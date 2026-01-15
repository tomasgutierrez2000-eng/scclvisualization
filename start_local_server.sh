#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  💻 Local Server - Share on Your Network"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Prepare file
if [ -f "_unified_view.html" ]; then
    cp _unified_view.html index.html
elif [ -f "sccl_unified_view.html" ]; then
    cp sccl_unified_view.html index.html
else
    echo "❌ Error: Visualization file not found"
    exit 1
fi

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null)
fi

PORT=8000

echo "✅ Starting server on port $PORT..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📍 ACCESS YOUR VISUALIZATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  On this computer:"
echo "  → http://localhost:$PORT"
echo ""

if [ ! -z "$LOCAL_IP" ]; then
    echo "  On other devices (same WiFi):"
    echo "  → http://$LOCAL_IP:$PORT"
    echo ""
    echo "  Share this URL with others on your network!"
else
    echo "  (Could not detect IP address)"
    echo "  Find your IP with: ifconfig | grep 'inet '"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Server will run until you press Ctrl+C"
echo "   Keep this terminal open while sharing"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start server
python3 -m http.server $PORT
