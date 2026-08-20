#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract.py —— 把本机各 agent 的会话抽成一行一会话的记录。

纯标准库。运行期不调用任何模型（合同 §2.4）。每天由 codex 增量跑一次：
未改动的文件直接复用缓存里的记录，所以第二天起只解析当天新写的文件。

输出 build/../out/<source>.sessions.jsonl —— 每行一个会话，字段见 SESSION_FIELDS。
同一个文件既是输出也是缓存：下次运行按 (mtime_ns, size) 判断是否需要重解析。

用法:
  python3 extract.py --out <目录>              # 全部来源，增量
  python3 extract.py --out <目录> --source codex --full   # 单来源，强制重解析
退出码: 0=成功 1=没有任何来源可读
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
APPSUP = HOME / "Library" / "Application Support"

# 本文件自身的指纹。进缓存键 —— 解析逻辑一变，所有缓存自动失效。
PARSER_FINGERPRINT = hashlib.sha256(
    Path(__file__).read_bytes()).hexdigest()[:8] if Path(__file__).is_file() else "dev"

# 本机实测位置（2026-08-20）。payload 是真实会话载荷，已剔除安装包与缓存。
SOURCES = {
    "claude-code": {"root": HOME / ".claude" / "projects",  "glob": "**/*.jsonl", "parser": "cc"},
    "codex":       {"root": HOME / ".codex" / "sessions",   "glob": "**/*.jsonl", "parser": "codex"},
    "kimi-code":   {"root": HOME / ".kimi-code" / "sessions", "glob": "**/*.jsonl", "parser": "kimi"},
    # DeepSeek Harness。会话是 zstd 压缩的 JSONL，本机 Python 3.9 没有 zstd
    # （stdlib 要 3.14+），用 node 的 zlib.zstdDecompressSync 解 —— DSH 自己的
    # 归档脚本也是这么做的。node 缺席时该来源标「不确定」，不静默跳过。
    "dsh":         {"root": HOME / ".dsh" / "sessions", "glob": "**/session.jsonl.zstd", "parser": "dsh"},
    "dws":         {"root": HOME / ".dws" / "audit",        "glob": "**/*.jsonl", "parser": "generic"},
    "openchatcut": {"root": HOME / ".openchatcut" / "project-store-v1", "glob": "**/*.json", "parser": "generic"},
    "claude-desktop": {"root": APPSUP / "Claude" / "claude-code-sessions", "glob": "**/*.json", "parser": "cdmeta"},
    # 仓内已入库的历史导出，回溯到 2025-11。路径相对仓根，由 --repo 指定。
    "chatgpt": {"root": Path("OpenAIDatabase/data/public_raw/chatgpt"), "glob": "*.json",
                "parser": "chatgpt", "repo_relative": True},
}

# 查过、确认没有对话内容的来源。**必须出现在产物里**，否则「筛掉的那部分」
# 不参与任何总量校验，总量就永远显得是对的（合同 §2.3 判据一）。
SKIPPED = {
    "dsh-desktop": {"path": "~/Library/Application Support/DSH Desktop", "size_mb": 1100,
                    "why": "Electron 缓存，无对话。真正的 DSH 会话在 ~/.dsh/sessions，已入库（source_id=dsh）"},
    "workbuddy": {"path": "~/.workbuddy",       "size_mb": 1300, "why": "应用安装包与运行日志，非对话"},
    "mmx":       {"path": "~/.mmx",             "size_mb": 0,    "why": "仅配置文件 8KB"},
    "kimi-desktop": {"path": "~/Library/Application Support/kimi-desktop", "size_mb": 428, "why": "缓存与共享资源，对话在云端"},
    "claude-vm": {"path": "~/Library/Application Support/Claude/vm_bundles", "size_mb": 10240, "why": "虚拟机镜像，非对话"},
}

REDACT = [
    (re.compile(re.escape(str(HOME))), "~"),
    # 令牌形态按**前缀族**匹配，不按字段名。实测踩过：MiniMax 的
    # access_token / refresh_token 嵌在 oauth 这一层里，按键名过滤完全挡不住。
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9\-]{20,}|AKIA[0-9A-Z]{16}|"
                r"oat-[A-Za-z0-9_\-]{16,}|dfrt-[A-Za-z0-9_\-]{16,}|"
                r"xox[baprs]-[A-Za-z0-9\-]{10,}|glpat-[A-Za-z0-9_\-]{16,}|"
                r"eyJ[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{8,})\b"), "<SECRET>"),
    # 任何 "xxx_token"/"xxx_secret"/"apiKey" 的取值也一并抹掉，兜住没见过的前缀
    (re.compile(r'("?(?:access|refresh|api|auth|bearer|client)[_-]?(?:token|secret|key)"?\s*[:=]\s*"?)[^",\s}]{12,}',
                re.I), r"\1<SECRET>"),
]

