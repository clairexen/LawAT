import http.server
import os
from urllib.parse import unquote
from pathlib import Path

class MultiRootHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    fallback_dirs = ['code', 'files']

    def send_head(self):
        """Try to serve the original path or from fallback dirs."""
        path = self.path
        # Try original path first
        filepath = self.translate_path(path)
        if os.path.isdir(filepath):
            # Try to serve index.html from directory
            for index in ["index.html", "index.htm"]:
                index_path = os.path.join(filepath, index)
                if os.path.isfile(index_path):
                    self.path = os.path.join(path.rstrip("/"), index)
                    return super().send_head()

        elif os.path.isfile(filepath):
            return super().send_head()

        # Try fallback directories
        for base in self.fallback_dirs:
            fallback_path = f"/{base}{path}"
            translated = self.translate_path(fallback_path)
            if os.path.isdir(translated):
                for index in ["index.html", "index.htm"]:
                    index_path = os.path.join(translated, index)
                    if os.path.isfile(index_path):
                        self.path = f"{fallback_path.rstrip('/')}/{index}"
                        return super().send_head()
            elif os.path.isfile(translated):
                self.path = fallback_path
                return super().send_head()

        return self.send_error(404, "File not found")

if __name__ == '__main__':
    from http.server import HTTPServer
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(('0.0.0.0', port), MultiRootHTTPRequestHandler)
    print(f"Serving with fallbacks: {MultiRootHTTPRequestHandler.fallback_dirs} on port {port}")
    server.serve_forever()
