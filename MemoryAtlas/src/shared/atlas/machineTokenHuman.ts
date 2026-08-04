/**
 * One place that turns machine tokens into Chinese for the reader.
 *
 * The ten original views leaked identifiers straight into visible text —
 * `belongs_to_theme:edge:memory:mem_0021f45ff99acd80:theme:...`,
 * `codex_usage_record`, `black_hole`, plus untranslated labels like
 * `Flow Field` and `rising`. UI_UX_VISUAL_CONTRACT requires the page to be
 * Chinese while protocol fields, code identifiers and third-party names keep
 * their native form, so this translates vocabulary and collapses identifiers
 * rather than trying to translate everything.
 */

/** Product and third-party names the contract keeps in their native form. */
export const nativeNames = [
  "Memory Atlas", "Codex", "ChatGPT", "OpenAI", "Notion", "Obsidian", "GitHub",
  "Cloudflare", "ROI", "Three.js", "GSAP", "API", "JSON", "URL", "ID", "Agent",
] as const;

/** Machine vocabulary that appears as a whole word in user-facing text. */
export const machineTokenLabels: Record<string, string> = {
  // node and memory taxonomy
  answering_rule: "回答规则",
  project_context: "项目上下文",
  security_boundary: "安全边界",
  temporary_or_sensitive: "短期或敏感背景",
  recommended_action: "建议动作",
  roi_opportunity: "价值机会",
  core_profile: "核心画像",
  codex_usage_record: "Codex 使用记录",
  memory: "记忆",
  theme: "主题",
  category: "分类",
  project: "项目",
  decision: "决策",
  knowledge: "知识",
  workflow: "工作流",
  preference: "偏好",
  // lifecycle and trend states
  black_hole: "风险循环",
  proto_star: "上升机会",
  rising: "上升",
  declining: "衰退",
  dominant: "主导",
  stable: "稳定",
  stale: "已陈旧",
  current: "当前",
  keep: "保留",
  consolidate: "合并",
  validate: "待验证",
  opportunity: "机会",
  lower_priority: "降低优先级",
  importance: "重要度",
  priority: "优先级",
  note: "备注",
  high: "高",
  mid: "中",
  low: "低",
  down: "下降",
  // visual and panel labels
  "Flow Field": "流场",
  Legacy: "旧版",
  Auto: "自动",
  Present: "当前",
  Analysis: "分析",
  Macro: "宏观",
  "Proposal UI": "提案界面",
  "Proposal Diff Preview": "提案差异预览",
  original_value: "原值",
  proposed_value: "建议值",
  // Added after a browser scan found them rendered raw across eleven views.
  temporary: "临时",
  conflict: "冲突",
  design: "设计",
  mixed: "混合",
  verified: "已验证",
  unverified: "未验证",
  accepted_verified: "已采纳并验证",
  adopted_verified: "已采用并验证",
  decision_execution: "决策与执行",
  decision_impact_verified: "决策影响已验证",
  codex_agent_metadata: "Codex 代理元数据",
  codex_development_record: "Codex 开发记录",
  codex_personalization: "Codex 个性化",
  "proto-star": "上升机会",
  "black-hole": "风险循环",
  latest: "最新",
  delta: "增量",
  Verifier: "验收者",
  TTT: "闭环时长",
  DIRECTION_ONLY: "仅方向可比",
  INSUFFICIENT_DATA: "证据不足",
  DIRECTLY_COMPARABLE: "可直接比较",
  NOT_COMPARABLE: "不可比较",
  // Trend arrows and asset actions rendered raw on the home cards.
  up: "上升",
  flat: "持平",
  archive: "归档",
  promote: "提升",
  // Added after a second browser scan: the reality panel rendered metric
  // denominators and activity keys straight from the snapshot.
  event_count: "事件数",
  known_work_time_minutes: "已知工时（分钟）",
  events_with_known_work_time: "有工时记录的事件",
  events_with_outcome_evidence: "有结果证据的事件",
  unverified_events: "未验证事件",
  verified_events: "已验证事件",
  development_deployment: "开发与部署",
  product_planning: "产品与规划",
  research_diagnosis: "研究与诊断",
  verification_repair: "验证与修复",
  management_learning: "管理与学习",
  unknown: "未分类",
  codex_sessions: "Codex 会话",
  codex_archived_sessions: "Codex 归档会话",
  codex_memories: "Codex 记忆",
  codex_state: "Codex 状态库",
  memory_update_candidate: "记忆更新候选",
  openaidatabase_live_data: "OpenAIDatabase 实时数据",
  deployed: "已部署",
  recovery: "已恢复",
  query_input: "查询输入",
  tier: "层级",
  topic: "主题",
  recency: "新近度",
  all: "全部",
  // Outcome states rendered raw in the heatmap.
  deployed_verified: "已部署并验证",
  draft_only: "仅草稿",
  recovery_verified: "已恢复并验证",
  failed: "失败",
  succeeded: "成功",
  blocked: "受阻",
  in_progress: "进行中",
  decision_verified: "决策已验证",
  abandoned: "已放弃",
  superseded: "已被取代",
  pending: "待处理",
};

/**
 * Collapse a graph edge or node identifier to something a person can read.
 *
 * `belongs_to_theme:edge:memory:mem_0021f45ff99acd80:theme:formal-engineering`
 * becomes `归属主题 · formal-engineering`, keeping the part that carries meaning
 * and dropping the opaque hash the reader cannot act on.
 */
export function humanizeIdentifier(value: string): string {
  const relation = value.match(/^([a-z_]+):edge:/);
  if (relation) {
    const label = machineTokenLabels[relation[1]] ?? relationLabels[relation[1]] ?? relation[1];
    const tail = value.split(":").filter((part) => part && !/^(edge|memory|mem_[0-9a-f]+)$/.test(part)).pop();
    return tail && tail !== relation[1] ? `${label} · ${tail}` : label;
  }
  if (/^mem_[0-9a-f]{8,}$/.test(value)) return "记忆条目";
  return value;
}

const relationLabels: Record<string, string> = {
  belongs_to_theme: "归属主题",
  has_category: "所属分类",
  relates_to: "相关联",
  derived_from: "派生自",
  supports: "支撑",
};

const tokenPattern = new RegExp(
  `(^|[^A-Za-z0-9_])(${Object.keys(machineTokenLabels)
    .sort((a, b) => b.length - a.length)
    .map((key) => key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|")})(?![A-Za-z0-9_])`,
  "g",
);

/** Translate machine vocabulary and collapse identifiers inside free text. */
export function humanizeMachineText(value: string): string {
  if (!value) return value;
  const collapsed = value.replace(/[a-z_]+:edge:[^\s,、]+|mem_[0-9a-f]{8,}/g, (match) =>
    humanizeIdentifier(match),
  );
  return collapsed.replace(tokenPattern, (_whole, lead: string, token: string) =>
    `${lead}${machineTokenLabels[token] ?? token}`,
  );
}
