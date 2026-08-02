import { Activity, BarChart3, CircleDot, GitBranch, RotateCcw } from "lucide-react";
import type { V31PrimaryView, V31Theme } from "./contracts";

const labels: Record<V31Theme, Record<V31PrimaryView, string>> = {
  A: { today: "今日总览", universe: "记忆宇宙", compound: "失败复利", economy: "行为经济", runtime: "系统运行" },
  B: { today: "今日简报", universe: "研究档案", compound: "复利账本", economy: "经济指数", runtime: "运行底稿" },
  C: { today: "战情", universe: "图谱", compound: "回归", economy: "洞察", runtime: "运维" },
};

const icons = {
  today: CircleDot,
  universe: GitBranch,
  compound: RotateCcw,
  economy: BarChart3,
  runtime: Activity,
} satisfies Record<V31PrimaryView, typeof CircleDot>;

const order: V31PrimaryView[] = ["today", "universe", "compound", "economy", "runtime"];

export function PrimaryNavigation({
  theme,
  active,
  onChange,
}: {
  theme: V31Theme;
  active: V31PrimaryView;
  onChange: (view: V31PrimaryView) => void;
}) {
  return (
    <nav className="ma31-primary-nav" aria-label="Memory Atlas 一级导航" data-primary-count="5">
      {order.map((view) => {
        const Icon = icons[view];
        return (
          <button
            aria-current={active === view ? "page" : undefined}
            className={active === view ? "ma31-primary-item active" : "ma31-primary-item"}
            data-primary-view={view}
            key={view}
            onClick={() => onChange(view)}
            type="button"
          >
            <Icon aria-hidden="true" size={18} />
            <span>{labels[theme][view]}</span>
          </button>
        );
      })}
    </nav>
  );
}
