// Split _scn-todo-prose.tsv data rows into fixed-size work chunks.
// Each chunk file: "# chunk <i>/<n> rows <a>-<b>" then lines "<globalIdx>\t<original>"
// ⚠️ 一次性工具（prose 批次）：输入 research/_scn-todo-prose.tsv 已于 2026-10-20 整理时归档。
//    2026-10-20 脚本树合并后本工具迁入 work/pegww2/scn/，但 OUT 仍指向数据原位
//    pegww2/work/scn/chunks/（该目录是「原版英文原文名参照数据」，按 .gitignore 白名单留在 pegww2 侧）。
import fs from 'node:fs';
import path from 'node:path';

const ROOT = 'D:/DSH/军事游戏汉化/pegww2';
const SRC = path.join(ROOT, 'research/_scn-todo-prose.tsv');
const OUT = path.join(ROOT, 'work/scn/chunks');
const SIZE = Number(process.argv[2] || 200);

const raw = fs.readFileSync(SRC, 'utf8');
const lines = raw.split(/\r?\n/);
if (lines[lines.length - 1] === '') lines.pop();
const header = lines.slice(0, 3);
const data = lines.slice(3);

fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const n = Math.ceil(data.length / SIZE);
const manifest = [];
for (let c = 0; c < n; c++) {
  const a = c * SIZE;
  const b = Math.min(data.length, a + SIZE);
  const body = [];
  for (let i = a; i < b; i++) {
    const f = data[i].split('\t');
    body.push(`${i}\t${f[0]}`);
  }
  const file = path.join(OUT, `chunk_${String(c + 1).padStart(2, '0')}.tsv`);
  fs.writeFileSync(file, `# chunk ${c + 1}/${n} rows ${a}-${b - 1} (id<TAB>source)\n` + body.join('\n') + '\n', 'utf8');
  manifest.push({ chunk: c + 1, file: file.replace(/\\/g, '/'), from: a, to: b - 1, rows: b - a });
}
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify({ total: data.length, size: SIZE, chunks: manifest }, null, 1), 'utf8');
console.log(JSON.stringify({ total: data.length, chunks: n, size: SIZE }));
