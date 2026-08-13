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
import sys,pathlib,json,re
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
# ★★★ 2026-08-13 晚：`NEW` 要求 `wip-*/workspaces/` 存在且非空，
#   于是**扁平布局**（账本直接在 `wip-*/` 下，早期那几个人）整个落在下面四道门之外：
#   语料指针 sha256／台账校验和／台账定位／重建清单 —— 一条都扫不到它们，
#   而那四行印的是「**%d 个工作区**逐条核」，读起来像全的。实测落在门外的有 22 个，
#   其中 15 个连账本都没有（探测桩，本来就没东西可查），**7 个有真账本共 993 行**。
#   [[a-gates-scan-set-is-smaller-than-reality]]：**判据扫的集合比实况小**，第八种形状。
#   这里不改 `NEW` 的定义（四道门的读法都按 `workspaces/` 布局写死，改它要连着改四处，
#   不是移交当晚该动的），而是**把差集印出来并标「未检查，不是通过」**——
#   空默认值吞掉「不知道」是另一条踩过的坑。
OUT=[p.name for p in sorted(C.glob("wip-*")) if p.is_dir() and p.name not in NEW]
out_led=[(w, sorted((C/w).rglob("source-ledger.jsonl"))) for w in OUT]
out_has=[(w,l) for w,l in out_led if l]
if OUT:
    n_rows=sum(sum(1 for x in l[0].read_text(encoding="utf-8",errors="replace").splitlines()
                   if x.strip()) for _,l in out_has)
    print("！ 另有 %d 个 wip 目录不在上面这 %d 个里（没有 `workspaces/` 布局）："
          "其中 %d 个无账本（探测桩，无可查），**%d 个有账本共 %d 行 —— 未检查，不是通过**"
          % (len(OUT), len(NEW), len(OUT)-len(out_has), len(out_has), n_rows))
    if out_has:
        print("     " + "、".join(w for w,_ in out_has))
# ★★★ 2026-08-13：定深路径**够不着第三种布局**。
#   实测有 8 个工作区多套了一层：`wip-osler-110/workspaces/william-osler/william-osler/…`，
#   于是 `d/slug/evidence/…` 一律落空，它们被报成「没有台账」并跳过；
#   同一个毛病让 **208 道真题（8 份 cases.jsonl）打包时一次都没被验过**，
#   而自验证照样往下走。[[a-gates-scan-set-is-smaller-than-reality]]
#   ⇒ 台账与 manifest 一律**在这个 wip 目录下递归找**，不写死层数。
def _find(root, rel):
    """在 root 下递归找 rel（如 `evidence/source-ledger.jsonl`），→ 第一个命中或 None。"""
    hits=sorted(root.rglob(rel.split("/")[-1]))
    want=tuple(rel.split("/"))
    for h in hits:
        if h.parts[-len(want):]==want: return h
    return None
miss=0; nolg=0
for ws in NEW:
    d=C/ws/"workspaces"
    lg=_find(d,"evidence/source-ledger.jsonl"); mf=_find(d,"raw/_fetch-manifest.json")
    if lg is None or mf is None or not lg.exists() or not mf.exists():
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
    d=C/ws/"workspaces"
    lg=_find(d,"evidence/source-ledger.jsonl")          # ★ 同上：递归，不写死层数
    if lg is None or not lg.exists(): continue
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

# ★★★ 量测产物是不是**当前这版工具**出的。2026-08-13 实测 4 个工作区不是
#   （Kant 道 6→3，而工具的注释里早就写着那个修正）——**修好判据不等于修好数据**。
#   接在这里而不是接进 quality_check：那件会改变门的判决，属用户裁定范围；
#   **本处只是回读报告，不改任何人的过门与否**。
fresh=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                          "/_ledgers/_pipeline/check_measurements_fresh.py")],
                     capture_output=True, text=True)
ftail=[l for l in fresh.stdout.strip().splitlines() if l.strip()]
head=ftail[0] if ftail else "(无输出)"
if fresh.returncode==0:
    print("✅ 量测产物与当前工具一致：%s"%head)
