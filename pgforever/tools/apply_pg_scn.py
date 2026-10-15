# -*- coding: utf-8 -*-
r"""
PG *.pgscn 汉化：只替换 Name 与 Description 两个显示字段。
其余全部原样保留——尤其 # Victory conditions 段（AXIS VICTORY / ALLIED VICTORY）是内部键，绝不能动。
源 UTF-16LE(BOM)，输出同样 UTF-16LE(BOM)，行结构不变。
"""
import json
import os

SRC = r'D:\DSH\军事游戏汉化\pgforever\backup\origin\PG\Scenario'
DST = r'D:\PGForever1.021\PG\Scenario'
TRANS = r'D:\DSH\军事游戏汉化\pgforever\work\pg\scn-trans.json'

tr = json.load(open(TRANS, encoding='utf-8'))
tr.pop('note', None)

done = 0
miss = []
for fn, cfg in sorted(tr.items()):
    src = os.path.join(SRC, fn)
    if not os.path.exists(src):
        miss.append(fn + ' (源文件缺失)')
        continue
    raw = open(src, 'rb').read()
    assert raw[:2] == b'\xff\xfe', '%s 不是 UTF-16LE' % fn
    text = raw.decode('utf-16')
    lines = text.split('\r\n')

    hit_name = hit_desc = False
    for i, line in enumerate(lines):
        if line.startswith('Name\t'):
            val = line.split('\t', 1)[1]
            if val.strip() == cfg['name']:
                hit_name = True
                continue
            lines[i] = 'Name\t' + cfg['name']
            hit_name = True
        elif line.startswith('Description\t'):
            lines[i] = 'Description\t' + cfg['desc']
            hit_desc = True

    if not hit_name or not hit_desc:
        miss.append('%s (name=%s desc=%s)' % (fn, hit_name, hit_desc))
        continue

    open(os.path.join(DST, fn), 'wb').write(('\ufeff' + '\r\n'.join(lines)).encode('utf-16-le'))
    done += 1

print('已处理 %d / %d 个 pgscn' % (done, len(tr)))
if miss:
    print('!! 未处理: %s' % miss)

# 校验：每个文件的行数、以及除 Name/Description 外所有行必须与原文逐字一致
bad = 0
for fn in tr:
    if fn == 'note':
        continue
    a = open(os.path.join(SRC, fn), 'rb').read().decode('utf-16').split('\r\n')
    b = open(os.path.join(DST, fn), 'rb').read().decode('utf-16').split('\r\n')
    if len(a) != len(b):
        print('!! %s 行数变化' % fn)
        bad += 1
        continue
    for x, y in zip(a, b):
        if x == y:
            continue
        if not (x.startswith('Name\t') or x.startswith('Description\t')):
            print('!! %s 非显示字段被改动: %r' % (fn, x[:60]))
            bad += 1
            break
print('校验完成，异常文件 %d 个' % bad)

# 抽查
print()
print('=== 抽查 ===')
for fn in ['001.pgscn', '015.pgscn', '030.pgscn']:
    t = open(os.path.join(DST, fn), 'rb').read().decode('utf-16')
    for l in t.split('\r\n')[:4]:
        if l.startswith(('Name', 'Description')):
            print('  %s | %s' % (fn, l[:90]))
