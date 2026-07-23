#!/usr/bin/env python3
"""Local preview server that mirrors Firebase Hosting's cleanUrls: a request
for /contact serves contact.html. Static only, no Firebase auth needed.
Run from the repo root:  python3 scripts/preview_server.py [port]"""

import http.server
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000


class CleanUrlHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path.split("?")[0])
        if os.path.isdir(local):
            return local
        if not os.path.exists(local) and not os.path.splitext(local)[1]:
            html = local + ".html"
            if os.path.exists(html):
                return html
        return local


os.chdir(ROOT)
http.server.HTTPServer(("127.0.0.1", PORT), CleanUrlHandler).serve_forever()
