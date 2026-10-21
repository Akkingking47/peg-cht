// Extract selected source rows by global id into a work batch file.
// usage: node scn_prose_make.mjs <name> <id> [<id> ...]
// ⚠️ 一次性工具（prose 批次）：输入 research/_scn-todo-prose.tsv 已于 2026-10-20 整理时归档，
//    如需复跑请先恢复该输入。2026-10-20 脚本树合并：本工具与产出同驻 work/pegww2/scn/。
import fs from 'node:fs';
import path from 'node:path';

const ROOT = 'D:/DSH/军事游戏汉化/pegww2';
const SRC = path.join(ROOT, 'research/_scn-todo-prose.tsv');
const OUT = 'D:/DSH/军事游戏汉化/work/pegww2/scn';

const [name, ...idsRaw] = process.argv.slice(2);
if (!name || idsRaw.length === 0) {
  console.error('usage: node scn_prose_make.mjs <name> <id> [<id>...]');
  process.exit(2);
}

const lines = fs.readFileSync(SRC, 'utf8').split(/\r?\n/);
if (lines[lines.length - 1] === '') lines.pop();
const data = lines.slice(3);

const ids = idsRaw.map(Number);
const body = ids.map((i) => {
  if (!Number.isInteger(i) || i < 0 || i >= data.length) throw new Error(`bad id ${i}`);
  return `${i}\t${data[i].split('\t')[0]}`;
});

fs.mkdirSync(OUT, { recursive: true });
const file = path.join(OUT, `${name}_src.tsv`);
fs.writeFileSync(file, '# id<TAB>source\n' + body.join('\n') + '\n', 'utf8');
console.log(JSON.stringify({ name, rows: ids.length, file: file.replace(/\\/g, '/'), ids }));