elif fresh.returncode==4:
    # 语料不在这棵树里 ⇒ **未判**，不是通过，也不判整包失败
    print("★ 量测产物一致性：**未判**（语料不在本树，一份都没比对成）")
else:
    ok=False
    print("❌ 量测产物与当前工具**不一致**——产物落后于工具：")
    for l in fresh.stdout.splitlines():
        if l.strip().startswith(("·","✗")) or ":" in l and "→" in l:
            print("     "+l.strip())

# ★ 出版年早于人物出生 ⇒ 不可能是他（同名者的最后一道，枚举挡不住的那部分）。
#   Ford #188 实测：同一个姓名下**至少五个人**，删到只剩 22 条时里面还有 1856／1860 两本。
life=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                         "/_ledgers/_pipeline/check_impossible_by_lifespan.py"),
                     "--scan-all"], capture_output=True, text=True)
ltail=[l for l in life.stdout.strip().splitlines() if l.strip()]
if life.returncode==0:
    print("✅ 生卒年可能性：%s"%(ltail[0] if ltail else "(无输出)"))
elif life.returncode==5:
    print("★ 生卒年可能性：**未判**（读不到生年表）")
else:
    ok=False
    print("❌ 有「出版年早于出生、且仍判成他的」条目：")
    for l in life.stdout.splitlines():
        if l.strip().startswith("·") or l.strip().startswith("✗"): print("     "+l.strip())

# ★ 队列有没有把已结案的人排回去（同一个病 2026-08-13 犯了两次）。
q=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                      "/_ledgers/_pipeline/check_queue_reflects_reality.py")],
                 capture_output=True, text=True)
qtail=[l for l in q.stdout.strip().splitlines() if l.strip()]
if q.returncode==0:
    print("✅ 队列与已落纸的结论一致：%s"%(qtail[0] if qtail else "(无输出)"))
elif q.returncode==4:
    print("★ 队列一致性：**未判**（跑不了 next_person）")
else:
    ok=False
    print("❌ 队列还在派工已结案的人：")
    for l in q.stdout.splitlines():
        if l.strip().startswith("·"): print("     "+l.strip())

# ★★ 台账里 rights 主张公有领域，而它自己写下的出版年接不接得住。
#   2026-08-13 Dewey #190 实测：published_at=2003 而 rights=pre1931，**同一行自相矛盾**，
#   而从抓源到建台账没有任何一件判据看这两个字段。scan_copyright 只扫正文，看不到台账字段。
#   ★ 只把 ①a（按**今天**的分界也够不着）算失败；①b 分界陈旧、② 无本地凭据只打印——
#     它们权利上没问题，混进来会让这道门永远红。
ry=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                       "/_ledgers/_pipeline/check_rights_year_agree.py")],
                  capture_output=True, text=True)
rlines=[l for l in ry.stdout.splitlines() if l.strip().startswith(("①","②","③","  ①","  ②","  ③"))]
if ry.returncode==0:
    print("✅ rights 主张与出版年互相印证（无自相矛盾行）")
    for l in rlines: print("     "+l.strip())
elif ry.returncode==4:
    print("★ rights／年份印证：**未判**（一个台账都没找到）")
else:
    ok=False
    print("❌ 台账里有 rights 主张 PD 而出版年按今天的分界也够不着的行：")
    for l in ry.stdout.splitlines():
        if l.strip().startswith("·"): print("     "+l.strip())

# ★ wip-<人>-<号> 的号有没有撞。2026-08-13 实测 hopkins-189 与 churchill-189 同号；
#   根因是这个号**没有真源**（延后名单没有编号字段，next_person 看目录不看号）。
wn=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                       "/_ledgers/_pipeline/check_workspace_numbers.py")],
                  capture_output=True, text=True)
wtail=[l for l in wn.stdout.strip().splitlines() if l.strip()]
if wn.returncode==0:
    print("✅ 工作区编号唯一：%s"%(wtail[0] if wtail else "(无输出)"))
