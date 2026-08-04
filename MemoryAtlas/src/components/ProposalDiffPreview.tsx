import { GitBranch } from "lucide-react";

export interface ProposalDiffPreviewChange {
  field: "importance" | "priority" | "status" | "theme_override" | "action_state" | "note";
  original_value: string;
  proposed_value: string;
  impact_summary: string;
  rollback_metadata: {
    rollback_field: string;
    rollback_value: string;
    rollback_hint: string;
  };
}

interface ProposalDiffPreviewProps {
  changes: ProposalDiffPreviewChange[];
  exportSchemaVersion: "memory_atlas_proposal_export.v1";
}

/** Proposal field names are UI chrome; the values they carry are the user's. */
export const proposalFieldLabel = (field: string): string =>
  ({
    importance: "重要度", priority: "优先级", status: "状态",
    theme_override: "主题覆盖", action_state: "动作状态", note: "备注",
  } as Record<string, string>)[field] ?? field;

export function ProposalDiffPreview({ changes, exportSchemaVersion }: ProposalDiffPreviewProps) {
  const visibleChanges = changes.slice(0, 6);
  return (
    <section
      aria-label="proposal diff preview"
      className="proposal-diff-preview"
      data-proposal-diff-preview={exportSchemaVersion}
      data-proposal-only="true"
    >
      <div className="panel-title-row">
        <h4>提案差异预览</h4>
        <span>{visibleChanges.length} 处调整</span>
      </div>

      {visibleChanges.length ? (
        <div className="proposal-diff-grid">
          {visibleChanges.map((change) => (
            <article key={change.field}>
              <div className="proposal-diff-field">
                <strong>{proposalFieldLabel(change.field)}</strong>
                <span>影响说明</span>
              </div>
              <dl>
                <div><dt>原值</dt><dd>{change.original_value || "空"}</dd></div>
                <div><dt>建议值</dt><dd>{change.proposed_value || "空"}</dd></div>
              </dl>
              <p>{change.impact_summary}</p>
              <div className="proposal-rollback-metadata" aria-label="回滚信息">
                <GitBranch size={14} />
                <span>
                  回滚到：{proposalFieldLabel(change.rollback_metadata.rollback_field)} -&gt; {change.rollback_metadata.rollback_value || "空"}
                </span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="proposal-diff-empty">当前没有本地调整；选择重要度或优先级后会显示原值、新值和影响说明。</p>
      )}

      <div className="proposal-diff-safety" aria-label="提案应用安全约束">
        <span>必须先做冲突检查</span>
        <span>只能由人工或受控代理应用</span>
        <span>不会直接改动稳定记忆</span>
      </div>
    </section>
  );
}
