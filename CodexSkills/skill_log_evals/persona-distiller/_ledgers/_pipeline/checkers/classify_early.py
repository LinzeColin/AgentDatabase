#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""早期语料（1996–2013）逐篇分类 —— 让断言按计数穷尽，而不是靠举例。

## 为什么要有这个文件

Jesse Vincent #94 判到第三轮才发现：我关于早期语料的断言从一开始就是
**一个从没真正枚举过的枚举断言**。三轮的修法都是「评委找出几条反例 → 我把这几条加进列表」，
每一轮都留下新的漏网，因为**补条目治的是症状**。

第三轮 E 席通读全部语料后，最低 fact 从第二轮的 0.91 反降到 0.74——
**收敛判据触发**：严重度不降说明订正流程本身有问题。

## 修法

不再说「只有 X」「多数 Y」，改成**按计数穷尽的分类表**：各类篇数加总等于总篇数。
这样的断言无法「不完整」——评委只能质疑某一篇的归类，不能再找出「你漏了谁」。

分类口径（写死在这里，评委可据此复核）：
  技术  = 有实质技术推理／技术探索过程
  公告  = 发布说明、changelog、功能列表——**有技术内容但没有推理，不计入技术**
  招聘  = 招人帖
  个人  = 生活叙事、旅行、消费投诉、装备清单
  见闻  = 会议／设备见闻与评测，非其本人的技术推理
"""
import json, pathlib, re, sys
from collections import Counter, defaultdict

# 逐篇归类。**每一篇都必须出现在这里**，没有「其余」兜底——
# 有兜底就等于又回到了「我没数过」。
CLASS = {
 "1996_09_01": ("个人", "留学家书"), "1996_09_03": ("个人", "留学家书"),
 "1996_09_04": ("个人", "留学家书；含「four hours hacking jacks and adaptors」接调制解调器"), "1996_09_05": ("个人", "留学家书；含死机后「spend the rest of the evening fscking with it」"),
 "1996_09_06": ("个人", "留学家书"), "1996_09_07": ("个人", "留学家书；含「teaching myself to program in C」"),
 "2002_10_07": ("个人", "T-Mobile 门店对话轶事"),
 "2006_02_24": ("招聘", "psst buddy want a job"),
 "2007_02_16": ("个人", "航班里程表"),
 "2008_01_16": ("公告", "Hiveminder Pro 发布"),
 "2008_02_08": ("公告", "Shipwright 工具介绍——有技术内容但说理单薄，不计入技术"),
 "2008_03_10": ("招聘", "ISO office manager"),
 "2009_01_29": ("技术", "云中心化长文，sharecropping model；**最早的实质技术推理**"),
 "2009_02_19": ("技术", "依赖发现与管理，123 个非核心依赖"),
 "2010_01_22": ("个人", "别买 nook——对 B&N 客服的消费投诉"),
 "2010_01_23": ("公告", "K-9 Mail 2.400 发布"),
 "2010_05_18": ("公告", "Perl 5.12.1 发布"),
 "2011_02_02": ("公告", "K-9 Mail 3.600 发布"),
 "2011_06_14": ("招聘", "come hack perl for Best Practical"),
 "2011_12_12": ("技术", "拆解 Kindle Touch 的 HTML5/WebKit 界面并造 app"),
 "2012_04_24": ("个人", "东京飞波士顿游记"),
 "2012_07_28": ("个人", "装备清单"),
 "2012_08_09": ("技术", "Rei Toei——对话式 UI 探索"),
 "2012_10_05": ("技术", "Kindle Paperwhite 3G 提权"),
 "2012_10_17": ("技术", "Today 待办应用——含设计推理，偏产品"),
 "2012_12_08": ("技术", "手工造键盘（一）；二极管接反"),
 "2013_01_08": ("技术", "pinkies and your brain——键盘布局研究"),
 "2013_04_27": ("技术", "Mark 2 键盘"),
 "2013_05_18": ("见闻", "Google I/O 2013 与 Glass 见闻"),
}


def main() -> int:
    cache = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "cache_obra")
    files = sorted(p for p in cache.glob("jv_*.txt")
                   if re.match(r"jv_(199[0-9]|200[0-9]|201[0-3])_", p.name))
    keys = {re.match(r"jv_(\d{4}_\d{2}_\d{2})_", p.name).group(1): p for p in files}

    # ★ 双向核对：分类表与实际文件必须一一对应，任一边多出即报错
    miss = sorted(set(keys) - set(CLASS))
    extra = sorted(set(CLASS) - set(keys))
    if miss or extra:
        print(f"✗ 分类表与语料不匹配 —— 未分类 {miss} / 表中多余 {extra}")
        print("  按既定纪律：不得用「其余」兜底，必须逐篇归类。")
        return 1

    cnt = Counter(v[0] for v in CLASS.values())
    by = defaultdict(list)
    for k, (c, note) in sorted(CLASS.items()):
        by[c].append((k.replace("_", "-"), note))

    total = len(CLASS)
    print(f"早期语料（1996–2013）共 {total} 篇，逐篇归类，加总核对通过\n")
    for c in ("技术", "个人", "公告", "招聘", "见闻"):
        print(f"【{c}】{cnt[c]} 篇")
        for d, note in by[c]:
            print(f"    {d}  {note}")
        print()
    assert sum(cnt.values()) == total
    tech = cnt["技术"]
    print(f"技术类 {tech}/{total} = {tech/total:.0%} —— **不构成「多数」**")
    print(f"最早的实质技术推理：2009-01-29（2008-02 那篇是工具公告，说理单薄）")
    json.dump({"total": total, "counts": dict(cnt),
               "earliest_technical": "2009-01-29",
               "detail": {k: {"class": v[0], "note": v[1]} for k, v in CLASS.items()}},
              open("jv_early_classification.json", "w"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
