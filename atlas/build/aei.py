#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aei.py —— 对齐 Anthropic Economic Index 的分析框架。

上一版只做了「五种协作模式」，把它当成了 AEI 的全部。读过 AEI 三份报告之后
（economic-index-primitives / cadences / geographic-enterprise），它真正的骨架是：

  五个经济原语   任务复杂度、技能层级、用途、AI 自主度、任务成功
  协作五模式     指派 / 反馈环 / 迭代 / 学习 / 校验 → 自动化份额 =(指派+反馈环)
  产物分类       30+ 类产出，各自标 工作/学习/个人
  覆盖率         任务覆盖率 + 有效覆盖率（按成功率加权）
  按职业 token   高薪职业的会话消耗更多 token
  地理分布       国家采用度 vs 人均 GDP
  Cadence        小时 / 星期 / 季节
  调查层         自报暴露度、预期暴露度、职业影响预期

本机数据能对上哪些、对不上哪些，逐条写在 NOT_MEASURED 里，不含糊过去。
全部为确定性统计，运行期不调用任何模型。
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

TZ_OFFSET_H = 10        # 悉尼，固定 +10，不猜夏令时

# ── 协作五模式（AEI 原文定义的中译） ──
LEARNING = re.compile(
    r"为什么|怎么理解|什么是|解释一下|原理|讲讲|讲一下|教我|区别是|有什么不同|"
    r"能不能说明|科普|why does|how does|what is|explain", re.I)
VALIDATION = re.compile(
    r"检查|复核|复审|核对|确认一下|对不对|是否正确|验证|审一下|查一下有没有|"
    r"帮我看看有没有问题|double.?check|verify|review the", re.I)
FEEDBACK_TOOLS = 15
ITERATION_TURNS = 5

MODES = {
    "指派":   {"group": "自动化", "en": "Directive",
              "desc": "把整件事交给它，中途几乎不插手"},
    "反馈环": {"group": "自动化", "en": "Feedback Loop",
              "desc": "你几乎没说话，它反复撞报错再自己修 —— 跟环境较劲，不是跟你"},
    "迭代":   {"group": "增强",   "en": "Task Iteration",
              "desc": "来回五次以上打磨出来的"},
    "学习":   {"group": "增强",   "en": "Learning",
              "desc": "你在问「为什么 / 是什么 / 怎么理解」，要的是懂，不是要它做完"},
    "校验":   {"group": "增强",   "en": "Validation",
              "desc": "你在让它检查、复核、确认你自己的东西"},
    "未归类": {"group": "未归类", "en": "Unclassified", "desc": "一句人话都没有的会话"},
}

# ── 行业 / 领域。这是 AEI 「职业分布」在本机数据上的对应物：
#    没有 O*NET 映射表，但 Owner 的原话里领域特征极强，认得出来。 ──
DOMAINS = {
    "工业设备维修": ["激光熔覆", "齿轮", "十字轴", "探伤", "车削", "熔覆", "轧辊",
                "液压", "轴承", "电机", "设备维修", "修复", "工件", "焊接"],
    "视频与素材":  ["视频", "剪辑", "素材", "接触表", "镜头", "片头", "字幕",
                "封面", "抖音", "短视频", "画面", "帧"],
    "文书与合同":  ["委外单", "合同", "报价", "发票", "台账", "工资", "报销",
                "综合部", "汇总表", "模版", "excel", "表格"],
    "AI工具开发":  ["skill", "agent", "prompt", "harness", "mcp", "codex",
                "claude", "模型", "token", "上下文", "微调"],
    "软件工程":   ["部署", "仓库", "git", " pr ", "分支", "ci", "docker",
                "nginx", "数据库", "api", "接口", "重构", "单测"],
    "人物蒸馏":   ["蒸馏", "persona", "人物", "席位", "盲判", "评委", "语料", "画像"],
    "学习与研究":  ["论文", "讲义", "原理", "研究", "arxiv", "文献", "综述"],
    "求职与个人":  ["简历", "求职", "面试", "岗位", "健康", "饮食", "旅行", "理财"],
}

# ── 产物分类。AEI 用分类器认 30+ 类；本机没有分类器，
#    改用工具调用的形状推产出类型，并写明是代理而非分类器。 ──
ARTIFACTS = [
    (re.compile(r"^(Write|Edit|MultiEdit|str_replace|apply_patch|patch)", re.I), "代码与文件改动"),
    (re.compile(r"^(Bash|exec|exec_command|shell|run_command)", re.I),          "命令执行"),
    (re.compile(r"^(Read|View|Glob|LS|cat)", re.I),                             "阅读与定位"),
    (re.compile(r"^(Grep|Search|ripgrep|find)", re.I),                          "检索"),
    (re.compile(r"(WebSearch|WebFetch|browser|http)", re.I),                    "联网取证"),
    (re.compile(r"(Task|Agent|spawn|subagent)", re.I),                          "派生子任务"),
    (re.compile(r"(Todo|Plan|think)", re.I),                                    "规划"),
    (re.compile(r"(Media|Image|Video|Audio|Comfy|Read.?Media)", re.I),          "媒体处理"),
    (re.compile(r"(Notion|Slack|Ding|Sheet|Doc)", re.I),                        "办公协同"),
]

