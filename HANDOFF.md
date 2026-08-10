# HANDOFF —— 接手这个仓要知道的全部

> 这份文件是**唯一入口**。一句话 prompt 只需把你指到这里。
> 写于 2026-08-10；每次移交前更新「现在做到哪」一节。

---

## 0. 先读这两份，其余都是细节

1. `~/Documents/Codex/GithubProject/README.md` 的 **「七条铁律」**（第 23 行起）——
   本机所有仓共用的硬约束。**代价最高的三条**摘在下面第 5 节。
2. `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_每次开工必读.md` ——
   这个项目自己的开工必读。

---

## 1. 这个项目在做什么

**人物蒸馏（persona distillation）**：把一个真实人物的公开材料，
蒸馏成一套可被 AI 扮演的产物（十份 Markdown + 断言层 + 用例集），
并用**盲评**测出它比裸模型好多少（`delta`）。

- 目标规模 **600 人**，分 **12 个职业族**。
- **只取公有领域材料**；付费墙一律不碰；不绕任何访问控制、不绕验证码。
  「开放获取」**不等于**公有领域。
- 每个人物走同一条流水线，**每一步都有判据（checker）把关**。

---

## 2. 现在做到哪（**更新这一节，不要更新别处**）

- **已入库：101 个产物**（2026-08-10 实测）。★ **要报这个数就当场跑一遍**，不要抄这一行：
  ```bash
  python3 -c "import json;print(len(json.load(open('CodexSkills/registry/codex/persona-distiller-group/team-index.json'))['products']))"
  ```
- **延后／拒发名单：137 条**（`_ledgers/_延后名单.json` 的 `total`），
  其中 **77 条**带 `pd_scope_pending`（等待裁定 ㉜）。
- **刚做完**：
  - **#156 Henry Gantt 记拒发**——真 delta **+0.0078**，quick 门 +0.03，**两席跨零**
    （F −0.0125 / G +0.0281）。判决书 `_corpora/wip-gantt-156/workspaces/henry-gantt/evals/00-结案.md`。
    ★ 盲判装置是至今最干净的一次：均长比 1.01、**「候选更短 ≥25%」首次通过（7/16）**、
    九种表面特征两侧全 0/16。
  - **#157–#160 建造采购师四人一次判掉**（Kelley/Walker/Oliver/Hau Lee）——
    判据是**出版年**晚于 1931 分界，**第二个被 PD 规则清空的族**。
  - **#161 Luca Pacioli 记延后（新类别⑦：方法证据全部汇到一部作品）**。
    ★ **这一条值得读，因为它不是「语料不够」**：10 份源、294 万字符、全部公有领域、
    全部读得到、研究门 passed、断言层 14 条逐字引文预检全过——
    **而他的记账论述只存在于一部作品**，三份译本只算一处证据，
    于是「方法类断言要 ≥2 处独立证据」诚实地只满足到 **1 个 mental-model ＋ 1 个 heuristic**
    （门要 2 和 3）。判决书 `_corpora/wip-pacioli-161/workspaces/luca-pacioli/references/research/00-处置.md`。
- **本轮新落的判据**：`check_translation_witness.py`——
  **同一部作品的多个译本不许当两处独立证据**。
  根因：`check_claim_source_independence` 的作品分组**是语言盲的**，
  实测把 Pacioli 的 10 份源分成 10 个作品组，而其中三份译的是同一篇论著。
  ★ 它的「自动认出哪些是译本」那一半**实测做不出来，已砍掉**（全库误报 38,368 对），
  文件头留了数字，别再建一遍。
- **待用户裁定的条目**：见任务列表里带「待裁定」字样的那些（⑤⑱⑲⑳㉑㉒㉓㉕㉖㉚㉛㉜**㉝**）。
  **这些不是你能自己决定的**，遇到就停下来问。
  ★ **㉜（PD-only 规则的射程）已经在挡排期**：延后名单里 `pd_scope_pending` 已 **77 人**，
  而剩余队列里生年 <1913（可能可做）的还有 **62 人**——**队列没被规则耗尽**。
  **这些延后都是可一行反转的**，不要因为它没裁定就停下来。
  ★ **㉝ 是本轮新增**：`status: hypothesis` 在流程里没有落脚点，
  门对它与 `pattern` 一视同仁地要 ≥2 处来源。

