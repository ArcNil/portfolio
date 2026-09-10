#!/usr/bin/env python3
"""
Tiny reverse proxy in front of PostgREST.

- /docs            -> Swagger UI (static files from /opt/swagger-ui)
- /docs/openapi.json -> OpenAPI spec fetched from PostgREST
- everything else  -> proxied verbatim to PostgREST on 127.0.0.1:$PGRST_PORT

Uses only the Python standard library. Runs as the same non-root user.
"""

import json
import os
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SWAGGER_DIR = "/opt/swagger-ui"
UPSTREAM = f"http://127.0.0.1:{os.environ.get('PGRST_PORT', '3000')}"
LISTEN_PORT = int(os.environ.get("PORT", "7860"))

# Swagger UI page that loads /docs/openapi.json
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PostgREST API Docs</title>
  <link rel="stylesheet" href="/docs/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="/docs/swagger-ui-bundle.js" charset="UTF-8"></script>
  <script>
    window.onload = () => {
      SwaggerUIBundle({
        url: "/docs/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
      });
    };
  </script>
</body>
</html>"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static Swagger UI files from SWAGGER_DIR
        super().__init__(*args, directory=SWAGGER_DIR, **kwargs)

    # --- /docs routes -----------------------------------------------------
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # --- proxying ---------------------------------------------------------
    def _proxy(self):
        url = UPSTREAM + self.path
        req = urllib.request.Request(url, method=self.command)
        for h in ("Content-Type", "Accept", "Prefer", "Range",
                  "If-Match", "Authorization"):
            if v := self.headers.get(h):
                req.add_header(h, v)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        try:
            with urllib.request.urlopen(req, body) as r:
                resp, code, rheaders = r.read(), r.status, r.headers
        except urllib.error.HTTPError as e:
            resp, code, rheaders = e.read(), e.code, e.headers
        except Exception as e:  # URLError, timeout, upstream down, ...
            print(f"proxy error: {self.command} {self.path}: {e!r}", flush=True)
            resp = json.dumps({"message": str(e)}).encode()
            code, rheaders = 502, {"Content-Type": "application/json"}

        self.send_response(code)
        for h in ("Content-Type", "Content-Range", "Content-Location",
                  "Location", "ETag", "Preference-Applied",
                  "Accept-Profile", "Content-Profile"):
            if v := rheaders.get(h):
                self.send_header(h, v)
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def do_GET(self):
        if self.path == "/docs" or self.path.startswith("/docs?"):
            self._send(200, INDEX_HTML.encode(), "text/html; charset=utf-8")
        elif self.path == "/docs/openapi.json":
            # Fetch the spec and rewrite its host so "Try it out" requests
            # hit the public origin instead of PostgREST's internal port
            import json
            spec = json.loads(urllib.request.urlopen(f"{UPSTREAM}/").read())
            spec["host"] = self.headers.get("Host") or f"localhost:{LISTEN_PORT}"
            spec["schemes"] = ["https"] if self.headers.get(
                "X-Forwarded-Proto") == "https" else ["http"]
            body = json.dumps(spec).encode()
            self._send(200, body, "application/openapi+json")
        elif self.path.startswith("/docs/"):
            # static assets: strip the /docs prefix
            self.path = self.path[len("/docs"):]
            super().do_GET()
        else:
            self._proxy()

    def do_HEAD(self):
        self.do_GET()

    def _proxy_with_body(self):
        self._proxy()

    do_POST = do_PATCH = do_PUT = do_DELETE = do_OPTIONS = _proxy_with_body

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler).serve_forever()