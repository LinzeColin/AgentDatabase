#!/usr/bin/env python3
"""全量筛查解剖学缺陷——机器闸门查不了的那一类。

`runner.py` 只判四个数：比例、宽度、亮度、主体溢出。它对「这个人有三只手」
一无所知，而这正是用户第一眼就会否掉的东西（lucia/whispering-dreams 就是
三只手过的闸门）。所以要一个能看画面的判官。

两个省钱的设计，合起来把成本压到全量可跑：

*   **只送人物那一块。** 立绘压在画幅左 35%，右边是刻意留白的低细节天空，
    送过去纯属浪费。裁左 40% 再降到 900px 宽，手指级别的缺陷仍然看得清。
*   **只问是非，不要作文。** 结构化输出一个清单，模型不必组织语言。

判据写死成可核对的条目，不用「看起来怪不怪」这种没法复核的说法。

Usage:
    python3 screen_defects.py --catalog … --out defects.json [--limit 20] [--jobs 6]
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import io
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

from PIL import Image

MODEL = "gpt-5"
API = "https://api.openai.com/v1/responses"
CROP = 0.42          # 人物占左 35%，留一点余量
# 900px 时肩部区域只有约 300px，判官据此报了"两条手臂都能追到肩"——
# 而那张图里握杖的手臂根本是从腰侧长出来的。放大到 1500px 后同一处一眼可辨。
WIDTH = 1500

CHECKLIST = """检查这张二次元角色立绘的解剖与结构缺陷。不评价画风、构图、配色。

**先数，再判。** 不要凭整体印象，逐个部件点过去：

1. 数出画面里能看到的**手**（含被手套包住的）有几只。正常是 2 只，被遮挡或出画可以少于 2。
2. 对每一只手，从手腕**往回追**：手腕 → 前臂 → 上臂 → 肩膀 → 躯干。
   在 arm_shoulder_notes 里逐条写出每条手臂**接在身体的哪个位置**
   （例如"左臂接左肩，可见"、"持杖的手臂在腰侧消失，看不到肩"）。
   追不到肩膀、从腰/背/腋下凭空长出、或两条手臂共用同一侧肩膀的，都是多余肢体，
   属于 major。**这是最常见也最致命的一类，务必逐条追完再下结论。**
   注意：**"肩被衣物遮挡所以假定正常"是不允许的**。看不到肩点时，
   要看这条手臂的走向与躯干体块是否对得上——从腰侧、腋下或背后中段冒出来的，
   即使被布料盖住，也算 major。宁可多报，也不要替可疑处找理由。
3. 数腿。数手指（能看清的话）。
4. 看有没有重复部件（两个头、同侧两条腿）、融合在一起的肢体、明显穿模。
5. 看持物与配饰：武器、法杖、饰品有没有断裂、从身体里长出来、
   或者悬空不与任何东西相连。
6. 看面部：五官数量与位置。

**最后给一个 0-10 的显眼度分（obviousness）**，这是唯一真正要用的数：

  0-2  只有逐像素找才发现；或者只是被衣物/头发挡住看不清，本身可能是正常的
  3-5  盯着看能发现，但正常浏览不会注意到
  6-7  多看两眼就会觉得不对劲
  8-10 一眼出戏，任何人都会立刻认出是 AI 失误（例如凭空多出一条手臂、六根手指）

