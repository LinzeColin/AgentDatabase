#!/usr/bin/env python3
"""Serve the skin library to DSH over loopback http.

Three things forced a dedicated server rather than shipping the artwork inside
the plugin, all measured against this build of DSH:

*   `/plugins/<pkg>/client.js` returns 200; every other path under a mounted
    plugin returns 404. There is no static asset route for plugins.
*   The renderer refuses `file://` (an `<img>` pointed at one fires `error`),
    while `http://127.0.0.1` loads fine.
*   The reference skin's answer — inline every asset as a data URI — is a
    multi-gigabyte bundle at 612 images.

And one thing forced this file over `python3 -m http.server`: the page lives on
`127.0.0.1:3080` and the assets on another port, so `fetch('/catalog.json')` is
a cross-origin request. Images were loading while the catalogue fetch failed
with a bare "Failed to fetch" — CORS, not a missing file.

Bound to loopback only; it serves a directory of game artwork, nothing private.

Usage:
    python3 asset_server.py --root …/skin-assets --port 3099
"""

from __future__ import annotations

import argparse
import functools
import http.server
import pathlib
import socketserver


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".webp": "image/webp",
        ".json": "application/json",
    }

    def end_headers(self):
        # The DSH page is another origin (port 3080), so the catalogue fetch
        # needs this header even though the images did not.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def log_message(self, *args):
        pass   # a backdrop swap should not spam a terminal


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=3099)
    args = parser.parse_args()
    handler = functools.partial(Handler, directory=str(args.root))
    with Server(("127.0.0.1", args.port), handler) as server:
        print(f"皮肤素材服务 http://127.0.0.1:{args.port}  根目录 {args.root}")
        server.serve_forever()


if __name__ == "__main__":
    main()
