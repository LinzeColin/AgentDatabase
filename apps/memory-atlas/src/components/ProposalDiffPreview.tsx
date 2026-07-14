import { GitBranch } from "lucide-react";
import { zhCNCopy as uiCopy, zhCNFieldLabel, zhCNProposalValue } from "../i18n/zh-CN";
import type { UiFieldKey } from "../i18n/types";

export interface ProposalDiffPreviewChange {
  field: UiFieldKey;
  original_value: string;
  proposed_value: string;
  impact_summary: string;
  rollback_metadata: {
    rollback_field: UiFieldKey;
    rollback_value: string;
    rollback_hint: string;
  };
}

interface ProposalDiffPreviewProps {
  changes: ProposalDiffPreviewChange[];
  exportSchemaVersion: "memory_atlas_proposal_export.v1";
}

export function ProposalDiffPreview({ changes, exportSchemaVersion }: ProposalDiffPreviewProps) {
  const visibleChanges = changes.slice(0, 6);
  return (
    <section
      aria-label={uiCopy.proposal.diffPreviewAria}
      className="proposal-diff-preview"
      data-proposal-diff-preview={exportSchemaVersion}
      data-proposal-only="true"
    >
      <div className="panel-title-row">
        <h4>{uiCopy.proposal.diffPreviewTitle}</h4>
        <span>{visibleChanges.length} {uiCopy.proposal.diffChangeUnit}</span>
      </div>

      {visibleChanges.length ? (
        <div className="proposal-diff-grid">
          {visibleChanges.map((change) => (
            <article key={change.field}>
              <div className="proposal-diff-field">
                <strong>{zhCNFieldLabel(change.field)}</strong>
                <span>{zhCNFieldLabel("impact_summary")}</span>
              </div>
              <dl>
                <div><dt>{zhCNFieldLabel("original_value")}</dt><dd>{zhCNProposalValue(change.field, change.original_value)}</dd></div>
                <div><dt>{zhCNFieldLabel("proposed_value")}</dt><dd>{zhCNProposalValue(change.field, change.proposed_value)}</dd></div>
              </dl>
              <p>{change.impact_summary}</p>
              <div className="proposal-rollback-metadata" aria-label={zhCNFieldLabel("rollback_metadata")}>
                <GitBranch size={14} />
                <span>
                  {uiCopy.proposal.rollbackSummaryPrefix}：{zhCNFieldLabel(change.rollback_metadata.rollback_field)}
                  {" -> "}
                  {zhCNProposalValue(change.rollback_metadata.rollback_field, change.rollback_metadata.rollback_value)}
                </span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="proposal-diff-empty">{uiCopy.proposal.diffEmpty}</p>
      )}

      <div className="proposal-diff-safety" aria-label="提案应用安全边界">
        <span>{uiCopy.proposal.safetyConflictCheck}</span>
        <span>{uiCopy.proposal.safetyHumanApply}</span>
        <span>{uiCopy.proposal.safetyNoMutation}</span>
      </div>
    </section>
  );
}
