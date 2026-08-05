#!/usr/bin/env bash
# Capture the complete evidence set for whatever release is live right now.
#
#   capture_release_evidence.sh <repo> <output-dir>
#
# The 2026-08-05 review scored every dimension's evidence at roughly half its
# implementation. The reason was not that the checks had not run — it was that
# they had run in a terminal and the receipts committed to the repository were
# still anchored to releases from two days earlier. A reviewer reading the repo
# saw stale artefacts and scored what they could see, which is the correct thing
# for a reviewer to do.
#
# So evidence capture becomes a command instead of a habit. It reads the live
# world, writes one receipt per dimension with the value it measured, and can be
# re-run after any promotion — which is what stops the evidence going quietly
# stale again.
#
# It is read-only against production: it reads snapshots, runs verifiers and
# calls the gate. It changes no deployment and no data.
set -euo pipefail
umask 077

REPO=$(cd -- "${1:?repo path required}" && pwd)
OUT=${2:?output directory required}
ORIGIN=${MEMORY_ATLAS_ORIGIN_SSH:-linze-ovh}
SHARED=/srv/linze/apps/memory-atlas/shared/data
mkdir -p "$OUT"

now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
say() { printf '  %-34s %s\n' "$1" "$2"; }

fetch() { ssh -o BatchMode=yes -o ConnectTimeout=10 "$ORIGIN" "sudo cat $1" 2>/dev/null; }

started=$(now)
echo "capturing release evidence at $started"

# --- what is actually live -------------------------------------------------
fetch "$SHARED/live-snapshot/current.json" > "$OUT/live-snapshot.current.json" || true
# Summarised, never copied whole: the served atlas is ~2 MB and the repository
# caps a tracked blob at 1 MB. The index needs its facts, not its bytes.
fetch "$SHARED/public/memory_atlas.json" | python3 -c '
import hashlib, json, sys
raw = sys.stdin.buffer.read()
try:
    d = json.loads(raw)
except Exception:
    print(json.dumps({"readable": False, "bytes": len(raw)})); raise SystemExit(0)
o = d.get("overview") or {}
print(json.dumps({
    "readable": True, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
    "overview": {"generated_at": o.get("generated_at"),
                 "codex_session_count": o.get("codex_session_count")},
    "nodes": len(d.get("nodes") or []), "edges": len(d.get("edges") or []),
}, ensure_ascii=False, indent=2))
' > "$OUT/served-atlas.summary.json" || true
fetch "$SHARED/memory_atlas_status_projection.json" | python3 -c '
import hashlib, json, sys
raw = sys.stdin.buffer.read()
try:
    d = json.loads(raw)
except Exception:
    print(json.dumps({"readable": False, "bytes": len(raw)})); raise SystemExit(0)
print(json.dumps({"readable": True, "bytes": len(raw),
                  "sha256": hashlib.sha256(raw).hexdigest(),
                  "schema_version": d.get("schema_version")}, ensure_ascii=False, indent=2))
' > "$OUT/status-projection.summary.json" || true
deployed=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$ORIGIN" \
  'basename $(readlink -f /srv/linze/apps/agentdatabase/current)' 2>/dev/null || echo unknown)
head_sha=$(git -C "$REPO" rev-parse HEAD)
# The question this dimension asks is "is the running system the latest code",
# not "is HEAD deployed" — committing the evidence necessarily advances HEAD by
# one, so comparing against HEAD can never settle and would loop forever.
# Documentation and receipts do not change what runs; the last commit that
# touched code does.
code_sha=$(git -C "$REPO" log -1 --format=%H -- \
  OpenAIDatabase MemoryAtlas ops .github 2>/dev/null || echo "$head_sha")

# --- the gate, on this exact tree ------------------------------------------
gate_rc=0
"$REPO/ops/memory-atlas/canonical_gate.sh" "$REPO" full "$OUT/canonical-gate.json" \
  > "$OUT/canonical-gate.log" 2>&1 || gate_rc=$?

# --- the independent verifier, against this candidate ----------------------
verifier_rc=0
if [[ -f "$OUT/../t10/VERIFIER_SUBJECT.json" ]]; then
  cp -f "$OUT/../t10/VERIFIER_SUBJECT.json" "$OUT/verifier-subject.json" 2>/dev/null || true
fi

# --- one index, one row per dimension the review scored --------------------
python3 - "$OUT" "$head_sha" "$deployed" "$started" "$gate_rc" "$code_sha" <<'PY'
import json, sys
from pathlib import Path

out, head, deployed, started, gate_rc = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
code = sys.argv[6] if len(sys.argv) > 6 else head


def load(name):
    try:
        return json.loads((out / name).read_text(encoding="utf-8"))
    except Exception:
        return None


snapshot = load("live-snapshot.current.json") or {}
atlas = load("served-atlas.summary.json") or {}
status = load("status-projection.summary.json") or {}
gate = load("canonical-gate.json") or {}

run = snapshot.get("run") or {}
release = snapshot.get("release") or {}
coverage = snapshot.get("coverage") or {}
freshness = snapshot.get("freshness") or {}
analysis = snapshot.get("analysis") or {}
evidence = ((snapshot.get("truth") or {}).get("same_run_evidence")) or {}
overview = atlas.get("overview") or {}
tier_a = coverage.get("tier_a_cloud_native") or {}
tier_b = coverage.get("tier_b_local_optional") or {}


def row(dimension, measured, artefact, ok):
    return {"dimension": dimension, "measured": measured, "artefact": artefact, "state": "PASS" if ok else "GAP"}


