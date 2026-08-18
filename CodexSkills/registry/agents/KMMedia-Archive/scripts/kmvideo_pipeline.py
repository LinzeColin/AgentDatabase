#!/usr/bin/env python3
"""KMVideo 一体化流水线 v0.2.0。

一条命令全跑：扫描+增量归档 → 规格探测 → 哈希去重 → 缩略图 → 本地标注（无外部 agent）
→ 幂等改名 → 登记表双格式 → 三处落地 → 自验收 → 产能汇总。

用法：
  python3 kmvideo_pipeline.py all --groups-file 白名单.txt [--workdir DIR] [--start "YYYY-MM-DD HH:MM:SS"]
  python3 kmvideo_pipeline.py {scan|probe|dedup|thumbs|label|rename|registry|upload|accept|report} ...

硬约束见 SKILL.md。不得调用任何外部 agent（cc/codex 等）。
"""
from __future__ import annotations

import argparse
import atexit
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archive_internal_media as aim  # noqa: E402

ARCHIVER = aim

TIMEZONE = aim.TIMEZONE
SMB_ROOT = aim.SMB_ROOT
MANIFEST = aim.MANIFEST_NAME
DWS = aim.dws_json
MEDIA_ID_RE = aim.MEDIA_ID_RE

SMB_THUMBS = Path("/Volumes/share/03_资料库/MetaData/IDS_MetaData/KMVideo_缩略图")
REG_CSV = SMB_ROOT / "素材登记表.csv"
MAP_CSV = SMB_ROOT / "原名新名映射.csv"
PRIVATE_CLIENT = aim.PRIVATE_DB_CLIENT

# 登记表三个本机落点（SMB 为唯一真源，另两处为分发副本）
DOCS_INDEX = Path.home() / "Documents" / "KMVideo" / "00_治理与登记" / "02_登记与索引"
DOWNLOADS = Path.home() / "Downloads"

# 视频子集列（供 ChatGPT 等无本地权限的模型上传使用，体积小）
VIDEO_SUBSET_COLS = ["项目", "文件名", "日期", "时长秒", "分辨率", "功能位", "画质等级",
                     "描述", "画面元素", "镜头特征", "工序阶段", "能证明什么", "脱敏风险", "置信度"]
MEDIA_FILTER = None  # main() 根据 --media-type 设置：None=全部 / "video" / "photo"
SKIP_GROUPS: set[str] = set()  # main() 根据 --skip-groups 设置（大目录 NAS 异常时跳过，夜间单独跑）

# 任务书业务映射（照抄）
BUSINESS = {
    "武汉开明高新科技有限公司": "内部", "付款请示群": "内部", "2026年商务部报价群": "内部",
    "生产管理群": "内部", "开明管理人员群": "内部", "张霖泽": "内部", "项目设备工具类管理群": "内部",
    "池州天赐20260415": "焊接", "福建韩研2026.4.30": "焊接", "阜阳电力齿轮修复2025.10.31": "焊接",
    "开明生产群": "焊接", "新洋丰焊补2026.5.4": "焊接",
    "山东日照检修群": "安装检修",
    "芜湖新兴铸管2026.3.31": "化工钢铁", "萍乡钢铁2026.6.3": "化工钢铁",
    "湘东区萍乡钢铁20260622": "化工钢铁", "湖南湘潭钢铁2026.3.6": "化工钢铁",
    "福建鼎信实业2026.6.4": "化工钢铁",
    "新都化工1500吨大颗粒项目": "化工", "新疆宜化技改2026": "化工", "新疆宜化2026": "化工",
    "内蒙古金鄂博氟化工2026.7.5": "化工", "赣锋锂业2026.7.27": "化工",
    "松滋葛洲坝小齿调整（原为调窑）2026.06.28": "水泥调测窑",
    "盐湖海纳2026.1.22": "水泥", "盐湖海纳大齿圈小齿更换2026.7.5": "水泥",
    "汝州天瑞2#线3档托轮2次返修2026.1.16": "水泥",
}

NEW_COLS = ["时长秒", "分辨率", "帧率", "有无音轨", "重复于", "可用起点秒", "可用终点秒",
            "功能位", "画质等级", "画面元素", "镜头特征", "工序阶段", "能证明什么",
            "脱敏风险", "缩略图路径", "标注执行者", "标注日期", "复核状态"]

VOCAB = {
    "功能位": {"开场证据", "过程证据", "关键细节", "验收闭环", "环境铺垫", "不可用"},
    "画面元素": {"火花", "刀具", "量具", "人员", "轮带", "托轮", "齿轮", "筒体", "表盘",
                 "焊接", "吊装", "厂区", "文字牌", "切屑", "加工纹面", "磨损面", "无"},
    "镜头特征": {"大特写", "中景", "全景", "运动镜头", "固定机位", "强对比", "逆光", "手持抖动"},
    "工序阶段": {"测量", "拆解", "加工", "焊接", "复检", "收尾", "无法判断"},
    "脱敏风险": {"客户名称", "人脸", "打卡应用水印", "精确地理位置", "车牌", "安全告示牌", "无"},
}

# 关键词 → (说明, 工序阶段, 功能位, 画面元素)  本地语义标注核心表
KEYWORDS = [
    ("车削", "轮带车削", "加工", "过程证据", "刀具、切屑、加工纹面"),
    ("切削", "车削加工", "加工", "过程证据", "刀具、切屑、加工纹面"),
    ("刀架", "车削装置", "加工", "过程证据", "刀具"),
    ("百分表", "跳动量测", "测量", "验收闭环", "量具、表盘"),
    ("跳动", "跳动量测", "测量", "验收闭环", "量具、表盘"),
    ("表座", "跳动量测", "测量", "关键细节", "量具、表盘"),
    ("轮带", "轮带检修", "加工", "关键细节", "轮带、磨损面"),
    ("托轮", "托轮检修", "复检", "关键细节", "托轮、磨损面"),
    ("窑", "窑体检修", "无法判断", "过程证据", "筒体"),
    ("筒体", "窑体检修", "无法判断", "过程证据", "筒体"),
    ("焊", "焊接作业", "焊接", "过程证据", "焊接"),
    ("打磨", "打磨作业", "加工", "过程证据", "火花、加工纹面"),
    ("吊装", "吊装作业", "拆解", "过程证据", "吊装、人员"),
    ("吊车", "吊装作业", "拆解", "过程证据", "吊装"),
    ("开工", "开工仪式", "无法判断", "环境铺垫", "人员、厂区"),
    ("仪式", "开工仪式", "无法判断", "环境铺垫", "人员、厂区"),
    ("班前", "班前会", "无法判断", "环境铺垫", "人员、厂区"),
    ("晨会", "班前会", "无法判断", "环境铺垫", "人员、厂区"),
    ("验收", "终检验收", "复检", "验收闭环", "量具"),
    ("复检", "终检验收", "复检", "验收闭环", "量具"),
    ("终检", "终检验收", "复检", "验收闭环", "量具"),
    ("量测", "尺寸量测", "测量", "关键细节", "量具"),
    ("测量", "尺寸量测", "测量", "关键细节", "量具"),
    ("量尺寸", "尺寸量测", "测量", "关键细节", "量具"),
    ("发货", "发货装车", "收尾", "环境铺垫", "吊装、厂区"),
    ("装车", "发货装车", "收尾", "环境铺垫", "吊装、厂区"),
    ("报价", "报价单据", "无法判断", "环境铺垫", "文字牌"),
    ("清单", "清单资料", "无法判断", "环境铺垫", "文字牌"),
    ("合同", "合同资料", "无法判断", "环境铺垫", "文字牌"),
    ("日志", "工作日志", "无法判断", "环境铺垫", "文字牌"),
    ("水印", "水印打卡", "无法判断", "不可用", "文字牌"),
    ("打卡", "打卡记录", "无法判断", "不可用", "文字牌"),
    ("马甲", "劳保马甲", "无法判断", "环境铺垫", "人员"),
    ("围栏", "移动围栏", "无法判断", "环境铺垫", "厂区"),
    ("安全帽", "劳保用品", "无法判断", "环境铺垫", "人员"),
    ("工具", "工具物资", "无法判断", "环境铺垫", "厂区"),
]

DESENS_RISK_KW = {
    "客户名称": ["客户", "甲方", "钢厂", "水泥厂", "公司名"],
    "人脸": ["人", "合影", "自拍"],
    "打卡应用水印": ["打卡", "水印"],
    "精确地理位置": ["定位", "位置", "GPS"],
    "车牌": ["车牌", "车号"],
    "安全告示牌": ["告示", "警示牌"],
}


def now_sh():
    return datetime.now(TIMEZONE).replace(microsecond=0)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rsync_write(src: Path, dst: Path) -> None:
    """约束7：rsync 写 SMB + 字节数校验。"""
    r = subprocess.run(["rsync", "--inplace", "--whole-file", str(src), str(dst)],
                       capture_output=True, text=True, timeout=1200)
    if r.returncode != 0:
        raise RuntimeError(f"rsync fail {dst}: {r.stderr[-200:]}")
    if os.path.getsize(dst) != os.path.getsize(src):
        raise RuntimeError(f"size mismatch {dst}")


