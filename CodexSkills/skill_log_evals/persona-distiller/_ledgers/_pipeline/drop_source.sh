#!/usr/bin/env bash
# 剔掉一份语料——**这不是一个动作，是一串**。
#
# ★★ 2026-08-13 一天之内漏了三次（Dewey／Churchill／Ford），
#    每次都是打包时被 check_measurements_fresh 或 emit_ids_rebuild 抓到：
#      · 删了文件没重跑**分道** ⇒ `_lanes.json` 停在删之前（writings 17→15、timeline 10→9）
#      · 删了文件没重出**复原指针** ⇒ `_ids-rebuild.txt` 多出一条抓不回来的 id
#    ⇒ 写成脚本，**不靠人记得**。
#
# 用法：bash drop_source.sh <工作区> <文件名> "<剔除理由>"
#   例：bash drop_source.sh _corpora/wip-x/workspaces/y mylifeandwork07213gut.txt "PG 电子本，年份与 rights 矛盾"
#
# ★ manifest 里那条**保留**、改 status=剔除并写明理由——
#   删记录等于把凭据一起删掉，留着才叫出处。
set -uo pipefail
WS="${1:?要给工作区路径}"; FILE="${2:?要给文件名}"; WHY="${3:?要给剔除理由}"
HERE="$(cd "$(dirname "$0")" && pwd)"

python3 - "$WS" "$FILE" "$WHY" <<'PY'
import json, pathlib, sys, collections
ws, fname, why = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
mp = ws / "raw/_fetch-manifest.json"
m = json.loads(mp.read_text(encoding="utf-8"))
hit = 0
for rec in m["记录"]:
    if rec.get("file") == fname:
        rec["原 status"] = rec.get("status"); rec["status"] = "剔除"; rec["剔除理由"] = why
        hit += 1
if hit != 1:
    print(f"★ manifest 里匹配到 {hit} 条（应为 1）——停手，不要继续"); sys.exit(2)
c = collections.Counter(r["status"] for r in m["记录"])
m["已取回"] = c["已取回"]; m["剔除"] = c.get("剔除", 0); m["请求数"] = len(m["记录"])
mp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
f = ws / "raw" / fname
if f.is_file():
    f.unlink()
print(f"✓ 已删 {fname}；manifest {dict(c)}")
PY
rc=$?; [ $rc -ne 0 ] && { echo "★ 第 1 步失败 rc=$rc，后面不跑"; exit $rc; }

echo "== 2/5 dedup =="   ; python3 "$HERE/dedup_corpus.py" --raw "$WS/raw" >/dev/null || exit 1
echo "== 3/5 台账 =="     ; python3 "$HERE/emit_source_ledger.py" --raw "$WS/raw" --workspace "$WS" >/dev/null || exit 1
echo "== 4/5 分道 =="     ; python3 "$HERE/assign_lanes.py" --raw "$WS/raw" >/dev/null || exit 1
echo "== 5/5 复原指针 ==" ; python3 "$HERE/emit_ids_rebuild.py" --raw "$WS/raw" >/dev/null || exit 1

echo
echo "== 回头验（这几件就是抓到前三次的那几件）=="
python3 "$HERE/check_measurements_fresh.py" >/dev/null 2>&1; echo "  量测产物一致        rc=$?"
python3 "$HERE/emit_ids_rebuild.py" --scan "$(dirname "$(dirname "$WS")")/.." --check >/dev/null 2>&1
python3 "$HERE/check_rights_year_agree.py" --ledger "$WS/evidence/source-ledger.jsonl" >/dev/null 2>&1; echo "  rights 与年份印证   rc=$?"
echo
echo "★ 还要人做的两件：① 若已切过密封集，重跑 assign_holdout 与 check_holdout_overlap；"
echo "                  ② 若首屏那张表的数会变，跑 check_start_here_numbers.py --apply"
