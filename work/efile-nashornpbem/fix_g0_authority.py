# -*- coding: utf-8 -*-
"""订正 2 处**组0**番号：上一轮 fix_division.py 未排除组 0，把镜像 `.txt` 的
`第11师团` / `第57师团` 误改成 `第11师` / `第57师`（bridge_check 报为 .xscn↔.txt 不一致）。

组 0 是 `.txt` 场景名清单的镜像（docs19 已定 .txt 为规范本地化）⇒ 必须跟随 .txt。
权威值取自 `bridge_check.py` 的「权威中文」列（`ORIGINAL-*.txt` ↔ 现值 `.txt` 逐行平行字典）。

用法： C:\\Python314\\python.exe fix_g0_authority.py [--apply]
备份： backup/olgww2-g0div-before/
"""
import os, sys, shutil

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
BK = r'D:\DSH\军事游戏汉化\backup\olgww2-g0div-before'

# (文件, 组, 索引, 旧中文, 权威中文)  —— 权威中文来自 rschi01.txt:26 与 rssov03.txt:8
FIX = [
    ('RSCHI01.xscn', 0, 14, '第11师', '第11师团'),
    ('RSSOV03.xscn', 0, 1, '第57师/[第3军/关东军]', '第57师团/[第3军/关东军]'),
]

apply = '--apply' in sys.argv
os.makedirs(BK, exist_ok=True)
byfile = {}
for fn, g, k, old, new in FIX:
    byfile.setdefault(fn, []).append((g, k, old, new))

n = 0
for fn, items in byfile.items():
    p = os.path.join(NN, fn)
    data, its, meta = parse(p)
    table = {(gg, kk): (o, l) for gg, kk, o, l in its}
    repl = []
    for g, k, old, new in items:
        if (g, k) not in table:
            print('!! 未找到 %s g%d#%d' % (fn, g, k))
            continue
        o, l = table[(g, k)]
        cur = data[o + 2:o + 2 + l].decode('gbk')
        if cur == new:
            print('   已合规 %s g%d#%d' % (fn, g, k))
            continue
        if cur != old:
            print('!! 现值不符，跳过 %s g%d#%d 现=%r 期=%r' % (fn, g, k, cur, old))
            continue
        nb = new.encode('gbk')
        repl.append((o, 2 + l, len(nb).to_bytes(2, 'little') + nb, g, k, cur, new))
    if not repl:
        continue
    for _, _, _, g, k, cur, new in repl:
        print('   %s g%d#%-4d %-24s -> %s' % (fn, g, k, cur, new))
    if not apply:
        continue
    dst = os.path.join(BK, fn)
    if not os.path.exists(dst):
        shutil.copy2(p, dst)
    buf = bytearray()
    last = 0
    for off, oldlen, nb, *_ in sorted(repl, key=lambda x: x[0]):
        buf += data[last:off] + nb
        last = off + oldlen
    buf += data[last:]
    tmp = p + '.new'
    open(tmp, 'wb').write(bytes(buf))
    assert open(tmp, 'rb').read() == bytes(buf)
    os.replace(tmp, p)
    n += 1
print('已写回 %d 文件%s' % (n, '' if apply else '（dry-run）'))
