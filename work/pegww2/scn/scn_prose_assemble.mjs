// Assemble final _scn-fill-prose.tsv from per-chunk output files, then self-check.
// usage: node scn_prose_assemble.mjs <outfile> <chunkOut1> [<chunkOut2> ...]
// ⚠️ 一次性工具（prose 批次）：输入 research/_scn-todo-prose.tsv 已于 2026-10-20 整理时归档；
//    原 chunk 输出目录 pegww2/work/scn/out/（gitignore 派生物）已删除。
//    2026-10-20 脚本树合并后本工具迁入 work/pegww2/scn/；chunk 参数按需传绝对路径。
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const ROOT = 'D:/DSH/军事游戏汉化/pegww2';
const SRC = path.join(ROOT, 'research/_scn-todo-prose.tsv');

const [outArg, ...chunkArgs] = process.argv.slice(2);
if (!outArg || chunkArgs.length === 0) {
  console.error('usage: node scn_prose_assemble.mjs <outfile> <chunkOut...>');
  process.exit(2);
}
const outFile = path.isAbsolute(outArg) ? outArg : path.join(ROOT, outArg);

const lines = fs.readFileSync(SRC, 'utf8').split(/\r?\n/);
if (lines[lines.length - 1] === '') lines.pop();
const data = lines.slice(3).map((l) => {
  const f = l.split('\t');
  return { src: f[0], n: f.length };
});

const map = new Map();
const errors = [];
for (const a of chunkArgs) {
  const p = path.isAbsolute(a) ? a : path.join(ROOT, a);
  const raw = fs.readFileSync(p, 'utf8');
  if (raw.charCodeAt(0) === 0xfeff) errors.push(`${path.basename(p)}: has BOM`);
  const cl = raw.split(/\r?\n/);
  if (cl[cl.length - 1] === '') cl.pop();
  let n = 0;
  for (const line of cl) {
    if (line === '') continue;
    if (line.startsWith('#')) continue;
    const tab = line.indexOf('\t');
    if (tab < 0) { errors.push(`${path.basename(p)}: no TAB in "${line.slice(0, 60)}"`); continue; }
    const id = Number(line.slice(0, tab));
    const zh = line.slice(tab + 1);
    if (!Number.isInteger(id) || id < 0 || id >= data.length) { errors.push(`${path.basename(p)}: bad id ${line.slice(0, 20)}`); continue; }
    if (/[\r\n\t]/.test(zh)) { errors.push(`${path.basename(p)}: id ${id} translation contains TAB/CR/LF`); continue; }
    if (zh.trim() === '') { errors.push(`${path.basename(p)}: id ${id} empty translation`); continue; }
    if (map.has(id)) { errors.push(`${path.basename(p)}: duplicate id ${id}`); continue; }
    map.set(id, zh);
    n++;
  }
  console.log(`${path.basename(p)}: ${n} rows`);
}

const missing = [];
const out = [];
for (let i = 0; i < data.length; i++) {
  if (!map.has(i)) { missing.push(i); out.push(`${data[i].src}\t`); continue; }
  const src = data[i].src;
  const zh = map.get(i);
  const esc = src.match(/\\x[0-9A-Fa-f]{2}/g) || [];
  const missingEsc = esc.filter((e) => !zh.includes(e));
  if (missingEsc.length) errors.push(`id ${i}: translation lost escape ${[...new Set(missingEsc)].join(',')}`);
  out.push(`${src}\t${zh}`);
}

const text = out.join('\n') + '\n';
fs.writeFileSync(outFile, Buffer.from(text, 'utf8'));

const buf = fs.readFileSync(outFile);
const sha = crypto.createHash('sha256').update(buf).digest('hex');
const badField = out.filter((l) => l.split('\t').length !== 2).length;
const empty = out.filter((l) => l.slice(l.indexOf('\t') + 1).trim() === '').length;

console.log('--- self check ---');
console.log(`input rows        : ${data.length}`);
console.log(`filled rows       : ${map.size}`);
console.log(`missing ids       : ${missing.length}${missing.length ? ' -> ' + missing.slice(0, 40).join(',') : ''}`);
console.log(`output lines      : ${out.length}`);
console.log(`field != 2        : ${badField}`);
console.log(`empty translations: ${empty}`);
console.log(`BOM               : ${buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf}`);
console.log(`bytes             : ${buf.length}`);
console.log(`sha256            : ${sha}`);
console.log(`first col identical to input (all rows): ${out.every((l, i) => l.slice(0, l.indexOf('\t')) === data[i].src)}`);
console.log(`errors            : ${errors.length}`);
for (const e of errors.slice(0, 60)) console.log('  ! ' + e);
