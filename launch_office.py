#!/usr/bin/env python3
"""
JARVIS4 AI OFFICE — Launch Script

Starts a local HTTP server for the 3D office and opens it in the browser.
This avoids CORS issues when connecting to Railway cloud API.
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

PROJECT_DIR = Path(__file__).parent.resolve()
FRONTEND_DIR = PROJECT_DIR / "frontend"
PORT = 3000


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logs


def start_server():
    os.chdir(str(FRONTEND_DIR))
    server = HTTPServer(("localhost", PORT), QuietHandler)
    server.serve_forever()


def main():
    print("=" * 50)
    print("  JARVIS4 AI OFFICE")
    print("=" * 50)

    # Start local HTTP server for frontend
    print(f"\n[1] Starting local server on http://localhost:{PORT}")
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    time.sleep(0.5)

    # Open in browser
    url = f"http://localhost:{PORT}/office3d.html"
    print(f"[2] Opening 3D Office: {url}")
    webbrowser.open(url)

    print(f"\n  Office is running at: {url}")
    print(f"  Connected to cloud: https://jarvis4-production-22c6.up.railway.app")
    print(f"\n  Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
