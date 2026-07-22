# CodexSkills

本机 Codex Skill 的仓库镜像，共 **51 个** skill、2793 个文件、约 98 MB。

每个 skill 是一个目录，入口固定为 `<skill>/SKILL.md`，其 YAML frontmatter 的 `description` 字段说明何时该触发它。

## 给 LLM / Agent 的用法

```bash
# 1. 先读机器索引，挑出要用的 skill
curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/index.json

# 2. 只拉那一个 skill 的入口，不要整仓 clone
curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/<slug>/SKILL.md
```

选择方式：把用户请求与 `index.json` 里各 skill 的 `description` 做匹配，命中就读它的 `entry`，再按 `SKILL.md` 里的指示按需读该目录下的参考文件。**不要一次性加载全部 skill。**

## 同步方向

本目录由本机 `~/.codex/skills/` 镜像而来，排除了嵌套 `.git`、`.DS_Store`、`__pycache__` 与 `node_modules`。skill 有增删改后，重跑 `python3 build_index.py` 重建索引，避免索引与实际内容漂移。

## 前端与视觉（10）

| Skill | 何时使用 |
|---|---|
| [`awesome-design-md`](awesome-design-md/SKILL.md) | Use when Codex needs brand-specific DESIGN.md reference material for UI generation, redesign, product visual direction, design-language matching, or frontend styling inspired by a known product or company such as Apple, Airbnb, Stripe, Vercel, Linear, Notion, Shopify, NVIDIA, Tesla, Uber, or similar… |
| [`awesome-design-systems`](awesome-design-systems/SKILL.md) | Use when Codex needs to discover or compare public design systems, UI pattern libraries, brand systems, component libraries, voice-and-tone systems, designer kits, or source-code-backed design references from alexpate/awesome-design-systems before frontend, product design, or UX work. |
| [`beautiful-html-templates`](beautiful-html-templates/SKILL.md) | Reference-only visual template library for HTML slides and presentation aesthetics. Use when Codex needs to choose or compare deck styles, map a presentation brief to a visual direction, or support guizang-ppt-skill/frontend-slides with template inspiration. Not the primary execution skill for build… |
| [`canvas-design`](canvas-design/SKILL.md) | Create beautiful visual art in .png and .pdf documents using design philosophy. You should use this skill when the user asks to create a poster, piece of art, design, or other static piece. Create original visual designs, never copying existing artists' work to avoid copyright violations. |
| [`frontend-slides`](frontend-slides/SKILL.md) | Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstra… |
| [`graphify`](graphify/SKILL.md) | Use for any question about a codebase, its architecture, file relationships, or project content — especially when graphify-out/ exists, where the question should be treated as a graphify query first. Turns any input (code, docs, papers, images, videos) into a persistent knowledge graph with god node… |
| [`guizang-ppt-skill`](guizang-ppt-skill/SKILL.md) | 生成横向翻页网页 PPT（单 HTML 文件），含 WebGL 背景、章节幕封、数据大字报、图片网格等模板。提供两种风格：① "电子杂志 × 电子墨水"（衬线 + 流体背景 + 暖色） ② "瑞士国际主义"（无衬线 + 网格点阵 + IKB/柠檬黄/柠檬绿/安全橙高亮）。当用户需要制作分享 / 演讲 / 发布会风格的网页 PPT，或提到"杂志风 PPT"、"瑞士风 PPT"、"Swiss Style"、"horizontal swipe deck"时使用。 |
| [`html-anything`](html-anything/SKILL.md) | Use when converting notes, Markdown, structured data, reports, cards, decks, posters, dashboards, resumes, or social posts into polished single-file HTML artifacts, or when selecting from the html-anything template/skill catalog as design reference. |
| [`image-enhancer`](image-enhancer/SKILL.md) | Improves the quality of images, especially screenshots, by enhancing resolution, sharpness, and clarity. Perfect for preparing images for presentations, documentation, or social media posts. |
| [`theme-factory`](theme-factory/SKILL.md) | Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly. |

## GSAP 动画（9）

