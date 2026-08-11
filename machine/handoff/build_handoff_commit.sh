#!/usr/bin/env bash
# 造一个「不含语料、只含交付物与全部记录」的移交提交，并**当场验它过不过 200 MB 闸**。
#
# ## 为什么需要它（2026-08-11 实测）
#
#     origin/main..HEAD：1128 个提交、新 blob **2106.2 MB**，而 pre-push 闸是 200 MB。
#     ★ **删文件不缩小推送量**——blob 已经在这 1128 个提交的历史里；
#     ★ `git filter-repo` 在 `blob:none` 部分克隆上不可用。
#
# 唯一走得通的是：**以 origin/main 为父做一个提交**，树 = 当前 HEAD 树减去语料。
# 这样推送只送增量，不送历史。实测 **31.2 MB**。
#
#     孤儿分支不行：没有共同祖先，git 会把整棵树 743.7 MB 全送。
#
# ## 保留什么、丢什么（按扩展名，不按目录——实测目录切不干净）
#
# `_corpora/` 里的语料散在 `raw/`、`references/sources/`、`references/holdout/`、
# `_fetch-staging/` 四处以上，**按目录切会漏 92.9 MB**。改按扩展名：
#
#     保留：.md .json .jsonl .py .yaml .yml .sh .ps1 .tsv   → 23.7 MB / 3440 个
#     丢弃：.txt .pdf .html .gz .xml .img                    → 2731.8 MB / 7266 个
#
# 保留集里最大的是 `wip-galen-101/raw/f1k_tree.json`（1.44 MB）与几份
# `source-ledger.jsonl`——**已逐个看过，没有大块语料混进来**。
#
# ## 语料去哪
#
# 用户已定：**语料另存 Release／私有仓，仓里只放指针**。
# 指针清单在 `_ledgers/_语料指针清单.json`（34 工作区 / 2071 行 / 853.9 MB，
# 74.3% 有 URL、4.9% 有档案条目号、18.7% 只有文字性坐标、2.1% 无坐标）。
#
# ## 用法
#
#     bash machine/handoff/build_handoff_commit.sh              # 只造+验，不建分支
#     bash machine/handoff/build_handoff_commit.sh --branch X   # 顺便把分支 X 指过去
#
# **本脚本不推送。** 推送是对外动作，由人按下。
set -uo pipefail

cd "$(git rev-parse --show-toplevel)"
BRANCH=""
[[ "${1:-}" == "--branch" ]] && BRANCH="${2:-}"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
export GIT_INDEX_FILE="$TMP/index"

BASE=$(git rev-parse origin/main) || { echo "✗ 取不到 origin/main" >&2; exit 2; }
git read-tree HEAD
BEFORE=$(git ls-files --cached | wc -l | tr -d ' ')

git ls-files --cached -z > "$TMP/all.z"
python3 - "$TMP/all.z" "$TMP/drop.z" <<'PY'
import sys, os
KEEP = {".md", ".json", ".jsonl", ".py", ".yaml", ".yml", ".sh", ".ps1", ".tsv"}
data = [p for p in open(sys.argv[1], "rb").read().split(b"\0") if p]
drop = []
for p in data:
    s = p.decode("utf-8", "surrogateescape")
    if "/_corpora/" not in s:
        continue
    if os.path.splitext(s)[1].lower() in KEEP:
        continue
    drop.append(p)
open(sys.argv[2], "wb").write(b"\0".join(drop) + (b"\0" if drop else b""))
print("  剔除语料文件：%d 个" % len(drop))
PY

git update-index --force-remove -z --stdin < "$TMP/drop.z"
AFTER=$(git ls-files --cached | wc -l | tr -d ' ')
echo "  index 条目：$BEFORE → $AFTER"

TREE=$(git write-tree)
NEW=$(git commit-tree "$TREE" -p "$BASE" \
      -m "handoff: 交付物・流水线・全部台账与判分记录（语料另存，仓里放指针）")
unset GIT_INDEX_FILE

echo "  基线 origin/main = ${BASE:0:12}"
echo "  移交提交         = $NEW"

