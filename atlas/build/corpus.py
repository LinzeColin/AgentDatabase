#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""corpus.py —— 把本机**所有 agent 的对话**导成一份可上传的语料。

Owner 的原话：「把 cc 和 codex 还有所有本地所有 agent 对话信息**全部都上传**到
private repo 并抽取提取沉淀经验，减少后续 agent 开发阻碍降低 token 损耗」。

上一版只推了蒸馏后的 `AGENT_BRIEF.md` —— 那是结论，不是语料。
结论只能回答「被问过几次」，回答不了「上次那条命令到底怎么写的」。

■ 「全部」到底包含什么 —— 这条必须说死，否则「全部」就是一句空话
  进：**你说的每一句话**（不截断）、会话元数据、模型/用量、
      工具指针（碰过的文件、跑过的命令）、话题、项目。
  不进：**助手输出与工具回显**。理由不是懒 ——
      实测原始来源合计约 5 GB，其中 99% 是助手正文与工具输出；
      而它们**可再生**（同一个提示词能再跑一遍），且正是它们让语料无法进 git。
      你的原话不可再生，那才是真正要留住的东西。
  结果：约 30 MB 明文。**故意不压缩** —— git 对文本做增量压缩，
      每天的新增只占几十 KB；压成 .gz 反而每天换一个全新的二进制块。

■ 硬门
  目标仓必须私有（里面有姓名、手机号、客户报价）。判不出来就拒绝推。
  这一条和 push_brief.sh 是同一条规矩，不重复实现，由 push_corpus.sh 统一把关。

运行期不调用任何模型。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import (SOURCES, PARSERS, blank, iso, redact, is_injected,  # noqa: E402
                     strip_injected, text_of, project_of, _dsh_prepare, _DSH_CACHE)

# ── 个人身份信息脱敏 ──
# extract.py 的 REDACT 只挡令牌和本机路径。**它不挡 PII。**
# 实测这份语料里有：邮箱 25 条、中国手机号 16 条、过 Luhn 的卡号 7 条、身份证形 1 条。
# 站点在 Cloudflare Access 后面只有你自己看，那是一回事；
# **进 git 是另一回事** —— 仓会被 clone、会加协作者、历史删不掉。
# 所以上传前必须再过一层。
#
# ★ 卡号判据是「长度 ∈ {16,19} **且** 过 Luhn」，两条缺一不可：
#   只看长度会把工单号、哈希、时间戳全打成 <CARD>；
#   只看 Luhn 也不行 —— 随机数字串过 Luhn 的概率是 1/10，
#   实测 14 位的工单号 20260817093012 就正好过了。
#   16/19 是 Visa/MC/银联的实际长度，覆盖住这台机器上真出现过的那 7 条。
PII = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"), "<EMAIL>"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "<PHONE>"),
    (re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "<ID>"),
]
CARD_LEN = {16, 19}
_DIGITS = re.compile(r"(?<!\d)\d{16,19}(?!\d)")
# 家目录路径归一。extract 的 REDACT 按**精确串** `/Users/linzezhang` 替换，
# 而对话里的路径常常被上游截断成 `/Users/linzez` —— 精确串就打不中了。
# 出仓的东西不该带任何用户名，所以这里按形态一律归一成 `~`。
_HOME = re.compile(r"/Users/[A-Za-z0-9_.\-]*")


def _luhn(num: str) -> bool:
    tot, alt = 0, False
    for ch in reversed(num):
        d = ord(ch) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        tot += d
        alt = not alt
    return tot % 10 == 0


def redact_pii(t: str) -> str:
    """在 extract 的脱敏之上再过一层 PII。返回的字符串才可以进仓。"""
    t = _HOME.sub("~", t)
    for rx, rep in PII:
        t = rx.sub(rep, t)
    return _DIGITS.sub(
        lambda m: "<CARD>" if (len(m.group(0)) in CARD_LEN and _luhn(m.group(0))) else m.group(0), t)


def scrub(o):
    """**在出口对整条记录递归脱敏**，而不是逐个字段挑。

    第一版只给 prompts 和 title 脱敏，结果 cmds / files 里照样漏出
    sk-proj-… 和邮箱 —— 白名单字段的写法在解析器新增字段时必然失守。
    脱敏必须发生在**边界**上：凡是要离开这台机器的字符串，一个不漏地过一遍。
    """
    if isinstance(o, str):
        return redact_pii(redact(o))
    if isinstance(o, list):
        return [scrub(x) for x in o]
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items()}
    return o


# 会话记录里带出去的字段。**白名单而不是黑名单** ——
# 黑名单的写法在解析器新增字段时会静默漏出去。
KEEP = ("id", "source", "start", "end", "project", "title", "kind", "batch",
        "turns", "msgs", "tools", "errors", "errors_tool", "models", "topics",
        "tok_in", "tok_out", "tok_cache_r", "tok_cache_w", "cost_cny",
        "files", "cmds", "provider_hint", "effort", "span_min", "hourly")


def full_prompts_cc(path: Path) -> list:
    """Claude Code：把用户发言原样取出来，**不截断**。

    extract.py 为了控制 atlas.json 体积，只留 12 条 × 400 字。
    那份是给页面看的；这一份是给下一个 agent 查的，不能截。
    """
    out = []
    for line in path.open(encoding="utf-8", errors="ignore"):
        if '"type":"user"' not in line and '"type": "user"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        body, _ = text_of(m.get("content"))
        if body and not is_injected(body):
            out.append({"at": iso(d.get("timestamp")), "text": redact_pii(redact(strip_injected(body)))})
    return out


