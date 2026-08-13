#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 `_fetch-manifest.json` 生成 **`_ids-rebuild.txt`** —— 语料不进 git 之后，
这份清单是收件人**逐字节重建语料的唯一入口**。

## 为什么要有这个工具

`_corpora/.gitignore` 里写着（用户 2026-08-13 裁定）：

    语料正文不进 git，进仓的是指针：
      _ids-rebuild.txt      ← **重建用的权威清单**（从 manifest 的「已取回」生成）
      _fetch-manifest.json  ← 每份的 source_url + sha256 + 字节数 + 词数

**而这份清单一直是手打的，没有生成器。** 后果当场兑现：
第 1 批 10 个工作区都有 `_ids-rebuild.txt`，
**第 2 批新建的 3 个（burbank-183／leonardo-184／michelangelo-185）一个都没有**——
它们的 manifest 在仓里，正文被 gitignore 挡在仓外，
**而把两者接起来的那份清单不存在** ⇒ 收件人拿到包也重建不出这三个人的语料。

[[tool-existed-and-i-did-it-by-hand]] 的反面：**这次是「工具本该存在而不存在」**，
于是同一件事做了 10 次都对、第 11 次漏了，且没有任何东西会提醒。

## 口径（与 .gitignore 的注释逐字一致）

- 只收 manifest 里 `status == "已取回"` 的。
  **`_ids*.txt` 是「打算抓的」，manifest 是「真抓到的」**——两者差在无文本层/取不到的那些。
  拿 `_ids.txt` 去重建会多抓一批必然失败的，也会让「份数对不上」变成常态。
- 输出**逐行 identifier**，前面带注释头（含生成时的份数），供 `fetch_ia.py --ids-file` 直接吃。
- ★ 重建后**必须**逐份比对 manifest 里的 sha256 —— `--verify` 就是干这个的。

用法：
    python3 emit_ids_rebuild.py --raw <raw 目录>            # 生成/更新
    python3 emit_ids_rebuild.py --raw <raw 目录> --check    # 只查不写（rc=1 表示不一致）
    python3 emit_ids_rebuild.py --scan <_corpora 目录>      # 扫全库，报哪些缺/不一致

退出码：0=一致或已写；1=有不一致（--check/--scan）；2=参数错；3=没有 manifest。
"""
import argparse
import json
import pathlib
import sys
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

HEAD = """# ★ **重建用的权威清单** —— 从 _fetch-manifest.json 的「已取回」现生成。
# 任何 _ids-*.txt（探源/增量/上限）都**重建不出这批**：
#   清单是「打算抓的」，manifest 是「真抓到的」，两者差在无文本层/取不到的那些。
# 重建后逐份比对 manifest 里的 sha256 才算通过。
# 本文件由 _ledgers/_pipeline/emit_ids_rebuild.py 生成，**不要手改**。
# 份数：{n}
"""


def ids_from_manifest(raw: pathlib.Path):
    mf = raw / "_fetch-manifest.json"
    if not mf.exists():
        return None
    recs = json.loads(mf.read_text(encoding="utf-8")).get(
        "记录", json.loads(mf.read_text(encoding="utf-8")).get("記錄", []))
    return [r["identifier"] for r in recs if r.get("status") == "已取回"]


def read_existing(p: pathlib.Path):
    if not p.exists():
        return None
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def one(raw: pathlib.Path, write: bool):
    """返回 (状态, 说明)。状态 ∈ {ok, wrote, missing-manifest, mismatch, absent}"""
    ids = ids_from_manifest(raw)
    if ids is None:
        return "missing-manifest", "没有 _fetch-manifest.json"
    out = raw / "_ids-rebuild.txt"
    cur = read_existing(out)
    if cur is None:
        if write:
            out.write_text(HEAD.format(n=len(ids)) + "\n".join(ids) + "\n", encoding="utf-8")
            return "wrote", "新建，%d 条" % len(ids)
        return "absent", "**缺 _ids-rebuild.txt**（manifest 有 %d 条已取回）" % len(ids)
    if cur == ids:
        return "ok", "%d 条，一致" % len(ids)
    # ★ 不一致要报**两个方向**：清单多了什么、少了什么。只报一个数会让人以为只是数目差。
    extra = [i for i in cur if i not in set(ids)]
    lack = [i for i in ids if i not in set(cur)]
    msg = "清单 %d 条 vs manifest 已取回 %d 条｜清单多出 %d、缺 %d" % (
        len(cur), len(ids), len(extra), len(lack))
    if extra:
        msg += "｜多出例：" + "、".join(extra[:3])
    if lack:
        msg += "｜缺失例：" + "、".join(lack[:3])
    if write:
        out.write_text(HEAD.format(n=len(ids)) + "\n".join(ids) + "\n", encoding="utf-8")
        return "wrote", "已重写；原" + msg
    return "mismatch", msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--scan", help="_corpora 目录，扫全部 wip-*/workspaces/*/raw")
    ap.add_argument("--check", action="store_true", help="只查不写")
    ap.add_argument("--apply", action="store_true", help="--scan 时也写")
    a = ap.parse_args()

    if a.raw:
        st, msg = one(pathlib.Path(a.raw), write=not a.check)
        print("%-16s %s" % (st, msg))
        return 3 if st == "missing-manifest" else (1 if st in ("mismatch", "absent") else 0)

    if not a.scan:
        print("要给 --raw 或 --scan", file=sys.stderr)
        return 2

    root = pathlib.Path(a.scan)
    bad = 0
    n_ok = n_no_mf = 0
    for raw in sorted(_w / "raw" for _w in iter_workspaces(root) if (_w / "raw").is_dir()):
        st, msg = one(raw, write=a.apply)
        ws = raw.parts[-4]
        if st == "missing-manifest":
            n_no_mf += 1
            continue                      # 老工作区没有 manifest，正文本来就在仓里
        if st in ("mismatch", "absent"):
            bad += 1
            print("❌ %-24s %s" % (ws, msg))
        elif st == "wrote":
            print("✍  %-24s %s" % (ws, msg))
        else:
            n_ok += 1
    print("\n扫完：一致 %d 个｜有问题 %d 个｜没有 manifest（老工作区，正文在仓里）%d 个"
          % (n_ok, bad, n_no_mf))
    if bad and not a.apply:
        print("★ 加 --apply 生成/修正")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
