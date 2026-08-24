#!/usr/bin/env python3
"""
T3 workflow 通道包装：persona-distiller 盲判/答题/研究生成走 DeepSeek API。

- 凭据从 ~/.kimi-code/config.toml 读（providers.deepseek），不在仓里留任何 key。
- 模型：--model flash(=deepseek-v4-flash，主力) / pro(=deepseek-v4-pro，仅关键决策)。
- 用法：
    python3 wf.py call  --model flash --prompt '...' [--temp 0.7] [--max-tokens 800]
    python3 wf.py batch --model flash --in in.jsonl --out out.jsonl [--temp 0.7] [--max-tokens 800]
        in.jsonl 每行 {"id": "...", "prompt": "..."}；out.jsonl 每行 {"id","content","usage",...}
    python3 wf.py usage-reset
    python3 wf.py usage     # 打印累计 token / 估算成本
- 双侧盲判纪律：candidate 与 baseline 必须同一 --model（默认都 flash）。
- 成本纪律：批量/答题/判分一律 flash；pro 仅关键决策（门线±0.03/两席分歧>0.1/首轮未过/发布门红）。
- 每条调用写 usage 日志（默认 ~/.kimi-code/wf-usage.jsonl），用于 flash/pro 分账。
"""
import sys, os, json, time, re, argparse, datetime, urllib.request, urllib.error

DEFAULT_LOG = os.path.expanduser("~/.kimi-code/wf-usage.jsonl")

MODELS = {
    "flash": "deepseek-v4-flash",
    "pro": "deepseek-v4-pro",
}
# 价格（元/百万 tokens，谷时，2026-08-16 官方价；只用于估算）
PRICES = {
    "deepseek-v4-flash": {"hit_in": 0.05, "miss_in": 1.5, "out": 4.5},
    "deepseek-v4-pro":   {"hit_in": 0.15, "miss_in": 4.5, "out": 13.5},
}


def load_credentials():
    """从 ~/.kimi-code/config.toml 读 providers.deepseek 的 base_url 与 api_key。"""
    cfg = os.path.expanduser("~/.kimi-code/config.toml")
    txt = open(cfg, encoding="utf-8").read()
    # ★ 2026-08-24 实测：config.toml 的 provider 段是 `[providers.Deepseek]`（大写），
    #   wf.py 原正则只认小写 `deepseek` 且强要 type 行 → 直接找不到 key。
    #   改成大小写不敏感 + type 段可选（实测两处都含 type，但不必依赖）。
    m = re.search(
        r'\[providers\.deepseek\]\s*base_url\s*=\s*"([^"]+)"\s*(?:type\s*=\s*"[^"]+"\s*)?api_key\s*=\s*"([^"]+)"',
        txt, re.IGNORECASE)
    if not m:
        raise SystemExit("wf.py: 无法在 ~/.kimi-code/config.toml 中找到 providers.deepseek")
    return m.group(1).rstrip("/"), m.group(2)


def call_api(base, key, model, prompt, temp, max_tokens, timeout=300):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    last_err = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.load(r)
            return d["choices"][0]["message"]["content"], d.get("usage", {})
        except urllib.error.HTTPError as e:
            last_err = "HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "ignore"))
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 60))
                continue
            raise SystemExit("wf.py: %s" % last_err)
        except Exception as e:
            last_err = repr(e)
            time.sleep(min(2 ** attempt, 60))
    raise SystemExit("wf.py: 重试耗尽: %s" % last_err)


def log_usage(model, usage, mode="call"):
    """写 usage 日志（append），供成本分账。"""
    try:
        os.makedirs(os.path.dirname(DEFAULT_LOG), exist_ok=True)
        with open(DEFAULT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "model": model,
                "mode": mode,
                "usage": usage,
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser(description="DeepSeek flash/pro 通道包装")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("call", "batch"):
        p = sub.add_parser(name)
        p.add_argument("--model", choices=sorted(MODELS), default="flash")
        p.add_argument("--temp", type=float, default=0.7)
        # ★ 2026-08-21 教训（Paracelsus #526）：flash 的 reasoning_content 独占 token 预算，
        #   max_tokens=500/100 时 content 返回空字符串。答案 ≥2000、判分 ≥500 才稳。
        p.add_argument("--max-tokens", type=int, default=2000)
        if name == "call":
            p.add_argument("--prompt", required=True)
        else:
            p.add_argument("--in", dest="inp", required=True)
            p.add_argument("--out", dest="out", required=True)

    sub.add_parser("usage-reset")
    u = sub.add_parser("usage")
    u.add_argument("--detail", action="store_true")
    args = ap.parse_args()

    if args.cmd == "usage":
        total = {}
        n = 0
        if os.path.exists(DEFAULT_LOG):
            for line in open(DEFAULT_LOG, encoding="utf-8"):
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                m = rec.get("model", "?")
                u = rec.get("usage", {})
                t = total.setdefault(m, {"calls": 0, "in": 0, "out": 0, "hit": 0, "cost": 0.0})
                t["calls"] += 1
                pt = u.get("prompt_tokens", 0)
                ct = u.get("completion_tokens", 0)
                hit = u.get("prompt_cache_hit_tokens", 0)
                t["in"] += pt
                t["out"] += ct
                t["hit"] += hit
                price = PRICES.get(m, {})
                cost = (pt - hit) * price.get("miss_in", 0) / 1e6 + hit * price.get("hit_in", 0) / 1e6 + ct * price.get("out", 0) / 1e6
                t["cost"] += cost
                n += 1
        for m, t in total.items():
            print("%-20s calls=%-5d in=%-10d out=%-8d cache_hit=%-10d 估成本≈¥%.4f" %
                  (m, t["calls"], t["in"], t["out"], t["hit"], t["cost"]))
        if not total:
            print("usage 日志为空:", DEFAULT_LOG)
        return

    if args.cmd == "usage-reset":
        if os.path.exists(DEFAULT_LOG):
            os.remove(DEFAULT_LOG)
            print("已重置 usage 日志")
        return

    base, key = load_credentials()
    model = MODELS[args.model]

    if args.cmd == "call":
        content, usage = call_api(base, key, model, args.prompt, args.temp, args.max_tokens)
        log_usage(model, usage)
        sys.stdout.write(content)
        return

    # batch
    items = []
    for line in open(args.inp, encoding="utf-8"):
        line = line.strip()
        if line:
            items.append(json.loads(line))
    out_lines = []
    for i, it in enumerate(items, 1):
        content, usage = call_api(base, key, model, it["prompt"], args.temp, args.max_tokens)
        log_usage(model, usage, mode="batch")
        rec = {"id": it.get("id"), "content": content, "usage": usage}
        out_lines.append(rec)
        # 进度到 stderr，避免污染 stdout 的 JSONL
        sys.stderr.write("[wf] %d/%d %s\n" % (i, len(items), it.get("id", "")))
        sys.stderr.flush()
    with open(args.out, "w", encoding="utf-8") as f:
        for rec in out_lines:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
