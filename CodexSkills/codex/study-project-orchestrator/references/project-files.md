# Study Project File Reference

Load this reference when creating or updating a Study Project folder, syncing Notion notes, writing daily logs, or performing weekly calibration.

## Standard Folder Structure

Root:

```text
LinzeColin/Notion/StudyProjects/<project-slug>/
```

Structure:

```text
StudyProjects/<project-slug>/
├── 00_PROJECT_BRIEF.md
├── 01_STUDY_PLAN.md
├── 02_TOP1_STRATEGY.md
├── 03_WEEKLY_PLANS/
│   └── W01.md
├── 04_DAILY_LOGS/
│   └── YYYY-MM-DD.md
├── 05_REVIEWS/
│   └── W01_REVIEW.md
├── 06_PERSONALIZATION/
│   ├── study_preferences.md
│   ├── behavior_patterns.md
│   └── teaching_adjustments.md
├── 07_NOTION/
│   ├── notion_layout.md
│   ├── note_index.md
│   └── import_seed.csv
├── 08_REMINDERS/
│   ├── reminder_plan.md
│   └── email_schedule.csv
├── 09_FRONTIER/
│   ├── source_log.csv
│   └── frontier_updates.md
├── metrics.csv
├── state.json
└── HANDOFF.md
```

## Required File Purposes

| File | Purpose |
|---|---|
| `00_PROJECT_BRIEF.md` | Goal, period, target outcome, success criteria, assumptions |
| `01_STUDY_PLAN.md` | 3-day launch, 7-day sprint, and optional extension plan |
| `02_TOP1_STRATEGY.md` | Top 1% capability definition, high-leverage concepts, defer list, ability tree |
| `03_WEEKLY_PLANS/Wxx.md` | Current week topics, daily missions, outputs, scoring |
| `04_DAILY_LOGS/YYYY-MM-DD.md` | Daily check-in, recall, teaching, practice, sync, next action |
| `05_REVIEWS/Wxx_REVIEW.md` | Weekly performance, plan fit, friction, next week changes |
| `06_PERSONALIZATION/` | User learning preferences, behavior patterns, teaching adjustments |
| `07_NOTION/` | Light Notion layout, note index, optional seed data |
| `08_REMINDERS/` | Reminder plan and optional email schedule |
| `09_FRONTIER/` | Current-source research and source logs for time-sensitive domains |
| `metrics.csv` | Daily numeric tracking |
| `state.json` | Current machine-readable state |
| `HANDOFF.md` | Fast restore summary for future agents |

## System-Level Files

These files may live outside a project folder:

```text
LinzeColin/Notion/_system/study-project-orchestrator/
├── CONNECTION_STATUS.md
└── PROJECT_INDEX.md
```

Use `_system/study-project-orchestrator/PROJECT_INDEX.md` to route multiple concurrent Study Projects without mixing logs.

Suggested project index row:

```markdown
| Project | Slug | Status | Domain | Notion source | Current week/day | Last sync | Next action |
|---|---|---|---|---|---|---|---|
```

For rolling multi-track programs, add:

```markdown
| Program | Active tracks | Queue rule | Current cycle | Last sync | Next promotion |
|---|---|---|---|---|---|
```

Suggested extra machine-readable files:

```text
10_PROGRAM_STATE/
├── active_tracks.json
├── archive_catalog.csv
└── progression_log.csv
```

## Intake Lock Template

Before creating a new project folder, lock these dimensions:

| Dimension | Default | Options |
|---|---|---|
| Learning goal | Real decision and output leverage | A understand / B apply / C monetize or career leverage / D expert judgment |
| Domain or industry | Infer from user prompt | A tech / B finance / C business / D productivity / E academic / F other |
| Subdomain focus | Recommend 3-5 concrete tracks | A fundamentals / B tools / C cases / D project / E frontier |
| Duration | 7 days (Top1 accelerated default) | A 7 / B 14 / C 30 / D 60 / E 90 |
| Daily time | 45-60 minutes | A 30 / B 45-60 / C 90+ |
| Weekly output | Visible deliverable | A notes / B project / C report or memo |
| Notion role | Clean notebook + light structure | A raw notes / B light structure / C full dashboard |

