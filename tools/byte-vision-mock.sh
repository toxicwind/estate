#!/usr/bin/env bash
# byte-vision mock - placeholder for vision API with health endpoint
# Returns health check response
PORT="${BYTE_VISION_PORT:-25121}"
echo "byte-vision-mock listening on $PORT"

# Start a simple HTTP server for health checks
python3 -c "
import http.server
import socketserver
import json
import sys

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'service': 'byte-vision-mock'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('', $PORT), HealthHandler) as httpd:
    print(f'byte-vision-mock health server on port $PORT')
    httpd.serve_forever()
" &

# Keep the script running
wait
