# -*- coding: utf-8 -*-
"""OLGWW2 .xscn 组1 番号串「师级单位名」定点订正（原始语言硬桥）。

判定：与 backup\\ORIGINAL-EFILE_OLGWW2\\SCENARIO 同 (gi,idx) 对齐，逐 '/' 段比对。
仅当原文段 = 纯 `数字 Pz` 或 `数字 Div.` 时，中文侧该段必须为 `第N装甲师` / `第N师`。
其余兵种（Arm/Inf/Cav/Mot…）多数派不明确 ⇒ 不动、只报告。

用法： python fix_division.py            # dry-run
       python fix_division.py --apply    # 写盘（备份 backup/olgww2-division-before/）
"""
import os, sys, io, glob, re, shutil, collections

sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse

OR = r'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OLGWW2\SCENARIO'
NN = r'D:\OpenPG2\EFILE_OLGWW2\SCENARIO'
BK = r'D:\DSH\军事游戏汉化\backup\olgww2-division-before'

PZ = re.compile(r'^(\d+)\s*Pz\s*\.?$', re.I)
DIV = re.compile(r'^(\d+)\s*Div\s*\.?$', re.I)


def desired(o_seg):
    m = PZ.match(o_seg)
    if m:
        return '第%s装甲师' % m.group(1)
    m = DIV.match(o_seg)
    if m:
        return '第%s师' % m.group(1)
    return None


def main():
    apply = '--apply' in sys.argv
    stats = collections.Counter()
    samples = []
    plan_all = []
    for po in sorted(glob.glob(os.path.join(OR, '*.xscn'))):
        fn = os.path.basename(po)
        pn = os.path.join(NN, fn)
        if not os.path.exists(pn):
            continue
        do, io_, _ = parse(po)
        dn, inn, _ = parse(pn)
        om = {(g, i): (o, l) for g, i, o, l in io_}
        nm = {(g, i): (o, l) for g, i, o, l in inn}
        repl = []          # (off, oldlenbytes, newbytes, 描述)
        for key in sorted(set(om) & set(nm)):
            g, i = key
            oo, ol = om[key]
            no, nl = nm[key]
            so = do[oo + 2:oo + 2 + ol].decode('cp1252', 'replace')
            sn = dn[no + 2:no + 2 + nl].decode('gbk', 'replace')
            ao = so.split('/'); an = sn.split('/')
            if len(ao) != len(an):
                stats['段数不齐'] += 1
                continue
            changed = False
            na = []
            for k, (a, b) in enumerate(zip(ao, an)):
                want = desired(a.strip())
                if want is not None and b.strip() != want:
                    stats[('PZ' if PZ.match(a.strip()) else 'DIV')] += 1
                    if len(samples) < 25:
                        samples.append((fn, g, i, a.strip(), b.strip(), want))
                    na.append(want)
                    changed = True
                else:
                    na.append(b.strip() if b.strip() else b)
            if changed:
                newval = '/'.join(na).encode('gbk')
                repl.append((no, 2 + nl, len(newval).to_bytes(2, 'little') + newval,
                             '%s g%d#%d' % (fn, g, i)))
        if repl:
            plan_all.append((pn, fn, do, dn, repl))

    print('=== 待改明细（前 25 例）===')
    for fn, g, i, a, b, want in samples:
        print('   %-16s g%d#%-4d  ORIG %-10s  NOW %-14s -> %s' % (fn, g, i, a, b, want))
    print('\n统计：', dict(stats), '  涉及文件', len(plan_all),
          ' 总替换段', sum(len(p[4]) for p in plan_all))

    if not apply:
        print('\n（dry-run，未写盘）')
        return
    os.makedirs(BK, exist_ok=True)
    for pn, fn, do, dn, repl in plan_all:
        dst = os.path.join(BK, fn)
        if not os.path.exists(dst):
            shutil.copy2(pn, dst)
        buf = bytearray()
        last = 0
        for off, oldlen, newbytes, _ in sorted(repl, key=lambda x: x[0]):
            buf += dn[last:off] + newbytes
            last = off + oldlen
        buf += dn[last:]
        tmp = pn + '.new'
        open(tmp, 'wb').write(bytes(buf))
        assert open(tmp, 'rb').read() == bytes(buf)
        os.replace(tmp, pn)
    print('已写回 %d 文件，备份 %s' % (len(plan_all), BK))


if __name__ == '__main__':
    main()