def full_prompts_codex(path: Path) -> list:
    out = []
    for line in path.open(encoding="utf-8", errors="ignore"):
        if '"message"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        p = d.get("payload")
        if not isinstance(p, dict) or p.get("type") != "message" or p.get("role") != "user":
            continue
        body, _ = text_of(p.get("content"))
        if body and not is_injected(body):
            out.append({"at": iso(d.get("timestamp")), "text": redact_pii(redact(strip_injected(body)))})
    return out


def full_prompts_kimi(path: Path) -> list:
    out = []
    for line in path.open(encoding="utf-8", errors="ignore"):
        if '"context.append_message"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        if m.get("role") != "user":
            continue
        body, _ = text_of(m.get("content"))
        if body and not is_injected(body):
            out.append({"at": iso(d.get("time")), "text": redact_pii(redact(strip_injected(body)))})
    return out


def full_prompts_dsh(path: Path) -> list:
    d = _DSH_CACHE.get(str(path)) or {}
    return [{"at": "", "text": redact_pii(redact(strip_injected(t)))}
            for t in (d.get("prompts") or []) if t and not is_injected(t)]


def full_prompts_chatgpt(path: Path) -> list:
    """仓内 ChatGPT 导出：{created_at, messages:[{created_at, role, text}]}。

    ChatGPT 是 Owner 点名清单里的第一个，379 场不能只有截断版。
    """
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return []
    out = []
    for m in (d.get("messages") or []):
        if not isinstance(m, dict) or m.get("role") != "user":
            continue
        body = m.get("text") or ""
        if body and not is_injected(body):
            out.append({"at": iso(m.get("created_at")), "text": redact_pii(redact(strip_injected(body)))})
    return out


FULL = {"cc": full_prompts_cc, "codex": full_prompts_codex,
        "kimi": full_prompts_kimi, "dsh": full_prompts_dsh,
        "chatgpt": full_prompts_chatgpt}


def build(sessions_dir: Path, out_dir: Path, repo_root: Path | None = None) -> dict:
    """按来源导出语料。会话记录来自已抽取的产物，全量发言现读源文件。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    for f in sorted(sessions_dir.glob("*.sessions.jsonl")):
        name = f.name.split(".")[0]
        cfg = SOURCES.get(name) or {}
        root = cfg.get("root")
        if root is not None and cfg.get("repo_relative") and repo_root:
            root = repo_root / root
        parser = cfg.get("parser")
        getter = FULL.get(parser)
        if parser == "dsh" and root and Path(root).is_dir():
            _dsh_prepare(Path(root))

        rows, n_full, n_chars, no_src = [], 0, 0, 0
        for line in f.open(encoding="utf-8"):
            s = json.loads(line)
            rec = {k: s[k] for k in KEEP if k in s}
            # 标题也是 Owner 写的，同样要过 PII
            if rec.get("title"):
                rec["title"] = redact_pii(rec["title"])
            # 默认用抽取时留下的那份（已截断）；能拿到源文件就换成全量。
            rec["prompts"] = [{"at": "", "text": redact_pii(p)} for p in (s.get("prompts") or [])]
            rec["prompts_truncated"] = True
            src = s.get("file", "")
            if getter and src:
                real = Path(src.replace("~", str(Path.home()), 1)) if src.startswith("~") else Path(src)
                if real.is_file():
                    try:
                        full = getter(real)
                    except Exception:
                        full = []
                    if full:
                        rec["prompts"] = full
                        rec["prompts_truncated"] = False
                        n_full += 1
                        n_chars += sum(len(x["text"]) for x in full)
                else:
                    no_src += 1
            rows.append(rec)

        rows = [scrub(r) for r in rows]
        rows.sort(key=lambda r: (r.get("start") or "", r.get("id") or ""))
        dst = out_dir / f"{name}.corpus.jsonl"
        # 明文 + 稳定排序：git 按行做增量，每天新增只占几十 KB。
        # 压成 .gz 的话每天换一个全新二进制块，仓会以每天一整份的速度涨。
        dst.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
                               for r in rows), encoding="utf-8")
        stats[name] = {"sessions": len(rows), "with_full_prompts": n_full,
                       "prompt_chars": n_chars, "source_missing": no_src,
                       "bytes": dst.stat().st_size}
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True, help="extract.py 的产出目录")
    ap.add_argument("--out", required=True, help="语料落在哪")
    ap.add_argument("--repo", default="", help="仓根（chatgpt 那类仓内来源要用）")
    a = ap.parse_args()
    st = build(Path(a.sessions), Path(a.out), Path(a.repo) if a.repo else None)
    tot_b = sum(v["bytes"] for v in st.values())
    tot_s = sum(v["sessions"] for v in st.values())
    tot_f = sum(v["with_full_prompts"] for v in st.values())
    for k, v in sorted(st.items(), key=lambda x: -x[1]["bytes"]):
        print(f"  {k:<16}{v['sessions']:>5} 场  全量发言 {v['with_full_prompts']:>5} 场  "
              f"{v['prompt_chars'] / 1e6:>6.2f}M 字  {v['bytes'] / 1048576:>6.2f} MB"
              + (f"  源已删 {v['source_missing']}" if v["source_missing"] else ""))
    print(f"\n合计 {tot_s} 场，其中 {tot_f} 场拿到了全量发言，{tot_b / 1048576:.1f} MB")
    # 拿不到全量的那部分必须自己站出来说 —— 沉默地用截断版顶替就是假的「全部上传」
    if tot_f < tot_s:
        print(f"⚠ 有 {tot_s - tot_f} 场只能用抽取时的截断版（源文件已删，或该来源没有全量读取器）。"
              f"这些记录上带 prompts_truncated=true，不会假装是全量。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
