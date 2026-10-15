# -*- coding: utf-8 -*-
"""打印 OLGWW2 .xscn 中「数字+兵种缩写」出现矛盾的那些条目的**完整番号串**（原文↔中文并列），
以便判断到底是同一部队的两种写法，还是两个不同部队（如 1 Arm = 1st Armoured 与 1st Army）。

用法： C:\\Python314\\python.exe dump_arm_context.py [文件名1 文件名2 ...]
"""
import os, sys, re

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
PURE = re.compile(r'^(\d+)\s*(Pz|Div\.?|Mot|Inf|Cav\.?|Mtn|Ski|Air|Arm|Para|PzGr)\s*\.?$', re.I)

WANT = sys.argv[1:] or ['DAK2.xscn', 'DAK5.xscn', 'DAK7.xscn', 'DAK8.xscn', 'DAKTU01.xscn',
                        'SPTU01.xscn', 'TU02.xscn', 'TU04.xscn', 'TU05.xscn', 'TU06.xscn',
                        'n42s01.xscn']

for fn in WANT:
    po, pn = os.path.join(OR, fn), os.path.join(NN, fn)
    if not (os.path.exists(po) and os.path.exists(pn)):
        print('!! 缺失', fn)
        continue
    do, io_, _ = parse(po)
    dn, inn, _ = parse(pn)
    mo = {(g, k): (do[o + 2:o + 2 + l].decode('cp1252', 'replace'))
          for g, k, o, l in io_ if g >= 1}
    mn = {(g, k): (dn[o + 2:o + 2 + l].decode('gbk', 'replace'))
          for g, k, o, l in inn if g >= 1}
    # 找出该文件里所有「N arm/inf/cav 段」出现的位置与译法
    rows = []
    for key in sorted(set(mo) & set(mn)):
        a, b = mo[key].split('/'), mn[key].split('/')
        if len(a) != len(b):
            continue
        for i, seg in enumerate(a):
            m = PURE.match(seg.strip())
            if m:
                rows.append((key, i, seg.strip(), b[i].strip(), mo[key], mn[key]))
    # 只打印有矛盾的键
    bykey = {}
    for key, i, seg, zh, so, sn in rows:
        m = PURE.match(seg)
        bykey.setdefault((m.group(1), m.group(2).rstrip('.').lower()), set()).add(zh)
    confl = {k for k, v in bykey.items() if len(v) > 1}
    if not confl:
        continue
    print('\n===== %s  矛盾键 %s =====' % (fn, sorted(confl)))
    for key, i, seg, zh, so, sn in rows:
        m = PURE.match(seg)
        k = (m.group(1), m.group(2).rstrip('.').lower())
        if k in confl:
            print('  g%d#%-4d 段%d  %-40s | %s' % (key[0], key[1], i, so, sn))