def load_media(groups: list[str]) -> list[dict]:
    """读各群 manifest 的 complete media 记录（只读），可按 MEDIA_FILTER 过滤。"""
    out = []
    for g in groups:
        mf = SMB_ROOT / g / MANIFEST
        if not mf.exists():
            continue
        for line in mf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("record_type") == "media":
                if MEDIA_FILTER and d.get("media_type") != MEDIA_FILTER:
                    continue
                if g in SKIP_GROUPS:
                    continue
                d["_group"] = g
                out.append(d)
    return out


# ---------- 运行前置：并发锁 / SMB 健康自检 / 动态群名单 ----------

def acquire_workdir_lock(workdir: Path) -> None:
    """同一 workdir 只允许一个 pipeline 实例。

    实测事故：cron 每 30 分钟触发一次，而全量要跑 1 小时以上 —— 21:06 的主实例
    （rename 阶段）和 21:30 的 cron 新实例（scan 阶段）并存过，两个进程同时写
    同一份 manifest 与登记表。这里用 pid 文件自锁，发现活着的同伴就直接退出。
    """
    lock = workdir / ".pipeline.lock"
    if lock.is_file():
        try:
            pid = int(lock.read_text(encoding="utf-8").split()[0])
        except (ValueError, OSError, IndexError):
            pid = -1
        if pid > 0 and pid != os.getpid():
            alive = True
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                alive = False  # 只有「查无此进程」才算残留锁
            except PermissionError:
                alive = True   # 进程在，只是不归我管（别把 EPERM 当成已退出）
            except OSError:
                alive = True
            if alive:
                raise SystemExit(
                    f"另一个 pipeline 实例仍在运行（pid={pid}，锁文件 {lock}）；"
                    "本次直接退出，绝不并发写同一份 manifest 与登记表。")

    lock.write_text(f"{os.getpid()} {now_sh().isoformat()}\n", encoding="utf-8")
    atexit.register(lambda: lock.unlink(missing_ok=True))


SMB_SLOW_SECONDS = float(os.environ.get("SMB_SLOW_SECONDS", "10"))


def smb_health_check(groups: list[str]) -> dict:
    """开跑前量一次 SMB，退化就把修复命令直接打出来。

    实测结论：服务端是 OpenWRT 路由器上的 Samba（USB 外接硬盘）。所谓「白天不可用」
    不是网络也不是时段问题，而是 **SMB 会话退化 + 卡死进程占管道**。挂载健康时
    18k 目录枚举 4s、单文件读 0.04s、写 2MB 1s；退化时同样的枚举 90s+ 跑不完。
    """
    if not SMB_ROOT.is_dir():
        return {"state": "unmounted", "hint": 'open "smb://GUEST:@192.168.0.1/share"'}
    target, best = None, -1
    for g in groups[:40]:
        for sub in ("file", "photo", "video"):
            d = SMB_ROOT / g / sub
            if d.is_dir():
                target = d
                break
        if target is not None:
            break
    if target is None:
        target = SMB_ROOT
    t0 = time.time()
    try:
        count = len(os.listdir(target))
    except OSError as e:
        return {"state": "error", "detail": str(e)}
    elapsed = round(time.time() - t0, 2)
    result = {"state": "ok" if elapsed <= SMB_SLOW_SECONDS else "degraded",
              "listdir_seconds": elapsed, "entries": count, "path": str(target)}
    if result["state"] == "degraded":
        result["hint"] = (
            "SMB 会话退化。修复三步："
            "1) 写 ~/Library/Preferences/nsmb.conf："
            "[default] dir_cache_max=300 dir_cache_min=240 max_dirs_cached=512 "
            "notify_off=yes streams=no soft=yes；"
            "2) diskutil unmount force /Volumes/share && "
            'open "smb://GUEST:@192.168.0.1/share" && sleep 12；'
            "3) 用 sample 查是否有进程阻塞在 stat，有就杀掉。")
        log(f"⚠ SMB 健康自检 degraded: listdir {count} 项耗时 {elapsed}s（阈值 {SMB_SLOW_SECONDS}s）")
        log(f"  {result['hint']}")
    else:
        log(f"SMB 健康自检 ok: listdir {count} 项 {elapsed}s")
    return result


# Owner 明确说过「不管」的群（2026-08-16 原话：台泥贵港、生产付款、生产周例会不管）。
# 单独列出来，动态枚举时归入「已排除」而不是「新增待确认」，避免每轮都重复问一遍。
# 要重新纳入就把群名从这里删掉，或显式 --allow-title 传进归档器。
DECLINED_TITLES = {
    "台泥(贵港)",
    "生产付款群",
    "生产周例会工作群",
}


def discover_groups(existing: list[str]) -> tuple[list[str], list[str]]:
    """dws 实时枚举 ∪ groups-file，返回 (合并名单, 新增群)。

    静态白名单会漏群：实测旧名单 26 个，dws 实时 30 个 —— 台泥(贵港)、生产付款群、
    生产周例会工作群三个新群一直没进过归档。新增群只报不自动收，
    要显式 --include-new-groups 才纳入本轮。
    """
    result = ARCHIVER.dws_json(["chat", "list-all-conversations"])
    live: list[str] = []
    for c in result.get("conversations") or []:
        if c.get("singleChat") is not False:
            continue
        title = str(c.get("title") or "").strip()
        if not title:
            continue
        if c.get("groupType") == "INTERNAL_GROUP" or title in ARCHIVER.AUTHORIZED_NON_INTERNAL_TITLES:
            live.append(title)
    known = set(existing)
    candidates = [t for t in dict.fromkeys(live) if t not in known]
    declined = [t for t in candidates if t in DECLINED_TITLES]
    new = [t for t in candidates if t not in DECLINED_TITLES]
    if declined:
        log(f"动态群名单：{len(declined)} 个群按 Owner 既往决定排除，不计入新增: {declined}")
    return list(dict.fromkeys(existing + new)), new


# ---------- 阶段一：扫描 + 增量归档 + 消息上下文 ----------

def stage_scan(args, ctx) -> dict:
    stats = {"archived": 0, "existing": 0, "unavailable": 0, "context_msgs": 0, "skipped_groups": []}
    start = args.start or (now_sh() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    # 1) 增量归档：显式白名单逐个传入（复用既有语义），DWS 瞬断重试 3 次
    for g in ctx["groups"]:
        saved = False
        for attempt in range(3):
            r = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "archive_internal_media.py"),
                 "--allow-title", g, "--start", start, "--workers", "4", "--apply",
                 *(["--since-manifest"] if getattr(args, "since_manifest", False) else [])],
                capture_output=True, text=True, timeout=7200)
            tail = (r.stdout or "").strip().splitlines()
            fin = [l for l in tail if "run_finished" in l]
            if fin:
                try:
                    ev = json.loads(fin[-1])
                    stats["archived"] += int(ev.get("smb_saved", 0) or 0)
                    # 幂等重跑时 smb_saved=0 是正常的（文件已在），不能当成失败。
                    # 分成「新增 / 已存在 / 钉钉侧已删」三个口径，避免 archived=0 被误读。
                    stats["existing"] += int(ev.get("skipped", 0) or 0)
                    stats["unavailable"] += int(ev.get("unavailable", 0) or 0)
                    if ev.get("failures"):
                        stats["skipped_groups"].append((g, "failures>0"))
                except Exception:
                    pass
                saved = True
                break
            if attempt < 2:
                time.sleep(30)
        if not saved:
            stats["skipped_groups"].append((g, "archive no run_finished"))
    # 2) 消息上下文捕获（只读 DWS，用于本地语义标注）
    ctx_file = ctx["workdir"] / "context.jsonl"
    seen = set()
    if ctx_file.exists():
        seen = {json.loads(l)["key"] for l in ctx_file.read_text(encoding="utf-8").splitlines() if l.strip()}
    with ctx_file.open("a", encoding="utf-8") as f:
        for g in ctx["groups"]:
            msgs = None
            for attempt in range(3):
                try:
                    convs = aim.select_groups([g])
                    if not convs:
                        stats["skipped_groups"].append((g, "group not found"))
                        break
                    conv = convs[0]
                    t_end = now_sh()
                    t_start = parse_ctx_start(ctx, g, t_end)
                    raw = list(aim.walk_window_messages(conv.conversation_id, t_start, t_end,
                                                        None, args.page_size))
                    msgs = sorted(((aim.parse_time(str(m.get("createTime"))), m) for m in raw),
                                  key=lambda x: x[0])
                    break
                except Exception as e:
                    if attempt < 2:
                        log(f"  scan {g} attempt {attempt+1} fail: {str(e)[:100]}; retry in 30s")
                        time.sleep(30)
                    else:
                        stats["skipped_groups"].append((g, f"walk fail: {str(e)[:80]}"))
                        msgs = None
                        break
            if msgs is None:
                continue
            from bisect import bisect_left, bisect_right
            times = [ts for ts, _ in msgs]
            # 每条媒体消息用二分定位 ±30 分钟窗口，避免 O(n²)
            for idx, (ts, m) in enumerate(msgs):
                content = str(m.get("content") or "")
                rids = MEDIA_ID_RE.findall(content)
                if not rids:
                    continue
                lo = bisect_left(times, ts - timedelta(seconds=1800))
                hi = bisect_right(times, ts + timedelta(seconds=1800))
                ctx_texts = []
                for j in range(max(lo, 0), min(hi, len(msgs))):
                    if j == idx:
                        continue
                    ts2, m2 = msgs[j]
                    c2 = str(m2.get("content") or "").strip()
                    if not c2 or MEDIA_ID_RE.search(c2) or c2.startswith("["):
                        continue
                    ctx_texts.append((ts2, c2[:120]))
                if not ctx_texts:
                    continue
                before = " | ".join(c for _, c in ctx_texts if _ <= ts)[-200:]
                after = " | ".join(c for _, c in ctx_texts if _ > ts)[-100:]
                for rid in rids:
                    key = f"{g}\t{rid}"
                    if key in seen:
                        continue
                    seen.add(key)
                    f.write(json.dumps({"key": key, "group": g, "resource_id": rid,
                                        "time": str(ts), "before": before, "after": after},
                                       ensure_ascii=False) + "\n")
                    stats["context_msgs"] += 1
    log(f"scan done: 新增={stats['archived']} 已存在={stats['existing']} "
        f"钉钉侧已删={stats['unavailable']} context={stats['context_msgs']} "
        f"skipped={stats['skipped_groups']}")
    return stats


