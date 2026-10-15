# -*- coding: utf-8 -*-
"""量化 **.xscn 组1 番号** 与 **同场景 .txt 清单** 的偏差（新发现的审计盲区：
bridge_check 只校验组0，组1 从未与 .txt 对过）。

以 .txt 为规范本地化（docs19），逐场景建「原文段 -> 中文段」字典（同场景优先），
再逐 .xscn 组1 段比对，按差异形态归类统计。

用法： C:\\Python314\\python.exe scan_g1_vs_txt.py
"""
import os, sys, glob, io, re, collections

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'


def dict_for(name):
    """同场景 .txt 的 原文段->中文段（逐行平行，段数必须相等）。"""
    po, pn = os.path.join(OR, name + '.txt'), os.path.join(NN, name + '.txt')
    d = {}
    if not (os.path.exists(po) and os.path.exists(pn)):
        return d
    lo = io.open(po, encoding='cp1252', errors='replace', newline='').read().replace('\r\n', '\n').split('\n')
    ln = io.open(pn, encoding='gbk', errors='replace', newline='').read().replace('\r\n', '\n').split('\n')
    for i in range(min(len(lo), len(ln))):
        a, b = lo[i].split('/'), ln[i].split('/')
        if len(a) != len(b):
            continue
        for x, y in zip(a, b):
            x, y = x.strip(), y.strip()
            if x and y and x not in d:
                d[x] = y
    return d


cats = collections.Counter()
samples = collections.defaultdict(list)
files = collections.Counter()
for p in sorted(glob.glob(os.path.join(NN, '*.xscn'))):
    name = os.path.basename(p)[:-5]
    dic = dict_for(name)
    if not dic:
        continue
    d, items, meta = parse(p)
    for g, k, o, l in items:
        if g < 1:
            continue
        po_path = os.path.join(OR, os.path.basename(p))
        if not os.path.exists(po_path):
            continue
        do, io_, _ = parse(po_path)
        om = {(gg, kk): (oo, ll) for gg, kk, oo, ll in io_}
        if (g, k) not in om:
            continue
        oo, ll = om[(g, k)]
        so = do[oo + 2:oo + 2 + ll].decode('cp1252', 'replace')
        sn = d[o + 2:o + 2 + l].decode('gbk', 'replace')
        ao, an = so.split('/'), sn.split('/')
        if len(ao) != len(an):
            cats['段数不齐(跳过)'] += 1
            continue
        for x, y in zip(ao, an):
            x, y = x.strip(), y.strip()
            if not x or not y or x not in dic:
                continue
            t = dic[x]
            if t == y:
                continue
            # 归类：仅师/师团之差 vs 其它
            if re.fullmatch(r'第(\d+)师团', t) and re.fullmatch(r'第(\d+)师', y) and t[:2] == y[:2]:
                cats['师 应作 师团'] += 1
            elif re.sub(r'师团', '师', t) == y:
                cats['师团族其它差异'] += 1
            elif re.sub(r'[\s·（）()]', '', t) == re.sub(r'[\s·（）()]', '', y):
                cats['仅空格/标点差异'] += 1
            else:
                cats['其它'] += 1
            files[name] += 1
            if len(samples[list(cats)[-1]]) < 6:
                samples[list(cats)[-1]].append((name, g, k, x, y, t))

print('=== .xscn 组1 与 .txt 清单的偏差 ===')
for k, v in cats.most_common():
    print('  %-16s %d' % (k, v))
print('\n涉及文件 %d 个，前 12:' % len(files), files.most_common(12))
print('\n=== 样例 ===')
for c, ss in samples.items():
    print(' [%s]' % c)
    for name, g, k, x, y, t in ss:
        print('    %-16s g%d#%-4d %-30s .xscn=%-18s .txt=%s' % (name, g, k, x, y, t))
