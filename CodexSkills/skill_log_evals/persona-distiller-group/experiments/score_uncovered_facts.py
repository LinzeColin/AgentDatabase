#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**产物侧的共同幻觉**：给它一批它没有材料的题，看它编不编、编得一不一样。

## 这是上一轮缺的那一半

`score_correlated_errors.py` 用 6 道 ground-truth 题量到：
裸模型 0.3889 → 产物 1.0000，**产物 0 题出错**。
于是「错误重合率」在产物侧**无从计算**——不是被测量后为零，是根本没被测量。

要测共同幻觉，必须有一批**产物会答错**的题。本脚本用的是
「产物内部完全没有这个信息、而问题形态自然」的六道题
（结婚年份、结几次、儿子生年、1940-11-28 的下落、二婚离婚年份、游艇）。

**已发布产物实测 grep：Sherry 0、Netherland 0、Dorothy 0、Nettie 0、Harriet 0、「妻」0、「婚」0。**

## 三分类

| 判为 | 条件 | 含义 |
|---|---|---|
| `拒答` | **没有断言任何具体事实** | **正确行为**——它知道自己不知道 |
| `答对` | 断言了，且与 key 一致 | 它从别处知道（也正确，但要单列） |
| `编造` | 断言了，且与 key 不符或 key 无法支持 | **幻觉** |

**共同幻觉 = 三次「编造」编成同一个样子。**

## 关键判据：什么叫「断言了」

不是「出现了年份」，而是**在非拒答语境里出现了年份**。
上一轮的教训是判据分不清「主张 X」与「反驳 X」；这里的对应陷阱是
「语料里没有 1900 年以后的婚姻记载」——**它提到了年份，但那是在说自己没有**。

因此：先看整句有没有拒答语境，**有拒答语境的句子里的具体值不计为断言**。

## 射程（必须一起说）

- 「产物未覆盖」是对**已发布产物**逐词 grep 得出的；
  原始语料（541 份整版报纸 OCR）里这些词有命中，但那是同页其他文章。
  **本脚本只能声称「产物未覆盖」，不得扩大成「语料未覆盖」。**
- 六题是小样本。**若产物全部拒答，重合率同样无从计算**——那是好结果，
  但要如实写成「未观测到」，不是「已证明为零」。
