#!/usr/bin/env python3
"""
Simple REST backend for the CN Phase 1 project (standard library only).

Run:
    BACKEND=A PORT=3001 python3 backend.py
    BACKEND=B PORT=3002 python3 backend.py
"""
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKEND = os.environ.get("BACKEND", "A")
PORT = int(os.environ.get("PORT", "3001"))

# Same body on both backends, so the ETag is identical on A and B.
INFO_BODY = json.dumps({"service": "cn-project", "version": 1,
                        "note": "cacheable endpoint"}).encode()
INFO_ETAG = '"' + hashlib.md5(INFO_BODY).hexdigest() + '"'


class Handler(BaseHTTPRequestHandler):
    server_version = "CNBackend"

    def _route(self, send_body):
        path = self.path.split("?")[0]
        headers = {"X-Backend": BACKEND}
        status = 200

        if path == "/":
            body = f"Backend {BACKEND} is running on port {PORT}\n".encode()
            headers["Content-Type"] = "text/plain"
            headers["Cache-Control"] = "no-store"
        elif path == "/api/status":
            body = json.dumps({"backend": BACKEND, "status": "ok"}).encode()
            headers["Content-Type"] = "application/json"
            headers["Cache-Control"] = "no-store"
        elif path == "/api/info":
            headers["Content-Type"] = "application/json"
            headers["Cache-Control"] = "max-age=60"
            headers["ETag"] = INFO_ETAG
            if self.headers.get("If-None-Match") == INFO_ETAG:
                status, body = 304, b""
            else:
                body = INFO_BODY
        else:
            status = 404
            body = json.dumps({"error": "not found"}).encode()
            headers["Content-Type"] = "application/json"

        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        if status != 304:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body and status != 304:
            self.wfile.write(body)

    def do_GET(self):
        self._route(True)

    def do_HEAD(self):  # needed because `curl -I` sends HEAD
        self._route(False)

    def log_message(self, fmt, *args):
        print(f"[Backend {BACKEND}:{PORT}] {self.client_address[0]} {fmt % args}")


if __name__ == "__main__":
    # 0.0.0.0 = listen on every interface (LAN reachable), NOT only 127.0.0.1
    print(f"Backend {BACKEND} listening on 0.0.0.0:{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