# --- 自验一：推送量 ---
MB=$(git rev-list --objects "$BASE..$NEW" | awk '{print $1}' \
     | git cat-file --batch-check='%(objecttype) %(objectsize)' \
     | awk '/^blob/{s+=$2} END{printf "%d", (s+0)/1048576}')
echo "  ★ 新 blob：${MB} MB（闸 ${LINZE_BULK_LIMIT_MB:-200} MB）"

# --- 自验二：**真的把钩子跑一遍**，不是自己算一遍就宣布过了 ---
HOOK=".githooks/pre-push"
if [[ -x "$HOOK" ]]; then
  if printf 'refs/heads/handoff %s refs/heads/main %s\n' "$NEW" "$BASE" \
     | "$HOOK" origin https://example.invalid/x.git >/dev/null 2>&1; then
    echo "  ✓ pre-push 钩子：放行"
  else
    echo "  ✗ pre-push 钩子：**拒绝** —— 不要推，先看上面的量" >&2
    exit 1
  fi
else
  echo "  ★ **$HOOK 不存在，本次没验钩子**（不是通过）。" >&2
  echo "    装法：cp .githooks/pre-push.worktree .githooks/pre-push && chmod +x .githooks/pre-push" >&2
fi

# --- 自验三：交付物与记录**没被误删** ---
fail=0
for P in "CodexSkills/registry/codex/persona-distiller-group/team-index.json" \
         "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_延后名单.json" \
         "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_语料指针清单.json"; do
  if git cat-file -e "$NEW:$P" 2>/dev/null; then echo "  ✓ $P"; else echo "  ✗ **缺** $P" >&2; fail=1; fi
done
# ★★★ 与 HEAD **精确比对**，不用绝对阈值。
#   第一版写的是 `N_EVAL -lt 100`，而变异实测（只保留 .json）把 evals 从 433 砍到 248——
#   **248 > 100，那道门一次也没红**。绝对阈值就是这样一道永远不会红的红
#   （[[a-red-that-can-never-turn-green-is-not-a-signal]] 的镜像）。
#   真值是「除语料外一份都不许少」，所以拿 HEAD 当基准逐类数。
count_records () {   # $1 = commit
  git ls-tree -r --name-only "$1" \
    | grep -E '/_corpora/.*\.(md|json|jsonl|py|yaml|yml|sh|ps1|tsv)$' | wc -l | tr -d ' '
}
count_outside () {   # 语料目录之外的文件，一份都不该动
  git ls-tree -r --name-only "$1" | grep -vc '/_corpora/'
}
H_REC=$(count_records HEAD);  N_REC=$(count_records "$NEW")
H_OUT=$(count_outside HEAD);  N_OUT=$(count_outside "$NEW")
N_EVAL=$(git ls-tree -r --name-only "$NEW" | grep -c '/evals/')
N_LEDG=$(git ls-tree -r --name-only "$NEW" | grep -c '_ledgers/')
echo "  _corpora 内记录类：HEAD ${H_REC} → 移交 ${N_REC}｜语料目录外：HEAD ${H_OUT} → 移交 ${N_OUT}"
echo "  （其中 evals ${N_EVAL} 份、台账 ${N_LEDG} 份）"
if [[ "$N_REC" -ne "$H_REC" ]]; then
  echo "  ✗ **_corpora 内的记录类少了 $((H_REC - N_REC)) 份**——只该丢语料，不该丢记录。不要推" >&2
  fail=1
fi
if [[ "$N_OUT" -ne "$H_OUT" ]]; then
  echo "  ✗ **语料目录之外少了 $((H_OUT - N_OUT)) 份**——切法越界了。不要推" >&2
  fail=1
fi
[[ "$fail" -ne 0 ]] && exit 1

if [[ -n "$BRANCH" ]]; then
  git branch -f "$BRANCH" "$NEW"
  echo "  分支 $BRANCH → ${NEW:0:12}"
fi
echo "  ★ **本脚本不推送。** 推送是对外动作，由人按下。"