# 主题词。中英混排是因为实际对话就是混着说的。
# 「赚钱」这一类刻意做得宽：Owner 三个月的核心疑问就是钱去哪了，
# 宁可多认一点，也不要因为词表太窄让这一类恒为 0 而看不出问题。
TOPICS = {
    # —— 写代码这一侧 ——
    "修bug":     ["报错", "失败了", "error", "修一下", "traceback", "崩了", "红了", "不work", "挂了"],
    "部署上线":   ["部署", "上线", "deploy", "生产环境", "production", "发布", "docker", "服务器", "域名"],
    "重构简化":   ["重构", "简化", "清理", "refactor", "瘦身", "去重", "删掉", "精简"],
    "测试验收":   ["测试", "验收", "unittest", "负控", "变异测试", "断言", "跑一遍"],
    "数据":      ["数据库", "备份", "迁移", "sqlite", "postgres", "schema", "索引", "数据源"],
    "自动化":     ["自动化", "cron", "定时", "workflow", "流水线", "脚本跑", "无人值守"],
    "治理规范":   ["治理", "governance", "agents.md", "铁律", "复审", "审计", "规范", "架构"],
    "文档":      ["文档", "readme", "说明书", "手册", "写清楚"],
    "前端界面":   ["前端", "界面", "ui", "页面", "样式", "可视化", "图表", "好看"],
    # —— 本职工作这一侧。这几类不单列，就会被当成「治理」——
    # 实测：填委外单的会话因为「合同」二字被判成治理，一整类真实工作被吞掉。
    "办公文书":   ["excel", "表格", "模版", "模板", "委外单", "报销", "发放", "工资",
                "ppt", "word", "排版", "打印", "台账", "填写", "汇总表"],
    "业务方案":   ["方案", "工艺", "投标", "报价", "需求清单", "痛点", "素材", "视频",
                "客户", "甲方", "现场", "设备", "验收单", "施工"],
    # —— 钱这一侧。刻意收紧：只留直接谈钱的词，否则「客户/市场/增长」会把
    # 普通开发对话也算成赚钱，让这一类虚高到看不出真实占比 ——
    "赚钱":      ["赚钱", "收入", "变现", "盈利", "定价", "付费", "订单", "销售额",
                "商业模式", "monetiz", "revenue", "pricing", "利润", "经济价值"],
    "找工作":     ["简历", "求职", "面试", "投递", "jobhunt", "岗位", "offer"],
    "学习":      ["为什么会", "原理", "教程", "怎么理解", "解释一下", "学一下"],
}

# 一个会话最多留几条用户原话（给日记用）。留多了产物会膨胀，留少了日记没内容。
MAX_PROMPTS = 12
PROMPT_CHARS = 400

# 机器触发的单轮会话。混进「我今天开了 N 个会话」里会让活跃度虚高，
# 而这正是 Owner 最怕的那种假绿：数字很好看，但那不是他干的活。
AUTO_PROMPTS = (
    "reply with only", "review the current code changes", "review the code changes against",
    "continue the conversation", "summarize the following", "ok", "ping", "健康检查",
)


def session_kind(rec: dict) -> str:
    """human = 人真的在对话；auto = 机器触发或无人发言。"""
    if rec["turns"] == 0:
        return "auto"
    if rec["turns"] == 1 and rec["prompts"]:
        first = rec["prompts"][0].strip().lower()
        if first.startswith("/") or first.startswith(AUTO_PROMPTS) or len(first) < 12:
            return "auto"
    return "human"


# 三家 agent 都会把系统提示、环境上下文、工具回包塞成 role=user。
# 实测后果：AGENTS.md 正文里几乎每个主题词都出现一次，不滤掉就会让
# 455 个 codex 会话**全部**命中 9~10 个主题，主题分布彻底失真。
INJECTED = (
    "# agents.md", "<instructions>", "<environment_context>", "<permissions instructions>",
    "<system-reminder>", "<user_instructions>", "<command-name>", "<local-command-stdout>",
    "# instructions", "caveat: the messages below", "<ide_", "<user-prompt-submit-hook>",
    "<task>", "<attachment", "[request interrupted", "# claude.md", "<repo_instructions>",
    "# files mentioned by the user", "# file mentioned by the user", "<attached",
    # 上下文压缩后自动注入的续接说明，不是人说的话
    "this session is being continued", "本会话是上一次对话的延续", "analysis:",
    # DSH 会把运行时状态变更也塞成 user/message
    "the approval policy changed", "the sandbox mode changed", "permission preset",
)


# 开头的注入块：`<git-context .../>`、`<system-reminder>...</system-reminder>` 之类。
# 直接整条丢弃是错的 —— 标签后面往往紧跟着人真正说的话（kimi 每一轮都这样）。
LEAD_TAG = re.compile(r"^\s*<([a-z][a-z0-9_\-]{1,40})\b[^>]*(?:/>|>.*?</\1>)\s*", re.S | re.I)


