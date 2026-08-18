# 「88% 只坐 1 个人」是**标签的产物** —— 换成任务口吻后 `single_expert` **一次也没被选中**（2026-08-18）

## 这是本会话被反复标注为「没量过」的那一个数，现在量了

`check_mode_ladder_reachable.py` 的 docstring 一直写着：

> 「下面的『N% 只坐 1 人』说的是**标签**，**不能读成用户用起来如此** —— 那个数没量过。」

它同时留了 `--tasks` 插座「留给真实用户提问」。仓里现成有 **72 道 TaskPack oracle**
（`_pipeline/benchmarks/development-48.jsonl` + `regression-24.jsonl`，**任务口吻、平均 64 字、
判据自己会印两份 sha256、且注明「从 TaskPack 原样复制，不是我编的」**）。
本轮把它们导出成一份 json 喂进那个插座。

## 结果：**头两条结论被推翻，第三条被坐实**

| | 名册标签 60 条（名词短语，33 字） | **72 道 oracle（任务口吻，64 字）** |
|---|---:|---:|
| `single_expert` | **53（88%）** | **0** |
| `small_team` | 7 | **54（75%）** |
| `deep_team` | **0** | **18（25%）** |
| `swarm` | 0 | **0** |

**① 「一个团队 skill 在 88% 的任务上只坐 1 个人」——** 那是**标签**的产物。
换成任务口吻，`single_expert` **一次也没被选中**。
**② 「deep_team 结构性不可达」——** 不成立。真任务上 **18/72 = 25%** 到达，靠 `complexity ≥ 0.76`。
**③ 「swarm 结构性不可达」——** **两份样本都坐实**：`parallelizability` 最大 **0.665 < 门 0.72**。
　★ 这与那条**照着 swarm 的门写的**验收题面读数**完全相同**（也是 0.665）——
　　三处独立样本给出同一个上界，**swarm 够不到是真的**。

## 逐触发的对照（同一张表，两份样本）

| 触发 | 门槛 | 标签上最大 | **真任务上最大** | 真任务命中 |
|---|---:|---:|---:|---:|
| small_team `complexity` | 0.38 | 0.494 | **0.872** | **72/72** |
| small_team `domains≥2` | 2 | 4 | 4 | **42/72** |
| small_team `risk` | 0.36 | 0.270 | **0.460** | 6/72 |
| deep_team `complexity` | 0.76 | 0.494 | **0.872** | **18/72** |
| deep_team `risk` | 0.72 | 0.270 | 0.460 | **0/72** |
| deep_team `domains≥5` | 5 | 4 | 4 | **0/72** |
| swarm `parallelizability` | 0.72 | 0.275 | 0.665 | **0/72** |

⇒ **`complexity` 才是真任务上唯一在起作用的触发**（标签上它只命中 6/60）。
  `risk` 与 `domains≥5` 在两份样本上都够不到；`swarm` 同理。

## `risk` 与 `parallel` 的词表召回也换了面貌（但结论不变）

    HIGH_RISK  18 个词｜有过命中 **3** 个｜每条命中数 {0:60, 1:6, **2:6**}（门槛需 2）
      ⇒ 真任务上**终于有 6 条命中够 2 个**（标签上是 0 条）——
        但它们的 `risk` 只到 0.460，**仍够不到 deep_team 的 0.72**。
    PARALLEL   14 个词｜有过命中 **4** 个｜每条命中数 {0:60, 1:6, **3:6**}（门槛需 4）
      ⇒ 最好的一条命中 **3 个**（竞品/矩阵/并行/批量），**仍差 1 个**。

★ 命中上下文逐条印了，不是只看计数：`法律`/`财务`/`安全` 各 6 次都在
「处理涉及财务、法律、运营和技术的**高风险**决策」这一句里 —— **真命中**，不是子串事故。

## ★★ 这条同时订正了域分类器那一段

标签上 `general-decision`（兜底档）占 **33/67 = 49.3%**；
**真任务上 72 条里兜底档一次都没出现**，`research-education` 占 72 次（50%）。
⇒ 「过半任务没被认成任何专业域」**也是标签的产物**。

## 我该怎么说这件事

**不是「先前的结论错了」，是「先前的结论只对标签成立，而它一直这么写着」。**
判据的 docstring 从建成起就带着那句射程话，`--tasks` 插座也一直留着 ——
**缺的只是有人把仓里现成的 72 条喂进去。** 本轮补上。
[[samples-cannot-support-universal-claims]]｜[[the-eval-covers-exactly-what-was-tuned]]｜[[we-need-X-is-a-hypothesis-until-you-fetch-an-X]]

★ 仍然要说清的射程：**这 72 条也不是真实用户提问**，是任务包作者写的 oracle
。★★ **订正（同日稍晚）**：**72 条 = 12 个独立题面 × 6 个变体**；且 `development-48` 与 `regression-24` **共用同一批 12 个题面** ⇒ `regression-24` **不是独立的第二份样本** —— 原文写的「3 个变体 / 24 个题面」**两个数都错**。
**真实提问的分布依然没有量过。**

## 可复算

```bash
# 导出 72 条
python3 - <<'PY'
import json, pathlib
B = pathlib.Path('CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/benchmarks')
out = [json.loads(l)["task"] for n in ("development-48","regression-24")
       for l in (B/(n+'.jsonl')).read_text(encoding='utf-8').splitlines() if l.strip()]
pathlib.Path('/tmp/bench72.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
print(len(out))
PY

cd CodexSkills/registry/codex/persona-distiller-group
python3 scripts/check_mode_ladder_reachable.py --tasks /tmp/bench72.json --limit 72
# 期望：small_team 54｜deep_team 18｜single_expert 0｜swarm 0
```

[[samples-cannot-support-universal-claims]]｜[[changing-the-sampling-unit-changes-the-ruler]]｜[[a-verdict-whose-scope-exceeds-its-inputs]]｜[[zero-hit-gates-must-prove-they-can-hit]]