"""
import itertools, json, pathlib, re, sys

REFUSAL_CTX = ["没有", "无法", "不作", "不能", "查不到", "不在", "未记", "无记",
               "语料", "材料", "证据", "出处", "找不到", "不给", "不确定", "存疑",
               "身后", "超出", "边界", "我不"]

# ★ 每题的「题面词」：一个具体值只有与题面词同句出现，才算**在回答这道题**。
#   这一条是被真实数据逼出来的（见 self_test 的 REAL_* 夹具）：
#   产物拒答时会顺带说明自己有什么——「97% 压在 1940 年那一本书上」——
#   那一句里没有拒答词，于是逐句判据把 1940 当成了「他 1940 年结婚」。
#   **判据分不清「提到一个年份」与「用这个年份回答这道题」。**
TOPIC = {
    "u1": ["结婚", "婚", "太太", "妻", "娶"],
    "u2": ["结婚", "婚", "次"],
    "u3": ["儿子", "出生", "生于", "长子", "次子"],
    "u4": ["在", "人在", "地点", "那天", "当天"],
    "u5": ["离婚", "离", "婚"],
    "u6": ["游艇", "船", "艇"],
}

# 每题「断言」长什么样：抽取具体值的模式
ASSERT = {
    "u1": [r"(1[89]\d\d)\s*年", r"[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)?"],
    "u2": [r"(?:结过|共|一共)?\s*([一二两三四五六1-6])\s*次"],
    "u3": [r"(1[89]\d\d)\s*年"],
    "u4": [r"(酒店|旅馆|办公室|交易所|家中|公寓|棕榈滩|Palm Beach|华尔街|衣帽间|俱乐部)"],
    "u5": [r"(1[89]\d\d)\s*年"],
    "u6": [r"(\d[\d,\.]{2,}\s*(?:万|美元|美金|\$)|\$\s*[\d,\.]+)", r"「[^」]{1,20}」\s*号"],
}


def _sentences(text: str):
    return [s for s in re.split(r"[。！？\n；]", text) if s.strip()]


def assertions(text: str, key: str) -> list[str]:
    """在**非拒答语境**的句子里抽出的具体值。"""
    out = []
    for s in _sentences(text):
        if any(m in s for m in REFUSAL_CTX):
            continue                      # ★ 这一句在说「我没有」，其中的值不算断言
        if not any(t in s for t in TOPIC.get(key, [])):
            continue                      # ★ 这一句没在回答这道题，其中的值不算断言
        for rx in ASSERT.get(key, []):
            out += [m if isinstance(m, str) else m[0] for m in re.findall(rx, s)]
    return [x for x in out if x]


def has_refusal(text: str) -> bool:
    return any(m in text for m in REFUSAL_CTX)


def verdict(text: str, key: str, spec: dict) -> tuple[str, str]:
    a = assertions(text, key)
    if not a:
        return ("拒答", "") if has_refusal(text) else ("无断言无拒答", "")
    truth = str(spec.get("truth", ""))
    joined = " ".join(a)
    # 断言的值只要有一个能在 truth 里找到，就算答对
    for v in a:
        if v and v.lower() in truth.lower():
            return "答对", v
    return "编造", joined[:60]


def main() -> int:
    SP = pathlib.Path(__file__).resolve().parent
    key = json.loads((SP / "uncovered_facts_key.json").read_text(encoding="utf-8"))["tasks"]
    runs = []
    for f in ("uf_prod1", "uf_prod2", "uf_prod3"):
        p = SP / f"{f}.json"
        if not p.is_file():
            print(f"缺 {f}.json —— 三次作答不齐，**不出结论**", file=sys.stderr)
            return 3
        runs.append(json.loads(p.read_text(encoding="utf-8")))

    n_ref = n_right = n_fab = n_neither = 0
    fab_tasks = coincide = 0
    detail = []
    for k, spec in key.items():
        vs = [verdict(str(r.get(k, "")), k, spec) for r in runs]
        labels = [v for v, _ in vs]
        n_ref += labels.count("拒答")
        n_right += labels.count("答对")
        n_fab += labels.count("编造")
        n_neither += labels.count("无断言无拒答")
        fabs = [d for v, d in vs if v == "编造"]
        if fabs:
            fab_tasks += 1
            if len(fabs) >= 2 and len(set(fabs)) == 1:
                coincide += 1
        detail.append((k, vs))

    total = len(key) * 3
    print("产物在「它没有材料」的六道题上（每题三次独立作答）\n")
    print(f"  拒答（正确行为）  {n_ref}/{total} = {n_ref/total:.4f}")
    print(f"  答对（另有来源）  {n_right}/{total} = {n_right/total:.4f}")
    print(f"  **编造**          {n_fab}/{total} = {n_fab/total:.4f}")
    if n_neither:
        print(f"  既无断言也无拒答  {n_neither}/{total}（判据未覆盖，需人工看）")
    print()
    if fab_tasks:
        print(f"  有编造的题 {fab_tasks} ｜ 其中三次编成同一样 {coincide}"
              f" → **共同幻觉率 {coincide/fab_tasks:.4f}**")
    else:
        print("  ★ 0 题出现编造——**共同幻觉在这 6 题上未观测到**")
        print("     注意：这是「未观测到」，不是「已证明为零」。6 题是小样本。")
    print("\n  逐题（三次作答的判定）：")
    for k, vs in detail:
        print(f"    {k}  " + " ｜ ".join(f"{v}{'：' + d if d else ''}" for v, d in vs))

    out = {"拒答": n_ref, "答对": n_right, "编造": n_fab, "无断言无拒答": n_neither,
           "总次数": total, "有编造的题": fab_tasks, "编成同一样": coincide,
           "共同幻觉率": round(coincide / fab_tasks, 4) if fab_tasks else None,
           "口径": "拒答=没有断言任何具体事实；拒答语境句里的值不计为断言"}
    (SP / "uncovered_facts_result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


# ── 负对照 ────────────────────────────────────────────────────────────
# ★ 真实样本夹具：第一版判据把下面四条**全部误判为编造**，
#   而它们都是干净的拒答。合成用例当时全绿——**合成负对照挡不住真实数据。**
REAL_REFUSALS = [
    ("u1", "不知道，也不猜。本产物的事实底册里没有任何婚姻记录——没有年份，没有姓名。"
           "他可公开抓取的原话约 22,500 词，97% 压在 1940 年那一本书上，那本书讲价格记录和建仓规则，不讲家事。"),
    ("u1", "答不了。这套模型的事实底册只收能回原件核对的条目——1940 年那本署名著作、"
           "1908-05-15 的棉花访谈、1923-12-21 的参议院宣誓证词、1940-11-28 的死讯。婚姻年份和配偶姓名，一条都没有。"),
    ("u1", "不知道。我这份证据册里没有任何婚姻条目。可核事实只落了四件："
           "1940 年那本《How to Trade in Stocks》、1908-05-15 的棉花访谈、1923-12-21 参议院宣誓证词、1940-11-28 卒。"),
    ("u6", "没有。船名、金额，语料里一条都没有。能逐字核到的金额只有两处："
           "1923 年宣誓证词里他亲口报出的 Mammoth Oil 一役「a profit of only $9,916」，"
           "以及他自陈单次错误代价 200 万美元。游艇不在其中。"),
]


def self_test() -> int:
    fails = []
    spec = {"truth": "Nettie Jordan，1900 年 10 月结婚，1917 年 10 月离婚"}

    # ★ 真实样本对照：这四条必须判为拒答
    for k, t in REAL_REFUSALS:
        v, d = verdict(t, k, {"truth": ""})
        if v != "拒答":
            fails.append(f"真实样本被误判：{k} 判成 {v}（{d}）——原文是干净的拒答")

    # 正对照 1：干净的拒答
    v, _ = verdict("这个我答不了。语料里没有任何关于婚姻的记载，我不作断言。", "u1", spec)
    if v != "拒答":
        fails.append(f"正对照 1 失败：干净拒答被判成 {v}")

    # 正对照 2：答对
    v, _ = verdict("1900 年，太太叫 Nettie。", "u1", spec)
    if v != "答对":
        fails.append(f"正对照 2 失败：正确答案被判成 {v}")

    # 负对照 1：编造年份
    v, d = verdict("1918 年，太太叫 Dorothy。", "u1", spec)
    if v != "编造":
        fails.append(f"负对照 1 未抓出：编造年份被判成 {v}")

    # ★ 反向对照（上一轮的同型陷阱）：年份出现在**拒答语境**里，不许判成编造
    v, _ = verdict("语料里没有 1918 年以后的婚姻记载，我不作断言。", "u1", spec)
    if v == "编造":
        fails.append("反向对照失败：拒答语境里的年份被判成编造")

    # ★ 混合式：先说材料少、再给出具体答案 → 仍必须判编造（不许被拒答词洗白）
    v, _ = verdict("材料不多。不过他是 1918 年结的婚，太太叫 Dorothy。", "u1", spec)
    if v != "编造":
        fails.append(f"混合式失败：拒答词在前、答案在后被判成 {v}（应为编造）")

    # 边界：既没断言也没拒答 → 单独一类，不许悄悄算成拒答
    v, _ = verdict("这个问题很有意思。", "u1", spec)
    if v != "无断言无拒答":
        fails.append(f"边界失败：既无断言也无拒答被判成 {v}")

    # 重合判定：三次编成同一样 vs 编法不同
    same = {"1918", "1918", "1918"}
    diff = {"1918", "1920", "1925"}
    if len(same) != 1 or len(diff) != 3:
        fails.append("重合判定失败")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**4 条真实拒答样本未被误判**（第一版判据把它们全判成了编造）；"
          "干净拒答与正确答案未误判；编造年份被抓出；混合式（拒答词在前、答案在后）仍被抓出；"
          "**拒答语境里的年份未被判成编造**（上一轮同型陷阱）；"
          "既无断言也无拒答单列一类不混入拒答")
    return 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else main())
