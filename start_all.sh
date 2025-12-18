#!/bin/bash
# Start everything automatically

echo "🚀 Starting Avto-Net Scraper Test Environment..."
echo ""

cd "$(dirname "$0")"

# Check and install dependencies
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing FastAPI..."
    pip3 install --quiet fastapi uvicorn pydantic 2>&1 | grep -v "already satisfied" || true
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    echo "Installing Playwright..."
    pip3 install --quiet playwright 2>&1 | grep -v "already satisfied" || true
    python3 -m playwright install chromium 2>&1 | grep -E "(chromium|Installing|Already)" || true
fi

# Create directories
mkdir -p data logs

# Kill existing servers
echo "🛑 Stopping any existing servers..."
pkill -f "api_server.py" 2>/dev/null
pkill -f "serve_pwa.py" 2>/dev/null
sleep 1

# Start API server
echo "🌐 Starting API server..."
nohup python3 api_server.py > logs/api_server.log 2>&1 &
API_PID=$!
echo $API_PID > /tmp/api_server.pid
echo "✅ API Server started (PID: $API_PID)"

# Wait for API to start
sleep 3

# Start PWA server
echo "📱 Starting PWA server..."
nohup python3 serve_pwa.py > logs/pwa_server.log 2>&1 &
PWA_PID=$!
echo $PWA_PID > /tmp/pwa_server.pid
echo "✅ PWA Server started (PID: $PWA_PID)"

# Wait a bit
sleep 2

# Check status
echo ""
echo "============================================"
echo "✅ SERVERS STARTED!"
echo "============================================"
echo ""
echo "📡 API Server: http://localhost:8000"
API_STATUS=$(curl -s http://localhost:8000/api/health 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('status', 'starting')} - {d.get('active_users', 0)} users\")" 2>/dev/null || echo "starting...")
echo "   Status: $API_STATUS"
echo ""
echo "🌐 PWA Website: http://localhost:8080"
PWA_STATUS=$(curl -s http://localhost:8080 >/dev/null 2>&1 && echo "online" || echo "starting...")
echo "   Status: $PWA_STATUS"
echo ""
echo "📝 View logs:"
echo "   API: tail -f logs/api_server.log"
echo "   PWA: tail -f logs/pwa_server.log"
echo "   Scraper: tail -f logs/scraper.log"
echo ""
echo "🛑 Stop servers: ./stop_servers.sh"
echo ""

# Try to open browser
if command -v open >/dev/null; then
    sleep 1
    open http://localhost:8080 2>/dev/null
    echo "🌐 Browser opened to http://localhost:8080"
fi

echo ""
echo "============================================"

