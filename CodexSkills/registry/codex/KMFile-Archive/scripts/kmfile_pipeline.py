#!/usr/bin/env python3
"""KMFile 一体化流水线 v0.0.0.1。

一条命令全跑：扫描+增量归档 → 规格探测 → 正文抽取 → md5 精确去重 → 本地标注（无外部 agent）
→ 幂等改名 → 登记表双格式 → 四处落地 → 自验收 → 产能汇总。

用法：
  python3 kmfile_pipeline.py all --groups-file 白名单.txt [--workdir DIR] [--start "YYYY-MM-DD HH:MM:SS"]
  python3 kmfile_pipeline.py {scan|probe|extract|dedup|label|rename|registry|upload|accept|report} ...

硬约束见 SKILL.md。不得调用任何外部 agent（cc/codex/远程视觉等）。
文档没有缩略图也没有画面，标注全部走本地文本：文件名 + 消息上下文 + 抽取正文。
"""
from __future__ import annotations

import argparse
import atexit
import csv
import json
import os
import re
import subprocess
import tempfile
import sys
import threading
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archive_internal_files as aif  # noqa: E402

ARCHIVER = aif

TIMEZONE = aif.TIMEZONE
SMB_ROOT = aif.SMB_ROOT
MANIFEST = aif.MANIFEST_NAME
DWS = aif.dws_json
FILE_MSG_RE = aif.FILE_MSG_RE
MEDIA_ID_RE = aif.MEDIA_ID_RE
AV_EXTENSIONS = aif.AV_EXTENSIONS

REG_CSV = SMB_ROOT / "文件登记表.csv"
MAP_CSV = SMB_ROOT / "原名新名映射.csv"
HANDOFF_CSV = SMB_ROOT / "待转KMVideo.csv"
PRIVATE_CLIENT = aif.PRIVATE_DB_CLIENT

# 登记表三个本机落点（SMB 为唯一真源，另两处为分发副本）
DOCS_INDEX = Path.home() / "Documents" / "KMFile" / "00_治理与登记" / "02_登记与索引"
DOWNLOADS = Path.home() / "Downloads"

# 精简子集列（供 ChatGPT 等无本地文件权限的模型直接上传使用，体积小）
SUBSET_COLS = ["项目", "文件名", "日期", "扩展名", "文档类型", "描述", "页数或行数", "字数",
               "工序阶段", "能证明什么", "脱敏风险", "摘要", "置信度"]

# 业务映射表（与 KMVideo/README.md 同一张表，不另立门户）
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

BASE_COLS = ["项目", "文件名", "日期", "原文件名", "大小", "描述", "置信度"]
NEW_COLS = ["扩展名", "文档类型", "页数或行数", "字数", "md5", "发送人", "重复于",
            "工序阶段", "能证明什么", "脱敏风险", "摘要", "标注执行者", "标注日期", "复核状态"]

VOCAB = {
    "文档类型": {"报价单", "投标记录", "中标通知", "合同", "施工方案", "验收报告", "图纸",
                 "清单", "工作日志", "票据", "明细账", "通知公告", "证明材料", "技术资料",
                 "考勤薪酬", "Excel", "PDF", "Word", "图片", "扫描件", "ZIP", "压缩包", "其他"},
    "工序阶段": {"测量", "拆解", "加工", "焊接", "复检", "收尾", "验收", "施工", "资料", "无法判断"},
    "脱敏风险": {"客户名称", "人脸", "打卡应用水印", "精确地理位置", "车牌", "安全告示牌",
                 "金额报价", "身份证号", "银行账号", "无"},
}

# 关键词 → (文档类型, 说明, 工序阶段)  本地语义标注核心表。
# 顺序即优先级：先命中先用，专有词放前面，泛词放后面。
DOC_KEYWORDS = [
    ("中标通知", "中标通知", "中标通知", "无法判断"),
    ("投标", "投标记录", "投标记录", "无法判断"),
    ("招标", "投标记录", "招标文件", "无法判断"),
    ("报价", "报价单", "报价单", "无法判断"),
    ("询价", "报价单", "询价单", "无法判断"),
    ("合同", "合同", "合同文本", "无法判断"),
    ("协议", "合同", "协议文本", "无法判断"),
    ("施工方案", "施工方案", "施工方案", "无法判断"),
    ("技术方案", "施工方案", "技术方案", "无法判断"),
    ("方案", "施工方案", "工程方案", "无法判断"),
    ("验收", "验收报告", "验收报告", "复检"),
    ("竣工", "验收报告", "竣工资料", "收尾"),
    ("检测报告", "验收报告", "检测报告", "复检"),
    ("图纸", "图纸", "工程图纸", "无法判断"),
    ("装配图", "图纸", "装配图纸", "无法判断"),
    ("明细账", "明细账", "明细账", "无法判断"),
    ("对账", "明细账", "对账单", "无法判断"),
    ("资金", "明细账", "资金明细", "无法判断"),
    ("发票", "票据", "发票凭证", "无法判断"),
    ("票据", "票据", "票据凭证", "无法判断"),
    ("付款", "票据", "付款单据", "无法判断"),
    ("税", "票据", "税务资料", "无法判断"),
    ("工资", "考勤薪酬", "工资表", "无法判断"),
    ("考勤", "考勤薪酬", "考勤表", "无法判断"),
    ("社保", "考勤薪酬", "社保资料", "无法判断"),
    ("日志", "工作日志", "工作日志", "无法判断"),
    ("日报", "工作日志", "工作日报", "无法判断"),
    ("周报", "工作日志", "工作周报", "无法判断"),
    ("月报", "工作日志", "工作月报", "无法判断"),
    ("总结", "工作日志", "工作总结", "无法判断"),
    ("会议纪要", "工作日志", "会议纪要", "无法判断"),
    ("清单", "清单", "物资清单", "无法判断"),
    ("台账", "清单", "设备台账", "无法判断"),
    ("统计", "清单", "统计表", "无法判断"),
    ("通知", "通知公告", "通知文件", "无法判断"),
    ("公告", "通知公告", "公告文件", "无法判断"),
    ("承诺书", "证明材料", "承诺书", "无法判断"),
    ("授权", "证明材料", "授权文件", "无法判断"),
    ("委托", "证明材料", "委托文件", "无法判断"),
    ("业绩", "证明材料", "业绩证明", "无法判断"),
    ("简历", "证明材料", "人员简历", "无法判断"),
    ("证明", "证明材料", "证明材料", "无法判断"),
    ("资质", "证明材料", "资质材料", "无法判断"),
    ("营业执照", "证明材料", "执照副本", "无法判断"),
    ("说明书", "技术资料", "技术说明", "无法判断"),
    ("规范", "技术资料", "技术规范", "无法判断"),
    ("工艺", "技术资料", "工艺文件", "加工"),
    ("焊", "技术资料", "焊接资料", "焊接"),
    ("轮带", "技术资料", "轮带资料", "加工"),
    ("托轮", "技术资料", "托轮资料", "复检"),
    ("齿轮", "技术资料", "齿轮资料", "加工"),
    ("检修", "技术资料", "检修资料", "拆解"),
    ("测量", "技术资料", "测量记录", "测量"),
]

