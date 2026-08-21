#!/usr/bin/env bash
# daily.sh —— 每日增量：抽取 → 聚合 → 部署。无人值守，零 agent，零 token。
#
# 为什么这一段必须跑在本机：源数据（~/.claude、~/.codex、~/.kimi-code …）
# 只存在于这台机器上，VPS 上没有。合同里「定时任务放 VPS」的用意是别让服务端
# 依赖笔记本；这里服务端不依赖 —— 笔记本关着，站点照常提供昨天的数据，
# 页面顶部会自己标出「数据截至」，超过 48 小时会显示「断了」。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"        # atlas/ ，代码所在，只读
REPO="${ATLAS_REPO_ROOT:-$(cd "$ROOT/.." && pwd)}"   # 仓根，chatgpt 归档在这下面（只读）
WORK="${ATLAS_WORK:-$HOME/.memory-atlas}"       # 产物所在，绝不写进仓
LOG="$WORK/daily.log"
LOCK="$WORK/.lock"

mkdir -p "$WORK/out" "$WORK/web"

# 上一轮没跑完就退出。不等待、不重试 —— 等待循环是这台机器上出过事的东西
# （同时挂过 7 个死等，最长 1 天 5 小时）。超过 3 小时的锁视为残留，直接清掉。
if [ -d "$LOCK" ]; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +180 2>/dev/null)" ]; then
    rmdir "$LOCK" 2>/dev/null || true
  else
    echo "$(date -u +%FT%TZ) 上一轮还在跑，本轮跳过" >>"$LOG"; exit 0
  fi
fi
mkdir "$LOCK" 2>/dev/null || { echo "$(date -u +%FT%TZ) 抢锁失败，跳过" >>"$LOG"; exit 0; }
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

{
  echo "───── $(date -u +%FT%TZ) ─────"
  python3 "$ROOT/build/extract.py" --out "$WORK/out" --repo "$REPO"
  # GitHub 活动：证明「做出来了」的那一半。拉不到不阻断本轮 —— 页面会把它标成「不确定」。
  python3 "$ROOT/build/github.py" --out "$WORK/out/github.json" || echo "GitHub 拉取失败，本轮该块标不确定"
  # 成果复利事件：先把私有仓里的语义事件拉进本机收件箱，再构建。
  # 拉不到不阻断本轮 —— 页面会如实显示「尚无事件」，不是假 0。
  bash "$ROOT/build/sync_compound.sh" pull || echo "复利事件拉取失败，本轮按无事件构建"
  python3 "$ROOT/build/build.py"   --sessions "$WORK/out" --out "$WORK/web" \
    --github "$WORK/out/github.json"
  # 给 agent 看的开发经验沉淀。落私有目录，**绝不进公开仓**（里面有 Owner 原话）。
  python3 "$ROOT/build/sediment.py" --sessions "$WORK/out" --out "$WORK/brief" --web "$WORK/web" \
    --atlas "$WORK/web/atlas/atlas.json"
  # 把《收尾必须回写》契约分发到每个 agent 的指令文件。内容没变就不动文件。
  # 靠人去五个文件里同步是同步不住的 —— 这一步就是为了不再靠人。
  # 提问那一刻要用的字面索引。**必须在 build.py 之后**（它读 atlas.json），
  # 也必须在部署之前 —— 索引落在本机 $WORK，不进站点、不进仓。
  python3 "$ROOT/build/brief_index.py" --atlas "$WORK/web/atlas/atlas.json" \
    --repo "$REPO" --out "$WORK/brief_index.jsonl" \
    || echo "字面索引生成失败，本轮 UserPromptSubmit 钩子会静默不注入"

  # 全量语料 → 私有仓。**这一步是 Owner 明确要过的**：
  # 「把 cc 和 codex 还有所有本地所有 agent 对话信息全部都上传到 private repo」。
  # 上传的是你的原话（不截断）+ 工具指针，不含助手输出（可再生、且是它撑到 5GB 的）。
  python3 "$ROOT/build/corpus.py" --sessions "$WORK/out" --out "$WORK/corpus" --repo "$REPO" \
    && bash "$ROOT/build/push_corpus.sh" "$WORK/corpus" \
    || echo "语料本轮未上传（自检没过或推送失败）—— 站点与 brief 不受影响"

  bash "$ROOT/build/install_agents_md.sh" || echo "契约分发失败，本轮 agent 指令未更新"
  # 权威副本推私有仓，让任何有仓权限的 agent 都能直接取。
  # 失败不阻断本轮 —— 站点和本机那两份还在。
  bash "$ROOT/build/push_brief.sh" "$WORK/brief" || echo "AGENT_BRIEF 推送失败，本轮只留站点与本机副本"
  # 复利投影回推私有仓，供 ChatGPT 定时任务与其他 agent 读取当前漏斗状态。
  python3 -c "
import json,sys,pathlib
a=json.loads(pathlib.Path('$WORK/web/atlas/atlas.json').read_text())
pathlib.Path('$WORK/compounding').mkdir(parents=True,exist_ok=True)
pathlib.Path('$WORK/compounding/latest.json').write_text(
    json.dumps(a.get('compounding') or {}, ensure_ascii=False, indent=2))
" && bash "$ROOT/build/sync_compound.sh" push "$WORK/compounding/latest.json" \
    || echo "复利投影推送失败，本轮只留本机副本"

  # 页面本体来自仓里的 web/，数据来自 $WORK/web/atlas/ —— 发布时合到一起
  rsync -a --delete --exclude atlas/ "$ROOT/web/" "$WORK/web/"
  bash "$ROOT/build/deploy.sh" "$WORK/web"
  echo "完成 $(date -u +%FT%TZ)"
} >>"$LOG" 2>&1

# 日志只留最近 2000 行，别让它无限长
tail -n 2000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