def parse_ctx_start(ctx, group: str, t_end: datetime) -> datetime:
    """上下文捕获起点：该群 manifest 最早 media 时间再往前 1 天。"""
    mf = SMB_ROOT / group / MANIFEST
    earliest = None
    if mf.exists():
        for line in mf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            mt = str(d.get("message_time") or "")[:19]
            if mt and (earliest is None or mt < earliest):
                earliest = mt
    if earliest:
        try:
            return datetime.strptime(earliest, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TIMEZONE) - timedelta(days=1)
        except ValueError:
            pass
    return t_end - timedelta(days=90)


MAP_COLS = ["项目", "原文件名", "新文件名", "日期", "大小"]


def load_ledger() -> dict:
    """读 `原名新名映射.csv` 改名账本 —— 「现用名」的唯一权威。

    `.manifest.jsonl` 永远记原名（硬约束 2），登记表可能还没回填，
    所以改名成功那一刻就必须落账；否则归档器/audit 会把已改名的素材当缺失。
    """
    ledger = {}
    if not MAP_CSV.exists():
        return ledger
    try:
        with MAP_CSV.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                folder = str(row.get("项目") or "").strip()
                old = str(row.get("原文件名") or "").strip()
                if folder and old:
                    ledger[(folder, old)] = {k: str(row.get(k) or "") for k in MAP_COLS}
    except (OSError, csv.Error):
        return {}
    return ledger


def save_ledger(ledger: dict) -> None:
    rows = [ledger[k] for k in sorted(ledger)]
    tmp = Path(tempfile.gettempdir()) / "原名新名映射.ledger.csv"
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=MAP_COLS)
    w.writeheader()
    w.writerows({k: r.get(k, "") for k in MAP_COLS} for r in rows)
    tmp.write_text("\ufeff" + buf.getvalue(), encoding="utf-8")
    rsync_write(tmp, MAP_CSV)


def reconcile_ledger(groups: list[str]) -> dict:
    """账本自愈：磁盘已改名、账本却还记着旧名的记录，按「同大小且唯一」认回来。

    为什么必须有这条路径：改名的幂等闸都以「原名还在磁盘上」为前提，一旦账本写丢
    （进程被杀、SMB 写失败、跨版本运行），rename 会因为原名已不在而永远跳过，
    账本再也回不来 —— 表现就是 audit / accept 一直报 missing，而磁盘上素材好好的。

    媒体的 manifest 里没有 md5（文件版有），所以判据是「同 media_type 目录内、
    字节数完全相同、且没有被别的记录认领」的唯一候选。有歧义就不认，留给人工。
    """
    ledger = load_ledger()
    repaired, ambiguous = [], []
    by_group = defaultdict(list)
    for m in load_media(groups):
        if m.get("smb_status") == "complete":
            by_group[m["_group"]].append(m)
    for group, records in by_group.items():
        for media_type in ("photo", "video"):
            directory = SMB_ROOT / group / media_type
            if not directory.is_dir():
                continue
            subset = [m for m in records if m.get("media_type") == media_type]
            if not subset:
                continue
            names = [n for n in os.listdir(directory) if not n.startswith("._")]
            claimed = {(ledger.get((group, os.path.basename(r.get("relative_path") or ""))) or {}).get("新文件名")
                       for r in subset}
            claimed.discard(None)
            by_size = defaultdict(list)
            for n in names:
                try:
                    by_size[(directory / n).stat().st_size].append(n)
                except OSError:
                    continue
            for m in subset:
                old_name = os.path.basename(m.get("relative_path") or "")
                if aim.resolve_current_path(m) is not None:
                    continue
                candidates = [n for n in by_size.get(int(m.get("size_bytes") or -1), [])
                              if n != old_name and n not in claimed]
                if len(candidates) == 1:
                    hit = candidates[0]
                    ledger[(group, old_name)] = {
                        "项目": group, "原文件名": old_name, "新文件名": hit,
                        "日期": str(m.get("message_time") or "")[2:10].replace("-", ""),
                        "大小": str(m.get("size_bytes") or ""),
                    }
                    claimed.add(hit)
                    repaired.append(f"{group}/{old_name} → {hit}")
                elif candidates:
                    ambiguous.append(f"{group}/{old_name} ?= {candidates[:3]}")
    if repaired:
        save_ledger(ledger)
        log(f"账本自愈: 认回 {len(repaired)} 条 —— {repaired[:3]}")
    if ambiguous:
        log(f"账本自愈: {len(ambiguous)} 条同大小多候选，不猜，留给人工 —— {ambiguous[:3]}")
    return {"repaired": len(repaired), "ambiguous": len(ambiguous)}


# ---------- 阶段二：规格探测 ----------

def stage_probe(args, ctx) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    healed = reconcile_ledger(ctx["groups"])
    specs = {}
    pf = ctx["workdir"] / "specs.jsonl"
    if pf.exists():
        specs = {json.loads(l)["file"]: json.loads(l) for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()}
    media = [m for m in load_media(ctx["groups"]) if m.get("smb_status") == "complete"]
    done = 0
    lock = threading.Lock()

    def probe_one(m):
        nonlocal done
        rel = m.get("relative_path") or ""
        name = os.path.basename(rel)
        if name in specs:
            return
        p = aim.resolve_current_path(m) or (SMB_ROOT / rel)
        if not p.exists():
            return
        if m.get("media_type") == "video":
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                                "-show_format", "-show_streams", str(p)],
                               capture_output=True, text=True, timeout=120)
            d = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
            vs = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
            audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
            dur = float(d.get("format", {}).get("duration") or vs.get("duration") or 0)
            fps = vs.get("avg_frame_rate") or vs.get("r_frame_rate") or ""
            try:
                num, den = fps.split("/")
                fps_s = round(int(num) / int(den), 1) if int(den) else 0
            except Exception:
                fps_s = 0
            rec = {"file": name, "media_type": "video", "duration": round(dur, 1),
                   "width": vs.get("width"), "height": vs.get("height"), "fps": fps_s,
                   "audio": audio, "size": p.stat().st_size}
        else:
            gps = False
            try:
                from PIL import Image
                ex = Image.open(p).getexif()
                gps = bool(ex and (ex.get(34853) or any(k.startswith("GPS") for k in ex)))
            except Exception:
                pass
            rec = {"file": name, "media_type": "photo", "duration": None,
                   "width": None, "height": None, "fps": None, "audio": None,
                   "gps": gps, "size": p.stat().st_size}
        rec["_group"] = m["_group"]
        rec["resource_id"] = m.get("resource_id")
        rec["message_id"] = m.get("message_id")
        specs[name] = rec
        with lock, pf.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            done += 1

    with ThreadPoolExecutor(max_workers=int(os.environ.get("PROBE_WORKERS", "8"))) as ex:
        list(ex.map(probe_one, media))
    log(f"probe done: new={done} total={len(specs)} 账本自愈={healed}")
    return {"probed": done, "total": len(specs), "ledger_healed": healed}


# ---------- 阶段二续：缩略图 + 感知哈希去重 ----------

