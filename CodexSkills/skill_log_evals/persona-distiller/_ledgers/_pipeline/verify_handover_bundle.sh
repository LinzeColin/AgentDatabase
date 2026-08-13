#!/usr/bin/env bash
# verify_handover_bundle.sh —— **接手方自己验包**，一条命令，退出码说话。
#
# ## 为什么要有这个
#
# 2026-08-14 我核一次包，**三条手敲的检查全是错的**：
#   ① grep「构建完成」—— 脚本印的其实是「回读自验证通过」，我读到 0 就以为构建没成；
#   ② `bundle list-heads | grep refs/heads/main` —— 包是 `--all` 打的，里面有几十个
#      `refs/codex/…`，那条 main 是**远端旧引用** `acf6b0e8`，我据此报「tip ✗ 不等」；
#      真正该看的是 `HEAD` 那一行（`5ac051ad`，与工作树一致）。
#   ③ sidecar 当成 `*.txt` 去 grep —— 它叫 `*.bundle.sha256`，于是「记录」是空的。
# 三条全部**指向不存在的出口**，而每一条都能让人得出相反的结论。
# ⇒ 手敲的核对命令是**没有版本、没有自测**的，必然漂。落成文件，配自测。
#
# ## 它验什么（**每一项都从产物里读，不信任何自述**）
#
#   1. 包存在、`git bundle verify` 通过
#   2. 实测 sha256 == sidecar 里写的 sha256
#   3. 包里的 **HEAD** ref == sidecar 里写的 tip
#   4. 从包里现算的提交数 == sidecar 里写的提交数
#   5. **真 clone 一次**，从 clone 里读回 HANDOFF.md，确认不是空壳
#
# ## 它验不了什么（**必须一起念**）
#
#   - 它**不判内容对不对**，只判「这个包是不是它自称的那个包、能不能 clone 出来」。
#   - sidecar 与包是一起产出的，**同源**；本件能抓的是「包被换了/坏了/传错了目录」，
#     抓不了「打包时就把错的东西打进去了」。那一层靠包里的判据自己跑。
#     [[same-source-self-attestation]]
#   - ★★ **上面 5 项全过 ≠ 拿的是最新那个包。** 旧包自己也自洽：2026-08-13 那个
#     （2,359 提交）跑本件同样 7 项全绿，只是少 43 个提交。**「自洽」与「最新」是两件事。**
#     ⇒ 要判「是不是该拿的那一个」，必须从**外面**给一个期望值：`--expect-tip <sha>`。
#     交付目录的封面信与仓根 HANDOFF.md 里都写着该用哪个 tip。
#
# 用法：
#   bash verify_handover_bundle.sh <交付目录>
#   bash verify_handover_bundle.sh <交付目录> --expect-tip <sha>   ← ★ 判「是不是最新那个」
#   bash verify_handover_bundle.sh --self-test
#
# 退出码：0＝全过；1＝有不通过项（**逐条印出来**）；2＝用法错/目录不对
set -uo pipefail          # ★ 故意不用 -e：要把每一项都跑完再汇总，不许跑一半就死
                          #   [[pipe-to-tail-hides-the-exit-code]]

OK=0; BAD=0
say() { printf '  %s %s\n' "$1" "$2"; }
pass() { OK=$((OK+1)); say "✓" "$1"; }
fail() { BAD=$((BAD+1)); say "✗" "$1"; }
chk()  { if [ "$2" = "$3" ]; then pass "$1（$2）"; else fail "$1：实测 [$2] ≠ 记录 [$3]"; fi; }

