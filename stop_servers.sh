#!/bin/bash
# Stop all servers

echo "🛑 Stopping servers..."

if [ -f /tmp/api_server.pid ]; then
    PID=$(cat /tmp/api_server.pid)
    kill $PID 2>/dev/null && echo "✅ Stopped API server (PID: $PID)" || echo "API server not running"
    rm /tmp/api_server.pid
fi

if [ -f /tmp/pwa_server.pid ]; then
    PID=$(cat /tmp/pwa_server.pid)
    kill $PID 2>/dev/null && echo "✅ Stopped PWA server (PID: $PID)" || echo "PWA server not running"
    rm /tmp/pwa_server.pid
fi

# Also kill by process name
pkill -f "api_server.py" 2>/dev/null
pkill -f "serve_pwa.py" 2>/dev/null

echo "✅ All servers stopped"

