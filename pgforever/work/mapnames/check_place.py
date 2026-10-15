# -*- coding: utf-8 -*-
"""
地名译表批量校验器。

用法：
    python check_place.py                # 校验所有 place_*.py
    python check_place.py --seg B        # 只校验 B 段，列出待译
    python check_place.py --todo B       # 输出 B 段待译清单（含长度/频次）

校验项：
    1) 是否覆盖源中全部名称
    2) 译名 UTF-8 字节 <= 19（6 汉字）
    3) 译名是否含中文（占位符除外）
    4) 译名是否与源重复（同译名冲突提示）
"""

import sys
import io
import os
import glob
import struct
import argparse
import collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import place_tools as T  # noqa
import place_mojibake as M  # noqa

WORK = HERE


def load_source_names(skip_format_b=True):
    """收集格式 A 文件中的全部名称 -> 频次。"""
    names = collections.Counter()
    for p in T.find_mapnames():
        raw = open(p, 'rb').read()
        n = struct.unpack_from('<H', raw, 0)[0]
        if skip_format_b and T.detect_format(raw, n) == 'B':
            continue
        for i in range(14, n):
            off = 2 + i * 20
            if off + 20 > len(raw):
                break
            nm = raw[off:off + 20].split(b'\x00')[0]
            try:
                s = nm.decode('utf-8')
            except UnicodeDecodeError:
                continue
            if s:
                names[s] += 1
    return names


def load_all_tables():
    tbl = {}
    dupe = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(WORK, 'place_*.py'))):
        if f.endswith('place_tools.py') or f.endswith('place_mojibake.py'):
            continue
        for k, v in T.load_table(f).items():
            dupe[k].append(v)
            tbl[k] = v
    return tbl, dupe


def check(only=None):
    names = load_source_names()
    tbl, dupe = load_all_tables()
    if only:
        src = sorted(k for k in names if k[:1].upper() == only.upper())
    else:
        src = sorted(k for k in names if not T.has_cn(k))
    missing = sorted(set(src) - set(tbl) - {b.decode('latin1') for b in M.MOJIBAKE})
    scope = {k: tbl[k] for k in src if k in tbl} if only else tbl
    over = [(k, v, T.zb(v)) for k, v in scope.items() if not T.fits(v)]
    nocn = [(k, v) for k, v in scope.items()
            if not T.has_cn(v) and k not in T.KEEP_AS_IS and len(v) > 2]
    print('源名称 %d，译表 %d' % (len(src), len(tbl)))
    print('未覆盖 %d' % len(missing))
    for m in missing[:40]:
        print('   ', repr(m))
    print('超长 %d' % len(over))
    for k, v, b in over[:40]:
        print('    %-26s %s (%dB)' % (k, v, b))
    print('无中文 %d' % len(nocn))
    for k, v in nocn[:40]:
        print('    %-26s %s' % (k, v))
    conflicts = {k: vs for k, vs in dupe.items() if len(set(vs)) > 1}
    if conflicts:
        print('⚠️ 同源多译分歧 %d' % len(conflicts))
        for k, vs in list(conflicts.items())[:20]:
            print('    %-26s %s' % (k, set(vs)))


def todo(seg):
    names = load_source_names()
    src = sorted(k for k in names if k[:1].upper() == seg.upper()
                 and not T.has_cn(k))
    out = os.path.join(WORK, 'todo_%s.txt' % seg.upper())
    with open(out, 'w', encoding='utf-8') as fh:
        for s in src:
            fh.write('%2d|%4d|%s\n' % (len(s), names[s], s))
    print('%s 段待译 %d 条 -> %s' % (seg.upper(), len(src), out))
    for s in src:
        print('%2d|%4d|%s' % (len(s), names[s], s))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', default=None)
    ap.add_argument('--todo', default=None)
    a = ap.parse_args()
    if a.todo:
        todo(a.todo)
    else:
        check(a.seg)
