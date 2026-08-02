#!/usr/bin/env bash
# 灌库：Galen of Pergamon #101
#
# 分层纪律（来自 meta.json:attribution_basis）：
#   · 89 部真作 → P1，--author "Galen"
#   · 16 部伪托/存疑 → **一条都不灌**。ingest 的 --tier 没有 P1-D 这一档，
#     而把它们塞成 S2 只会让它们以「材料」身份进入下游；
#     真伪分层的意义就是**不让它们进训练**。它们逐条列在 meta.json 里，可查可审。
#   · Athenaeus → P2（**全语料唯一的同期第三人称**）
#   · 现代学术 → S1
#   · De indolentia → holdout（2005 年才重见天日，不在 Kühn，**按构造零泄漏**）
set -euo pipefail
SK=/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller
SP=/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-character-distillation-skill-reorganize-d57595/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/pd-work
G=/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-character-distillation-skill-reorganize-d57595/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/galen
WS=$SP/ws-galen/galen-of-pergamon
C=$SP/galen-corpus
LOC="https://github.com/galenus-verbatim/galenus_cts (TEI-XML, CTS urn:cts:greekLit:tlg0057)"
RIGHTS="public-domain (ancient text); repository CC-BY-SA"

ing () {  # ing <dimension> <files...>
  local dim="$1"; shift
  python3 "$SK/scripts/ingest.py" "$WS" "$@" \
    --tier P1 --author "Galen" --language grc \
    --source-type "tei-xml-critical-edition" --dimension "$dim" \
    --rights "$RIGHTS" --locator "$LOC" \
    --abstract "Galen 本人著作，希腊文校勘本纯文本；真伪按 meta.json:attribution_basis 分层，本条在真作之列" \
    >/dev/null
}

# ── writings：方法论与理论主干 ───────────────────────────────────────
ing writings $(cd "$C" && ls galen_tlg00{1,2,3,4,5,6,7,8,9}_grc.txt 2>/dev/null | sed "s|^|$C/|")
ing writings $(cd "$C" && ls galen_tlg01{0,1,2,3,4,5}_grc.txt 2>/dev/null | sed "s|^|$C/|")
ing writings $(cd "$C" && ls galen_tlg02{0,1,2,3,4,5}_grc.txt 2>/dev/null | sed "s|^|$C/|")

# ── expression：长篇第一人称、语体最富 ──────────────────────────────
ing expression $(cd "$C" && ls galen_tlg03{0,1,2,3}_grc.txt galen_tlg0{36,37,38,39}_grc.txt 2>/dev/null | sed "s|^|$C/|")

# ── decisions：临床决断与治疗方法 ───────────────────────────────────
ing decisions $(cd "$C" && ls galen_tlg0{41,42,43,44,45,46,47}_grc.txt 2>/dev/null | sed "s|^|$C/|")
ing decisions $(cd "$C" && ls galen_tlg0{50,51,53,54,55}_grc.txt 2>/dev/null | sed "s|^|$C/|")

# ── conversations：注疏体（引一句、答一句）与对具名论敌的驳论 ────────
ing conversations $(cd "$C" && ls galen_tlg0{87,88,89,90,91,92,93,94,95}_grc.txt 2>/dev/null | sed "s|^|$C/|")

# ── timeline：★ 自著目录与自述 —— 归属依据的原件 ────────────────────
python3 "$SK/scripts/ingest.py" "$WS" "$C/galen_tlg104_grc.txt" "$C/galen_tlg105_grc.txt" \
  --tier P1 --author "Galen" --language grc --dimension timeline \
  --source-type "tei-xml-critical-edition" --rights "$RIGHTS" --locator "$LOC" \
  --abstract "★ De libris propriis 与 De ordine librorum suorum —— 他本人编纂的真作目录，为对抗市面冒名伪托本而写。**本工作区 attribution_basis 的 authority 原件。**" >/dev/null

ing timeline $(cd "$C" && ls galen_tlg1{00,01,02,03}_grc.txt 2>/dev/null | sed "s|^|$C/|")

# ── external：★ 全语料唯一的同期第三人称 ────────────────────────────
python3 "$SK/scripts/ingest.py" "$WS" "$G/bodies/athenaeus_1A.html" \
  --tier P2 --author "Athenaeus of Naucratis" --language en \
  --source-type "ancient-third-party-account" --dimension external \
  --rights "public-domain (LacusCurtius transcription)" \
  --locator "https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Athenaeus/1A*.html" \
  --abstract "★ Deipnosophistae 1.1e 提到「帕加马的盖伦」为宴客之一，约两句。**这是探源能确认的唯一同期第三人称见证**——他活得比所有能描述他的人都久。" >/dev/null

echo "灌库完成，账本统计："
python3 - <<PY
import json, pathlib
from collections import Counter
p = pathlib.Path("$WS/research/source-universe.json")
d = json.loads(p.read_text(encoding="utf-8"))
rows = d if isinstance(d, list) else d.get("sources", [])
print(" 总数", len(rows))
print(" tier", Counter(r.get("tier") for r in rows))
print(" split", Counter(r.get("split") for r in rows))
lanes = Counter()
for r in rows:
    for x in (r.get("dimensions") or []): lanes[x] += 1
print(" lanes", dict(lanes))
PY