elif wn.returncode==4:
    print("★ 工作区编号：**未判**（一个 wip-* 都没有）")
else:
    ok=False
    print("❌ 工作区编号撞了：")
    for l in wn.stdout.splitlines():
        if l.strip().startswith("·"): print("     "+l.strip())

# ★★★ START-HERE.md 首屏那张表——**收件人第一眼看的六个数**。
#   2026-08-13 实测：六格里六格与实测不一致，其中「已入库人物档案 71」
#   数的是 registry/codex/ 下的**技能目录**，根本不是人物（真值 102）。
#   表头写着「数字由脚本现算」，而**并没有任何脚本在算**。
#   ⇒ 这一条必须在打包**之前**红：一份首屏就写错数的交付包，比不交更糟。
sh=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                       "/_ledgers/_pipeline/check_start_here_numbers.py")],
                  capture_output=True, text=True)
if sh.returncode==0:
    print("✅ START-HERE.md 首屏那张表：六格全部与实测一致")
    # ★★ rc=0 时也要把**第 8 项**捞出来印。它算的是「台账每条正文在不在仓里」，
    #   有真发现（wip-livermore-100：536 条、正文 0 份、连指针都没有）。
    #   原先只在 rc≠0 时印细节 ⇒ **判据算对了，交付日志把它咽下去了**。
    #   一道判据的产出不该由「它这次是不是红的」决定给不给人看。
    for l in sh.stdout.splitlines():
        if l.startswith("账本逐条可取") or l.strip().startswith("！ **取不回来**"):
            print("     " + l.strip())
elif sh.returncode==4:
    print("★ START-HERE 数字：**未判**（找不到 START-HERE.md 或不在 git 树里）")
else:
    ok=False
    print("❌ START-HERE.md 首屏那张表与实测不一致（跑 --apply 整格重写）：")
    for l in sh.stdout.splitlines():
        if l.strip().startswith(("✗","？","       表里")): print("     "+l.strip())

# ★★ 空心道：某条道的源去重后同属**一部作品**（`check_lane_distinct_works.py`）。
#   2026-08-13 抓到 Churchill #191——他的 `timeline` 2 份是同一部书的两个印本，
#   `min_lanes 3` 是一部作品数了两遍换来的，而我当天已在这份语料上做完阶段 3、4。
#   ★ **这一条不做成「有命中就红」**：Churchill 与 Marshall 是已查清、已落纸的两例，
#     且本机补不了（语料不进 git）⇒ 做成硬红就是一个**永远变不绿的红**，那不是信号。
#   ⇒ 判据改成**比对基线名单**：挡住的人 == 已记录的那两个 → 绿；
#     **多出一个新的人就红**（那才是回归）。
EXPECT_BLOCKED={"winston-churchill","john-marshall"}
lw=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                      "/_ledgers/_pipeline/check_lane_distinct_works.py")],
                  capture_output=True, text=True)
got={l.split("：")[0].strip(" ·") for l in lw.stdout.splitlines()
     if l.strip().startswith("·")}
# ★★ **子集比 ＋ 覆盖面下限**，不是相等比。
#   相等比会在「Churchill 真被补出第三条道」这种**好事**上误红
#   （合著那道门当天已因同类问题把整个包判失败一次）。
#   而「少了」真正危险的那一种是**判据扫不到东西了**——那个用覆盖面直接守：
#   有实测去重的工作区数掉下基线 18 就红。
MIN_MEASURED=18
n_measured=0
for l in lw.stdout.splitlines():
    m=re.search(r"扫过 \*\*(\d+) 个\*\*工作区", l)
    if m: n_measured=int(m.group(1))
new_blocked=sorted(got-EXPECT_BLOCKED)
if lw.returncode not in (0,1):
    print("★ 空心道：**未判**（判据 rc=%d）"%lw.returncode)
