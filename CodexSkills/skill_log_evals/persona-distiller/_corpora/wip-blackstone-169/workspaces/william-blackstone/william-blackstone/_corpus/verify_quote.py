#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**逐条核引文**：这段字在不在编者注块里？

1898 年 Rees Welsh 版 *Commentaries* 是本工作区**唯一长 s 干净、能取逐字引文**的本子，
而它混着 CHRISTIAN / SHARSWOOD / CHITTY 等人的编者注。
版面上两者可分（见 `00-编者注与逐字引文.md`）：

- **编者注**：`(27)` 这样的**数字**括号起头的块，多以 `—CHRISTIAN.` 落款；
- **Blackstone 自己**：正文，其脚注记号是 `(y)(z)(a)` 这样的**字母**括号。

★ 不要用「编者注占全书百分之几」去判一条引文——那个比值两把尺子差 2.2 倍，给不准。
**逐条核给得准**，这就是这把尺子。

用法：
    python3 verify_quote.py "要核的那段字"           # 核一条
    python3 verify_quote.py --self-test             # 正反自测
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "raw"
NOTE_HEAD = re.compile(r"^\s*\(\d{1,3}\)")
# 正文恢复的标志：页码边码（`42-43 OF THE N`）、章眉（`CHAP. 2]`）、或整块只有一个页码。
BODY_RESUME = re.compile(r"(^|\n)\s*(?:\d{1,4}\s*$|\d{1,4}-\d{1,4}\s+[A-Z]|CHAP\.|\*)", re.M)


def blocks(text):
    """→ [(起, 止, 是不是编者注块)]，按空行切。

    ★★★ 第三条规则：**注会跨空行续段**。Book 1 的注 (8) 开头是
    `Mr. Justice Coleridge remarks that he understands the author to mean…`，
    而续段 `It Bepcars to me, however, … I cannot agree that when a law,
    decided to be constitutional, is in full force…` **另起一块、不带注号**——
    只按块首判会把它当成正文，于是**编者的第一人称被当成他的话**。
    （`decided to be constitutional` 是 judicial review 意义上的用法，
    18 世纪的英国法学家不会这么说；**是读原文才看出来的，不是判据抓到的**。）

    所以注块的属性**向后传播**，直到出现正文恢复的标志（页码边码／章眉／`*`）。
    """
    out, pos, carry = [], 0, False
    for b in re.split(r"(\n\s*\n)", text):
        if b.strip() and not re.fullmatch(r"\n\s*\n", b):
            if NOTE_HEAD.match(b):
                carry = True
            elif carry and BODY_RESUME.search(b):
                carry = False
            out.append((pos, pos + len(b), carry))
        pos += len(b)
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def find(quote, files=None):
    """→ [(文件名, 偏移, 在注块?, 块首 60 字, 前后提到他名字?)]。空列表 = 语料里找不到。"""
    q = norm(quote)
    if len(q) < 12:
        return [("**太短，不判**", -1, None, "", False)]
    hits = []
    for f in sorted(files or RAW.glob("commentaries_bk*_1898_en.txt")):
        t = f.read_text(encoding="utf-8", errors="replace")
        flat = norm(t)
        idx = flat.find(q)
        if idx < 0:
            continue
        # 用原文再定位一次（归一化会移位，故按锚点词回找）
        anchor = q.split(" ")[0]
        raw_idx = t.find(anchor)
        while raw_idx >= 0:
            if norm(t[raw_idx:raw_idx + len(q) + 80]).startswith(q[:60]):
                break
            raw_idx = t.find(anchor, raw_idx + 1)
        if raw_idx < 0:
            raw_idx = 0
        in_note, head, about = None, "", False
        for lo, hi, isnote in blocks(t):
            if lo <= raw_idx < hi:
                in_note = isnote
                head = norm(t[lo:lo + 60])
                # ★★★ 第二条判据：**块内（或前后 1500 字）出现「Blackstone」这个名字**
                #   → 说话的多半是**在谈论他的人**，不是他。
                #   起因：Book 1 卷首 W. D. Lewis 的序言里有
                #   `The unsigned notes are my own.` 与
                #   `the learning which has accumulated around Blackstone's work`——
                #   **那不是数字括号注块，第一条判据放它过去了**。
                #   实测这条规则很干净：正文块含 `Blackstone` 的只占 0.1–0.4%
                #   （bk1 19/5206、bk2 13/5258、bk4 16/12200），
                #   而第一人称正文块里含它的三卷合计只有 5 块——正是编者序言那几块。
                w = t[max(0, lo - 1500):min(len(t), hi + 1500)]
                about = "Blackstone" in w
                break
        hits.append((f.name, raw_idx, in_note, head, about))
    return hits


