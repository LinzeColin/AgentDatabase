# AgentDatabase

Agent 数据仓。三个活动范围：
- **`OpenAIDatabase/`** —— Codex / OpenAI 会话与记忆运行时（记忆图谱、个性化、行为智能）。
- **`MemoryAtlas/`** —— 记忆图谱发布件。
- **`CodexSkills/`** —— 本机 Codex Skill 的仓库镜像与治理登记（人物蒸馏等）。

以及从旧 Mac 迁出的历史归档（作为 Release 资产，不占本地存储）。

## 📦 数据落地政策（长期有效 · 自运行分仓治理）

**本仓存代码/治理/技能登记与已发布制品；开发中新产生的长期/业务/运行时数据不入本仓**，
一律写私有仓 `LinzeColin/Private-Database`：Agent 会话/记忆数据 → `Private-AgentDatabase/`。
用各仓内 `private_db_client.py` 免 clone 读写（`ingest/get/list/verify`）；Private-Database 禁止 `git clone`；派生/临时物走 `.gitignore`。
> ⛔ 唯一待闭环：`OpenAIDatabase/data/` 仍是活运行记忆、尚未迁走，详见 [`OpenAIDatabase/MIGRATION_MANDATE.md`](OpenAIDatabase/MIGRATION_MANDATE.md)（SDK cutover 完成前不得删）。

### 外部产品蒸馏成果（**内容只在私有仓，本仓只放指针**）

**本仓是 PUBLIC。** 外部商业闭源产品的蒸馏产物一律 `private-only`，一个字节都不进本仓。

| 对象 | 交付包（私有仓路径） | 状态 |
|---|---|---|
| Kimi Code **v0.34.0** | `Private-AgentDatabase/kimi-code-distillation/kimi-code-hub-install-v1.0.0.zip` | 单位数 / 工具数 / 门数 **见包内现算的 `README.md`**（此处曾写死「21 工具、17/17 门」，两个数都早已过期） |

取包与验收（免 clone，复用 `gh` 登录态）：

```bash
python3 OpenAIDatabase/scripts/private_db_client.py get Private-AgentDatabase \
  kimi-code-distillation/kimi-code-hub-install-v1.0.0.zip /tmp/kc.zip
unzip -q /tmp/kc.zip -d /tmp/kc && python3 /tmp/kc/kimi-code-hub/tools/kc_verify.py /tmp/kc/kimi-code-hub
```

> ⚠️ 版本号曾长期写成 **v2.38.5** —— 那是 bundle 里第三方 rive 库的版本。
> 真值 **0.34.0**，两条独立证据：`main.cjs` 的构建注入点 + 本机更新通道自报。

**依赖如实说清**（这一段我先写成「接手方只需要 python3」，那是**错的** ——上面第一条命令要用本仓的脚本，而它内部调 `gh api`）：

| 步骤 | 需要什么 |
|---|---|
| 取包（第一条命令） | 本仓 + `gh` 已登录。**或者**直接在 GitHub 网页上从私有仓下载那个 zip —— 那样不需要本仓、也不需要 gh |
| 验收与读全部内容（第二条命令起） | **只要 `python3`** —— 零第三方 import、零外部工具链调用，包内 G92 逐条判这件事 |

**全程不需要任何 AI 工具链**：不需要 Claude、不需要任何模型 API。

交接说明同在私有仓 `kimi-code-distillation/HANDOFF.md`（含待 Owner 裁定的 KSEC-001）。
冻结快照 236 MB 留在本机 `_protected/kimi-code-distillation/phase0/`，**不入任何仓**。

## Contents

Large archives are stored as **release assets** (not in git), because GitHub
rejects any file over 100 MB inside a repository. See the release
[`old-mac-20260630`](../../releases/tag/old-mac-20260630).

| Asset | Size | Contents |
|---|---|---|
| `codex-token-history-migration-pack-20260630.tar.gz` | 1.08 GiB | Token-usage history migration pack from the old Mac: 408 session rollouts (2026-06-02 → 2026-06-30), sqlite log databases, `~/.codex` home state |
| `old-mac-session-history-20260630.tar.gz` | 800 MiB | Old-Mac Codex session history export |
| `current-mac-session-history-20260630.tar.gz` | 36.5 MiB | Current-Mac Codex session history export, as of 2026-06-30 |
| `codex-numeric-token-usage-export-20260630.tar.gz` | 147 KiB | Numeric token-usage export (CSV/JSON) |

The 408 session rollouts in the migration pack exist **only** here — they were never
imported into `~/.codex/sessions` on this machine.

## Restore

    gh release download old-mac-20260630 --repo LinzeColin/AgentDatabase
    shasum -a 256 -c checksums.txt
    tar -xzf codex-token-history-migration-pack-20260630.tar.gz

## Integrity

`checksums.txt` holds the sha256 of every asset, computed before upload.

## CodexSkills

本机 Codex Skill 的仓库镜像与治理登记。索引：[`CodexSkills/README.md`](CodexSkills/README.md)（人读）、[`CodexSkills/index.json`](CodexSkills/index.json)（机器读，供 Agent 按需检索单个 skill，不要整仓 clone）。