elif new_blocked or n_measured < MIN_MEASURED:
    ok=False
    if new_blocked:
        print("❌ 空心道出现**新增**被挡的人：%s（基线 %s）"
              %("／".join(new_blocked), "／".join(sorted(EXPECT_BLOCKED))))
    if n_measured < MIN_MEASURED:
        print("❌ 空心道**覆盖面缩了**：实测只量到 %d 个工作区，基线 %d"
              %(n_measured, MIN_MEASURED))
    for l in lw.stdout.splitlines():
        if l.strip().startswith("·"): print("     "+l.strip())
else:
    print("✅ 空心道：挡住的 %d 人未超出基线（%s）；量到 %d 个工作区 ≥ 基线 %d"
          %(len(got), "／".join(sorted(got)) or "无", n_measured, MIN_MEASURED))
    gone=sorted(EXPECT_BLOCKED-got)
    if gone:
        print("     ★ 基线里 %s 这次**没被挡住**——是补好了道，还是判据够不着？**要人看一眼**"
              %("／".join(gone)))
# ★ 覆盖面同时印出来：**「没红」不等于「都查过」**
for l in lw.stdout.splitlines():
    if l.startswith("扫过"): print("     "+l.strip())

# ★★ 负空间泄题（`check_negative_space_leak.py`）：**按体裁描述「我手边缺什么」，
#   等于把 holdout 的题目说出来**。Grotius #168 一天撞两次，而三道现有门全绿。
#   ★ 2026-08-13 实测：39 个有产物的工作区里 **6 个红**。修好 Dewey 之后剩 5 个，
#     **全是已判分/已结案的人**（Gantt／Nasmyth／Pasteur／Roberts-Austen／Whitworth）
#     ⇒ 按㊵「已判分即冻结」不动它们。
#   ⇒ 按**基线**比：新增一个才红。
EXPECT_LEAK={"henry-gantt","james-nasmyth","louis-pasteur",
             "william-chandler-roberts-austen","joseph-whitworth"}
leak=set(); leak_n=0
for _ws in sorted((R/"CodexSkills/skill_log_evals/persona-distiller/_corpora").glob("wip-*/workspaces/*")):
    if not (_ws/"persona.md").is_file(): continue
    leak_n+=1
    _r=subprocess.run([sys.executable, str(R/"CodexSkills/registry/codex/persona-distiller"
                                          "/scripts/check_negative_space_leak.py"), str(_ws)],
                      capture_output=True, text=True)
    if _r.returncode!=0: leak.add(_ws.name)
_new_leak=sorted(leak-EXPECT_LEAK)
if _new_leak:
    ok=False
    print("❌ 负空间泄题**新增**：%s（基线 %d 个都是已结案冻结的）"
          %("／".join(_new_leak), len(EXPECT_LEAK)))
else:
    print("✅ 负空间泄题：扫 %d 个有产物的工作区，%d 个红且**都在基线内**（已判分冻结）"
          %(leak_n, len(leak)))
    _gone=sorted(EXPECT_LEAK-leak)
    if _gone: print("     ★ 基线里 %s 这次没红——是修好了还是判据够不着？**要人看一眼**"%("／".join(_gone)))

# ★ 可得性探测前置（`check_probe_precondition.py`）：卒于 1930 年后的人排期前要先探。
#   ★ **只印现状，不参与红绿**：队列里 215 人卒年未知或在 1930 后，
#     它按设计 rc=1；做成硬门就是一道**永远红的门**。
pp=subprocess.run([sys.executable, str(R/"CodexSkills/registry/codex/persona-distiller"
                                      "/scripts/check_probe_precondition.py"),
                   "--queue", str(R/"CodexSkills/skill_log_evals/persona-distiller/_ledgers/_蒸馏队列.json"),
                   "--corpora", str(R/"CodexSkills/skill_log_evals/persona-distiller/_corpora")],
                  capture_output=True, text=True)
for l in pp.stdout.splitlines():
    if l.startswith("✗ ") or l.startswith("✓ "):
        print("     ★ 可得性探测前置：%s"%l.strip()[:110]); break

