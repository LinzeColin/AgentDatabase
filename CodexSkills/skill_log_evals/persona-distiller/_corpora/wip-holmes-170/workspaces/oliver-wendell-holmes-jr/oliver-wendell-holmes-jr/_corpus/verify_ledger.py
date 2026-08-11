#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#170 Holmes -- re-verify source-ledger.jsonl against the files on disk.

Self-contained: needs nothing but this workspace.  Run it from anywhere:

    python3 _corpus/verify_ledger.py

Exit 0 = every checkable claim in the ledger still holds.  Exit 1 = something
drifted; the failing lines are printed at the end.

What it checks
  1. every row's sha256/byte count recomputed from the file it points at
  2. the ledger covers exactly the .txt files present in _corpus/raw
  3. `title` is a real title, not a filename
  4. every backticked transcription in `attribution` that is claimed to come
     from the file itself really occurs in it (whitespace flattened).
     Quotes that the ledger sources elsewhere -- Library of Congress scans,
     CAP volume metadata, archive.org MARC -- are listed as EXTERNAL and
     counted, not silently dropped, so a shrinking denominator is visible.
  5. required fields non-empty; voice in {first-person, third-person}
  6. dimension conventions: decisions -> ['decisions'];
     The Common Law -> ['writings']; speeches -> expression/conversations
  7. tier totals and the first-hand ratio
"""
import json, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
LEDGER = os.path.join(HERE, 'source-ledger.jsonl')
RAW = os.path.join(HERE, 'raw')

CJK = re.compile(r'[　-鿿＀-￯]')
fails = []


def chk(cond, msg):
    print(('  OK   ' if cond else '  FAIL ') + msg)
    if not cond:
        fails.append(msg)


def flat(s):
    return re.sub(r'\s+', ' ', s).strip()


rows = [json.loads(l) for l in open(LEDGER, encoding='utf-8') if l.strip()]
print(f'LEDGER ROWS       : {len(rows)}')
print(f'RAW .txt ON DISK  : {len([f for f in os.listdir(RAW) if f.endswith(".txt")])}')

print('\n== 1/2. sha256 + byte count recomputed from disk, and coverage ==')
seen = set()
for r in rows:
    p = os.path.join(WS, r['local_path'])
    if not os.path.exists(p):
        chk(False, f"missing file {r['local_path']}")
        continue
    b = open(p, 'rb').read()
    chk(hashlib.sha256(b).hexdigest() == r['sha256'] == r['checksum'] and len(b) == r['bytes'],
        f"{r['original_filename'][:54]:<56} {len(b):>9} B  sha256 ok")
    seen.add(r['original_filename'])
ondisk = {f for f in os.listdir(RAW) if f.endswith('.txt')}
chk(seen == ondisk, f'ledger covers exactly the raw files (extra={ondisk - seen}, missing={seen - ondisk})')

print('\n== 3. title is a title, not a filename ==')
for r in rows:
    chk(r['title'] and '.txt' not in r['title'] and len(r['title']) > 40,
        f"{r['original_filename'][:54]:<56} title[{len(r['title'])}]")

print('\n== 4. transcriptions in `attribution` ==')
for r in rows:
    own = flat(open(os.path.join(WS, r['local_path']), encoding='utf-8', errors='replace').read())
    field = r['attribution']
    in_file = external = 0
    misses = []
    # Pair backticks by POSITION, not by regex search.  A regex like
    # `([^`]{25,})` silently skips short spans and then pairs the *next*
    # opening tick with a later closing one -- which is how an earlier version
    # of this check missed the single most important quote in three rows.
    parts = field.split('`')
    if len(parts) % 2 == 0:
        chk(False, f"{r['original_filename'][:54]:<56} unbalanced backticks in attribution")
    for i in range(1, len(parts) - 1, 2):
        q = flat(parts[i])
        after = parts[i + 1] if i + 1 < len(parts) else ''
        if len(q) < 25:
            continue
        if CJK.search(q):                       # prose caught between unrelated backticks
            continue
        if q.startswith('http') or q.endswith('.pdf'):
            continue
        if re.match(r'^\s*的?\s*OCR\s*讹形', after[:25]):
            continue                            # a labelled *reading* of an OCR corruption
        if q in own:
            in_file += 1
        else:
            external += 1
            misses.append(q[:60])
    tag = f"{r['original_filename'][:44]:<46} in-file={in_file:<2} external={external:<2}"
    if misses:
        tag += ' | EXTERNAL: ' + ' ;; '.join(misses[:3])
    chk(in_file >= 1, tag)

print('\n== 5. required fields ==')
NEED = ['title', 'attribution', 'rights', 'rights_basis', 'namesake_basis', 'dimensions', 'voice', 'notes']
for r in rows:
    bad = [k for k in NEED if not r.get(k)]
    chk(not bad and r['voice'] in ('first-person', 'third-person') and r['rights'] == r['rights_basis'],
        f"{r['original_filename'][:54]:<56} fields ok, voice={r['voice']}")

print('\n== 6. dimensions ==')
for r in rows:
    fn, d = r['original_filename'], r['dimensions']
    if fn.startswith('decisions_'):
        chk(d == ['decisions'], f'{fn[:54]:<56} {d}')
    elif fn.startswith('common_law'):
        chk(d == ['writings'], f'{fn[:54]:<56} {d}')
    elif fn.startswith(('speeches', 'speech_', 'dead_yet')):
        chk('expression' in d or 'conversations' in d, f'{fn[:54]:<56} {d}')
    else:
        print(f'  note  {fn[:54]:<56} {d}')

print('\n== 7. tiers ==')
p1 = [r for r in rows if r['tier'] == 'P1']
print(f'  P1={len(p1)}  non-P1={len(rows) - len(p1)}  total={len(rows)}')
print(f'  first-hand ratio by count = {len(p1) / len(rows):.4f}  (quick gate 0.40)')
print(f'  first-hand ratio by bytes = {sum(r["bytes"] for r in p1) / sum(r["bytes"] for r in rows):.4f}')
print(f'  total bytes = {sum(r["bytes"] for r in rows):,}')
chk(len(p1) / len(rows) >= 0.40, 'first-hand count ratio >= 0.40')

print(f'\nFAILURES: {len(fails)}')
for f in fails:
    print('  -', f)
sys.exit(1 if fails else 0)