If the user gives a broad field, propose 3-5 subdomain choices. Example for "AI Agent":

| Track | Focus | Best for |
|---|---|---|
| A Agent fundamentals | architecture, tools, memory, orchestration | foundation |
| B Agent product building | ChatGPT Apps, MCP, workflows, deployment | practical output |
| C Agent business use cases | operations, sales, research, automation | monetization |
| D Agent evaluation/safety | evals, reliability, governance | expert judgment |
| E Frontier papers/tools | latest frameworks and research | frontier tracking |

Ask at most 3 questions in one turn and include a default recommendation.

Before starting the learning plan, ask for explicit confirmation and authorization. Do not begin daily teaching until the user has confirmed:

- Final learning scope.
- Total duration.
- Day 1 start date.
- Authorization to start.

Every daily log and daily response should include current progress as:

```text
第X/Y天
```

For a 7-day sprint, examples are `第1/7天`, `第4/7天`, and `第7/7天`.

Do not create artificial `D000` / `第0天` learning sessions for fixed-duration projects. If the user starts early, move `D01` to the actual start date. If a user finishes the current day and continues, move to the next real lesson early. Each accelerated lesson still requires its own daily log, metrics row, Notion sync, GitHub state update, verification, external review packet/handshake, and next-plan update.

If today has no study log by 18:00 local time, set `missed_study_today: true` in `state.json` and produce a reminder action.

## Universal Zero-Base Cognitive Chain Rule

Every Study Project must include a zero-base ramp distilled from the DLM zero-base patch style. The purpose is to make any knowledge or skill learnable from first principles without staying shallow.

Do not start from advanced labels, paper names, formulas, tool names, or implementation tasks. First build this chain:

```text
observable problem -> minimum unit -> representation -> mechanism -> system flow -> constraints/costs -> failure modes -> use cases -> ROI action -> verification
```

For every project plan, include a daily zero-base gate:

| Element | Meaning | Example prompt |
|---|---|---|
| Observable problem | What real-world problem or decision does this knowledge solve? | What situation makes this concept useful? |
| Minimum unit | What is the smallest object the system manipulates? | In DLM it is token/text unit; in finance it might be order/cashflow/risk unit. |
| Representation | How is the object encoded, measured, classified, or modeled? | Is it a number, vector, state, table, graph, rule, or probability? |
| Mechanism | What process changes the object? | What moves from input to output? |
| System flow | How do components connect end to end? | What are the steps from raw input to useful output? |
| Constraints/costs | What limits quality, speed, money, safety, or reliability? | What gets expensive or fragile as scale increases? |
| Failure modes | How does misunderstanding or misuse break the system? | What false confidence or wrong output should we expect? |
| Use cases | Where does this concept create practical leverage? | Which tasks should use it and which should not? |
| ROI action | What is the smallest high-value action today? | What task, memo, table, diagram, or test proves value? |
| Verification | How do we know the learner understood it? | Can the learner explain, apply, and detect failure cases? |

Daily teaching rule:

1. Ask or infer the zero-base gate first.
2. If the user does not know the answer, teach it directly in plain Chinese.
3. Only after the gate is usable, move to advanced theory, papers, tools, formulas, or projects.
4. End with an output that proves understanding: concept map, mechanism table, decision rule, task pack, mini memo, or verification checklist.
5. Record weak links in personalization and adjust future lessons.

Project plan files should reflect this rule:

- `01_STUDY_PLAN.md`: add a zero-base chain and daily zero-base gates.
- `03_WEEKLY_PLANS/Wxx.md`: add a `Zero-Base Gate` column.
- `04_DAILY_LOGS/YYYY-MM-DD.md`: record zero-base gate answer, correction, and score.
- `06_PERSONALIZATION/teaching_adjustments.md`: record recurring missing links such as minimum unit, mechanism, cost, or failure mode.

## Notion Workspace Rule

The user's Notion structure is:

```text
Linz Dashboard
├── 个人价值增长
├── 制造业
├── Re:0
└── arXiv
```

For every new Study Project:

1. Create its Notion database/page under `Linz Dashboard` as a peer to the existing workspaces.
2. Treat existing workspaces as read-only unless the user explicitly asks to modify them.
3. Before creating or importing the new Study Project workspace/database, back up relevant accessible Notion content to GitHub.
4. Configure the Notion page icon to match the target database's existing icon style before marking Notion creation/sync complete. The dominant palette, corner radius, stroke weight, background style, and shadow style must match sibling pages in the same database. Use existing assets from `LinzeColin/Notion/_assets/notion-icons/` when available; otherwise create a matching SVG/PNG asset and record it in GitHub before applying it.
5. Backup path:

```text
LinzeColin/Notion/NotionBackup/YYYYMMDD/
```

Backup should include a manifest and fetched Markdown snapshots of accessible relevant Notion pages/databases. If a complete workspace export is not available through the connector, state the backup scope and gaps.

## Notion Icon Style Rule

When creating or updating Notion Study Project pages, match the existing Notion icon style and dominant color palette.

1. Fetch the target page/database and inspect sibling page icons before writing when connector access exists.
2. Identify the database-level visual system: dominant color family, background, border, shadow, corner radius, icon density, and accent color rules.
3. For `Codex Study Timeline`, default to the blue/white B-tech page-icon system used by sibling timeline pages. Do not use green, orange, purple, or other competing dominant palettes for individual Study Project rows unless the database itself uses that palette or the user explicitly asks for it.
4. Use existing icon assets from `LinzeColin/Notion/_assets/notion-icons/`.
5. For Study Project timeline pages, prefer `LinzeColin/Notion/_assets/notion-icons/study-timeline-pages/`.
6. For arXiv taxonomy/archive pages, prefer `LinzeColin/Notion/_assets/notion-icons/arxiv-taxonomy/`.
7. If no matching icon exists, create a style-consistent SVG or PNG asset, save it under `_assets/notion-icons/`, then apply that asset or record why it could not be applied.
8. Do not use random emoji, mismatched generic icons, style-breaking covers, or a dominant palette that conflicts with sibling pages in the same database.
9. If Notion icon read/write fails, record the blocker in the project's `07_NOTION/note_index.md`, `state.json`, or a system sync log; do not claim icon sync is complete.

## Divergent Scope Expansion Rule

When the user gives a broad learning field, propose meaningful high-ROI expansions before locking scope.

For each expansion, include:

- Domain or subdomain.
- Why it matters.
- ROI use case.
- Example output.
- Whether it is foundation, application, business, automation, or frontier.

Then recommend one default scope that is broad enough to compound but narrow enough for the chosen 30/60/90-day period.

## Daily Log Template

File: `04_DAILY_LOGS/YYYY-MM-DD.md`

```markdown
# Daily Log - YYYY-MM-DD

Project: <project-slug>
Week: Wxx
Day: Dxx
Timezone: Australia/Sydney

## Check-In

| Field | Value |
|---|---|
| Planned minutes | |
| Actual minutes | |
| Energy 1-5 | |
| Main blocker | |

## Active Recall

| Question | User Answer | Score 1-5 | Follow-up |
|---|---|---:|---|

## Concepts Studied

| Concept | Understanding 1-5 | Usage Clarity 1-5 | ROI Application |
|---|---:|---:|---|

## Core Explanation Notes

### What is it?

### Core theory

### How should I use it?

### How it helps life, decisions, learning, and work

### How it improves ability, productivity, thinking, or efficiency

### ROI-max action

## Practice / Output

| Task | Status | Evidence |
|---|---|---|

## Notion Sync

| Field | Value |
|---|---|
| Synced | yes/no |
| Source link | |
| Sync mode | summary/structured/full-body |
| Key links | |

## Personalization Observations

- 

## Next Action

Return prompt:

```text
Continue <project-slug> WxxDxx.
```

## Upcoming Lessons

| Day | Topic | Why it matters | Status |
|---|---|---|---|
| D+1 | | | planned |
| D+2 | | | planned |
| D+3 | | | planned |
```

## Metrics Schema

File: `metrics.csv`

```csv
date,week,day,planned_minutes,actual_minutes,energy_1_5,recall_score_1_5,concept_score_1_5,output_score_1_5,roi_score_1_5,streak,notion_synced,github_updated,next_action
```

## State Schema

File: `state.json`

