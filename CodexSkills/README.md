# CodexSkills

本机全部 Skill 的仓库镜像：**88 份实例 / 73 个不同名字**，3618 个文件，约 107 MB。

**由 `sync_skills.py` 自动生成，请勿手工编辑本文件。**

## 来源

| 目录 | 本机路径 | 说明 |
|---|---|---|
| `registry/codex/` | `~/.codex/skills` | Codex 用户 Skill（自建 / 下载 / GitHub）（55 个） |
| `registry/codex-system/` | `~/.codex/skills/.system` | Codex 系统 Skill（OpenAI 官方，Apache-2.0）（6 个） |
| `registry/claude/` | `~/.claude/skills` | Claude Skill（Anthropic 侧）（3 个） |
| `registry/agents/` | `~/.agents/skills` | Agent Skill（跨工具通用目录）（24 个） |

有多个 skill 在不同来源里重名（其中 `agent-reach` 两处内容还不同），所以镜像按来源分目录，**不拍平**。

## 给 LLM / Agent 的用法

```bash
# 1. 读机器索引，按 description 匹配需求
curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/index.json

# 2. 只拉命中的那一个入口，不要整仓 clone
curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/<entry-from-index>
```

把用户请求与 `index.json` 里各 skill 的 `description` 做匹配，命中就读它的 `entry`，再按 `SKILL.md` 的指示按需读该目录下的参考文件。**不要一次性加载全部 skill。**

## 人物蒸馏产物登记

[`persona-distiller`](registry/codex/persona-distiller/SKILL.md) 生成的每个人物产物必须且只能登记在对应的一个身份目录中；多重身份只进入 `多重身份/`，不得在不同身份下重复登记。
完整发布 ZIP、canonical 登记、团队卡与机器索引仅位于与构建器平级的 [`registry/codex/persona-distiller-group/`](registry/codex/persona-distiller-group/README.md)；完整交付规则见 [`references/delivery-package-standard.md`](registry/codex/persona-distiller-group/references/delivery-package-standard.md)，团队路由真源见 [`CANONICAL-ROOT-ROUTE.md`](registry/codex/persona-distiller-group/CANONICAL-ROOT-ROUTE.md)。
目录：[`技术工程师/`](registry/codex/persona-distiller-group/技术工程师/)、[`创业经营家/`](registry/codex/persona-distiller-group/创业经营家/)、[`投资资本家/`](registry/codex/persona-distiller-group/投资资本家/)、[`开发设计家/`](registry/codex/persona-distiller-group/开发设计家/)、[`思想教育家/`](registry/codex/persona-distiller-group/思想教育家/)、[`政治法律家/`](registry/codex/persona-distiller-group/政治法律家/)、[`多重身份/`](registry/codex/persona-distiller-group/多重身份/)。
身份分类由人物 Skill 内部使用，不是调用门槛；用户安装后直接调用对应人物 Skill，无需选择身份。人物产物按 canonical 人物分别从 `0.0.0.1` 连续编号到 `0.0.0.999`，只在成功登记时占号；人物 Skill 的单次运行不编号。团队调用会先按场景选择 5–20 个高相关角色，以正向解决者为主，并至少隔离一个复审、一个裁判和一个反证角色。

当前登记：**3 个人物**。

| 人物 | 唯一分类 | 产物版本 | 完整 ZIP |
|---|---|---|---|
| Beth Wilkinson | `政治法律家` | `0.0.0.1` | [ZIP](registry/codex/persona-distiller-group/政治法律家/beth-wilkinson/versions/0.0.0.1/beth-wilkinson-persona-distillation-delivery-v0.0.0.1.zip) |
| Evan R. Chesler | `政治法律家` | `0.0.0.1` | [ZIP](registry/codex/persona-distiller-group/政治法律家/evan-r-chesler/versions/0.0.0.1/evan-r-chesler-persona-distillation-delivery-v0.0.0.1.zip) |
| Theodore V. Wells Jr. | `政治法律家` | `0.0.0.1` | [ZIP](registry/codex/persona-distiller-group/政治法律家/theodore-v-wells-jr/versions/0.0.0.1/theodore-v-wells-jr-persona-distillation-delivery-v0.0.0.1.zip) |