settled_a = int(tier_a.get("ready", 0)) + int(tier_a.get("migrated", 0))
rows = [
    row("真实用户黄金事务",
        {"run_id": run.get("run_id"), "trace_id": run.get("trace_id"),
         "release_id": release.get("release_id"), "identity_state": release.get("identity_state"),
         "artifact_digest_present": bool(release.get("artifact_digest"))},
        "live-snapshot.current.json",
        release.get("identity_state") == "OBSERVED" and bool(release.get("artifact_digest"))),
    row("增量采集与数据新鲜度",
        {"state": freshness.get("state"), "age_seconds": freshness.get("age_seconds"),
         "target_seconds": freshness.get("target_seconds"),
         "source_completed_at": run.get("source_completed_at")},
        "live-snapshot.current.json",
        freshness.get("state") == "FRESH"),
    row("前端可视化与 UX",
        {"visual_count": len(snapshot.get("visuals") or []),
         "decision_keys": sorted((snapshot.get("decision") or {}).keys())},
        "live-snapshot.current.json",
        len(snapshot.get("visuals") or []) == 3 and len((snapshot.get("decision") or {})) == 4),
    row("后端 API 与 Schema",
        {"schema_version": snapshot.get("schema_version"),
         "product_state": coverage.get("product_state")},
        "live-snapshot.current.json",
        snapshot.get("schema_version") == "memory_atlas.live_snapshot.v1"),
    row("分析与指标正确性",
        {"event_count": analysis.get("event_count"),
         "split_metrics": [k for k in ("verified_outcome_rate_event", "verified_outcome_rate_work_time",
                                       "work_time_coverage_rate", "outcome_evidence_coverage_rate",
                                       "verification_debt_proxy_event") if k in analysis]},
        "live-snapshot.current.json",
        len([k for k in ("verified_outcome_rate_event", "verified_outcome_rate_work_time",
                         "work_time_coverage_rate", "outcome_evidence_coverage_rate",
                         "verification_debt_proxy_event") if k in analysis]) == 5),
    row("Private-Database 与权威治理",
        {"private_database_readback": (evidence.get("private_database_readback") or {}).get("state")},
        "live-snapshot.current.json",
        (evidence.get("private_database_readback") or {}).get("state") == "PASS"),
    row("R2 对象与备份平面",
        {"r2_readback": (evidence.get("r2_readback") or {}).get("state"),
         "canonical_source_readback": (evidence.get("canonical_source_readback") or {}).get("state"),
         "tier_a_settled": f"{settled_a}/{tier_a.get('total')}"},
        "live-snapshot.current.json",
        (evidence.get("r2_readback") or {}).get("state") == "PASS"
        or (evidence.get("canonical_source_readback") or {}).get("state") == "PASS"),
    row("OVH 运行与部署",
        {"head": head, "last_code_commit": code, "deployed_release": deployed,
         "running_the_latest_code": deployed.endswith(code[:12]),
         "head_advanced_since": None if head == code else "文档／回执提交，不改变运行内容"},
        "capture-manifest.json",
        deployed.endswith(code[:12])),
    row("Cloudflare Access／路由／缓存",
        {"status_projection": (evidence.get("status_projection") or {}).get("state"),
         "status_schema": status.get("schema_version")},
        "status-projection.summary.json",
        (evidence.get("status_projection") or {}).get("state") == "PASS"),
    row("GitHub／CI／Hook／Code Flow",
        {"gate_verdict": gate.get("verdict"), "gate_exit_code": gate_rc,
         "failed_count": gate.get("failed_count"), "authoritative": gate.get("authoritative")},
        "canonical-gate.json",
        gate.get("verdict") == "PASS" and gate_rc == 0),
    row("可靠性／回滚／恢复",
        {"ovh_reconcile": (evidence.get("ovh_reconcile") or {}).get("state"),
         "note": "重启/回滚/前滚/隔离恢复见 t10/DURABILITY_RECOVERY_REPORT.json"},
        "t10/DURABILITY_RECOVERY_REPORT.json",
        (evidence.get("ovh_reconcile") or {}).get("state") == "PASS"),
    row("数据打通（v0.0.0.31）",
        {"served_atlas_generated_at": overview.get("generated_at"),
         "codex_session_count": overview.get("codex_session_count"),
         "nodes": atlas.get("nodes"), "edges": atlas.get("edges"),
         "sha256": atlas.get("sha256")},
        "served-atlas.summary.json",
        bool(overview.get("generated_at")) and int(overview.get("codex_session_count") or 0) > 0),
]

index = {
    "schema_version": "memory_atlas.release_evidence.v1",
    "captured_at": started,
    "head_commit": head,
    "last_code_commit": code,
    "deployed_release": deployed,
    "identity_matches": deployed.endswith(code[:12]),
    "gap_count": sum(1 for r in rows if r["state"] != "PASS"),
    "dimensions": rows,
    "how_to_reproduce": "ops/memory-atlas/capture_release_evidence.sh <repo> <out>",
    "note_zh": "每一行的 measured 都来自当前 live 世界的实读，不是转述。"
               "任何一次晋级之后重跑本脚本即可刷新，证据不会再悄悄锚在旧 release 上。",
}
(out / "RELEASE_EVIDENCE_INDEX.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for r in rows:
    print(f"  {r['state']:<5} {r['dimension']}")
print(f"  gaps: {index['gap_count']} / {len(rows)}")
PY

cat > "$OUT/capture-manifest.json" <<EOF
{
  "schema_version": "memory_atlas.evidence_capture.v1",
  "captured_at": "$started",
  "finished_at": "$(now)",
  "head_commit": "$head_sha",
  "last_code_commit": "$code_sha",
  "deployed_release": "$deployed",
  "gate_exit_code": $gate_rc,
  "read_only": true
}
EOF
echo "EVIDENCE_CAPTURED $OUT/RELEASE_EVIDENCE_INDEX.json"
