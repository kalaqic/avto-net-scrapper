#!/usr/bin/env python3
"""
Simple HTTP server to serve the test PWA
Run this after starting the API server
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8080
PWA_DIR = Path(__file__).parent / "test-pwa"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PWA_DIR), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    os.chdir(PWA_DIR)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 50)
        print("🌐 PWA Server Started!")
        print("=" * 50)
        print(f"📱 Open your browser and go to: {url}")
        print("")
        print("💡 The API server should be running on http://localhost:8000")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        print("")
        
        # Try to open browser automatically
        try:
            webbrowser.open(url)
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")

if __name__ == "__main__":
    main()