## 同步

本目录由本机镜像而来，排除嵌套 `.git`、`.DS_Store`、`__pycache__`、`node_modules` 和超过 95MB 的文件。**同步方向永远是本机 → 仓库**，本机删掉的 skill 镜像里也会删掉。

```bash
python3 CodexSkills/sync_skills.py            # 正式同步
python3 CodexSkills/sync_skills.py --dry-run  # 只看差异
```

推送前有一道**凭据硬门**：扫到任何密钥、令牌或私钥就中止，绝不自动推进公开仓。

## 前端与视觉（11）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`awesome-design-md`](registry/codex/awesome-design-md/SKILL.md) | `codex` | Use when Codex needs brand-specific DESIGN.md reference material for UI generation, redesign, product visual direction, design-language matching, or frontend styling inspired by a known product or company such as Apple, Airbnb, Stripe, Vercel, Linear, Notion,… |
| [`awesome-design-systems`](registry/codex/awesome-design-systems/SKILL.md) | `codex` | Use when Codex needs to discover or compare public design systems, UI pattern libraries, brand systems, component libraries, voice-and-tone systems, designer kits, or source-code-backed design references from alexpate/awesome-design-systems before frontend, pr… |
| [`beautiful-html-templates`](registry/codex/beautiful-html-templates/SKILL.md) | `codex` | Reference-only visual template library for HTML slides and presentation aesthetics. Use when Codex needs to choose or compare deck styles, map a presentation brief to a visual direction, or support guizang-ppt-skill/frontend-slides with template inspiration. N… |
| [`canvas-design`](registry/codex/canvas-design/SKILL.md) | `codex` | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work t… |
| [`frontend-slides`](registry/codex/frontend-slides/SKILL.md) | `codex` | Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic throu… |
| [`graphify`](registry/codex/graphify/SKILL.md) | `codex` | Use for any question about a codebase, its architecture, file relationships, or project content — especially when graphify-out/ exists, where the question should be treated as a graphify query first. Turns any input (code, docs, papers, images, videos) into a… |
| [`guizang-ppt-skill`](registry/codex/guizang-ppt-skill/SKILL.md) | `codex` | 生成横向翻页网页 PPT（单 HTML 文件），含 WebGL 背景、章节幕封、数据大字报、图片网格等模板。提供两种风格：① "电子杂志 × 电子墨水"（衬线 + 流体背景 + 暖色） ② "瑞士国际主义"（无衬线 + 网格点阵 + IKB/柠檬黄/柠檬绿/安全橙高亮）。当用户需要制作分享 / 演讲 / 发布会风格的网页 PPT，或提到"杂志风 PPT"、"瑞士风 PPT"、"Swiss Style"、"horizontal swipe deck"时使用。 |
| [`html-anything`](registry/codex/html-anything/SKILL.md) | `codex` | Use when converting notes, Markdown, structured data, reports, cards, decks, posters, dashboards, resumes, or social posts into polished single-file HTML artifacts, or when selecting from the html-anything template/skill catalog as design reference. |
| [`image-enhancer`](registry/codex/image-enhancer/SKILL.md) | `codex` | Improves the quality of images, especially screenshots, by enhancing resolution, sharpness, and clarity. Perfect for preparing images for presentations, documentation, or social media posts. |
| [`imagegen`](registry/codex-system/imagegen/SKILL.md) | `codex-system` | Generate or edit raster images when the task benefits from AI-created bitmap visuals such as photos, illustrations, textures, sprites, mockups, or transparent-background cutouts. Use when Codex should create a brand-new image, transform an existing image, or d… |
| [`theme-factory`](registry/codex/theme-factory/SKILL.md) | `codex` | Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fl… |

