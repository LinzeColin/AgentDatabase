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
import json
import pathlib
import time
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

    def do_POST(self):
        """插件把自己的状态回报到这里，落成一行日志。

        为什么需要它：DSH 是打包应用，它的渲染进程既不能从外面查 DOM，
        也不方便开控制台 —— 用鼠标去点它的开发者工具已经出过一次事故
        （点错窗口，把诊断代码打进了用户正在用的另一个应用并发送）。
        让被诊断的代码自己说话，比隔着屏幕去问它可靠得多。
        """
        if self.path.startswith("/__state"):
            # DSH 的皮肤面板住在浏览器里，写不了文件——它只能写自己的
            # localStorage，而同一份状态每 15 秒又从共享文件读回来覆盖。
            # 结果是那个面板看起来能改模式和间隔，实际上改完 15 秒内就被盖掉。
            # 给它一条写回的路，控制才是真的。
            length = int(self.headers.get("content-length") or 0)
            try:
                patch = json.loads(self.rfile.read(length).decode("utf-8", "replace"))
            except Exception:
                self.send_response(400); self.end_headers(); return
            target = pathlib.Path.home() / ".harness-ui" / "state.json"
            try:
                current = json.loads(target.read_text(encoding="utf-8"))
            except Exception:
                current = {}
            # 只收白名单里的键：面板改的是模式和间隔，不该让它整份覆盖，
            # 否则一个陈旧的面板会把菜单栏刚推进的周期游标抹掉。
            for key in ("mode", "selected", "intervalMs", "hidden", "cycle", "cursor", "lastRotate"):
                if key in patch:
                    current[key] = patch[key]
            current["updated"] = int(time.time() * 1000)
            tmp = target.with_suffix(".tmp")
            tmp.write_text(json.dumps(current, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(target)
            self.send_response(204); self.end_headers(); return
        if not self.path.startswith("/__diag"):
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace")[:4000]
        with open(pathlib.Path.home() / ".harness-ui" / "diag.log", "a") as handle:
            handle.write(f"{time.strftime('%H:%M:%S')}  {body}\n")
        self.send_response(204); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
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
