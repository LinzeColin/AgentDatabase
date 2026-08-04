import { Database, HardDrive, RefreshCw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { usePrivateAnalytics } from "./PrivateAnalyticsProvider";
import { CoverageList, StateBanner } from "./shared";

export function RuntimeView() {
  const { snapshot, requestAction } = usePrivateAnalytics();
  const [message, setMessage] = useState("");
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
    { label: "本机采集", state: snapshot?.run.state ?? "未知", icon: HardDrive },
    { label: "R2 对象", state: snapshot?.run.objects?.length ? `${snapshot.run.objects.length} 个已登记` : "未知", icon: Database },
    { label: "Private-Database", state: snapshot ? "事实投影可读" : "未知", icon: ShieldCheck },
    { label: "OVH 处理", state: snapshot?.run.state === "REBUILT_FROM_AUTHORITIES" ? "已重建" : "等待运行证据", icon: RefreshCw },
  ], [snapshot]);
  return (
    <div className="ma31-view ma31-runtime" data-v31-view="runtime">
      <StateBanner />
      <header className="ma31-view-heading"><div><p className="ma31-kicker">运行 · 恢复 · 自愈</p><h1>系统运行</h1>
        <p>每一段都显示真实状态、时间、责任边界和失败恢复。点击“立即备份”只创建源端请求，不会把排队误报为成功。</p></div></header>
      <section className="ma31-runtime-chain">{chain.map(({ label, state, icon: Icon }) => <article key={label}>
        <Icon aria-hidden="true" size={22} /><b>{label}</b><span>{state}</span></article>)}</section>
      <section className="ma31-action-grid">
        <button disabled={busy !== null} onClick={() => void runAction("capture-request")} type="button"><HardDrive size={22} /><b>立即备份</b><span>创建本机源端采集请求</span></button>
        <button disabled={busy !== null} onClick={() => void runAction("diagnose")} type="button"><RefreshCw size={22} /><b>诊断并修复</b><span>只执行有界、安全、自证的修复</span></button>
        <button disabled={busy !== null} onClick={() => void runAction("restore-drill")} type="button"><ShieldCheck size={22} /><b>恢复演练</b><span>隔离重建并逐对象验哈希</span></button>
      </section>
      {message ? <div className="ma31-action-result" role="status">{message}</div> : null}
      <section className="ma31-two-column">
        <article className="ma31-panel"><header><div><p className="ma31-kicker">来源覆盖</p><h2>缺口必须可见</h2></div></header>
          <CoverageList rows={snapshot?.run.source_coverages ?? []} /></article>
        <article className="ma31-panel"><header><div><p className="ma31-kicker">权威边界</p><h2>不会出现第二事实源</h2></div></header>
          <dl className="ma31-authorities"><div><dt>全量事件字节</dt><dd>GitHub 私有仓 Release（2026-08-04 起，R2 因容量上限与收费风险已清空）</dd></div>
            <div><dt>长期结构化事实</dt><dd>GitHub 私有仓 Private-Database</dd></div>
            <div><dt>Cloudflare 与 OVH</dt><dd>只做入口、访问控制与计算，不承担数据存量</dd></div>
            <div><dt>运行队列与游标</dt><dd>OVH SQLite，可重建</dd></div>
            <div><dt>状态展示</dt><dd>status.linzezhang.com，只读投影</dd></div></dl>
        </article>
      </section>
    </div>
  );
}
