"""Paths and contract identifiers shared by Memory Atlas CLI modules."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHATGPT_SYNC = ROOT / "scripts" / "sync_chatgpt_memory_data.py"
CHATGPT_DERIVED_BUILDER = ROOT / "scripts" / "build_memory_atlas_chatgpt_derived.py"
CODEX_SYNC = ROOT / "scripts" / "sync_codex_memory_data.py"
CODEX_DERIVED_BUILDER = ROOT / "scripts" / "build_memory_atlas_codex_derived.py"
FUTURE_AGENT_SYNC = ROOT / "scripts" / "sync_future_agent_data.py"
BUILD_ATLAS = ROOT / "scripts" / "build_memory_atlas_data.py"
GITHUB_BACKUP = ROOT / "scripts" / "github_backup.py"
FACET_EXTRACTOR = ROOT / "scripts" / "extract_memory_atlas_facets.py"
CLUSTER_BUILDER = ROOT / "scripts" / "build_memory_atlas_clusters.py"
LOW_VALUE_LOOP_BUILDER = ROOT / "scripts" / "build_memory_atlas_low_value_loops.py"
OPPORTUNITY_BUILDER = ROOT / "scripts" / "build_memory_atlas_opportunities.py"
ECONOMIC_PROXY_BUILDER = ROOT / "scripts" / "build_memory_atlas_economic_proxy.py"
INFORMATION_ROI_BUILDER = ROOT / "scripts" / "build_memory_atlas_information_roi.py"
FORMULA_WHAT_IF_BUILDER = ROOT / "scripts" / "build_memory_atlas_formula_what_if.py"
AGENT_COLLABORATION_BUILDER = ROOT / "scripts" / "build_memory_atlas_agent_collaboration.py"
AGENT_AUTHORIZATION_BUILDER = ROOT / "scripts" / "build_memory_atlas_agent_authorization.py"
STAGE_FLIGHT_BUILDER = ROOT / "scripts" / "build_memory_atlas_stage_flight.py"
LATENT_SIGNAL_BUILDER = ROOT / "scripts" / "build_memory_atlas_latent_signals.py"
SELF_ITERATION_BUILDER = ROOT / "scripts" / "build_memory_atlas_self_iteration.py"
DECISION_DEBT_BUILDER = ROOT / "scripts" / "build_memory_atlas_decision_debt.py"
PERSONALIZATION_BUILDER = ROOT / "scripts" / "build_personalization_exports.py"
CHATGPT_DEEP_EXPLORE_BUILDER = ROOT / "scripts" / "build_chatgpt_deep_explore_prompt.py"
PROPOSAL_STATE_TASK_ID = "MA-V12-S13P1"
PROPOSAL_STATE_ACCEPTANCE_ID = "ACC-MA-V12-S13P1"
PROPOSAL_STATE_CONTRACT_VERSION = "proposal_state_machine.v1_2_s13_p1"
PROPOSAL_STATE_BUILDER_RELATIVE = "scripts/build_memory_atlas_proposal_state_machine.py"
PROPOSAL_STATE_BUILDER = ROOT / PROPOSAL_STATE_BUILDER_RELATIVE
DIFF_NARRATOR_TASK_ID = "MA-V12-S13P2"
DIFF_NARRATOR_ACCEPTANCE_ID = "ACC-MA-V12-S13P2"
DIFF_NARRATOR_CONTRACT_VERSION = "diff_narrator.v1_2_s13_p2"
DIFF_NARRATOR_BUILDER_RELATIVE = "scripts/build_memory_atlas_diff_narrator.py"
DIFF_NARRATOR_BUILDER = ROOT / DIFF_NARRATOR_BUILDER_RELATIVE
PROPOSAL_APPLY_TASK_ID = "MA-V12-S13P3"
PROPOSAL_APPLY_ACCEPTANCE_ID = "ACC-MA-V12-S13P3"
PROPOSAL_APPLY_CONTRACT_VERSION = "proposal_apply.v1_2_s13_p3"
PROPOSAL_APPLY_BUILDER_RELATIVE = "scripts/build_memory_atlas_proposal_apply.py"
PROPOSAL_APPLY_BUILDER = ROOT / PROPOSAL_APPLY_BUILDER_RELATIVE
FINAL_AUDIT_TASK_ID = "MA-V12-S14P2"
FINAL_AUDIT_ACCEPTANCE_ID = "ACC-MA-V12-S14P2"
FINAL_AUDIT_CONTRACT_VERSION = "atlasctl_final_audit.v1_2_s14_p2"
FINAL_AUDIT_PHASE_STATUS = "phase_s14_p2_final_audit_gate_completed_pending_s14_p3"
FINAL_AUDIT_OUTPUT_TAIL_CHARS = 600

__all__ = (
    "ROOT",
    "CHATGPT_SYNC",
    "CHATGPT_DERIVED_BUILDER",
    "CODEX_SYNC",
    "CODEX_DERIVED_BUILDER",
    "FUTURE_AGENT_SYNC",
    "BUILD_ATLAS",
    "GITHUB_BACKUP",
    "FACET_EXTRACTOR",
    "CLUSTER_BUILDER",
    "LOW_VALUE_LOOP_BUILDER",
    "OPPORTUNITY_BUILDER",
    "ECONOMIC_PROXY_BUILDER",
    "INFORMATION_ROI_BUILDER",
    "FORMULA_WHAT_IF_BUILDER",
    "AGENT_COLLABORATION_BUILDER",
    "AGENT_AUTHORIZATION_BUILDER",
    "STAGE_FLIGHT_BUILDER",
    "LATENT_SIGNAL_BUILDER",
    "SELF_ITERATION_BUILDER",
    "DECISION_DEBT_BUILDER",
    "PERSONALIZATION_BUILDER",
    "CHATGPT_DEEP_EXPLORE_BUILDER",
    "PROPOSAL_STATE_TASK_ID",
    "PROPOSAL_STATE_ACCEPTANCE_ID",
    "PROPOSAL_STATE_CONTRACT_VERSION",
    "PROPOSAL_STATE_BUILDER_RELATIVE",
    "PROPOSAL_STATE_BUILDER",
    "DIFF_NARRATOR_TASK_ID",
    "DIFF_NARRATOR_ACCEPTANCE_ID",
    "DIFF_NARRATOR_CONTRACT_VERSION",
    "DIFF_NARRATOR_BUILDER_RELATIVE",
    "DIFF_NARRATOR_BUILDER",
    "PROPOSAL_APPLY_TASK_ID",
    "PROPOSAL_APPLY_ACCEPTANCE_ID",
    "PROPOSAL_APPLY_CONTRACT_VERSION",
    "PROPOSAL_APPLY_BUILDER_RELATIVE",
    "PROPOSAL_APPLY_BUILDER",
    "FINAL_AUDIT_TASK_ID",
    "FINAL_AUDIT_ACCEPTANCE_ID",
    "FINAL_AUDIT_CONTRACT_VERSION",
    "FINAL_AUDIT_PHASE_STATUS",
    "FINAL_AUDIT_OUTPUT_TAIL_CHARS",
)
