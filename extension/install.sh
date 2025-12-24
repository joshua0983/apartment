#!/bin/bash

echo "🏙️  NYC Apartment Evaluator - Extension Installation"
echo "===================================================="
echo ""

# Navigate to extension directory
cd "$(dirname "$0")"

# Create icons if they don't exist
if [ ! -f "icons/icon16.png" ]; then
    echo "📦 Creating extension icons..."
    python3 create_icons.py
    echo ""
fi

# Check if backend is running
echo "🔍 Checking if API server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is running!"
else
    echo "⚠️  API server not detected."
    echo ""
    echo "Starting API server in background..."
    cd ..
    source venv/bin/activate 2>/dev/null || true
    nohup python -m uvicorn api.server:app --reload > /tmp/apt-eval-api.log 2>&1 &
    API_PID=$!
    echo "Started API server (PID: $API_PID)"
    echo "Logs: /tmp/apt-eval-api.log"
    sleep 3
    cd extension
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "For Chrome:"
echo "  1. Open chrome://extensions/"
echo "  2. Enable 'Developer mode' (top-right toggle)"
echo "  3. Click 'Load unpacked'"
echo "  4. Select this folder: $(pwd)"
echo ""
echo "For Firefox:"
echo "  1. Open about:debugging#/runtime/this-firefox"
echo "  2. Click 'Load Temporary Add-on'"
echo "  3. Select manifest.json from: $(pwd)"
echo ""
echo "Then visit a rental listing on StreetEasy, Zillow,"
echo "Apartments.com, or RentHop and click the extension icon!"
echo ""
