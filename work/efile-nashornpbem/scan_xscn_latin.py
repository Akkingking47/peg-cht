# -*- coding: utf-8 -*-
"""扫描中文侧 .xscn：找仍以拉丁字母出现（未译）的字串，并区分政策保留与真漏译。

用法:  python scan_xscn_latin.py [EFILE_OLGWW2 ...]
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_residual import parse  # noqa: E402

GAME = r'D:\OpenPG2'
CJK = re.compile(r'[\u4e00-\u9fff]')
LATIN = re.compile(r'[A-Za-z]')
ROMAN = re.compile(r'^[IVXLCDM]+$')
# 政策保留：舰名前缀、纯编号、常见番号缩写
SHIP_PFX = ('HMS ', 'HMAS ', 'HMNZS ', 'USS ', 'KMS ', 'RM ', 'RN ')


def classify(val):
    s = val.strip().strip('\x00')
    if not s or not LATIN.search(s):
        return None
    if CJK.search(s):
        # 中文夹拉丁 —— 混合串，多半合格（型号/缩写），但要记录
        return 'MIXED'
    core = s.replace(' ', '')
    if core.isdigit() or re.fullmatch(r'[\dA-Za-z\-/\.\[\]]+', s) and len(core) <= 8:
        if ROMAN.match(core) or re.fullmatch(r'[\d\-/\.\[\]]+', core):
            return 'CODE'
    if any(s.upper().startswith(p) for p in SHIP_PFX):
        return 'SHIP'
    if re.search(r'[^\x00-\x7f]', s):
        return 'LATIN1'   # 含非 ASCII 字节 -> 中文环境下会乱码，重点
    return 'LATIN'


def scan(efile):
    # 引擎实际读取的目录：<efile>\SCENARIO\（TEXT-ZH\SCENARIO 只是死镜像，不参与）
    root = os.path.join(GAME, efile, 'SCENARIO')
    files = sorted(glob.glob(os.path.join(root, '*.xscn')))
    stats = collections.Counter()
    per_group = collections.defaultdict(collections.Counter)
    samples = collections.defaultdict(list)
    for p in files:
        try:
            data, items, meta = parse(p)
        except Exception as e:
            print('  !! %s %s' % (os.path.basename(p), e))
            continue
        if not items:
            continue
        for gi, idx, voff, vlen in items:
            raw = data[voff + 2:voff + 2 + vlen]
            try:
                val = raw.decode('gbk')
            except Exception:
                val = raw.decode('gbk', errors='replace')
            k = classify(val)
            if not k:
                continue
            stats[k] += 1
            per_group[gi][k] += 1
            if len(samples[k]) < 400:
                samples[k].append((os.path.basename(p), gi, idx, val.replace('\x00', '·')))
    return stats, per_group, samples


def main():
    efiles = [a for a in sys.argv[1:]] or ['EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM']
    allsm = collections.defaultdict(list)
    for e in efiles:
        stats, per_group, samples = scan(e)
        print('=' * 70)
        print('%s   分类: %s' % (e, dict(stats)))
        for gi in sorted(per_group):
            print('   组%-3d %s' % (gi, dict(per_group[gi])))
        for k in ('LATIN', 'LATIN1'):
            for it in samples.get(k, [])[:25]:
                print('   [%s] g%-2d %-16s %s' % (k, it[1], it[0], it[3][:60]))
            allsm[k].extend((e,) + it for it in samples.get(k, []))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'xscn-latin-residual.tsv'),
              'w', encoding='utf-8-sig', newline='') as f:
        f.write('kind\tefile\tfile\tgroup\tidx\tval\n')
        for k in ('LATIN', 'LATIN1'):
            for row in allsm[k]:
                f.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (row[0], row[1], row[2], row[3], row[4], row[5].replace('\t', ' ')))
    print('\n明细 -> out/xscn-latin-residual.tsv')


if __name__ == '__main__':
    main()