def strip_injected(text: str) -> str:
    """剥掉开头连续的注入标签块，返回人真正说的那部分。"""
    prev = None
    while prev != text:
        prev = text
        text = LEAD_TAG.sub("", text, count=1)
    return text.strip()


def is_injected(text: str) -> bool:
    """整段都是系统注入、没有人话时为真。"""
    t = strip_injected(text).lower()
    return (not t) or t.startswith(INJECTED)


def _under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def redact(s: str) -> str:
    for pat, rep in REDACT:
        s = pat.sub(rep, s)
    return s


def iso(ts) -> str:
    """把各家的时间戳统一成 UTC ISO。认 ISO 字符串、秒、毫秒。"""
    if ts is None:
        return ""
    if isinstance(ts, str):
        t = ts.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(t).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return ""
    if isinstance(ts, (int, float)):
        # 13 位是毫秒。用 1e11 分界（1970 年后的秒不会超过它，毫秒一定超过）。
        v = ts / 1000.0 if ts > 1e11 else float(ts)
        try:
            return datetime.fromtimestamp(v, timezone.utc).isoformat().replace("+00:00", "Z")
        except Exception:
            return ""
    return ""


def project_of(cwd: str) -> str:
    """把 cwd 变成人看得懂的项目名。GithubProject 下取仓名，其余取末级目录。"""
    if not cwd:
        return "未知"
    p = redact(cwd).strip("/")
    parts = [x for x in p.split("/") if x]
    if "GithubProject" in parts:
        i = parts.index("GithubProject")
        tail = parts[i + 1:]
        if not tail:
            return "GithubProject"
        if tail[0] == "_scratch" and len(tail) > 1:
            return f"_scratch/{tail[1]}"
        return tail[0]
    return parts[-1] if parts else "未知"


def count_keywords(text: str) -> dict:
    """每个关键词的命中次数。主题归并与权重放在 build 阶段做：

    「方案」「客户」这类词几乎每场对话都出现，按出现次数算权重会让一个主题
    吞掉六成会话（实测 业务方案 1055/1752）。要按整个语料的稀有度降权，
    而稀有度只有把所有会话都数完才知道 —— 所以这里只数，不判。
    """
    low = text.lower()
    out = {}
    for words in TOPICS.values():
        for w in words:
            n = low.count(w.lower())
            if n:
                out[w] = n
    return out


def text_of(content) -> tuple:
    """message.content -> (人说的话, 工具回包条数)。

    只认 type 为 text/input_text/output_text 的块。tool_result 也挂在 role=user 下，
    照着 `text or content` 取会把每一次工具返回都算成一个用户轮次 ——
    实测能把真实轮次放大一个数量级。
    """
    if isinstance(content, str):
        return content, 0
    if not isinstance(content, list):
        return "", 0
    out, tools = [], 0
    for c in content:
        if isinstance(c, str):
            out.append(c)
        elif isinstance(c, dict):
            ct = c.get("type") or ""
            if ct in ("tool_result", "tool_use", "function_call_output", "custom_tool_call_output"):
                tools += 1
            elif ct in ("text", "input_text", "output_text") or (not ct and isinstance(c.get("text"), str)):
                t = c.get("text")
                if isinstance(t, str):
                    out.append(t)
    return "\n".join(out), tools


def blank(sid: str, source: str, path: Path) -> dict:
    return {
        "id": sid, "source": source, "file": redact(str(path)),
        "start": "", "end": "", "project": "", "title": "",
        "turns": 0, "msgs": 0, "tools": 0, "errors": 0,
        "tok_in": 0, "tok_out": 0, "tok_cache_r": 0, "tok_cache_w": 0,
        "models": [], "kw": {}, "topics": [], "prompts": [], "bytes": 0,
        "tool_names": {}, "provider_hint": "", "effort": "",
        "kind": "human", "batch": "", "dsh_origin": "", "dsh_preset": "",
    }