def make_thumb(rel: str, media_type: str, dst: Path) -> bool:
    """视频 6 帧 3x2 拼图；照片单张缩放。宽 400，JPEG q85。"""
    from PIL import Image
    src = SMB_ROOT / rel
    if not src.exists():
        return False
    if media_type == "video":
        r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                            "-show_format", str(src)], capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else {}
        dur = float(d.get("format", {}).get("duration") or 0) or 5.0
        with tempfile.TemporaryDirectory(prefix="kf-") as td:
            frames = []
            for i in range(6):
                t = dur * (i + 0.5) / 6
                fp = os.path.join(td, f"f{i}.jpg")
                rr = subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(src),
                                     "-frames:v", "1", "-vf", "scale=400:-2", "-q:v", "4", fp],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
                if rr.returncode == 0 and os.path.exists(fp):
                    frames.append(Image.open(fp).convert("RGB"))
            if not frames:
                return False
            w = max(im.width for im in frames)
            canvas = Image.new("RGB", (w * 3, w * 2), (0, 0, 0))
            for i, im in enumerate(frames):
                x = (i % 3) * w + (w - im.width) // 2
                y = (i // 3) * w + (w - im.height) // 2
                canvas.paste(im, (x, y))
            canvas.save(dst, quality=85)
    else:
        try:
            with Image.open(src) as im:
                im = im.convert("RGB")
                im.thumbnail((400, 400))
                im.save(dst, quality=85)
        except Exception:
            return False
    return True


def stage_thumbs(args, ctx) -> dict:
    from PIL import Image
    from concurrent.futures import ThreadPoolExecutor
    out_dir = ctx["workdir"] / "thumbs"
    out_dir.mkdir(parents=True, exist_ok=True)
    SMB_THUMBS.mkdir(parents=True, exist_ok=True)
    media = [m for m in load_media(ctx["groups"]) if m.get("smb_status") == "complete"]
    made = skipped = 0
    lock = threading.Lock()

    def work(m):
        nonlocal made, skipped
        name = os.path.basename(m.get("relative_path") or "")
        stem = os.path.splitext(name)[0]
        local = out_dir / f"{stem}.jpg"
        if local.exists():
            with lock:
                skipped += 1
        elif make_thumb(m["relative_path"], m.get("media_type"), local):
            with lock:
                made += 1

    with ThreadPoolExecutor(max_workers=int(os.environ.get("THUMB_WORKERS", "8"))) as ex:
        list(ex.map(work, media))
    # rsync 到 SMB 缩略图区
    for p in out_dir.glob("*.jpg"):
        dst = SMB_THUMBS / p.name
        if not dst.exists() or dst.stat().st_size != p.stat().st_size:
            rsync_write(p, dst)
    log(f"thumbs done: made={made} local_total={len(list(out_dir.glob('*.jpg')))}")
    return {"made": made}


def ahash(path: Path, size: int = 16) -> int:
    from PIL import Image
    im = Image.open(path).convert("L").resize((size, size))
    px = list(im.getdata())
    avg = sum(px) / len(px)
    return sum((1 << i) for i, v in enumerate(px) if v > avg)


def stage_dedup(args, ctx) -> dict:
    out = ctx["workdir"] / "dups.jsonl"
    media = [m for m in load_media(ctx["groups"]) if m.get("smb_status") == "complete"]
    hashes = {}
    thumbs_dir = ctx["workdir"] / "thumbs"
    for m in media:
        stem = os.path.splitext(os.path.basename(m.get("relative_path") or ""))[0]
        p = thumbs_dir / f"{stem}.jpg"
        if p.exists():
            try:
                hashes[m["relative_path"]] = ahash(p)
            except Exception:
                pass
    groups_done = defaultdict(list)
    for rel, h in hashes.items():
        groups_done[h].append(rel)
    dups = {rel: keep for h, rels in groups_done.items() if len(rels) > 1
            for rel, keep in ((r, rels[0]) for r in rels if r != rels[0])}
    with out.open("w", encoding="utf-8") as f:
        for rel, keep in dups.items():
            f.write(json.dumps({"file": rel, "重复于": os.path.basename(keep)}, ensure_ascii=False) + "\n")
    log(f"dedup done: {len(dups)} duplicates of {len(hashes)} hashed")
    return {"hashed": len(hashes), "dups": len(dups)}


# ---------- 阶段三：本地标注（无外部 agent） ----------

def kw_label(text: str):
    """关键词 → (说明, 工序阶段, 功能位, 画面元素)。"""
    for kw, desc, stage, func, elems in KEYWORDS:
        if kw in text:
            return desc, stage, func, elems
    return None


VISION_DOMAIN = (
    "这是水泥/钢铁行业【回转窑在线车磨削检修】现场素材的多帧拼图。常见对象："
    "回转窑筒体（大直径卧式旋转筒）、轮带（套在筒体外的厚钢环，是加工对象）、"
    "托轮（支撑轮带的小轮）、挡块、车刀架与刀头（贴在轮带外圆切削）、"
    "百分表（测轮带跳动与复检精度）、钢直尺（横搭在轮带面上量磨损凹陷间隙）。"
    "画面里的大圆筒是回转窑筒体，不是管道；量具贴在轮带面上是量磨损量，不是量直径。"
)

# 脱敏必须宁可多标：漏标一次客户名 = 对外泄露；多标一次 = 人工复核 30 秒。
# 实测教训：把规则收紧成「只有确实看见才标」后，写着企业名的 LED 屏反而不再被标出。
VISION_DESENS = (
    "【脱敏风险·宁可多标不可漏标】画面中只要出现任何文字牌、显示屏、横幅、水印、"
    "证件、车辆，就必须先在「可见文字」里逐字抄出，再判断风险。"
    "文字里含任何企业/工厂/公司名称 → 标 客户名称；"
    "出现可辨认人物面部 → 标 人脸；出现打卡类应用浮层 → 标 打卡应用水印；"
    "出现具体地址或经纬度 → 标 精确地理位置；出现车牌号 → 标 车牌。"
    "拿不准时一律标出，不要因为不确定而填 无。"
)

# 功能位是叙事判断，不是画面识别。实测 gpt-4o 三轮准确率仅 33–40%，
# 因此只作为「建议值」写入，置信度一律「待确认」，由抽样复核定案，不得直接参与改名。
VISION_SLOTS = (
    "【功能位·只给建议值】"
    "开场证据=展示问题存在或损坏程度（量具贴在磨损面上露出缝隙、可见凹陷剥落）；"
    "过程证据=正在施加加工动作且看得见作用（刀尖吃刀、切屑飞出、火花）；"
    "关键细节=看得清工艺分界或成品特征（已加工亮面与未加工黑面的分界、整圈镜面带）；"
    "验收闭环=用量具证明做完且合格（百分表在转动中读数稳定）；"
    "环境铺垫=人员、厂区、标牌、班前会等非工艺画面；不可用=糊、黑、无内容。"
)

VISION_PROMPT = (
    VISION_DOMAIN + VISION_SLOTS + VISION_DESENS +
    "这是一张工业设备维修现场素材接触表的缩略图。"
    "只输出一个 JSON 对象，不要任何其他文字，字段如下："
    "{\"可见文字\":\"逐字抄出画面中所有文字，无则填 无\",\"描述\":\"2-6字中文内容描述\",\"功能位\":\"开场证据|过程证据|关键细节|验收闭环|环境铺垫|不可用\","
    "\"画质等级\":\"可全屏|仅可内嵌|不可用\","
    "\"画面元素\":\"火花、刀具、量具、人员、轮带、托轮、齿轮、筒体、表盘、焊接、吊装、厂区、文字牌、切屑、加工纹面、磨损面 中多选顿号分隔，无则填 无\","
    "\"镜头特征\":\"大特写、中景、全景、运动镜头、固定机位、强对比、逆光、手持抖动 中多选顿号分隔\","
    "\"工序阶段\":\"测量|拆解|加工|焊接|复检|收尾|无法判断\","
    "\"能证明什么\":\"一句话，必须能接在“这段画面证明了____”后面读得通，填不出则填 无法判断\","
    "\"脱敏风险\":\"客户名称、人脸、打卡应用水印、精确地理位置、车牌、安全告示牌 中多选顿号分隔，无则填 无\"}"
)


def minimax_vision(thumb: Path, attempts: int = 3) -> dict | None:
    """单轮无状态视觉调用：一张拼图 → JSON → 结束（禁止 agent 会话）。

    配置来自环境变量 MINIMAX_API_BASE / MINIMAX_API_KEY / MINIMAX_MODEL。
    网络瞬断重试 attempts 次；仍未配置或全部失败返回 None（调用方回退关键词并把置信度标「待确认」）。
    """
    import base64
    import urllib.request
    base = os.environ.get("MINIMAX_API_BASE", "").strip()
    key = os.environ.get("MINIMAX_API_KEY", "").strip()
    model = os.environ.get("MINIMAX_MODEL", "").strip()
    if not (base and key and model) or not thumb.exists():
        return None
    b64 = base64.b64encode(thumb.read_bytes()).decode()
    payload = {
        "model": model,
        "max_tokens": 800,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    }
    for _ in range(max(1, attempts)):
        req = urllib.request.Request(
            f"{base.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except Exception:
            time.sleep(2)
            continue
        text = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
        s, e = text.find("{"), text.rfind("}")
        if s == -1 or e == -1:
            continue
        try:
            obj = json.loads(text[s:e + 1])
        except Exception:
            continue
        if not obj.get("描述"):
            continue
        return obj
    return None


# 泛化标签黑名单：模型把接触表格式当成画面内容时输出这类词，不能进文件名
GENERIC_REJECT = ("多帧", "拼图", "工业场景", "设备维修画面", "工业设备维修", "工业设备维护",
                  "现场多帧", "磨削现场", "多帧图片", "工业设备", "设备维修", "现场维修")


def reject_generic(note: str) -> bool:
    return any(k in note for k in GENERIC_REJECT)


def stage_label(args, ctx) -> dict:
    """合并：MiniMax 视觉（单轮 API）→ 关键词兜底 → EXIF → 分辨率画质。"""
    media = [m for m in load_media(ctx["groups"]) if m.get("smb_status") == "complete"]
    ctx_map = {}
    cf = ctx["workdir"] / "context.jsonl"
    if cf.exists():
        for l in cf.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            ctx_map[(d["group"], d["resource_id"])] = d
    specs = {}
    sf = ctx["workdir"] / "specs.jsonl"
    if sf.exists():
        specs = {json.loads(l)["file"]: json.loads(l) for l in sf.read_text(encoding="utf-8").splitlines() if l.strip()}
    dups = {}
    df = ctx["workdir"] / "dups.jsonl"
    if df.exists():
        dups = {json.loads(l)["file"]: json.loads(l)["重复于"] for l in df.read_text(encoding="utf-8").splitlines() if l.strip()}
    override = {}
    ovf = ctx["workdir"] / "vision_override.jsonl"
    if ovf.exists():
        for l in ovf.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            override[d["file"]] = d
    thumbs_dir = ctx["workdir"] / "thumbs"
    # 跳过已标注（登记表已有描述且置信度高）：照片全量重跑时避免重复付费
    reg_desc = {}
    if REG_CSV.exists():
        for rr in csv.DictReader(REG_CSV.open(encoding="utf-8-sig")):
            if (rr.get("描述") or "").strip() and (rr.get("置信度") or "") != "待确认":
                reg_desc[(rr["项目"], rr["原文件名"])] = True
    rows = []
    labeled = pending = 0
    vision_ok = vision_fail = 0
    lock = threading.Lock()

    def process_one(m):
        nonlocal labeled, pending, vision_ok, vision_fail
        name = os.path.basename(m.get("relative_path") or "")
        if (m["_group"], name) in reg_desc:
            return None  # 已有标注，跳过（不重标不重付费）
        s = specs.get(name, {})
        ov = override.get(name, {})
        c = ctx_map.get((m["_group"], m.get("resource_id")), {})
        text = f"{c.get('before','')} {c.get('after','')}"
        hit = kw_label(text)
        vision = None
        thumb = thumbs_dir / f"{os.path.splitext(name)[0]}.jpg"
        if thumb.exists():
            vision = minimax_vision(thumb)
            with lock:
                if vision is not None:
                    vision_ok += 1
                else:
                    vision_fail += 1
        if vision and (not vision.get("描述") or reject_generic(str(vision["描述"]))):
            # 泛化标签（“多帧拼图”等）不可信，视作未标注
            vision = None
        if ov.get("描述"):
            desc = ov["描述"]
        elif vision and vision.get("描述"):
            desc = str(vision["描述"]).strip()
        elif hit:
            desc = hit[0]
        else:
            desc = ""
        if not desc or len(desc) > 6:
            # 说明必须 2-6 字：超长/空一律待确认（不污染文件名）
            desc = "待确认"
        # 置信度：视觉/人工覆盖=高；关键词兜底与无信号=待确认（兜底不可信）
        conf = "高" if (ov or vision) else "待确认"
        row = {
            "项目": m["_group"], "原文件名": name,
            "relative_path": m.get("relative_path"), "media_type": m.get("media_type"),
            "说明": desc, "置信度": conf,
        }
        if ov:
            src = ov
        elif vision:
            src = vision
        elif hit:
            src = {"工序阶段": hit[1], "功能位": hit[2], "画面元素": hit[3],
                   "镜头特征": "", "能证明什么": (c.get("before") or c.get("after") or "").strip()[:60],
                   "脱敏风险": desens_risk(text)}
            if not src["能证明什么"]:
                src["功能位"] = "不可用"
        else:
            src = {"功能位": "不可用", "工序阶段": "无法判断", "画面元素": "无",
                   "镜头特征": "", "能证明什么": "", "脱敏风险": desens_risk(text)}
        for k in ("功能位", "画质等级", "画面元素", "镜头特征", "工序阶段", "能证明什么", "脱敏风险"):
            row[k] = src.get(k, "")
        # 枚举消毒：未知词丢弃；功能位/工序阶段非法→不可用/无法判断；镜头特征空→""
        for fld in ("画面元素", "镜头特征", "脱敏风险"):
            vals = [x.strip() for x in str(row.get(fld, "")).replace("、", ",").split(",") if x.strip()]
            keep = [v for v in vals if v in VOCAB[fld]]
            if not keep:
                keep = ["无"] if fld == "画面元素" else [""]
            row[fld] = "、".join(dict.fromkeys(keep))
        if str(row.get("功能位", "")) not in VOCAB["功能位"]:
            row["功能位"] = "不可用"
        if str(row.get("工序阶段", "")) not in VOCAB["工序阶段"]:
            row["工序阶段"] = "无法判断"
        with lock:
            if ov or vision:
                labeled += 1
            else:
                pending += 1
        # 画质等级：分辨率硬信息
        if row.get("画质等级") not in ("可全屏", "仅可内嵌", "不可用"):
            w, h = (s.get("width") or 0), (s.get("height") or 0)
            if m.get("media_type") == "video" and w and h:
                row["画质等级"] = "可全屏" if min(w, h) >= 720 else "仅可内嵌"
            else:
                row["画质等级"] = ""
        # 脱敏：EXIF GPS
        if s.get("gps") and "精确地理位置" not in str(row.get("脱敏风险", "")):
            row["脱敏风险"] = "、".join(x for x in [row.get("脱敏风险") or "", "精确地理位置"] if x and x != "无")
        if not row.get("脱敏风险"):
            row["脱敏风险"] = "无"
        row["重复于"] = dups.get(m.get("relative_path"), "无")
        if ov:
            row["标注执行者"] = "claude-code-cli"
        elif vision:
            row["标注执行者"] = "minimax-hub"
        else:
            row["标注执行者"] = "pipeline-local"
        row["标注日期"] = "260817"
        return row

    workers = int(os.environ.get("LABEL_WORKERS", "8"))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(process_one, media))
    rows = [r for r in results if r is not None]
    skipped = sum(1 for r in results if r is None)
    out = ctx["workdir"] / "desc.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["项目", "原文件名", "relative_path", "media_type",
                                          "说明", "置信度", "功能位", "画质等级", "画面元素",
                                          "镜头特征", "工序阶段", "能证明什么", "脱敏风险",
                                          "重复于", "标注执行者", "标注日期"])
        w.writeheader()
        w.writerows(rows)
    log(f"label done: total={len(rows)} skipped={skipped} labeled={labeled} pending={pending} "
        f"vision_ok={vision_ok} vision_fail={vision_fail}")
    return {"total": len(rows), "skipped": skipped, "labeled": labeled, "pending": pending,
            "vision_ok": vision_ok, "vision_fail": vision_fail}


