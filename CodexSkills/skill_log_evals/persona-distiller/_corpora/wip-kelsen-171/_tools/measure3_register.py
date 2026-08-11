#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#171 Kelsen —— **分语域**的第一人称计数（`measure2.py` 的更正）。

## 为什么要有这一把尺子

`measure2.py` 的 `cnt()` 用 `(?i)` 大小写不敏感地数 `\\bich\\b`，
于是**德语名词 `das Ich`（哲学意义的「自我」）和代词 `ich`（他本人在说话）被算成一回事**。

2026-08-11 实测：*Politische Weltanschauung und Erziehung*（1918）
25 处命中里 **13 处是名词**（`Ich-Bewußtsein`、`Ich und Welt`、`das Faktum Ich`、
`dem individualistischen Ich`……）——那一篇正好在论个人主义与集体主义，
**满篇都在把「自我」当对象谈**。台账 `04-声口密度实测.md` 记的 **29.39／万词
因此虚高一倍**，真值 14.55。

★ 这是 [[measured-voice-in-the-wrong-register]] 的同一族：
  上一次是拿合著技术论文的第一人称密度判「有没有声口」，
  这一次是拿**被当作研究对象的那个词**去判「他在不在说话」。

## ★★ 另一半：**不是** `measure2.py` 的锅

同日我用临时脚本复核时，把 1916 件数成 48 处（真值 14）。
原因是我的分词字符类 `[A-Za-zÄÖÜäöüßÀ-ÿ]+` **覆盖不到长 s `ſ`（U+017F）**，
于是 Fraktur 的 `ſich`（反身代词 sich）被切成 `ich` 计进声口——48 里 34 处是假的。

`measure2.py` 用的是正则 `\\bich\\b`，而 Python 的 `\\w` 认得 `ſ` 是字母，
所以它**本来就不会犯这个错**。⇒ 台账那一列没问题，出错的是我的临时脚本。
[[regex-must-clear-the-corpus-language]]：正则要过语料的语种关，**也要过它的字形关**。

## 判据

1. **名词 `Ich`**：大写且**不在句首**，或出现在 `Ich-` 复合词里。
2. **可能在引文内**：命中点前 400 字符内有开引号且其间没有闭引号。
   ★ 这批 OCR 的引号字符是乱的（10 种混用、开闭配不上），
     所以这一栏**只报不扣**——[[counts-need-their-cutoff-stated]]：
     单给一个数等于替读者选了一档口径。
3. **声口** = 总数 − 名词。另给「声口下限」= 总数 − 名词 − 可能引文内。

用法：
    python3 _tools/measure3_register.py            # 扫台账全部 train+holdout 件
    python3 _tools/measure3_register.py --self-test