# ★★★ 合同漂移（`check_contract_drift.py`）：版本三轴单一真源、检查器两处镜像一致、
#   **发布清单 checksums.sha256 与磁盘对得上**。
#   ★ 2026-08-13 实测：它**有**调用方（quality_check 等），但**不在本脚本里**
#     ⇒ 交付包连着 5 版（build21–25）带着「checksums.sha256 与磁盘对不上 6 个文件」发了出去，
#       而回读自验证一路绿。**改了随包分发的文件却没重算清单，包里就是错的。**
#   ⇒ 做**硬门**：它现在是干净的，且修法明确（跑 build_manifest.py、把 scripts/ 同步到 references/）。
cd_=subprocess.run([sys.executable, str(R/"CodexSkills/registry/codex/persona-distiller"
                                      "/scripts/check_contract_drift.py")],
                   capture_output=True, text=True)
if cd_.returncode==0:
    print("✅ 合同漂移：无（版本三轴单一真源／镜像一致／发布清单与磁盘对得上）")
else:
    ok=False
    print("❌ 合同漂移：")
    for l in cd_.stdout.splitlines():
        if l.strip().startswith("- ["): print("     "+l.strip()[:150])

# ★★ 一个人只能有**一种**处置（`check_disposition_exclusive.py`）。
#   这是**硬门**——它不像上面两件那样有「本机修不了的既成事实」，
#   两处并存永远是错，且改起来就是移出一条。当前实测 0 错。
#   ★ 它 2026-08-10 抓到过 Steinhardt／Godin，而**此后一直没有任何代码在调它**；
#     8-13 手跑一次又抓到 Taguchi／Carmack ——「没有调用方的判据等于不存在」。
de=subprocess.run([sys.executable, str(R/"CodexSkills/registry/codex/persona-distiller"
                                      "/scripts/check_disposition_exclusive.py"),
                   "--group", str(R/"CodexSkills/registry/codex/persona-distiller-group/team-index.json"),
                   "--ledgers", str(R/"CodexSkills/skill_log_evals/persona-distiller/_ledgers"),
                   "--corpora", str(R/"CodexSkills/skill_log_evals/persona-distiller/_corpora")],
                  capture_output=True, text=True)
dtail=[l for l in de.stdout.strip().splitlines() if l.startswith("三份台账合计")]
if de.returncode==0:
    print("✅ 一人一种处置：%s"%(dtail[0] if dtail else "错 0"))
else:
    ok=False
    print("❌ 有人同时出现在两份台账里：")
    for l in de.stdout.splitlines():
        if l.startswith("✗"): print("     "+l.strip()[:140])

# ★★ 序言里声明了分工 / 「与某人合作」式署名（`check_declared_coauthor_split.py`）。
#   同样**按基线比**，不做成「有命中就红」：这 14 条都已查清并落纸
#   （Dewey 3 ＝《Ethics》1908 三个印本，序言明写 Part I 是 Tufts 写的；
#     Ford 10 ＝ IN COLLABORATION WITH SAMUEL CROWTHER；Grotius 1）。
#   ★ 这件判据 2026-08-13 修过两处，两处都钉了自测：
#     ① DocSouth 的「transcribed by Apex Data Services, Inc.」是**转写外包**不是合著
#        （误报挂在 Carver #127 这个**已入库**的人身上）；
#     ② 而那道排除第一版按邻近词一刀切，**当场杀掉一条真阳**——Ford 的 IA 扫描件
#        把「Digitized by the Internet Archive」插在题名与署名之间。
#        ⇒ 排除只绑在「转写类」构式上，`in collaboration with` 一律不压。
EXPECT_SPLIT={"john-dewey":3,"henry-ford":10,"hugo-grotius":1}
cs=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                      "/_ledgers/_pipeline/check_declared_coauthor_split.py"),
                   "--scan", str(R/"CodexSkills/skill_log_evals/persona-distiller/_corpora")],
                  capture_output=True, text=True)