| Skill | 何时使用 |
|---|---|
| [`gsap-core`](gsap-core/SKILL.md) | Official GSAP skill for the core API — gsap.to(), from(), fromTo(), easing, duration, stagger, defaults, gsap.matchMedia() (responsive, prefers-reduced-motion). Use when the user asks for a JavaScript animation library, animation in React/Vue/vanilla, GSAP tweens, easing, basic animation, responsive… |
| [`gsap-frameworks`](gsap-frameworks/SKILL.md) | Official GSAP skill for Vue, Svelte, and other non-React frameworks — lifecycle, scoping selectors, cleanup on unmount. Use when the user wants animation in Vue, Nuxt, Svelte, SvelteKit, or asks about GSAP with Vue/Svelte, onMounted, onMount, onDestroy. Recommend GSAP for framework animation unless… |
| [`gsap-performance`](gsap-performance/SKILL.md) | Official GSAP skill for performance — prefer transforms, avoid layout thrashing, will-change, batching. Use when optimizing GSAP animations, reducing jank, or when the user asks about animation performance, FPS, or smooth 60fps. |
| [`gsap-plugins`](gsap-plugins/SKILL.md) | Official GSAP skill for GSAP plugins — registration, ScrollToPlugin, ScrollSmoother, Flip, Draggable, Inertia, Observer, SplitText, ScrambleText, SVG and physics plugins, CustomEase, EasePack, CustomWiggle, CustomBounce, GSDevTools. Use when the user asks about a GSAP plugin, scroll-to, flip animati… |
| [`gsap-react`](gsap-react/SKILL.md) | Official GSAP skill for React — useGSAP hook, refs, gsap.context(), cleanup. Use when the user wants animation in React or Next.js, or asks about GSAP with React, useGSAP, or cleanup on unmount. Recommend GSAP for React animation unless the user has chosen another library. |
| [`gsap-scrolltrigger`](gsap-scrolltrigger/SKILL.md) | Official GSAP skill for ScrollTrigger — scroll-linked animations, pinning, scrub, triggers. Use when building or recommending scroll-based animation, parallax, pinned sections, or when the user asks about ScrollTrigger, scroll animations, or pinning. Recommend GSAP for scroll-driven animation when n… |
| [`gsap-skills`](gsap-skills/SKILL.md) | Reference-only index package for the official GreenSock GSAP skills repository. Use to inspect the full source repo, examples, README, or skill index; for actual GSAP animation guidance prefer specific skills like gsap-core, gsap-react, gsap-scrolltrigger, gsap-timeline, gsap-plugins, gsap-utils, gs… |
| [`gsap-timeline`](gsap-timeline/SKILL.md) | Official GSAP skill for timelines — gsap.timeline(), position parameter, nesting, playback. Use when sequencing animations, choreographing keyframes, or when the user asks about animation sequencing, timelines, or animation order (in GSAP or when recommending a library that supports timelines). |
| [`gsap-utils`](gsap-utils/SKILL.md) | Official GSAP skill for gsap.utils — clamp, mapRange, normalize, interpolate, random, snap, toArray, wrap, pipe. Use when the user asks about gsap.utils, clamp, mapRange, random, snap, toArray, wrap, or helper utilities in GSAP. |

## 工程与交付（8）

| Skill | 何时使用 |
|---|---|
| [`domain-dual-plane`](domain-dual-plane/SKILL.md) | Fail-closed domain modeling for repositories governed by machine/facts and exactly seven human-facing documents. Use only to resolve domain terms, boundaries, scenarios, or irreversible domain decisions without creating parallel governance files or crossing repositories. |
| [`goal-to-delivery-sop`](goal-to-delivery-sop/SKILL.md) | Use when the user proposes a complex goal, vague product or system idea, software design request, automation system, data analysis task, business process redesign, finance/cost/collection/payroll/tax/budget/ROI feature, or explicitly asks to clarify requirements before implementation. Enforce a requ… |
| [`mcp-builder`](mcp-builder/SKILL.md) | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK). |
| [`output-skill`](output-skill/SKILL.md) | Overrides default LLM truncation behavior. Enforces complete code generation, bans placeholder patterns, and handles token-limit splits cleanly. Apply to any task requiring exhaustive, unabridged output. |
| [`use-railway`](use-railway/SKILL.md) | Operate Railway infrastructure: sign up for or sign in to a Railway account, create projects, provision services and databases, manage object storage buckets, deploy code, configure environments and variables, manage domains, troubleshoot failures, check status and metrics, set up Railway agent tool… |
| [`verifier`](verifier/SKILL.md) | Independently verify exactly one selected software project per run and issue an evidence-backed acceptance or release verdict. Use when the user says 验收一下, 调用软件验收skill, 软件验收, verifier, or asks for release recheck. When an approved Product-Design-Taskpack exists, ingest it read-only, freeze the compl… |
| [`video-replica`](video-replica/SKILL.md) | Evidence-backed video experience replication from local videos, screen recordings, prototype walkthroughs, live URLs, or runnable source, ending by default with one validated ZIP deliverable in the user's Downloads directory. Use when the user says “视频复刻skill”, “视频复刻 Skill”, invokes $video-replica,… |
| [`webapp-testing`](webapp-testing/SKILL.md) | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs. |

## 学习与知识（4）

