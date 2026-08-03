export type MemoryAtlasTheme = "A" | "B" | "C";
export type MemoryAtlasColorMode = "light" | "dark";
export type MemoryAtlasV31View = "failureCompound" | "behaviorEconomy" | "runtime";

export interface SourceCoverageV31 {
  source_id: string;
  label_zh: string;
  required: boolean;
  state: "READY" | "MISSING_OPTIONAL" | "MISSING_REQUIRED" | "UNREADABLE" | "EMPTY" | string;
  object_count: number;
  size_bytes: number;
  message_zh: string;
}

export interface FailureCompoundSnapshotV31 {
  schema_version: "memory_atlas.failure_compound.v1" | string;
  generated_at: string;
  compound_score: number | null;
  formula?: string;
  metrics: {
    incident_count?: number;
    active_regression_assets?: number;
    passing_regression_assets?: number;
    historical_recurrences?: number;
    blocked_recurrences?: number;
    asset_coverage?: number;
    last_pass_rate?: number;
    nonrecurrence_ratio?: number;
  };
  incidents: Array<Record<string, unknown>>;
  regression_assets: Array<Record<string, unknown>>;
  fault_injections: Array<Record<string, unknown>>;
}

export interface BehaviorEconomicsSnapshotV31 {
  schema_version: "memory_atlas.behavior_economics.v1" | string;
  generated_at: string;
  event_count: number;
  activity_distribution: Record<string, { count: number; share: number | null }>;
  augmentation_distribution: Record<string, { count: number; share: number | null }>;
  outcome_distribution: Record<string, number>;
  verified_outcome_rate: {
    value: number | null;
    numerator: number;
    denominator: number;
    denominator_type: "effort_minutes" | "event_count" | string;
    state: "MEASURED" | "UNKNOWN" | string;
  };
  projects: Array<Record<string, unknown>>;
  recommendations?: Array<{
    recommendation_id: string;
    fact: string;
    alternative_explanation: string;
    action: string;
    success_metric: string;
    observation_window_days: number;
    rollback: string;
    confidence: string;
  }>;
}

export interface PrivateAnalyticsSnapshotV31 {
  schema_version: "memory_atlas.private_analytics.v1" | string;
  generated_at: string;
  source_contract: {
    mode: "private_full_fidelity_read_only_analytics" | string;
    writeback: "proposal_only" | string;
    direct_stable_memory_mutation: false;
  };
  run: {
    run_id?: string;
    state: string;
    started_at?: string;
    source_completed_at?: string;
    source_coverages?: SourceCoverageV31[];
    objects?: Array<Record<string, unknown>>;
  };
  behavior_economics: BehaviorEconomicsSnapshotV31;
  failure_compound: FailureCompoundSnapshotV31;
}

export interface ActionResponseV31 {
  request_id: string;
  action: string;
  requested_at: string;
  state: string;
  source_required: boolean;
  message_zh: string;
}
