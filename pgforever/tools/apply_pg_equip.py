# -*- coding: utf-8 -*-
r"""
PG equipment.pgeqp 单位名汉化：
- 源文件 UTF-16LE(BOM) + TAB 分隔，第 2 列是 Name
- 只改 Name 列，其余列（数值）原样不动
- 词级替换：按词长降序 + 词边界保护
- 输出仍为 UTF-16LE with BOM，行结构不变
"""
import json
import os
import re

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario\equipment.pgeqp'
DST = r'D:\PGForever1.021\PG\Scenario\equipment.pgeqp'
TERMS = r'D:\DSH\军事游戏汉化\pgforever\work\pg\equip-terms.json'
REPORT = r'D:\DSH\军事游戏汉化\pgforever\work\pg\equip-changes.txt'

conf = json.load(open(TERMS, encoding='utf-8'))
terms = conf['terms']
whole = conf.get('whole', {})
rules = sorted(terms.items(), key=lambda x: -len(x[0]))

raw = open(SRC, 'rb').read()
assert raw[:2] == b'\xff\xfe', '源文件应为 UTF-16LE BOM'
# 'utf-16' 解码会自动去掉 BOM；输出时用 utf-16-le 并手工补回 BOM
body = raw.decode('utf-16')

lines = body.split('\r\n')
print('总行数 %d（含表头注释）' % len(lines))


def tr_name(name):
    # 整体映射优先（用于语序需要调整的复合名）
    if name in whole:
        return whole[name], ['整条替换']
    out = name
    hits = []
    for en, zh in rules:
        pat = r'(?<![A-Za-z])' + re.escape(en) + r'(?![A-Za-z])'
        new = re.sub(pat, zh, out)
        if new != out:
            hits.append('%s→%s' % (en, zh))
            out = new
    # 中文排版：去掉汉字之间的多余空格（如 "2 磅 反坦克炮" -> "2 磅反坦克炮"）
    out = re.sub(r'(?<=[\u4e00-\u9fff]) +(?=[\u4e00-\u9fff])', '', out)
    return out, hits


changed = []
kept = 0
for i, line in enumerate(lines):
    if i < 2 or not line.strip():
        continue
    cols = line.split('\t')
    if len(cols) < 2:
        continue
    new_name, hits = tr_name(cols[1])
    if new_name != cols[1]:
        changed.append((cols[0], cols[1], new_name, hits))
        cols[1] = new_name
        lines[i] = '\t'.join(cols)
    else:
        kept += 1

out = '\ufeff' + '\r\n'.join(lines)
open(DST, 'wb').write(out.encode('utf-16-le'))

print('已改写名称 %d 条；保持原样（纯型号）%d 条' % (len(changed), kept))

# 校验：行数、列数、非 Name 列内容必须完全一致
src_lines = body.split('\r\n')
new_body = open(DST, 'rb').read().decode('utf-16').lstrip('\ufeff')
new_lines = new_body.split('\r\n')
assert len(src_lines) == len(new_lines), '行数变化！'
diff_cols = 0
for a, b in zip(src_lines, new_lines):
    ca, cb = a.split('\t'), b.split('\t')
    if len(ca) != len(cb):
        diff_cols += 1
        continue
    for j in range(len(ca)):
        if j == 1:
            continue
        if ca[j] != cb[j]:
            diff_cols += 1
            break
assert diff_cols == 0, '非 Name 列被改动！'
print('校验通过：行数一致，除 Name 列外全部列逐字未变')

with open(REPORT, 'w', encoding='utf-8') as f:
    f.write('装备名改写清单（%d 条）\n\n' % len(changed))
    for idx, old, new, hits in changed:
        f.write('%4s  %-30s -> %-30s   [%s]\n' % (idx, old, new, ', '.join(hits)))
print('-> %s' % REPORT)

print()
print('=== 抽查前 25 条 ===')
for idx, old, new, hits in changed[:25]:
    print('  %4s %-30s -> %s' % (idx, old, new))