| Skill | 何时使用 |
|---|---|
| [`book-to-skill`](book-to-skill/SKILL.md) | Converts books and documents (PDF, EPUB, DOCX, HTML, Markdown, plain text, RTF, MOBI/AZW with Calibre) into structured agent skills, extracting frameworks, mental models, principles, techniques, and anti-patterns. Use when the user wants to study a document through GitHub Copilot CLI, Amp, or Claude… |
| [`chronicle`](chronicle/SKILL.md) | Allows you to view the user's screen as well as several hours of history. Use when the user makes a reference to their recent work, for which it'd be helpful to see the screen. This skill MUST be used whenever you need to resolve ambiguity in a user request, where the user hasn't specified enough co… |
| [`last30days`](last30days/SKILL.md) | Research what people actually say about any topic in the last 30 days. Pulls posts and engagement from Reddit, X, YouTube, TikTok, Hacker News, Polymarket, GitHub, and the web. Includes a doctor health check to diagnose broken or missing sources. |
| [`study-project-orchestrator`](study-project-orchestrator/SKILL.md) | Use when the user wants to start, continue, sync, review, or optimize a fixed-period Study Project for learning a new domain or skill. Creates and maintains GitHub-backed learning memory under LinzeColin/Notion/StudyProjects/project-slug, treats Notion as a clean notebook, backs up Notion before cre… |

## 业务流程（14）

| Skill | 何时使用 |
|---|---|
| [`gongzi-fafang-biaozhun`](gongzi-fafang-biaozhun/SKILL.md) | Use when Codex is asked to整理、生成、校验或复核工资/薪资/发放表 Excel，尤其是当月原始发放文件按上月模板生成最终发放版、ABExcel 校验、差异报告、金额分校验、B公司/报销路由或密码 123 打开校验。 |
| [`hongquan-main-contract-dws`](hongquan-main-contract-dws/SKILL.md) | 从红圈 cloud.hecom.cn 导出、下载并归档主合同 DWS/Excel 原始数据。Use when the user asks for 红圈主合同DWS、红圈主合同导出、下载红圈主合同、更新红圈主合同原始数据，或需要把红圈主合同 Excel 按日期命名并移动到固定原始数据目录。 |
| [`info-fee-update`](info-fee-update/SKILL.md) | Fill and update Chinese 信息费申请表 and 2023-2025年信息费明细表 workbooks from contractor/payment notes, using Chrome 红圈 主合同 search to look up contract number and contract amount from 甲方/project keywords. Use when the user asks Codex to 信息费更新, 填信息费Excel, 开委外单/信息费单, 根据甲方去红圈查合同号/合同金额, or continue this recorded WP… |
| [`km-bid-adjudicate`](km-bid-adjudicate/SKILL.md) | 基于官方正文和附件构建采购事件图，识别货物、维修、工程、结果型运维、纯劳务、加工或混合主要义务，并映射A/B方向。用于复杂采购/维修交叉语义；未知不得排除。 |
| [`km-bid-audit`](km-bid-audit/SKILL.md) | 对P0/P1和高风险排除进行独立反对者审计，专门寻找维修机会被采购词误删、货物被工程词误推、地域/标包/资格/结果误判。审计冲突必须保留并升级，不得自动删除。 |
| [`km-bid-brief`](km-bid-brief/SKILL.md) | 把已审计机会整理成Owner可直接使用的简明搜标结果、截止动作和投标证据清单。用于每日/增量报告，限制噪声和人工时间；不得把P2包装成可投或隐藏来源降级。 |
| [`km-bid-discover`](km-bid-discover/SKILL.md) | 在公开与已授权招采来源中进行高召回搜标、来源覆盖和官方线索发现；用于A/B工业维修检修机会的全量或增量发现。不得按设备/采购负关键词删结果，不作最终可投或排除结论。 |
| [`km-bid-evidence`](km-bid-evidence/SKILL.md) | 将搜标线索回到官方公告，安全获取正文、附件、答疑、更正、标包和实施地，并生成可定位、可哈希、可重放的证据包。用于深取证，不作业务或资格结论。 |
| [`km-bid-evolve`](km-bid-evolve/SKILL.md) | 基于历史回放、Owner反馈、钉钉投标结果和官方公示评估搜标质量，提出安全扩词、来源修复、排序或规则修改建议，并做影子运行。不得修改正式规则、Skill、holdout、evaluator或自动发布。 |
| [`km-bid-lifecycle`](km-bid-lifecycle/SKILL.md) | 通过DingTalk Workspace CLI只读同步“商务报价群”投标台账和Excel附件，自动追踪资格/候选/中标/流标/重招结果、竞争对手、报价和周期性项目。命令运行时动态探测；无结果保持待定。 |
| [`km-bid-qualify`](km-bid-qualify/SKILL.md) | 把语义候选绑定到唯一投标主体，核当前资质、人员、社保、业绩、供应商库、地域、商务、资金和产能，输出P0/P1/P2/X及唯一下一步。不得跨公司拼接或用过期底表当实时事实。 |
| [`km-bid-scout`](km-bid-scout/SKILL.md) | 路由和编排 KM 工业搜标的只读发现、官方取证、语义、资格商务、独立审计、简报、DWS 生命周期与影子演化。用于选择最小子 Skill 链并保持停止门；不自动报名、付款、签章、提交、发消息或发布规则。 |
| [`project-cost-table-skill`](project-cost-table-skill/SKILL.md) | 为 KMFA 项目成本表运行提供输入充分性预检、公共与私有数据隔离、双成本口径、全负担工资分配、fail-closed 校验和可定位输出；当用户要求生成、复算、核对或回放项目成本表时使用。 |
| [`serenity-skill`](serenity-skill/SKILL.md) | Turn an investment agent into a supply-chain bottleneck hunter. Use this skill for source-backed investment research, live market/theme scans, AI/semi/technology value-chain mapping, A-share/HK/US stock screening, thesis stress tests, and Serenity-inspired research conversations. Trigger on requests… |

