# -*- coding: utf-8 -*-
"""把 backup/olgww2-b-unify-before 里的文件还原回原路径。
备份名格式： <EFILE>__<relpath 的 \\ 换成 _>。用手头真实文件枚举反向映射，避免下划线歧义。
"""
import os, shutil, sys, glob

GAME = r'D:\OpenPG2'
BK = r'D:\DSH\军事游戏汉化\backup\olgww2-b-unify-before'
EFILES = ['EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM']

# 建 mangled -> 真实路径 映射
m = {}
for ef in EFILES:
    base = os.path.join(GAME, ef)
    for p in glob.glob(os.path.join(base, '**', '*'), recursive=True):
        if not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, base)
        m[ef + '__' + rel.replace('\\', '_')] = p

apply = '--apply' in sys.argv
n = 0
for f in sorted(os.listdir(BK)):
    src = os.path.join(BK, f)
    dst = m.get(f)
    if not dst:
        print('!! 无对应: %s' % f)
        continue
    print('%-64s -> %s' % (f[:64], os.path.relpath(dst, GAME)))
    if apply:
        shutil.copy2(src, dst)
    n += 1
print('\n%s 共 %d 个' % ('已还原' if apply else '（dry-run）', n))
