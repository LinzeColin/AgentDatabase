import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ActionResponseV31, PrivateAnalyticsSnapshotV31 } from "./contracts";

interface PrivateAnalyticsContextValue {
  snapshot: PrivateAnalyticsSnapshotV31 | null;
  state: "loading" | "ready" | "unknown" | "error";
  error: string | null;
  refresh: () => Promise<void>;
  requestAction: (action: "capture-request" | "diagnose" | "restore-drill") => Promise<ActionResponseV31>;
}

const Context = createContext<PrivateAnalyticsContextValue | null>(null);

function isSnapshot(value: unknown): value is PrivateAnalyticsSnapshotV31 {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const row = value as Record<string, unknown>;
  const contract = row.source_contract as Record<string, unknown> | undefined;
  return (
    row.schema_version === "memory_atlas.private_analytics.v1" &&
    contract?.mode === "private_full_fidelity_read_only_analytics" &&
    contract.direct_stable_memory_mutation === false &&
    Boolean(row.behavior_economics) &&
    Boolean(row.failure_compound)
  );
}

async function fetchSnapshot(signal?: AbortSignal): Promise<PrivateAnalyticsSnapshotV31 | null> {
  const url = new URL("/api/v31/status", window.location.origin);
  url.searchParams.set("revision", String(Date.now()));
  const response = await fetch(url, {
    cache: "no-store",
    credentials: "same-origin",
    signal,
    headers: { "Cache-Control": "no-cache" },
  });
  if (response.status === 404) return null;
  if (response.status === 403) throw new Error("私有分析读取未通过 Cloudflare Access 身份验证");
  if (!response.ok) throw new Error(`私有分析快照读取失败（${response.status}）`);
  const payload: unknown = await response.json();
  if (!isSnapshot(payload)) throw new Error("私有分析快照未通过运行时契约");
  return payload;
}

export function PrivateAnalyticsProvider({ children }: PropsWithChildren) {
  const [snapshot, setSnapshot] = useState<PrivateAnalyticsSnapshotV31 | null>(null);
  const [state, setState] = useState<PrivateAnalyticsContextValue["state"]>("loading");
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    setState("loading");
    setError(null);
    try {
      const next = await fetchSnapshot();
      setSnapshot(next);
      setState(next ? "ready" : "unknown");
    } catch (reason) {
      setSnapshot(null);
      setError(reason instanceof Error ? reason.message : String(reason));
      setState("error");
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    fetchSnapshot(controller.signal)
      .then((next) => {
        setSnapshot(next);
        setState(next ? "ready" : "unknown");
      })
      .catch((reason) => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : String(reason));
        setState("error");
      });
    return () => controller.abort();
  }, []);
  const requestAction = useCallback(async (action: "capture-request" | "diagnose" | "restore-drill") => {
    const idempotencyKey = `${action}:${new Date().toISOString().slice(0, 16)}`;
    const response = await fetch(`/api/v31/actions/${action}`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    });
    const payload: unknown = await response.json();
    if (!response.ok || !payload || typeof payload !== "object") {
      throw new Error(`动作请求失败（${response.status}）`);
    }
    return payload as ActionResponseV31;
  }, []);
  const value = useMemo(() => ({ snapshot, state, error, refresh, requestAction }), [error, refresh, requestAction, snapshot, state]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function usePrivateAnalytics(): PrivateAnalyticsContextValue {
  const value = useContext(Context);
  if (!value) throw new Error("usePrivateAnalytics must be used inside PrivateAnalyticsProvider");
  return value;
}