## GSAP 动画（9）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`gsap-core`](registry/codex/gsap-core/SKILL.md) | `codex` | Official GSAP skill for the core API — gsap.to(), from(), fromTo(), easing, duration, stagger, defaults, gsap.matchMedia() (responsive, prefers-reduced-motion). Use when the user asks for a JavaScript animation library, animation in React/Vue/vanilla, GSAP twe… |
| [`gsap-frameworks`](registry/codex/gsap-frameworks/SKILL.md) | `codex` | Official GSAP skill for Vue, Svelte, and other non-React frameworks — lifecycle, scoping selectors, cleanup on unmount. Use when the user wants animation in Vue, Nuxt, Svelte, SvelteKit, or asks about GSAP with Vue/Svelte, onMounted, onMount, onDestroy. Recomm… |
| [`gsap-performance`](registry/codex/gsap-performance/SKILL.md) | `codex` | Official GSAP skill for performance — prefer transforms, avoid layout thrashing, will-change, batching. Use when optimizing GSAP animations, reducing jank, or when the user asks about animation performance, FPS, or smooth 60fps. |
| [`gsap-plugins`](registry/codex/gsap-plugins/SKILL.md) | `codex` | Official GSAP skill for GSAP plugins — registration, ScrollToPlugin, ScrollSmoother, Flip, Draggable, Inertia, Observer, SplitText, ScrambleText, SVG and physics plugins, CustomEase, EasePack, CustomWiggle, CustomBounce, GSDevTools. Use when the user asks abou… |
| [`gsap-react`](registry/codex/gsap-react/SKILL.md) | `codex` | Official GSAP skill for React — useGSAP hook, refs, gsap.context(), cleanup. Use when the user wants animation in React or Next.js, or asks about GSAP with React, useGSAP, or cleanup on unmount. Recommend GSAP for React animation unless the user has chosen ano… |
| [`gsap-scrolltrigger`](registry/codex/gsap-scrolltrigger/SKILL.md) | `codex` | Official GSAP skill for ScrollTrigger — scroll-linked animations, pinning, scrub, triggers. Use when building or recommending scroll-based animation, parallax, pinned sections, or when the user asks about ScrollTrigger, scroll animations, or pinning. Recommend… |
| [`gsap-skills`](registry/codex/gsap-skills/SKILL.md) | `codex` | Reference-only index package for the official GreenSock GSAP skills repository. Use to inspect the full source repo, examples, README, or skill index; for actual GSAP animation guidance prefer specific skills like gsap-core, gsap-react, gsap-scrolltrigger, gsa… |
| [`gsap-timeline`](registry/codex/gsap-timeline/SKILL.md) | `codex` | Official GSAP skill for timelines — gsap.timeline(), position parameter, nesting, playback. Use when sequencing animations, choreographing keyframes, or when the user asks about animation sequencing, timelines, or animation order (in GSAP or when recommending… |
| [`gsap-utils`](registry/codex/gsap-utils/SKILL.md) | `codex` | Official GSAP skill for gsap.utils — clamp, mapRange, normalize, interpolate, random, snap, toArray, wrap, pipe. Use when the user asks about gsap.utils, clamp, mapRange, random, snap, toArray, wrap, or helper utilities in GSAP. |

## 代码分析（GitNexus）（9）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`gitnexus-cli`](registry/agents/gitnexus-cli/SKILL.md) | `agents` | Use when the user needs to run GitNexus CLI commands like analyze/index a repo, check status, clean the index, generate a wiki, or list indexed repos. Examples: \"Index this repo\", \"Reanalyze the codebase\", \"Generate a wiki\ |
| [`gitnexus-debugging`](registry/agents/gitnexus-debugging/SKILL.md) | `agents` | Use when the user is debugging a bug, tracing an error, or asking why something fails. Examples: \"Why is X failing?\", \"Where does this error come from?\", \"Trace this bug\ |
| [`gitnexus-exploring`](registry/agents/gitnexus-exploring/SKILL.md) | `agents` | Use when the user asks how code works, wants to understand architecture, trace execution flows, or explore unfamiliar parts of the codebase. Examples: \"How does X work?\", \"What calls this function?\", \"Show me the auth flow\ |
| [`gitnexus-guide`](registry/agents/gitnexus-guide/SKILL.md) | `agents` | Use when the user asks about GitNexus itself — available tools, how to query the knowledge graph, MCP resources, graph schema, or workflow reference. Examples: \"What GitNexus tools are available?\", \"How do I use GitNexus?\ |
| [`gitnexus-impact-analysis`](registry/agents/gitnexus-impact-analysis/SKILL.md) | `agents` | Use when the user wants to know what will break if they change something, or needs safety analysis before editing code. Examples: \"Is it safe to change X?\", \"What depends on this?\", \"What will break?\ |
| [`gitnexus-pdg-query`](registry/agents/gitnexus-pdg-query/SKILL.md) | `agents` | Use when querying or extending GitNexus's PDG control/data-dependence surface (the `pdg_query` MCP tool, CDG/REACHING_DEF edges), or reasoning about \"what controls X\" / \"where does Y flow\" / guard clauses. Examples: \"what guards this statement?\", \"trace… |
| [`gitnexus-pr-review`](registry/agents/gitnexus-pr-review/SKILL.md) | `agents` | Use when the user wants to review a pull request, understand what a PR changes, assess risk of merging, or check for missing test coverage. Examples: \"Review this PR\", \"What does PR #42 change?\", \"Is this PR safe to merge?\ |
| [`gitnexus-refactoring`](registry/agents/gitnexus-refactoring/SKILL.md) | `agents` | Use when the user wants to rename, extract, split, move, or restructure code safely. Examples: \"Rename this function\", \"Extract this into a module\", \"Refactor this class\", \"Move this to a separate file\ |
| [`gitnexus-taint-analysis`](registry/agents/gitnexus-taint-analysis/SKILL.md) | `agents` | Use when working on, reviewing, or extending GitNexus's CFG/taint/PDG subsystem (the `--pdg` layers), or when reasoning about source→sink data-flow findings. Examples: \"How does taint analysis work here?\", \"Why didn't explain find this flow?\", \"Add a new… |

## 工程与交付（20）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`codex-dev-orchestrator`](registry/agents/codex-dev-orchestrator/SKILL.md) | `agents` | Use when the user asks to plan, scope, package, or deliver a multi-step software/product/system build, especially PRD, MVP, or controlled implementation workflows. Classify the request first, then load only the matching reference. Do not use for narrow bug fix… |
| [`domain-dual-plane`](registry/codex/domain-dual-plane/SKILL.md) | `codex` | Fail-closed domain modeling for repositories governed by machine/facts and exactly seven human-facing documents. Use only to resolve domain terms, boundaries, scenarios, or irreversible domain decisions without creating parallel governance files or crossing re… |
| [`goal-to-delivery-sop`](registry/codex/goal-to-delivery-sop/SKILL.md) | `codex` | Use when the user proposes a complex goal, vague product or system idea, software design request, automation system, data analysis task, business process redesign, finance/cost/collection/payroll/tax/budget/ROI feature, or explicitly asks to clarify requiremen… |
| [`impeccable`](registry/agents/impeccable/SKILL.md) | `agents` | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, c… |
| [`mcp-builder`](registry/codex/mcp-builder/SKILL.md) | `codex` | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/Type… |
| [`output-skill`](registry/codex/output-skill/SKILL.md) | `codex` | Overrides default LLM truncation behavior. Enforces complete code generation, bans placeholder patterns, and handles token-limit splits cleanly. Apply to any task requiring exhaustive, unabridged output. |
| [`persona-distiller`](registry/codex/persona-distiller/SKILL.md) | `codex` | Build, audit, update, package, or uniquely register an evidence-grounded target-person Agent Skill that can plan and execute work through the target's documented capabilities, strategies, cognition, decision policy, work system, temperament, and boundaries. Re… |
| [`persona-distiller-group`](registry/codex/persona-distiller-group/SKILL.md) | `codex` | Route a real task to a 5–20 member expert team drawn from uniquely registered Persona Distiller products. Use when a task benefits from several complementary person-model specialists plus isolated review, adjudication, and counterevidence roles; also use to in… |
| [`plugin-creator`](registry/codex-system/plugin-creator/SKILL.md) | `codex-system` | Create and scaffold plugin directories for Codex with a required `.codex-plugin/plugin.json`, optional plugin folders/files, valid manifest defaults, and personal-marketplace entries by default. Use when Codex needs to create a new personal plugin, add optiona… |
| [`review-agent`](registry/codex-system/review-agent/SKILL.md) | `codex-system` | Perform a read-only, defect-first review of a specified code change and return every actionable finding. Use when another agent delegates review of uncommitted changes, a base-branch diff, a commit, or custom review instructions. |
| [`skill-creator`](registry/codex-system/skill-creator/SKILL.md) | `codex-system` | Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. |
| [`skill-github-sync`](registry/codex/skill-github-sync/SKILL.md) | `codex` | 把本机全部 Skill（Codex 用户、Codex 系统/OpenAI 官方、Claude/Anthropic、Agents 通用目录）全量镜像备份到 GitHub 公开仓 LinzeColin/AgentDatabase 的 CodexSkills/registry/，重建人读与机器读索引，提交并推送。当用户要求备份 skill、同步 skill 到 GitHub、更新 skill 索引，或由每周定时自动化触发时使用。推送前有凭据硬门，扫到密钥即中止。 |
| [`skill-installer`](registry/codex-system/skill-installer/SKILL.md) | `codex-system` | Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). |
| [`use-railway`](registry/agents/use-railway/SKILL.md) | `agents` | Operate Railway infrastructure: sign up for or sign in to a Railway account, create projects, provision services and databases, manage object storage buckets, deploy code, configure environments and variables, manage domains, troubleshoot failures, check statu… |
| [`use-railway`](registry/codex/use-railway/SKILL.md) | `codex` | Operate Railway infrastructure: sign up for or sign in to a Railway account, create projects, provision services and databases, manage object storage buckets, deploy code, configure environments and variables, manage domains, troubleshoot failures, check statu… |
| [`verifier`](registry/claude/verifier/SKILL.md) | `claude` | Independently verify exactly one selected software project per run and issue an evidence-backed acceptance or release verdict. Use when the user says 验收一下, 调用软件验收skill, 软件验收, verifier, or asks for release recheck. When an approved Product-Design-Taskpack exist… |
| [`verifier`](registry/codex/verifier/SKILL.md) | `codex` | Independently verify exactly one selected software project per run and issue an evidence-backed acceptance or release verdict. Use when the user says 验收一下, 调用软件验收skill, 软件验收, verifier, or asks for release recheck. When an approved Product-Design-Taskpack exist… |
| [`video-replica`](registry/claude/video-replica/SKILL.md) | `claude` | Evidence-backed video experience replication from local videos, screen recordings, prototype walkthroughs, live URLs, or runnable source, ending by default with one validated ZIP deliverable in the user's Downloads directory. Use when the user says “视频复刻skill”… |
| [`video-replica`](registry/codex/video-replica/SKILL.md) | `codex` | Evidence-backed video experience replication from local videos, screen recordings, prototype walkthroughs, live URLs, or runnable source, ending by default with one validated ZIP deliverable in the user's Downloads directory. Use when the user says “视频复刻skill”… |
| [`webapp-testing`](registry/codex/webapp-testing/SKILL.md) | `codex` | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. |