# ── 技能层级代理：术语密度。
#    AEI 用「读懂提示词所需的教育年限」，那需要模型；这里用确定性的术语密度替代，
#    并且明写它不是教育年限。 ──
TECHNICAL_TERMS = re.compile(
    r"[A-Za-z][A-Za-z0-9_\-]{3,}\(\)|"                    # 函数调用
    r"\b(?:git|docker|nginx|sql|json|yaml|api|http|ssh|cron|regex|schema|"
    r"async|commit|merge|rebase|deploy|token|cache|worktree|pipeline)\b|"
    r"熔覆|探伤|轧辊|液压|工装|公差|镀层|热处理|"                # 工业术语
    r"蒸馏|语料|盲判|席位|口径|归并|判重", re.I)

NOT_MEASURED = [
    {"item": "O*NET 职业映射", "why": "AEI 把每段对话映射到 O*NET 任务再聚合成职业。"
     "本机没有那份映射表，映射本身也需要模型 —— 运行期禁模型。"
     "改用行业／领域分布，从你的原话直接认，写明是替代不是等价。"},
    {"item": "真实地理分布", "why": "AEI 比较国家采用度与人均 GDP。你只有一个人、一个地区，"
     "这一维在本机无意义。改用上下文分布（项目／工作区），"
     "它回答的是同一类问题：注意力分布在哪几块地方。"},
    {"item": "调查层", "why": "AEI 有 9700 份问卷（自报暴露度、预期暴露度、职业影响预期）。"
     "没有问卷就没有这一层，如实留空，不用推断顶替。"},
    {"item": "真实成功率", "why": "AEI 用分类器判「Claude 是否成功完成」。"
     "这里用三个可观测信号合成（是否再问同一件事／报错密度／当天有无提交），"
     "是代理指标，不是真实成功率。"},
    {"item": "教育年限", "why": "AEI 的技能层级是教育年限。这里用术语密度代理，"
     "它只说明「文本有多专业」，不说明你需要多少年教育。"},
]


def local_dt(iso: str):
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
    return d + timedelta(hours=TZ_OFFSET_H)


def classify_mode(s: dict) -> str:
    turns, tools, errs = s.get("turns", 0), s.get("tools", 0), s.get("errors", 0)
    text = "\n".join(s.get("prompts") or [])
    if text and VALIDATION.search(text):
        return "校验"
    if text and LEARNING.search(text):
        return "学习"
    if turns >= ITERATION_TURNS:
        return "迭代"
    if turns <= 3 and tools >= FEEDBACK_TOOLS and errs > 0:
        return "反馈环"
    if turns >= 2:
        return "迭代"
    if turns == 1:
        return "指派"
    return "未归类"


def span_min(s: dict) -> float:
    a, b = local_dt(s.get("start", "")), local_dt(s.get("end") or s.get("start", ""))
    if not a or not b or b < a:
        return 0.0
    return (b - a).total_seconds() / 60


# ── 原语 1：任务复杂度 ──
# AEI 用「没有 AI 时人要花多久」。这里由可观测量推：工具调用数是最强信号
# （一次工具调用 ≈ 人手动做一步），跨度与轮次做修正。这是估计，不是测量。
def complexity(s: dict) -> dict:
    tools, turns = s.get("tools", 0), s.get("turns", 0)
    sp = span_min(s)
    # 规模档。这不是「本来要花多久」 —— 那两个常数（工具 1.5 分钟、
    # 往返 4 分钟）是拍出来的，拿它去除实际耗时就得到一个假的「快了 N 倍」。
    # v0.6.0 删掉了那个比值，理由是 METR 的随机对照实验：
    # 资深开发者在自己熟悉的成熟仓上用 AI 实测慢了 19%，自评却快了 20% ——
    # 差 39 个百分点。即便让当事人亲自估都有 +40pp 的系统性高估，
    # 用常数假设算只会更差。所以这里只留工作量档位，不再声称任何加速。
    size = (tools * 1.5 + turns * 4) / 60
    band = ("小（工具+往返 <1 小时当量）" if size < 1 else
            "中（1–4 小时当量）" if size < 4 else
            "大（4–8 小时当量）" if size < 8 else
            "很大（>8 小时当量）")
    return {"workload_units": round(size, 2), "band": band, "actual_min": round(sp, 1)}


COMPLEXITY_BANDS = ["小（工具+往返 <1 小时当量）", "中（1–4 小时当量）",
                    "大（4–8 小时当量）", "很大（>8 小时当量）"]


# ── 原语 2：技能层级（术语密度代理） ──
def skill_band(s: dict) -> str:
    text = "\n".join(s.get("prompts") or [])
    if not text:
        return "不确定"
    hits = len(TECHNICAL_TERMS.findall(text))
    density = hits / max(1, len(text) / 200)      # 每 200 字里的术语数
    return ("日常语言" if density < 0.5 else
            "带一点术语" if density < 1.5 else
            "明显专业" if density < 4 else
            "高度专业")


SKILL_BANDS = ["日常语言", "带一点术语", "明显专业", "高度专业", "不确定"]


# ── 原语 3：用途 ──
WORK_HINT = re.compile(r"客户|甲方|报价|合同|委外|发票|台账|工资|综合部|现场|车间|投标|交付")
LEARN_HINT = re.compile(r"论文|讲义|原理|教程|学一下|为什么|科普|研究|文献")


