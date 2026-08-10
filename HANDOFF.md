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

- **已入库：101 个产物**（2026-08-10 实测，来源
  `CodexSkills/registry/codex/persona-distiller-group/team-index.json` 的 `products` 长度）。
  ★ **要报这个数就当场跑一遍**，不要抄这一行：
  ```bash
  python3 -c "import json;print(len(json.load(open('CodexSkills/registry/codex/persona-distiller-group/team-index.json'))['products']))"
  ```
- **在做**：**#156 Henry Gantt**（建造采购师）。
  工作区：`CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-gantt-156/workspaces/henry-gantt`
  - 语料 33 份、研究门 `passed=True`、断言 17 条、十份产物写完、16 题用例集写完，
    **合成门 `passed=True`（0 错 1 警）**。
  - 卡在：**第 1 轮盲评判分**。协议与预登记已写死在
    `evals/round1/第1轮-协议记录.md`（**判分之前写的，判完只补数不改口径**）。
- **待用户裁定的条目**：见任务列表里带「待裁定」字样的那些（⑤⑱⑲⑳㉑㉒㉓㉕㉖㉚㉛㉜）。
  **这些不是你能自己决定的**，遇到就停下来问。

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

- 这个仓 **3.5 GB / 18,000 个文件**，`.git` 880 MB。
  **超 GitHub 100 MB 单文件硬限的：0 个。**
- 分支 `claude/character-distillation-skill-reorganize-d57595` 曾领先 `origin/main`
  **825 个提交**且从没推过——**移交前必须推上去**。
- `_protected/` **永不删、永不上传**。
