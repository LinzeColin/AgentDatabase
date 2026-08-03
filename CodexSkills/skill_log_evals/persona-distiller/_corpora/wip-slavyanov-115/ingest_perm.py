#!/usr/bin/env python3
"""Ingest the Slavyanov primary texts transcribed on the Perm 150th-anniversary
   site, retrieved through the Wayback Machine (the live host now redirects to a
   https vhost whose certificate does not match the name)."""
import html, os, re, sys

sys.path.insert(0, '/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-slavyanov-115')
import ingest


def dec(b):
    for enc in ('windows-1251', 'utf-8'):
        try:
            t = b.decode(enc)
            if enc == 'utf-8' and 'Ð' in t[:3000]:
                continue
            return t
        except Exception:
            pass
    return b.decode('utf-8', 'replace')


def to_text(b):
    t = dec(b)
    t = re.sub(r'<script.*?</script>', '', t, flags=re.S | re.I)
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S | re.I)
    t = re.sub(r'<br\s*/?>', '\n', t, flags=re.I)
    t = re.sub(r'</(p|div|tr|h[1-6]|li)>', '\n\n', t, flags=re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = t.replace('\xa0', ' ')
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n[ \t]+', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


BASE = 'https://web.archive.org/web/{ts}id_/http://weld.pfo-perm.ru/Date/{name}.htm'

ITEMS = [
 ('otlivka-1892-ch1-elektroliteinaya-fabrika', 'Otlivka1', '20040511192317',
  'Н. Г. Славянов. «Электрическая отливка металлов. Руководство к установке и практическому применению её» (СПб., 1892), ГЛАВА I. УСТРОЙСТВО ЭЛЕКТРОЛИТЕЙНОЙ ФАБРИКИ.',
  'копия-текст на сайте, посвящённом 150-летию Н. Г. Славянова (Администрация Пермской обл. / Пермский ЦНТИ, 2004); набрано по переизданию Машгиз, Москва, 1954'),
 ('otlivka-1892-ch2-prakticheskie-podrobnosti', 'Otlivka2', '20040511192358',
  'Н. Г. Славянов. «Электрическая отливка металлов» (СПб., 1892), ГЛАВА II. ПРАКТИЧЕСКИЕ ПОДРОБНОСТИ РАБОТЫ С ПОМОЩЬЮ ЭЛЕКТРИЧЕСКОЙ ОТЛИВКИ.',
  'то же издание, глава II — самая длинная глава книги'),
 ('otlivka-1892-ch3-osobye-primeneniya', 'Otlivka3', '20040511192504',
  'Н. Г. Славянов. «Электрическая отливка металлов» (СПб., 1892), ГЛАВА III. ОСОБЫЕ ПРИМЕНЕНИЯ ЭЛЕКТРИЧЕСКОЙ ОТЛИВКИ.',
  'то же издание, глава III'),
 ('otlivka-1892-ch4-koksovye-kvartsevye-plitki', 'Otlivka4', '20040511192539',
  'Н. Г. Славянов. «Электрическая отливка металлов» (СПб., 1892), ГЛАВА IV. ПРИГОТОВЛЕНИЕ КОКСОВЫХ И КВАРЦЕВЫХ ПЛИТОК И СТЕРЖНЕЙ.',
  'то же издание, глава IV'),
 ('privilegiya-1891-otlivka-metallov', 'Svarka2', '20040710215628',
  'Привилегия, выданная из Департамента торговли и мануфактур в 1891 г. горному инженеру надворному советнику Николаю Славянову, на способ и аппараты для электрической отливки металлов (прошение подано 17 марта 1890 г.).',
  'текст привилегии (русский патент) в перепечатке; на сайте помещён отдельной страницей'),
 ('privilegiya-1891-uplotnenie-otlivok', 'Svarka3', '20040711114743',
  'Привилегия, выданная из Департамента торговли и мануфактур в 1891 г. горному инженеру надворному советнику Николаю Славянову, на способ электрического уплотнения металлических отливок (прошение подано 8 августа 1890 г.).',
  'текст второй привилегии в перепечатке'),
 ('doklad-irto-1895-uplotnenie-bolvanok', 'Svarka4', '20040711223430',
  'Н. Г. Славянов. «Об электрическом уплотнении металлических отливок, установленном практически в применении к стальным болванкам». Доклад в Общем собрании членов Императорского Русского технического общества 15 апреля 1895 г.',
  'стенограмма/текст доклада в перепечатке'),
]

for short, name, ts, source, where in ITEMS:
    p = 'perm/%s.html' % name
    if not os.path.exists(p):
        ingest.log('FAIL %s local file missing' % short)
        continue
    txt = to_text(open(p, 'rb').read())
    url = BASE.format(ts=ts, name=name)
    ingest.write(short, txt, source, url, where,
                 'HTML→text (windows-1251 decoded, tags stripped); no OCR involved — the page is a keyed transcription')
    st = ingest.cyrillic_stats(txt)
    ingest.log('   cyr-stats %s %s' % (short, st))
