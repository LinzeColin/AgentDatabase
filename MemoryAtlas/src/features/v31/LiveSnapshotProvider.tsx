import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

export type Metric = { value: number | null; numerator: number | null; denominator: number | null; denominator_basis: string; label_zh: string; proxy: boolean };
export type Visual = { id: "quality_contribution_grid" | "verification_debt_trend" | "task_tool_outcome_heatmap"; title_zh: string; kind: "GRID" | "TREND" | "HEATMAP"; rows: Array<Record<string, unknown>> };
export type LiveSnapshot = {
  schema_version: "memory_atlas.live_snapshot.v1";
  generated_at: string;
  run: { run_id: string; trace_id: string; source_state: "SUCCEEDED" | "REBUILT_FROM_AUTHORITIES"; source_started_at: string | null; source_completed_at: string; reconciled_at: string | null };
  release: { identity_state: "VERIFIED" | "OBSERVED" | "UNVERIFIED"; repository_commit: string | null; release_id: string | null; artifact_digest: string | null; deployment_revision: string | null };
  freshness: { state: "FRESH" | "DEGRADED" | "STALE" | "UNKNOWN"; evaluated_at: string; age_seconds: number; target_seconds: number; reason_zh: string };
  coverage: { product_state: "PASS" | "DEGRADED" | "WAITING_SOURCE" | "FAILED" | "UNKNOWN"; tier_a_cloud_native: Record<string, number>; tier_b_local_optional: Record<string, number>; sources: Array<Record<string, unknown>> };
  analysis: { event_count: number; event_window: { start_at: string | null; end_at: string | null }; activity_distribution: Array<{ key: string; label_zh: string; count: number; share: number | null }>; outcome_distribution: Record<string, number>; verified_outcome_rate_event: Metric; verified_outcome_rate_work_time: Metric; work_time_coverage_rate: Metric; outcome_evidence_coverage_rate: Metric; verification_debt_proxy_event: Metric; failure_compound: Record<string, number | null> };
  decision: { primary_use: Record<string, unknown> & { title_zh: string; detail_zh: string }; verified_results: Record<string, unknown> & { title_zh: string; detail_zh: string }; low_value_loop: Record<string, unknown> & { title_zh: string; detail_zh: string }; top_action: Record<string, unknown> & { title_zh: string; detail_zh: string; recommendation_id?: string } };
  visuals: Visual[];
  benchmarks: { state: "DIRECTLY_COMPARABLE" | "DIRECTION_ONLY" | "NOT_COMPARABLE" | "INSUFFICIENT_DATA"; comparisons: Array<Record<string, unknown>>; limitations: string[] };
  truth: { metric_contract_version: string; historical_snapshot_role: string; limitations: string[]; same_run_evidence: Record<string, { state: string; run_id: string | null; trace_id: string | null; ref: string | null }> };
  privacy: { raw_content_included: false; secret_values_included: false; private_paths_included: false; object_keys_included: false };
};

type Lifecycle = "loading" | "ready" | "degraded" | "error";
type ContextValue = { snapshot: LiveSnapshot | null; lifecycle: Lifecycle; error: string; clientReceivedAt: Date | null; refresh: () => Promise<void> };
const LiveSnapshotContext = createContext<ContextValue | null>(null);

function assertSnapshot(value: unknown): asserts value is LiveSnapshot {
  if (!value || typeof value !== "object") throw new Error("LiveSnapshot 必须是对象");
  const row = value as Partial<LiveSnapshot>;
  if (row.schema_version !== "memory_atlas.live_snapshot.v1") throw new Error("LiveSnapshot Schema 不匹配");
  if (!row.run?.run_id || !row.run.trace_id || !row.run.source_completed_at) throw new Error("LiveSnapshot 运行身份不完整");
  if (!row.release || row.visuals?.length !== 3) throw new Error("LiveSnapshot 发布身份或三图合同不完整");
  const ids = new Set(row.visuals.map((item) => item.id));
  if (ids.size !== 3 || !ids.has("quality_contribution_grid") || !ids.has("verification_debt_trend") || !ids.has("task_tool_outcome_heatmap")) throw new Error("LiveSnapshot 可视化合同不匹配");
  if (row.privacy?.raw_content_included !== false || row.privacy?.secret_values_included !== false || row.privacy?.private_paths_included !== false || row.privacy?.object_keys_included !== false) throw new Error("LiveSnapshot 隐私合同失败");
}