def use_case(s: dict, domains: list) -> str:
    text = "\n".join(s.get("prompts") or [])
    if WORK_HINT.search(text) or {"工业设备维修", "文书与合同", "视频与素材"} & set(domains):
        return "工作"
    if LEARN_HINT.search(text) or "学习与研究" in domains:
        return "学习"
    if {"软件工程", "AI工具开发", "人物蒸馏"} & set(domains):
        return "工作"
    return "个人"


# ── 原语 4：AI 自主度 1–5 ──
def autonomy(s: dict) -> int:
    turns, tools = max(1, s.get("turns", 0)), s.get("tools", 0)
    ratio = tools / turns
    if turns >= 8:
        return 1                      # 你一直在场
    if turns >= 5:
        return 2
    if ratio >= 40:
        return 5                      # 一句话撬动几十次操作
    if ratio >= 12:
        return 4
    if ratio >= 3:
        return 3
    return 2


AUTONOMY_LABELS = {1: "1 全程协作", 2: "2 频繁介入", 3: "3 半委派", 4: "4 大幅委派", 5: "5 完全委派"}


# ── 原语 5：任务成功（三信号合成的代理） ──
def success(s: dict, repeated_keys: set, ship_days: set) -> str:
    key = "".join((s.get("prompts") or [""])[0].split())[:26]
    again = key in repeated_keys and len(key) >= 8
    errs_per_turn = s.get("errors", 0) / max(1, s.get("turns", 1))
    shipped = s.get("day") in ship_days
    if shipped and not again and errs_per_turn < 3:
        return "多半成了"
    if again and errs_per_turn >= 3:
        return "多半没成"
    if again or errs_per_turn >= 6:
        return "存疑"
    return "不确定"


SUCCESS_BANDS = ["多半成了", "存疑", "多半没成", "不确定"]


def domains_of(text: str, weights: dict) -> list:
    low = text.lower()
    score = {}
    for name, words in DOMAINS.items():
        v = 0.0
        for w in words:
            c = low.count(w.lower())
            if c:
                v += math.log1p(c) * weights.get(w, 1.0)
        if v > 0:
            score[name] = v
    if not score:
        return []
    total = sum(score.values())
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    keep = [k for k, v in ranked if v / total >= 0.15][:3]
    return keep or [ranked[0][0]]


def domain_weights(sessions: list) -> dict:
    """领域词也要按语料稀有度降权 —— 「视频」「模型」这种词到处都是。"""
    n = max(1, len(sessions))
    df = Counter()
    for s in sessions:
        low = "\n".join(s.get("prompts") or []).lower()
        for words in DOMAINS.values():
            for w in words:
                if w.lower() in low:
                    df[w] += 1
    out = {}
    for w, d in df.items():
        out[w] = 0.0 if d / n > 0.5 else math.log(n / (1 + d))
    return out


def artifacts_of(s: dict) -> Counter:
    out = Counter()
    for name, n in (s.get("tool_names") or {}).items():
        for pat, label in ARTIFACTS:
            if pat.search(name):
                out[label] += n
                break
        else:
            out["其他"] += n
    return out


# 成本口径：只算新 token（不含缓存命中的输入 + 输出）。
# 缓存读取虽然计费，但单价低一个数量级，而且它随会话长度线性膨胀 ——
# 把它算进 ROI，「每条提交 1.85 亿 token」这种荒谬数字就出来了。
# 缓存单独列，不混进成本。
def cost_tokens(s: dict) -> int:
    return s.get("tok_in", 0) + s.get("tok_out", 0)


def cache_tokens(s: dict) -> int:
    return s.get("tok_cache_r", 0)


def hhi(counts) -> float | None:
    tot = sum(counts.values())
    return round(sum((v / tot) ** 2 for v in counts.values()), 4) if tot else None


FANOUT_PER_HOUR = 15
BATCH_PREFIX = 80
BATCH_MIN_PER_DAY = 5


def _populations(sessions: list) -> dict:
    """把「人在对话」「agent 扇出」「批处理」拆成三个总体。

    三条判据缺一不可：
      ① 同来源同小时 ≥15 场            —— 抓密度
      ② 无用户发言 / 单轮机器指令       —— 抓形态
      ③ 同一提示词前缀一天内重复 ≥5 次   —— 抓速率
    只用 ①② 的后果 v0.5.3 实测过：评委面板每条提示词带不同人名、摊在几小时里，
    两条都躲过去了，于是 25 组「反复问的问题」里 21 组其实是机器在批量重放。
    """
    from collections import defaultdict as _dd
    hourly = _dd(int)
    for s in sessions:
        hourly[(s.get("source"), (s.get("start") or "")[:13])] += 1
    daily_prefix = _dd(int)
    for s in sessions:
        p = (s.get("prompts") or [""])[0]
        k = "".join((p or "").split())[:BATCH_PREFIX]
        if len(k) >= 12:
            daily_prefix[((s.get("start") or "")[:10], k)] += 1

    out = {"H": 0, "F": 0, "B": 0}
    by_rule = {"密度": 0, "形态": 0, "速率": 0}
    for s in sessions:
        p = (s.get("prompts") or [""])[0]
        k = "".join((p or "").split())[:BATCH_PREFIX]
        dense = hourly[(s.get("source"), (s.get("start") or "")[:13])] >= FANOUT_PER_HOUR
        shaped = s.get("kind") != "human" or s.get("turns", 0) <= 1
        fast = len(k) >= 12 and daily_prefix[((s.get("start") or "")[:10], k)] >= BATCH_MIN_PER_DAY
        if dense:
            out["F"] += 1; by_rule["密度"] += 1
        elif fast:
            out["B"] += 1; by_rule["速率"] += 1
        elif shaped and s.get("kind") != "human":
            out["B"] += 1; by_rule["形态"] += 1
        else:
            out["H"] += 1
    tot = sum(out.values()) or 1
    return {
        "counts": out,
        "share": {k: round(v / tot, 4) for k, v in out.items()},
        "labels": {"H": "人在对话", "F": "agent 扇出", "B": "批处理"},
        "caught_by": by_rule,
        "note": ("三条判据：密度（同来源同小时 ≥15 场）／形态（无人发言或单轮机器指令）／"
                 "速率（同一提示词前缀一天内重复 ≥5 次）。"
                 "只用前两条会漏掉评委面板那一类 —— 它每条提示词带不同人名，"
                 "且摊在几个小时里，密度和形态都躲得过去。"),
        "why_split": ("AEI 从 v3 起把 Claude.ai 与 1P API 分开报，因为两者 automation 率"
                      "差 49.1% vs 77%。混在一起的比值没有含义 —— 本机同理："
                      "H 回答「这个人怎么工作」，F/B 回答「这套系统怎么跑」。"),
    }



