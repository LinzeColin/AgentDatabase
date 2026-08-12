#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive.org 抓源器 —— 阶段 1b 唯一的下载入口。

用法：
    python3 fetch_ia.py --ids-file <每行一个 identifier 的文件> --out <raw 目录>
    python3 fetch_ia.py --ids a,b,c --out <raw 目录>

**它做的四件事，每一件都是实测教训换来的：**

① **`access-restricted-item: true` 一律硬跳过。**
   那是 archive.org 的借阅限制 = 访问控制。本项目**不绕任何访问控制**，
   跳过要记进日志并计入 `skipped_access_restricted`，**不许静默丢**
   （[[empty-default-swallows-unknown]]：空默认值会被读成「没问题」）。

② **并发 4，遇 429/403 立刻退回 1 并退避。**
   退避后不再抬回 4——本轮剩下的全部串行。宁可慢，不许把对方惹毛。

③ **出版年不信 `metadata.date`。**
   archive.org 的 `date` 是**原作年份不是版次年份**
   （`_IA的date是原作年不是版次年-2026-08-11.md`）。本工具把 `date`／`year`／
   `publicdate` 三个字段**原样记下**，并另外从正文头 400 行里抓出所有四位年份
   存进 `titlepage_years`，**PD 判定由人看这两组数，不由本工具下结论**。

④ **每份都落 sha256 + 字节数 + 词数 + 取回时刻**，写进 `_fetch-manifest.json`。
   证据要留在仓里，不是留在终端里（[[evidence-must-live-in-the-repo-not-the-terminal]]）。

★ 退出码：0=全部尝试完（**不等于全部成功**，成败看 manifest 的计数）；
          2=参数错；3=一个都没取到。
★ **不要接管道判成败**（[[pipe-to-tail-hides-the-exit-code]]）。
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import pathlib
import re
import sys
import threading
import time
import urllib.error
import urllib.request

UA = "persona-distiller/1.0 (public-domain corpus collection; contact via repo)"
META = "https://archive.org/metadata/{}"
DL = "https://archive.org/download/{}/{}"
YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")

# 并发闸门：一旦撞 429/403 就永久降到 1
_lock = threading.Lock()
_serial_mode = {"on": False, "reason": ""}


def _get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _trip_serial(reason: str) -> None:
    with _lock:
        if not _serial_mode["on"]:
            _serial_mode["on"] = True
            _serial_mode["reason"] = reason
            print(f"  ⚠️  撞到 {reason} —— **并发降到 1，本轮不再抬回**", flush=True)


def pick_text_file(meta: dict) -> str:
    """挑正文文件：优先 *_djvu.txt，退而求其次任一 .txt（不要 _meta.txt）。"""
    files = meta.get("files") or []
    djvu = [f["name"] for f in files if f.get("name", "").endswith("_djvu.txt")]
    if djvu:
        return sorted(djvu)[0]
    txt = [f["name"] for f in files
           if f.get("name", "").endswith(".txt")
           and not f.get("name", "").endswith("_meta.txt")
           and "_chocr" not in f.get("name", "")]
    return sorted(txt)[0] if txt else ""


