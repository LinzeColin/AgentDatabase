import type { ViewKey } from "../types";

export type ProposalActionCopyKey =
  | "update_statement"
  | "add_context"
  | "change_tier"
  | "flag_conflict"
  | "rollback_to_version";

export type UiFieldKey =
  | "importance"
  | "priority"
  | "note"
  | "status"
  | "theme_override"
  | "action_state"
  | "original_value"
  | "proposed_value"
  | "impact_summary"
  | "rollback_metadata"
  | "saved_at";

export type UiEnumGroup =
  | "importance"
  | "priority"
  | "status"
  | "rollbackUnit"
  | "proposalLineage"
  | "runtimeLifecycle"
  | "serverMode"
  | "confidence"
  | "boolean";

export interface UiGlossaryEntry {
  term: string;
  label: string;
  description: string;
}

export interface ChineseUiCopy {
  app: {
    brandTitle: string;
    productName: string;
    fallbackTitle: string;
    navigationAria: string;
    snapshotGeneratedAt: string;
    snapshotLoadedAt: string;
    runtimeStatus: string;
    topbarEyebrow: string;
  };
  navigation: {
    views: Record<ViewKey, string>;
  };
  metrics: {
    memory: string;
    nodes: string;
    edges: string;
    activity: string;
  };
  filters: {
    ariaLabel: string;
    searchPlaceholder: string;
    sourceLabel: string;
    tierLabel: string;
    categoryLabel: string;
    topicLabel: string;
    allOption: string;
  };
  states: {
    notLoaded: string;
    loading: string;
    loadFailedTitle: string;
    loadFailedDescription: string;
    loadFailedAction: string;
    loadingGalaxy: string;
    emptyAtlasTitle: string;
    emptyAtlasDescription: string;
    emptyAtlasAction: string;
    noFilteredResultsTitle: string;
    noFilteredResultsDescription: string;
    noFilteredResultsAction: string;
    webglUnavailableTitle: string;
    webglUnavailableDescription: string;
    webglUnavailableAction: string;
    proposalUnavailableTitle: string;
    proposalUnavailableDescription: string;
    proposalUnavailableAction: string;
  };
  help: {
    eyebrow: string;
    buttonLabel: string;
    panelTitle: string;
    panelSubtitle: string;
    closeLabel: string;
    durationLabel: string;
    threeMinuteTitle: string;
    threeMinutePath: Array<{
      minute: string;
      title: string;
      description: string;
      actionLabel: string;
      view: ViewKey;
    }>;
    modeTitle: string;
    modes: {
      presentation: {
        label: string;
        description: string;
      };
      analysis: {
        label: string;
        description: string;
      };
    };
    workflowTitle: string;
    workflowNotes: Array<{
      title: string;
      description: string;
    }>;
    glossaryTitle: string;
    glossary: UiGlossaryEntry[];
    footerNote: string;
  };
  overview: {
    eyebrow: string;
    title: string;
    defaultFocus: string;
    noTopic: string;
    defaultEntry: string;
    arrivalQuestion: string;
    arrivalTitle: string;
    arrivalDescription: string;
    arrivalSummaryAction: string;
    arrivalMachineDetails: string;
    arrivalLabels: {
      newMaterial: string;
      strengthened: string;
      weakened: string;
      pendingProposal: string;
      syncFailure: string;
    };
    weatherTitle: string;
    previewAria: string;
    miniStarfieldTitle: string;
    miniStarfieldAction: string;
    miniStarfieldAria: string;
    riverPulseTitle: string;
    riverPulseAction: string;
    riverPulseNote: string;
    nextBestActionsTitle: string;
    proposalOnlyLabel: string;
    inspectorTitle: string;
    inspectorHint: string;
    dominantTopics: string;
    memoryTiers: string;
    semanticCategories: string;
  };
  inspector: {
    emptyTitle: string;
    emptyDescription: string;
    meaningTitle: string;
    impactTitle: string;
    futureUseTitle: string;
    relatedTopicsTitle: string;
    debugShow: string;
    debugHide: string;
    debugTitle: string;
    debugDefaultHidden: string;
    lowSensitivitySummary: string;
    explanationTitle: string;
    explanationMeta: string;
  };
  proposal: {
    panelTitle: string;
    versionSuffix: string;
    description: string;
    safetyProposalOnly: string;
    safetyNoDirectMutation: string;
    safetyNeedsApply: string;
    diffLength: string;
    diffSegments: string;
    rollbackUnit: string;
    actionLabel: string;
    draftLabel: string;
    reasonLabel: string;
    reasonPlaceholder: string;
    buttons: {
      save: string;
      exportLatest: string;
      exportHistory: string;
      loadPrevious: string;
      createRollback: string;
      jsonPreview: string;
    };
    actions: Record<ProposalActionCopyKey, string>;
    emptyVersion: string;
    latestVersionPrefix: string;
    editorAria: string;
    editorTitle: string;
    editorScope: string;
    notePlaceholder: string;
    savedAtPrefix: string;
    localOnlyNote: string;
    saveDraft: string;
    exportJson: string;
    resetDraft: string;
    diffPreviewAria: string;
    diffPreviewTitle: string;
    diffChangeUnit: string;
    diffEmpty: string;
    rollbackSummaryPrefix: string;
    safetyConflictCheck: string;
    safetyHumanApply: string;
    safetyNoMutation: string;
  };
  fields: Record<UiFieldKey, string>;
  enums: {
    unknownValue: string;
    emptyValue: string;
    importance: Record<string, string>;
    priority: Record<string, string>;
    status: Record<string, string>;
    rollbackUnit: Record<string, string>;
    proposalLineage: Record<string, string>;
    runtimeLifecycle: Record<string, string>;
    serverMode: Record<string, string>;
    confidence: Record<string, string>;
    boolean: Record<string, string>;
  };
}