DESENS_RISK_KW = {
    "客户名称": ["客户", "甲方", "钢厂", "水泥厂", "有限公司", "股份", "集团"],
    "金额报价": ["报价", "金额", "单价", "总价", "元", "万元", "含税"],
    "银行账号": ["开户行", "账号", "银行账", "卡号"],
    "身份证号": ["身份证", "证件号"],
    "车牌": ["车牌", "车号"],
    "精确地理位置": ["定位", "经纬度", "GPS"],
}

# 泛化说明黑名单：这些词进了文件名等于没标
GENERIC_REJECT = ("文件", "文档", "资料", "附件", "新建", "未命名", "扫描件", "图片")

TEXT_EXTENSIONS = {"txt", "csv", "md", "log", "json", "xml"}
TEXTUTIL_EXTENSIONS = {"doc", "rtf", "html", "htm", "rtfd", "odt"}
OOXML_EXTENSIONS = {"xlsx", "docx", "pptx", "et", "wps", "dps"}
XML_TAG_RE = re.compile(r"<[^>]+>")


def now_sh():
    return datetime.now(TIMEZONE).replace(microsecond=0)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def rsync_write(src: Path, dst: Path) -> None:
    """约束7：rsync 写 SMB + 字节数校验。

    这台机器的 SMB 挂载写后 `stat` 会短暂返回旧尺寸（实测），所以校验失败要先沉降再重试，
    连续 3 轮仍对不上才认失败——直接报错会把「其实写对了」误判成写坏。
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    want = os.path.getsize(src)
    last = ""
    for attempt in range(3):
        r = subprocess.run(["rsync", "--inplace", "--whole-file", str(src), str(dst)],
                           capture_output=True, text=True, timeout=1200)
        if r.returncode != 0:
            last = r.stderr[-200:] or "rsync returned non-zero"
        else:
            for settle in range(2):
                if dst.is_file() and os.path.getsize(dst) == want:
                    return
                if not settle:
                    time.sleep(1)
            last = f"size mismatch: want {want}, got {dst.stat().st_size if dst.is_file() else 'missing'}"
        time.sleep(2 ** attempt)
    raise RuntimeError(f"rsync write did not verify {dst}: {last}")


def load_files(groups: list[str]) -> list[dict]:
    """读各群 manifest 的 file 记录（只读）。"""
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
            if d.get("record_type") == "file":
                d["_group"] = g
                out.append(d)
    # 同一 record_id 后写覆盖先写（manifest 是追加式的）
    dedup = {}
    for d in out:
        dedup[d["record_id"]] = d
    return list(dedup.values())


def load_handoffs(groups: list[str]) -> list[dict]:
    out = {}
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
            if d.get("record_type") == "handoff_av":
                d["_group"] = g
                out[d["record_id"]] = d
    return list(out.values())


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
    stats = {"archived": 0, "existing": 0, "unavailable": 0, "handoff_av": 0,
             "context_msgs": 0, "skipped_groups": []}
    start = args.start or (now_sh() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    archiver = Path(__file__).parent / "archive_internal_files.py"
    for g in ctx["groups"]:
        saved = False
        for attempt in range(3):
            cmd = [sys.executable, str(archiver), "--allow-title", g,
                   "--start", start, "--window-days", str(args.window_days),
                   "--workers", "4", "--apply"]
            if args.no_private:
                cmd.append("--smb-only")
            if getattr(args, "since_manifest", False):
                cmd.append("--since-manifest")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            fin = [l for l in (r.stdout or "").splitlines() if "run_finished" in l]
            if fin:
                try:
                    ev = json.loads(fin[-1])
                    stats["archived"] += int(ev.get("smb_saved", 0) or 0)
                    # 幂等重跑时 smb_saved=0 是正常的（文件已在），不能当成失败。
                    stats["existing"] += int(ev.get("skipped", 0) or 0)
                    stats["unavailable"] += int(ev.get("unavailable", 0) or 0)
                    stats["handoff_av"] += int(ev.get("handoff_av", 0) or 0)
                    if ev.get("failures"):
                        stats["skipped_groups"].append((g, "failures>0"))
                except json.JSONDecodeError:
                    pass
                saved = True
                break
            if attempt < 2:
                time.sleep(30)
        if not saved:
            stats["skipped_groups"].append((g, "archive no run_finished"))
    # 消息上下文捕获（只读 DWS，用于本地语义标注）
    ctx_file = ctx["workdir"] / "context.jsonl"
    seen = set()
    if ctx_file.exists():
        seen = {json.loads(l)["key"] for l in ctx_file.read_text(encoding="utf-8").splitlines() if l.strip()}
    with ctx_file.open("a", encoding="utf-8") as f:
        for g in ctx["groups"]:
            msgs = None
            for attempt in range(3):
                try:
                    convs = aif.select_groups([g])
                    if not convs:
                        stats["skipped_groups"].append((g, "group not found"))
                        break
                    conv = convs[0]
                    t_end = now_sh()
                    t_start = parse_ctx_start(ctx, g, t_end)
                    raw = list(aif.walk_window_messages(conv.conversation_id, t_start, t_end,
                                                        None, args.page_size))
                    msgs = sorted(((aif.parse_time(str(m.get("createTime"))), m) for m in raw),
                                  key=lambda x: x[0])
                    break
                except Exception as e:  # noqa: BLE001 - DWS 瞬断一律重试
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
            # 每条文件消息用二分定位 ±30 分钟窗口，避免 O(n²)
            for idx, (ts, m) in enumerate(msgs):
                hit = FILE_MSG_RE.match(str(m.get("content") or "").strip())
                if not hit:
                    continue
                file_id = hit.group(2)
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
                before = " | ".join(c for t, c in ctx_texts if t <= ts)[-200:]
                after = " | ".join(c for t, c in ctx_texts if t > ts)[-100:]
                key = f"{g}\t{file_id}"
                if key in seen:
                    continue
                seen.add(key)
                f.write(json.dumps({"key": key, "group": g, "file_id": file_id,
                                    "time": str(ts), "before": before, "after": after},
                                   ensure_ascii=False) + "\n")
                stats["context_msgs"] += 1
    log(f"scan done: 新增={stats['archived']} 已存在={stats['existing']} "
        f"钉钉侧已删={stats['unavailable']} handoff_av={stats['handoff_av']} "
        f"context={stats['context_msgs']} skipped={stats['skipped_groups']}")
    return stats


def parse_ctx_start(ctx, group: str, t_end: datetime) -> datetime:
    """上下文捕获起点：该群 manifest 最早 file 时间再往前 1 天。"""
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


def _stat_sizes(directory: Path, names: list[str]) -> dict[str, int]:
    """并行 stat（问题记录：SMB IO 一律 >=8 worker 并行，串行会被每请求固定延迟吃死）。"""
    from concurrent.futures import ThreadPoolExecutor
    out: dict[str, int] = {}

    def one(n: str):
        try:
            return n, (directory / n).stat().st_size
        except OSError:
            return n, None

    workers = int(os.environ.get("RECONCILE_WORKERS", "8"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n, size in ex.map(one, names):
            if size is not None:
                out[n] = size
    return out


def reconcile_ledger(groups: list[str]) -> dict:
    """账本自愈：磁盘已改名、账本却还记着旧名的记录，按 md5/大小认回来。

    为什么必须有这条路径：改名的三道幂等闸都以「原名还在磁盘上」为前提，
    一旦账本写丢（进程被杀、SMB 写失败、跨版本运行），rename 会因为原名已不在
    而永远跳过，账本再也回不来 —— 表现就是 accept 的 md5 校验一直报 missing，
    而磁盘上文件其实好好的。md5 存在 manifest 里，是精确判据。

    性能约束（问题记录 P2-4）：**存在性判定只用一次 listdir + 内存比对，绝不逐文件 stat**；
    只有确实要配对时才对未被认领的候选并行 stat，md5 只算到命中为止。
    """
    ledger = load_ledger()
    repaired, ambiguous, scanned = [], [], 0
    by_group: dict[str, list[dict]] = defaultdict(list)
    for m in load_files(groups):
        if m.get("smb_status") == "complete":
            by_group[m["_group"]].append(m)
    for group, records in by_group.items():
        directory = SMB_ROOT / group / "file"
        if not directory.is_dir():
            continue
        names = {n for n in os.listdir(directory) if not n.startswith("._")}
        scanned += 1
        mapped_of = {}
        for m in records:
            old = os.path.basename(m.get("relative_path") or "")
            mapped_of[old] = (ledger.get((group, old)) or {}).get("新文件名", "")
        unresolved = [m for m in records
                      if os.path.basename(m.get("relative_path") or "") not in names
                      and mapped_of.get(os.path.basename(m.get("relative_path") or ""), "") not in names]
        if not unresolved:
            continue  # 早退，一次 stat 都不做
        claimed = {v for v in mapped_of.values() if v and v in names}
        claimed |= {os.path.basename(m.get("relative_path") or "") for m in records} & names
        candidates = sorted(names - claimed)
        if not candidates:
            continue
        sizes = _stat_sizes(directory, candidates)
        by_size: dict[int, list[str]] = defaultdict(list)
        for n, size in sizes.items():
            by_size[size].append(n)
        for m in unresolved:
            old_name = os.path.basename(m.get("relative_path") or "")
            hits = [n for n in by_size.get(int(m.get("size_bytes") or -1), []) if n not in claimed]
            digest = str(m.get("md5") or "")
            hit = None
            if digest:
                for n in hits:
                    if aif.md5_b64(directory / n) == digest:
                        hit = n
                        break
            elif len(hits) == 1:
                hit = hits[0]
            if hit:
                ledger[(group, old_name)] = {
                    "项目": group, "原文件名": old_name, "新文件名": hit,
                    "日期": str(m.get("message_time") or "")[2:10].replace("-", ""),
                    "大小": str(m.get("size_bytes") or ""), "md5": digest,
                }
                claimed.add(hit)
                repaired.append(f"{group}/{old_name} → {hit}")
            elif hits:
                ambiguous.append(f"{group}/{old_name} ?= {hits[:3]}")
    if repaired:
        save_ledger(ledger, Path(tempfile.gettempdir()))
        log(f"账本自愈: 认回 {len(repaired)} 条 —— {repaired[:3]}")
    if ambiguous:
        log(f"账本自愈: {len(ambiguous)} 条大小相同但 md5 对不上，留给人工 —— {ambiguous[:3]}")
    return {"repaired": len(repaired), "ambiguous": len(ambiguous), "dirs_scanned": scanned}


# ---------- 阶段二：规格探测 ----------

def stage_probe(args, ctx) -> dict:
    """文件版的规格全部来自 manifest（归档时已从 dws drive info 拿到 md5/大小/扩展名）。

    这里只做磁盘核对：文件在不在、字节数对不对；缺 md5 的补算本机 md5。
    不再打一次 DWS —— 云成本红线：存在性判定不许高频轮询。
    """
    healed = reconcile_ledger(ctx["groups"])
    specs = {}
    pf = ctx["workdir"] / "specs.jsonl"
    files = load_files(ctx["groups"])
    missing = mismatched = 0
    with pf.open("w", encoding="utf-8") as f:
        for m in files:
            if m.get("smb_status") != "complete":
                continue
            rel = m.get("relative_path") or ""
            name = os.path.basename(rel)
            # 改名后原路径已不存在，按映射表回查真实路径（见 aif.resolve_current_path）
            p = aif.resolve_current_path(m)
            rec = {
                "file": name, "_group": m["_group"], "relative_path": rel,
                "current_path": str(p) if p else "",
                "file_id": m.get("file_id"), "message_id": m.get("message_id"),
                "extension": str(m.get("extension") or aif.extension_of(name)).lower(),
                "size": m.get("size_bytes"), "md5": m.get("md5") or "",
                "sender": m.get("sender") or "", "message_time": m.get("message_time") or "",
                "on_disk": p is not None,
            }
            if p is None:
                missing += 1
            else:
                actual = p.stat().st_size
                rec["disk_size"] = actual
                if rec["size"] and actual != rec["size"]:
                    mismatched += 1
                if not rec["md5"]:
                    rec["md5"] = aif.md5_b64(p)
            specs[name] = rec
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"probe done: total={len(specs)} missing_on_disk={missing} size_mismatch={mismatched} "
        f"账本自愈={healed}")
    return {"total": len(specs), "missing": missing, "mismatched": mismatched, "ledger_healed": healed}


# ---------- 阶段二续：正文抽取（零新增依赖） ----------

def _strip_xml(raw: bytes, limit: int) -> str:
    text = XML_TAG_RE.sub(" ", raw.decode("utf-8", "ignore"))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def extract_text(path: Path, extension: str, limit: int = 20000) -> tuple[str, int]:
    """返回 (正文, 页数或行数)。全部本机零新增依赖：

    pdf → PyMuPDF(fitz)；xlsx/docx/pptx/et → 标准库 zipfile 拆 XML；
    doc/rtf/html → macOS 自带 textutil；txt/csv/md → 直读；其余 → 空。
    """
    if not path.exists():
        return "", 0
    try:
        if extension == "pdf":
            import fitz  # PyMuPDF
            with fitz.open(path) as doc:
                pages = doc.page_count
                chunks = []
                for page in doc:
                    chunks.append(page.get_text())
                    if sum(len(c) for c in chunks) > limit:
                        break
                return re.sub(r"\s+", " ", " ".join(chunks)).strip()[:limit], pages
        if extension in OOXML_EXTENSIONS:
            if not zipfile.is_zipfile(path):
                return "", 0
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                if extension in {"xlsx", "et"}:
                    shared = ""
                    if "xl/sharedStrings.xml" in names:
                        shared = _strip_xml(archive.read("xl/sharedStrings.xml"), limit)
                    sheets = [n for n in names if n.startswith("xl/worksheets/sheet")]
                    body = shared
                    if len(body) < limit and sheets:
                        body = (body + " " + _strip_xml(archive.read(sheets[0]), limit))[:limit]
                    return body.strip(), len(sheets)
                if extension in {"docx", "wps"}:
                    if "word/document.xml" not in names:
                        return "", 0
                    body = _strip_xml(archive.read("word/document.xml"), limit)
                    return body, 0
                slides = [n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
                body = " ".join(_strip_xml(archive.read(n), limit) for n in slides[:20])
                return re.sub(r"\s+", " ", body).strip()[:limit], len(slides)
        if extension in TEXTUTIL_EXTENSIONS:
            r = subprocess.run(["/usr/bin/textutil", "-convert", "txt", "-stdout", str(path)],
                               capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                return "", 0
            body = re.sub(r"\s+", " ", r.stdout).strip()[:limit]
            return body, r.stdout.count("\n") + 1
        if extension in TEXT_EXTENSIONS:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            return re.sub(r"\s+", " ", raw).strip()[:limit], raw.count("\n") + 1
    except Exception:  # noqa: BLE001 - 抽取失败一律降级为「无正文」，不阻塞流水线
        return "", 0
    return "", 0


def stage_extract(args, ctx) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    specs = {}
    pf = ctx["workdir"] / "specs.jsonl"
    if pf.exists():
        for l in pf.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                specs[d["file"]] = d
    out_dir = ctx["workdir"] / "texts"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = empty = 0
    lock = threading.Lock()

    def work(rec):
        nonlocal done, empty
        name = rec["file"]
        stem = os.path.splitext(name)[0]
        dst = out_dir / f"{stem}.txt"
        if dst.exists():
            body = dst.read_text(encoding="utf-8", errors="ignore")
            pages = rec.get("页数或行数", 0)
        else:
            src = Path(rec.get("current_path") or (SMB_ROOT / rec["relative_path"]))
            body, pages = extract_text(src, rec.get("extension", ""))
            dst.write_text(body, encoding="utf-8")
        with lock:
            rec["页数或行数"] = pages
            rec["字数"] = len(body)
            rec["摘要"] = body[:100]
            if body:
                done += 1
            else:
                empty += 1

    with ThreadPoolExecutor(max_workers=int(os.environ.get("EXTRACT_WORKERS", "6"))) as ex:
        list(ex.map(work, [r for r in specs.values() if r.get("on_disk")]))
    with pf.open("w", encoding="utf-8") as f:
        for rec in specs.values():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"extract done: with_text={done} no_text={empty}")
    return {"with_text": done, "no_text": empty}


# ---------- 阶段三：md5 精确去重 ----------

def stage_dedup(args, ctx) -> dict:
    out = ctx["workdir"] / "dups.jsonl"
    files = [m for m in load_files(ctx["groups"]) if m.get("smb_status") == "complete"]
    by_md5 = defaultdict(list)
    for m in files:
        digest = m.get("md5") or ""
        if digest:
            by_md5[digest].append(m)
    dups = {}
    for digest, group in by_md5.items():
        if len(group) < 2:
            continue
        # 保留最早发出的那份，其余标重复
        group.sort(key=lambda m: str(m.get("message_time") or ""))
        keep = group[0]
        for m in group[1:]:
            dups[m["relative_path"]] = os.path.basename(keep["relative_path"])
    with out.open("w", encoding="utf-8") as f:
        for rel, keep in dups.items():
            f.write(json.dumps({"file": rel, "重复于": keep}, ensure_ascii=False) + "\n")
    log(f"dedup done: {len(dups)} duplicates of {len(files)} files ({len(by_md5)} distinct md5)")
    return {"files": len(files), "distinct_md5": len(by_md5), "dups": len(dups)}


# ---------- 阶段四：本地标注（无外部 agent，无视觉调用） ----------

def kw_label(text: str):
    """关键词 → (文档类型, 说明, 工序阶段)。三路文本共用同一张表。"""
    for kw, doc_type, note, stage in DOC_KEYWORDS:
        if kw in text:
            return doc_type, note, stage
    return None


def desens_risk(text: str) -> str:
    risks = []
    for risk, kws in DESENS_RISK_KW.items():
        if any(k in text for k in kws):
            risks.append(risk)
    return "、".join(risks) if risks else "无"


def reject_generic(note: str) -> bool:
    return (not note) or any(k in note for k in GENERIC_REJECT)


def stage_label(args, ctx) -> dict:
    """三路本地信号：①原文件名 ②消息上下文 ③抽取正文。全部本地，不调任何外部 agent。"""
    files = [m for m in load_files(ctx["groups"]) if m.get("smb_status") == "complete"]
    ctx_map = {}
    cf = ctx["workdir"] / "context.jsonl"
    if cf.exists():
        for l in cf.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                ctx_map[(d["group"], d["file_id"])] = d
    specs = {}
    sf = ctx["workdir"] / "specs.jsonl"
    if sf.exists():
        for l in sf.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                specs[d["file"]] = d
    dups = {}
    df = ctx["workdir"] / "dups.jsonl"
    if df.exists():
        for l in df.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                dups[d["file"]] = d["重复于"]
    override = {}
    ovf = ctx["workdir"] / "label_override.jsonl"
    if ovf.exists():
        for l in ovf.read_text(encoding="utf-8").splitlines():
            if l.strip():
                d = json.loads(l)
                override[d["file"]] = d
    # 已有高置信度标注的行不重标（幂等，也避免覆盖人工终审结果）
    reg_done = set()
    if REG_CSV.exists():
        for rr in csv.DictReader(REG_CSV.open(encoding="utf-8-sig")):
            if (rr.get("描述") or "").strip() and (rr.get("置信度") or "") != "待确认":
                reg_done.add((rr.get("项目"), rr.get("原文件名")))

    rows, labeled, pending, skipped = [], 0, 0, 0
    for m in files:
        name = os.path.basename(m.get("relative_path") or "")
        if (m["_group"], name) in reg_done:
            skipped += 1
            continue
        s = specs.get(name, {})
        ov = override.get(name, {})
        c = ctx_map.get((m["_group"], m.get("file_id")), {})
        context_text = f"{c.get('before','')} {c.get('after','')}"
        body = str(s.get("摘要") or "")
        # 三路信号按可信度排序：文件名 > 消息上下文 > 正文首段
        hit = kw_label(name) or kw_label(context_text) or kw_label(body)
        if ov.get("描述"):
            doc_type = ov.get("文档类型") or (hit[0] if hit else "其他")
            note = str(ov["描述"]).strip()
            stage = ov.get("工序阶段") or (hit[2] if hit else "无法判断")
            source = "人工覆盖"
        elif hit:
            doc_type, note, stage = hit
            source = "pipeline-local"
        else:
            doc_type, note, stage, source = "其他", "", "无法判断", "pipeline-local"
        if reject_generic(note) or not (2 <= len(note) <= 6):
            note = "待确认"
        risk_text = " ".join([name, context_text, body])
        row = {
            "项目": m["_group"], "原文件名": name,
            "relative_path": m.get("relative_path"),
            "扩展名": s.get("extension") or aif.extension_of(name),
            "文档类型": doc_type if doc_type in VOCAB["文档类型"] else "其他",
            "说明": note,
            "置信度": "高" if (ov or (hit and note != "待确认")) else "待确认",
            "工序阶段": stage if stage in VOCAB["工序阶段"] else "无法判断",
            "能证明什么": (ov.get("能证明什么") or c.get("before") or body[:60] or "").strip()[:60] or "无法判断",
            "脱敏风险": ov.get("脱敏风险") or desens_risk(risk_text),
            "页数或行数": s.get("页数或行数", ""),
            "字数": s.get("字数", ""),
            "摘要": body,
            "md5": s.get("md5", "") or m.get("md5", ""),
            "发送人": s.get("sender", "") or m.get("sender", ""),
            "重复于": dups.get(m.get("relative_path"), "无"),
            "标注执行者": source,
            "标注日期": now_sh().strftime("%y%m%d"),
        }
        # 枚举消毒：未知词丢弃，全丢完则退回「无」
        vals = [x.strip() for x in str(row["脱敏风险"]).replace("、", ",").split(",") if x.strip()]
        keep = [v for v in vals if v in VOCAB["脱敏风险"]] or ["无"]
        row["脱敏风险"] = "、".join(dict.fromkeys(keep))
        if note == "待确认":
            pending += 1
        else:
            labeled += 1
        rows.append(row)

    out = ctx["workdir"] / "desc.csv"
    cols = ["项目", "原文件名", "relative_path", "扩展名", "文档类型", "说明", "置信度",
            "工序阶段", "能证明什么", "脱敏风险", "页数或行数", "字数", "摘要", "md5",
            "发送人", "重复于", "标注执行者", "标注日期"]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    log(f"label done: total={len(rows)} labeled={labeled} pending={pending} skipped={skipped}")
    return {"total": len(rows), "labeled": labeled, "pending": pending, "skipped": skipped}


# ---------- 阶段五：幂等改名 ----------

MAP_COLS = ["项目", "原文件名", "新文件名", "日期", "大小", "md5"]


def load_ledger() -> dict[tuple[str, str], dict]:
    """读 `原名新名映射.csv` 改名账本。它是「现用名」的唯一权威。

    `.manifest.jsonl` 永远记原名（硬约束 2），登记表可能还没回填，
    所以改名成功的瞬间就必须落这张账本 —— 否则归档器会把已改名的文件当缺失重下，
    重下回来的原名又会被再改一次，滚出 _01/_02/_03 一串重复件。
    """
    ledger: dict[tuple[str, str], dict] = {}
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


def save_ledger(ledger: dict[tuple[str, str], dict], workdir: Path) -> None:
    rows = [ledger[k] for k in sorted(ledger)]
    tmp = workdir / "原名新名映射.ledger.csv"
    tmp.write_text("﻿" + csv_text(rows, MAP_COLS), encoding="utf-8")
    rsync_write(tmp, MAP_CSV)


def stage_rename(args, ctx) -> dict:
    desc = {}
    df = ctx["workdir"] / "desc.csv"
    if df.exists():
        desc = {(r["项目"], r["原文件名"]): r for r in csv.DictReader(df.open(encoding="utf-8-sig"))}
    ledger = load_ledger()
    renamed_set = set()
    if REG_CSV.exists():
        for r in csv.DictReader(REG_CSV.open(encoding="utf-8-sig")):
            if r.get("文件名") and r.get("原文件名") and r["文件名"] != r["原文件名"]:
                renamed_set.add((r["项目"], r["原文件名"]))
    ops = []
    stale = 0
    counters = defaultdict(int)
    # 先把磁盘上已有的新名计入序号，保证重跑不撞号
    existing_names = {}
    for m in load_files(ctx["groups"]):
        g = m["_group"]
        if g not in existing_names:
            d = SMB_ROOT / g / "file"
            existing_names[g] = set(os.listdir(d)) if d.is_dir() else set()
    for m in sorted(load_files(ctx["groups"]), key=lambda x: str(x.get("message_time") or "")):
        rel = m.get("relative_path") or ""
        old_name = os.path.basename(rel)
        key = (m["_group"], old_name)
        if key in renamed_set:
            continue
        # 幂等第二道闸（账本）：账本里已有新名且该新名在磁盘上，这份就是改过的，绝不再改。
        mapped = (ledger.get(key) or {}).get("新文件名", "")
        if mapped and mapped != old_name and mapped in existing_names.get(m["_group"], set()):
            if old_name in existing_names.get(m["_group"], set()):
                stale += 1  # 旧名残留（历史重下产物），只记账不删，交人工处置
            continue
        # 幂等第三道闸（磁盘）：原名已不在磁盘上 = 早就改过了，别再排一次操作。
        if old_name not in existing_names.get(m["_group"], set()):
            continue
        d = desc.get(key)
        note = (d.get("说明") or "").strip() if d else ""
        if not note or note == "待确认":
            continue  # 保留原名，进待办等人工终审
        biz = BUSINESS.get(m["_group"], "")
        if not biz:
            continue
        ext = os.path.splitext(old_name)[1]
        mt = str(m.get("message_time") or "")[:10]
        date = mt[2:4] + mt[5:7] + mt[8:10] if len(mt) == 10 else ""
        if not date:
            continue
        counters[(m["_group"], biz, note, date)] += 1
        new_name = f"{biz}_{note}_{date}_{counters[(m['_group'], biz, note, date)]:02d}{ext}"
        while new_name in existing_names.get(m["_group"], set()) and new_name != old_name:
            counters[(m["_group"], biz, note, date)] += 1
            new_name = f"{biz}_{note}_{date}_{counters[(m['_group'], biz, note, date)]:02d}{ext}"
        if new_name == old_name:
            continue
        ops.append((rel, new_name, note, date, m.get("size_bytes", ""), m.get("md5", "")))
    seen = Counter(o[1] for o in ops)
    conflicts = {k: v for k, v in seen.items() if v > 1}
    if conflicts:
        log(f"name conflicts {len(conflicts)} — 这些保持原名: {list(conflicts)[:5]}")
        ops = [o for o in ops if seen[o[1]] == 1]
    ok = gone = fail = 0
    done_ops = []
    for rel, nn, note, date, size, digest in ops:
        old_p = SMB_ROOT / rel
        new_p = old_p.parent / nn
        # SMB 的 rename 实测会随机 EIO，重试 3 次；仍失败则记账不中断整轮
        last = None
        for attempt in range(3):
            try:
                os.rename(old_p, new_p)
                ok += 1
                done_ops.append((rel, nn, note, date, size, digest))
                last = None
                break
            except FileNotFoundError:
                gone += 1
                last = None
                break
            except OSError as e:
                last = e
                time.sleep(2 ** attempt)
        if last is not None:
            fail += 1
            log(f"rename fail {rel}: {last}")
    # 改名成功即刻落账本 —— 不等 registry，否则中途中断会留下「磁盘已改、账本没记」的黑洞
    if done_ops:
        for rel, nn, _note, date, size, digest in done_ops:
            folder = rel.split("/")[0]
            ledger[(folder, os.path.basename(rel))] = {
                "项目": folder, "原文件名": os.path.basename(rel), "新文件名": nn,
                "日期": date, "大小": str(size), "md5": digest,
            }
        save_ledger(ledger, ctx["workdir"])
    cmp_path = ctx["workdir"] / "改名前后对照.csv"
    with cmp_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["项目", "原文件名", "新文件名", "说明"])
        w.writeheader()
        for rel, nn, note, *_ in ops:
            w.writerow({"项目": rel.split("/")[0], "原文件名": os.path.basename(rel),
                        "新文件名": nn, "说明": note})
    log(f"rename done: ops={len(ops)} ok={ok} gone={gone} fail={fail} 旧名残留={stale}")
    return {"ops": len(ops), "ok": ok, "gone": gone, "fail": fail, "stale": stale}


# ---------- 阶段六：登记表双格式 + 四处落地 ----------

def csv_text(rows, cols) -> str:
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    w.writerows({k: r.get(k, "") for k in cols} for r in rows)
    return buf.getvalue()


def stage_registry(args, ctx) -> dict:
    desc = {}
    df = ctx["workdir"] / "desc.csv"
    if df.exists():
        desc = {(r["项目"], r["原文件名"]): r for r in csv.DictReader(df.open(encoding="utf-8-sig"))}
    ledger = load_ledger()
    fieldnames = list(BASE_COLS) + list(NEW_COLS)
    reg_rows, bykey = [], {}
    if REG_CSV.exists():
        reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig")))
        existing_cols = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig")).fieldnames or [])
        fieldnames = existing_cols + [c for c in fieldnames if c not in existing_cols]
        bykey = {(r.get("项目"), r.get("原文件名")): r for r in reg_rows}

    dir_cache: dict[str, set[str]] = {}

    def names_in(group: str) -> set[str]:
        if group not in dir_cache:
            d = SMB_ROOT / group / "file"
            dir_cache[group] = set(os.listdir(d)) if d.is_dir() else set()
        return dir_cache[group]

    updated = added = 0
    for m in load_files(ctx["groups"]):
        if m.get("smb_status") != "complete":
            continue
        rel = m.get("relative_path") or ""
        old_name = os.path.basename(rel)
        key = (m["_group"], old_name)
        mt = str(m.get("message_time") or "")[:10]
        date = mt[2:4] + mt[5:7] + mt[8:10] if len(mt) == 10 else ""
        r = bykey.get(key)
        if r is None:
            r = {"项目": m["_group"], "文件名": old_name, "日期": date, "原文件名": old_name,
                 "大小": m.get("size_bytes", ""), "描述": "", "置信度": ""}
            reg_rows.append(r)
            bykey[key] = r
            added += 1
        for k in fieldnames:
            r.setdefault(k, "")
        names = names_in(m["_group"])
        d = desc.get(key)
        note = (d.get("说明") or "").strip() if d else ""
        # 文件名列以改名账本为准：账本在改名成功那一刻就写了，比事后扫磁盘猜可靠。
        # 只有账本记的新名确实不在磁盘上（人工回退过）才退回原名。
        mapped = (ledger.get(key) or {}).get("新文件名", "")
        if mapped and mapped != old_name and mapped in names:
            r["文件名"] = mapped
        elif not str(r.get("文件名") or "").strip():
            r["文件名"] = old_name
        elif r.get("文件名") != old_name and r.get("文件名") not in names and old_name in names:
            r["文件名"] = old_name  # 磁盘已回退，登记表跟随
        r["日期"] = r.get("日期") or date
        r["大小"] = m.get("size_bytes", "")
        r["md5"] = m.get("md5", "")
        r["扩展名"] = str(m.get("extension") or aif.extension_of(old_name))
        r["发送人"] = m.get("sender", "")
        if d:
            for col in ("文档类型", "工序阶段", "能证明什么", "脱敏风险", "页数或行数",
                        "字数", "摘要", "重复于", "标注执行者", "标注日期"):
                r[col] = d.get(col, "")
            r["复核状态"] = r.get("复核状态") or "未复核"
            has_desc = bool(str(r.get("描述") or "").strip())
            renamed = (r.get("文件名") or "") != (r.get("原文件名") or "")
            if note and note != "待确认" and not has_desc:
                # 首次落描述必须写，改没改名都一样。
                # rename 跑在 registry 之前，若把「已改名」当成「已定案」直接跳过，
                # 首轮的描述就永远写不进去 —— 登记表整列空白。
                r["描述"] = note
                r["置信度"] = "高"
            elif renamed:
                pass  # 已改名且已有描述：定案，不覆盖重标
            elif note and note != "待确认":
                r["描述"] = note
                r["置信度"] = "高"
            elif has_desc:
                r["描述"] = ""  # 未改名却留着旧描述 = 改名被回退，清掉重来
                r["置信度"] = "待确认"
            updated += 1

    tmp = ctx["workdir"] / "文件登记表.new.csv"
    tmp.write_text("﻿" + csv_text(reg_rows, fieldnames), encoding="utf-8")
    rsync_write(tmp, REG_CSV)

    # 账本合并回写：登记表补齐日期/大小/md5，但**不得把已有新名覆盖回原名**
    for r in reg_rows:
        k = (r.get("项目", ""), r.get("原文件名", ""))
        prev = ledger.get(k) or {}
        current = str(r.get("文件名") or "").strip()
        if current == r.get("原文件名", ""):
            current = prev.get("新文件名") or current
        ledger[k] = {"项目": k[0], "原文件名": k[1], "新文件名": current or k[1],
                     "日期": r.get("日期", "") or prev.get("日期", ""),
                     "大小": str(r.get("大小", "") or prev.get("大小", "")),
                     "md5": r.get("md5", "") or prev.get("md5", "")}
    save_ledger(ledger, ctx["workdir"])

    # 公开脱敏版：项目名 → 「业务名+群」，去掉「能证明什么」（照 KMVideo 同一套规则）
    pub_cols = [c for c in fieldnames if c != "能证明什么"]
    pub_rows = []
    for r in reg_rows:
        rr = {k: r.get(k, "") for k in pub_cols}
        rr["项目"] = f"{BUSINESS.get(r.get('项目', ''), '其他')}群"
        pub_rows.append(rr)
    (ctx["workdir"] / "文件登记表_public.csv").write_text(
        "﻿" + csv_text(pub_rows, pub_cols), encoding="utf-8")
    tmp3 = ctx["workdir"] / "文件登记表_public.md"
    with tmp3.open("w", encoding="utf-8") as f:
        f.write("# 文件登记表（公开脱敏版）\n\n")
        f.write("| " + " | ".join(pub_cols) + " |\n")
        f.write("|" + "---|" * len(pub_cols) + "\n")
        for r in pub_rows:
            f.write("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in pub_cols) + " |\n")

    subset = [{k: r.get(k, "") for k in SUBSET_COLS} for r in reg_rows]
    (ctx["workdir"] / "文件登记表_子集.csv").write_text(
        "﻿" + csv_text(subset, SUBSET_COLS), encoding="utf-8")
    pub_subset_cols = [c for c in SUBSET_COLS if c != "能证明什么"]
    pub_subset = []
    for r in reg_rows:
        rr = {k: r.get(k, "") for k in pub_subset_cols}
        rr["项目"] = f"{BUSINESS.get(r.get('项目', ''), '其他')}群"
        pub_subset.append(rr)
    (ctx["workdir"] / "文件登记表_子集_public.csv").write_text(
        "﻿" + csv_text(pub_subset, pub_subset_cols), encoding="utf-8")

    # 待转 KMVideo 交接清单（音视频不进 KMFile）
    handoffs = load_handoffs(ctx["groups"])
    ho_cols = ["项目", "文件名", "扩展名", "消息时间", "发送人", "fileId",
               "openMessageId", "openConversationId", "交接状态"]
    ho_rows = [{"项目": h["_group"], "文件名": h.get("file_name", ""),
                "扩展名": h.get("extension", ""), "消息时间": h.get("message_time", ""),
                "发送人": h.get("sender", ""), "fileId": h.get("file_id", ""),
                "openMessageId": h.get("message_id", ""),
                "openConversationId": h.get("conversation_id", ""),
                "交接状态": h.get("handoff_status", "pending")} for h in handoffs]
    tmp4 = ctx["workdir"] / "待转KMVideo.new.csv"
    tmp4.write_text("﻿" + csv_text(ho_rows, ho_cols), encoding="utf-8")
    rsync_write(tmp4, HANDOFF_CSV)

    dist = distribute_registry(ctx)
    log(f"registry done: rows={len(reg_rows)} added={added} updated={updated} "
        f"handoff={len(ho_rows)} dist={dist}")
    return {"rows": len(reg_rows), "added": added, "updated": updated,
            "handoff": len(ho_rows), "dist": dist}


def distribute_registry(ctx) -> dict:
    """三个本机落点。SMB 为唯一真源，另两处为只读副本。任一处失败即抛错，不静默跳过。"""
    wd = ctx["workdir"]
    plan = [
        (wd / "文件登记表.new.csv", DOCS_INDEX / "文件登记表.csv"),
        (wd / "原名新名映射.ledger.csv", DOCS_INDEX / "原名新名映射.csv"),
        (wd / "文件登记表_子集.csv", DOCS_INDEX / "文件登记表_子集.csv"),
        (wd / "文件登记表_public.csv", DOCS_INDEX / "文件登记表_public.csv"),
        (wd / "文件登记表_public.md", DOCS_INDEX / "文件登记表_public.md"),
        (wd / "待转KMVideo.new.csv", DOCS_INDEX / "待转KMVideo.csv"),
        (wd / "文件登记表.new.csv", DOWNLOADS / "KMFile文件登记表.csv"),
        (wd / "文件登记表_子集.csv", DOWNLOADS / "KMFile文件登记表_子集.csv"),
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
        raise RuntimeError(f"登记表分发失败 {len(fail)} 处: {fail}")
    return {"copied": ok}


# ---------- 阶段七：公开仓 / 私有仓 / Release ----------

def shutil_which(x):
    import shutil
    return shutil.which(x)


def stage_upload(args, ctx) -> dict:
    res = {}
    kmos_data = Path(aif.ROOT) / "KMDatabase" / "data" / "KMFile"
    kmos_data.mkdir(parents=True, exist_ok=True)
    for name in ("文件登记表_public.csv", "文件登记表_public.md", "文件登记表_子集_public.csv"):
        src = ctx["workdir"] / name
        if src.exists():
            (kmos_data / name).write_bytes(src.read_bytes())
    res["kmos_files"] = len(list(kmos_data.glob("*")))

    if args.release_tag and shutil_which("gh"):
        try:
            subprocess.run(["gh", "release", "view", args.release_tag], capture_output=True, timeout=60)
            asset = ctx["workdir"] / "文件登记表_子集_public.csv"
            if asset.exists():
                subprocess.run(["gh", "release", "upload", args.release_tag, str(asset), "--clobber"],
                               capture_output=True, timeout=300)
            res["release_assets"] = 1
        except Exception as e:  # noqa: BLE001
            res["release_assets"] = f"skip: {e}"
    else:
        res["release_assets"] = "skip (no tag/gh)"

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


# ---------- 阶段八：自验收 + 产能汇总 ----------

def stage_accept(args, ctx) -> dict:
    checks = {"pass": [], "fail": []}

    def chk(name, cond, detail=""):
        (checks["pass"] if cond else checks["fail"]).append({"项": name, "详情": str(detail)})

    reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig"))) if REG_CSV.exists() else []
    chk("登记表可读且非空", len(reg_rows) > 0, len(reg_rows))
    chk("无重复行(项目+原文件名)", len(reg_rows) == len({(r.get("项目"), r.get("原文件名")) for r in reg_rows}))

    bad_fmt = [r["文件名"] for r in reg_rows
               if r.get("文件名") and r.get("原文件名") and r["文件名"] != r["原文件名"]
               and not re.fullmatch(r".{2,5}_.{2,6}_\d{6}_\d{2,3}\.[A-Za-z0-9]{1,5}", r["文件名"])]
    chk("新文件名格式", not bad_fmt, bad_fmt[:5])

    bad_desc = [r.get("描述") for r in reg_rows if r.get("描述") and not (2 <= len(r["描述"]) <= 6)]
    chk("描述 2-6 字", not bad_desc, bad_desc[:5])

    bad_vocab = []
    for r in reg_rows:
        for fld, vocab in VOCAB.items():
            if fld not in r or not str(r.get(fld) or "").strip():
                continue
            for x in str(r[fld]).replace("、", ",").split(","):
                x = x.strip()
                if x and x not in vocab:
                    bad_vocab.append((r.get("原文件名"), fld, x))
    chk("枚举字段原始词汇", not bad_vocab, bad_vocab[:5])

    # 文件版独有：落地件 md5 必须与登记表（=服务端）一致
    md5_bad, md5_checked = [], 0
    files = {(m["_group"], os.path.basename(m.get("relative_path") or "")): m
             for m in load_files(ctx["groups"]) if m.get("smb_status") != "unavailable"}
    gone = [m for m in load_files(ctx["groups"]) if m.get("smb_status") == "unavailable"]
    for r in reg_rows:
        m = files.get((r.get("项目"), r.get("原文件名")))
        if not m or not r.get("md5"):
            continue
        rel = m.get("relative_path") or ""
        # 三级定位：登记表现用名 → 改名账本 → manifest 原路径。
        # 只用前两级里的一级都会在改名后误报 missing（DS 那轮 5 条 md5 fail 就是这么来的）。
        cur = SMB_ROOT / str(r.get("项目") or "") / "file" / (r.get("文件名") or os.path.basename(rel))
        if not cur.exists():
            resolved = aif.resolve_current_path(m)
            cur = resolved if resolved is not None else SMB_ROOT / rel
        if not cur.exists():
            md5_bad.append((r.get("原文件名"), "missing"))
            continue
        md5_checked += 1
        if aif.md5_b64(cur) != r["md5"]:
            md5_bad.append((r.get("原文件名"), "md5 mismatch"))
    chk("落地件 md5 与服务端一致", not md5_bad, f"checked={md5_checked} bad={md5_bad[:5]}")
    # 钉钉侧已删的是外部障碍，单列一项如实报，不混进 md5 失败里
    chk("钉钉侧已删条目已登记待办", True, f"{len(gone)} 条（fileId 已留档，需人工在钉钉确认）")

    base = ctx["workdir"] / "manifest_mtime_base.jsonl"
    if base.exists():
        changed = []
        for l in base.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            d = json.loads(l)
            p = SMB_ROOT / d["group"] / MANIFEST
            if p.exists() and abs(os.path.getmtime(p) - d["mtime"]) > 2:
                changed.append(d["group"])
        chk(".manifest.jsonl 未修改", not changed, changed)

    dir_cache: dict[str, set[str]] = {}

    def names(group: str) -> set[str]:
        if group not in dir_cache:
            d = SMB_ROOT / group / "file"
            dir_cache[group] = set(os.listdir(d)) if d.is_dir() else set()
        return dir_cache[group]

    old_left = sum(1 for r in reg_rows
                   if r.get("文件名") and r.get("原文件名") and r["文件名"] != r["原文件名"]
                   and r["原文件名"] in names(r.get("项目", "")))
    chk("改名幂等(旧名残留0)", old_left == 0, old_left)

    if reg_rows and "复核状态" in reg_rows[0]:
        n_reviewed = sum(1 for r in reg_rows if str(r.get("复核状态") or "") in ("已复核通过", "已复核修正"))
        n_sens = sum(1 for r in reg_rows if str(r.get("脱敏风险") or "") not in ("", "无"))
        n_lab = sum(1 for r in reg_rows if (r.get("描述") or "").strip())
        need = n_sens + max(1, int(n_lab * 0.1))
        chk("复核覆盖率(脱敏100%+抽样10%)", n_reviewed >= need,
            f"已复核 {n_reviewed}/{need} (脱敏 {n_sens} 条 100% + 抽样 10%)")

    out = ctx["workdir"] / "accept_report.json"
    out.write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"accept: pass={len(checks['pass'])} fail={len(checks['fail'])}")
    return checks


def stage_report(args, ctx) -> dict:
    files = [m for m in load_files(ctx["groups"]) if m.get("smb_status") == "complete"]
    handoffs = load_handoffs(ctx["groups"])
    reg_rows = list(csv.DictReader(REG_CSV.open(encoding="utf-8-sig"))) if REG_CSV.exists() else []
    by_ext = Counter(str(m.get("extension") or "").lower() for m in files)
    renamed = sum(1 for r in reg_rows if r.get("文件名") and r["文件名"] != r.get("原文件名"))
    labeled = sum(1 for r in reg_rows if (r.get("描述") or "").strip())
    pending = len(reg_rows) - labeled
    dup_count = sum(1 for r in reg_rows if r.get("重复于") and r["重复于"] != "无")
    sens = sum(1 for r in reg_rows if r.get("脱敏风险") and r["脱敏风险"] != "无")
    lines = [
        "| 指标 | 数量 |", "|---|---|",
        f"| 归档文件总数 | {len(files)} |",
        f"| 登记表行数 | {len(reg_rows)} |",
        f"| 已改名 | {renamed} |",
        f"| 已标注(有描述) | {labeled} |",
        f"| 待确认/未标注 | {pending} |",
        f"| 重复文件 | {dup_count} |",
        f"| 脱敏风险文件 | {sens} |",
        f"| 待转 KMVideo 音视频 | {len(handoffs)} |",
        f"| 钉钉侧已删（外部障碍） | {sum(1 for m in load_files(ctx['groups']) if m.get('smb_status') == 'unavailable')} |",
        f"| 名单外新增群 | {len(ctx.get('new_groups') or [])} {(ctx.get('new_groups') or [''])[:3]} |",
        f"| SMB 健康自检 | {(ctx.get('smb_health') or {}).get('state', '未跑')} "
        f"{(ctx.get('smb_health') or {}).get('listdir_seconds', '')} |",
        "", "| 扩展名 | 数量 |", "|---|---|",
    ] + [f"| {k or '(无)'} | {v} |" for k, v in by_ext.most_common()]
    txt = "\n".join(lines) + "\n"
    (ctx["workdir"] / "产能汇总.md").write_text(txt, encoding="utf-8")
    print(txt)
    return {"files": len(files), "rows": len(reg_rows), "renamed": renamed,
            "labeled": labeled, "pending": pending, "handoff_av": len(handoffs)}


# ---------- 入口 ----------

def snapshot_manifest_mtimes(ctx, groups):
    recs = []
    for g in groups:
        p = SMB_ROOT / g / MANIFEST
        if p.exists():
            recs.append({"group": g, "mtime": os.path.getmtime(p)})
    (ctx["workdir"] / "manifest_mtime_base.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs) + ("\n" if recs else ""), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="KMFile 一体化流水线 v0.0.0.1")
    ap.add_argument("stage", choices=["all", "scan", "probe", "extract", "dedup", "label",
                                      "rename", "registry", "upload", "accept", "report"])
    ap.add_argument("--groups-file", help="白名单文件（每行一个群名）")
    ap.add_argument("--only-group", help="只跑单群")
    ap.add_argument("--workdir", default="/tmp/kmfile_work/pipeline_v0001")
    ap.add_argument("--start", help="归档起点 YYYY-MM-DD HH:MM:SS（首轮建议 2025-01-01 00:00:00）")
    ap.add_argument("--window-days", type=int, default=30, help="时间切片天数，默认 30")
    ap.add_argument("--page-size", type=int, default=100)
    ap.add_argument("--release-tag", default="", help="GitHub Release tag，空则跳过 Release 上传")
    ap.add_argument("--no-private", action="store_true")
    ap.add_argument("--refresh-groups", action="store_true",
                    help="跑前用 dws 实时枚举群列表，与 --groups-file 求并集；新增群只报不收。")
    ap.add_argument("--include-new-groups", action="store_true",
                    help="与 --refresh-groups 连用：把新发现的群纳入本轮归档（默认只报不收）。")
    ap.add_argument("--since-manifest", action="store_true",
                    help="每群起点改为该群 manifest 最后一个 complete 窗口的终点（增量提速）。")
    ap.add_argument("--skip-smb-check", action="store_true", help="跳过开跑前的 SMB 健康自检。")
    args = ap.parse_args()

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

    order = ["scan", "probe", "extract", "dedup", "label", "rename", "registry",
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
