# -*- coding: utf-8 -*-
"""B 类统一后对**改动过的 .xscn** 做独立结构复核（逐条目，不靠子串猜）。

对 backup/olgww2-b-unify2-before 与现值分别用独立解析器 parse() 解析，比对：
  · 条目数 / 标题 / 组表 必须完全一致（结构无损）
  · 列出所有取值改变的条目（g#k 旧 -> 新），供人工判方向

用法： C:\\Python314\\python.exe verify_xscn_after.py
"""
import os, sys

sys.path.insert(0, os.path.join(r'D:\DSH\军事游戏汉化\work', 'efile-nashornpbem'))
from apply_residual import parse

GAME = r'D:\OpenPG2'
BK = r'D:\DSH\军事游戏汉化\backup\olgww2-b-unify2-before'


def vals(d, items, meta):
    """(g,k) -> 值字符串；标题记为 (-1, 0)。"""
    out = {}
    for g, k, off, ln in items:
        out[(g, k)] = d[off + 2:off + 2 + ln].decode('gbk', 'replace')
    if meta and meta[0] is not None:
        out[(-1, 0)] = d[meta[0] + 2:meta[0] + 2 + meta[1]].decode('gbk', 'replace')
    return out


ok = bad = changed_files = n_chg = 0
for b in sorted(os.listdir(BK)):
    if not b.endswith('.xscn'):
        continue
    ef, tail = b.split('__', 1)
    fn = tail.replace('SCENARIO_', '')
    old = os.path.join(BK, b)
    cur = os.path.join(GAME, ef, 'SCENARIO', fn)
    if not os.path.exists(cur):
        print('!! 现值缺失', ef, fn)
        bad += 1
        continue
    d1, i1, m1 = parse(old)
    d2, i2, m2 = parse(cur)
    prob = []
    if len(i1) != len(i2):
        prob.append('条目数 %d->%d' % (len(i1), len(i2)))
    if (m1[0] is None) != (m2[0] is None):
        prob.append('标题有无变化')
    if (m1[2] or []) != (m2[2] or []):
        prob.append('组表变化 %s->%s' % (m1[2], m2[2]))
    if prob:
        print('!! %-12s %-22s %s' % (ef[6:], fn, '; '.join(prob)))
        bad += 1
        continue
    ok += 1
    v1, v2 = vals(d1, i1, m1), vals(d2, i2, m2)
    diffs = [(k, v1[k], v2.get(k, '')) for k in v1 if v1[k] != v2.get(k)]
    if diffs:
        changed_files += 1
        n_chg += len(diffs)
        print('  %-12s %-22s' % (ef[6:], fn))
        for (g, k), a, z in sorted(diffs):
            tag = '标题' if g == -1 else 'g%d#%d' % (g, k)
            print('      %-10s %-26s -> %s' % (tag, a[:26], z[:26]))

print('\n结构复核: 通过 %d / 异常 %d ；取值改动 %d 处 / %d 文件' % (ok, bad, n_chg, changed_files))
