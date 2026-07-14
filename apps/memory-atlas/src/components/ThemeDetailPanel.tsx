import { X } from "lucide-react";
import { zhCNEnumLabel, zhCNMachineValue } from "../i18n/zh-CN";
import type { TopicClassificationDetail } from "../shared/atlas/contracts";
import { humanCategoryLabel } from "../shared/atlas/semanticHuman";
import { EvidenceRefsDetails, MachineFieldDetails } from "../shared/ui/display";

export type { TopicClassificationDetail } from "../shared/atlas/contracts";

interface ThemeDetailPanelProps {
  topic: TopicClassificationDetail | null;
  onClose: () => void;
  onOpenTarget: (topic: TopicClassificationDetail) => void;
}

export function ThemeDetailPanel({ topic, onClose, onOpenTarget }: ThemeDetailPanelProps) {
  if (!topic) return null;

  return (
    <aside
      aria-label="主题分类明细"
      className="theme-detail-panel"
      data-active-memory-mutation="false"
      data-proposal-only="true"
      data-theme-detail-panel={topic.topic_id}
    >
      <div className="theme-detail-panel-heading">
        <div>
          <span>{zhCNMachineValue("topicState", topic.topic_state)} · {topic.parent_topic || "未设置上级主题"}</span>
          <h4>{topic.topic_label}</h4>
        </div>
        <button aria-label="关闭主题分类明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{topic.matched_reason}</p>

      <dl className="theme-detail-panel-grid">
        <div><dt>分类</dt><dd>{humanCategoryLabel(topic.category)}</dd></div>
        <div><dt>主题强度</dt><dd>{formatTopicScore(topic.topic_strength)}</dd></div>
        <div><dt>趋势</dt><dd>{zhCNMachineValue("trend", topic.trend)}</dd></div>
        <div><dt>投入回报</dt><dd>{formatTopicScore(topic.roi_score)}</dd></div>
        <div><dt>冲突程度</dt><dd>{formatTopicScore(topic.conflict_score)}</dd></div>
        <div><dt>置信度</dt><dd>{formatTopicScore(topic.confidence)}</dd></div>
        <div><dt>记录数量</dt><dd>{topic.record_count.toLocaleString()} 条</dd></div>
        <div><dt>近期记录</dt><dd>{topic.recent_count.toLocaleString()} 条</dd></div>
      </dl>

      <section className="theme-detail-section" aria-label="关联资产与行动">
        <span>关联内容</span>
        <p>{topic.linked_asset_ids.length.toLocaleString()} 个资产 · {topic.linked_action_ids.length.toLocaleString()} 个动作</p>
      </section>

      <section className="theme-detail-section" aria-label="跨板块交接">
        <span>跨视图交接</span>
        <p>可在星图聚焦该主题，也可在时间河查看近期记录。</p>
      </section>

      <section className="theme-detail-section" aria-label="代表记录">
        <span>代表记录</span>
        <p>{topic.representative_record_ids.length.toLocaleString()} 条</p>
        <MachineFieldDetails title="高级详情：关联与交接标识" className="inline-machine-field-details">
          <small>资产标识：{joinOrEmpty(topic.linked_asset_ids)}</small>
          <small>动作标识：{joinOrEmpty(topic.linked_action_ids)}</small>
          <small>代表记录标识：{joinOrEmpty(topic.representative_record_ids)}</small>
          <small>星图交接：{topic.starfield_handoff}</small>
          <small>时间河交接：{topic.river_handoff}</small>
        </MachineFieldDetails>
      </section>

      <EvidenceRefsDetails refs={topic.evidence_refs} />

      <div className="theme-detail-safety-strip" aria-label="主题提案安全边界">
        <span>{zhCNMachineValue("proposalHint", topic.proposal_hint)}</span>
        <span>{topic.rollback_hint}</span>
        <span>仅生成提案：{zhCNEnumLabel("boolean", String(topic.proposal_only))}</span>
      </div>

      <button className="theme-detail-open-target" onClick={() => onOpenTarget(topic)} type="button">
        打开主题上下文
      </button>
    </aside>
  );
}

function formatTopicScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "无";
}