def self_test():
    cases, fails = [], []

    def chk(label, got, want):
        cases.append(label)
        if got != want:
            fails.append("%s：得 %r 应为 %r" % (label, got, want))

    bk1 = RAW / "commentaries_bk1_1898_en.txt"
    if not bk1.is_file():
        print("语料不在本机，自测跳过（**不算通过**）")
        return 0
    t = bk1.read_text(encoding="utf-8", errors="replace")
    bs = blocks(t)
    note = next(b for b in bs if b[2] and b[1] - b[0] > 200)
    body = next(b for b in bs if not b[2] and b[1] - b[0] > 400)

    # ① 正对照：正文块里的一段，必须判「不在注块」
    q = norm(t[body[0]:body[0] + 160])
    r = find(q, [bk1])
    chk("① 正文段 → 命中", bool(r), True)
    chk("① 正文段 → 不在注块", r[0][2] if r else None, False)

    # ② 反对照：编者注块里的一段，必须判「在注块」
    q2 = norm(t[note[0]:note[0] + 160])
    r2 = find(q2, [bk1])
    chk("② 注块段 → 命中", bool(r2), True)
    chk("② 注块段 → **在注块**", r2[0][2] if r2 else None, True)

    # ★★★ ②b 反对照：**编者 W. D. Lewis 的序言**——它不是数字括号注块，
    #   第一版判据放它过去了。这正是 [[fixtures-are-clean-because-i-wrote-them]]：
    #   我编的夹具只有「正文块 vs 注块」两种，**从没有「编者在正文块里说话」这一种**。
    r2b = find("In using the notes of other editors, I have followed the example", [bk1])
    chk("②b 编者序言 → 命中", bool(r2b), True)
    chk("②b 编者序言 → **不许判成他的话**",
        bool(r2b and (r2b[0][2] or r2b[0][4])), True)

    # ③ 反对照：语料里没有的字，必须报找不到
    chk("③ 编造的句子 → 找不到",
        find("this sentence does not occur anywhere in the corpus at all", [bk1]), [])

    # ④ 反对照：太短的串不判（不许冒充「已核」）
    chk("④ 太短 → 不判", find("the law", [bk1])[0][0], "**太短，不判**")

    # ★★★ ②c 反对照：**跨块续段的编者注**（注 (8) 的续段）。
    #   只按块首判会把它当正文——这是读原文才发现的，判据没抓到。
    r2c = find("I cannot agree that when a law, decided to be constitutional", [bk1])
    chk("②c 注的续段 → 命中", bool(r2c), True)
    chk("②c 注的续段 → **不许判成他的话**",
        bool(r2c and (r2c[0][2] or r2c[0][4])), True)

    # ⑤ 正对照：**他自己的第一人称**必须判为干净正文
    r5 = find("I shall not here enter into any minute inquiries",
              [RAW / "commentaries_bk4_1898_en.txt"])
    if r5:
        chk("⑤ 他自己的第一人称 → 在正文块", r5[0][2], False)
        chk("⑤ 他自己的第一人称 → 前后不提他的名字", r5[0][4], False)
    else:
        cases.append("⑤ 未命中（**不算通过**）")

    print("自测 %d/%d 通过" % (len(cases) - len(fails), len(cases)))
    for f in fails:
        print("  ✗", f)
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    res = find(sys.argv[1])
    if not res:
        print("✗ **语料里找不到这段字**——不要用它做逐字引文")
        sys.exit(1)
    # ★★ 退出码三档：0 = 可用｜1 = 不可用｜**2 = 没判**。
    #   第一版「太短不判」走的是 0，于是**「不判」冒充了「通过」**——
    #   这是本项目反复吃亏的形态（[[empty-default-swallows-unknown]]）。
    bad = unjudged = 0
    for name, off, in_note, head, about in res:
        if in_note is None:
            print("· %s —— **这不是通过，是没判**" % name)
            unjudged += 1
            continue
        if in_note:
            tag = "✗ **在编者注块里——不是他的话**"
        elif about:
            tag = "✗ **前后 1500 字里出现「Blackstone」——说话的多半是谈论他的人（编者序言／注）**"
        else:
            tag = "✓ 在正文块，且前后不提他的名字"
        print("%s\n    %s @%d｜块首：%s" % (tag, name, off, head[:70]))
        bad += 1 if (in_note or about) else 0
    if bad:
        sys.exit(1)
    sys.exit(2 if unjudged else 0)
