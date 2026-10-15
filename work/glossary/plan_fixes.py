# -*- coding: utf-8 -*-
"""为 4 批订正生成精确定位与计划（只读，不改游戏文件）。
输出：glossary/fix-plan-*.tsv 与 stdout 摘要。
"""
import os, io, csv, re, glob, collections, sys

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
OUT = os.path.join(ROOT, 'glossary')

FAKE = {'鯾': 'ob', '閑': 'ee', '鰎': 'or', '黶': 'us',
        '雗': 'en', '馻': 'na', '黷': 'ut', '鰊': 'on'}

def rd(p):
    return open(p, 'rb').read()

def ctx(effile, root, fn, needle, enc='gbk'):
    """在文件中定位 needle（bytes）并返回其所在行的原文。"""
    p = os.path.join(GAME, effile, root, fn)
    if not os.path.exists(p):
        return None
    d = rd(p)
    hits = []
    for m in re.finditer(re.escape(needle), d):
        s = d.rfind(b'\n', 0, m.start()) + 1
        e = d.find(b'\n', m.start())
        if e < 0:
            e = len(d)
        line = d[s:e].decode(enc, 'replace')
        hits.append((m.start(), line))
    return hits

print('#' * 70)
print('A. (not used) 定位')
print('#' * 70)
for effile in ['EFILE_NASHORNPBEM', 'EFILE_OLGWW2', 'EFILE_OPENPG']:
    for root in ['TEXT-ZH']:
        h = ctx(effile, root, 'equip.txt', b'(not used)')
        if h:
            print('%-20s %-10s 命中 %d 行' % (effile, root, len(h)))
            for off, line in h[:6]:
                print('    off=%-8d %s' % (off, line[:110]))
print()

print('#' * 70)
print('B. 假汉字装备名 定位（逐文件逐行）')
print('#' * 70)
plan_enc = []
for effile in ['EFILE_NASHORNPBEM', 'EFILE_OLGWW2', 'EFILE_OPENPG']:
    for relroot in ['TEXT-ZH', '.']:
        d0 = os.path.join(GAME, effile, relroot)
        if not os.path.isdir(d0):
            continue
        for fn in ['equip.txt']:
            p = os.path.join(d0, fn)
            if not os.path.exists(p):
                continue
            d = rd(p)
            t = d.decode('gbk', 'replace')
            if not any(ch in t for ch in FAKE):
                continue
            for ln, line in enumerate(t.split('\n'), 1):
                if any(ch in line for ch in FAKE):
                    fixed = ''.join(FAKE.get(c, c) for c in line)
                    plan_enc.append((effile, relroot, fn, ln, line.strip(), fixed.strip()))
                    print('%s\\%s\\%s L%-4d' % (effile, relroot, fn, ln))
                    print('     now : %s' % line.strip()[:110])
                    print('     fix : %s' % fixed.strip()[:110])
print('假汉字行数：', len(plan_enc))
print()

print('#' * 70)
print('C. .xscn 番号串非法字节（Aé）定位')
print('#' * 70)
sys.path.insert(0, os.path.join(ROOT, 'work', 'efile-nashornpbem'))
from apply_residual import parse
plan_xscn = []
for effile in ['EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM']:
    root = os.path.join(GAME, effile, 'SCENARIO')
    for p in sorted(glob.glob(os.path.join(root, '*.xscn'))):
        data, items, meta = parse(p)
        if not items:
            continue
        for gi, idx, voff, vlen in items:
            raw = data[voff + 2:voff + 2 + vlen]
            t = raw.decode('gbk', 'replace')
            if '\ufffd' in t:
                plan_xscn.append((effile, os.path.basename(p), gi, idx, raw, t))
                print('%-16s %-16s g%-2d #%-4d raw=%s  gbk=%s' % (effile, os.path.basename(p), gi, idx, raw, t))
print('xscn 非法串：', len(plan_xscn))
print()

print('#' * 70)
print('D. 希劳德 / Giraud 权威偏离定位')
print('#' * 70)
for effile in ['EFILE_OLGWW2']:
    for p in glob.glob(os.path.join(GAME, effile, '**', '*'), recursive=True):
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext not in ('.txt', '.xscn'):
            continue
        d = rd(p)
        for enc, pat in (('gbk', '希劳德'.encode('gbk')),):
            if pat in d:
                rel = os.path.relpath(p, GAME)
                for ln, line in enumerate(d.decode('gbk', 'replace').split('\n'), 1):
                    if '希劳德' in line:
                        print('  %-52s L%-4d %s' % (rel, ln, line.strip()[:100]))
print()

print('#' * 70)
print('E. 第21装甲（非「师」）定位')
print('#' * 70)
PAT = re.compile('第21装甲(?!师)')
for effile in ['EFILE_OLGWW2']:
    for p in glob.glob(os.path.join(GAME, effile, '**', '*'), recursive=True):
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext not in ('.txt', '.xscn'):
            continue
        d = rd(p)
        try:
            t = d.decode('gbk')
        except Exception:
            t = d.decode('gbk', 'replace')
        for ln, line in enumerate(t.split('\n'), 1):
            if PAT.search(line):
                rel = os.path.relpath(p, GAME)
                print('  %-52s L%-4d %s' % (rel, ln, line.strip()[:100]))