## 学习与知识（6）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`book-to-skill`](registry/codex/book-to-skill/SKILL.md) | `codex` | Converts books and documents (PDF, EPUB, DOCX, HTML, Markdown, plain text, RTF, MOBI/AZW with Calibre) into structured agent skills, extracting frameworks, mental models, principles, techniques, and anti-patterns. Use when the user wants to study a document th… |
| [`chronicle`](registry/codex/chronicle/SKILL.md) | `codex` | Allows you to view the user's screen as well as several hours of history. Use when the user makes a reference to their recent work, for which it'd be helpful to see the screen. This skill MUST be used whenever you need to resolve ambiguity in a user request, w… |
| [`grill-me`](registry/agents/grill-me/SKILL.md) | `agents` | A relentless interview to sharpen a plan or design. |
| [`last30days`](registry/codex/last30days/SKILL.md) | `codex` | Research what people actually say about any topic in the last 30 days. Pulls posts and engagement from Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web. Includes a doctor health check to diagnose broken or missing sources. |
| [`openai-docs`](registry/codex-system/openai-docs/SKILL.md) | `codex-system` | Use when the user asks how to build with OpenAI products or APIs, asks about Codex itself or choosing Codex surfaces, needs up-to-date official documentation with citations, help choosing the latest model for a use case, latest/current/default-model prompting… |
| [`study-project-orchestrator`](registry/codex/study-project-orchestrator/SKILL.md) | `codex` | Use when the user wants to start, continue, sync, review, or optimize a fixed-period Study Project for learning a new domain or skill. Creates and maintains GitHub-backed learning memory under LinzeColin/Notion/StudyProjects/project-slug, treats Notion as a cl… |