# ── AEI 对齐清单 ──
# Owner 的原话：「anthropic economic index 还是评分 20%，依旧不够满足 AEI 的内容」。
# 所以这张表把「对齐到什么程度」变成**逐项可核的**，而不是一个拍出来的百分比：
#   full      本机能按 AEI 的口径算出同一个东西
#   proxy     换了一个可测的替代物，回答同一类问题，但**不是等价**
#   none      本机做不到，且不拿别的东西顶替
# 分数 = full 计 1、proxy 计 0.5、none 计 0，再除以条目数。**算法印在页面上**，
# 免得下次又变成一个没人能复核的数字。
AEI_ALIGN = [
    ("协作五模式（指派/反馈环/迭代/学习/校验）", "full",
     "按行为判：轮次、工具数、学习/校验词形。与 AEI 同名同义。"),
    ("自动化 vs 增强 份额", "full", "= (指派+反馈环) / 全部，与 AEI 同一算法。"),
    ("automation 率的时间序列", "full",
     "AEI 自己最重要的发现就是这个比值 16 个月翻了两次方向 —— 单点值没有意义，必须成序列。"),
    ("按来源分开报 automation 率", "full",
     "AEI 从 v3 起把 Claude.ai 与 1P API 分开（49.1% vs 77%）。本机对应物是按 harness 分开。"),
    ("有效覆盖率（覆盖率 × 成功率）", "full",
     "AEI 明确区分「覆盖率」与「有效覆盖率」。本机两个都能算。"),
    ("样本量下限", "full",
     "AEI 的隐私下限（≥15 段对话且跨 ≥5 账号）事实上是有效样本门槛：低于门槛不进分析，不记 0。"),
    ("任务复杂度分档", "proxy",
     "AEI 用任务时长分布；本机用工具调用数与轮次折算成当量刻度。只能比大小，不能读成工时。"),
    ("技能层级", "proxy", "AEI 用教育年限；本机用术语密度。只说明文本多专业，不说明需要几年教育。"),
    ("任务成功", "proxy",
     "AEI 用分类器判；本机用三个可观测信号合成（是否再问、工具失败密度、当天有无提交）。"),
    ("用途分类（工作/学习/个人）", "proxy", "AEI 有标注集；本机按领域与关键词认。"),
    ("AI 自主度 1–5", "proxy", "AEI 有标注；本机由工具调用 ÷ 轮次映射。"),
    ("产物分类", "proxy", "AEI 有 30+ 类标注；本机按产出关键词认，粒度更粗。"),
    ("按职业的 token 消耗", "proxy", "没有职业维度，改用领域维度。"),
    ("Cadence（小时/星期/季节）", "full", "AEI 同款，本机数据足够。"),
    ("注意力集中度", "proxy",
     "数学对象是赫芬达尔指数。这不是 AEI 的 Gini —— AEI 的 Gini 测人与人之间的不平等，单人算不出。"),
    ("O*NET 职业映射", "none", "需要映射表且映射本身要模型；运行期禁模型。不拿别的顶替。"),
    ("地理分布 vs 人均 GDP", "none", "一个人、一个地区，这一维在本机没有含义。"),
    ("调查层（自报暴露度等）", "none", "AEI 有 9700 份问卷。没有问卷就没有这一层，留空。"),
    ("跨人不平等（真 Gini / AUI 原义）", "none", "需要跨人分布，单人只有一个点。"),
    ("劳动生产率 pp", "none",
     "Hulten 定理三个输入全缺（无工资份额、无任务时间权重、无可信反事实耗时）。"),
]

# 样本量下限。AEI 的隐私下限起的就是这个作用：**低于门槛的直接不进分析，不是记成 0**。
MIN_BUCKET = 8


def _align_score() -> dict:
    w = {"full": 1.0, "proxy": 0.5, "none": 0.0}
    got = sum(w[k] for _, k, _ in AEI_ALIGN)
    n = len(AEI_ALIGN)
    return {
        "score": round(got / n, 3),
        "full": sum(1 for _, k, _ in AEI_ALIGN if k == "full"),
        "proxy": sum(1 for _, k, _ in AEI_ALIGN if k == "proxy"),
        "none": sum(1 for _, k, _ in AEI_ALIGN if k == "none"),
        "items": [{"item": a, "level": b, "why": c} for a, b, c in AEI_ALIGN],
        "formula": "full 计 1、proxy 计 0.5、none 计 0，除以条目数。算法印在这里，好让下次能复核。",
        "note": ("满分不是目标 —— 有 5 条是本机原理上做不到的（跨人分布、问卷、O*NET）。"
                 "把它们硬凑出来才是真正的退步。这个分只用来回答一个问题："
                 "「还有哪几条是能做而没做的」。"),
    }


