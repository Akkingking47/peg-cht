# -*- coding: utf-8 -*-
"""批次二/三：A 类 (not used) 与 F 类权威偏离订正。

① EFILE_NASHORNPBEM\\TEXT-ZH\\equip.txt : (not used) -> （未使用）
② EFILE_OLGWW2\\TEXT-ZH\\names.txt      : 巴约·希劳德 -> 巴约·吉罗
（只改 TEXT-ZH 中文侧；root 是原文，不动。）

用法： python fix_batch_A_F.py [--apply]
"""
import os, sys, shutil, hashlib

GAME = r'D:\OpenPG2'
BK = r'D:\DSH\军事游戏汉化\backup\batch-A-F-before'

JOBS = [
    (os.path.join(GAME, 'EFILE_NASHORNPBEM', 'TEXT-ZH', 'equip.txt'),
     '(not used)'.encode('ascii'), '（未使用）'.encode('gbk'), 'equip.txt'),
    (os.path.join(GAME, 'EFILE_OLGWW2', 'TEXT-ZH', 'names.txt'),
     '巴约·希劳德'.encode('gbk'), '巴约·吉罗'.encode('gbk'), 'names.txt'),
]

def main():
    apply = '--apply' in sys.argv
    os.makedirs(BK, exist_ok=True)
    for path, old, new, tag in JOBS:
        d = open(path, 'rb').read()
        n = d.count(old)
        print('%-58s  %s  x%d' % (os.path.relpath(path, GAME), old.decode('gbk', 'replace'), n))
        if n == 0:
            continue
        nd = d.replace(old, new)
        print('     -> %s   %d B -> %d B' % (new.decode('gbk'), len(d), len(nd)))
        if apply:
            dst = os.path.join(BK, os.path.basename(path))
            if not os.path.exists(dst):
                shutil.copy2(path, dst)
            tmp = path + '.new'
            open(tmp, 'wb').write(nd)
            assert open(tmp, 'rb').read() == nd
            os.replace(tmp, path)
            print('     已写回（备份 %s）' % os.path.basename(dst))
    print('\n%s' % ('完成' if apply else '（dry-run，未写盘）'))

if __name__ == '__main__':
    main()