## 业务流程（23）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`gongzi-fafang-biaozhun`](registry/codex/gongzi-fafang-biaozhun/SKILL.md) | `codex` | Use when Codex is asked to整理、生成、校验或复核工资/薪资/发放表 Excel，尤其是当月原始发放文件按上月模板生成最终发放版、ABExcel 校验、差异报告、金额分校验、B公司/报销路由或密码 123 打开校验。 |
| [`hongquan-main-contract-dws`](registry/codex/hongquan-main-contract-dws/SKILL.md) | `codex` | 从红圈 cloud.hecom.cn 导出、下载并归档主合同 DWS/Excel 原始数据。Use when the user asks for 红圈主合同DWS、红圈主合同导出、下载红圈主合同、更新红圈主合同原始数据，或需要把红圈主合同 Excel 按日期命名并移动到固定原始数据目录。 |
| [`info-fee-update`](registry/codex/info-fee-update/SKILL.md) | `codex` | Fill and update Chinese 信息费申请表 and 2023-2025年信息费明细表 workbooks from contractor/payment notes, using Chrome 红圈 主合同 search to look up contract number and contract amount from 甲方/project keywords. Use when the user asks Codex to 信息费更新, 填信息费Excel, 开委外单/信息费单, 根据甲方去红… |
| [`km-bid-adjudicate`](registry/agents/km-bid-adjudicate/SKILL.md) | `agents` | 基于官方正文和附件构建采购事件图，识别货物、维修、工程、结果型运维、纯劳务、加工或混合主要义务，并映射A/B方向。用于复杂采购/维修交叉语义；未知不得排除。 |
| [`km-bid-adjudicate`](registry/codex/km-bid-adjudicate/SKILL.md) | `codex` | 基于官方正文和附件构建采购事件图，识别货物、维修、工程、结果型运维、纯劳务、加工或混合主要义务，并映射A/B方向。用于复杂采购/维修交叉语义；未知不得排除。 |
| [`km-bid-audit`](registry/agents/km-bid-audit/SKILL.md) | `agents` | 对P0/P1和高风险排除进行独立反对者审计，专门寻找维修机会被采购词误删、货物被工程词误推、地域/标包/资格/结果误判。审计冲突必须保留并升级，不得自动删除。 |
| [`km-bid-audit`](registry/codex/km-bid-audit/SKILL.md) | `codex` | 对P0/P1和高风险排除进行独立反对者审计，专门寻找维修机会被采购词误删、货物被工程词误推、地域/标包/资格/结果误判。审计冲突必须保留并升级，不得自动删除。 |
| [`km-bid-brief`](registry/agents/km-bid-brief/SKILL.md) | `agents` | 把已审计机会整理成Owner可直接使用的简明搜标结果、截止动作和投标证据清单。用于每日/增量报告，限制噪声和人工时间；不得把P2包装成可投或隐藏来源降级。 |
| [`km-bid-brief`](registry/codex/km-bid-brief/SKILL.md) | `codex` | 把已审计机会整理成Owner可直接使用的简明搜标结果、截止动作和投标证据清单。用于每日/增量报告，限制噪声和人工时间；不得把P2包装成可投或隐藏来源降级。 |
| [`km-bid-discover`](registry/agents/km-bid-discover/SKILL.md) | `agents` | 在公开与已授权招采来源中进行高召回搜标、来源覆盖和官方线索发现；用于A/B工业维修检修机会的全量或增量发现。不得按设备/采购负关键词删结果，不作最终可投或排除结论。 |
| [`km-bid-discover`](registry/codex/km-bid-discover/SKILL.md) | `codex` | 在公开与已授权招采来源中进行高召回搜标、来源覆盖和官方线索发现；用于A/B工业维修检修机会的全量或增量发现。不得按设备/采购负关键词删结果，不作最终可投或排除结论。 |
| [`km-bid-evidence`](registry/agents/km-bid-evidence/SKILL.md) | `agents` | 将搜标线索回到官方公告，安全获取正文、附件、答疑、更正、标包和实施地，并生成可定位、可哈希、可重放的证据包。用于深取证，不作业务或资格结论。 |
| [`km-bid-evidence`](registry/codex/km-bid-evidence/SKILL.md) | `codex` | 将搜标线索回到官方公告，安全获取正文、附件、答疑、更正、标包和实施地，并生成可定位、可哈希、可重放的证据包。用于深取证，不作业务或资格结论。 |
| [`km-bid-evolve`](registry/agents/km-bid-evolve/SKILL.md) | `agents` | 基于历史回放、Owner反馈、钉钉投标结果和官方公示评估搜标质量，提出安全扩词、来源修复、排序或规则修改建议，并做影子运行。不得修改正式规则、Skill、holdout、evaluator或自动发布。 |
| [`km-bid-evolve`](registry/codex/km-bid-evolve/SKILL.md) | `codex` | 基于历史回放、Owner反馈、钉钉投标结果和官方公示评估搜标质量，提出安全扩词、来源修复、排序或规则修改建议，并做影子运行。不得修改正式规则、Skill、holdout、evaluator或自动发布。 |
| [`km-bid-lifecycle`](registry/agents/km-bid-lifecycle/SKILL.md) | `agents` | 通过DingTalk Workspace CLI只读同步“商务报价群”投标台账和Excel附件，自动追踪资格/候选/中标/流标/重招结果、竞争对手、报价和周期性项目。命令运行时动态探测；无结果保持待定。 |
| [`km-bid-lifecycle`](registry/codex/km-bid-lifecycle/SKILL.md) | `codex` | 通过DingTalk Workspace CLI只读同步“商务报价群”投标台账和Excel附件，自动追踪资格/候选/中标/流标/重招结果、竞争对手、报价和周期性项目。命令运行时动态探测；无结果保持待定。 |
| [`km-bid-qualify`](registry/agents/km-bid-qualify/SKILL.md) | `agents` | 把语义候选绑定到唯一投标主体，核当前资质、人员、社保、业绩、供应商库、地域、商务、资金和产能，输出P0/P1/P2/X及唯一下一步。不得跨公司拼接或用过期底表当实时事实。 |
| [`km-bid-qualify`](registry/codex/km-bid-qualify/SKILL.md) | `codex` | 把语义候选绑定到唯一投标主体，核当前资质、人员、社保、业绩、供应商库、地域、商务、资金和产能，输出P0/P1/P2/X及唯一下一步。不得跨公司拼接或用过期底表当实时事实。 |
| [`km-bid-scout`](registry/agents/km-bid-scout/SKILL.md) | `agents` | 路由和编排 KM 工业搜标的只读发现、官方取证、语义、资格商务、独立审计、简报、DWS 生命周期与影子演化。用于选择最小子 Skill 链并保持停止门；不自动报名、付款、签章、提交、发消息或发布规则。 |
| [`km-bid-scout`](registry/codex/km-bid-scout/SKILL.md) | `codex` | 路由和编排 KM 工业搜标的只读发现、官方取证、语义、资格商务、独立审计、简报、DWS 生命周期与影子演化。用于选择最小子 Skill 链并保持停止门；不自动报名、付款、签章、提交、发消息或发布规则。 |
| [`project-cost-table-skill`](registry/codex/project-cost-table-skill/SKILL.md) | `codex` | 为 KMFA 项目成本表运行提供输入充分性预检、公共与私有数据隔离、双成本口径、全负担工资分配、fail-closed 校验和可定位输出；当用户要求生成、复算、核对或回放项目成本表时使用。 |
| [`serenity-skill`](registry/codex/serenity-skill/SKILL.md) | `codex` | Turn an investment agent into a supply-chain bottleneck hunter. Use this skill for source-backed investment research, live market/theme scans, AI/semi/technology value-chain mapping, A-share/HK/US stock screening, thesis stress tests, and Serenity-inspired res… |