"""
import json
import pathlib
import re
import sys

WS = pathlib.Path(__file__).resolve().parent.parent / 'workspaces/hans-kelsen'

OPEN_Q = '„“«‚‘"'
CLOSE_Q = '“”»‘’"'
QUOTE_WINDOW = 400


def dehyphenate(text: str) -> str:
    """折行连字符归一；随后把空白压成单空格，便于定位上下文。"""
    text = re.sub(r'-\s*\n\s*', '', text)
    return re.sub(r'\s+', ' ', text)


def classify(text: str, word: str = 'ich') -> dict:
    """把 `word` 的每一处命中分成 名词／可能引文内／声口。"""
    flat = dehyphenate(text)
    cap = word.capitalize()
    total = noun = quoted = 0
    samples = {'noun': [], 'quoted': [], 'voice': []}
    for m in re.finditer(r'\b%s\b|\b%s\b' % (word, cap), flat):
        total += 1
        hit = m.group()
        before = flat[max(0, m.start() - 40):m.start()]
        # ★ 句首的大写是代词，不是名词——`Ich halte es nicht für einen Zufall`
        sentence_start = bool(re.search(r'(^|[.!?:;»"”])\s*$', before)) or m.start() == 0
        # ★ `Ich-Bewußtsein` 这类复合词一律是名词，不看句首
        compound = flat[m.end():m.end() + 1] == '-'
        is_noun = hit == cap and (compound or not sentence_start)
        window = flat[max(0, m.start() - QUOTE_WINDOW):m.start()]
        last_open = max((window.rfind(c) for c in OPEN_Q), default=-1)
        last_close = max((window.rfind(c) for c in CLOSE_Q), default=-1)
        in_quote = last_open > last_close
        ctx = flat[max(0, m.start() - 60):m.end() + 60]
        if is_noun:
            noun += 1
            bucket = 'noun'
        else:
            if in_quote:
                quoted += 1
            bucket = 'quoted' if in_quote else 'voice'
        if len(samples[bucket]) < 3:
            samples[bucket].append(ctx)
    words = len(re.findall(r'\w+', flat))
    voice = total - noun
    return {'words': words, 'total': total, 'noun': noun, 'quoted': quoted,
            'voice': voice, 'voice_floor': voice - quoted,
            'per10k': round(voice * 1e4 / words, 2) if words else 0.0,
            'per10k_floor': round((voice - quoted) * 1e4 / words, 2) if words else 0.0,
            'samples': samples}


# ---- 自测夹具：**逐字取自本工作区语料**，不是我照着症状编的 ----
# [[fixtures-cleaner-than-the-real-thing]]：夹具比原文干净就等于没测。
_FX_NOUN = ('Wenn der Universalismus nur einer Seelenverfassung adäquat ist, deren '
            'metaphysisches Ich-Bewußtsein verhältnismäßig schwach betont ist, so daß '
            'die Beziehung von Ich und Welt, Ich und Gesellschaft oder Ich und Staat '
            'nicht als Gegensatz, sondern als höhere harmonische Einheit in die '
            'Erscheinung tritt')
_FX_VOICE = ('Indem ich die Erörterung dieses Postulates aufnehme, trete ich aus der '
             'Ebene einer Seinserklärung und kausalen Wirklichkeitebeschreibung in ein '
             'Gebiet der Soll-Betrachtung.')
_FX_SENTENCE_START = 'Ich halte es nicht für einen Zufall, daß in dem Lande des intensivsten politischen Lebens'
_FX_QUOTED = ('„Staat, was ist das? Wohlan! Jetzt tut mir die Ohren auf, denn jetzt sage '
              'ich euch ein Wort vom Tode der Völker.“')
# ★ 长 s：Fraktur 的反身代词。**分词法会把它切成 `ich`**，正则不会。
_FX_LONG_S = 'einer Metaphyſik findet ſich der charakteriſtiſche Zug, daß ſich die Kategorien unterſcheiden'


def self_test() -> int:
    fails = []

    def eq(label, got, want):
        if got != want:
            fails.append('%s：期望 %s，实得 %s' % (label, want, got))

    # ① 名词：`Ich-Bewußtsein` + `Ich und Welt/Gesellschaft/Staat` 共 4 处，声口 0
    r = classify(_FX_NOUN)
    eq('① 名词全判为名词', (r['total'], r['noun'], r['voice']), (4, 4, 0))

    # ② 声口：句中小写 ich 两处
    r = classify(_FX_VOICE)
    eq('② 句中小写是声口', (r['total'], r['noun'], r['voice']), (2, 0, 2))

    # ③ ★ 过校正守卫：**句首大写 Ich 是代词，不许判成名词**
    r = classify(_FX_SENTENCE_START)
    eq('③ 句首大写仍是声口', (r['total'], r['noun'], r['voice']), (1, 0, 1))

    # ④ 引文内：尼采那段，单列一栏（不从声口里扣）
    r = classify(_FX_QUOTED)
    eq('④ 引文内单列', (r['total'], r['noun'], r['quoted'], r['voice']), (1, 0, 1, 1))

    # ⑤ ★★ 长 s：`ſich` 一处都不许算成 ich（我的临时脚本就栽在这里）
    r = classify(_FX_LONG_S)
    eq('⑤ 长 s 的 ſich 不算 ich', r['total'], 0)

    # ⑥ ★ 反向：把 ſ 换成普通 s 后，`sich` 同样不许算（证明 ⑤ 不是靠字符怪才对的）
    r = classify(_FX_LONG_S.replace('ſ', 's'))
    eq('⑥ 普通 sich 也不算', r['total'], 0)

    for line in fails:
        print('✗ ' + line, file=sys.stderr)
    print('measure3_register 自测：%d/6 通过' % (6 - len(fails)), file=sys.stderr)
    return 1 if fails else 0


def main() -> int:
    if '--self-test' in sys.argv[1:]:
        return self_test()
    rows = [json.loads(line) for line
            in (WS / 'evidence/source-ledger.jsonl').read_text(encoding='utf-8').splitlines()
            if line.strip()]
    out = []
    print('%-20s %-6s %-10s %8s %6s %6s %6s %8s %9s' %
          ('source_id', '年', '道', '词数', '总', '名词', '引文', '**声口**', '声口/万词'))
    for rec in sorted(rows, key=lambda r: str(r.get('published_at'))):
        path = WS / rec['local_path']
        if not path.is_file():
            print('✗ 取不到：%s' % rec['local_path'], file=sys.stderr)
            return 2
        res = classify(path.read_text(encoding='utf-8', errors='replace'))
        lane = ','.join(rec.get('dimensions', [])) or '-'
        print('%-20s %-6s %-10s %8d %6d %6d %6d %8d %9.2f' %
              (rec['source_id'], rec.get('published_at', '?'), lane[:10],
               res['words'], res['total'], res['noun'], res['quoted'],
               res['voice'], res['per10k']))
        out.append({'source_id': rec['source_id'], 'published_at': rec.get('published_at'),
                    'dimensions': rec.get('dimensions', []), 'split': rec.get('split'),
                    **{k: v for k, v in res.items() if k != 'samples'}})
    dest = pathlib.Path(__file__).resolve().parent / 'measure3_register.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n→ 已写 %s' % dest.name, file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