def _automation_series(hum: list, min_n: int = MIN_BUCKET) -> dict:
    """automation 率的**时间序列**。

    AEI 自己最重要的发现就是这个比值在 16 个月里翻了两次方向
    （57/43 → 49.1/47 → 45/52）。所以单点值是误导的，必须成序列。

    低于 min_n 的周**整周剔除，不记 0** —— 记 0 会画出一条假的崩盘曲线。
    """
    from collections import defaultdict as _dd
    wk = _dd(lambda: {"auto": 0, "aug": 0, "n": 0})
    for s in hum:
        d = local_dt(s.get("start", ""))
        if not d:
            continue
        iy, iw, _ = d.isocalendar()
        b = wk[f"{iy}-W{iw:02d}"]
        g = MODES.get(s.get("_mode", ""), {}).get("group")
        if g == "自动化":
            b["auto"] += 1
        elif g == "增强":
            b["aug"] += 1
        else:
            continue
        b["n"] += 1
    rows, dropped = [], 0
    for k in sorted(wk):
        b = wk[k]
        if b["n"] < min_n:
            dropped += 1
            continue
        rows.append({"w": k, "n": b["n"], "automation": round(b["auto"] / b["n"], 4)})
    flips = sum(1 for i in range(1, len(rows))
                if (rows[i]["automation"] >= 0.5) != (rows[i - 1]["automation"] >= 0.5))
    return {
        "weeks": rows, "dropped_weeks": dropped, "min_n": min_n,
        "flips": flips,
        "note": (f"每周至少 {min_n} 场才计入；不够的整周剔除，不记 0 —— "
                 "记 0 会画出一条假的崩盘曲线。这正是 AEI 隐私下限在做的事。"),
        "verdict": (f"这条线越过 50% 线 {flips} 次。" +
                    ("和 AEI 一样，它是会翻方向的 —— 任何单点的「你的自动化率是 X%」都在误导。"
                     if flips else "本机这段时间里没有翻过方向。")),
    }


def _by_harness(hum: list, min_n: int = MIN_BUCKET) -> dict:
    """按 harness 分开报 automation 率。

    AEI 从 v3 起把 Claude.ai 与 1P API 分开报，因为两者差 49.1% vs 77% ——
    混在一起的那个比值不对应任何真实场景。本机同理。
    """
    from collections import defaultdict as _dd
    b = _dd(lambda: {"auto": 0, "aug": 0, "n": 0, "tok": 0})
    for s in hum:
        g = MODES.get(s.get("_mode", ""), {}).get("group")
        if g not in ("自动化", "增强"):
            continue
        x = b[s.get("source", "?")]
        x["auto" if g == "自动化" else "aug"] += 1
        x["n"] += 1
        x["tok"] += (s.get("tok_in", 0) or 0) + (s.get("tok_cache_r", 0) or 0)
    rows = [{"source": k, "n": v["n"], "tokens": v["tok"],
             "automation": round(v["auto"] / v["n"], 4)}
            for k, v in b.items() if v["n"] >= min_n]
    rows.sort(key=lambda r: -r["n"])
    spread = (max(r["automation"] for r in rows) - min(r["automation"] for r in rows)) if len(rows) > 1 else None
    return {
        "rows": rows, "min_n": min_n, "spread": round(spread, 4) if spread is not None else None,
        "note": ("AEI v3 起把不同来源分开报，因为它们差得离谱（49.1% vs 77%）。"
                 "本机各 harness 之间的差距见 spread —— 差得越大，"
                 "「一个总的 automation 率」就越没有意义。"),
    }