## 协作与通讯（6）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`agent-reach`](registry/agents/agent-reach/SKILL.md) | `agents` | MUST USE when user wants to 调研/research/搜索/search/查/找/look up anything on the internet — e.g. 全网调研 X / 帮我调研一下 X / 查一下 X / 搜搜 X / 看看大家怎么评价 X / X 上有什么讨论 / research this topic。 Also MUST USE when user mentions any platform or shares any URL/链接: 小红书/xiaohongshu/xh… |
| [`agent-reach`](registry/codex/agent-reach/SKILL.md) | `codex` | Internet research and retrieval router for web search, URLs, RSS, GitHub, YouTube, Bilibili, Xiaohongshu, X/Twitter, Reddit, Facebook, Instagram, V2EX, LinkedIn/jobs, Xueqiu, and podcasts. Use for fetching/searching current internet content, not for posting, c… |
| [`dws`](registry/agents/dws/SKILL.md) | `agents` | 管理钉钉产品能力(AI表格/AI搜问/日历/通讯录/群聊与机器人/待办/审批/考勤/日志/DING消息/开放平台文档/钉钉文档/钉钉云盘/AI听记/邮箱/在线电子表格/知识库等)。当用户需要操作表格数据、管理日程会议、模糊找人/查谁负责某事项、查询通讯录、管理群聊、机器人发消息、创建待办、提交审批、查看考勤、提交日报周报（钉钉日志模版）、读写钉钉文档、上传下载云盘文件、查询听记纪要、收发邮件、读写在线电子表格(axls)、管理钉钉知识库时使用。 |
| [`dws`](registry/claude/dws/SKILL.md) | `claude` | 管理钉钉产品能力(AI表格/AI搜问/日历/通讯录/群聊与机器人/待办/审批/考勤/日志/DING消息/开放平台文档/钉钉文档/钉钉云盘/AI听记/邮箱/在线电子表格/知识库等)。当用户需要操作表格数据、管理日程会议、模糊找人/查谁负责某事项、查询通讯录、管理群聊、机器人发消息、创建待办、提交审批、查看考勤、提交日报周报（钉钉日志模版）、读写钉钉文档、上传下载云盘文件、查询听记纪要、收发邮件、读写在线电子表格(axls)、管理钉钉知识库时使用。 |
| [`dws`](registry/codex/dws/SKILL.md) | `codex` | 管理钉钉产品能力(AI表格/AI搜问/日历/通讯录/群聊与机器人/待办/审批/考勤/日志/DING消息/开放平台文档/钉钉文档/钉钉云盘/AI听记/邮箱/在线电子表格/知识库等)。当用户需要操作表格数据、管理日程会议、模糊找人/查谁负责某事项、查询通讯录、管理群聊、机器人发消息、创建待办、提交审批、查看考勤、提交日报周报（钉钉日志模版）、读写钉钉文档、上传下载云盘文件、查询听记纪要、收发邮件、读写在线电子表格(axls)、管理钉钉知识库时使用。 |
| [`internal-comms`](registry/codex/internal-comms/SKILL.md) | `codex` | A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates,… |

