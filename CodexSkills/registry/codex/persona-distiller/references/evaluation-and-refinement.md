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