“人物蒸馏 Skill”构建器位于
[`CodexSkills/registry/codex/persona-distiller/`](CodexSkills/registry/codex/persona-distiller/)，
唯一 canonical 登记与专家团队 Skill 位于平级的
[`CodexSkills/registry/codex/persona-distiller-group/`](CodexSkills/registry/codex/persona-distiller-group/)。
它生成的每个人物产物必须且只能登记到对应的一个身份目录；每个人物只进入一个
单一主身份目录，不再使用“多重身份”目录。十二个目录固定为 `材料建工师/`、
`软件开发师/`、`艺术设计师/`、`创业经营师/`、`投资资本师/`、`思想教育师/`、
`政治法律师/`、`客户营销师/`、`建造采购师/`、`财务合规师/`、`医疗护理师/`、
`农林牧渔师/`；每个版本只保存一个全量完整交付 ZIP，机器索引为
[`team-index.json`](CodexSkills/registry/codex/persona-distiller-group/team-index.json)，
最高优先级团队路由为
[`CANONICAL-ROOT-ROUTE.md`](CodexSkills/registry/codex/persona-distiller-group/CANONICAL-ROOT-ROUTE.md)。
身份目录只用于唯一登记；安装后用户直接调用对应人物 Skill，内部自动路由身份与场景，
不要求用户选择身份。每个 canonical 人物的成功蒸馏产物独立使用
`0.0.0.1` 至 `0.0.0.999` 连续版本；单次运行没有版本编号。

## 治理规则：受保护资产

`CodexSkills/registry/codex/persona-distiller/**` 与
`CodexSkills/registry/codex/persona-distiller-group/**` 是**不可再生资产**。
每个交付 ZIP 都是一次数十万 token、约一小时的蒸馏产出，丢了只能重蒸。

**为什么有这条规则**：2026-07-26 出过一次严重丢失 —— 一次例行同步
（`chore(skills): 同步本机 Skill 到仓库（更新 4）`）把本机上一份**陈旧的**副本按
「本机 → 仓库」方向覆盖回仓库，`team-index.json` 从 **70 人掉到 3 人**，
两个 skill 合计删掉 11159 行 / 311 个文件，事后靠 git 历史恢复。
根因不是有人误删，而是**同步器默认本机永远是真相源，而这两个 skill 的真相源其实是仓库**。

1. **仓库优先**：受保护资产以仓库为准。本机副本陈旧时，从仓库更新本机，
   **绝不**把本机推平仓库。
2. **只增不减**：任何操作若会让 `team-index.json` 的 `products` 数量减少、
   或删除任一已登记人物目录，一律视为事故并中止。
   `CodexSkills/sync_skills.py` 已内置这道硬门（写入前比对本机与仓库的已登记人物集合，
   会抹人就中止、不写不提交不推送），绕过需显式 `--allow-persona-shrink` 并写明理由。
3. **改前留基线、改后验数**：数字必须只增不减。

   ```bash
   python3 CodexSkills/registry/codex/persona-distiller-group/scripts/validate_group.py \
       --registry-root CodexSkills/registry/codex/persona-distiller-group
   python3 CodexSkills/registry/codex/persona-distiller/scripts/self_check.py
   # 已入库的交付 ZIP 数必须等于 team-index 的 products 数
   git -c core.quotepath=false ls-files -- CodexSkills/registry/codex/persona-distiller-group \
       | grep -c '\.zip$'
   ```

   > `git ls-files` 默认会把中文路径转义成 `"...\350..."`，结尾是引号不是 `zip`，
   > 直接 `grep '\.zip$'` 会数出 0 —— 必须带 `-c core.quotepath=false`。

4. **交付 ZIP 必须入库**：根 `.gitignore` 有全局 `*.zip`，已针对
   `CodexSkills/registry/codex/persona-distiller-group/**/*.zip` 开了否定例外。
   不要删掉那条例外 —— 没有它，`register_persona` 之后 `git add -A` 会**静默漏掉 ZIP**，
   仓库会变成「`team-index` 说 N 人、实际只有 N−1 个 ZIP」的坏状态。
5. **禁止**：对受保护路径 `rm -rf`；`git push --force`；`git reset --hard` 到丢失点之前的提交；
   `git gc --prune=now`（立即销毁不可达对象、没有后悔药，本机已有线程因此丢过 2467 个提交
   且不可恢复 —— 清缓存只用 `git gc`）。
5. **三条恢复退路**：① git 历史（`git log --diff-filter=D -- <路径>` 定位删除点，
   `git checkout <删除前的提交> -- <路径>` 取回）；② 本机快照 `~/Downloads/蒸馏/` 里的交付 ZIP
   （`register_persona.py <zip>` 重新登记即可完全复原）；③ GitHub release 资产。
   恢复后必须重跑上面两条校验，并让 `persona-distiller/tests` 全绿。
6. **文档由数据派生**：身份目录清单与登记人数一律从 `team-index.json` 生成，
   不在文档或脚本里硬编码，避免分类改版后文档滞留旧分类。

## 全量专家团队蒸馏（长期任务）

目标 12 组 × 50 = 600 人。单会话、并发 1、不花 API 钱、**每周只用 20% 周额度**；
撞额度即推送 main 并休眠，下周继续。
作业规程与锁定决策不在本仓，在本机 `~/Downloads/蒸馏/`：
`_每次开工必读.md`（总入口）、`_决策台账.md`、`_质量评分矩阵_v1.md`、
`_蒸馏名单_v1草稿.md`、`_pipeline/RUNBOOK.md`（每人 12 步）、
`_pipeline/next_person.py`（确定性算出“下一个是谁” —— done 状态实时从本仓 +
Downloads 推导，不靠记忆，因此换会话、隔几周都不会漂移）。
每周开工只需一句：**「开始本周蒸馏」**。
