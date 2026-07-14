import { X } from "lucide-react";
import { zhCNEnumLabel, zhCNMachineValue } from "../i18n/zh-CN";
import type { HomeActionDetail } from "../shared/atlas/contracts";
import { EvidenceRefsDetails, MachineFieldDetails } from "../shared/ui/display";

export type { HomeActionDetail } from "../shared/atlas/contracts";

interface ActionDetailDrawerProps {
  action: HomeActionDetail | null;
  onClose: () => void;
  onOpenTarget: (action: HomeActionDetail) => void;
}

export function ActionDetailDrawer({ action, onClose, onOpenTarget }: ActionDetailDrawerProps) {
  if (!action) return null;

  return (
    <aside
      aria-label="建议动作明细"
      className="action-detail-drawer"
      data-action-detail-drawer={action.action_id}
      data-active-memory-mutation="false"
      data-proposal-only="true"
    >
      <div className="action-detail-drawer-heading">
        <div>
          <span>{zhCNEnumLabel("priority", action.priority.toLowerCase())} · {zhCNMachineValue("actionType", action.action_type)}</span>
          <h4>{action.title}</h4>
        </div>
        <button aria-label="关闭建议动作明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{action.reason}</p>

      <dl className="action-detail-drawer-grid">
        <div><dt>投入回报</dt><dd>{formatActionScore(action.roi_score)}</dd></div>
        <div><dt>投入成本</dt><dd>{zhCNMachineValue("effort", action.effort_cost)}</dd></div>
        <div><dt>紧迫程度</dt><dd>{zhCNMachineValue("urgency", action.urgency)}</dd></div>
        <div><dt>置信度</dt><dd>{formatActionScore(action.confidence)}</dd></div>
        <div><dt>判断来源</dt><dd>{zhCNMachineValue("source", action.source)}</dd></div>
        <div><dt>当前状态</dt><dd>{zhCNEnumLabel("status", action.status)}</dd></div>
        <div><dt>证据数量</dt><dd>{action.evidence_count.toLocaleString()} 条</dd></div>
        <div><dt>建议时间</dt><dd>{zhCNMachineValue("timeWindow", action.recommended_time_window)}</dd></div>
      </dl>

      <section className="action-detail-section" aria-label="为什么命中">
        <span>为什么命中</span>
        <p>{action.matched_reason}</p>
      </section>

      <section className="action-detail-section" aria-label="下一步">
        <span>建议下一步</span>
        <p>{action.next_step}</p>
      </section>

      <section className="action-detail-section" aria-label="关联主题与资产">
        <span>关联内容</span>
        <p>{action.linked_topic_ids.length.toLocaleString()} 个主题 · {action.linked_asset_ids.length.toLocaleString()} 个资产</p>
        <MachineFieldDetails title="高级详情：关联标识" className="inline-machine-field-details">
          <small>主题标识：{joinOrEmpty(action.linked_topic_ids)}</small>
          <small>资产标识：{joinOrEmpty(action.linked_asset_ids)}</small>
        </MachineFieldDetails>
      </section>

      <EvidenceRefsDetails refs={action.evidence_refs} />

      <div className="action-detail-safety-strip" aria-label="仅生成提案的安全边界">
        <span>{zhCNMachineValue("proposalHint", action.proposal_hint)}</span>
        <span>{action.rollback_hint}</span>
        <span>仅生成提案：{zhCNEnumLabel("boolean", String(action.proposal_only))}</span>
      </div>

      <button className="action-detail-open-target" onClick={() => onOpenTarget(action)} type="button">
        打开关联视图
      </button>
    </aside>
  );
}

function formatActionScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "无";
}
