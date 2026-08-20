#!/usr/bin/env python3
"""把契约段写进一个 agent 指令文件，或只判断它有没有漂移。

单独拆成文件而不是内嵌 heredoc：内嵌版在 zsh 里被引号吃过一次，
一个引号的差别会让分发静默变成半成品 —— 这类东西不该靠 shell 转义活着。

约定用环境变量传参，输出恰好一行：SAME / WROTE / DRIFT。
"""
import os
import pathlib
import sys


def main() -> int:
    tgt = pathlib.Path(os.environ["ATLAS_TGT"])
    src = pathlib.Path(os.environ["ATLAS_SRC"])
    b, e = os.environ["ATLAS_B"], os.environ["ATLAS_E"]
    check = os.environ.get("ATLAS_MODE") == "--check"

    s = src.read_text(encoding="utf-8")
    block = s[s.index(b): s.index(e) + len(e)]
    t = tgt.read_text(encoding="utf-8")

    # 旧哨兵先清掉。不清的后果：v1 那 116 行留在原地不被替换，
    # v2 的 25 行追加在后面 —— 文件变成 141 行，比不瘦身还糟。
    ob, oe = os.environ.get("ATLAS_OB", ""), os.environ.get("ATLAS_OE", "")
    if ob and oe and ob in t and oe in t and ob != b:
        t = t[:t.index(ob)] + t[t.index(oe) + len(oe):]
        t = t.replace("\n\n\n", "\n\n")

    has = b in t and e in t
    cur = t[t.index(b): t.index(e) + len(e)] if has else None

    if has and cur == block:
        print("SAME")
        return 0
    if check:
        print("DRIFT")
        return 0

    if has:
        # 整段替换。段外内容原样保留 —— 那可能是别人写的，不归这个脚本管。
        new = t[:t.index(b)] + block + t[t.index(e) + len(e):]
    else:
        new = t + ("" if t.endswith("\n") else "\n") + "\n" + block + "\n"

    if new == tgt.read_text(encoding="utf-8"):
        print("SAME")
        return 0

    # 只在真要改的时候留一份备份，且固定一个文件名 —— 每天无条件备份
    # 会在半年里堆出上千个 .bak，那本身就是一种垃圾。
    tgt.with_name(tgt.name + ".bak-agents").write_text(t, encoding="utf-8")
    tgt.write_text(new, encoding="utf-8")
    print("WROTE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