判分只看"普通人当壁纸看第一眼的反应"，不看"我作为检查者能不能挑出毛病"。
**被遮挡导致看不清 ≠ 显眼**，那种给 0-2 分。
风格化变形（长腿、大眼、飘发、夸张比例）一律 0 分。"""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        # 先逼它把数报出来。只问是非，模型会凭整体印象答"没问题"——
        # 校准时它就是这么放过了一张有三只手的图。
        "hands_visible": {"type": "integer"},
        "arms_traceable_to_shoulder": {"type": "integer"},
        # 逼它把每条手臂的连接位置写出来。只报一个数字时它会凭印象填 2 ——
        # 校准时那张"手臂从腰侧长出来"的图就是这么被放过的。
        "arm_shoulder_notes": {"type": "array", "items": {"type": "string"}},
        "legs_visible": {"type": "integer"},
        "has_defect": {"type": "boolean"},
        # 真正用来排序和取舍的是这个分。只问"有没有毛病"时答案永远是有 ——
        # 第一版据此把 100 张里的 83 张判成缺陷，那种清单没法用。
        "obviousness": {"type": "integer"},
        "severity": {"type": "string", "enum": ["none", "minor", "major"]},
        "defects": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "part": {"type": "string", "enum":
                             ["hand", "arm", "leg", "body", "face", "prop", "floating"]},
                    "detail": {"type": "string"},
                },
                "required": ["part", "detail"],
            },
        },
    },
    "required": ["hands_visible", "arms_traceable_to_shoulder", "arm_shoulder_notes", "legs_visible",
                 "has_defect", "obviousness", "severity", "defects"],
}


def _encode(region: Image.Image, width: int) -> str:
    scale = width / region.size[0]
    region = region.resize((width, int(region.size[1] * scale)), Image.LANCZOS)
    buffer = io.BytesIO()
    region.save(buffer, "JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode()


def crop_payload(master: pathlib.Path) -> tuple[str, str]:
    """两张图：整个人物，加一张上半身特写。

    只送整体时判官会替可疑处开脱——「肩被披帛遮挡但位置合理」。同一张图裁到
    上半身后，那条从腰侧长出来的手臂一眼可辨。手、脸、肩这些缺陷最集中的部位
    值得单独给一张，代价只是多一张 1100px 的图。
    """
    with Image.open(master) as image:
        image = image.convert("RGB")
        w, h = image.size
        whole = image.crop((0, 0, int(w * CROP), h))
        # 上半身：躯干与双臂所在的区间
        torso = image.crop((int(w * 0.02), int(h * 0.08), int(w * 0.32), int(h * 0.64)))
        return _encode(whole, WIDTH), _encode(torso, 1100)


def judge(entry: dict, key: str, root: pathlib.Path, side: str) -> dict | None:
    master = root / "master" / entry["id"] / f"{side}.png"
    if not master.exists():
        return None
    whole, torso = crop_payload(master)
    body = json.dumps({
        "model": MODEL,
        "input": [{"role": "user", "content": [
            {"type": "input_text", "text": CHECKLIST},
            {"type": "input_text", "text": "第一张：整个人物。第二张：同一张图的上半身特写，"
                                           "手、肩、脸的连接关系以这张为准。"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{whole}"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{torso}"},
        ]}],
        "text": {"format": {"type": "json_schema", "name": "defect_report",
                            "schema": SCHEMA, "strict": True}},
    }).encode()
    request = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.load(response)
            text = next(c["text"] for item in payload["output"]
                        if item.get("type") == "message"
                        for c in item["content"] if c.get("type") == "output_text")
            verdict = json.loads(text)
            verdict.update({"id": entry["id"], "side": side,
                            "label": entry.get("label") or entry["character"]})
            return verdict
        except Exception as error:
            if attempt == 2:
                return {"id": entry["id"], "side": side, "error": str(error)[:120]}
            time.sleep(2 * (attempt + 1))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=pathlib.Path, required=True)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.home() / ".harness-ui")
    parser.add_argument("--key-file", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--sides", default="light,dark")
    args = parser.parse_args()

    key = args.key_file.read_text().strip()
    entries = json.loads(args.catalog.read_text(encoding="utf-8"))["entries"]
    if args.limit:
        entries = entries[:args.limit]
    jobs = [(e, s) for e in entries for s in args.sides.split(",")]

    # 断点续跑：全量要跑十几分钟，中断了不该从头再来
    done = {}
    if args.out.exists():
        try:
            for row in json.loads(args.out.read_text(encoding="utf-8"))["results"]:
                done[f"{row['id']}|{row['side']}"] = row
        except Exception:
            pass
    jobs = [(e, s) for e, s in jobs if f"{e['id']}|{s}" not in done]
    print(f"待判 {len(jobs)} 张（已有 {len(done)} 张结果）")

    results = list(done.values())
    checked = 0
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = {pool.submit(judge, e, key, args.root, s): (e, s) for e, s in jobs}
        for future in concurrent.futures.as_completed(futures):
            verdict = future.result()
            checked += 1
            if verdict:
                results.append(verdict)
                if (verdict.get("obviousness") or 0) >= 6:
                    parts = "、".join(d["part"] for d in verdict.get("defects", []))
                    print(f"  ✗ {verdict['label']} [{verdict['side']}] 显眼度 "
                          f"{verdict['obviousness']}：{parts}", flush=True)
            if checked % 20 == 0:
                print(f"     …已判 {checked}/{len(jobs)}", flush=True)
                args.out.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=1),
                                    encoding="utf-8")

    bad = [r for r in results if (r.get("obviousness") or 0) >= 6]
    major = [r for r in results if (r.get("obviousness") or 0) >= 8]
    args.out.write_text(json.dumps({"model": MODEL, "total": len(results),
                                    "defective": len(bad), "major": len(major),
                                    "results": results}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    print(f"\n判完 {len(results)} 张 · 显眼度≥6 共 {len(bad)}（≥8 共 {len(major)}）→ {args.out}",
          flush=True)


if __name__ == "__main__":
    main()