def parse_cc(path: Path, rec: dict) -> dict:
    """Claude Code / Claude Desktop 的 ~/.claude/projects/**.jsonl

    先做子串判断再 json.loads：助手正文和工具输出占 84% 的行，我们一条都不需要，
    对 150MB 的会话这一步能省掉大部分解析成本。
    """
    models, prompts, texts = set(), [], []
    # 同一个 message.id 只许计一次用量 —— 见下面 usage 累加处的长注释
    seen_usage: set[str] = set()
    for line in path.open(encoding="utf-8", errors="ignore"):
        need_usage = '"usage"' in line
        need_user = '"type":"user"' in line or '"type": "user"' in line
        need_title = '"ai-title"' in line or '"custom-title"' in line
        need_meta = not rec["start"] and '"timestamp"' in line
        if not (need_usage or need_user or need_title or need_meta):
            # 助手/工具行只计数，不解析
            if '"type":"assistant"' in line:
                rec["msgs"] += 1
            if '"tool_use"' in line:
                rec["tools"] += 1
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        ts = iso(d.get("timestamp"))
        if ts:
            if not rec["start"] or ts < rec["start"]:
                rec["start"] = ts
            if ts > rec["end"]:
                rec["end"] = ts
        if d.get("cwd") and not rec["project"]:
            rec["project"] = project_of(d["cwd"])
        if t in ("ai-title", "custom-title"):
            ttl = d.get("title") or d.get("customTitle") or d.get("aiTitle")
            if isinstance(ttl, str) and ttl.strip():
                rec["title"] = redact(ttl.strip())[:120]
        m = d.get("message")
        if isinstance(m, dict):
            if m.get("model"):
                models.add(m["model"])
            u = m.get("usage")
            for blk in (m.get("content") or []):
                if isinstance(blk, dict) and blk.get("type") == "tool_use" and blk.get("name"):
                    nm = str(blk["name"])[:40]
                    rec["tool_names"][nm] = rec["tool_names"].get(nm, 0) + 1
            # 一个 API 响应在 JSONL 里**不是一条记录**：它按 content block 拆成多行
            # （1 个 thinking + 6 个并行 tool_use = 7 行），而**每一行都带着同一份完整的
            # usage**；会话 resume 时还会把整段历史再重放一遍。
            #
            # 直接 += 的后果实测过：全语料 322,284 条 usage 记录只对应 130,138 个不同的
            # message.id —— 每个响应被算了 2.48 次（独立抽样 60 个文件复核得 2.26 次）。
            # 更糟的是**虚高不均匀**：一轮里并行工具调用越多虚高越狠，单场 1×–4.99×，
            # 于是按天/周/来源的排序被非均匀扭曲，乘个常数修不好。
            #
            # 为什么这个 bug 活了这么久：**命中率对它免疫** —— 四类 token 一起虚高，
            # 比值几乎不变（99.998007% → 99.998682%），而命中率正是这一块最常被看的数。
            if isinstance(u, dict):
                mid = m.get("id")
                if not mid or mid not in seen_usage:
                    if mid:
                        seen_usage.add(mid)
                    rec["tok_in"] += int(u.get("input_tokens") or 0)
                    rec["tok_out"] += int(u.get("output_tokens") or 0)
                    rec["tok_cache_r"] += int(u.get("cache_read_input_tokens") or 0)
                    rec["tok_cache_w"] += int(u.get("cache_creation_input_tokens") or 0)
            if t == "user":
                rec["msgs"] += 1
                body, tool_blocks = text_of(m.get("content"))
                rec["tools"] += tool_blocks
                if body and not is_injected(body):
                    rec["turns"] += 1
                    texts.append(body)
                    if len(prompts) < MAX_PROMPTS:
                        prompts.append(redact(strip_injected(body))[:PROMPT_CHARS])
    rec["models"] = sorted(models)
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["errors"] = joined.lower().count("error") + joined.count("报错")
    rec["kw"] = count_keywords(joined)
    if not rec["title"] and prompts:
        rec["title"] = prompts[0][:80]
    return rec


def parse_codex(path: Path, rec: dict) -> dict:
    """Codex 的 rollout-*.jsonl：session_meta / response_item / event_msg。"""
    models, prompts, texts = set(), [], []
    for line in path.open(encoding="utf-8", errors="ignore"):
        if '"reasoning"' in line and '"session_meta"' not in line:
            rec["msgs"] += 1
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        ts = iso(d.get("timestamp"))
        if ts:
            if not rec["start"] or ts < rec["start"]:
                rec["start"] = ts
            if ts > rec["end"]:
                rec["end"] = ts
        p = d.get("payload")
        if not isinstance(p, dict):
            continue
        pt = p.get("type")
        if d.get("type") == "session_meta":
            if p.get("cwd"):
                rec["project"] = project_of(p["cwd"])
            if p.get("model"):
                models.add(p["model"])
        elif d.get("type") == "turn_context":
            # 真正带模型的是 turn_context，不是 session_meta。漏了这一支，
            # 455 场 codex 会全部显示「未记录模型」——实测就是这么错的。
            if p.get("model"):
                models.add(str(p["model"]))
            if p.get("model_provider"):
                rec["provider_hint"] = str(p["model_provider"])
            if p.get("effort"):
                rec["effort"] = str(p["effort"])
        elif pt == "token_count":
            # 累计值挂在 info.total_token_usage 下，不是 info 本身。取 max 而不是求和：
            # 每一轮都会重报一次累计数，求和会把用量放大几十倍。
            usage = ((p.get("info") or {}).get("total_token_usage") or {})
            inp = usage.get("input_tokens")
            cached = usage.get("cached_input_tokens") or 0
            out = usage.get("output_tokens")
            # 口径统一：codex 的 input_tokens **含**缓存命中，claude-code 的**不含**
            # （它把缓存单列成 cache_read_input_tokens）。不减掉就是把两种口径相加，
            # 单场会被抬到 24 亿这种量级，看着像天文数字其实是重复计数。
            if isinstance(inp, (int, float)):
                rec["tok_in"] = max(rec["tok_in"], int(inp) - int(cached))
            if isinstance(cached, (int, float)):
                rec["tok_cache_r"] = max(rec["tok_cache_r"], int(cached))
            if isinstance(out, (int, float)):
                rec["tok_out"] = max(rec["tok_out"], int(out))
        elif pt in ("function_call", "custom_tool_call", "local_shell_call"):
            rec["tools"] += 1
            nm = p.get("name") or p.get("tool_name") or pt
            rec["tool_names"][str(nm)[:40]] = rec["tool_names"].get(str(nm)[:40], 0) + 1
        elif pt == "message":
            rec["msgs"] += 1
            role = p.get("role")
            if role == "user":
                body, tool_blocks = text_of(p.get("content"))
                rec["tools"] += tool_blocks
                if body and not is_injected(body):
                    rec["turns"] += 1
                    texts.append(body)
                    if len(prompts) < MAX_PROMPTS:
                        prompts.append(redact(strip_injected(body))[:PROMPT_CHARS])
        elif pt == "agent_message":
            rec["msgs"] += 1
    rec["models"] = sorted(models)
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["errors"] = joined.lower().count("error") + joined.count("报错")
    rec["kw"] = count_keywords(joined)
    rec["title"] = (prompts[0][:80] if prompts else "codex 会话")
    return rec


