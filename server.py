import http.server
import os
import mimetypes
from urllib.parse import urlparse, parse_qs, unquote

SERVE_DIR = "WebScrapBook/data/20260622133604444"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # Remap /_next/static/chunks/pages/X -> /X
        if path.startswith("/_next/static/chunks/pages/"):
            filename = path.split("/")[-1]
            self.path = "/" + filename
        # Remap /_next/static/chunks/X -> /X
        elif path.startswith("/_next/static/chunks/"):
            filename = path.split("/")[-1]
            candidate = os.path.join(SERVE_DIR, filename)
            if os.path.exists(candidate):
                self.path = "/" + filename
            else:
                # Missing chunk — serve an empty stub so React doesn't crash hard
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        # Remap /_next/static/media/X -> /X
        elif path.startswith("/_next/static/media/"):
            filename = path.split("/")[-1]
            self.path = "/" + filename
        # Handle /_next/image?url=...&w=...&q=...  -> serve the image directly
        elif path == "/_next/image":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [""])[0]
            # url is like /_next/static/media/latest1.e78cae7c.png
            filename = url.split("/")[-1]
            # strip any hash suffix (latest1.e78cae7c.png -> latest1.png)
            parts = filename.rsplit(".", 2)
            if len(parts) == 3:
                clean = parts[0] + "." + parts[2]
            else:
                clean = filename
            candidate = os.path.join(SERVE_DIR, clean)
            if os.path.exists(candidate):
                self.path = "/" + clean
            else:
                self.send_error(404)
                return
        # Remap /latest/X -> /X
        elif path.startswith("/latest/"):
            filename = path.split("/")[-1]
            self.path = "/" + filename

        super().do_GET()

    def log_message(self, format, *args):
        pass  # suppress verbose logs

if __name__ == "__main__":
    import socketserver
    PORT = 5000
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving on port {PORT}")
        httpd.serve_forever()
