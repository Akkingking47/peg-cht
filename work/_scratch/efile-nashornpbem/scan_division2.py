# -*- coding: utf-8 -*-
"""精确统计 OLGWW2 .xscn 组1：「原文段=纯 数字+兵种缩写」时，中文侧怎么译。
用于找出**同形态译法不一致**（师级漏「师」/ 团级多「团」）。
"""
import os, sys, io, glob, collections, re

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'

# 纯「数字 + 单个兵种缩写」= 师/独立单位级，后面不再跟子单位
PURE = re.compile(r'^(\d+)\s*(Pz|Div\.?|Mot|Inf|Cav\.?|Mtn|Ski|Air|Arm|Para|PzGr)\s*\.?$', re.I)
SUB = re.compile(r'^(\d+)\s*(Pz|Cav|Mot|Inf)\s*(R\b|Br\b|Bde|Rgt|Bn|Coy|Kompanie|Bataillon|Regt|Brg)', re.I)

def g1(path):
    d, items, meta = parse(path)
    out = {}
    if not items:
        return out
    for gi, idx, off, ln in items:
        if gi >= 1:
            out[(gi, idx)] = d[off + 2:off + 2 + ln]
    return out

pairs = collections.Counter()
examples = collections.defaultdict(list)
for po in sorted(glob.glob(os.path.join(OR, '*.xscn'))):
    fn = os.path.basename(po)
    pn = os.path.join(NN, fn)
    if not os.path.exists(pn):
        continue
    o, n = g1(po), g1(pn)
    for key in sorted(set(o) & set(n)):
        so = o[key].decode('cp1252', 'replace')
        sn = n[key].decode('gbk', 'replace')
        for a, b in zip(so.split('/'), sn.split('/')):
            a = a.strip(); b = b.strip()
            m = PURE.match(a)
            if not m:
                continue
            typ = m.group(2).rstrip('.').lower()
            # 中文侧剥掉「第N」
            core = re.sub(r'^第\d+', '', b)
            pairs[(typ, core)] += 1
            if len(examples[(typ, core)]) < 2:
                examples[(typ, core)].append((fn, key[0], key[1], a, b))

print('=== 「纯 数字+兵种缩写」的中文译法分布 ===')
for typ in sorted(set(k[0] for k in pairs)):
    sub = [(k[1], v) for k, v in pairs.items() if k[0] == typ]
    sub.sort(key=lambda x: -x[1])
    tot = sum(v for _, v in sub)
    print('\n[%s]  共 %d 段' % (typ, tot))
    for core, v in sub:
        print('    %-16s %4d   e.g. %s' % (core or '(空)', v, examples[(typ, core)][0][3:]))

print('\n=== 疑似问题：core 为空 或含 ASCII 点 ===')
for (typ, core), v in sorted(pairs.items(), key=lambda x: -x[1]):
    if core == '' or re.search(r'[.\-]$', core) or re.search(r'[A-Za-z]', core):
        print('   [%s] core=%-14s x%-4d  %s' % (typ, core or '(空)', v, examples[(typ, core)][0]))
