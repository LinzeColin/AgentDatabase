# 接手入口（2026-08-12）

**给下一个接手的 agent。** 这份是指针，不是内容 —— 本仓是**公开仓**，实质内容都在私有仓，路径写在下面。

## 一句话就够

用户会说：

> **开始本周蒸馏**

看到这句话，**先按「第一步」把工作树恢复出来**，然后照
`CodexSkills/skill_log_evals/persona-distiller/_ledgers/_每次开工必读.md` 从第零步执行。
那份文件是防漂移总入口，里面的锁定项不许擅自改。

## 现在做到哪

| | |
|---|---|
| 已交付人物产物 | **102** 个（`CodexSkills/registry/codex/persona-distiller-group/team-index.json` 的 `products`） |
| 队列下一个 | **Dennis Ritchie**（软件开发师族，priority 1 / order 1） |
| 延后名单 | 5 条（各带退档理由，别当成"没做"） |
| 最近一次裁定 | 2026-08-12「按可得性选档 + 退档写明理由」，取代旧的"全 deep" |

## 第一步：把工作树恢复出来（**必做，否则你看到的仓是残缺的**）

`origin/main` 上**没有**最近这一批工作。截至 2026-08-12，
分支 `claude/character-distillation-skill-reorganize-d57595`（1388 个提交、约 2.3 GB）
**只存在于一个 git bundle 里**：

```
仓库：LinzeColin/Private-Database（私有）
Release：agentdb-handover-20260812
资产：agentdb-persona-distiller-full.bundle（约 972 MB）
```

恢复：

```bash
gh release download agentdb-handover-20260812 \
  --repo LinzeColin/Private-Database \
  --pattern 'agentdb-persona-distiller-full.bundle' --dir /tmp

git bundle verify /tmp/agentdb-persona-distiller-full.bundle     # 应报 "records a complete history"
git clone /tmp/agentdb-persona-distiller-full.bundle agentdb-restored
cd agentdb-restored && git checkout claude/character-distillation-skill-reorganize-d57595
```

**为什么是 bundle 不是分支**：这一支里含 `_ledgers/_教训库/`（agent 教训库，涉及基础设施细节），
按移交规则「任何 private-only 资产一个字节都不许进 AgentDatabase」，不能推公开仓；
而 2.3 GB 也会被本机 pre-push 的 200 MB 体积闸拒绝。放私有 Release 是既定的存储优先级
（Release 资产 > R2 > OVH：不计仓库体积、无操作计费）。

## 三本台账在哪（决定"下一个做谁"，缺了就断线）

它们既在上面那个 bundle 里，也**单独存了一份**方便直接取：

```bash
python3 <任一源仓>/private_db_client.py get Private-AgentDatabase \
  persona-distiller-ledgers/_蒸馏队列.json ./_蒸馏队列.json
# 另两份：persona-distiller-ledgers/_延后名单.json、persona-distiller-ledgers/_卒年.json
```

## 别人踩过的坑（开工前扫一眼，省得重踩）

```bash
python3 <任一源仓>/private_db_client.py get Private-AgentDatabase \
  claude-memory/README.md ./lessons.md
```

`Private-AgentDatabase/claude-memory/` 有 129 条实际踩过的教训，`README.md` 是「最贵的十条」，一屏读完。
入口也写在 `LinzeColin/Governance` 的 `AGENTS.md` 里。

## 规矩在哪（按优先级，冲突时上面的赢）

1. **本机七条铁律** —— `~/Documents/Codex/GithubProject/README.md`
   （按需 clone / **主树只读、开发一律在 worktree** / 谁开的谁收 / 不跨仓 /
   `_protected/` 永不删永不传 / `_scratch/` 放临时物 / 云端零付费）
2. **跨仓治理** —— `LinzeColin/Governance`（私有）：双平面七文件、三道门、数据落地铁律
3. **部署事实与已知事故** —— `LinzeColin/Private-Database` 的 `OPS/AGENT_ONBOARDING.md`
4. **本项目锁定项** —— `_ledgers/_决策台账.md`（恢复工作树后可见）

## 判据怎么跑

```bash
# 受保护资产完好性（每次开工第零步，必做）
python3 CodexSkills/registry/codex/persona-distiller-group/scripts/validate_group.py \
  --registry-root CodexSkills/registry/codex/persona-distiller-group
```

`passed=true` 且 `products` **不少于** `_决策台账.md` 末尾记录的数字才继续。
少了就是事故 —— **停下先恢复**，且方向永远是「仓库 → 本机」，绝不用本机副本覆盖仓库。
（2026-07-26 出过一次：例行同步反向覆盖，`team-index.json` 从 70 人掉到 3 人。）

## 云端三个站点怎么部署（2026-08-12 起统一）

`LinzeColin/MetaDatabase` 里三个 Cloudflare Worker **各有认可的部署入口，不要裸跑 `wrangler deploy`**：

| 站点 | 入口 |
|---|---|
| `adp.linzezhang.com` | `arxiv-daily-push/deploy/cloudflare/deploy.py` |
| `eei.linzezhang.com` | `EEI/scripts/deploy_cloud.sh` |
| `weread.linzezhang.com` | `WeReadPort` 里 `npm run deploy:cloudflare` |

三个脚本都会：部署前取回线上变量（缺一个就拒绝部署）→ 部署 → 回读线上确认 → 不过自动回滚。
**裸跑 `wrangler deploy` 会用配置文件替换线上 vars**（secret 保留、plain_text 不保留）——
2026-08-12 真发生过一次，站点断了 3 分钟。

## 还悬着的三件事

1. **jobhunt 验收停在「不确定」** —— 核心链路在注册＋邮箱验证之后，验收方不能替 Owner 创建账户。
   解法写在 `MetaDatabase/JobHuntBotOnline/OWNER_WALKTHROUGH_20260811.md`：先给 Owner 一条不用邮箱的入口。
2. **`real-arxiv-30-day-backfill` 那道门过不去** —— 要求 30 天里每天都有排队行，实测只有 11 天有；
   是阈值设错还是重放逻辑该产出而没产出，要写它的人判。详见 MetaDatabase PR #182 的评论。
3. **ADP 的 `arxiv:TimeoutError` 根因未查** —— 33 天里 5 次，那 5 天主源整个缺席。
   现在至少不会再被静默算成「正常」（PR #184）。
