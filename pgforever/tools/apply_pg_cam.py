# -*- coding: utf-8 -*-
r"""
PG pg.pgcam 汉化。

引用链（务必保持自洽）：
  Campaign path[第3列 场景名] -> Scenarios 段[第1列 Label] -> Scn File(001.pgscn)

因此「显示用的场景名」两处都改、且改成同一个中文值，引用依旧成立。
**内部键一律保留**：小写驼峰 Label（Poland/Warsaw/North_Africa…）、END、
Entry points 第2列（Poland/Barbarossa…）。
Outcomes（MAJOR VICTORY 等）暂保留原文，待实测确认引擎是按位置而非按名匹配后再处理。
"""
import json
import os

SRC_DIR = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario'
DST_DIR = r'D:\PGForever1.021\PG\Scenario'
SCN_TRANS = r'D:\DSH\军事游戏汉化\pgforever\work\pg\scn-trans.json'

# --- 1. 构建「原始大写场景名 -> 中文」映射（来自 pgscn 译表 + 备份原文）---
scn_tr = json.load(open(SCN_TRANS, encoding='utf-8'))
scn_tr.pop('note', None)
name_map = {}
for fn, cfg in scn_tr.items():
    raw = open(os.path.join(SRC_DIR, fn), 'rb').read().decode('utf-16')
    for line in raw.split('\r\n'):
        if line.startswith('Name\t'):
            name_map[line.split('\t', 1)[1].strip()] = cfg['name']
            break
print('场景名映射 %d 条' % len(name_map))

# --- 2. Entry points 显示名与描述 ---
ENTRY_DISPLAY = {
    '1939': '1939',
    '1941 West': '1941 西线',
    '1941 East': '1941 东线',
    '1943 West': '1943 西线',
    '1943 East': '1943 东线',
}
ENTRY_DESC = [
    '德国在欧洲发动一连串闪电战攻势，自波兰开始。',
    '为攫取中东的石油，轴心国挥师横扫北非。',
    '史上规模最大的入侵——轴心国突入苏联。',
    '主力已投入东线，轴心国必须守住欧洲柔软的下腹部。',
    '面对战线过长的苏军，轴心国试图在东线重夺主动权。',
]
entry_idx = 0      # 按 Entry points 段出现顺序依次套用译文（避免长文本当做键时因换行/截断不匹配）

src = os.path.join(SRC_DIR, 'pg.pgcam')
dst = os.path.join(DST_DIR, 'pg.pgcam')
raw = open(src, 'rb').read()
assert raw[:2] == b'\xff\xfe'
text = raw.decode('utf-16')
lines = text.split('\r\n')

n_entry = n_scn = n_path = 0
unmapped = []
for i, line in enumerate(lines):
    if not line.strip() or line.lstrip().startswith('#'):
        continue
    cols = line.split('\t')

    # Campaign path：含 .pgbrf，只译第 3 列（显示场景名）
    if any('.pgbrf' in c for c in cols):
        if len(cols) > 2 and cols[2].strip() and cols[2].strip() in name_map:
            cols[2] = name_map[cols[2].strip()]
            lines[i] = '\t'.join(cols)
            n_path += 1
        elif len(cols) > 2 and cols[2].strip():
            unmapped.append('path L%d: %r' % (i + 1, cols[2]))
        continue

    # Scenarios 段：含 .pgscn，译第 1 列（显示场景名 / Label）
    if any('.pgscn' in c for c in cols):
        if cols[0].strip() in name_map:
            cols[0] = name_map[cols[0].strip()]
            lines[i] = '\t'.join(cols)
            n_scn += 1
        else:
            unmapped.append('scn L%d: %r' % (i + 1, cols[0]))
        continue

    # Entry points：6 列且第 4、5 列为数字（Side / Nation）
    if len(cols) >= 6 and cols[3].strip().isdigit() and cols[4].strip().isdigit():
        if cols[0].strip() in ENTRY_DISPLAY:
            cols[0] = ENTRY_DISPLAY[cols[0].strip()]
        if entry_idx < len(ENTRY_DESC):
            cols[2] = ENTRY_DESC[entry_idx]
        entry_idx += 1
        lines[i] = '\t'.join(cols)
        n_entry += 1
        continue

open(dst, 'wb').write(('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le'))
print('已改：Entry points %d 行，Scenarios %d 行，Campaign path %d 行' % (n_entry, n_scn, n_path))
if unmapped:
    print('!! 未匹配: %d 条' % len(unmapped))
    for u in unmapped[:10]:
        print('   ' + u)

# --- 3. 校验 ---
a = open(src, 'rb').read().decode('utf-16').split('\r\n')
b = open(dst, 'rb').read().decode('utf-16').split('\r\n')
assert len(a) == len(b), '行数变化'
KEEP_TOKENS = ('END',)
bad = 0
for x, y in zip(a, b):
    if x == y:
        continue
    xa, ya = x.split('\t'), y.split('\t')
    # 只允许：Scenarios 第1列、Campaign path 第3列、Entry points 第1/3列 变化
    ok = True
    for j, (p, q) in enumerate(zip(xa, ya)):
        if p == q:
            continue
        if p.strip() in KEEP_TOKENS:
            ok = False
        elif any('.pgscn' in c for c in xa) and j == 0:
            pass
        elif any('.pgbrf' in c for c in xa) and j == 2:
            pass
        elif len(xa) >= 6 and xa[3].strip().isdigit() and j in (0, 2):
            pass
        else:
            ok = False
    if not ok:
        bad += 1
        print('!! 越界改动: %r' % x[:100])
print('校验完成：行数一致，越界改动 %d 处' % bad)

print()
print('=== 抽查 ===')
for idx in (11, 12, 27, 69, 70):
    print('  %3d| %s' % (idx + 1, b[idx][:110]))
