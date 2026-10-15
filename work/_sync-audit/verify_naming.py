# -*- coding: utf-8 -*-
"""定名改写后的结构完整性核对：改动只应发生在槽值内容，槽结构必须不变。

对每个 EFILE 的每个 .xscn，用 apply_residual.parse 同时解析
  · 成品侧 D:/OpenPG2/<EFILE>/SCENARIO/<fn>
  · 原始侧 D:/DSH/军事游戏汉化/backup/ORIGINAL-<EFILE>/SCENARIO/<fn>
比较槽键序列 (g,k) 与槽数；不一致即报告。另统计尺寸变化分布。

用法： python verify_naming.py
"""
import os, sys, collections

sys.path.insert(0, os.path.join(r'D:\DSH\军事游戏汉化\work', 'efile-nashornpbem'))
from apply_residual import parse

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
EFILES = ['EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM']

bad = 0
n_files = 0
big = []
for efile in EFILES:
    d = os.path.join(GAME, efile, 'SCENARIO')
    b = os.path.join(ROOT, 'backup', 'ORIGINAL-' + efile, 'SCENARIO')
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith('.xscn'):
            continue
        p, q = os.path.join(d, fn), os.path.join(b, fn)
        if not os.path.exists(q):
            print('! 原始侧缺失 %s/%s' % (efile, fn))
            continue
        n_files += 1
        _, it1, _ = parse(p)
        _, it2, _ = parse(q)
        k1 = [(g, k) for g, k, _o, _l in it1]
        k2 = [(g, k) for g, k, _o, _l in it2]
        if k1 != k2:
            bad += 1
            print('! 槽结构不同 %s/%s 成品 %d 槽 · 原始 %d 槽' % (efile, fn, len(k1), len(k2)))
            for i in range(max(len(k1), len(k2))):
                a = k1[i] if i < len(k1) else None
                c = k2[i] if i < len(k2) else None
                if a != c:
                    print('    首个差异 idx=%d 成品=%s 原始=%s' % (i, a, c))
                    break
        n1, n2 = os.path.getsize(p), os.path.getsize(q)
        if n1 != n2:
            big.append((n1 - n2, efile, fn))

print('核对 .xscn %d 个 · 槽结构异常 %d 个' % (n_files, bad))
big.sort()
print('尺寸有变化的文件 %d 个：' % len(big))
for dl, efile, fn in big:
    print('  %+5d B  %s/%s' % (dl, efile, fn))
print('尺寸总变化 %+d B' % sum(x[0] for x in big))
print('结论：' + ('槽结构全部一致 ✅' if bad == 0 else '存在异常 ❌'))
