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
- **在办：#162 William Andrew Paton**（财务合规师，1889–1991）。
  工作区 `_corpora/wip-paton-162/workspaces/william-andrew-paton`（**单层，不是双层嵌套**）。
  - 同名门 blocked(14) → 按 Livermore #100 先例选定 → **ready**。
    ★★★★ **最大风险是他儿子** `William A. Paton, Jr., 1925-`：
    LC 给父子**同一个领域标目**，儿子另有一条**不带生卒年的光秃标目**，父子还合著过。
    **最硬的判别是 PD 窗口本身**——他 1925 年生，1931 年 6 岁，**窗口内不可能有他的东西**。
  - 语料 **5 份 / 50.7 万词**，全部 `writings` 道。
    **独著只占 31.79%**（只有 1922《Accounting Theory》一本），三本合著无分工说明。
  - ★★★ **声口在 `the writer` 不在 `I`**：全 5 份 498 个 `I` 逐个分类完，
    **属于他本人的 0 个**（罗马数字／页码讹字／数学变量 `I`／被引用的他人话语）。
    1922 那本 14 处 `the writer`，每处都在下判断。
  - **研究门错 8 → 3**，剩下的全是「语料不够广」：
    来源 5<8、覆盖 1 道<3、完成 0 道<3。**第二轮抓源已派出**（补 external / timeline
    ＋《The Accounting Review》1926–1931 他自己的文章）。
  - ★ 拿不到的两本已记坐标：1924《Accounting》894 页独著、1919 GPO 那本，
    **HathiTrust 是 PD 全视图而本机被 Cloudflare 挡住，没有尝试绕过**。
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
| **声明重复源**（先 dry-run） | `python3 scripts/declare_source_dedup.py <workspace>` |

★★★★ `declare_source_dedup.py` **默认只写「机械上确定」的那一类**
（去掉来源后缀后词干相同＝同一件的另一份副本）。
**其余只列出来给人读，不写。** 这不是保守，是实测：
Nightingale 465 对里**只有 48 对是确定的**，其余 417 对包含
`royal-commission-report-1858` ↔ `mortality-british-army-1858`（0.44）这种
**跨作品的真实重印**——皇家委员会报告收录了她的 Notes，两者确实大段相同，
**但不是同一部作品**，方向靠干净度猜必然出错。
★ Blackwell 61 对一次做完（全对）**是个例外，别当通例**。

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
| **★★★★ 教训库（101 条实测事故）** | `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/`，**入口是 `_索引.md`** |

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

### ★★★★ 处置有**三种**状态，三份机器可读的文件，别只看两份

| 状态 | 文件 | 现有条数 | 含义 |
|---|---|---:|---|
| 已入库 | `registry/codex/persona-distiller-group/team-index.json` 的 `products` | **101** | 做完并注册 |
| 延后／拒发 | `skill_log_evals/persona-distiller/_ledgers/_延后名单.json` | **137** | **我判的**：够不着门、材料不可得 |
| **受阻待裁** | `skill_log_evals/persona-distiller/_ledgers/_受阻待裁.json` | **3** | **我判不了的**：只能由用户拍板 |

★ **第三份是 2026-08-10 移交前才建的。** 在那之前这个状态**只活在会话的任务表里**，
而任务表不跟着仓走——核对时发现 Adams／Martens／Roberts-Austen 三人
**既不在名册也不在延后名单**，接手的人会把他们当成「从没碰过」。

★★ 用户裁定之后，把人**从受阻名单挪走**（入库进 team-index，判不做进延后名单），
**别让同一个人同时留在两处**。

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
   ★ **尤其是这条门正挡着你的时候。** 2026-08-10 实测过一次：
   `status: hypothesis` 被门当成 `pattern` 要 ≥2 处来源，
   而全库爆炸半径是 **2 条（都是我当轮刚写的）**——**改它安全，但不正当**，
   所以改了产物不改门，把问题记成待裁定 ㉝。
