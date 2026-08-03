#!/usr/bin/env python3
"""Corpus ingest helper for #115 Nikolai Slavyanov.

Every write goes through here so that (a) the 5-line provenance header is
identical across files and (b) raw/_fetch.log gets one line per attempt,
success or failure.  Nothing here invents metadata: `source`, `where` and
`url` are passed in by the caller after the document has actually been read.
"""
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'raw')
LOG = os.path.join(RAW, '_fetch.log')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
TODAY = '2026-08-04'

os.makedirs(RAW, exist_ok=True)


def log(line):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')
    print(line, file=sys.stderr)


def fetch(url, timeout=120, binary=False):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
    b = r.read()
    return b if binary else b.decode('utf-8', 'replace')


def write(short, text, source, url, where, extraction):
    """Write raw/<short>/<short>.txt with the standard 5-line header."""
    d = os.path.join(RAW, short)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, short + '.txt')
    head = (
        f'# SOURCE: {source}\n'
        f'# where: {where}\n'
        f'# URL: {url}\n'
        f'# retrieved: {TODAY}\n'
        f'# extraction: {extraction}\n'
        '\n' + '=' * 70 + '\n\n'
    )
    with open(p, 'w', encoding='utf-8') as f:
        f.write(head + text)
    n = len(text)
    log(f'OK {short} chars={n} url={url}')
    return n


def cyrillic_stats(text):
    """Homoglyph tripwire: count Cyrillic chars sitting inside Latin words."""
    cyr = len(re.findall(r'[Ѐ-ӿ]', text))
    lat = len(re.findall(r'[A-Za-z]', text))
    mixed = len(re.findall(r'\b(?=[A-Za-z]*[Ѐ-ӿ])(?=[Ѐ-ӿ]*[A-Za-z])'
                          r'[A-Za-zЀ-ӿ]{2,}\b', text))
    return {'cyrillic': cyr, 'latin': lat, 'mixed_script_words': mixed}


if __name__ == '__main__':
    print(__doc__)
