# -*- coding: utf-8 -*-
"""扫描 OLGWW2 番号串的**同文件内自相矛盾**：
同一个「数字+兵种缩写」段在同一文件里出现多种中文译法（如 4 Arm 既作「第4装甲」又作「第4装甲师」）。

原文侧／中文侧按 (gi, idx) 与 '/' 段号逐段对齐（.xscn 用索引、.txt 用行号），零歧义。
按用户裁定：**只修同文件内自相矛盾的**（跨文件的差异保留，可能指不同部队）。

用法： C:\\Python314\\python.exe scan_arm_inf_conflict.py
"""
import os, sys, io, glob, re, collections

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
PURE = re.compile(r'^(\d+)\s*(Pz|Div\.?|Mot|Inf|Cav\.?|Mtn|Ski|Air|Arm|Para|PzGr)\s*\.?$', re.I)


def pairs_xscn(fn):
    po, pn = os.path.join(OR, fn), os.path.join(NN, fn)
    if not (os.path.exists(po) and os.path.exists(pn)):
        return
    do, io_, _ = parse(po)
    dn, inn, _ = parse(pn)
    mo = {(g, k): v for g, k, v in
          ((g, k, do[o + 2:o + 2 + l].decode('cp1252', 'replace')) for g, k, o, l in io_) if g >= 1}
    mn = {(g, k): v for g, k, v in
          ((g, k, dn[o + 2:o + 2 + l].decode('gbk', 'replace')) for g, k, o, l in inn) if g >= 1}
    for key in sorted(set(mo) & set(mn)):
        a, b = mo[key].split('/'), mn[key].split('/')
        for i, seg in enumerate(a):
            yield seg.strip(), (b[i].strip() if i < len(b) else ''), 'g%d#%d' % key


def pairs_txt(fn):
    po, pn = os.path.join(OR, fn + '.txt'), os.path.join(NN, fn + '.txt')
    if not (os.path.exists(po) and os.path.exists(pn)):
        return
    lo = io.open(po, encoding='cp1252', errors='replace', newline='').read().replace('\r\n', '\n').split('\n')
    ln = io.open(pn, encoding='gbk', errors='replace', newline='').read().replace('\r\n', '\n').split('\n')
    for i in range(min(len(lo), len(ln))):
        a, b = lo[i].split('/'), ln[i].split('/')
        if len(a) != len(b):
            # 段数不齐 = 英中两侧该行结构不同（如中文侧多了 [军] 标注）⇒ 位置对齐失效，整行跳过
            continue
        for j, seg in enumerate(a):
            yield seg.strip(), b[j].strip(), 'L%d' % (i + 1)


total = collections.Counter()
bad_files = []
for kind, fnlist, fnfunc in (
        ('xscn', sorted(os.path.basename(p) for p in glob.glob(os.path.join(NN, '*.xscn'))), pairs_xscn),
        ('txt', sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(NN, '*.txt'))), pairs_txt)):
    for fn in fnlist:
        bykey = collections.defaultdict(lambda: collections.defaultdict(list))
        for en, zh, loc in fnfunc(fn):
            m = PURE.match(en)
            if not m or not zh:
                continue
            bykey[(m.group(1), m.group(2).rstrip('.').lower())][zh].append(loc)
        hits = {k: v for k, v in bykey.items() if len(v) > 1}
        if hits:
            bad_files.append((kind, fn, hits))
            for k, v in hits.items():
                total['%s %s' % k] += 1

print('=== 同文件内自相矛盾：%d 个文件 ===' % len(bad_files))
for kind, fn, hits in bad_files:
    print('\n[%s] %s' % (kind, fn))
    for (num, typ), v in sorted(hits.items()):
        items = ' | '.join('%s x%d %s' % (zh, len(locs), locs[:2]) for zh, locs in sorted(v.items()))
        print('   %-10s %s' % ('%s %s' % (num, typ), items))
print('\n合计矛盾键 %d 个:' % sum(total.values()), dict(total))
