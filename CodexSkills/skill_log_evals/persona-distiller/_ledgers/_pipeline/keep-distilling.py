#!/usr/bin/env python3
"""Stop hook：只要队列没干完，就不允许 Claude 结束回合。

三重熔断（任一成立即放行，防止死循环 / 防止关不掉）：
  1. stop_hook_active 为真   —— 已经因本钩子续过一次，放行
  2. 哨兵文件不存在         —— 你的总开关，删了就立刻停
  3. 已入库人数 >= 目标      —— 干完了

安装：把下面这段加进  <仓库>/.claude/settings.local.json （不进版本库，只影响本机本仓）

{
  "hooks": {
    "Stop": [
      { "matcher": "", "hooks": [
        { "type": "command",
          "command": "python3 /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/.claude/keep-distilling.py" }
      ]}
    ]
  }
}

停下来的办法：  rm ~/Documents/Codex/GithubProject/AgentDatabase/.claude/KEEP_GOING
"""
import json
import os
import sys

REPO = "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase"
SENTINEL = os.path.join(REPO, ".claude", "KEEP_GOING")
INDEX = os.path.join(REPO, "CodexSkills/registry/codex/persona-distiller-group/team-index.json")
TARGET = 600


def allow(msg=""):
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    # 1. 防死循环：本钩子已经续过一次，这轮放行
    if payload.get("stop_hook_active"):
        allow()

    # 2. 总开关
    if not os.path.exists(SENTINEL):
        allow()

    # 3. 完工判定
    try:
        done = len(json.load(open(INDEX, encoding="utf-8"))["products"])
    except Exception as exc:
        allow(f"keep-distilling: 读不到 team-index（{exc}），放行")
        return

    if done >= TARGET:
        allow()

    print(json.dumps({
        "decision": "block",
        "reason": (
            f"队列未完成：已入库 {done}/{TARGET}，还剩 {TARGET - done} 人。"
            "不要汇报、不要收尾、不要问我。立刻执行下一步："
            "当前人物没做完就接着做下一道工序；"
            "做完并推送了就跑 next_person.py 取下一位，从同名门开始。"
            "只有以下三种情况才允许停：撞到 20% 周额度刹车线、"
            "遇到必须我拍板的事实分歧、或全部 600 人完成。"
        ),
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