self_test() {
  echo "自测：造一个真包，逐项验；再逐项弄坏，确认每一项都会红"
  T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
  git init -q "$T/src"
  ( cd "$T/src"
    git config user.email t@t; git config user.name t
    echo hi > HANDOFF.md; git add HANDOFF.md; git commit -qm one
    echo more >> HANDOFF.md; git commit -qam two ) || { echo "✗ 造样本失败"; return 1; }
  mkdir -p "$T/d"; B="$T/d/agentdb-persona-distiller-full.bundle"
  git -C "$T/src" bundle create "$B" --all >/dev/null 2>&1
  TIP="$(git -C "$T/src" bundle list-heads "$B" | awk '$2=="HEAD"{print $1}')"
  N="$(git -C "$T/src" rev-list --count "$TIP")"
  H="$(shasum -a 256 "$B" | awk '{print $1}')"
  w() { printf '文件   x\n大小   1 字节\nsha256 %s\ntip    %s\n提交数 %s\n打包   x\n' \
        "$1" "$2" "$3" > "$B.sha256"; }
  w "$H" "$TIP" "$N"
  ( verify "$T/d" >/dev/null 2>&1 ); r=$?
  [ $r -eq 0 ] && say "✓" "★ 好包 → rc=0" || { say "✗" "★ 好包却 rc=$r"; return 1; }
  local bad=0
  # ★ 反例三连：每一项都必须**单独**能把它判红
  w "deadbeef$(printf '%056d' 0)" "$TIP" "$N"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] && say "✓" "★ 反例：sha256 对不上 → 红" || { say "✗" "sha256 错了却绿"; bad=1; }
  w "$H" "0000000000000000000000000000000000000000" "$N"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] && say "✓" "★ 反例：tip 对不上 → 红" || { say "✗" "tip 错了却绿"; bad=1; }
  w "$H" "$TIP" "999"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] && say "✓" "★ 反例：提交数对不上 → 红" || { say "✗" "提交数错了却绿"; bad=1; }
  w "$H" "$TIP" "$N"; : > "$B"          # 包清空
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] && say "✓" "★ 反例：包是空的 → 红" || { say "✗" "空包却绿"; bad=1; }
  rm -f "$B.sha256"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] && say "✓" "★ 反例：sidecar 不在 → 红（**不许当成没问题**）" || { say "✗" "缺 sidecar 却绿"; bad=1; }
  # ★★★ 审计没过的那次构建：包自洽、8 项本会全绿，只有这张标记拦得住
  git -C "$T/src" bundle create "$B" --all >/dev/null 2>&1
  w "$(shasum -a 256 "$B" | awk '{print $1}')" "$TIP" "$N"
  echo x > "$T/d/BUILD-FAILED.txt"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -ne 0 ] \
    && say "✓" "★★★ **反例：包完全自洽，但旁边有 BUILD-FAILED.txt → 红**（审计没过的包不许上传）" \
    || { say "✗" "审计没过的包却绿"; bad=1; }
  rm -f "$T/d/BUILD-FAILED.txt"
  ( verify "$T/d" >/dev/null 2>&1 ); [ $? -eq 0 ] && say "✓" "★ 正对照：标记删掉后又是绿的" || { say "✗" "标记删了仍红"; bad=1; }
  # ★★ --expect-tip：对的放行、错的判红（这是唯一能分辨「旧包」的一项）
  git -C "$T/src" bundle create "$B" --all >/dev/null 2>&1
  w "$(shasum -a 256 "$B" | awk '{print $1}')" "$TIP" "$N"
  ( verify "$T/d" "$TIP" >/dev/null 2>&1 ); [ $? -eq 0 ] && say "✓" "★★ --expect-tip 给对了 → 绿" || { say "✗" "expect-tip 对却红"; bad=1; }
  ( verify "$T/d" "0000000000000000000000000000000000000000" >/dev/null 2>&1 ); [ $? -ne 0 ] \
    && say "✓" "★★ **反例：包自洽但 tip 不是期望的那个 → 红**（这正是「拿了旧包」那一种）" \
    || { say "✗" "旧包却绿"; bad=1; }
  [ $bad -eq 0 ] && { echo; echo "✓ 全过"; return 0; } || { echo; echo "✗ 有不符"; return 1; }
}

