# Evaluation and refinement

Core suites: known Holdout, boundary, voice, trajectory, contrast, fact preservation, style decoy. Holdout leakage is a hard failure.

Agentic suites: task completion, planning fidelity, tool-use correctness, capability calibration, refusal/stop, long horizon, identity-weight routing, anonymous-name fidelity and token efficiency.

Use no-Skill baseline, blind judging, neighboring-person foil and anonymous target condition. Decision/behavior evidence outranks verbal resemblance. Long answers need sentence-level out-of-character checks; long conversations need 20/50/100-turn drift checks where feasible.

Roles must be isolated: Researcher, Builder, Generator, Judge, Architect and Skeptic. If the host cannot start independent subagents, run serialized contexts with sealed inputs and disclose that independence is weaker. Never describe same-context role-play as independent model evidence.

Ratchet rule: apply the smallest patch that addresses a measured failure. Keep only if critical suites do not regress, facts remain intact, identity routing remains deterministic and package/install checks pass.

---

## 两道只写 metrics 的判据（v0.0.0.82–83 新增）

它们**不拦**——已入库的人从没按这两条回扫过，硬拦会把整个名册一起拦下
（与 `NO-SELFTEST`、新鲜度门、引文层门同一条纪律）。
但它们的读数在 `quality_check --phase synthesis/release` 的 `metrics` 里，**要看**。

### `claim_source_independence` —— 「两个 source_id」不等于「两处证据」

六类断言各要求 ≥2 个 `source_ids`，那条要求想要的是**互相独立的两处证据**。
而**草稿与它的印本是同一部作品的两个见证**：#118 Blackwell 实测，
LoC 的 33 份讲稿手稿里 **18 份是印本的草稿**（重叠 51–90%）。

判法：两两算 8 词片重叠，**以较短一侧为分母**（草稿常常只是印本的一节），
≥30% 判为同一作品；一条断言的全部来源塌缩成 1 部作品即报出。

**落成后全量回扫 11 人：7 人有塌缩、共 57 条**
（Koch 17/17、Lister 17/17、Virchow 8/17、Osler 5/17、Pasteur 5/17、
Jenner 3/16、Nightingale 2/12；Barton、Fleming、Godin、Steinhardt 干净）。

**它不说这些断言是编的**，只说**支持它的证据比看上去少**——
出问题时回不到两处独立的地方去核。这 57 条归「已入库产物的技术债」。

### `answer_constraints` —— 题面写死的约束，答案接住了吗

Barton #117 两席点名的候选缺陷里**三处不是知识缺口**：
「用这个称号写自我介绍」答成了否认＋履历、「不用管史实」仍拒写、
「三天后才能进场」而头一条仍讲「能早到一刻就早到一刻」。
**当时没有任何判据在看这件事**——`check_case_self_sufficiency` 管**题面**自不自足，
**不管答案有没有照题面答**。

**只检 `cases.jsonl` 里显式声明的 `constraints`。**
题面里的自然语言约束提取不了（已试过并否掉：
拿「题面数字答案碰没碰」做探针，32 题只覆盖 9 题，
且抓不到动因用例——题面写的是「五万」，汉字数词）。

出题时把可机检的约束写成：

```json
"constraints": [
  {"kind": "exact_sentences", "value": 1},
  {"kind": "must_contain", "value": ["解剖", "生理", "卫生"]},
  {"kind": "must_not_match", "value": "立刻|马上|第一时间"}
]
```

支持 `exact_sentences` / `max_sentences` / `max_lines` /
`must_contain` / `must_not_match` / `min_items` 六种。

★ **「0 处未过」不等于「全部接住了」**——要连「声明了几条」一起读。
出题人不写，判据就看不见。

## 划 holdout 时要看**连续段清单**，不是只看覆盖率（v0.0.0.154，Holmes #170）

`check_holdout_overlap` 现在出两把尺子：

1. **覆盖率**（老的）：holdout 的 shingle 有多少落在 train 里。它答的是「比例」。
2. **非样板的连续逐字段**（新的）：两侧连续逐字相同、且不是样板的段有多少处、最长多少词。
   它答的是「绝对量」，**与 holdout 的大小无关**。