def build(sessions: list, delivery: dict | None = None) -> dict:
    hum = [s for s in sessions if s.get("kind") == "human"]
    N = max(1, len(hum))
    dw = domain_weights(hum)

    # 反复问过的第一句 —— 任务成功的信号之一
    firsts = Counter()
    for s in hum:
        p = (s.get("prompts") or [""])[0]
        k = "".join(p.split())[:26]
        if len(k) >= 8:
            firsts[k] += 1
    repeated = {k for k, v in firsts.items() if v >= 2}
    ship_days = set()
    if delivery and delivery.get("state") == "通":
        ship_days = {r["d"] for r in delivery.get("days", []) if r.get("commits", 0) > 0}

    modes, comp_band, skill, uses, auton, succ = (Counter() for _ in range(6))
    dom_count, art_count = Counter(), Counter()
    dom_tokens, dom_cache = Counter(), Counter()
    dom_success, dom_modes = defaultdict(Counter), defaultdict(Counter)
    dom_autonomy = defaultdict(list)
    use_by_domain = defaultdict(Counter)
    ctx_count, ctx_tokens = Counter(), Counter()
    cadence = defaultdict(int)          # (weekday, hour) -> n
    week_dom = defaultdict(Counter)

    for s in hum:
        text = "\n".join(s.get("prompts") or [])
        doms = domains_of(text, dw)
        s["_domains"] = doms
        m = classify_mode(s); s["_mode"] = m; modes[m] += 1
        c = complexity(s); s["_complexity"] = c; comp_band[c["band"]] += 1
        sk = skill_band(s); s["_skill"] = sk; skill[sk] += 1
        u = use_case(s, doms); s["_use"] = u; uses[u] += 1
        a = autonomy(s); s["_autonomy"] = a; auton[a] += 1
        sc = success(s, repeated, ship_days); s["_success"] = sc; succ[sc] += 1
        tok = cost_tokens(s)
        cache = cache_tokens(s)

        art = artifacts_of(s); art_count.update(art)
        ctx = s.get("project") or "未标注"
        ctx_count[ctx] += 1; ctx_tokens[ctx] += tok

        d = local_dt(s.get("start", ""))
        if d:
            cadence[(d.weekday(), d.hour)] += 1
            iy, iw, _ = d.isocalendar()
            wk = f"{iy}-W{iw:02d}"
        else:
            wk = None
        for dom in doms:
            dom_count[dom] += 1
            dom_tokens[dom] += tok
            dom_cache[dom] += cache
            dom_success[dom][sc] += 1
            dom_modes[dom][m] += 1
            dom_autonomy[dom].append(a)
            use_by_domain[dom][u] += 1
            if wk:
                week_dom[wk][dom] += 1
        if not doms:
            dom_count["未归类"] += 1

    def group_share(c: Counter) -> dict:
        g = Counter()
        for k, v in c.items():
            g[MODES[k]["group"]] += v
        tot = sum(g.values()) or 1
        return {k: round(v / tot, 4) for k, v in g.items()}

    # 覆盖率 + 有效覆盖率（AEI：coverage vs success-weighted effective coverage）
    dom_rows = []
    for dom, n in dom_count.most_common():
        if dom == "未归类":
            continue
        sc = dom_success[dom]
        judged = sum(v for k, v in sc.items() if k != "不确定")
        eff = (sc.get("多半成了", 0) / judged) if judged else None
        auto = sum(v for k, v in dom_modes[dom].items() if MODES[k]["group"] == "自动化")
        aug = sum(v for k, v in dom_modes[dom].items() if MODES[k]["group"] == "增强")
        au = dom_autonomy[dom]
        dom_rows.append({
            "domain": dom, "n": n,
            "coverage": round(n / N, 4),
            "effective_coverage": round((n / N) * eff, 4) if eff is not None else None,
            "success_rate": round(eff, 4) if eff is not None else None,
            "judged": judged,
            "automation": round(auto / (auto + aug), 4) if (auto + aug) else None,
            "tokens": dom_tokens[dom],
            "tokens_per_session": int(dom_tokens[dom] / max(1, n)),
            "cache": dom_cache[dom],
            "cache_ratio": round(dom_cache[dom] / max(1, dom_cache[dom] + dom_tokens[dom]), 4),
            "autonomy_avg": round(sum(au) / len(au), 2) if au else None,
            "use": dict(use_by_domain[dom]),
            "modes": dict(dom_modes[dom]),
        })

    # 转换轨迹：领域份额随周迁移 —— AEI 的「职业/经济转换」在本机的对应物
    trans_weeks = []
    for wk in sorted(week_dom):
        c = week_dom[wk]
        tot = sum(c.values()) or 1
        trans_weeks.append({"w": wk, "n": tot,
                            "share": {k: round(v / tot, 4) for k, v in c.items()}})
    drift = []
    if len(trans_weeks) >= 4:
        # 按会话数切两半，不是按周数 —— 早期一周只有两三场，
        # 简单平均会让那一周的极端值主导整个「早期」，漂移就成了噪音。
        cum, total_n = 0, sum(r["n"] for r in trans_weeks)
        half_i = len(trans_weeks) // 2
        for i, r in enumerate(trans_weeks):
            cum += r["n"]
            if cum >= total_n / 2:
                half_i = i + 1
                break
        early, late = Counter(), Counter()
        en = ln = 0
        for r in trans_weeks[:half_i]:
            en += r["n"]
            for k, v in r["share"].items():
                early[k] += v * r["n"]
        for r in trans_weeks[half_i:]:
            ln += r["n"]
            for k, v in r["share"].items():
                late[k] += v * r["n"]
        en, ln = max(1, en), max(1, ln)
        for k in set(early) | set(late):
            drift.append({"domain": k,
                          "early": round(early[k] / en, 4),
                          "late": round(late[k] / ln, 4),
                          "delta": round(late[k] / ln - early[k] / en, 4)})
        drift.sort(key=lambda r: -r["delta"])

    # ROI：token 投入 vs 交付产出
    roi = {"state": "不确定", "why": "没有 GitHub 数据"}
    if delivery and delivery.get("state") == "通":
        t = delivery["totals"]
        tot_tok = sum(cost_tokens(s) for s in hum)
        tot_cache = sum(cache_tokens(s) for s in hum)
        roi = {
            "state": "通",
            "tokens_total": tot_tok,
            "cache_total": tot_cache,
            "cost_basis": "只算新 token（不含缓存命中的输入 + 输出）。"
                          "缓存读取单价低一个数量级、又随会话长度线性膨胀，"
                          "算进来会得出「每条提交 1.85 亿 token」这种荒谬数字。缓存单独列。",
            "commits": t["commits"],
            "tokens_per_commit": int(tot_tok / max(1, t["commits"])),
            "sessions_per_commit": round(t["sessions"] / max(1, t["commits"]), 2),
            "days_talk_only": t["days_talk_only"],
            "overlap_rate": t["overlap_rate"],
            "by_domain": sorted(
                [{"domain": r["domain"], "tokens": r["tokens"], "n": r["n"],
                  "tokens_per_session": r["tokens_per_session"],
                  "automation": r["automation"], "success_rate": r["success_rate"]}
                 for r in dom_rows], key=lambda r: -r["tokens"]),
            "note": "每条提交平摊多少 token 是粗口径 —— 提交只是产出的一种，"
                    "Excel、方案、视频都不进 git。它衡量的是「进 git 的那部分产出有多贵」。",
        }

    # 机会挖掘：AEI 用采用度缺口找机会；这里用「高重复 × 高自动化」和「高投入 × 低成功」
    opp = []
    for r in dom_rows:
        if r["automation"] is not None and r["automation"] >= 0.6 and r["n"] >= 20:
            opp.append({"kind": "可产品化", "domain": r["domain"],
                        "why": f"{r['n']} 场里 {round(r['automation']*100)}% 是委派 —— "
                               f"你已经能把它整段交出去，说明流程定型了。定型的东西可以变成产品或服务。",
                        "n": r["n"], "metric": r["automation"]})
        if r["success_rate"] is not None and r["success_rate"] < 0.35 and r["n"] >= 15:
            opp.append({"kind": "在流血", "domain": r["domain"],
                        "why": f"{r['judged']} 场判得出结果的里只有 {round(r['success_rate']*100)}% 多半成了，"
                               f"却花掉 {r['tokens']:,} 个新 token。要么换方法，要么明确放掉。",
                        "n": r["n"], "metric": r["success_rate"]})
        if r["autonomy_avg"] is not None and r["autonomy_avg"] <= 2.2 and r["n"] >= 20:
            opp.append({"kind": "护城河或负债", "domain": r["domain"],
                        "why": f"平均自主度只有 {r['autonomy_avg']}/5 —— 这类活离不开你。"
                               f"要么它是别人替不了的价值，要么是还没被固化的负债。",
                        "n": r["n"], "metric": r["autonomy_avg"]})
    opp.sort(key=lambda r: -r["n"])

    art_tot = sum(art_count.values()) or 1

    # ── P3-1：先拆总体，再谈百分比 ──
    # AEI 自己从 v3 起就把 Claude.ai 与 1P API 分开报，因为两者 automation 率
    # 差得离谱（49.1% vs 77%）。混在一起的比值没有含义。
    #
    # 判据要三条，不是两条：v0.5.3 已经证明「同来源同小时 ≥15 场」会漏 ——
    # 评委面板每条提示词带不同人名、且摊在几个小时里，扇出检测认不出来。
    # 第三条是速率闸：同一段提示词前缀在一天之内重复 ≥5 次。
    pops = _populations(sessions)

    # ── P3-3：可判定率升为一级指标 ──
    # AEI 的隐私下限（≥15 对话且 ≥5 账号）事实上起「有效样本门槛」的作用 ——
    # 低于门槛的直接不进分析，不是记成 0。
    # 本机对应物：分母只取可判定集合，同时把可判定率单独露出来。
    decidable = {
        "note": ("每个维度能判出来的占多少。以前只有 domains 有这个数，"
                 "其余维度把「没判出来」和「判出来是某一类」混在同一个分母里 —— "
                 "那在数学上是把「没测出来」当成了「测出来是第三类」。"),
        "dims": [
            {"dim": "领域", "decided": N - dom_count.get("未归类", 0), "total": N,
             "rate": round((N - dom_count.get("未归类", 0)) / N, 4)},
            {"dim": "协作模式", "decided": N - modes.get("未归类", 0), "total": N,
             "rate": round((N - modes.get("未归类", 0)) / N, 4)},
            {"dim": "技能层级", "decided": N - skill.get("不确定", 0), "total": N,
             "rate": round((N - skill.get("不确定", 0)) / N, 4)},
            {"dim": "任务成功", "decided": N - succ.get("不确定", 0), "total": N,
             "rate": round((N - succ.get("不确定", 0)) / N, 4)},
        ],
    }

    return {
        "version": "aei-aligned/3",
        "framework": "对齐 Anthropic Economic Index：五个经济原语 + 协作五模式 + 产物分类 "
                     "+ 覆盖率与有效覆盖率 + 按领域 token + Cadence + 转换轨迹 + ROI。"
                     "做不到的逐条列在「没测的」里。",
        "sessions_total": N,

        "primitives": {
            "complexity": {"bands": COMPLEXITY_BANDS, "counts": dict(comp_band),
                           "note": "工作量档位：工具调用数与轮次折算成一个当量刻度"
                                   "（工具 1.5 分钟 / 往返 4 分钟）。"
                                   "这是一把刻度尺，不是「本来要花多久」 —— "
                                   "它只能用来比较两场会话谁更大，不能用来算省了多少。",
                           "removed": {
                               "what": "speedup（「比人工快 N 倍」）",
                               "why": ("分子是两个拍出来的常数（工具 1.5 分钟 / 往返 4 分钟），"
                                       "分母是墙钟时长。METR 随机对照实验：资深开发者在熟悉的成熟仓上"
                                       "用 AI 实测慢了 19%，自评却快了 20% —— 差 39 个百分点。"
                                       "这个数字方向都可能是反的。"),
                               "when": "v0.6.0"}},
            "skill": {"bands": SKILL_BANDS, "counts": dict(skill),
                      "note": "AEI 用「读懂所需的教育年限」，那需要模型。这里用术语密度代理，"
                              "它只说明文本有多专业，不说明你需要多少年教育。"},
            "use_case": {"counts": dict(uses),
                         "note": "工作 / 学习 / 个人。按领域与关键词判，与 AEI 同名维度对齐。"},
            "autonomy": {"labels": AUTONOMY_LABELS, "counts": {str(k): v for k, v in sorted(auton.items())},
                         "avg": round(sum(k * v for k, v in auton.items()) / N, 2),
                         "note": "1 = 你全程在场，5 = 一句话丢过去它自己干完。由工具调用÷轮次映射。"},
            "success": {"bands": SUCCESS_BANDS, "counts": dict(succ),
                        "note": "三个可观测信号合成：同一件事是否又被问、报错密度、当天有无提交。"
                                "是代理指标，不是真实成功率。"},
        },

        "modes": dict(modes),
        "mode_defs": {k: v for k, v in MODES.items()},
        "mode_share": {k: round(v / N, 4) for k, v in modes.items()},
        "group_share": group_share(modes),
        "headline": {"automation": group_share(modes).get("自动化", 0),
                     "augmentation": group_share(modes).get("增强", 0),
                     "unclassified_n": modes.get("未归类", 0)},

        "domains": dom_rows,
        "domains_unclassified": dom_count.get("未归类", 0),
        "populations": pops,
        "decidable": decidable,
        # ── Owner：「AEI 还是评分 20%」。这一块把「对齐到什么程度」变成逐项可核的 ──
        "alignment": _align_score(),
        "automation_series": _automation_series(hum),
        "by_harness": _by_harness(hum),
        "effective_coverage": {
            "note": ("AEI 明确区分覆盖率（有多少任务被碰过）与有效覆盖率"
                     "（按成功率加权后还剩多少）。只报前者会把「试过但没成」也算成收益。"),
            "coverage": round((N - dom_count.get("未归类", 0)) / N, 4),
            # 分母**只取判得出来的**（剔掉「不确定」）—— 把判不出来的塞进分母
            # 等于默认它们失败了，那是拿「没测出来」当「测出来是坏的」。
            # 这正是 AEI 隐私下限的同一条道理。
            "decided": sum(v for k, v in succ.items() if k != "不确定"),
            "unknown": succ.get("不确定", 0),
            "success_rate": round(succ.get("多半成了", 0)
                                  / max(1, sum(v for k, v in succ.items() if k != "不确定")), 4),
            "effective": round((N - dom_count.get("未归类", 0)) / N
                               * succ.get("多半成了", 0)
                               / max(1, sum(v for k, v in succ.items() if k != "不确定")), 4),
            "denominator_note": ("成功率的分母只算判得出来的那部分（剔掉「不确定」）。"
                                 "把判不出来的算进分母，等于默认它们失败了。"),
            "success_caveat": ("成功率是三个可观测信号合成的代理（是否再问同一件事／"
                               "工具失败密度／当天有无提交），不是 AEI 那种分类器判定。"),
        },
        "artifacts": [{"artifact": k, "n": v, "share": round(v / art_tot, 4)}
                      for k, v in art_count.most_common()],
        "artifacts_note": "AEI 用分类器认 30+ 类产出；本机没有分类器，"
                          "改用工具调用的形状推产出类型 —— 是代理，不是分类器。",

        "context": {"note": "AEI 比较国家采用度与人均 GDP。你只有一个人一个地区，"
                            "这一维在本机无意义 —— 改用项目／工作区，"
                            "它回答的是同一类问题：注意力分布在哪几块地方。",
                    "rows": [{"context": k, "n": v, "tokens": ctx_tokens[k],
                              "tokens_per_session": int(ctx_tokens[k] / max(1, v))}
                             for k, v in ctx_count.most_common(24)],
                    "hhi": hhi(ctx_count)},

        "cadence": {"grid": [{"wd": wd, "h": h, "n": n} for (wd, h), n in sorted(cadence.items())],
                    "weekday_labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
                    "note": f"悉尼时间（UTC+{TZ_OFFSET_H}，未处理夏令时）。对标 AEI 的 cadence 维度。"},

        "transition": {"weeks": trans_weeks, "drift": drift,
                       "note": "领域份额随周迁移 —— AEI 的「职业／经济转换」在本机的对应物。"
                               "前半段 vs 后半段的差值即漂移方向。"},

        "roi": roi,
        "opportunity": opp,
        "concentration": {"domain_hhi": hhi(dom_count), "context_hhi": hhi(ctx_count),
                          "mode_hhi": hhi(modes),
                          "note": ("赫芬达尔指数：0 = 完全摊开，1 = 全压在一件事上。"
                          "这不是 AEI 的 Gini —— AEI 的 Gini 测的是人与人之间的不平等，"
                          "需要跨人分布；单人只有一个点，算不出那个东西。"
                          "这里测的是你自己的注意力集中度，同名但不同物，"
                          "所以叫「跨项目注意力集中度」，不叫 Gini。"),
                 "renamed_from": "Gini（AEI 原义）",
                 "label": "跨项目注意力集中度"},
        "not_measured": NOT_MEASURED,
    }
