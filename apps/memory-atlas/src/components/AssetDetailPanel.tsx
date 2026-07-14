import { X } from "lucide-react";
import { zhCNEnumLabel, zhCNMachineValue } from "../i18n/zh-CN";
import type { TierAssetDetail } from "../shared/atlas/contracts";
import { EvidenceRefsDetails, MachineFieldDetails } from "../shared/ui/display";

export type { TierAssetDetail } from "../shared/atlas/contracts";

interface AssetDetailPanelProps {
  asset: TierAssetDetail | null;
  onClose: () => void;
  onOpenTarget: (asset: TierAssetDetail) => void;
}

export function AssetDetailPanel({ asset, onClose, onOpenTarget }: AssetDetailPanelProps) {
  if (!asset) return null;

  return (
    <aside
      aria-label="层级资产明细"
      className="asset-detail-panel"
      data-active-memory-mutation="false"
      data-asset-detail-panel={asset.asset_id}
      data-proposal-only="true"
    >
      <div className="asset-detail-panel-heading">
        <div>
          <span>{zhCNMachineValue("assetTier", asset.asset_tier)} · {zhCNEnumLabel("priority", asset.priority)}</span>
          <h4>{asset.title}</h4>
        </div>
        <button aria-label="关闭层级资产明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{asset.summary}</p>

      <dl className="asset-detail-panel-grid">
        <div><dt>主题</dt><dd>{asset.theme}</dd></div>
        <div><dt>价值评分</dt><dd>{formatAssetScore(asset.value_score)}</dd></div>
        <div><dt>重要性</dt><dd>{zhCNEnumLabel("importance", asset.importance)}</dd></div>
        <div><dt>优先级</dt><dd>{zhCNEnumLabel("priority", asset.priority)}</dd></div>
        <div><dt>置信度</dt><dd>{formatAssetScore(asset.confidence)}</dd></div>
        <div><dt>时效状态</dt><dd>{zhCNMachineValue("staleness", asset.staleness_status)}</dd></div>
        <div><dt>更新时间</dt><dd>{formatDisplayDate(asset.updated_at)}</dd></div>
        <div><dt>最近出现</dt><dd>{asset.last_seen_range || "暂无记录"}</dd></div>
        <div><dt>来源范围</dt><dd>{zhCNMachineValue("source", asset.source_scope)}</dd></div>
        <div><dt>证据数量</dt><dd>{asset.evidence_count.toLocaleString()} 条</dd></div>
      </dl>

      <section className="asset-detail-section" aria-label="建议资产动作">
        <span>建议资产动作</span>
        <p>{zhCNMachineValue("assetAction", asset.recommended_asset_action)}</p>
      </section>

      <section className="asset-detail-section" aria-label="关联动作与主题">
        <span>关联内容</span>
        <p>{asset.linked_action_ids.length.toLocaleString()} 个动作 · {asset.linked_topic_ids.length.toLocaleString()} 个主题</p>
        <MachineFieldDetails title="高级详情：关联标识" className="inline-machine-field-details">
          <small>动作标识：{joinOrEmpty(asset.linked_action_ids)}</small>
          <small>主题标识：{joinOrEmpty(asset.linked_topic_ids)}</small>
        </MachineFieldDetails>
      </section>

      <EvidenceRefsDetails refs={asset.evidence_refs} />

      <div className="asset-detail-safety-strip" aria-label="资产提案安全边界">
        <span>{zhCNMachineValue("proposalHint", asset.proposal_hint)}</span>
        <span>{asset.rollback_hint}</span>
        <span>仅生成提案：{zhCNEnumLabel("boolean", String(asset.proposal_only))}</span>
      </div>

      <button className="asset-detail-open-target" onClick={() => onOpenTarget(asset)} type="button">
        打开关联上下文
      </button>
    </aside>
  );
}

function formatAssetScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function formatDisplayDate(value: string): string {
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? new Date(timestamp).toLocaleString("zh-CN") : "时间未知";
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "无";
}
