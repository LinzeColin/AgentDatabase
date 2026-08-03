import { AlertTriangle, CheckCircle2, CircleHelp, Database, HardDrive, RefreshCw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { usePrivateAnalytics } from "./PrivateAnalyticsProvider";
import type { SourceCoverageV31 } from "./contracts";

const activityLabels: Record<string, string> = {
  research_diagnosis: "研究与诊断",
  product_planning: "产品与规划",
  development_deployment: "开发与部署",
  verification_repair: "验证与修复",
  management_learning: "学习与管理",
  decision_execution: "决策与执行",
  unknown: "未分类",
};

function formatPercent(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "未知";
}

function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString("zh-CN") : "未知";
}

function StateBanner() {
  const { state, error, refresh } = usePrivateAnalytics();
  if (state === "ready") return null;
  const content = state === "loading"
    ? "正在读取最新私有分析快照。"
    : state === "unknown"
      ? "尚无可验证的私有分析快照；系统不会用演示数据冒充生产事实。"
      : `私有分析快照读取失败：${error ?? "未知错误"}`;
  return <div className={`ma31-state-banner ${state}`}><CircleHelp aria-hidden="true" size={18} /><span>{content}</span><button onClick={() => void refresh()} type="button">重新读取</button></div>;
}

function MetricCard({ label, value, note }: { label: string; value: string; note: string }) {
  return <article className="ma31-metric"><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

function CoverageList({ rows }: { rows: SourceCoverageV31[] }) {
  if (!rows.length) return <p className="ma31-empty">暂无来源覆盖事实。</p>;
  return <div className="ma31-coverage-list">{rows.map((row) => {
    const ok = row.state === "READY";
    return <div className="ma31-coverage-row" key={row.source_id}><span className={ok ? "ma31-state-ok" : "ma31-state-gap"}>{ok ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}{row.state}</span><div><b>{row.label_zh}</b><p>{row.message_zh}</p></div><span>{formatNumber(row.object_count)} 个</span></div>;
  })}</div>;
}

export function TodayView() {
  const { snapshot } = usePrivateAnalytics();
  const behavior = snapshot?.behavior_economics;
  const compound = snapshot?.failure_compound;
  const coverages = snapshot?.run.source_coverages ?? [];
  const ready = coverages.filter((row) => row.state === "READY").length;
  return <div className="ma31-view ma31-today"><StateBanner /><section className="ma31-hero"><div><p className="ma31-kicker">今日现实 · 证据优先</p><h1>看见哪些投入<br />真正变成了结果。</h1><p>记忆、失败、行为与运行被放在同一事实链上。所有未知、缺口和等待来源均保持可见。</p></div><div className="ma31-hero-orbit" aria-hidden="true"><i /><i /><i /><span>Verified<br />Outcome</span></div></section><section className="ma31-metrics"><MetricCard label="已验证成果率" value={formatPercent(behavior?.verified_outcome_rate.value)} note={behavior?.verified_outcome_rate.denominator_type === "effort_minutes" ? "按已记录投入分钟" : "按可观察事件"} /><MetricCard label="失败复利分" value={compound?.compound_score == null ? "未知" : String(compound.compound_score)} note="Fixture、Oracle、红绿证据与阻断" /><MetricCard label="已阻止重复错误" value={formatNumber(compound?.metrics.blocked_recurrences)} note="由故障注入或真实回归证明" /><MetricCard label="来源覆盖" value={coverages.length ? `${ready}/${coverages.length}` : "未知"} note="缺失来源不会被算作成功" /></section><section className="ma31-two-column"><article className="ma31-panel"><header><div><p className="ma31-kicker">下一步</p><h2>只显示最多三项可验证建议</h2></div></header><div className="ma31-recommendations">{behavior?.recommendations?.length ? behavior.recommendations.slice(0, 3).map((item) => <article key={item.recommendation_id}><b>{item.action}</b><p>{item.fact}</p><small>成功指标：{item.success_metric} · {item.observation_window_days} 天 · 置信度 {item.confidence}</small><details><summary>反例与回滚</summary><p>{item.alternative_explanation}</p><p>{item.rollback}</p></details></article>) : <p className="ma31-empty">当前证据不足，暂不生成建议。</p>}</div></article><article className="ma31-panel"><header><div><p className="ma31-kicker">数据来源</p><h2>全量不是一句绿灯</h2></div></header><CoverageList rows={coverages} /></article></section></div>;
}

export function FailureCompoundView() {
  const { snapshot } = usePrivateAnalytics();
  const compound = snapshot?.failure_compound;
  const metrics = compound?.metrics;
  return <div className="ma31-view"><StateBanner /><header className="ma31-view-heading"><div><p className="ma31-kicker">Failure-to-Regression Compound Engine</p><h1>失败复利</h1><p>每一次失败都必须变成可复现、可验证、长期运行的回归资产。</p></div><div className="ma31-score-ring"><strong>{compound?.compound_score ?? "?"}</strong><span>复利分</span></div></header><section className="ma31-metrics"><MetricCard label="Incident" value={formatNumber(metrics?.incident_count)} note="同类错误按签名去重" /><MetricCard label="活跃回归资产" value={formatNumber(metrics?.active_regression_assets)} note="Fixture＋Oracle＋测试" /><MetricCard label="最后一次通过率" value={formatPercent(metrics?.last_pass_rate)} note="未运行不计通过" /><MetricCard label="同类不复发率" value={formatPercent(metrics?.nonrecurrence_ratio)} note="已阻止 ÷（已阻止＋复发）" /></section><section className="ma31-compound-flow" aria-label="失败复利流水线"><div><b>1</b><span>原始证据</span></div><div><b>2</b><span>错误签名</span></div><div><b>3</b><span>最小复现</span></div><div><b>4</b><span>修复前红灯</span></div><div><b>5</b><span>修复后转绿</span></div><div><b>6</b><span>长期阻断</span></div></section><section className="ma31-panel"><header><div><p className="ma31-kicker">长期回归资产账本</p><h2>Incident → Regression Asset</h2></div></header><div className="ma31-table-scroll"><table><thead><tr><th>错误模式</th><th>类别</th><th>首次发生</th><th>复发</th><th>回归资产</th><th>状态</th></tr></thead><tbody>{compound?.incidents?.length ? compound.incidents.map((row, index) => <tr key={String(row.incident_id ?? index)}><td>{String(row.title ?? "未知")}</td><td>{String(row.category ?? "未知")}</td><td>{String(row.first_seen ?? "未知")}</td><td>{formatNumber(row.recurrence_count)}</td><td>{String(row.regression_asset_id ?? "未形成")}</td><td>{String(row.status ?? "UNKNOWN")}</td></tr>) : <tr><td colSpan={6}>暂无可验证 Incident。</td></tr>}</tbody></table></div><p className="ma31-formula">{compound?.formula ?? "复利分公式尚不可验证"}</p></section></div>;
}

export function EconomyView() {
  const { snapshot } = usePrivateAnalytics();
  const behavior = snapshot?.behavior_economics;
  const activities = Object.entries(behavior?.activity_distribution ?? {});
  return <div className="ma31-view"><StateBanner /><header className="ma31-view-heading"><div><p className="ma31-kicker">Observed Usage · Transparent Comparison</p><h1>行为经济</h1><p>从真实可观察使用开始，按工作活动、AI 使用方式和现实结果分层。没有同口径总体时禁止生成全球百分位。</p></div></header><section className="ma31-two-column"><article className="ma31-panel"><header><div><p className="ma31-kicker">工作活动</p><h2>最近快照的活动分布</h2></div></header><div className="ma31-bars">{activities.length ? activities.map(([key, value]) => <div className="ma31-bar" key={key}><span>{activityLabels[key] ?? key}</span><div><i style={{ width: `${Math.max(0, Math.min(100, (value.share ?? 0) * 100))}%` }} /></div><b>{formatPercent(value.share)}</b></div>) : <p className="ma31-empty">暂无活动分布。</p>}</div></article><article className="ma31-panel"><header><div><p className="ma31-kicker">核心结果</p><h2>Verified Outcome Rate</h2></div></header><div className="ma31-vor"><strong>{formatPercent(behavior?.verified_outcome_rate.value)}</strong><p>{formatNumber(behavior?.verified_outcome_rate.numerator)} / {formatNumber(behavior?.verified_outcome_rate.denominator)}</p><small>分母类型：{behavior?.verified_outcome_rate.denominator_type ?? "未知"}</small></div><div className="ma31-comparability"><ShieldCheck size={22} /><div><b>全球比较门</b><p>分类法、单位、时间窗、总体范围和样本数必须同时一致；否则只展示方向参考。</p></div></div></article></section><section className="ma31-panel"><header><div><p className="ma31-kicker">AI 使用方式</p><h2>增强、自动化与混合</h2></div></header><div className="ma31-metrics compact">{Object.entries(behavior?.augmentation_distribution ?? {}).map(([key, value]) => <MetricCard key={key} label={key} value={formatPercent(value.share)} note={`${value.count} 个可观察事件`} />)}</div></section></div>;
}

export function RuntimeView() {
  const { snapshot, requestAction } = usePrivateAnalytics();
  const [message, setMessage] = useState<string>("");
  const [busy, setBusy] = useState<string | null>(null);
  const runAction = async (action: "capture-request" | "diagnose" | "restore-drill") => {
    setBusy(action); setMessage("");
    try {
      const result = await requestAction(action);
      setMessage(`${result.request_id} · ${result.state} · ${result.message_zh}`);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(null); }
  };
  const chain = useMemo(() => [
    { label: "本机采集", state: snapshot?.run.state ?? "UNKNOWN", icon: HardDrive },
    { label: "R2 对象", state: snapshot?.run.objects?.length ? `${snapshot.run.objects.length} 个已登记` : "UNKNOWN", icon: Database },
    { label: "Private-Database", state: snapshot ? "事实投影可读" : "UNKNOWN", icon: ShieldCheck },
    { label: "OVH 处理", state: snapshot?.run.state === "REBUILT_FROM_AUTHORITIES" ? "已重建" : "等待运行证据", icon: RefreshCw },
  ], [snapshot]);
  return <div className="ma31-view"><StateBanner /><header className="ma31-view-heading"><div><p className="ma31-kicker">Runtime · Recovery · Self-heal</p><h1>系统运行</h1><p>每一段都显示真实状态、时间、责任边界和失败恢复。点击“立即备份”只创建源端请求，不会把排队误报为成功。</p></div></header><section className="ma31-runtime-chain">{chain.map(({ label, state, icon: Icon }) => <article key={label}><Icon aria-hidden="true" size={22} /><b>{label}</b><span>{state}</span></article>)}</section><section className="ma31-action-grid"><button disabled={busy !== null} onClick={() => void runAction("capture-request")} type="button"><HardDrive size={22} /><b>立即备份</b><span>创建本机源端采集请求</span></button><button disabled={busy !== null} onClick={() => void runAction("diagnose")} type="button"><RefreshCw size={22} /><b>诊断并修复</b><span>只执行有界、安全、自证的修复</span></button><button disabled={busy !== null} onClick={() => void runAction("restore-drill")} type="button"><ShieldCheck size={22} /><b>恢复演练</b><span>隔离重建并逐对象验哈希</span></button></section>{message ? <div className="ma31-action-result" role="status">{message}</div> : null}<section className="ma31-panel"><header><div><p className="ma31-kicker">权威边界</p><h2>不会出现第二事实源</h2></div></header><dl className="ma31-authorities"><div><dt>对象字节</dt><dd>Cloudflare R2 `primary-objects/`</dd></div><div><dt>长期结构化事实</dt><dd>Private-Database / Private-AgentDatabase</dd></div><div><dt>运行队列与游标</dt><dd>OVH SQLite，可重建</dd></div><div><dt>状态展示</dt><dd>status.linzezhang.com，只读投影</dd></div></dl></section></div>;
}
