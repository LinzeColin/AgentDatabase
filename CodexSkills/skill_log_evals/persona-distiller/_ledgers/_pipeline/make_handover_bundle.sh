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
# ★★ 2026-08-13：清单**从包里现扫**，不再写死。
#   原先写死的是第 1 批那 10 个；当天新增了 wip-burbank-183／wip-leonardo-184／
#   wip-michelangelo-185 三个工作区，**一个都没被验到，而自验证照样打印「通过」**。
#   写死的名单只保证「我列出来的那些是好的」，不保证「包里的都是好的」——
#   而移交方拿到的是包里的全部。[[a-checker-nothing-calls-is-not-a-checker]]
NEW=sorted(p.name for p in C.glob("wip-*")
           if (p/"workspaces").is_dir() and any((p/"workspaces").iterdir()))
print("扫到 %d 个 wip 工作区（**从包里现扫，不是写死的名单**）：%s\n"
      % (len(NEW), "、".join(NEW)))
if len(NEW) < 10:
    print("❌ 只扫到 %d 个，少于第 1 批的 10 个 —— 包可能不全"%len(NEW)); ok=False
miss=0; nolg=0
for ws in NEW:
    d=C/ws/"workspaces"
    slug=[p.name for p in d.iterdir() if p.is_dir()][0]
    lg=d/slug/"evidence"/"source-ledger.jsonl"; mf=d/slug/"raw"/"_fetch-manifest.json"
    if not lg.exists() or not mf.exists():
        # ★ 缺文件要**单独报**，不许混进「0 条查不到」里当成通过
        print("！ %s 没有台账或 manifest —— **本条未检查（不是通过）**"%ws); nolg+=1; continue
    rows=[json.loads(l) for l in lg.read_text(encoding="utf-8").splitlines() if l.strip()]
    man=json.loads(mf.read_text(encoding="utf-8"))
    shas={e.get("sha256") for e in man.get("記錄",man.get("记录",[])) if isinstance(e,dict)}
    m=sum(1 for r in rows if r.get("checksum") not in shas); miss+=m
    if m: print("❌ %s 有 %d 条台账在 manifest 里查不到 sha256"%(ws,m)); ok=False
print(("✅" if not miss else "❌")+" 语料指针：**%d 个工作区**逐条核 sha256，查不到的 = %d"
      %(len(NEW)-nolg,miss)+("　（另有 %d 个未检查）"%nolg if nolg else ""))

# ★★ 台账的**定位字段**：老工作区用 `locator`，新的用 `url`——
#   我一度只查 `url`，于是把 939 行报成「缺指针」。**两个都认，缺的才是真缺。**
noloc=0; nosum=0; rowN=0
for ws in NEW:
    d=C/ws/"workspaces"; slug=[p.name for p in d.iterdir() if p.is_dir()][0]
    lg=d/slug/"evidence"/"source-ledger.jsonl"
    if not lg.exists(): continue
    rs=[json.loads(l) for l in lg.read_text(encoding="utf-8").splitlines() if l.strip()]
    rowN+=len(rs)
    noloc+=sum(1 for r in rs if not (r.get("locator") or r.get("url")))
    nosum+=sum(1 for r in rs if not (r.get("checksum") or r.get("normalized_checksum")))
print(("✅" if not nosum else "❌")+" 台账 %d 行：缺校验和 %d 行"%(rowN,nosum))
# ★ 缺定位**不许挂在上一行的 ✅ 下面**——绿勾旁边写着「重抓不回来」是自相矛盾的报告。
#   这一条是已知缺口，不是通过：那 72 行的正文在仓里（所以不影响交付），
#   但**一旦丢了就重抓不回来**，必须单独一行、单独的记号。
print(("✅" if not noloc else "！")+" 台账定位（locator 或 url）：缺 %d 行"%noloc
      + ("　—— **已知缺口，不是通过**：正文在仓里可用，但丢了就重抓不回来" if noloc else ""))

# ★★★ 重建清单：语料不进 git 之后，`_ids-rebuild.txt` 是收件人重建语料的**唯一入口**。
#   它一直是手打的 ⇒ 实测 13 个里 **10 个是坏的**（Rousseau 少 39 条、Marshall 少 22、
#   Kant 反向多出 4 条从没抓成功的），而没有任何东西会提醒。已做成 emit_ids_rebuild.py，
#   这里接上它的 --scan（只查不写），**不许再靠人记得跑**。
import subprocess
chk=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                        "/_ledgers/_pipeline/emit_ids_rebuild.py"),
                    "--scan", str(C)], capture_output=True, text=True)