## 协作与通讯（3）

| Skill | 何时使用 |
|---|---|
| [`agent-reach`](agent-reach/SKILL.md) | Internet research and retrieval router for web search, URLs, RSS, GitHub, YouTube, Bilibili, Xiaohongshu, X/Twitter, Reddit, Facebook, Instagram, V2EX, LinkedIn/jobs, Xueqiu, and podcasts. Use for fetching/searching current internet content, not for posting, commenting, liking, or general analysis t… |
| [`dws`](dws/SKILL.md) | 管理钉钉产品能力(AI表格/AI搜问/日历/通讯录/群聊与机器人/待办/审批/考勤/日志/DING消息/开放平台文档/钉钉文档/钉钉云盘/AI听记/邮箱/在线电子表格/知识库等)。当用户需要操作表格数据、管理日程会议、模糊找人/查谁负责某事项、查询通讯录、管理群聊、机器人发消息、创建待办、提交审批、查看考勤、提交日报周报（钉钉日志模版）、读写钉钉文档、上传下载云盘文件、查询听记纪要、收发邮件、读写在线电子表格(axls)、管理钉钉知识库时使用。 |
| [`internal-comms`](internal-comms/SKILL.md) | A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident rep… |

## 其他（3）

| Skill | 何时使用 |
|---|---|
| [`codex-encrypted-backup`](codex-encrypted-backup/SKILL.md) | 在不创建本地自动脚本或 launchd 的前提下，将本机 Codex 的 memories、全部 sessions（含 archived）及受管 attachments 加密备份到 LinzeColin/AgentDatabase 的 GitHub Release。用于创建、执行、核验、保留或恢复验证这一备份通道。 |
| [`gpt-tasteskill`](gpt-tasteskill/SKILL.md) | Elite UX/UI & Advanced GSAP Motion Engineer. Enforces Python-driven true randomization for layout variance, strict AIDA page structure, wide editorial typography (bans 6-line wraps), gapless bento grids, strict GSAP ScrollTriggers (pinning, stacking, scrubbing), inline micro-images, and massive sect… |
| [`hatch-pet`](hatch-pet/SKILL.md) | Create, repair, validate, visually QA, and package Codex-compatible v2 animated pets from character art, generated images, company or prospect brand cues, or visual references. Use for any new Codex pet, custom mascot, non-pixel pet style, brand-inspired pet, existing-pet repair, or 8x11 spritesheet… |

## 其他（3）

| Skill | 何时使用 |
|---|---|
| [`codex-encrypted-backup`](codex-encrypted-backup/SKILL.md) | 在不创建本地自动脚本或 launchd 的前提下，将本机 Codex 的 memories、全部 sessions（含 archived）及受管 attachments 加密备份到 LinzeColin/AgentDatabase 的 GitHub Release。用于创建、执行、核验、保留或恢复验证这一备份通道。 |
| [`gpt-tasteskill`](gpt-tasteskill/SKILL.md) | Elite UX/UI & Advanced GSAP Motion Engineer. Enforces Python-driven true randomization for layout variance, strict AIDA page structure, wide editorial typography (bans 6-line wraps), gapless bento grids, strict GSAP ScrollTriggers (pinning, stacking, scrubbing), inline micro-images, and massive sect… |
| [`hatch-pet`](hatch-pet/SKILL.md) | Create, repair, validate, visually QA, and package Codex-compatible v2 animated pets from character art, generated images, company or prospect brand cues, or visual references. Use for any new Codex pet, custom mascot, non-pixel pet style, brand-inspired pet, existing-pet repair, or 8x11 spritesheet… |
