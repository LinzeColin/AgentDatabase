import { StateBanner, MetricCard, formatNumber, formatPercent } from "./shared";
import { usePrivateAnalytics } from "./PrivateAnalyticsProvider";

export function FailureCompoundView() {
  const { snapshot } = usePrivateAnalytics();
  const compound = snapshot?.failure_compound;
  const metrics = compound?.metrics;
  return (
    <div className="ma31-view ma31-failure-compound" data-v31-view="failureCompound">
      <StateBanner />
      <header className="ma31-view-heading">
        <div><p className="ma31-kicker">Failure-to-Regression Compound Engine</p><h1>失败复利</h1>
          <p>每一次失败都必须变成可复现、可验证、长期运行的回归资产；相同错误以后更难再次发生。</p></div>
        <div className="ma31-score-ring"><strong>{compound?.compound_score ?? "?"}</strong><span>复利分</span></div>
      </header>
      <section className="ma31-metrics">
        <MetricCard label="Incident" value={formatNumber(metrics?.incident_count)} note="同类错误按签名去重" />
        <MetricCard label="活跃回归资产" value={formatNumber(metrics?.active_regression_assets)} note="Fixture＋Oracle＋测试" />
        <MetricCard label="最后一次通过率" value={formatPercent(metrics?.last_pass_rate)} note="未运行不计通过" />
        <MetricCard label="同类不复发率" value={formatPercent(metrics?.nonrecurrence_ratio)} note="已阻止 ÷（已阻止＋复发）" />
      </section>
      <section className="ma31-compound-flow" aria-label="失败复利流水线">
        {[["1","原始证据"],["2","错误签名"],["3","最小复现"],["4","修复前红灯"],["5","修复后转绿"],["6","长期阻断"]].map(([n,label]) =>
          <div key={n}><b>{n}</b><span>{label}</span></div>)}
      </section>
      <section className="ma31-panel">
        <header><div><p className="ma31-kicker">长期回归资产账本</p><h2>Incident → Regression Asset</h2></div></header>
        <div className="ma31-table-scroll"><table><thead><tr><th>错误模式</th><th>类别</th><th>首次发生</th><th>复发</th><th>回归资产</th><th>状态</th></tr></thead>
          <tbody>{compound?.incidents?.length ? compound.incidents.map((row, index) => <tr key={String(row.incident_id ?? index)}>
            <td>{String(row.title ?? "未知")}</td><td>{String(row.category ?? "未知")}</td><td>{String(row.first_seen ?? "未知")}</td>
            <td>{formatNumber(row.recurrence_count)}</td><td>{String(row.regression_asset_id ?? "未形成")}</td><td>{String(row.status ?? "UNKNOWN")}</td>
          </tr>) : <tr><td colSpan={6}>暂无可验证 Incident。</td></tr>}</tbody></table></div>
        <p className="ma31-formula">{compound?.formula ?? "复利分公式尚不可验证"}</p>
      </section>
    </div>
  );
}