got_split={}; unread=[]
for l in cs.stdout.splitlines():
    s=l.strip()
    if s.startswith("·") and ("① " in s or "③ " in s):
        w=s.split("／")[0].strip(" ·"); got_split[w]=got_split.get(w,0)+1
    m=re.match(r"^(\S+)\s+读不到 (\d+) 份", s)
    if m: unread.append(m.group(1))
# ★★ **子集比，不是相等比。** 第一版用相等，当场把整个包判失败：
#   基线是在**工作树**量的（那里语料齐），而 clone 里新工作区的 `raw/*.txt`
#   被 `.gitignore` 挡在仓外 ⇒ Dewey 与 Ford 各报 0 命中。
#   **那是没东西可读，不是没问题**——[[green-in-the-repo-dead-in-the-package]]。
#   ⇒ 少报不算回归（可能是修好了、也可能是读不到，判据自己会说哪一种）；
#     **多出一个新人、或某人比基线更多，才是回归**。
new=[w for w in got_split if w not in EXPECT_SPLIT]
more=[w for w,n in got_split.items() if w in EXPECT_SPLIT and n>EXPECT_SPLIT[w]]
if cs.returncode not in (0,1):
    print("★ 合著分工：**未判**（判据 rc=%d）"%cs.returncode)
elif new or more:
    ok=False
    print("❌ 合著分工①③出现新增：新人物 %s；比基线更多 %s（基线 %s，实测 %s）"
          %(new or "无", more or "无", EXPECT_SPLIT, got_split))
    for l in cs.stdout.splitlines():
        s=l.strip()
        if s.startswith("·") and ("① " in s or "③ " in s): print("     "+s[:120])
else:
    miss={w:n for w,n in EXPECT_SPLIT.items() if got_split.get(w,0)<n}
    print("✅ 合著分工：①③ 实测 %d 条，未超出基线（基线 %d 条）"
          %(sum(got_split.values()), sum(EXPECT_SPLIT.values())))
    if miss:
        print("     ★ 基线里有 %s 在本包内**没量到**——%s"
              %("／".join(miss), "语料不在包里（未判，不是通过）" if unread
                else "语料在而未命中，请人看一眼"))
if unread:
    print("     ★ 本包内读不到语料的工作区 %d 个（未判，不是通过）"%len(unread))

# ★★ 判分就绪度：等着判分的人，装置齐不齐、判得出判不出（`check_scoring_ready.py`）。
#   它**不判该不该发**，也不代替授权——判分要两名互相独立的评委，只能由人起。
#   ⇒ 这里只印现状，**不参与红绿**：缺预登记/有矛盾是要人看的信息，不是构建失败。
sr=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                      "/_ledgers/_pipeline/check_scoring_ready.py")],
                  capture_output=True, text=True)
for l in sr.stdout.splitlines():
    if l.startswith("真正等着判分的") or "矛盾" in l or "空心道 " in l:
        print("     ★ "+l.strip()[:150])

# ★ 踩坑库被 START-HERE 列为「开工前必读」，而它的条数/索引/文件三者一度对不上：
#   README 说 153（把 README 与 00-索引自己也数了进去），实际 151，另有 3 条没搬进仓。
ll=subprocess.run([sys.executable, str(R/"CodexSkills/skill_log_evals/persona-distiller"
                                       "/_ledgers/_pipeline/check_lessons_library.py")],
                  capture_output=True, text=True)
lt=[l for l in ll.stdout.strip().splitlines() if l.strip()]
if ll.returncode==0:
    print("✅ 踩坑库条数/索引/文件三者一致：%s"%(lt[0] if lt else "(无输出)"))
elif ll.returncode==4:
    print("★ 踩坑库：**未判**（找不到 文档/踩坑库/）")