9. **★ 不是所有真缺陷都有判据形状的探测器。** 同一天两次：
   - 「某句是不是译者的编者话」——窗口共现上**事故句 60% ＞ 真段落 56%，顺序是反的**；
   - 「这份语料根本不是他的」——三把尺子（姓零命中 290 份 / P 档零命中 242 份 /
     文件名实词不在正文 86 份）**全被合理情形淹没**
     （Godin 的博客正文只写 `Seth's Blog` 不带姓，196/196 全零）。

   **两次都是靠「先缩到异常组，再读原文」查出来的**，不是靠全库扫。
   查不出来就**如实写「这一条没有判据兜底」**，别上线一个抓不到本案的判据。
10. **★ 比相似度之前先做负对照。** `difflib` 的 `quick_ratio` **只比字符多重集**：
    两本毫不相干的书给 **0.945**（真 ratio 0.012）。
    换 8 词片 Jaccard 也踩过一次——**按固定步长取片会因错位让逐字相同的两份得 0.000**，
    要按 `zlib.crc32(片) % k == 0` 取样（内建 `hash()` 带每进程随机种子，不能用）。
    **同一件事上量错三次，每次都是负对照或读命中挡回来的。**

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

### ★★ 这一推有多大（实测，2026-08-10）

| 项 | 值 |
|---|---|
| 待推送提交 | **870** |
| 仓内 pack | **835.94 MiB** |
| 已跟踪的语料文件 | **9,578** |
| **最大的单个已跟踪文件** | **18.1 MB**（`probe-adams-131/raw/whoswho1922_djvu.txt`） |

★ **没有文件超过 GitHub 的 100 MB 硬上限**，所以不会因为单文件被整推拒掉。

★★★★ **`git push --dry-run` 2026-08-10 实跑通过**（联了服务器，只是不更新 ref）：

```
To github.com:LinzeColin/AgentDatabase.git
 * [new branch]  claude/character-distillation-skill-reorganize-d57595 -> ...
```

**远端可达、凭据可用、分支会作为新分支建立、无任何拒绝。**
移交那晚照 §7 的三条命令走即可。
★★ 但这是一次**大推**（语料整个在库里），网络慢的时候会跑很久——
**移交那晚给它留时间，别掐掉。**
★★★ `git count-objects` 会报两条 `garbage found: …/worktrees/agentdb-nasmyth-153/info/sparse-checkout`
的警告——那是 worktree 的元数据，**与推送无关，不要去动它**。

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

### ★★★★ 教训库：**它原本不在仓里，接手方一条都读不到**

`_ledgers/_教训库/` 是 2026-08-10 移交前才复制进来的 **101 条实测教训**（约 468 KB）。
**原本存在上一任 agent 的私有存储 `~/.claude/projects/…/memory/` 下——
不在 GitHub 上。** 核对移交时才发现这个缺口。

- **入口是 `_索引.md`**：一行一条，带一句话钩子。
- **动手改判据之前先在索引里搜相关的词**——这个项目里判据第一版出错是常态，多半有人踩过。
- ★ **这是快照，不是活文档。** 里面提到的文件、字段、命令可能已经变了，
  引用到具体路径时**先去仓里确认它还在**。
- ★★ **移交那晚要重导一次**（本会话之后又攒了新的）：

  ```bash
  cp ~/.claude/projects/-Users-linzezhang-Documents-Codex-GithubProject-AgentDatabase/memory/*.md \
     CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/
  mv CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/MEMORY.md \
     CodexSkills/skill_log_evals/persona-distiller/_ledgers/_教训库/_索引.md
  ```

### 交接前还要做的

1. **`_scratch/agentdb-nasmyth-153` 这个 worktree 是我开的，得我收**：
   合并 → 关 PR → `git worktree remove` → 删分支 → `git gc`（**禁止 `--prune=now`**）。
2. **`_protected/` 永不上传**，交接时也不上传。
3. **Notion 全程没碰过**，按约定要等 600 人全完成。
