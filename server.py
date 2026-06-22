import http.server
import os
import mimetypes
from urllib.parse import urlparse, parse_qs, unquote

SERVE_DIR = "WebScrapBook/data/20260622133604444"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def resolve_media(self, filename):
        """Try to find the actual file for a media filename (with or without hash)."""
        # 1. Exact match (full hashed name)
        candidate = os.path.join(SERVE_DIR, filename)
        if os.path.exists(candidate):
            return filename

        # 2. Strip hash suffix: name.hash.ext -> name.ext
        parts = filename.rsplit(".", 2)
        if len(parts) == 3:
            clean = parts[0] + "." + parts[2]
            candidate = os.path.join(SERVE_DIR, clean)
            if os.path.exists(candidate):
                return clean

        # 3. Numeric prefix: 0.descriptive-text.hash.ext -> 0.ext
        first = filename.split(".")[0]
        ext = filename.rsplit(".", 1)[-1]
        if first.isdigit():
            simple = first + "." + ext
            candidate = os.path.join(SERVE_DIR, simple)
            if os.path.exists(candidate):
                return simple

        return None

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
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        # Remap /_next/static/media/X -> /X (full hashed name)
        elif path.startswith("/_next/static/media/"):
            filename = path[len("/_next/static/media/"):]
            resolved = self.resolve_media(filename)
            if resolved:
                self.path = "/" + resolved
            else:
                self.send_error(404)
                return
        # Handle /_next/image?url=...&w=...&q=... -> serve the image directly
        elif path == "/_next/image":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [""])[0]
            filename = url.split("/")[-1]
            resolved = self.resolve_media(filename)
            if resolved:
                self.path = "/" + resolved
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