else:
    ok=False
    print("❌ 踩坑库三者对不上：")
    for l in ll.stdout.splitlines():
        if l.strip().startswith("✗"): print("     "+l.strip())

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
# ★★★ 用 rglob，不用定深 glob：`wip-*/workspaces/*/evals/cases.jsonl` 扫到 37 份，
#   而仓里跟踪着 45 份 —— 差的 8 份全在多套一层的那种布局里（见上面 _find 的注释），
#   合计 **208 道题从来没被验过**。
CASES=sorted(p for p in C.rglob("cases.jsonl") if p.parent.name=="evals")
print("\n扫到 %d 份 evals/cases.jsonl（**rglob 现扫，不写死层数也不写死名单**）"%len(CASES))
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
# ★★★ 移交封面信里那张「包的身份证」原先是**每次打完包我手工抄进去的**。
#   2026-08-14 一晚同步了 5 次，其中一次的「打包」时间是我手打的（写成 01:35，真值 00:44）——
#   [[self-reported-numbers-must-be-computed]]。这里把那 5 行**从 sidecar 现读回填**，
#   去掉手工环节；封面信不在就跳过（只印一行，不报错）。
_COVER="$(dirname "$B")/00-你要做的两件事.md"
if [ -f "$_COVER" ]; then
  python3 - "$_COVER" "$B.sha256" <<'COVEOF'
import pathlib, re, sys
cover, side = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
s = side.read_text(encoding="utf-8")
def g(k, pat=r"(\S.*?)\s*$"):
    m = re.search(rf"^{k}\s+{pat}", s, re.M)
    return m.group(1).strip() if m else None
size = (g("大小") or "").replace(" 字节", "")
sha, tip, n, when = g("sha256"), (g("tip") or "").split()[0], g("提交数"), g("打包")
t = old = cover.read_text(encoding="utf-8")
if size and size.isdigit():
    t = re.sub(r"\| 大小 \| \*\*[\d,]+ 字节\*\* \|", f"| 大小 | **{int(size):,} 字节** |", t)
if sha:  t = re.sub(r"\| sha256 \| `[0-9a-f]{64}` \|", f"| sha256 | `{sha}` |", t)
if tip:  t = re.sub(r"\| tip \| `[0-9a-f]{40}`", f"| tip | `{tip}`", t)
if n:    t = re.sub(r"\| 提交数 \| \*\*[\d,]+\*\* \|", f"| 提交数 | **{int(n):,}** |", t)
if when: t = re.sub(r"\| 打包 \| [\d\-]+ [\d:]+ \|", f"| 打包 | {when} |", t)
cover.write_text(t, encoding="utf-8")
print("✅ 封面信身份证：已从 sidecar 现读回填" + ("（无变化）" if t == old else ""))
COVEOF
else
  echo "！ 本目录没有 00-你要做的两件事.md —— 身份证**未回填**（不是通过）"
fi
echo "包在：$B"
# ★★★ 2026-08-14 00:11 实测：输出目录名带**当天日期**（第 18 行），跨零点就换一个目录。
#   当晚 build29 落在 `…-20260813/`，build30 落在 `…-20260814/`，
#   而**移交封面信连同上传命令还留在旧目录里**——照它跑就是把旧包（少 3 个提交）传出去。
#   脚本自己 rc=0、完成标记也印了，**日志一个字都没错**，是我去核产物才发现的。
#   ⇒ 收尾时把**同级的其它 handover 目录**点名列出来，标成旧的。
_par="$(dirname "$B")"; _par="$(dirname "$_par")"
_stale=$(find "$_par" -maxdepth 2 -name 'agentdb-persona-distiller-full.bundle' \
         ! -path "$B" 2>/dev/null | sort)
if [ -n "$_stale" ]; then
  echo
  echo "⚠️  同级还有**别的日期**的交付包 —— 它们是旧的，**别传错**："
  echo "$_stale" | while read -r f; do
    echo "     旧: $f  （$(stat -f%z "$f" 2>/dev/null) 字节）"
  done
  echo "     ★ 要传的是上面那一个：$B"
fi
echo "上传（**由人按**，一条命令，公开仓不用改）："
echo "  gh release upload agentdb-handover-20260812 \"$B\" --repo LinzeColin/Private-Database --clobber"
