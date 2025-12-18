#!/bin/bash

# Start Test Environment Script
# This script starts the API server and provides instructions for the PWA

echo "🚀 Starting Avto-Net Scraper Test Environment..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip3 install -r requirements/common.txt
fi

if ! python3 -c "import playwright" 2>/dev/null; then
    echo "⚠️  Playwright not found. Installing..."
    pip3 install playwright
    python3 -m playwright install chromium
fi

echo "✅ Dependencies checked"
echo ""

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p logs

echo "🌐 Starting API server on http://localhost:8000"
echo "📱 PWA will be available at: file://$(pwd)/test-pwa/index.html"
echo ""
echo "💡 To serve the PWA properly, you can:"
echo "   1. Use Python's HTTP server: python3 -m http.server 8080 -d test-pwa"
echo "   2. Or open test-pwa/index.html directly in your browser"
echo ""
echo "⚠️  Note: Opening HTML files directly may have CORS issues."
echo "   For best results, use a local HTTP server."
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the API server
cd "$(dirname "$0")"
python3 api_server.py

