# -*- coding: utf-8 -*-
r"""
提取 PG 的 178 个战役简报（*.pgbrf），按战役上下文分批，供分组翻译。
- pgbrf 是 UTF-8/ASCII 的 HTML 片段（形如 <p>…</p>）
- 借助 pgcam 的 Campaign path 反查每个简报所属的场景名，便于翻译把握上下文
输出：work\pg\brf\batch1..6.json  [{file, scn, en}]
"""
import json
import os
import re

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario'
OUTDIR = r'D:\DSH\军事游戏汉化\pgforever\work\pg\brf'
os.makedirs(OUTDIR, exist_ok=True)

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith('.pgbrf'))
print('pgbrf 共 %d 个' % len(files))

# 从 pg.pgcam 建立 简报文件 -> 场景名 的映射
cam = open(os.path.join(SRC, 'pg.pgcam'), 'rb').read().decode('utf-16')
scn_of = {}
for line in cam.split('\r\n'):
    if '.pgbrf' not in line:
        continue
    cols = line.split('\t')
    # Campaign path 行：Label | Briefing | Scenario | ... 共 12 列
    if len(cols) >= 12:
        label = cols[0].strip()
        for i in (1, 5, 8, 11):
            if i < len(cols) and cols[i].strip().endswith('.pgbrf'):
                scn_of.setdefault(cols[i].strip(), [])
                if cols[2].strip():
                    scn_of[cols[i].strip()].append(cols[2].strip())

items = []
for f in files:
    raw = open(os.path.join(SRC, f), 'rb').read()
    try:
        t = raw.decode('utf-8')
    except UnicodeDecodeError:
        t = raw.decode('latin-1')
    scns = scn_of.get(f, [])
    items.append({
        'file': f,
        'scn': ' / '.join(sorted(set(scns))) or '?',
        'en': t.strip(),
        'bytes': len(raw),
        'chars': len(t),
    })

total_chars = sum(i['chars'] for i in items)
print('总字符 %d，平均 %.0f' % (total_chars, total_chars / len(items)))

N = 6
per = (len(items) + N - 1) // N
for b in range(N):
    part = items[b*per:(b+1)*per]
    if not part:
        continue
    p = os.path.join(OUTDIR, 'batch%d.json' % (b + 1))
    json.dump(part, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('batch%d: %d 个，%d 字符 -> %s' % (b + 1, len(part), sum(x['chars'] for x in part), p))