```json
{
  "project_slug": "example-project",
  "domain": "Example Domain",
  "timezone": "Australia/Sydney",
  "start_date": "YYYY-MM-DD",
  "duration_days": 30,
  "current_week": 1,
  "current_day": 1,
  "current_focus": "",
  "last_session_date": "",
  "streak": 0,
  "missed_study_today": false,
  "last_reminder_at": "",
  "next_action": "",
  "notion_source": {
    "page_url": "",
    "database_url": "",
    "sync_mode": "summary_structured_links_plus_optional_full_body"
  },
  "reminder_mode": "return_to_codex",
  "status": "active"
}
```

For rolling multi-track programs, extend with:

```json
{
  "program_mode": "rolling_parallel_tracks",
  "active_track_limit": 2,
  "group_sequence_total": 8,
  "archive_cycle_days": 30,
  "active_tracks": [
    {
      "group_id": 1,
      "archive_id": 1,
      "archive_label": "archive-1",
      "mastery_pct": 100,
      "status": "completed"
    },
    {
      "group_id": 2,
      "archive_id": 2,
      "archive_label": "archive-2",
      "mastery_pct": 21,
      "status": "active"
    }
  ],
  "queued_groups": [3,4,5,6,7,8],
  "promotion_rule": "when_any_group_completes_promote_next_group; when_archive_completes_move_same_group_to_next_archive"
}
```

## Weekly Review Template

File: `05_REVIEWS/Wxx_REVIEW.md`

```markdown
# Weekly Review - Wxx

Project: <project-slug>
Date range: <YYYY-MM-DD> to <YYYY-MM-DD>

## Scoreboard

| Metric | Score |
|---|---:|
| Consistency | /5 |
| Total time | /5 |
| Active recall | /5 |
| Concept depth | /5 |
| Practical output | /5 |
| ROI application | /5 |
| Motivation | /5 |
| Plan fit | /5 |

## What Actually Happened

## Strong Signals

## Weak Signals

## Misunderstandings Found

## Best Teaching Patterns For This User

## Friction Points

## Output Completed

## Plan Changes For Next Week

| Change | Reason | Expected ROI |
|---|---|---:|

## Next Week Default Plan
```

## Personalization Template

File: `06_PERSONALIZATION/study_preferences.md`

```markdown
# Study Preferences

## Explanation Preferences

- Preferred difficulty:
- Preferred examples:
- Preferred language mix:
- Needs more:
- Needs less:

## Motivation Patterns

- Works well:
- Does not work:
- Return triggers:

## Learning Style

- Strongest mode:
- Weakest mode:
- Best practice format:

## Current Weak Areas

| Area | Evidence | Intervention |
|---|---|---|

## Teaching Adjustments

| Date | Adjustment | Reason | Result |
|---|---|---|---|
```

## Notion Sync Rules

Default sync:

- Summary.
- Structured learning behavior.
- Key links.

Allowed when useful:

- Full note body.

Exclude:

- Secrets.
- Tokens.
- Cookies.
- Private credentials.
- Unrelated private content.

Do not overwrite original Notion notes unless explicitly requested. Prefer companion pages, index pages, suggested layouts, and visual organization.

## Reminder Template

Reminder goal: bring the user back to Codex.

```text
Return to Codex for <project-slug> WxxDxx.
Today focus: <focus>.
Ask: "Continue <project-slug> WxxDxx and sync my Notion notes."

If missed at 18:00+: "未完成今天学习打卡。请优先返回并同步今日学习：Continue <project-slug> WxxDxx and sync my Notion notes."
```

Keep reminders short. Add D06 and D07 reminders to prepare the next week when using weekly email or calendar cadence.

## Automation Record Template

When an actual automation is created or updated, record it in `08_REMINDERS/reminder_plan.md`, `state.json`, and `HANDOFF.md`.

Required fields:

```markdown
| Automation | ID | Kind | Schedule | Role | Status |
|---|---|---|---|---|---|
```

Rules:

- `study-project-daily-sync` should be a detached cron that reads GitHub/Notion state directly.
- Return-to-Codex reminders should be detached cron jobs by default. Thread heartbeats are allowed only when the user explicitly asks to wake the current conversation.
- If a project has a `next_phase`, reminders must mention the phase decision gate so the project is not treated as complete after the first sprint.
