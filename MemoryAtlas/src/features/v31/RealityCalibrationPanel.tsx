import { useLiveSnapshot, type Metric, type Visual } from "./LiveSnapshotProvider";
import "./RealityCalibrationPanel.css";

function pct(value: number | null): string { return value === null ? "证据不足" : `${(value * 100).toFixed(1)}%`; }
function MetricCard({ metric, oracle }: { metric: Metric; oracle: string }) {
  return <article className="ma-metric" data-oracle={oracle} data-oracle-value={metric.value ?? "null"}>
    <p>{metric.label_zh}</p><strong>{pct(metric.value)}</strong>
    <span>{metric.numerator ?? "—"} / {metric.denominator ?? "—"}</span>
    <small>{metric.denominator_basis}{metric.proxy ? " · 代理指标" : ""}</small>
  </article>;
}
function Contribution({ visual }: { visual: Visual }) {
  return <div className="ma-contribution-grid">{visual.rows.map((raw, index) => {
    const row=raw as { activity_type?: string; event_count?: number; verified_count?: number; quality_score?: number | null };
    return <div className="ma-contribution-cell" key={`${row.activity_type}-${index}`} style={{ "--ma-strength": row.quality_score ?? 0 } as Record<string, number>}>
      <span>{row.activity_type ?? "未分类"}</span><strong>{row.verified_count ?? 0}</strong><small>{row.event_count ?? 0} 个事件 · 结果率 {pct(row.quality_score ?? null)}</small>
    </div>;
  })}</div>;
}
function Trend({ visual }: { visual: Visual }) {
  const rows = visual.rows.map((raw) => raw as { date?: string; event_count?: number; verified_count?: number; verification_debt_proxy_event?: number | null; time_to_truth_hours?: number | null; time_to_truth_sample_count?: number });
  const width = 680;
  const height = 240;
  const padX = 36;
  const padY = 28;
  const spanX = width - padX * 2;
  const spanY = height - padY * 2;
  const maxTruth = Math.max(1, ...rows.map((row) => row.time_to_truth_hours ?? 0));
  const x = (index: number) => rows.length <= 1 ? width / 2 : padX + (index / (rows.length - 1)) * spanX;
  const debtY = (value: number | null | undefined) => padY + (1 - Math.max(0, Math.min(1, value ?? 0))) * spanY;
  const truthY = (value: number | null | undefined) => value === null || value === undefined ? null : padY + (1 - Math.max(0, Math.min(1, value / maxTruth))) * spanY;
  const debtPath = rows.map((row, index) => `${index === 0 ? "M" : "L"}${x(index).toFixed(1)},${debtY(row.verification_debt_proxy_event).toFixed(1)}`).join(" ");
  const truthSegments: string[] = [];
  let open = false;
  rows.forEach((row, index) => {
    const y = truthY(row.time_to_truth_hours);
    if (y === null) { open = false; return; }
    truthSegments.push(`${open ? "L" : "M"}${x(index).toFixed(1)},${y.toFixed(1)}`);
    open = true;
  });
  return <div className="ma-trend">
    <div className="ma-trend-legend" aria-hidden="true"><span><i className="ma-legend-debt" />验证债务</span><span><i className="ma-legend-truth" />Time-to-Truth</span></div>
    <svg className="ma-trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="验证债务比例与可验证的 Time-to-Truth 趋势">
      {[0,0.25,0.5,0.75,1].map((value) => <line key={value} x1={padX} x2={width-padX} y1={debtY(value)} y2={debtY(value)} className="ma-chart-gridline" />)}
      <path d={debtPath} className="ma-line-debt" />
      {truthSegments.length > 0 && <path d={truthSegments.join(" ")} className="ma-line-truth" />}
      {rows.map((row,index) => <g key={`${row.date}-${index}`}>
        <circle cx={x(index)} cy={debtY(row.verification_debt_proxy_event)} r="4" className="ma-dot-debt"><title>{row.date}：验证债务 {pct(row.verification_debt_proxy_event ?? null)}</title></circle>
        {truthY(row.time_to_truth_hours) !== null && <circle cx={x(index)} cy={truthY(row.time_to_truth_hours) ?? 0} r="4" className="ma-dot-truth"><title>{row.date}：Time-to-Truth {row.time_to_truth_hours?.toFixed(1)} 小时</title></circle>}
      </g>)}
    </svg>
    <div className="ma-trend-list">{rows.map((row,index) => <div key={`${row.date}-${index}`}><time>{row.date}</time><span>债务 {pct(row.verification_debt_proxy_event ?? null)}</span><span>TTT {row.time_to_truth_hours === null || row.time_to_truth_hours === undefined ? "证据不足" : `${row.time_to_truth_hours.toFixed(1)}h`}</span><small>{row.time_to_truth_sample_count ?? 0} 个验证时间样本</small></div>)}</div>
  </div>;
}
function Heatmap({ visual }: { visual: Visual }) {
  return <div className="ma-table-wrap"><table className="ma-heatmap"><thead><tr><th>任务</th><th>模型／工具</th><th>结果</th><th>次数</th></tr></thead><tbody>{visual.rows.map((raw,index) => {
    const row=raw as { activity_type?: string; model_tool?: string; outcome_state?: string; count?: number };
    return <tr key={`${row.activity_type}-${row.model_tool}-${row.outcome_state}-${index}`}><td>{row.activity_type}</td><td>{row.model_tool}</td><td>{row.outcome_state}</td><td><span className="ma-heat" style={{ "--ma-strength": Math.min(1,(row.count ?? 0)/4) } as Record<string, number>}>{row.count ?? 0}</span></td></tr>;
  })}</tbody></table></div>;
}