---

## 3. 怎么跑

所有工具在 `CodexSkills/registry/codex/persona-distiller/scripts/`。

```bash
cd CodexSkills/registry/codex/persona-distiller
```

| 要做什么 | 命令 |
|---|---|
| **下一个做谁** | `python3 references/pipeline/next_person.py` |
| 同名护栏 | `python3 scripts/namesake_gate.py <人名>` |
| 建工作区 | `python3 scripts/init_target.py …` |
| 灌语料 | `python3 scripts/ingest.py …` |
| **三道主门** | `python3 scripts/quality_check.py <workspace> --phase research\|synthesis\|release` |
| 造盲判载荷 | `python3 scripts/build_blind_payload.py --workspace <ws> --round-dir round1 --candidate <c.json> --baseline <b.json>` |
| 汇总判分 | `python3 scripts/assemble_judge_results.py …` |
| 打包 / 入库 | `python3 scripts/package_target.py …` / `register_persona.py …` |

★ **NEXT 一律以 `next_person.py` 的输出为准**，不许凭记忆或凭队列文件里的顺序。

★★ 每个 `check_*.py` 都有 `--self-test`。**改判据之前先跑它，改完再跑一次。**
判据自己也会错——本项目里判据的第一版出错是常态，不是例外。

---

## 4. 数据在哪

| 东西 | 路径 |
|---|---|
| 判据与工具（**唯一真源**） | `CodexSkills/registry/codex/persona-distiller/scripts/` |
| 判据镜像（合同：`check_*.py` 与上面**逐字节相同**） | `.../references/pipeline/checkers/` |
| 人物工作区 | `CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-<名>-<编号>/` |
| ★ 工作区的**真实层级**要用 `find … -path '*/evidence/claims.jsonl'` 定位 | 见下 |
| 名册（已入库的人） | `CodexSkills/registry/codex/persona-distiller-group/` |
| **台账**（队列 / 延后名单 / 卒年 / 额度 / 决策） | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/` |
| 已交付的 44 个 zip | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/*.zip` |

### ★★ 工作区层级：有三个人是**双层嵌套**，别猜路径

`_corpora/wip-osler-110/workspaces/william-osler/**william-osler**/`（Nightingale、Virchow 同）；
而近期的人（Gantt、Nasmyth、Pacioli）是单层。
**根因是 `init_target.py --workspace` 会自己追加 slug**——
传 `.../workspaces/<slug>` 就会变成 `.../workspaces/<slug>/<slug>`，
**要传 `.../workspaces`**。

**所以定位工作区一律用：**

```bash
find CodexSkills/skill_log_evals/persona-distiller/_corpora -path '*<slug>*/evidence/claims.jsonl'
```

### ★★ 抓源方**不要**把下载件写进 `raw/`

`ingest.py` 会把每份源**复制两处**：`raw/src-<id>/<名>.txt` 与
`references/sources/src-<id>/<名>.normalized.txt`。
所以如果抓源方直接把原件下载到 `raw/`，灌完之后 `raw/` 里会同时有
`raw/<名>.txt` 与 `raw/src-<id>/<名>.txt` —— **同一份文件两次**。

**给抓源子代理的指令里，落盘目录要写工作区外的暂存目录**（或 `_staging/`），
灌完再删暂存。2026-08-10 我给 Pacioli 的指令写成了 `raw/`，
于是那个工作区成了全库 28 个里**唯一**有同名冲突的一个
（文件 17 份、按 basename 去重后 10 份）。

★ 路径猜错时判据会老实返回 `状态: …未核验（不是通过）`——
**但只有你把 `状态` 字段打印出来才看得见。** 2026-08-10 我因此差点把「没核过」记成「修好了」。

★ 台账原本只在 `~/Downloads/蒸馏/`，**2026-08-10 搬进仓**。
`next_person.py` 现在**仓内优先**；两处都在且内容不同时，它会把两边的 sha256 与 mtime
打到 stderr 上——**看到那段就先弄清哪一份是对的，别当没看见。**

---

## 5. 三条最贵的铁律（全文见 GithubProject/README.md）