def desens_risk(text: str) -> str:
    risks = []
    for risk, kws in DESENS_RISK_KW.items():
        if any(k in text for k in kws):
            risks.append(risk)
    return "、".join(risks) if risks else "无"


# ---------- 阶段四：幂等改名 ----------

def stage_rename(args, ctx) -> dict:
    desc = {}
    df = ctx["workdir"] / "desc.csv"
    if df.exists():
        desc = {(r["项目"], r["原文件名"]): r for r in csv.DictReader(df.open(encoding="utf-8-sig"))}
    # 已有登记表：已改名（文件名 != 原文件名）的跳过，避免二次改名
    renamed_set = set()
    if REG_CSV.exists():
        for r in csv.DictReader(REG_CSV.open(encoding="utf-8-sig")):
            if r.get("文件名") and r.get("原文件名") and r["文件名"] != r["原文件名"]:
                renamed_set.add((r["项目"], r["原文件名"]))
    ops = []
    photo_counters = defaultdict(int)
    for m in load_media(ctx["groups"]):
        key = (m["_group"], os.path.basename(m.get("relative_path") or ""))
        if key in renamed_set:
            continue
        d = desc.get(key)
        note = (d.get("说明") or "").strip() if d else ""
        if not note or note == "待确认":
            continue  # 保留原名，待终审
        biz = BUSINESS.get(m["_group"], "")
        rel = m.get("relative_path") or ""
        old_name = os.path.basename(rel)
        stem = os.path.splitext(old_name)[0]
        ext = os.path.splitext(old_name)[1]
        mt = str(m.get("message_time") or "")[:10]
        date = mt[2:4] + mt[5:7] + mt[8:10] if len(mt) == 10 else ""
        if m.get("media_type") == "video":
            new_name = f"{biz}_{note}_{stem}{ext}"  # 序号沿用原两位
        elif re.fullmatch(r"\d{6}_\d{3}", stem):
            new_name = f"{biz}_{note}_{stem}{ext}"  # 老格式带日期序号：沿用
        else:
            photo_counters[(biz, note, date)] += 1
            new_name = f"{biz}_{note}_{date}_{photo_counters[(biz, note, date)]:03d}{ext}"
        if new_name == old_name:
            continue
        ops.append((rel, new_name, note))
    # 冲突检查
    seen = Counter()
    for _, nn, _ in ops:
        seen[nn] += 1
    conflicts = {k: v for k, v in seen.items() if v > 1}
    if conflicts:
        log(f"name conflicts {len(conflicts)} — 这些保持原名: {list(conflicts)[:5]}")
        ops = [o for o in ops if seen[o[1]] == 1]
    ledger = load_ledger()
    # 账本幂等闸：账本已记新名、且该新名确实在磁盘上 → 这份早就改过了，绝不再改一次
    kept = []
    for op in ops:
        rel = op[0]
        folder, old_name = rel.split("/")[0], os.path.basename(rel)
        mapped = (ledger.get((folder, old_name)) or {}).get("新文件名", "")
        if mapped and mapped != old_name and (SMB_ROOT / rel).parent.joinpath(mapped).is_file():
            continue
        kept.append(op)
    ops = kept
    ok = gone = fail = 0
    done_ops = []
    for rel, nn, _ in ops:
        old_p = SMB_ROOT / rel
        new_p = old_p.parent / nn
        last = None
        for attempt in range(3):
            try:
                os.rename(old_p, new_p)
                ok += 1
                done_ops.append((rel, nn))
                last = None
                break
            except FileNotFoundError:
                gone += 1
                last = None
                break
            except OSError as e:
                last = e   # SMB rename 实测会随机 EIO，重试而不是直接判失败
                time.sleep(2 ** attempt)
        if last is not None:
            fail += 1
            log(f"rename fail {rel}: {last}")
    # 改名成功即刻落账本，不等 registry —— 中途中断也不会留下「磁盘已改、账本没记」的黑洞
    if done_ops:
        for rel, nn in done_ops:
            folder = rel.split("/")[0]
            old_name = os.path.basename(rel)
            prev = ledger.get((folder, old_name)) or {}
            ledger[(folder, old_name)] = {
                "项目": folder, "原文件名": old_name, "新文件名": nn,
                "日期": prev.get("日期", ""), "大小": prev.get("大小", ""),
            }
        save_ledger(ledger)
    # 对照表
    cmp = ctx["workdir"] / "改名前后对照.csv"
    with cmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["项目", "原文件名", "新文件名", "说明"])
        w.writeheader()
        for rel, nn, note in ops:
            w.writerow({"项目": rel.split("/")[0], "原文件名": os.path.basename(rel),
                        "新文件名": nn, "说明": note})
    log(f"rename done: ops={len(ops)} ok={ok} gone={gone} fail={fail}")
    return {"ops": len(ops), "ok": ok, "gone": gone, "fail": fail}