export function RealityCalibrationPanel() {
  const { snapshot, lifecycle, error, clientReceivedAt, refresh } = useLiveSnapshot();
  if (!snapshot) return <section className="ma-reality-panel ma-loading" aria-live="polite"><h2>正在读取现实校准快照</h2><p>{error || "只接受完成态、同次运行且通过隐私校验的数据。"}</p><button type="button" onClick={() => void refresh()}>重新读取</button></section>;
  const visual = Object.fromEntries(snapshot.visuals.map((item) => [item.id,item])) as Record<Visual["id"],Visual>;
  return <section className="ma-reality-panel" aria-labelledby="ma-reality-title" data-run-id={snapshot.run.run_id} data-trace-id={snapshot.run.trace_id} data-release-id={snapshot.release.release_id ?? "UNVERIFIED"} data-deployment-revision={snapshot.release.deployment_revision ?? "UNVERIFIED"}>
    <header className="ma-reality-header"><div><p className="ma-eyebrow">Memory Atlas · 现实校准</p><h2 id="ma-reality-title">先看清现实，再决定下一步</h2><p>静态历史图谱继续保留；这里仅显示完成态实时快照与可核对结论。</p></div><button className="ma-refresh" type="button" onClick={() => void refresh()}>刷新事实</button></header>
    {lifecycle !== "ready" && <div className="ma-warning" role="status">当前为降级读取：{snapshot.freshness.reason_zh}{error ? `；${error}` : ""}</div>}
    {/* 四结论在上、真值带紧随其后：UI_UX_VISUAL_CONTRACT 要求第一屏先给结论，
        真值带每次渲染仍然完整显示，只是不再把结论挤到第一屏之外。 */}
    <div className="ma-answer-grid">
      {(["primary_use","verified_results","low_value_loop","top_action"] as const).map((key) => <article className={`ma-answer ${key === "top_action" ? "ma-answer-action" : ""}`} key={key}><p>{({primary_use:"主要用途",verified_results:"现实结果",low_value_loop:"最大缺口",top_action:"今天唯一动作"} as const)[key]}</p><h3>{snapshot.decision[key].title_zh}</h3><span>{snapshot.decision[key].detail_zh}</span></article>)}
    </div>
    <div className="ma-truth-ribbon" aria-label="数据真值带">
      <span><b>运行</b>{snapshot.run.run_id}</span><span><b>追踪</b>{snapshot.run.trace_id}</span><span><b>数据截止</b>{snapshot.run.source_completed_at}</span><span><b>年龄</b>{snapshot.freshness.age_seconds}s</span><span><b>Tier A</b>{snapshot.coverage.tier_a_cloud_native.ready}/{snapshot.coverage.tier_a_cloud_native.total}</span><span><b>Tier B</b>{snapshot.coverage.tier_b_local_optional.ready}/{snapshot.coverage.tier_b_local_optional.total}</span><span><b>发布</b>{snapshot.release.release_id ?? "未验证"}</span><span><b>部署</b>{snapshot.release.deployment_revision ?? "未验证"}</span><span><b>浏览器收到</b>{clientReceivedAt?.toISOString() ?? "—"}</span>
    </div>
    <div className="ma-metrics" data-oracle="event_count" data-oracle-value={snapshot.analysis.event_count}>
      <MetricCard metric={snapshot.analysis.verified_outcome_rate_event} oracle="verified_outcome_rate_event" />
      <MetricCard metric={snapshot.analysis.verified_outcome_rate_work_time} oracle="verified_outcome_rate_work_time" />
      <MetricCard metric={snapshot.analysis.work_time_coverage_rate} oracle="work_time_coverage_rate" />
      <MetricCard metric={snapshot.analysis.outcome_evidence_coverage_rate} oracle="outcome_evidence_coverage_rate" />
      <MetricCard metric={snapshot.analysis.verification_debt_proxy_event} oracle="verification_debt_proxy_event" />
    </div>
    <div className="ma-visual-grid" data-oracle="visual_count" data-oracle-value={snapshot.visuals.length}>
      <article className="ma-chart"><header><p>结果贡献</p><h3>{visual.quality_contribution_grid.title_zh}</h3></header><Contribution visual={visual.quality_contribution_grid} /></article>
      <article className="ma-chart"><header><p>闭环速度</p><h3>{visual.verification_debt_trend.title_zh}</h3></header><Trend visual={visual.verification_debt_trend} /></article>
      <article className="ma-chart ma-chart-wide"><header><p>方法适配</p><h3>{visual.task_tool_outcome_heatmap.title_zh}</h3></header><Heatmap visual={visual.task_tool_outcome_heatmap} /></article>
    </div>
    <article className="ma-benchmark" data-oracle="benchmark_state" data-oracle-value={snapshot.benchmarks.state}><div><p>全球公开参照</p><h3>{snapshot.benchmarks.state}</h3></div><p>{snapshot.benchmarks.limitations.join(" ")}</p><ul>{snapshot.benchmarks.comparisons.slice(0,4).map((row,index) => <li key={String(row.benchmark_id ?? index)}><b>{String(row.label_zh ?? row.benchmark_id ?? "参照")}</b><span>{String(row.comparability_state ?? "NOT_COMPARABLE")}</span><small>{String(row.reason_zh ?? "口径不足")}</small></li>)}</ul></article>
    <details className="ma-limitations"><summary>口径、限制和同次运行证据</summary><ul>{snapshot.truth.limitations.map((item) => <li key={item}>{item}</li>)}</ul><div className="ma-evidence-grid">{Object.entries(snapshot.truth.same_run_evidence).map(([name,value]) => <span key={name}><b>{name}</b>{value.state}</span>)}</div></details>
  </section>;
}