def fetch_one(ident: str, out: pathlib.Path, skip_existing: bool = False) -> dict:
    rec = {"identifier": ident, "status": "", "note": ""}
    # 串行模式下每次请求之间强制间隔
    if _serial_mode["on"]:
        time.sleep(3.0)
    try:
        meta = json.loads(_get(META.format(ident)).decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            _trip_serial(f"HTTP {e.code}（metadata {ident}）")
        rec["status"] = "元数据取不到"
        rec["note"] = f"HTTP {e.code}"
        return rec
    except Exception as e:  # noqa: BLE001
        rec["status"] = "元数据取不到"
        rec["note"] = f"{type(e).__name__}: {e}"
        return rec

    m = meta.get("metadata") or {}
    if not m:
        rec["status"] = "元数据为空"
        rec["note"] = "**不是「没问题」，是这个 identifier 在 IA 上不存在或已下架**"
        return rec

    # ① 访问控制：硬跳过
    ar = m.get("access-restricted-item")
    if str(ar).lower() in ("true", "1", "yes"):
        rec["status"] = "跳过·访问受限"
        rec["note"] = "access-restricted-item=true（借阅限制）。**本项目不绕访问控制。**"
        rec["ia_date"] = m.get("date", "")
        rec["ia_year"] = m.get("year", "")
        return rec

    name = pick_text_file(meta)
    if not name:
        rec["status"] = "无文本层"
        rec["note"] = "该 item 没有 _djvu.txt 或任何正文 .txt（可能只有图像）"
        return rec

    dest_pre = out / f"{ident}.txt"
    if skip_existing and dest_pre.exists():
        blob = dest_pre.read_bytes()   # ★ 不重下，sha256 从**本地这一份**算
    else:
      try:
        blob = _get(DL.format(ident, urllib.request.quote(name)), timeout=300)
      except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            _trip_serial(f"HTTP {e.code}（download {ident}）")
        rec["status"] = "正文取不到"
        rec["note"] = f"HTTP {e.code} on {name}"
        return rec
      except Exception as e:  # noqa: BLE001
        rec["status"] = "正文取不到"
        rec["note"] = f"{type(e).__name__}: {e}"
        return rec

    dest = out / f"{ident}.txt"
    if not (skip_existing and dest.exists()):
        dest.write_bytes(blob)
    text = blob.decode("utf-8", "replace")
    head = "\n".join(text.splitlines()[:400])

    rec.update({
        "status": "已取回",
        "file": dest.name,
        "source_url": DL.format(ident, name),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "words": len(text.split()),
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
        # ★ 三个年份字段原样记，不合并、不下结论
        "ia_date": m.get("date", ""),
        "ia_year": m.get("year", ""),
        "ia_publicdate": m.get("publicdate", ""),
        "ia_creator": m.get("creator", ""),
        "ia_title": m.get("title", ""),
        "ia_licenseurl": m.get("licenseurl", ""),
        # ★ 正文头 400 行里出现的四位年份 —— PD 判定看这个，不看 ia_date
        "titlepage_years": sorted(set(YEAR_RE.findall(head)))[:12],
    })
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids-file")
    ap.add_argument("--ids")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-existing", action="store_true",
                    help="盘上已有同名 .txt 时不重下正文，只补元数据并从本地文件算 sha256")
    a = ap.parse_args()

    if a.ids_file:
        ids = [x.strip() for x in pathlib.Path(a.ids_file).read_text(encoding="utf-8").splitlines()
               if x.strip() and not x.strip().startswith("#")]
    elif a.ids:
        ids = [x.strip() for x in a.ids.split(",") if x.strip()]
    else:
        print("要么 --ids-file 要么 --ids", file=sys.stderr)
        return 2
    if not ids:
        print("identifier 列表是空的 —— **这不是「没有要抓的」，是参数给错了**", file=sys.stderr)
        return 2

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"抓源：{len(ids)} 个 identifier → {out}  并发 {a.workers}（遇 429/403 降 1）", flush=True)

    recs = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch_one, i, out, a.skip_existing): i for i in ids}
        for fut in cf.as_completed(futs):
            r = fut.result()
            recs.append(r)
            mark = {"已取回": "✓", "跳过·访问受限": "⊘"}.get(r["status"], "✗")
            extra = f'{r.get("words", 0):>7} 词' if r["status"] == "已取回" else r.get("note", "")
            print(f"  {mark} {r['identifier'][:52]:<52} {r['status']:<12} {extra}", flush=True)

    # ★★ **合并，不覆盖。** 实测事故（2026-08-12）：增量抓源直接重写 manifest，
    #   Marshall／Lincoln／Fröbel **共 71 份的指针（source_url + sha256）被抹掉**，
    #   正文还在盘上而仓里只存指针 —— 指针没了就重建不了。
    #   同 [[empty-default-swallows-unknown]]：少掉的那部分不会报错，只是「变少了」。
    mf = out / "_fetch-manifest.json"
    if mf.exists():
        old = json.loads(mf.read_text(encoding="utf-8")).get("记录", [])
        seen = {r["identifier"] for r in recs}
        merged_in = [r for r in old if r["identifier"] not in seen]
        if merged_in:
            print(f"  ↳ 并入既有 manifest 的 {len(merged_in)} 条（本轮没碰的）")
        recs += merged_in
    recs.sort(key=lambda r: r["identifier"])
    ok = [r for r in recs if r["status"] == "已取回"]
    restricted = [r for r in recs if r["status"] == "跳过·访问受限"]
    failed = [r for r in recs if r["status"] not in ("已取回", "跳过·访问受限")]

    manifest = {
        "生成时刻": datetime.datetime.now().isoformat(timespec="seconds"),
        "请求数": len(ids),
        "已取回": len(ok),
        "skipped_access_restricted": len(restricted),
        "失败": len(failed),
        "并发降级": _serial_mode["reason"] or "无（全程并发 4）",
        "总词数": sum(r["words"] for r in ok),
        "★ 年份口径": "ia_date 是原作年不是版次年；PD 判定看 titlepage_years，由人判",
        "记录": recs,
    }
    mf.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # ★ 分母写清楚是**本轮请求数**还是 manifest 全量——合并之后这两个数不一样，
    #   直接印 `{len(ok)}／{len(ids)}` 会出现「73／9」这种读起来像超过 100% 的行。
    this_round = len([r for r in recs if r["identifier"] in set(ids)])
    ok_this = len([r for r in ok if r["identifier"] in set(ids)])
    print(f"\n本轮 {ok_this}／{len(ids)} 取回｜manifest 全量 {len(ok)} 份"
          f"｜访问受限跳过 {len(restricted)}｜失败 {len(failed)}｜总词数 {manifest['总词数']:,}")
    empties = [r["identifier"] for r in ok if r.get("words", 0) == 0]
    if empties:
        print(f"⚠️ **落盘但 0 词** {len(empties)} 份（**不是「取回成功」**，正文是空的）："
              + "、".join(empties[:6]))
    if restricted:
        print("⊘ 访问受限（**不绕，记档**）：" + "、".join(r["identifier"] for r in restricted))
    if failed:
        print("✗ 失败：" + "、".join(f"{r['identifier']}({r['status']})" for r in failed))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
