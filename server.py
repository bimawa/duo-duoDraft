#!/usr/bin/env python3
"""Local HTTP server for duo-buro.com offline copy.
Serves static files + handles Readymag API endpoints."""

import os
import json
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8080"))

# Preload widget data
WIDGETS_DATA = None
widgets_path = os.path.join(ROOT, "api", "viewer", "project", "4078184", "widgets.json")
if os.path.exists(widgets_path):
    with open(widgets_path) as f:
        WIDGETS_DATA = f.read()

class DuoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode() if isinstance(data, str) else json.dumps(data).encode())

    def _send_ok(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Widgets API: /api/viewer/project/{id}/widgets?pageId=...
        if "/api/viewer/project/" in path and path.endswith("/widgets"):
            if WIDGETS_DATA:
                self._send_json(WIDGETS_DATA)
            else:
                self._send_json({"error": "No widget data"}, 404)
            return

        # Font CSS mapping: /api/fonts/typetoday/css -> /api/fonts/typetoday/css.css
        if path.endswith("/css") and "/api/fonts/" in path:
            css_path = os.path.join(ROOT, path.lstrip("/")) + ".css"
            if os.path.exists(css_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/css; charset=utf-8")
                self.end_headers()
                with open(css_path) as f:
                    self.wfile.write(f.read().encode())
                return

        # Missing sprite asset - serve the downloaded one as fallback
        if path == "/img/common/navigation/sprite@2x.png" or path == "/img/common/navigation/sprite.png":
            sprite_name = "sprite@2x-OLGX4CHD.png" if "@2x" in path else "sprite-25E3AVGT.png"
            real_sprite = os.path.join(
                ROOT, "st-p.rmcdn1.net", "161b6d7b", "dist",
                "sprite@2x-OLGX4CHD.png"
            )
            if os.path.exists(real_sprite):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                with open(real_sprite, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Default: serve static files
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # View count tracking
        if "/api/countview/" in path:
            self._send_ok()
            return

        # Honeycomb telemetry proxy
        if path == "/api/proxy/honeycomb":
            self._send_ok()
            return

        # Unknown POST - return 200 to avoid errors
        self._send_ok()

    def log_message(self, format, *args):
        if "/api/countview" not in args[0] and "/api/proxy" not in args[0]:
            super().log_message(format, *args)


if __name__ == "__main__":
    server = HTTPServer(("", PORT), DuoHandler)
    print(f"DUO BURO - Local Server")
    print(f"  http://localhost:{PORT}")
    print(f"  Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