1. **主树只读，开发一律在 worktree。**
   `GithubProject/<REPO>/` 永远停 `main`、永远干净、只 `git pull` 不写。
   ```bash
   git worktree add ../_scratch/<repo>-<任务名> -b <分支名> origin/main
   ```
2. **谁开的谁收。** 代码合了 + PR 关了 + worktree 收了 + 分支删了 + 缓存清了，**五件缺一不算完成**。
   清缓存用 `git gc`，**禁止 `--prune=now`**（有线程因此丢过 2467 个提交且不可恢复）。
3. **云端零付费，账单恒为 $0.00。** 禁止 R2 的 `InfrequentAccess` 存储类；
   禁止「整包下载来判断存在」的高频轮询。

---

## 6. 这个项目最容易犯的错（**都是实测过的，不是假设**）

1. **判据绿了但指错了文件。** 已发生二十七次以上。
   改完判据要**真去把它该抓的东西改坏一次**，看它红不红；**正例必须同时是绿的**。
2. **空默认值吞掉「不知道」。** `[]` / `{}` / `0 个文件` 都会被读成「没问题」。
   判据里凡有早退分支，**返回的字段形状必须和正常分支一样**，只多一个「未核验」标记。
3. **自述不是证据。** 子代理说「我没读 holdout」不算数，要有独立通道去核。
4. **夹具比真东西干净就等于没测。** 自测夹具要像真语料一样脏（OCR 讹字、跨行连字符、页眉插进词中间）。
5. **逐字引文就是逐字。** OCR 讹字**不许改**；要给还原读法就写在括号里并注明「这是判读」。
6. **报数之前先跑一遍命令。** 手写的数必然往好里漂。
7. **没做完不能停。** 发现意外先把不依赖它的事做完，别用汇报替代推进。
8. **达不到门时不要放宽判据。** 选诚实退路（记延后 / 记拒发）+ 写台账，继续往下走。

---

## 7. 交接时的注意

### ★★★★ 给用户的一句话 prompt（**合并到 main 之后才成立**）

```
接手我的人物蒸馏项目：cd ~/Documents/Codex/GithubProject/AgentDatabase && git pull，读 HANDOFF.md 按它继续做，遇到标「待裁定」的条目停下来问我。
```

**不需要任何设置**：路径是本机已有的主树，`git pull` 之后 `HANDOFF.md` 就在仓根。

### ★★★★ 它现在还不成立，缺的是这一步

实测（2026-08-10）：

| 检查 | 结果 |
|---|---|
| `~/Documents/Codex/GithubProject/AgentDatabase/HANDOFF.md` | **不存在** |
| 主树分支 / 状态 | `main` / 干净 |
| 主树 HEAD vs 本分支 | **落后 862 个提交** |

**HANDOFF.md 只在 `claude/character-distillation-skill-reorganize-d57595` 上。**
移交那晚要做完的是：

```bash
git push -u origin claude/character-distillation-skill-reorganize-d57595
gh pr create --fill && gh pr merge --squash --delete-branch
cd ~/Documents/Codex/GithubProject/AgentDatabase && git pull
```

做完之后，上面那句 prompt 才会在收件人的布局里跑通。

### 已经在**干净检出**里验过的（不是在我的工作目录里验的）

`git worktree add --detach` 一个全新检出，逐条跑：

| 步骤 | 结果 |
|---|---|
| `HANDOFF.md` 在仓根 | ✓ |
| §2 那条「当场跑一遍」的产物计数命令 | ✓ 101 |
| `_ledgers/_每次开工必读.md` | ✓ |
| `references/pipeline/next_person.py` | ✓ **NEXT = William Paton（财务合规师）** |

★ `next_person.py` 会在 stderr 上打印台账来源；两处不一致时它**明说用的是仓内那份**
并给出两边的 sha256 与 mtime。**看到那条警告不是出错，是它在告诉你用了哪一份。**
★★ 演练检出跑完**已经收掉**（铁律 3：谁开的谁收）。

### 交接前还要做的

1. **`_scratch/agentdb-nasmyth-153` 这个 worktree 是我开的，得我收**：
   合并 → 关 PR → `git worktree remove` → 删分支 → `git gc`（**禁止 `--prune=now`**）。
2. **`_protected/` 永不上传**，交接时也不上传。
3. **Notion 全程没碰过**，按约定要等 600 人全完成。
