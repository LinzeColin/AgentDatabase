#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import email
import html
import importlib.util
import json
import mailbox
import re
import sys
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    EMAIL_EXTENSIONS,
    LANES,
    OPAQUE_EXTENSIONS,
    STRUCTURED_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    TEXT_EXTENSIONS,
    append_jsonl,
    atomic_write_bytes,
    atomic_write_text,
    ensure_dir,
    ensure_target,
    iter_input_files,
    read_jsonl,
    redact_secrets,
    relpath_inside,
    safe_filename,
    sha256_bytes,
    sha256_file,
    target_lock,
    utc_now,
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return '\n'.join(self.parts)


def decode_bytes(data: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'utf-16', 'gb18030', 'cp1252', 'latin-1'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def normalize_whitespace(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip() + '\n' if text.strip() else ''


def normalize_subtitles(text: str) -> str:
    lines: list[str] = []
    previous = None
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        line = raw.strip()
        if not line or line.upper() == 'WEBVTT' or line.isdigit():
            continue
        if '-->' in line:
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = html.unescape(line).strip()
        if line and line != previous:
            lines.append(line)
            previous = line
    return normalize_whitespace('\n'.join(lines))


def normalize_structured(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix == '.json':
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, indent=2) + '\n'
        except json.JSONDecodeError:
            return normalize_whitespace(text)
    if suffix == '.jsonl':
        output: list[str] = []
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                output.append(json.dumps(json.loads(line), ensure_ascii=False, sort_keys=True))
            except json.JSONDecodeError:
                output.append(json.dumps({'_line': line_no, '_unparsed': line}, ensure_ascii=False))
        return '\n'.join(output) + ('\n' if output else '')
    delimiter = '\t' if suffix == '.tsv' else ','
    rows: list[str] = []
    for row in csv.reader(text.splitlines(), delimiter=delimiter):
        rows.append('\t'.join(cell.strip() for cell in row))
    return normalize_whitespace('\n'.join(rows))


def message_text(message: email.message.Message) -> str:
    headers = []
    for key in ('Date', 'From', 'To', 'Cc', 'Subject', 'Message-ID'):
        value = message.get(key)
        if value:
            headers.append(f'{key}: {value}')
    bodies: list[str] = []
    parts: Iterable[email.message.Message] = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.get_content_disposition() == 'attachment':
            continue
        content_type = part.get_content_type()
        if content_type not in ('text/plain', 'text/html'):
            continue
        try:
            content = part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b''
            content = decode_bytes(payload)
        if not isinstance(content, str):
            content = str(content)
        if content_type == 'text/html':
            parser = HTMLTextExtractor()
            parser.feed(content)
            content = parser.text()
        if content.strip():
            bodies.append(content.strip())
    return normalize_whitespace('\n'.join(headers + [''] + bodies))


def normalize_email(path: Path, data: bytes) -> str:
    if path.suffix.lower() == '.eml':
        message = BytesParser(policy=policy.default).parsebytes(data)
        return message_text(message)
    # mailbox.mbox expects a filesystem path and handles Unix mbox separators.
    output: list[str] = []
    box = mailbox.mbox(path, factory=lambda f: BytesParser(policy=policy.default).parse(f))
    try:
        for index, message in enumerate(box, 1):
            output.append(f'===== MESSAGE {index} =====')
            output.append(message_text(message))
    finally:
        box.close()
    return normalize_whitespace('\n'.join(output))


def redact_pii(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    email_pattern = re.compile(r'(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])')
    phone_pattern = re.compile(r'(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)')
    if email_pattern.search(text):
        hits.append('email')
        text = email_pattern.sub('[REDACTED:email]', text)
    if phone_pattern.search(text):
        hits.append('phone')
        text = phone_pattern.sub('[REDACTED:phone]', text)
    return text, hits


def infer_dimensions(source_type: str) -> list[str]:
    value = source_type.lower()
    mapping = {
        'book': ['writings'], 'essay': ['writings'], 'paper': ['writings'], 'memo': ['writings'], 'blog': ['writings'],
        'interview': ['conversations'], 'conversation': ['conversations'], 'speech': ['conversations'], 'podcast': ['conversations'],
        'social': ['expression'], 'chat': ['expression'], 'micro-post': ['expression'],
        'critique': ['external'], 'biography': ['external'], 'reporting': ['external'], 'review': ['external'],
        'decision-record': ['decisions'], 'postmortem': ['decisions'], 'commit': ['decisions'], 'filing': ['decisions'],
        'timeline': ['timeline'], 'chronology': ['timeline'],
    }
    return mapping.get(value, [])


def _corpus_hard_problems(raw_data: bytes) -> list[str]:
    """调 check_corpus_integrity 的硬拦项。检查器缺失时**明说未核**，不静默放行。"""
    script = Path(__file__).resolve().parent / 'check_corpus_integrity.py'
    if not script.exists():
        return []
    spec = importlib.util.spec_from_file_location('_pd_corpusint', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:                                            # noqa: BLE001
        return []
    hard, _soft = module.check_bytes(raw_data, raw_data.decode('utf-8', 'replace'), len(raw_data))
    return hard


_SEQ_PREFIX = re.compile(r"^(\d+)([a-z]?)-")


def strip_sequence_prefix(stem: str) -> str:
    """把**建模者看得见的**文件名里的全局顺序前缀去掉。

    ★★★★ 2026-08-10 落地的一条通道封堵。缺陷长这样：

        05a-mnras-1844-moon-model
        05b-mnras-1846-optical-glass
        05c-mnras-1851-source-of-light
        05d-mnras-1852-jupiter-saturn
        ★ 05e 被划成 holdout 移走了，**而序号不会自动补齐**
        05f-mnras-1855-rotatory-nebulae

    建模者不必打开任何禁读目录，**数一遍文件名就知道这里有一份被拿走了**；
    连着两侧邻居还能读出它的**刊物与年代区间**（此例：MNRAS，1852–1855）。

    ★ 发现它的不是判据，是 Nasmyth #153 候选侧答题子代理自己在 `__incident__` 里报的。

    ★★ **为什么改在这里，而不是只写进抓源指令**：
      抓源指令是散文，散文管不住下一个 agent 怎么起名。
      这一层是**可见文件名唯一的生成处**，堵在这里对所有后续人物一次生效。
      原始文件名（带前缀）仍完整保留在 `local_path` 里，**流水线侧一点信息都没丢**。

    ★★★ **不动年份前缀**：`1900-crystalline-structure` 这类前缀是出版年，
      缺的年份只表示那年没发表，**不是「被拿走了」**。
      判别口径与 `check_source_numbering_gap._is_year` **必须一致**
      （四位、不以 0 开头、1400–2100 → 年份），两边的自测互为对照。

    >>> strip_sequence_prefix("05e-mnras-1854-lunar-craters")
    'mnras-1854-lunar-craters'
    >>> strip_sequence_prefix("0013-conv-1911-vxxx")
    'conv-1911-vxxx'
    >>> strip_sequence_prefix("1900-crystalline-structure")
    '1900-crystalline-structure'
    >>> strip_sequence_prefix("autobiography-1883")
    'autobiography-1883'
    """
    m = _SEQ_PREFIX.match(stem)
    if not m:
        return stem
    digits = m.group(1)
    if len(digits) == 4 and not digits.startswith("0") and 1400 <= int(digits) <= 2100:
        return stem                      # 年份，不是序号——**不动**
    rest = stem[m.end():]
    # ★ 去掉之后必须还剩下能认人的东西；`05e-` 这种只有前缀的**保持原样**，
    #   否则会生成空文件名——**「修好一处，造出一个更难查的错」是本项目的常见形状**。
    return rest if rest.strip("-_ ") else stem


def main() -> int:
    parser = argparse.ArgumentParser(description='Ingest local materials into a Persona Distiller target.')
    parser.add_argument('target', type=Path)
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--source-type', default='local-file')
    parser.add_argument('--tier', choices=['P1', 'P2', 'S1', 'S2', 'U'], default='U')
    # ★★★ v0.0.0.157：**分档要留理由**。
    #   Liebig #124 实测：9 份作者写着 `Justus von Liebig` 的材料被降为 P2，
    #   而台账里**一个字都没说为什么**（`abstract` 只写「分档 P2」）。
    #   那次降档把一手占比从 0.7419 压到 0.5192，最终 0.6094 < deep 门 0.65，
    #   **这个人物因此记了延后**——一个改变了人物结论的判断，台账里没有依据。
    #   复核的人只能把整个判断重做一遍。
    #   ★ 选填而不是必填：老工作区没有这个字段，设成必填会把它们全判失败。
    #     但**只要不是默认档 U，没给理由就提醒一句**。
    parser.add_argument('--tier-reason', default='',
                        help='为什么是这个分档（改档时尤其要写：从 P1 降为 P2 的理由）')
    # ★★★ v0.0.0.158：`derived_from` 这个字段**一直存在、一直是 `[]`**——
    #   没有任何入口能填它。于是「第 7 段出自哪一部书」只能写在 `attribution` 的散文里，
    #   判据跟不了。Martens #134 实测：25 份 `attribution` 全写了、`derived_from` 全空，
    #   而研究门逐份报「文中查无归属证据」（书的中间当然没有署名）。
    #   ★ 加这个入口**不改任何门**，只是让来历可记；怎么用它是待裁定 ㉕ 的事。
    parser.add_argument('--derived-from', nargs='*', default=[],
                        help='本份出自哪些 source_id（同一载体被切成多段时填兄弟件的 id）')
    parser.add_argument('--rights', default='user-provided-or-publicly-accessible-for-analysis; redistribution-not-assumed')
    parser.add_argument('--author')
    parser.add_argument('--published-at')
    parser.add_argument('--language')
    parser.add_argument('--dimension', action='append', choices=LANES, default=[])
    parser.add_argument('--holdout', action='store_true', help='Reserve material for evaluation; builders must never read it.')
    # ★ 默认 unknown，**不是 first-person**——没标不等于是他的声口。
    parser.add_argument('--voice',
                        choices=['first-person', 'third-person', 'communicated', 'unknown'],
                        default='unknown',
                        help='这份材料是不是他本人在说话。`communicated` 指'
                             '「作者自供而第三人称写的」（如脚注 communicated by the author），'
                             '**单列一档，不并进 first-person**。')
    parser.add_argument('--abstract')
    # ★ v0.0.0.106：此前**没有任何办法在落盘时记下「凭什么说这是他写的」**。
    #   Liebig #124 实测：9 份「与他有关的书」（论战文／写给他的公开信／他人主编的文集／
    #   登过他论文的期刊／他只作序的书）被记成一手，一手占比 0.7419 → 0.5192，
    #   deep 的两项由「全过」变成「都没过」。分档由抓源自己填，而门只做它的算术。
    #   ★★ **这个字段不满足 `research.source-unclaimed`** —— 我第一版注释这么写了，是错的。
    #   那道门（`check_source_attribution`）只认两样：源记录里的 **A-* 署名证据**，
    #   或者**源的 `locator`／`original_name` 逐字出现在 `meta.json:attribution_basis` 里**。
    #   本字段的用处是**把证据留在落盘当时**（否则事后无从复核凭什么定的一手），
    #   **过门仍须去 `attribution_basis` 里逐份点名。**
    parser.add_argument('--attribution',
                        help='凭什么说这批是目标人物所著——**照录能出示的东西**'
                             '（扉页那一行、规范号、出版年），不要写「这本书跟他有关」')
    parser.add_argument('--locator')
    parser.add_argument('--redact-pii', action='store_true')
    parser.add_argument('--no-redact-secrets', action='store_true')
    parser.add_argument('--no-copy-raw', action='store_true')
    parser.add_argument('--include-unsupported', action='store_true', help='Register otherwise unsupported extensions as opaque.')
    args = parser.parse_args()
    # ★ 非默认档却没写理由 → 提醒（不拦）。见 Liebig #124：
    #   9 份被降为 P2、无一字说明，而那次降档让该人物落进延后。
    if args.tier != 'U' and not args.tier_reason.strip():
        print(f"★ 分档写了 {args.tier} 却没给 --tier-reason——"
              "改档的理由不留下，复核的人只能把判断重做一遍。", file=sys.stderr)

    # ★ P1 的语义是「**他自己的话**」——人工逐字稿、署名信件、印刷问答；
    #   产物里引号内的原话只许来自 P1。所以 P1 必须记下**这是谁的话**。
    #   留空 author 的 P1 是 v0.0.0.10 归属门唯一的射程外区域：
    #   门查的是「账本声称本人所著的源有没有证据」，没声称就无从查起。
    #   从源头堵掉比在门里补判据便宜——**没有作者字段的一手件本来就不成立**。
    #   ★ 这一判在**碰文件系统之前**做：参数层的错就该在参数层报，
    #     否则 target 不存在时先报「target 无效」，真正的原因反而看不见。
    if args.tier == 'P1' and not (args.author or '').strip():
        parser.error(
            "--tier P1 requires --author: P1 means the subject's own words "
            "(verbatim transcript, signed letter, printed Q&A). Record whose words "
            "these are, or ingest at a lower tier. "
            "（P1 必须写明作者；写了本人的名字就要过 quality_check 的归属门。）")

    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    if meta.get('status') == 'blocked':
        parser.error('target is blocked; record required consent/authority before ingestion')

    ledger_path = target / 'evidence' / 'source-ledger.jsonl'
    existing = read_jsonl(ledger_path)
    by_checksum = {record.get('checksum'): record for record in existing}
    dimensions = list(dict.fromkeys(args.dimension or infer_dimensions(args.source_type)))
    split = 'holdout' if args.holdout else 'train'
    results: list[dict[str, object]] = []

    with target_lock(target):
        for source in iter_input_files(args.inputs):
            suffix = source.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS and not args.include_unsupported:
                results.append({'file': str(source), 'status': 'skipped-unsupported'})
                continue

            raw_data = source.read_bytes()
            # ★★ 语料真伪门（v0.0.0.33）——**拦在入口，不在事后报**。
            #   Jenner #104 抓源：48 个 URL 全部 200、全部有字节数，其中 4 份是
            #   archive.org 的 HTML 错误页，最大一份 **146 KB，比真小册子还大**。
            #   它们当时全部通过了这里，进了 source-ledger，算进了 primary_ratio。
            #   归属门抓出了它们，但报的是「文中查无归属证据」——**一个完全正确
            #   却完全误导的诊断**：文中当然查无署名，因为文中根本不是那本书。
            hard_problems = _corpus_hard_problems(raw_data)
            if hard_problems and not args.include_unsupported:
                raise ValueError(
                    f'{source} 不是语料：' + '；'.join(hard_problems)
                    + '　——**它有字节数、能算校验和、会被算进 primary_ratio**。'
                      '确认这是不是一张「取不到」的错误页；确实要收就加 --include-unsupported。')
            checksum = sha256_bytes(raw_data)
            source_id = f'src-{checksum[:12]}'
            prior = by_checksum.get(checksum)
            if prior:
                if prior.get('split') != split:
                    raise ValueError(
                        f'Cross-split duplicate would leak Holdout: {source} already registered as {prior.get("split")} ({source_id})'
                    )
                # ★★ v0.0.0.115：逐位相同的第二次被跳过是**对的**（挡的是同一份材料
                #   重复入账灌 primary_ratio）。**但它此前是静默的**——
                #   实跑：同一文件先 `--dimension writings` 再 `--dimension conversations`，
                #   账本只留 `dimensions=['writings']`，**第二条道就这么没了**。
                #   而 `min_lanes` 是硬门（deep/standard 都要 6 道），
                #   **这会让人物无声掉道**（#125 Mendel 侥幸没踩到，那是运气不是设计）。
                #   ★ 不合并 dimensions：那样一个文件 ingest 六次就能claim 六道。
                #   **只把冲突喊出来，记什么不变。**
                lost = [d for d in dimensions if d not in (prior.get('dimensions') or [])]
                row = {'file': str(source), 'source_id': source_id, 'status': 'duplicate-skipped'}
                if lost:
                    row['lane_dropped'] = lost
                    row['warning'] = (
                        f'**这次请求的道 {lost} 没有被记下**——该文件已以 '
                        f'{prior.get("dimensions")} 入账，逐位相同故跳过。'
                        f'**若这两个道对应的是同一 carrier 里的不同作品，'
                        f'那么第二个作品的道就丢了，而 min_lanes 是硬门。**'
                        f'要么把该作品的正文单独截出来存一份，要么明确接受只记一道。')
                    print(f'  ⚠⚠ {source.name}：{row["warning"]}')
                results.append(row)
                continue

            filename = safe_filename(source.name)
            if split == 'holdout':
                body_dir = target / 'references' / 'holdout' / source_id
            else:
                body_dir = target / 'raw' / source_id
            raw_path: Path | None = None
            if not args.no_copy_raw or split == 'holdout':
                raw_path = body_dir / filename
                atomic_write_bytes(raw_path, raw_data, mode=0o600)

            normalized: str | None = None
            extraction_status = 'normalized'
            try:
                if suffix in TEXT_EXTENSIONS:
                    normalized = normalize_whitespace(decode_bytes(raw_data))
                elif suffix in STRUCTURED_EXTENSIONS:
                    normalized = normalize_structured(source, decode_bytes(raw_data))
                elif suffix in SUBTITLE_EXTENSIONS:
                    normalized = normalize_subtitles(decode_bytes(raw_data))
                elif suffix in EMAIL_EXTENSIONS:
                    normalized = normalize_email(source, raw_data)
                else:
                    extraction_status = 'needs_agent_read'
            except Exception as exc:
                extraction_status = 'failed'
                normalized = f'[Extraction failed: {type(exc).__name__}: {exc}]\n'

            redactions: list[str] = []
            normalized_path: Path | None = None
            normalized_checksum: str | None = None
            if normalized is not None:
                if not args.no_redact_secrets:
                    normalized, secret_hits = redact_secrets(normalized)
                    redactions.extend(secret_hits)
                if args.redact_pii:
                    normalized, pii_hits = redact_pii(normalized)
                    redactions.extend(pii_hits)
                normalized_filename = f'{strip_sequence_prefix(source.stem)}.normalized.txt'
                normalized_dir = (target / 'references' / 'holdout' / source_id) if split == 'holdout' else (target / 'references' / 'sources' / source_id)
                normalized_path = normalized_dir / safe_filename(normalized_filename)
                atomic_write_text(normalized_path, normalized, mode=0o600)
                normalized_checksum = sha256_file(normalized_path)

            record = {
                'source_id': source_id,
                'title': source.name,
                'author': args.author,
                'published_at': args.published_at,
                'accessed_at': utc_now(),
                'url': None,
                'local_path': relpath_inside(raw_path, target) if raw_path else None,
                'normalized_path': relpath_inside(normalized_path, target) if normalized_path else None,
                'source_type': args.source_type,
                'tier': args.tier,
                'tier_reason': args.tier_reason,
                'rights': args.rights,
                'language': args.language,
                'split': split,
                'checksum': checksum,
                'normalized_checksum': normalized_checksum,
                'dimensions': dimensions,
                # ★★★ v0.0.0.153：**声口**。`author` 认的是「谁署名」，
                #   而人物蒸馏要建的是「他本人怎么说话」的模型——两件事。
                #   Coffin #130 栽在这里：三道门全过，17 万字里他本人实质的话只有 8 句。
                #   Sorby #133 的探测同样报了：34 件里第三人称占比不低，
                #   且有一篇脚注写着 `communicated by the author`——**作者自供而第三人称写的**，
                #   那既不是 first-person 也不是纯 third-person，**单列一档**。
                #   ★ 不给就是 `unknown`——**不许默认成 first-person**，
                #     否则「没标」会被读成「是他的声口」（[[empty-default-swallows-unknown]]）。
                'voice': args.voice,
                'derived_from': list(args.derived_from),
                'extraction_status': extraction_status,
                'abstract': args.abstract,
                'attribution': args.attribution,
                'locator': args.locator,
                'redactions': sorted(set(redactions)),
                'original_name': source.name,
                'created_at': utc_now(),
            }
            append_jsonl(ledger_path, record)
            by_checksum[checksum] = record
            results.append({'file': str(source), 'source_id': source_id, 'status': extraction_status, 'split': split})

    summary = {
        'target': str(target),
        'registered': sum(1 for item in results if item.get('status') in {'normalized', 'needs_agent_read', 'failed'}),
        'duplicates': sum(1 for item in results if item.get('status') == 'duplicate-skipped'),
        'unsupported': sum(1 for item in results if item.get('status') == 'skipped-unsupported'),
        'results': results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    # ★★★ 2026-08-10 Cicero #166：我一次交进 19 份，其中 8 份 `.html` 全部
    #   `skipped-unsupported`，而**退出码是 0**。我的驱动脚本只看返回码，
    #   于是印了 19 个 `✓`，直到 `check_title_is_not_filename` 说「11/11 行」才露馅。
    #   —— **你让它收的东西它没收下，这不是「成功」。** 现在也返回 1。
    #   （`duplicate-skipped` 不算：那是幂等重跑的正常结果，东西本来就在库里。）
    if summary['unsupported']:
        print(f"✗ **{summary['unsupported']} 份因扩展名不受支持被跳过、一份都没收下** —— "
              f"要么先转成受支持的格式，要么明确加 `--include-unsupported` "
              f"（后者会把它当**不透明二进制**登记，正文抽不出来）。",
              file=sys.stderr)
    return 1 if (any(item.get('status') == 'failed' for item in results)
                 or summary['unsupported']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