tail=[l for l in chk.stdout.strip().splitlines() if l.strip()][-1:] or ["(无输出)"]
print(("✅" if chk.returncode==0 else "❌")+" 重建清单 _ids-rebuild.txt：%s"%tail[0])
if chk.returncode!=0:
    ok=False
    for l in chk.stdout.splitlines():
        if l.startswith("❌"): print("     "+l)

# ★★ 盲判用例要**正面数出来**，不能只在出错时才打印——沉默不等于通过。
#    ★ 期望值**不写死题数**：写死过一次（16/16/17/16），quick 四人补题到 32 之后
#      它当场变红，而产物其实是对的。改成**按档位判下限 + 类数必须 16**，总数只打印。
# ★★ 2026-08-13：用例清单也改成**从包里现扫**（与上面工作区清单同一个毛病）。
#   原来写死第 1 批那 8 个 slug；当天新做的 Michelangelo #185 有 32 题，
#   **一条都没被验到，而自验证照样打印「回读自验证通过」**。
# ★ **例外表：有产物而有意没有尺子的**。只许写已记档的，且必须带理由与出处。
#   不写成例外就会让整包自验证红在一件**已经查清并等用户裁定**的事上。
KNOWN_NO_RULER = {
 "john-marshall": "Marshall #173——34 条断言、十份产物都做出来了，"
   "而唯一过双卡的密封候选是纪念 John Marshall **Harlan** 的册子（同名者），"
   "holdout 归零 ⇒ **盲判装置不成立**（同 Paton #162／Kelsen #171）。三条路待用户裁定。",
}
DEEP={"abraham-lincoln","thomas-jefferson","otto-von-bismarck","johann-pestalozzi"}
tot=0; nfile=0
CASES=sorted(C.glob("wip-*/workspaces/*/evals/cases.jsonl"))
print("\n扫到 %d 份 evals/cases.jsonl（**现扫，不是写死的 8 个**）"%len(CASES))
# ★★★ 空的 cases.jsonl **不一律算失败**：已延后/拒发的人物本来就没有题。
#   分界是**这个工作区有没有产物**（persona.md）：
#     有产物而没题 ⇒ ❌ 真失败（产物做出来了却没有尺子）
#     没产物也没题 ⇒ ！ 记「未生成（该人物无产物）」，**不计入合计、不判失败**
#   第一版把 10 份空文件全判成 ❌，自验证整包失败 —— 而那 10 个全是延后/拒发的人。
nempty=0
for f in CASES:
    slug=f.parts[-3]
    lo = 32 if slug in DEEP else 16          # deep 档下限 32，其余 16
    rows=[json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    su=len({r["suite"] for r in rows})
    # ★★ 「有没有产物」不能看 persona.md 存不存在——**脚手架会造 175 字节的空壳**，
    #   实测 9 个报「有产物却 0 题」里 **8 个是空壳**。判别改成**正文里有没有 claim 标记**。
    pf=f.parent.parent/"persona.md"
    has_products = pf.exists() and "<!-- claim:" in pf.read_text(encoding="utf-8")
    if not rows:
        if has_products and slug in KNOWN_NO_RULER:
            print("！ %-24s **有产物却 0 题 —— 已知且已记档**：%s"%(slug,KNOWN_NO_RULER[slug]))
            nempty+=1
        elif has_products:
            print("❌ %-24s **有产物却 0 题**（产物做出来了却没有尺子）"%slug); ok=False
        else:
            print("！ %-24s 未生成（persona.md 是空壳，该人物无产物）—— **本条未检查，不是通过**"%slug)
            nempty+=1
        continue
    good = len(rows)>=lo and su==16
    ok &= good; tot+=len(rows); nfile+=1
    print(("✅" if good else "❌")+" %-24s %2d 题 / %2d 类（下限 %d / 16 类）"%(slug,len(rows),su,lo))
if nfile<8:
    print("❌ 只扫到 %d 份**有题的**用例，少于第 1 批的 8 份 —— 包可能不全"%nfile); ok=False
if nempty: print("　（另有 %d 份空用例未检查，见上）"%nempty)
print(("✅" if tot>=nfile*16 else "❌")+" 盲判用例合计 **%d** 题（%d 份 × 下限 16 = %d）"
      %(tot,nfile,nfile*16)); ok &= tot>=nfile*16

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