def parse_generic(path: Path, rec: dict) -> dict:
    """kimi-code / dws / openchatcut：结构各异，按 role+content 的通用形状尽力抽。"""
    prompts, texts = [], []
    raw = path.read_text(encoding="utf-8", errors="ignore")
    docs = []
    if path.suffix == ".json":
        try:
            j = json.loads(raw)
            docs = j if isinstance(j, list) else [j]
        except Exception:
            docs = []
    else:
        for line in raw.splitlines():
            try:
                docs.append(json.loads(line))
            except Exception:
                continue

    def walk(o):
        if isinstance(o, dict):
            role = o.get("role")
            if role in ("user", "human"):
                body, tool_blocks = text_of(o.get("content") or o.get("text"))
                rec["tools"] += tool_blocks
                if body and not is_injected(body):
                    rec["turns"] += 1
                    texts.append(body)
                    if len(prompts) < MAX_PROMPTS:
                        prompts.append(redact(strip_injected(body))[:PROMPT_CHARS])
            elif role in ("assistant", "model"):
                rec["msgs"] += 1
            for k in ("timestamp", "created_at", "createdAt", "time", "ts", "lastActivityAt"):
                if k in o:
                    ts = iso(o[k])
                    if ts:
                        if not rec["start"] or ts < rec["start"]:
                            rec["start"] = ts
                        if ts > rec["end"]:
                            rec["end"] = ts
            for k in ("cwd", "workspace", "projectPath"):
                if o.get(k) and not rec["project"]:
                    rec["project"] = project_of(str(o[k]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for d in docs:
        walk(d)
    rec["msgs"] += rec["turns"]
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["kw"] = count_keywords(joined)
    rec["errors"] = joined.lower().count("error")
    rec["title"] = (prompts[0][:80] if prompts else f"{rec['source']} 会话")
    return rec


def parse_cdmeta(path: Path, rec: dict) -> dict:
    """Claude Desktop 的会话元数据：给出 model / branch / cwd / 起止时间。

    正文在 ~/.claude/projects 里已经抽过，这里**只补元数据不重复计会话**，
    所以 turns/msgs 保持 0，由 build 阶段按 cliSessionId 合并。
    """
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return rec
    if not isinstance(d, dict):
        return rec
    rec["start"] = iso(d.get("createdAt"))
    rec["end"] = iso(d.get("lastActivityAt") or d.get("lastFocusedAt"))
    rec["project"] = project_of(d.get("originCwd") or d.get("cwd") or "")
    if d.get("model"):
        rec["models"] = [d["model"]]
    rec["title"] = redact(str(d.get("title") or ""))[:120]
    rec["link"] = d.get("cliSessionId") or ""
    return rec


_NODE = shutil.which("node") or str(HOME / ".local" / "bin" / "node")
_DSH_HELPER = Path(__file__).resolve().parent / "helpers" / "dsh_reduce.js"
_DSH_CACHE: dict = {}
_DSH_BATCH = 220          # 一次给 node 多少个文件；太多会顶穿 argv 上限


def _dsh_prepare(root: Path) -> None:
    """一次 node 进程归约全部 DSH 会话。

    两件必须知道的事：
    1. DSH 把**每一行当成独立的 zstd 帧**追加，一个文件里能有上千帧。
       zstdDecompressSync 只解第一帧 —— 照着它拿，每个会话只会得到那条
       session 元数据（273 字节），正文一行都读不到。实测就是这么错的：
       1937 场全是 0 轮 0 消息，看起来"抽到了"，其实什么都没抽到。
    2. 一次 node 进程处理全部文件。1937 个文件各起一个进程要几分钟。

    本机 Python 3.9 没有 zstd（stdlib 要 3.14+），所以借 node 的 zlib；
    DSH 自己的归档脚本也是这么解的。node 缺席就抛错，不静默跳过。
    """
    if _DSH_CACHE:
        return
    if not Path(_NODE).is_file() or not _DSH_HELPER.is_file():
        raise RuntimeError("node_or_helper_missing")
    files = [str(p) for p in sorted(root.rglob("session.jsonl.zstd"))]
    for i in range(0, len(files), _DSH_BATCH):
        r = subprocess.run([_NODE, str(_DSH_HELPER), *files[i:i + _DSH_BATCH]],
                           capture_output=True, timeout=900)
        for line in r.stdout.decode("utf-8", "ignore").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            _DSH_CACHE[d["path"]] = d


def parse_dsh(path: Path, rec: dict) -> dict:
    """DeepSeek Harness 的 session.jsonl.zstd（多帧 zstd，见 helpers/dsh_reduce.js）。"""
    d = _DSH_CACHE.get(str(path))
    if not d or not d.get("ok"):
        raise RuntimeError("dsh_decode_failed")
    if d.get("first"):
        rec["start"] = iso(d["first"])
    if d.get("last"):
        rec["end"] = iso(d["last"])
    rec["project"] = project_of(d.get("cwd") or "")
    rec["msgs"] = d.get("msgs", 0) + d.get("turns", 0)
    rec["tools"] = d.get("tools", 0)
    rec["tool_names"] = d.get("toolNames") or {}
    if d.get("model"):
        rec["models"] = [f'{d.get("provider", "")}/{d["model"]}'.strip("/")]
    if d.get("provider"):
        rec["provider_hint"] = d["provider"]

    prompts, texts = [], []
    for raw in (d.get("prompts") or []):
        if is_injected(raw):
            continue
        texts.append(raw)
        if len(prompts) < MAX_PROMPTS:
            prompts.append(redact(strip_injected(raw))[:PROMPT_CHARS])
    rec["turns"] = len(texts)
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["errors"] = joined.lower().count("error") + joined.count("报错")
    rec["kw"] = count_keywords(joined)
    rec["title"] = redact(d.get("title") or "")[:120] or (prompts[0][:80] if prompts else "dsh 会话")
    # DSH 的子代理会话带 origin=subagent —— 那是扇出，不是你在对话。
    rec["dsh_origin"] = d.get("origin") or ""
    rec["dsh_preset"] = d.get("preset") or ""
    return rec


def parse_kimi(path: Path, rec: dict) -> dict:
    """Kimi Code 的 wire.jsonl。

    用户发言同时出现在 turn.prompt 和 context.append_message 两处，
    只认后者，否则每一轮都会被计两次。
    """
    models, prompts, texts = set(), [], []
    for line in path.open(encoding="utf-8", errors="ignore"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        ts = iso(d.get("time") or d.get("created_at"))
        if ts:
            if not rec["start"] or ts < rec["start"]:
                rec["start"] = ts
            if ts > rec["end"]:
                rec["end"] = ts
        if t == "metadata":
            ts = iso(d.get("created_at"))
            if ts and (not rec["start"] or ts < rec["start"]):
                rec["start"] = ts
        elif t == "profile.bind" and d.get("modelAlias"):
            models.add(d["modelAlias"])
        elif t == "usage.record":
            u = d.get("usage") or {}
            rec["tok_in"] += int(u.get("inputOther") or 0)
            rec["tok_out"] += int(u.get("output") or 0)
            rec["tok_cache_r"] += int(u.get("inputCacheRead") or 0)
            rec["tok_cache_w"] += int(u.get("inputCacheCreation") or 0)
        elif t == "context.append_message":
            m = d.get("message") or {}
            body, tool_blocks = text_of(m.get("content"))
            rec["tools"] += tool_blocks
            if m.get("role") == "user":
                rec["msgs"] += 1
                if body and not is_injected(body):
                    rec["turns"] += 1
                    texts.append(body)
                    if len(prompts) < MAX_PROMPTS:
                        prompts.append(redact(strip_injected(body))[:PROMPT_CHARS])
            elif m.get("role") == "assistant":
                rec["msgs"] += 1
        elif t == "context.append_loop_event":
            ev = (d.get("event") or {}).get("type") or ""
            if "tool" in ev:
                rec["tools"] += 1
    if not rec["project"]:
        # 目录名形如 wd_githubproject_75a0129b38fb —— 中间那段才是工作区
        for part in path.parts:
            if part.startswith("wd_"):
                rec["project"] = part[3:].rsplit("_", 1)[0]
                break
    rec["models"] = sorted(models)
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["errors"] = joined.lower().count("error") + joined.count("报错")
    rec["kw"] = count_keywords(joined)
    rec["title"] = (prompts[0][:80] if prompts else "kimi 会话")
    return rec


def parse_chatgpt(path: Path, rec: dict) -> dict:
    """仓内 ChatGPT 导出：{created_at, messages:[{created_at, role, text}]}。"""
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return rec
    prompts, texts = [], []
    for m in d.get("messages") or []:
        if not isinstance(m, dict):
            continue
        ts = iso(m.get("created_at"))
        if ts:
            if not rec["start"] or ts < rec["start"]:
                rec["start"] = ts
            if ts > rec["end"]:
                rec["end"] = ts
        rec["msgs"] += 1
        body = m.get("text") or ""
        if m.get("role") == "user" and body and not is_injected(body):
            rec["turns"] += 1
            texts.append(body)
            if len(prompts) < MAX_PROMPTS:
                prompts.append(redact(strip_injected(body))[:PROMPT_CHARS])
    if not rec["start"]:
        rec["start"] = iso(d.get("created_at"))
    rec["project"] = "ChatGPT"
    rec["prompts"] = prompts
    joined = "\n".join(texts)
    rec["errors"] = joined.lower().count("error") + joined.count("报错")
    rec["kw"] = count_keywords(joined)
    rec["title"] = redact(str(d.get("title") or ""))[:120] or (prompts[0][:80] if prompts else "ChatGPT 对话")
    return rec


PARSERS = {"cc": parse_cc, "chatgpt": parse_chatgpt, "dsh": parse_dsh, "kimi": parse_kimi, "codex": parse_codex, "generic": parse_generic, "cdmeta": parse_cdmeta}


BATCH_MIN = 5
BATCH_PREFIX = 80


def mark_batches(records: list) -> int:
    """把「同一段提示词被重复投喂很多次」的会话标成批处理。

    实测：455 个 codex 会话里 340 个的第一句一模一样（一个生成讲义的批处理）。
    按会话数算活跃度的话，四分之三的活跃度是同一个脚本刷出来的。
    这类必须单独标出来 —— 被丢掉的部分不参与总量校验，总量就永远对。
    """
    groups = {}
    for r in records:
        if r["turns"] > 2 or not r["prompts"]:
            continue
        groups.setdefault(r["prompts"][0][:BATCH_PREFIX].strip(), []).append(r)
    marked = 0
    for prefix, rs in groups.items():
        if len(rs) < BATCH_MIN:
            continue
        for r in rs:
            r["kind"] = "auto"
            r["batch"] = prefix[:40]
            marked += 1
    return marked


def extract_source(name: str, cfg: dict, outdir: Path, full: bool) -> dict:
    root: Path = cfg["root"]
    out = outdir / f"{name}.sessions.jsonl"
    stats = {"source": name, "root": redact(str(root)), "exists": root.is_dir(),
             "files": 0, "parsed": 0, "cached": 0, "failed": 0, "bytes": 0}
    if not root.is_dir():
        if out.is_file() and out.stat().st_size > 0:
            stats["degraded"] = f"来源目录不存在：{redact(str(root))}；已保留旧产物，未覆盖"
        return stats

    cache = {}
    if out.is_file() and not full:
        for line in out.open(encoding="utf-8", errors="ignore"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("_k"):
                cache[r["_k"]] = r

    if cfg["parser"] == "dsh":
        try:
            _dsh_prepare(root)
        except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
            # 解不了就整源标不确定，**不产出空壳会话** ——
            # 1937 个 0 轮 0 消息的记录会把总量灌水，那比没有更糟。
            stats["degraded"] = f"DSH 解压失败（{exc}）；本轮不产出该来源"
            return stats

    records = []
    prior = len(cache)
    scanned = set()
    for path in sorted(root.glob(cfg["glob"])):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        if st.st_size == 0:
            continue
        scanned.add(str(path.relative_to(root)) if _under(path, root) else str(path))
        stats["files"] += 1
        stats["bytes"] += st.st_size
        # 身份用**相对来源根**的路径，不用绝对路径：仓根一变（比如从主树换到
        # ~/.memory-atlas/src），所有绝对路径都会失效 —— 旧记录被当成「源已删」
        # 留下来，同一批文件又重新解析一遍，同一份数据就被算了两次。
        # 实测：chatgpt 379 个文件，新解析 379 + 源已删留存 379 = 虚涨一倍。
        rel = str(path.relative_to(root)) if _under(path, root) else str(path)
        # 缓存键还要带解析器指纹：只按 (路径, mtime, 大小) 判重的话，
        # 改了解析逻辑却复用旧记录，产出会静默陈旧且没有任何东西会变红。
        key = f"{rel}|{st.st_mtime_ns}|{st.st_size}|{PARSER_FINGERPRINT}"
        hit = cache.get(key)
        if hit is not None:
            records.append(hit)
            stats["cached"] += 1
            continue
        # record_id 必须对「文件」唯一而不是文件名：kimi-code 的会话文件全叫
        # wire.jsonl，只是分散在不同目录，只用文件名会把 419 个会话压成 1 个。
        # record_id 也用相对路径：绝对路径一变，同一场会话就会换个 id 冒出来。
        sid = f"{name}-{hashlib.sha256(rel.encode()).hexdigest()[:12]}"
        rec = blank(sid, name, path)
        rec["bytes"] = st.st_size
        try:
            rec = PARSERS[cfg["parser"]](path, rec)
        except Exception as exc:
            stats["failed"] += 1
            rec["title"] = f"<解析失败: {type(exc).__name__}>"
        if not rec["start"]:
            rec["start"] = iso(st.st_mtime)
        if not rec["end"]:
            rec["end"] = rec["start"]
        rec["kind"] = session_kind(rec)
        # DSH 的 origin=subagent 是 agent 自己派生的子会话 —— 1937 场里 1929 场是这个。
        # 不标出来，「你亲自开口」会一夜之间多出近两千场。
        if rec.get("dsh_origin") == "subagent":
            rec["kind"] = "auto"
            rec["batch"] = f"DSH 子代理（{rec.get('dsh_preset') or 'agent'}）"
        rec["_k"] = key
        records.append(rec)
        stats["parsed"] += 1

    # 源文件被清掉之后，那段历史不能跟着消失 —— 这是个「记忆」图谱，
    # 缓存文件本身就是长期归档。本机确实在按天清理会话缓存（磁盘从 19G 压到 8.3G），
    # 所以这不是假想风险。留下来的记录标 gone，页面上照常算，只是不再更新。
    kept = 0
    for key, rec in cache.items():
        rel_path = key.split("|", 1)[0]
        # 相对路径比对：这一轮扫到了就跳过；文件还在也跳过。
        if rel_path in scanned or (root / rel_path).exists():
            continue
        rec["gone"] = True
        records.append(rec)
        kept += 1
    stats["kept_gone"] = kept
    if kept:
        records.sort(key=lambda r: r.get("start") or "")

    # 防倒退门：上一轮有记录、这一轮一个文件都没扫到 —— 那几乎一定是路径解析
    # 或挂载出了问题，不是数据真的没了。此时**不覆盖**旧产物，并让整轮失败。
    # 实测踩过：仓根解析错，chatgpt 归档从 379 个文件掉到 0，产物被清空，
    # 2025-11 到 2026-05 的历史静默消失，而流程照样报成功。
    if not records and prior and not stats.get("kept_gone"):
        stats["degraded"] = f"上一轮有 {prior} 条，这一轮扫到 0 个文件；已保留旧产物，未覆盖"
        return stats

    # 批处理判定要看整个来源，所以放在写盘前、缓存复用之后 ——
    # 复用回来的记录也要重新参与分组，否则增量跑会漏标。
    stats["batched"] = mark_batches(records)

    outdir.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(out)
    stats["sessions"] = len(records)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default="all")
    ap.add_argument("--full", action="store_true", help="忽略缓存，全部重解析")
    ap.add_argument("--repo", default=".", help="仓根，供 repo_relative 来源解析路径")
    args = ap.parse_args()

    outdir = Path(args.out)
    names = list(SOURCES) if args.source == "all" else [args.source]
    t0 = time.time()
    all_stats = []
    repo = Path(args.repo).resolve()
    for n in names:
        if n not in SOURCES:
            print(f"未知来源: {n}", file=sys.stderr)
            return 1
        cfg = dict(SOURCES[n])
        if cfg.get("repo_relative"):
            cfg["root"] = repo / cfg["root"]
        s = extract_source(n, cfg, outdir, args.full)
        all_stats.append(s)
        if s.get("degraded"):
            print(f"  {n:16s} ✗ 倒退：{s['degraded']}", file=sys.stderr)
            continue
        print(f"  {n:16s} 文件 {s['files']:5d}  新解析 {s['parsed']:5d}  复用 {s['cached']:5d}  "
              f"失败 {s['failed']:3d}  批处理 {s.get('batched', 0):4d}  "
              f"源已删留存 {s.get('kept_gone', 0):4d}  {s['bytes']/1048576:8.1f}MB")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "elapsed_sec": round(time.time() - t0, 1),
        "sources": all_stats,
        "skipped": SKIPPED,
    }
    (outdir / "extract_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for s in all_stats if s["exists"])
    bad = [s for s in all_stats if s.get("degraded")]
    print(f"\n用时 {meta['elapsed_sec']}s，可读来源 {ok}/{len(all_stats)}")
    if bad:
        print(f"✗ {len(bad)} 个来源倒退，旧产物已保留未被覆盖。"
              f"先修路径再跑，不要拿残缺数据发布。", file=sys.stderr)
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
