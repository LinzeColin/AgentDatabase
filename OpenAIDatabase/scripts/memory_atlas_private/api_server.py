from __future__ import annotations

import argparse
import json
import mimetypes
import os
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import api_live_snapshot
from .action_queue import ActionQueue
from .access_auth import AccessVerificationError, CloudflareAccessVerifier

LIVE_SNAPSHOT_SCHEMA = (
    Path(__file__).resolve().parents[2] / "schema" / "memory_atlas.live_snapshot.v1.schema.json"
)


class ApiState:
    def __init__(
        self,
        runtime_dir: Path,
        web_data_dir: Path,
        external_origin: str,
        access_verifier: CloudflareAccessVerifier | object | None = None,
        live_snapshot_root: Path | None = None,
        live_snapshot_schema: Path | None = None,
    ):
        self.runtime_dir = runtime_dir
        self.web_data_dir = web_data_dir
        self.external_origin = external_origin.rstrip("/")
        self.access_verifier = access_verifier or CloudflareAccessVerifier.from_env()
        self.queue = ActionQueue(runtime_dir / "action-queue.sqlite3")
        # The pipeline publishes the same-run snapshot next to the other web data,
        # so the API reads exactly what the terminal run promoted to current.
        self.live_snapshot_root = live_snapshot_root or (web_data_dir / "live-snapshot")
        self.live_snapshot_schema = live_snapshot_schema or LIVE_SNAPSHOT_SCHEMA

    def load_json(self, filename: str) -> dict[str, object]:
        path = self.web_data_dir / filename
        if not path.is_file():
            return {
                "schema_version": "memory_atlas.api_unknown.v1",
                "state": "UNKNOWN",
                "message_zh": f"尚无 {filename} 的权威投影。",
            }
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"{filename} 不是 JSON object")
        return value


class Handler(BaseHTTPRequestHandler):
    server_version = "MemoryAtlasPrivateAPI/0.0.0.31"

    @property
    def state(self) -> ApiState:
        return self.server.state  # type: ignore[attr-defined]

    def _json(self, status: int, value: dict[str, object]) -> None:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(payload)

    def _raw(self, status: int, headers: dict[str, str], payload: bytes) -> None:
        # The live-snapshot helper owns its own headers (no-store, ETag and the
        # four identity headers the browser cross-checks against the body), so
        # they are written verbatim instead of being rebuilt by _json.
        self.send_response(status)
        for name, value in headers.items():
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(payload)

    def _access_authorized(self, *, require_origin: bool) -> bool:
        # The service binds to loopback. Traefik/Cloudflare Access is the only external
        # path, but the origin still verifies the signed assertion itself: header
        # presence is never treated as authentication. Mutations additionally require
        # the exact product Origin to reduce cross-site request risk.
        assertion = self.headers.get("Cf-Access-Jwt-Assertion", "").strip()
        origin = self.headers.get("Origin", "").rstrip("/")
        if not assertion or (require_origin and origin != self.state.external_origin):
            return False
        try:
            verify = getattr(self.state.access_verifier, "verify")
            verify(assertion)
        except Exception:
            return False
        return True

    def _read_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 64 * 1024:
            raise ValueError("请求体大小不合法")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("请求体必须是 JSON object")
        return value

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self._json(HTTPStatus.OK, {
                "schema_version": "memory_atlas.health.v1",
                "state": "PASS",
                "component": "private-api",
            })
            return
        if parsed.path.startswith("/api/v31/") and not self._access_authorized(require_origin=False):
            self._json(HTTPStatus.FORBIDDEN, {
                "state": "DENIED",
                "message_zh": "私有分析读取必须通过已验证的 Cloudflare Access 身份。",
            })
            return
        if parsed.path == "/api/v31/live-snapshot":
            # Reuses the Access gate above; `authorized` is only ever True here
            # because an unauthenticated request already returned 403.
            status, headers, payload = api_live_snapshot.response(
                self.state.live_snapshot_root,
                self.state.live_snapshot_schema,
                authorized=True,
            )
            self._raw(status, headers, payload)
            return
        if parsed.path == "/api/v31/status":
            self._json(HTTPStatus.OK, self.state.load_json("memory_atlas_private_analytics.json"))
            return
        if parsed.path == "/api/v31/analytics":
            snapshot = self.state.load_json("memory_atlas_private_analytics.json")
            self._json(HTTPStatus.OK, snapshot.get("behavior_economics", snapshot))  # type: ignore[arg-type]
            return
        if parsed.path == "/api/v31/failure-compound":
            snapshot = self.state.load_json("memory_atlas_private_analytics.json")
            self._json(HTTPStatus.OK, snapshot.get("failure_compound", snapshot))  # type: ignore[arg-type]
            return
        if parsed.path.startswith("/api/v31/actions/"):
            request_id = parsed.path.rsplit("/", 1)[-1]
            try:
                value = self.state.queue.status(request_id)
            except KeyError:
                self._json(HTTPStatus.NOT_FOUND, {"state": "NOT_FOUND", "request_id": request_id})
            else:
                self._json(HTTPStatus.OK, value)
            return
        self._json(HTTPStatus.NOT_FOUND, {"state": "NOT_FOUND"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._access_authorized(require_origin=True):
            self._json(HTTPStatus.FORBIDDEN, {
                "state": "DENIED",
                "message_zh": "该动作必须通过已认证的 Memory Atlas 私有入口执行。",
            })
            return
        routes = {
            "/api/v31/actions/capture-request": "capture_request",
            "/api/v31/actions/diagnose": "diagnose",
            "/api/v31/actions/restore-drill": "restore_drill",
        }
        action = routes.get(urlparse(self.path).path)
        if not action:
            self._json(HTTPStatus.NOT_FOUND, {"state": "NOT_FOUND"})
            return
        try:
            body = self._read_body()
            idempotency_key = str(body.get("idempotency_key", "")).strip()
            request = self.state.queue.enqueue(action, idempotency_key)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"state": "INVALID", "message_zh": str(exc)})
            return
        self._json(HTTPStatus.ACCEPTED, asdict(request))

    def log_message(self, fmt: str, *args: object) -> None:
        # Avoid request headers and query strings in ordinary logs.
        print(f"{self.address_string()} {fmt % args}")


def serve(host: str, port: int, runtime_dir: Path, web_data_dir: Path, external_origin: str) -> None:
    state = ApiState(runtime_dir, web_data_dir, external_origin)
    server = ThreadingHTTPServer((host, port), Handler)
    server.state = state  # type: ignore[attr-defined]
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory Atlas private read-only analytics and action API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--web-data-dir", type=Path, required=True)
    parser.add_argument("--external-origin", required=True)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "::1"}:
        raise SystemExit("API 必须绑定 loopback；外部访问只能经 Cloudflare Access/Traefik")
    serve(args.host, args.port, args.runtime_dir, args.web_data_dir, args.external_origin)


if __name__ == "__main__":
    main()