# ---------- 阶段五：登记表双格式 + 三处落地 ----------

def stage_registry(args, ctx) -> dict:
    desc = {}
    df = ctx["workdir"] / "desc.csv"
    if df.exists():
        desc = {(r["项目"], r["原文件名"]): r for r in csv.DictReader(df.open(encoding="utf-8-sig"))}
    specs = {}
    sf = ctx["workdir"] / "specs.jsonl"
    if sf.exists():
        specs = {json.loads(l)["file"]: json.loads(l) for l in sf.read_text(encoding="utf-8").splitlines() if l.strip()}
    # 现有登记表（可能已含新列）
    reg_rows, fieldnames = [], []
    if REG_CSV.exists():
        reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig")))
        fieldnames = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig")).fieldnames)
    else:
        fieldnames = ["项目", "文件名", "日期", "原文件名", "大小", "描述", "置信度"]
        for m in load_media(ctx["groups"]):
            name = os.path.basename(m.get("relative_path") or "")
            mt = str(m.get("message_time") or "")[:10]
            reg_rows.append({"项目": m["_group"], "文件名": name, "日期": mt[2:4]+mt[5:7]+mt[8:10],
                             "原文件名": name, "大小": m.get("size_bytes", ""), "描述": "", "置信度": ""})
    fieldnames = list(fieldnames) + [c for c in NEW_COLS if c not in fieldnames]
    bykey = {(r["项目"], r["原文件名"]): r for r in reg_rows}
    updated = 0

    # 目录级清单缓存（一次 listdir，避免逐文件 stat 拖垮 SMB）
    dir_cache: dict[tuple[str, str], set[str]] = {}

    def names_in(group: str, sub: str) -> set[str]:
        key = (group, sub)
        if key not in dir_cache:
            d = SMB_ROOT / group / sub
            dir_cache[key] = set(os.listdir(d)) if d.is_dir() else set()
        return dir_cache[key]

    # 磁盘新名回填
    for m in load_media(ctx["groups"]):
        key = (m["_group"], os.path.basename(m.get("relative_path") or ""))
        r = bykey.get(key)
        if not r:
            continue
        rel = m.get("relative_path") or ""
        old_name = os.path.basename(rel)
        d = desc.get(key)
        note = (d.get("说明") or "").strip() if d else ""
        s = specs.get(old_name, {})
        # 文件名同步（磁盘真相）：登记表文件名列与磁盘现状对齐（目录级缓存）
        sub = rel.split("/")[1] if len(rel.split("/")) > 1 else "photo"
        names = names_in(m["_group"], sub)
        cur_name = r.get("文件名") or old_name
        if cur_name != old_name:
            if old_name not in names and cur_name in names:
                pass  # 磁盘确已改名，保持
            elif old_name in names and cur_name not in names:
                r["文件名"] = old_name  # 磁盘已回退，登记表跟随
        elif note and note != "待确认" and old_name not in names:
            # 登记表仍为旧名、磁盘已按 rename 规则改名时回填新名
            stem = os.path.splitext(old_name)[0]
            ext = os.path.splitext(old_name)[1]
            if s.get("media_type") == "video":
                cand = f"{BUSINESS.get(m['_group'],'')}_{note}_{stem}{ext}"
            elif re.fullmatch(r"\d{6}_\d{3}", stem):
                cand = f"{BUSINESS.get(m['_group'],'')}_{note}_{stem}{ext}"
            else:
                cand = None
            if cand and cand in names:
                r["文件名"] = cand
        for k in NEW_COLS:
            r.setdefault(k, "")
        if s.get("media_type") == "video":
            r["时长秒"] = str(s.get("duration") or "")
            r["分辨率"] = f'{s.get("width")}x{s.get("height")}' if s.get("width") else ""
            r["帧率"] = str(s.get("fps") or "")
            r["有无音轨"] = "有" if s.get("audio") else "无"
        if d:
            r["重复于"] = d.get("重复于", "无")
            r["功能位"] = d.get("功能位", "")
            r["画质等级"] = d.get("画质等级", "")
            r["画面元素"] = d.get("画面元素", "")
            r["镜头特征"] = d.get("镜头特征", "")
            r["工序阶段"] = d.get("工序阶段", "")
            r["能证明什么"] = d.get("能证明什么", "")
            r["脱敏风险"] = d.get("脱敏风险", "")
            r["缩略图路径"] = f"assets/thumbs/{os.path.splitext(old_name)[0]}.jpg"
            r["标注执行者"] = d.get("标注执行者", "")
            r["标注日期"] = d.get("标注日期", "")
            r["复核状态"] = r.get("复核状态") or "未复核"
            if (r.get("文件名") or "") != (r.get("原文件名") or ""):
                pass  # 已改名行（如 29 条打样）：描述保持，不覆盖重标
            elif note and note != "待确认":
                r["描述"] = note
                r["置信度"] = "高"
            elif (r.get("描述") or "").strip():
                # 回退行（改名被撤销）：清掉旧描述，置信度待确认
                r["描述"] = ""
                r["置信度"] = "待确认"
            updated += 1
    # 双格式写本地 → rsync SMB（约束7）
    tmp = ctx["workdir"] / "素材登记表.new.csv"
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in reg_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    rsync_write(tmp, REG_CSV)
    # 原名新名映射：与账本合并，**不得把已有新名覆盖回原名**
    ledger = load_ledger()
    for r in reg_rows:
        key = (r.get("项目", ""), r.get("原文件名", ""))
        prev = ledger.get(key) or {}
        current = str(r.get("文件名") or "").strip()
        if current == r.get("原文件名", ""):
            current = prev.get("新文件名") or current
        ledger[key] = {"项目": key[0], "原文件名": key[1], "新文件名": current or key[1],
                       "日期": r.get("日期", "") or prev.get("日期", ""),
                       "大小": str(r.get("大小", "") or prev.get("大小", ""))}
    save_ledger(ledger)
    # 分发副本（distribute_registry 会从 workdir 取）
    import io as _io
    _buf = _io.StringIO()
    _w = csv.DictWriter(_buf, fieldnames=MAP_COLS)
    _w.writeheader()
    _w.writerows({k: ledger[key].get(k, "") for k in MAP_COLS} for key in sorted(ledger))
    (ctx["workdir"] / "原名新名映射.new.csv").write_text("\ufeff" + _buf.getvalue(), encoding="utf-8")
    # 公开仓脱敏 md 版（项目名 → 业务名+群）
    pub_rows = []
    for r in reg_rows:
        biz = BUSINESS.get(r["项目"], "其他")
        rr = dict(r)
        rr["项目"] = f"{biz}群"
        rr.pop("能证明什么", None)
        pub_rows.append(rr)
    pub_cols = [c for c in fieldnames if c != "能证明什么"]
    tmp3 = ctx["workdir"] / "素材登记表_public.md"
    with tmp3.open("w", encoding="utf-8") as f:
        f.write("# 素材登记表（公开脱敏版）\n\n")
        f.write("| " + " | ".join(pub_cols) + " |\n")
        f.write("|" + "---|" * len(pub_cols) + "\n")
        for r in pub_rows:
            f.write("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in pub_cols) + " |\n")
    (ctx["workdir"] / "素材登记表_public.csv").write_text(
        "\ufeff" + csv_text(pub_rows, pub_cols), encoding="utf-8")
    # 视频子集（只含视频、精简列）——供 ChatGPT 等无本地权限的模型直接上传
    vid_rows = [{k: r.get(k, "") for k in VIDEO_SUBSET_COLS}
                for r in reg_rows if str(r.get("文件名", "")).lower().endswith((".mp4", ".mov"))]
    (ctx["workdir"] / "素材登记表_视频子集.csv").write_text(
        "﻿" + csv_text(vid_rows, VIDEO_SUBSET_COLS), encoding="utf-8")
    # 视频子集·公开脱敏版（项目名 → 业务名+群，去掉「能证明什么」）——只有这份能进 KMOS 公开仓
    pub_vid_cols = [c for c in VIDEO_SUBSET_COLS if c != "能证明什么"]
    pub_vid = []
    for r in reg_rows:
        if not str(r.get("文件名", "")).lower().endswith((".mp4", ".mov")):
            continue
        rr = {k: r.get(k, "") for k in pub_vid_cols}
        rr["项目"] = f"{BUSINESS.get(r['项目'], '其他')}群"
        pub_vid.append(rr)
    (ctx["workdir"] / "素材登记表_视频子集_public.csv").write_text(
        "﻿" + csv_text(pub_vid, pub_vid_cols), encoding="utf-8")
    # 分发到另外两个本机落点（SMB 已在上方 rsync 写入，是唯一真源）
    dist = distribute_registry(ctx)
    log(f"registry done: rows={len(reg_rows)} videos={len(vid_rows)} updated={updated} dist={dist}")
    return {"rows": len(reg_rows), "videos": len(vid_rows), "updated": updated, "dist": dist}


def distribute_registry(ctx) -> dict:
    """把登记表分发到三个本机落点。SMB 为唯一真源，另两处为只读副本。

    1. SMB        smb://192.168.0.1/.../KMVideo/            （已由 rsync_write 完成）
    2. 输出工作区  ~/Documents/KMVideo/00_治理与登记/02_登记与索引/
    3. 下载目录    ~/Downloads/                              （便于拖给 ChatGPT 上传）
    """
    wd = ctx["workdir"]
    plan = [
        (wd / "素材登记表.new.csv", DOCS_INDEX / "素材登记表.csv"),
        (wd / "原名新名映射.new.csv", DOCS_INDEX / "原名新名映射.csv"),
        (wd / "素材登记表_视频子集.csv", DOCS_INDEX / "素材登记表_视频子集.csv"),
        (wd / "素材登记表_public.csv", DOCS_INDEX / "素材登记表_public.csv"),
        (wd / "素材登记表_public.md", DOCS_INDEX / "素材登记表_public.md"),
        # Downloads 只放两份最常用的：全量表 + 可直接上传的视频子集
        (wd / "素材登记表.new.csv", DOWNLOADS / "KMVideo素材登记表.csv"),
        (wd / "素材登记表_视频子集.csv", DOWNLOADS / "KMVideo素材登记表_视频子集.csv"),
    ]
    ok, fail = 0, []
    for src, dst in plan:
        if not src.exists():
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            if dst.stat().st_size != src.stat().st_size:
                raise RuntimeError("size mismatch")
            ok += 1
        except OSError as e:
            fail.append(f"{dst}: {e}")
    if fail:
        # 分发失败不静默：本机副本缺失会让下游 agent 读到过期数据
        raise RuntimeError(f"登记表分发失败 {len(fail)} 处: {fail}")
    return {"copied": ok}


def csv_text(rows, cols) -> str:
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def stage_upload(args, ctx) -> dict:
    res = {}
    # 1) KMOS 公开仓（脱敏登记表 + 缩略图清单）
    kmos_data = Path(aim.ROOT) / "KMDatabase" / "data" / "KMVideo"
    kmos_data.mkdir(parents=True, exist_ok=True)
    for name in ("素材登记表_public.csv", "素材登记表_public.md",
                 "素材登记表_视频子集_public.csv"):
        src = ctx["workdir"] / name
        if src.exists():
            dst = kmos_data / name
            dst.write_bytes(src.read_bytes())
    thumbs = sorted((ctx["workdir"] / "thumbs").glob("*.jpg"))
    with (kmos_data / "缩略图清单.csv").open("w", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["文件名", "资产路径"])
        for t in thumbs:
            w.writerow([t.name, f"assets/thumbs/{t.name}"])
    res["kmos_files"] = len(list(kmos_data.glob("*")))
    # 2) GitHub Release 资产（有 gh 且配置 tag 才传，失败不阻塞）
    if args.release_tag and shutil_which("gh"):
        try:
            subprocess.run(["gh", "release", "view", args.release_tag], capture_output=True, timeout=60)
            for t in thumbs:
                subprocess.run(["gh", "release", "upload", args.release_tag, str(t), "--clobber"],
                               capture_output=True, timeout=300)
            res["release_assets"] = len(thumbs)
        except Exception as e:
            res["release_assets"] = f"skip: {e}"
    else:
        res["release_assets"] = "skip (no tag/gh)"
    # 3) Private-Database（完整登记表）
    if args.no_private:
        res["private"] = "skip"
    elif PRIVATE_CLIENT.exists():
        r = subprocess.run([sys.executable, str(PRIVATE_CLIENT), "ingest",
                            "Private-KMDatabase", str(REG_CSV), "--domain", "其他"],
                           capture_output=True, text=True, timeout=1800)
        res["private"] = "ok" if r.returncode == 0 else f"fail: {r.stderr[-150:]}"
    else:
        # 静默跳过 → 显式失败：否则自验收会误判通过
        raise RuntimeError(
            f"private_db_client.py 不存在：{PRIVATE_CLIENT}。"
            "请设置环境变量 KMOS_ROOT 指向 KMOS checkout（或在 KMOS worktree 内运行），"
            "或显式传 --no-private 声明本轮跳过私有仓落地。")
    log(f"upload done: {res}")
    return res


def shutil_which(x):
    import shutil
    return shutil.which(x)


# ---------- 阶段六：自验收 + 产能汇总 ----------

def stage_accept(args, ctx) -> dict:
    checks = {"pass": [], "fail": []}
    def chk(name, cond, detail=""):
        (checks["pass"] if cond else checks["fail"]).append({"项": name, "详情": detail})
    # 登记表完整性
    reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig"))) if REG_CSV.exists() else []
    chk("登记表可读且非空", len(reg_rows) > 0, str(len(reg_rows)))
    chk("无重复行(项目+原文件名)", len(reg_rows) == len({(r["项目"], r["原文件名"]) for r in reg_rows}))
    # 改名后文件名格式（仅对已改名的）
    bad_fmt = []
    for r in reg_rows:
        if r["文件名"] != r["原文件名"]:
            if not re.fullmatch(r".{2,5}_.{2,6}_\d{6}_\d{2,3}\.[A-Za-z0-9]{3,4}", r["文件名"]):
                bad_fmt.append(r["文件名"])
    chk("新文件名格式", not bad_fmt, str(bad_fmt[:5]))
    # 描述长度
    bad_desc = [r for r in reg_rows if r.get("描述") and not (2 <= len(r["描述"]) <= 6)]
    chk("描述 2-6 字", not bad_desc, str(bad_desc[:5]))
    # 枚举词汇
    bad_vocab = []
    for r in reg_rows:
        for fld, vocab in VOCAB.items():
            if fld not in r:
                continue
            for x in str(r[fld]).replace("、", ",").split(","):
                x = x.strip()
                if x and x not in vocab:
                    bad_vocab.append((r["原文件名"], fld, x))
    chk("枚举字段原始词汇", not bad_vocab, str(bad_vocab[:5]))
    # 画质等级与分辨率
    bad_q = []
    for r in reg_rows:
        if r.get("分辨率") and r.get("画质等级") in ("可全屏", "仅可内嵌"):
            m = re.match(r"(\d+)x(\d+)", r["分辨率"])
            if m:
                want = "可全屏" if min(int(m[1]), int(m[2])) >= 720 else "仅可内嵌"
                if r["画质等级"] != want:
                    bad_q.append((r["原文件名"], r["画质等级"], want))
    chk("画质等级与分辨率一致", not bad_q, str(bad_q[:5]))
    # manifest 未修改（mtime 基线）
    base = ctx["workdir"] / "manifest_mtime_base.jsonl"
    if base.exists():
        changed = []
        for l in base.read_text(encoding="utf-8").splitlines():
            d = json.loads(l)
            cur = os.path.getmtime(SMB_ROOT / d["group"] / MANIFEST)
            if abs(cur - d["mtime"]) > 2:
                changed.append(d["group"])
        chk(".manifest.jsonl 未修改", not changed, str(changed))
    # 幂等：重跑改名应零操作（旧名不存在，目录级缓存）
    old_left = 0
    _dir_cache: dict[tuple[str, str], set[str]] = {}

    def _names(group: str, sub: str) -> set[str]:
        k = (group, sub)
        if k not in _dir_cache:
            d = SMB_ROOT / group / sub
            _dir_cache[k] = set(os.listdir(d)) if d.is_dir() else set()
        return _dir_cache[k]

    for r in reg_rows:
        if r["文件名"] != r["原文件名"]:
            if r["原文件名"] in _names(r["项目"], "photo") or r["原文件名"] in _names(r["项目"], "video"):
                old_left += 1
    chk("改名幂等(旧名残留0)", old_left == 0, str(old_left))
    # 标注 vs 画面 抽样复核规则（任务书最高优先级）：脱敏非「无」100% 复核，其余抽样 ≥10%
    if "复核状态" in (reg_rows[0].keys() if reg_rows else []):
        n_reviewed = sum(1 for r in reg_rows if str(r.get("复核状态") or "") in ("已复核通过", "已复核修正"))
        n_sens = sum(1 for r in reg_rows if str(r.get("脱敏风险") or "") not in ("", "无"))
        n_lab = sum(1 for r in reg_rows if (r.get("描述") or "").strip())
        need = n_sens + max(1, int(n_lab * 0.1))
        chk("复核覆盖率(脱敏100%+抽样10%)", n_reviewed >= need, f"已复核 {n_reviewed}/{need} (脱敏 {n_sens} 条 100% + 抽样 10%)")
    out = ctx["workdir"] / "accept_report.json"
    out.write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"accept: pass={len(checks['pass'])} fail={len(checks['fail'])}")
    return checks


