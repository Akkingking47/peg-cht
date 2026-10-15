# -*- coding: utf-8 -*-
r"""
全库 .pgcam 盘点（v2，已修正）。

⚠️ 结构实证结论（2026-09-21，务必遵守）：
  .pgcam 是"按位置解析"的定位格式，**只有 3 类文本会显示给玩家**：
    1. entry_name —— `# Entry points` 段 数据行 col0（战役入口名，如 "North Africa"）
    2. entry_desc —— `# Entry points` 段 数据行 col2（战役简介）
    3. outcome    —— `# Outcomes` 段 每行的 col0（结算名，如 "MAJOR VICTORY"）

  以下**绝对不能译**（引擎内部键 / 文件名）：
    · `# Entry points` col1 (`Label in campaign path`) —— 实证 == `# Campaign path` col0
    · `# Scenarios` col0 (Label) —— 与 `# Campaign path` col0 同一键空间
    · `# Campaign path` 全段 —— 只有 Label / *.pgbrf 文件名 / NextLabel / Prestige
    · 其余所有段（Victory conditions / Deploy hexes 等）

  佐证：exe 内 `outcome %s for scenario %s` / `campaign path label %s` 表明这些名是匹配键；
  `# Campaign path` 段里 NextLabel 列直接就是另一个 Label 名。

输出：work\cam-all\src01.json（去重后）+ paths.json
  paths.json: md5 -> {"kind":.., "locs":[[rel, line_idx, col], ...]}
"""
import os, re, glob, json, hashlib

ROOT = r'D:\PGForever1.021'
WORK = r'D:\DSH\军事游戏汉化\pgforever\work\cam-all'
os.makedirs(WORK, exist_ok=True)

CJK = re.compile(r'[\u4e00-\u9fff]')


def sections(lines):
    """按空行切段 → [(start, end, title)]"""
    out, a = [], None
    for i, l in enumerate(lines):
        if l.strip() == '':
            if a is not None:
                out.append((a, i, lines[a].strip()))
                a = None
        elif a is None:
            a = i
    if a is not None:
        out.append((a, len(lines), lines[a].strip()))
    return out


files = sorted(glob.glob(os.path.join(ROOT, '**', '*.pgcam'), recursive=True))
print('共 %d 个 .pgcam' % len(files))

items = []          # (kind, text)
locmap = {}         # (kind,text) -> [[rel,line,col],...]
nfile = 0

for path in files:
    rel = os.path.relpath(path, ROOT)
    try:
        raw = open(path, 'rb').read()
        text = raw.decode('utf-16')
    except Exception as e:
        print('!! 跳过', rel, e)
        continue
    lines = text.split('\r\n')
    nfile += 1

    entry = outcomes = None
    for (a, b, ti) in sections(lines):
        if ti.startswith('# Entry points'):
            entry = (a, b)
        elif ti.startswith('# Outcomes'):
            outcomes = (a, b)

    # --- Entry points：col0 = Name, col2 = Description ---
    if entry:
        for k in range(entry[0], entry[1]):
            ln = lines[k]
            if ln.startswith('#'):
                continue
            c = ln.split('\t')
            for col in (0, 2):
                if col < len(c):
                    v = c[col].strip()
                    if v and not CJK.search(v):
                        kind = 'entry_name' if col == 0 else 'entry_desc'
                        items.append((kind, v))
                        locmap.setdefault((kind, v), []).append([rel, k, col])

    # --- Outcomes：每行 col0 ---
    if outcomes:
        for k in range(outcomes[0], outcomes[1]):
            ln = lines[k]
            if ln.startswith('#'):
                continue
            c = ln.split('\t')
            if c and c[0].strip():
                v = c[0].strip()
                if not CJK.search(v):
                    items.append(('outcome', v))
                    locmap.setdefault(('outcome', v), []).append([rel, k, 0])

print('可译条目共 %d 条' % len(items))

# 去重
uniq = {}
for kind, t in items:
    uniq[(kind, t)] = uniq.get((kind, t), 0) + 1

recs = []
for (kind, t), n in sorted(uniq.items(), key=lambda x: (x[0][0], -x[1])):
    md5 = hashlib.md5((kind + '\x00' + t).encode('utf-8')).hexdigest()
    recs.append({
        'id': md5[:10], 'md5': md5, 'kind': kind,
        'text': t, 'n': n,
    })

print('去重后唯一条目 %d 条' % len(recs))
from collections import Counter
cc = Counter(r['kind'] for r in recs)
print('  ' + ' / '.join('%s %d' % (k, v) for k, v in cc.items()))

json.dump(recs, open(os.path.join(WORK, 'src01.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

pmap = {}
for r in recs:
    locs = locmap[(r['kind'], r['text'])]
    pmap[r['md5']] = {'kind': r['kind'], 'locs': locs}
json.dump(pmap, open(os.path.join(WORK, 'paths.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('→ src01.json（%d 条）, paths.json（%d 组）' % (len(recs), len(pmap)))

print('\n=== 样本 ===')
for r in recs[:12]:
    print('  [%s] %r ×%d' % (r['kind'], r['text'][:80], r['n']))