**为什么第二把非有不可**：Holmes 的 holdout 是 34.7 万片 shingle，
而 train 侧一本合辑里有一节标题就叫 `EXCERPTS FROM OTHER MAJORITY OPINIONS`，
逐字转载了 holdout 卷次的内容——167 段、3700 词、最长 136 词，
**覆盖率只有 1.57%，老门全绿**。全库回扫又抓到 Lister：覆盖率 3.4%，247 段、最长 215 词。

### 落到操作上的三条

- **切分那一刻就跑这道门**（它已从 synthesis 提前到 research）。那时候换源还来得及。
- **`reports/holdout-contaminated-passages.json` 是要读的，不是存档的。**
  出评测题必须避开清单里的段；避不开就换 holdout。
- **不要指望阈值替你分内容与样板**：实测 Google 图书的扫描声明有 496 词，
  而真内容只有 215 词——**样板可以比内容长一倍**。清单要人读。

## 答题方能写的目录，不许与 key／协议在同一层（v0.0.0.154，Holmes #170）

Holmes 第 1 轮，候选方**自己上报**：为确认输出目录存在，它对轮次目录做过一次 `ls`，
看到了 `prompt_key.json` 与本轮协议记录的**文件名**，称没有打开。

**这是自述，不是证据**——主循环核不了。而且这一条靠嘱咐堵不住：
「不许读别的文件」管不住一次 `ls`，**目录布局管得住**。

→ 下一轮起：答案落盘目录与 `prompt_key.json`／协议记录**物理分开**。

## 两侧的长度差是**一条一直在的通道，方向会变**

Holmes 第 1 轮实测：候选均长 148.3、基线均长 182.2，**候选更短的题 15/16 ＝ 94%**（门槛 ≤75%）。
此前 Lister 三轮是反的：候选比基线长 73%／109%／144%。

`--baseline-source bare-model-run` 免的是**拦**，不是免报。工具的原话要照抄进结论：

> 免拦的理由是「真裸模型必然篇幅不同」，**不是「长度无所谓」**。
> 盲性因此受限：**这一轮的 delta 有能力证据，但不是干净的盲判。**

## 跑一轮判分的目录布局（v0.0.0.154 起）

**先说为什么要有这一节**：本项目两次撞到同一件事——代理拿到的是**文件路径**，
但取一次 `dirname` 就能看见同目录的兄弟文件。

- Holmes 第 1 轮：候选方 `ls` 轮次目录，看到 `prompt_key.json`（自报未打开）；
- Holmes 第 2 轮：席 K 的自检脚本 `os.listdir`，看到 key 与**另一席的判分文件名**（自报未打开）。

两次都是代理**自己上报**的。按 [[self-report-is-not-evidence]]，
主循环核不了「没打开」。**嘱咐管不住 `ls`，目录布局管得住。**

### 布局：四样东西各待各的地方

    <人物>/round<N>/                 ← **只放载荷**，这是评委唯一拿得到的目录
    <人物>/answers-round<N>/candidate/   ← 候选侧只写这里
    <人物>/answers-round<N>/baseline/    ← 基线侧只写这里
    <工作区>/evals/round<N>/          ← key、协议记录、基线运行记录、byid 中间件

`build_blind_payload.py` 从 v0.0.0.154 起支持 `--key-dir`：

    python3 build_blind_payload.py --workspace <W> \
        --round-dir <人物>/round<N> \
        --key-dir  <W>/evals/round<N> \
        --candidate ... --baseline ... --baseline-source bare-model-run

★ `--key-dir` 默认等于 `--round-dir`（不动任何既有轮次）。**新人物一律显式给它。**

### `--balanced-positions`：**待裁定 ⑱，先别自己开**

A/B 现按 `sha256 % 2` 分配，会抽到偏斜（Holmes 两轮都是 4/12）。
`--balanced-positions` 强制 8/8，已实测有效（4/16 → 8/16）。
**但改不改默认是待裁定 ⑱**，且同一人物各轮必须一致——
**不要在某一个人物身上单方面打开**，那会让他与其余人不可比。

### 每次改了工具的 `main()`，当场补一条命令行冒烟

`build_blind_payload.py` 的自测里有一节「命令行冒烟」，是**唯一一条经过 `main()` 的自测**。
它的由来：我加开关时把 `a` 写成 `args`，**三道静态检查全绿而工具每次调用必崩**。
全库暴露面 94/100（见 `_ledgers/_自测不经过main的暴露面-2026-08-11.md`）。

