// dsh_reduce.js —— 把 DSH 的 session.jsonl.zstd 归约成一行 JSON。
//
// 两个必须知道的事实：
// 1. DSH 把**每一行当成独立的 zstd 帧**追加，一个文件里能有上千帧。
//    zstdDecompressSync 只解第一帧 —— 照着它拿，每个会话只会得到那条 session
//    元数据（273 字节），正文一行都读不到。实测就是这么错的。
//    所以要按魔数 0xFD2FB528 切帧逐个解。
// 2. 一次 node 进程处理全部文件。1937 个文件各起一个进程要几分钟，
//    批处理只要一次启动开销。
const { readFileSync } = require('fs');
const zlib = require('zlib');

const MAGIC = 0xFD2FB528;
function decodeAll(buf) {
  const offs = [];
  for (let i = 0; i + 4 <= buf.length; i++) if (buf.readUInt32LE(i) === MAGIC) offs.push(i);
  if (!offs.length) return '';
  let out = '';
  for (let k = 0; k < offs.length; k++) {
    const a = offs[k], b = (k + 1 < offs.length) ? offs[k + 1] : buf.length;
    try { out += zlib.zstdDecompressSync(buf.subarray(a, b)).toString('utf8'); } catch (e) { /* 坏帧跳过 */ }
  }
  return out;
}

const textOf = c => Array.isArray(c)
  ? c.filter(x => x && x.type === 'text' && typeof x.text === 'string').map(x => x.text).join('\n')
  : (typeof c === 'string' ? c : '');

const files = process.argv.slice(2);
for (const f of files) {
  const rec = { path: f, ok: false, prompts: [], msgs: 0, tools: 0, toolNames: {},
                title: '', provider: '', model: '', cwd: '', origin: '', preset: '',
                first: 0, last: 0, lines: 0, turns: 0 };
  try {
    const text = decodeAll(readFileSync(f));
    for (const line of text.split('\n')) {
      if (!line) continue;
      let d; try { d = JSON.parse(line); } catch (e) { continue; }
      rec.lines++;
      const t = d.time || d.time0 || d.createdAt;
      if (typeof t === 'number') {
        if (!rec.first || t < rec.first) rec.first = t;
        if (t > rec.last) rec.last = t;
      }
      const D = d.data || {};
      switch (d.type) {
        case 'session':
          rec.cwd = d.cwd || ''; rec.origin = d.origin || '';
          rec.preset = d.agentPreset || '';
          if (d.createdAt) { if (!rec.first || d.createdAt < rec.first) rec.first = d.createdAt; }
          break;
        case 'session/title': if (D.title) rec.title = String(D.title).slice(0, 160); break;
        case 'request/header': {
          const c = (D.header || {}).config || {};
          if (c.provider) rec.provider = String(c.provider);
          if (c.model) rec.model = String(c.model);
          break;
        }
        case 'user/message': {
          const s = textOf(D.content);
          rec.turns++;
          if (s && rec.prompts.length < 12) rec.prompts.push(s.slice(0, 1200));
          break;
        }
        case 'assistant/message': rec.msgs++; break;
        case 'tool/call':
          rec.tools++;
          if (D.name) rec.toolNames[String(D.name).slice(0, 40)] = (rec.toolNames[String(D.name).slice(0, 40)] || 0) + 1;
          break;
        case 'tool/code-dispatch':
          if (D.name) rec.toolNames[String(D.name).slice(0, 40)] = (rec.toolNames[String(D.name).slice(0, 40)] || 0) + 1;
          break;
      }
    }
    rec.ok = rec.lines > 0;
  } catch (e) { rec.err = String(e.message || e).slice(0, 120); }
  process.stdout.write(JSON.stringify(rec) + '\n');
}