def stage_report(args, ctx) -> dict:
    media = [m for m in load_media(ctx["groups"]) if m.get("smb_status") == "complete"]
    reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig"))) if REG_CSV.exists() else []
    by_type = Counter(m.get("media_type") for m in media)
    renamed = sum(1 for r in reg_rows if r["文件名"] != r["原文件名"])
    labeled = sum(1 for r in reg_rows if r.get("描述"))
    pending = sum(1 for r in reg_rows if not r.get("描述"))
    dup_count = sum(1 for r in reg_rows if r.get("重复于") and r["重复于"] != "无")
    sens = sum(1 for r in reg_rows if r.get("脱敏风险") and r["脱敏风险"] != "无")
    lines = [
        "| 指标 | 数量 |", "|---|---|",
        f"| 检测照片 | {by_type.get('photo',0)} |",
        f"| 检测视频 | {by_type.get('video',0)} |",
        f"| 登记表行数 | {len(reg_rows)} |",
        f"| 已改名 | {renamed} |",
        f"| 已标注(有描述) | {labeled} |",
        f"| 待确认/未标注 | {pending} |",
        f"| 重复素材 | {dup_count} |",
        f"| 脱敏风险素材 | {sens} |",
        f"| 名单外新增群 | {len(ctx.get('new_groups') or [])} {(ctx.get('new_groups') or [''])[:3]} |",
        f"| SMB 健康自检 | {(ctx.get('smb_health') or {}).get('state', '未跑')} "
        f"{(ctx.get('smb_health') or {}).get('listdir_seconds', '')} |",
    ]
    txt = "\n".join(lines) + "\n"
    (ctx["workdir"] / "产能汇总.md").write_text(txt, encoding="utf-8")
    print(txt)
    return {"photos": by_type.get("photo", 0), "videos": by_type.get("video", 0),
            "renamed": renamed, "labeled": labeled, "pending": pending}


