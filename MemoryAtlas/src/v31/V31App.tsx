import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { Activity, Archive, CircleDot, Command, ShieldCheck } from "lucide-react";
import { PrimaryNavigation } from "./PrimaryNavigation";
import { PrivateAnalyticsProvider, usePrivateAnalytics } from "./PrivateAnalyticsProvider";
import { ThemeControls } from "./ThemeControls";
import { V31ThemeProvider, useV31Theme } from "./ThemeContext";
import { EconomyView, FailureCompoundView, RuntimeView, TodayView } from "./V31Views";
import type { V31PrimaryView } from "./contracts";
import "./v31.css";

const VIEW_KEY = "memory-atlas-v31-primary-view";
const primaryViews: V31PrimaryView[] = ["today", "universe", "compound", "economy", "runtime"];

function initialView(): V31PrimaryView {
  const hash = window.location.hash.slice(1);
  if (primaryViews.includes(hash as V31PrimaryView)) return hash as V31PrimaryView;
  const stored = window.localStorage.getItem(VIEW_KEY);
  return primaryViews.includes(stored as V31PrimaryView) ? (stored as V31PrimaryView) : "today";
}

function ViewContent({ active, legacy }: { active: V31PrimaryView; legacy: ReactNode }) {
  if (active === "today") return <TodayView />;
  if (active === "universe") {
    return (
      <section className="ma31-universe" aria-label="原有 Memory Atlas 完整工作区">
        <header className="ma31-universe-intro">
          <div>
            <p className="ma31-kicker">Existing Memory Atlas Preserved</p>
            <h1>记忆探索工作区</h1>
          </div>
          <p>Galaxy、Obsidian、Notion Map、ROI、时间线、贡献图、词云、搜索复审、总结迭代和提案流程全部原样保留。</p>
        </header>
        <div className="ma31-legacy-boundary" data-existing-memory-atlas-preserved="true">{legacy}</div>
      </section>
    );
  }
  if (active === "compound") return <FailureCompoundView />;
  if (active === "economy") return <EconomyView />;
  return <RuntimeView />;
}

function FreshnessChip() {
  const { snapshot, state } = usePrivateAnalytics();
  const label = state === "ready" ? snapshot?.run.state ?? "READY" : state.toUpperCase();
  return <span className={`ma31-freshness state-${state}`}><i aria-hidden="true" />{label}</span>;
}

function Brand({ theme }: { theme: "A" | "B" | "C" }) {
  const Icon = theme === "A" ? CircleDot : theme === "B" ? Archive : Command;
  const subtitle = theme === "A" ? "星海观测站" : theme === "B" ? "复利研究院" : "白箱指挥舱";
  return <div className="ma31-brand"><span className="ma31-brand-mark"><Icon aria-hidden="true" size={19} /></span><div><b>Memory Atlas</b><small>{subtitle} · v0.0.0.31</small></div></div>;
}

function Shell({ legacy }: { legacy: ReactNode }) {
  const { theme, mode } = useV31Theme();
  const [active, setActive] = useState<V31PrimaryView>(initialView);
  const changeView = useCallback((next: V31PrimaryView) => {
    setActive(next);
    window.localStorage.setItem(VIEW_KEY, next);
    window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#${next}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);
  useEffect(() => {
    const onHash = () => {
      const next = window.location.hash.slice(1) as V31PrimaryView;
      if (primaryViews.includes(next)) setActive(next);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const content = <ViewContent active={active} legacy={legacy} />;

  if (theme === "B") {
    return (
      <div className="ma31-root ma31-theme-b" data-layout-adapter="B" data-color-mode={mode}>
        <aside className="ma31-b-rail">
          <Brand theme="B" />
          <PrimaryNavigation active={active} onChange={changeView} theme="B" />
          <div className="ma31-b-rail-footer"><FreshnessChip /><small>Private analytics · proposal only</small></div>
        </aside>
        <div className="ma31-b-stage">
          <header className="ma31-b-utility"><span>MEMORY ATLAS · OWNER RESEARCH EDITION</span><ThemeControls /></header>
          <main className="ma31-main" id="ma31-main">{content}</main>
        </div>
      </div>
    );
  }

  if (theme === "C") {
    return (
      <div className="ma31-root ma31-theme-c" data-layout-adapter="C" data-color-mode={mode}>
        <div className="ma31-c-systembar"><span><i />SYSTEM OBSERVABLE</span><span>PRIVATE_ANALYTICS / PROPOSAL_ONLY</span><FreshnessChip /></div>
        <header className="ma31-c-commandbar">
          <Brand theme="C" />
          <PrimaryNavigation active={active} onChange={changeView} theme="C" />
          <ThemeControls />
        </header>
        <main className="ma31-main" id="ma31-main">{content}</main>
      </div>
    );
  }

  return (
    <div className="ma31-root ma31-theme-a" data-layout-adapter="A" data-color-mode={mode}>
      <header className="ma31-a-topbar">
        <Brand theme="A" />
        <PrimaryNavigation active={active} onChange={changeView} theme="A" />
        <div className="ma31-a-actions"><FreshnessChip /><ThemeControls /></div>
      </header>
      <main className="ma31-main" id="ma31-main">{content}</main>
      <footer className="ma31-a-footer"><Activity aria-hidden="true" size={15} /><span>事实不足显示 UNKNOWN；不会把排队、未运行或无法读回写成成功。</span><ShieldCheck aria-hidden="true" size={15} /></footer>
    </div>
  );
}

export function V31App({ legacy }: { legacy: ReactNode }) {
  return (
    <V31ThemeProvider>
      <PrivateAnalyticsProvider>
        <Shell legacy={legacy} />
      </PrivateAnalyticsProvider>
    </V31ThemeProvider>
  );
}