verify() {
  D="${1%/}"
  EXPECT="${2:-}"
  B="$D/agentdb-persona-distiller-full.bundle"
  S="$B.sha256"
  echo "验：$D"
  # ★★ 先看有没有「这次构建审计没过」的标记。包是在审计**之前**写好的，
  #   审计失败时它照样自洽，下面 8 项会全绿——这一项是唯一能拦住它的。
  if [ -f "$D/BUILD-FAILED.txt" ]; then
    fail "**这个包来自审计没过的那次构建**（旁边有 BUILD-FAILED.txt）——不要上传"
    while IFS= read -r _l; do say " " "   $_l"; done < "$D/BUILD-FAILED.txt"
    echo; echo "❌ $BAD 项不通过"; return 1
  fi
  [ -s "$B" ] || { fail "包不存在或是空的：$B"; echo; echo "✗ $BAD 项不通过"; return 1; }
  pass "包在（$(wc -c < "$B" | tr -d ' ') 字节）"
  [ -s "$S" ] || { fail "sidecar 不在：$S —— **没有可比对的记录，不是「没问题」**"; echo; echo "✗ $BAD 项不通过"; return 1; }

  git bundle verify "$B" >/dev/null 2>&1 && pass "git bundle verify 通过" || fail "git bundle verify 不通过"

  R_SHA="$(awk '/^sha256/{print $2}' "$S")"
  R_TIP="$(awk '/^tip/{print $2}' "$S")"
  R_N="$(awk '/^提交数/{print $2}' "$S")"
  chk "sha256" "$(shasum -a 256 "$B" | awk '{print $1}')" "$R_SHA"
  # ★★ 要 HEAD 那一行，不是 refs/heads/main —— 包是 --all 打的，main 可能是远端旧引用
  A_TIP="$(git bundle list-heads "$B" 2>/dev/null | awk '$2=="HEAD"{print $1}')"
  chk "tip（包里的 HEAD ref）" "$A_TIP" "$R_TIP"

  T="$(mktemp -d)"
  if git clone -q "$B" "$T/r" 2>/dev/null; then
    pass "真 clone 成功"
    chk "提交数（从 clone 现算）" "$(git -C "$T/r" rev-list --count HEAD)" "$R_N"
    if [ -s "$T/r/HANDOFF.md" ]; then
      pass "clone 里 HANDOFF.md 有内容（$(wc -l < "$T/r/HANDOFF.md" | tr -d ' ') 行）"
    else
      fail "clone 里 HANDOFF.md 不存在或是空的 —— 包能 clone 不等于内容在"
    fi
  else
    fail "clone 不出来"
  fi
  rm -rf "$T"

  # ★★ 外部期望值：唯一能判「是不是该拿的那一个」的检查。没给就明说没判。
  if [ -n "$EXPECT" ]; then
    chk "★ tip 与外部期望值" "$A_TIP" "$EXPECT"
  else
    say "！" "★ **没给 --expect-tip ⇒ 「是不是最新那个包」这一项未判**，不是通过。"
    say " " "   旧包自己也全绿（2026-08-13 那个 2,359 提交）。期望值写在封面信里。"
  fi

  # ★ 同级还有别的日期目录 ⇒ 提醒，但不判红（本件只管手上这一个）
  P="$(dirname "$D")"
  for o in "$P"/agentdb-handover-*/; do
    [ "${o%/}" = "$D" ] && continue
    [ -e "${o}agentdb-persona-distiller-full.bundle" ] || continue
    say "！" "同级还有别的日期的包：${o} —— **别传错**"
  done

  echo
  if [ $BAD -eq 0 ]; then echo "✅ $OK 项全过 —— 这个包就是 sidecar 自称的那个包，且 clone 得出来"; return 0
  else echo "❌ $BAD 项不通过（过 $OK 项）"; return 1; fi
}

case "${1:-}" in
  --self-test) self_test ;;
  "") echo "用法：bash $0 <交付目录>｜bash $0 --self-test"; exit 2 ;;
  *) [ -d "$1" ] || { echo "★ 不是目录：$1"; exit 2; }
     if [ "${2:-}" = "--expect-tip" ]; then
       [ -n "${3:-}" ] || { echo "★ --expect-tip 后面要跟一个 sha"; exit 2; }
       verify "$1" "$3"
     else verify "$1"; fi ;;
esac
