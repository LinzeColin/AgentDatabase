import { humanizeMachineText } from "../../shared/atlas/machineTokenHuman";
import { ShieldCheck } from "lucide-react";
import { usePrivateAnalytics } from "./PrivateAnalyticsProvider";
import { StateBanner, MetricCard, activityLabels, formatNumber, formatPercent } from "./shared";

export function BehaviorEconomyView() {
  const { snapshot } = usePrivateAnalytics();
  const behavior = snapshot?.behavior_economics;
  const activities = Object.entries(behavior?.activity_distribution ?? {});
  return (
    <div className="ma31-view ma31-behavior-economy" data-v31-view="behaviorEconomy">
      <StateBanner />
      <header className="ma31-view-heading"><div><p className="ma31-kicker">可观察使用 · 透明比较</p>
        <h1>行为经济</h1><p>从真实可观察使用开始，按工作活动、AI 使用方式和现实结果分层。没有同口径总体时禁止生成全球百分位。</p></div></header>
      <section className="ma31-two-column">
        <article className="ma31-panel"><header><div><p className="ma31-kicker">工作活动</p><h2>最近快照的活动分布</h2></div></header>
          <div className="ma31-bars">{activities.length ? activities.map(([key, value]) => <div className="ma31-bar" key={key}>
            <span>{activityLabels[key] ?? humanizeMachineText(key)}</span><div><i style={{ width: `${Math.max(0, Math.min(100, (value.share ?? 0) * 100))}%` }} /></div><b>{formatPercent(value.share)}</b>
          </div>) : <p className="ma31-empty">暂无活动分布。</p>}</div>
        </article>
        <article className="ma31-panel"><header><div><p className="ma31-kicker">核心结果</p><h2>已验证结果率</h2></div></header>
          <div className="ma31-vor"><strong>{formatPercent(behavior?.verified_outcome_rate.value)}</strong>
            <p>{formatNumber(behavior?.verified_outcome_rate.numerator)} / {formatNumber(behavior?.verified_outcome_rate.denominator)}</p>
            <small>分母类型：{humanizeMachineText(behavior?.verified_outcome_rate.denominator_type ?? "未知")}</small></div>
          <div className="ma31-comparability"><ShieldCheck size={22} /><div><b>全球比较门</b><p>分类法、单位、时间窗、总体范围和样本数必须同时一致；否则只展示方向参考。</p></div></div>
        </article>
      </section>
      <section className="ma31-panel"><header><div><p className="ma31-kicker">AI 使用方式</p><h2>增强、自动化与混合</h2></div></header>
        <div className="ma31-metrics compact">{Object.entries(behavior?.augmentation_distribution ?? {}).map(([key, value]) =>
          <MetricCard key={key} label={humanizeMachineText(key)} value={formatPercent(value.share)} note={`${value.count} 个可观察事件`} />)}</div>
      </section>
    </div>
  );
}