function header(response: Response, name: string): string { return response.headers.get(name) ?? ""; }

export function LiveSnapshotProvider({ children, endpoint = "/api/v31/live-snapshot", pollIntervalMs = 60_000 }: PropsWithChildren<{ endpoint?: string; pollIntervalMs?: number }>) {
  const [snapshot, setSnapshot] = useState<LiveSnapshot | null>(null);
  const [lifecycle, setLifecycle] = useState<Lifecycle>("loading");
  const [error, setError] = useState("");
  const [clientReceivedAt, setClientReceivedAt] = useState<Date | null>(null);
  const lastGoodRef = useRef<LiveSnapshot | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    if (!lastGoodRef.current) setLifecycle("loading");
    try {
      const response = await fetch(endpoint, { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" }, signal: controller.signal });
      if (!response.ok) throw new Error(`实时快照读取失败（HTTP ${response.status}）`);
      if (!header(response, "Cache-Control").toLowerCase().includes("no-store")) throw new Error("实时快照缺少 no-store，拒绝把缓存冒充当前数据");
      const candidate: unknown = await response.json();
      assertSnapshot(candidate);
      const identities = {
        run: header(response, "X-Memory-Atlas-Run-Id"),
        trace: header(response, "X-Memory-Atlas-Trace-Id"),
        release: header(response, "X-Memory-Atlas-Release-Id"),
        deployment: header(response, "X-Memory-Atlas-Deployment-Revision"),
      };
      if (identities.run !== candidate.run.run_id || identities.trace !== candidate.run.trace_id) throw new Error("API Header 与 Body 运行身份不一致");
      if (candidate.release.release_id && identities.release !== candidate.release.release_id) throw new Error("API Header 与 Body 发布身份不一致");
      if (candidate.release.deployment_revision && identities.deployment !== candidate.release.deployment_revision) throw new Error("API Header 与 Body 部署身份不一致");
      const previous = lastGoodRef.current;
      if (previous && Date.parse(candidate.run.source_completed_at) < Date.parse(previous.run.source_completed_at)) throw new Error("服务器返回更旧快照，已拒绝时间倒退");
      lastGoodRef.current = candidate;
      setSnapshot(candidate);
      setClientReceivedAt(new Date());
      setError("");
      setLifecycle(candidate.freshness.state === "FRESH" && candidate.coverage.product_state === "PASS" ? "ready" : "degraded");
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      const message = reason instanceof Error ? reason.message : "未知实时快照错误";
      setError(message);
      if (lastGoodRef.current) { setSnapshot(lastGoodRef.current); setLifecycle("degraded"); }
      else { setSnapshot(null); setLifecycle("error"); }
    }
  }, [endpoint]);

  useEffect(() => {
    void refresh();
    const interval = pollIntervalMs > 0 ? window.setInterval(() => {
      if (document.visibilityState === "visible" && navigator.onLine) void refresh();
    }, Math.max(15_000, pollIntervalMs)) : null;
    const onVisibility = () => { if (document.visibilityState === "visible" && navigator.onLine) void refresh(); };
    const onOnline = () => { if (document.visibilityState === "visible") void refresh(); };
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("online", onOnline);
    return () => {
      if (interval !== null) window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("online", onOnline);
      controllerRef.current?.abort();
    };
  }, [pollIntervalMs, refresh]);

  const value = useMemo(() => ({ snapshot, lifecycle, error, clientReceivedAt, refresh }), [snapshot, lifecycle, error, clientReceivedAt, refresh]);
  return <LiveSnapshotContext.Provider value={value}>{children}</LiveSnapshotContext.Provider>;
}

export function useLiveSnapshot(): ContextValue {
  const value = useContext(LiveSnapshotContext);
  if (!value) throw new Error("useLiveSnapshot 必须位于 LiveSnapshotProvider 内");
  return value;
}