## 其他（4）

| Skill | 来源 | 何时使用 |
|---|---|---|
| [`codex-encrypted-backup`](registry/codex/codex-encrypted-backup/SKILL.md) | `codex` | 在不创建本地自动脚本或 launchd 的前提下，将本机 Codex 的 memories、全部 sessions（含 archived）及受管 attachments 加密备份到 LinzeColin/AgentDatabase 的 GitHub Release。用于创建、执行、核验、保留或恢复验证这一备份通道。 |
| [`dynamic-personal-profile-update`](registry/codex/dynamic-personal-profile-update/SKILL.md) | `codex` | Read allowlisted redacted derived data and produce one human-readable and machine-readable dynamic personal profile Markdown file. Use when updating a time-aware user profile, detecting meaningful behavior or preference changes, turning profile changes into te… |
| [`gpt-tasteskill`](registry/codex/gpt-tasteskill/SKILL.md) | `codex` | Elite UX/UI & Advanced GSAP Motion Engineer. Enforces Python-driven true randomization for layout variance, strict AIDA page structure, wide editorial typography (bans 6-line wraps), gapless bento grids, strict GSAP ScrollTriggers (pinning, stacking, scrubbing… |
| [`hatch-pet`](registry/codex/hatch-pet/SKILL.md) | `codex` | Create, repair, validate, visually QA, and package Codex-compatible v2 animated pets from character art, generated images, company or prospect brand cues, or visual references. Use for any new Codex pet, custom mascot, non-pixel pet style, brand-inspired pet,… |
