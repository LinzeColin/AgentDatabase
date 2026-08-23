#!/usr/bin/env python3
"""Archive the finished skins to the NAS, beside the source material.

The library already lives on the share as
`HarnessUI/<游戏>/<角色>/refs/…` — the anchors this run was generated from. The
deliverables belong next to the material they came from, not in a separate
tree, so a character folder answers "what did we have, and what did we make"
in one place:

    HarnessUI/<游戏>/<角色>/refs/            已有：锚图与出处
    HarnessUI/<游戏>/<角色>/skins/<变体>/    新增：light.png / dark.png / meta.json

Copies are verified by size and skipped when already correct, so this is safe
to re-run after an interrupted transfer — which matters, because 4.8GB over SMB
is slow enough that being interrupted is the normal case, not the exception.
AppleDouble sidecars are suppressed; the share is already littered with `._`
files from earlier passes and they double the file count for nothing.

Usage:
    python3 archive.py --src …/run/output --share ~/mnt/share/03_资料库/MetaData/HarnessUI
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
import time

GAME_ZH = {"genshin": "原神", "hsr": "崩铁", "zzz": "绝区零", "wuwa": "鸣潮", "nte": "异环",
           "hi3": "崩坏3"}


def digest(path: pathlib.Path) -> str:
    """内容摘要。SMB 上「返回成功」不等于「数据落盘」，只有读回来比对算数。"""
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_verified(source: pathlib.Path, target: pathlib.Path, *, tries: int = 4) -> str:
    """Returns 'copied', 'skipped', or 'failed'.

    Retries on I/O error with a backoff. Copying 612 files of 6-8MB back to back
    made the share return EIO on 240 of them, while the very same file copied by
    hand a minute later went through in under a second — the mount was being
    overrun, not broken. So a failure here is a reason to wait and try again,
    not a reason to give up on the file.
    """
    # 只比大小是不够的：2026-08-20 全量复查发现 614 张归档里 376 张
    # 「大小完全正确、内容全是 0」，而这个 skip 判据把它们一律当成已完成，
    # 于是每次重跑都跳过，坏了一个月也不会被发现。要比内容。
    try:
        if target.exists() and digest(target) == digest(source):
            return "skipped"
    except OSError:
        pass
    for attempt in range(1, tries + 1):
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Copy to a sidecar then rename, so an interrupted transfer never
            # leaves a half-written file the next run mistakes for complete.
            staging = target.with_name(target.name + ".part")
            # 不要用 shutil.copyfile：macOS 上它走 fcopyfile(clone)，在 smbfs 上
            # 写出一个尺寸完全正确、内容全是 0 的文件，并且**返回成功**。
            # 376 张空壳就是这么来的。
            want = digest(source)
            with open(source, "rb") as reader, open(staging, "wb") as writer:
                for chunk in iter(lambda: reader.read(4 * 1024 * 1024), b""):
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            if digest(staging) != want:
                staging.unlink(missing_ok=True)
                raise OSError("写完读回来对不上（SMB 静默写零）")
            if target.exists():
                target.unlink()          # SMB 上覆盖同名的 rename 会报 EIO
            staging.replace(target)
            return "copied"
        except Exception as error:
            if attempt == tries:
                print(f"  ! {target.parent.name}/{target.name}: {str(error)[:90]}", flush=True)
                return "failed"
            time.sleep(attempt * 2)
    return "failed"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=pathlib.Path, required=True)
    parser.add_argument("--share", type=pathlib.Path, required=True)
    parser.add_argument("--state", type=pathlib.Path, help="batch.json，用来带上验收指标")
    args = parser.parse_args()

    os.environ["COPYFILE_DISABLE"] = "1"
    metrics = {}
    pack_version = "1.7.0"
    if args.state and args.state.exists():
        state = json.loads(args.state.read_text(encoding="utf-8"))
        pack_version = state.get("pack_version") or pack_version
        for unit in state["units"].values():
            metrics.setdefault(unit["task"], {})[unit["side"]] = {
                "status": unit["status"], "metrics": unit["metrics"],
                "attempts": unit["attempt"],
            }

    masters = [p for p in sorted(args.src.rglob("*.png"))
               if "reject" not in p.name and len(p.relative_to(args.src).parts) == 4]
    tally = {"copied": 0, "skipped": 0, "failed": 0}
    started = time.time()
    seen_variants = 0

    for index, master in enumerate(masters, 1):
        game, character, variant, name = master.relative_to(args.src).parts
        game_zh = GAME_ZH.get(game)
        if not game_zh:
            continue
        destination = args.share / game_zh / character / "skins" / variant / name
        tally[copy_verified(master, destination)] += 1
        # A short breath every few files keeps the share from being overrun; the
        # unthrottled run failed 240 of 612.
        if index % 8 == 0:
            time.sleep(0.4)

        if name == "light.png":
            seen_variants += 1
            note = destination.parent / "meta.json"
            record = {
                "task": f"{game}/{character}/{variant}",
                "game": game, "game_zh": game_zh,
                "character": character, "variant": variant,
                "model": "gpt-image-2", "size": "3840x2160",
                "pack_version": pack_version,
                "acceptance": metrics.get(f"{game}/{character}/{variant}", {}),
                "generated": time.strftime("%Y-%m-%d"),
            }
            try:
                note.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8")
            except Exception as error:
                print(f"  ! meta.json: {str(error)[:60]}", flush=True)

        if index % 40 == 0:
            rate = index / max(time.time() - started, 1)
            print(f"  {index}/{len(masters)} · 新拷 {tally['copied']} · 已在 {tally['skipped']}"
                  f" · 失败 {tally['failed']} · {rate:.1f} 张/秒", flush=True)

    print(f"\n完成：{len(masters)} 张 · 新拷 {tally['copied']} · 已在 {tally['skipped']}"
          f" · 失败 {tally['failed']} · {seen_variants} 个变体 · "
          f"用时 {(time.time()-started)/60:.0f} 分", flush=True)


if __name__ == "__main__":
    main()
