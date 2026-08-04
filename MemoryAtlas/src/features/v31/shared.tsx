import { humanizeMachineText } from "../../shared/atlas/machineTokenHuman";
import { AlertTriangle, CheckCircle2, CircleHelp } from "lucide-react";
import { usePrivateAnalytics } from "./PrivateAnalyticsProvider";
import type { SourceCoverageV31 } from "./contracts";

export const activityLabels: Record<string, string> = {
  research_diagnosis: "研究与诊断",
  product_planning: "产品与规划",
  development_deployment: "开发与部署",
  verification_repair: "验证与修复",
  management_learning: "学习与管理",
  decision_execution: "决策与执行",
  unknown: "未分类",
};

export function formatPercent(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "未知";
}

export function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("zh-CN") : "未知";
}

export function StateBanner() {
  const { state, error, refresh } = usePrivateAnalytics();
  if (state === "ready") return null;
  const content = state === "loading"
    ? "正在读取最新私有分析快照；原 Memory Atlas 仍可正常使用。"
    : state === "unknown"
      ? "新增私有分析尚未接通；系统不会用演示数据冒充生产事实，原 Memory Atlas 不受影响。"
      : `新增私有分析读取失败：${error ?? "未知错误"}。原 Memory Atlas 不受影响。`;
  return <div className={`ma31-state-banner ${state}`} role="status"><CircleHelp aria-hidden="true" size={18} />
    <span>{content}</span><button onClick={() => void refresh()} type="button">重新读取</button></div>;
}

export function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="ma31-metric"><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

export function CoverageList({ rows }: { rows: SourceCoverageV31[] }) {
  if (!rows.length) return <p className="ma31-empty">暂无来源覆盖事实。</p>;
  return <div className="ma31-coverage-list">{rows.map((row) => {
    const ok = row.state === "READY";
    return <div className="ma31-coverage-row" key={row.source_id}>
      <span className={ok ? "ma31-state-ok" : "ma31-state-gap"}>{ok ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}{humanizeMachineText(row.state)}</span>
      <div><b>{row.label_zh}</b><p>{row.message_zh}</p></div><span>{formatNumber(row.object_count)} 个</span>
    </div>;
  })}</div>;
}