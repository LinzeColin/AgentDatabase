"""v0.0.0.32 T04 — the protected /api/v31/live-snapshot route.

The route reuses the existing Cloudflare Access gate in `Handler.do_GET`; it
adds no second authentication path. These tests pin the four documented
responses (403/404/503/200), the header-vs-body identity contract the browser
provider cross-checks, and the privacy contract.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from OpenAIDatabase.scripts.memory_atlas_private.access_auth import AccessVerificationError
from OpenAIDatabase.scripts.memory_atlas_private.api_server import ApiState, Handler

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "OpenAIDatabase" / "schema" / "memory_atlas.live_snapshot.v1.schema.json"
FIXTURE = REPO / "OpenAIDatabase" / "fixtures" / "live_snapshot.synthetic.json"


class FixtureAccessVerifier:
    def verify(self, token: str) -> dict[str, str]:
        if token != "fixture":
            raise AccessVerificationError("invalid fixture assertion")
        return {"sub": "fixture-owner"}


class _Server:
    def __init__(self, tmp_path: Path):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.state = ApiState(  # type: ignore[attr-defined]
            tmp_path / "runtime",
            tmp_path / "web",
            "https://memoryatlas.example.test",
            access_verifier=FixtureAccessVerifier(),
            live_snapshot_root=tmp_path / "web" / "live-snapshot",
            live_snapshot_schema=SCHEMA,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def get(self, path: str, *, assertion: str | None = "fixture"):
        headers = {"Cf-Access-Jwt-Assertion": assertion} if assertion else {}
        return urllib.request.urlopen(
            urllib.request.Request(self.base + path, headers=headers), timeout=5
        )

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


@pytest.fixture()
def server(tmp_path: Path):
    running = _Server(tmp_path)
    try:
        yield running
    finally:
        running.close()


def _publish(tmp_path: Path, mutate=None) -> dict:
    snapshot = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(snapshot)
    root = tmp_path / "web" / "live-snapshot"
    root.mkdir(parents=True, exist_ok=True)
    (root / "current.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return snapshot


def test_live_snapshot_is_never_anonymously_readable(server: _Server) -> None:
    with pytest.raises(urllib.error.HTTPError) as denied:
        server.get("/api/v31/live-snapshot", assertion=None)
    assert denied.value.code == 403
    with pytest.raises(urllib.error.HTTPError) as forged:
        server.get("/api/v31/live-snapshot", assertion="forged")
    assert forged.value.code == 403


def test_authorized_read_without_a_published_snapshot_is_404(server: _Server) -> None:
    with pytest.raises(urllib.error.HTTPError) as missing:
        server.get("/api/v31/live-snapshot")
    assert missing.value.code == 404
    assert json.loads(missing.value.read())["error"] == "live_snapshot_not_available"


def test_invalid_current_snapshot_is_503_not_a_partial_200(server: _Server, tmp_path: Path) -> None:
    # A snapshot that fails schema or authority validation must not reach the
    # browser at all: a partial 200 would let the page render numbers whose run
    # identity was never proven.
    _publish(tmp_path, lambda snapshot: snapshot["truth"]["same_run_evidence"]["r2_readback"].update({"state": "FAIL"}))
    with pytest.raises(urllib.error.HTTPError) as invalid:
        server.get("/api/v31/live-snapshot")
    assert invalid.value.code == 503
    assert json.loads(invalid.value.read())["error"] == "live_snapshot_invalid"


def test_published_snapshot_is_served_with_matching_identity_headers(
    server: _Server, tmp_path: Path
) -> None:
    snapshot = _publish(tmp_path)
    with server.get("/api/v31/live-snapshot") as response:
        body = json.loads(response.read())
        headers = {name.lower(): value for name, value in response.headers.items()}
    assert response.status == 200
    assert body["run"]["run_id"] == snapshot["run"]["run_id"]
    assert headers["x-memory-atlas-run-id"] == snapshot["run"]["run_id"]
    assert headers["x-memory-atlas-trace-id"] == snapshot["run"]["trace_id"]
    assert headers["x-memory-atlas-release-id"] == snapshot["release"]["release_id"]
    assert headers["x-memory-atlas-deployment-revision"] == snapshot["release"]["deployment_revision"]
    # The provider refuses a response without no-store rather than let a cached
    # body impersonate current data.
    assert "no-store" in headers["cache-control"]
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["etag"].startswith('"') and len(headers["etag"]) == 66


def test_unverified_release_identity_is_reported_not_omitted(server: _Server, tmp_path: Path) -> None:
    def clear_release(snapshot: dict) -> None:
        snapshot["release"]["release_id"] = None
        snapshot["release"]["deployment_revision"] = None
        snapshot["release"]["identity_state"] = "UNVERIFIED"

    _publish(tmp_path, clear_release)
    with server.get("/api/v31/live-snapshot") as response:
        headers = {name.lower(): value for name, value in response.headers.items()}
    assert headers["x-memory-atlas-release-id"] == "UNVERIFIED"
    assert headers["x-memory-atlas-deployment-revision"] == "UNVERIFIED"


def test_served_body_carries_the_privacy_contract(server: _Server, tmp_path: Path) -> None:
    _publish(tmp_path)
    with server.get("/api/v31/live-snapshot") as response:
        body = json.loads(response.read())
    assert body["privacy"] == {
        "raw_content_included": False,
        "secret_values_included": False,
        "private_paths_included": False,
        "object_keys_included": False,
    }
    serialized = json.dumps(body, ensure_ascii=False)
    for forbidden in ("primary-objects/", "sha256/", "/srv/linze/secrets", "R2_SECRET"):
        assert forbidden not in serialized
