#!/usr/bin/env bash
# 造移交 bundle + 校验 sidecar —— **可重跑**，每次都自洽。
#
# ★★ 为什么要有这个脚本：sidecar 我手写过一次，把 tip 写成了**当时的 HEAD**，
#    而包是更早打的——中间又提交了两次，于是 sidecar 说 d2d1008c、包里其实是 2122dc78。
#    **tip 必须从包里读，不能从工作树读。** 这是操作单开头警告过的那个循环的第二种形态。
#
# ★ 资产名固定为 agentdb-persona-distiller-full.bundle：
#   公开仓 origin/main 的 HANDOFF.md 里 `gh release download --pattern` 写的就是这个名字，
#   且那份指针**没有写死 sha256**。⇒ 原名替换资产，公开仓一个字都不用改。
#
# 用法：bash make_handover_bundle.sh [输出目录]
#   默认输出到 _protected/agentdb-handover-<今天>/ —— **必须是 _protected/**，
#   `_scratch/`、构建树、~/Downloads 三处都会被回收（上一版包就是这么没的）。
set -uo pipefail

REPO="$(git rev-parse --show-toplevel)" || { echo "★ 不在 git 仓里"; exit 1; }
OUT="${1:-$HOME/Documents/Codex/GithubProject/_protected/agentdb-handover-$(date +%Y%m%d)}"
NAME="agentdb-persona-distiller-full.bundle"
mkdir -p "$OUT"
B="$OUT/$NAME"

echo "== 1/4 打包（--all）=="
git -C "$REPO" bundle create "$B" --all
rc=$?; [ $rc -ne 0 ] && { echo "★ 打包失败 rc=$rc"; exit $rc; }

echo "== 2/4 verify（必须在 git 仓里跑；空目录会报 need a repository）=="
git -C "$REPO" bundle verify "$B" | tail -2
rc=$?; [ $rc -ne 0 ] && { echo "★ verify 失败 rc=$rc"; exit $rc; }

echo "== 3/4 sidecar（tip 从包里读，不从工作树读）=="
TIP="$(git -C "$REPO" bundle list-heads "$B" \
       | awk '/refs\/heads\/claude\/character-distillation/{print $1}')"
[ -z "$TIP" ] && { echo "★ 包里没有那条分支"; exit 1; }
SHA="$(shasum -a 256 "$B" | awk '{print $1}')"
SZ="$(wc -c < "$B" | tr -d ' ')"
N="$(git -C "$REPO" rev-list --count "$TIP")"
cat > "$B.sha256" <<EOF
文件   $NAME
大小   $SZ 字节
sha256 $SHA
tip    $TIP        ← 从包里读出来的，不是工作树的 HEAD
提交数 $N
打包   $(date +%Y-%m-%d\ %H:%M)
EOF
cat "$B.sha256"

echo "== 4/4 回读自验证：真 clone 一次，验交付物在不在 =="
TMP="$(mktemp -d)"
git clone -q "$B" "$TMP/r" && git -C "$TMP/r" checkout -q \
  claude/character-distillation-skill-reorganize-d57595
python3 - "$TMP/r" <<'PYEOF'
import sys,pathlib,json
R=pathlib.Path(sys.argv[1]); C=R/"CodexSkills/skill_log_evals/persona-distiller/_corpora"
ok=True
NEW=["wip-marshall-173","wip-lincoln-174","wip-jefferson-175","wip-bismarck-176","wip-machiavelli-177",
     "wip-rousseau-178","wip-kant-179","wip-pestalozzi-180","wip-frobel-181","wip-comenius-182"]
miss=0
for ws in NEW:
    d=C/ws/"workspaces"
    if not d.exists(): print("❌ %s 不在包里"%ws); ok=False; continue
    slug=[p.name for p in d.iterdir() if p.is_dir()][0]
    rows=[json.loads(l) for l in (d/slug/"evidence"/"source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    man=json.loads((d/slug/"raw"/"_fetch-manifest.json").read_text(encoding="utf-8"))
    shas={e.get("sha256") for e in man.get("記錄",man.get("记录",[])) if isinstance(e,dict)}
    m=sum(1 for r in rows if r.get("checksum") not in shas); miss+=m
    if m: print("❌ %s 有 %d 条台账在 manifest 里查不到 sha256"%(ws,m)); ok=False
print(("✅" if not miss else "❌")+" 语料指针：台账 sha256 查不到的 = %d"%miss)
h=(R/"HANDOFF.md").read_text(encoding="utf-8")
for k in ["16 类，不是 7 类","evals/cases.jsonl"]:
    print(("✅" if k in h else "❌")+" HANDOFF 含「%s」"%k); ok&= k in h
print("\n"+("回读自验证通过" if ok else "★ 回读自验证有不通过项"))
sys.exit(0 if ok else 1)
PYEOF
rc=$?
rm -rf "$TMP"
[ $rc -ne 0 ] && { echo "★ 回读自验证失败"; exit $rc; }
echo
echo "包在：$B"
echo "上传（**由人按**，一条命令，公开仓不用改）："
echo "  gh release upload agentdb-handover-20260812 \"$B\" --repo LinzeColin/Private-Database --clobber"