# ---------- 入口 ----------

def snapshot_manifest_mtimes(ctx, groups):
    recs = []
    for g in groups:
        p = SMB_ROOT / g / MANIFEST
        if p.exists():
            recs.append({"group": g, "mtime": os.path.getmtime(p)})
    (ctx["workdir"] / "manifest_mtime_base.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="KMVideo 一体化流水线 v0.2.0")
    ap.add_argument("stage", choices=["all", "scan", "probe", "thumbs", "dedup", "label",
                                      "rename", "registry", "upload", "accept", "report"])
    ap.add_argument("--groups-file", help="白名单文件（每行一个群名）")
    ap.add_argument("--only-group", help="只跑单群")
    ap.add_argument("--workdir", default="/tmp/kmvideo_work/pipeline_v020")
    ap.add_argument("--start", help="归档起点 YYYY-MM-DD HH:MM:SS")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--release-tag", default="", help="GitHub Release tag，空则跳过 Release 上传")
    ap.add_argument("--no-private", action="store_true")
    ap.add_argument("--media-type", default="", choices=["", "video", "photo"],
                    help="仅处理该媒体类型（空=全部）")
    ap.add_argument("--skip-groups", default="",
                    help="逗号分隔的群名黑名单（NAS 大目录异常时跳过，夜间单独跑）")
    ap.add_argument("--refresh-groups", action="store_true",
                    help="跑前用 dws 实时枚举群列表，与 --groups-file 求并集；新增群只报不收。")
    ap.add_argument("--include-new-groups", action="store_true",
                    help="与 --refresh-groups 连用：把新发现的群纳入本轮归档（默认只报不收）。")
    ap.add_argument("--since-manifest", action="store_true",
                    help="每群起点改为该群 manifest 最后一个 complete 窗口的终点（增量提速）。")
    ap.add_argument("--skip-smb-check", action="store_true", help="跳过开跑前的 SMB 健康自检。")
    args = ap.parse_args()
    global MEDIA_FILTER
    MEDIA_FILTER = args.media_type or None
    global SKIP_GROUPS
    SKIP_GROUPS = {g.strip() for g in (args.skip_groups or "").split(",") if g.strip()}

    groups = []
    if args.groups_file:
        groups = [l.strip() for l in open(args.groups_file, encoding="utf-8") if l.strip()]
    if args.only_group:
        groups = [args.only_group]
    if not groups:
        # 自举：skill 包里不带白名单文件，新 agent 拿到就该能跑。
        # 内置的 BUSINESS 业务映射表本身就是 Owner authorized 的群名单，拿它当基线；
        # 想拿实时名单再叠 --refresh-groups。
        groups = sorted(BUSINESS)
        log(f"未指定 --groups-file/--only-group，用内置 BUSINESS 映射表作基线：{len(groups)} 个群")
        log("  要拿 dws 实时名单请加 --refresh-groups（新增群只报不收）")
    ctx = {"groups": groups, "workdir": Path(args.workdir)}
    ctx["workdir"].mkdir(parents=True, exist_ok=True)
    acquire_workdir_lock(ctx["workdir"])

    new_groups: list[str] = []
    if args.refresh_groups and not args.only_group:
        merged, new_groups = discover_groups(groups)
        if new_groups:
            (ctx["workdir"] / "新增群待确认.txt").write_text(
                "\n".join(new_groups) + "\n", encoding="utf-8")
            log(f"发现 {len(new_groups)} 个名单外的群: {new_groups}")
            if args.include_new_groups:
                groups = merged
                log("  已按 --include-new-groups 纳入本轮")
            else:
                log("  本轮不收（要收加 --include-new-groups）；清单见 workdir/新增群待确认.txt")
        else:
            log("动态群名单：与实时枚举一致，无新增")
    ctx["groups"] = groups
    ctx["new_groups"] = new_groups
    if not args.skip_smb_check:
        ctx["smb_health"] = smb_health_check(groups)

    order = ["scan", "probe", "thumbs", "dedup", "label", "rename", "registry",
             "upload", "accept", "report"] if args.stage == "all" else [args.stage]
    snapshot_manifest_mtimes(ctx, groups)
    stats = {}
    for st in order:
        log(f"=== stage {st} ===")
        stats[st] = globals()[f"stage_{st}"](args, ctx)
        if st == "scan" and args.stage == "all":
            snapshot_manifest_mtimes(ctx, groups)  # 归档后刷新基线
    log(f"pipeline finished: {json.dumps(stats, ensure_ascii=False, default=str)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
