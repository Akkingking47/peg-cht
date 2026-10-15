# -*- coding: utf-8 -*-
"""原文侧编码普查 v3 —— 用 ASCII 占比判编码，排除排版分隔线，分层统计。

判编码：GBK 中文文本的高位字节占比约 0.3~0.4，而英文/西文原文仅 0.01~0.05。
分隔线：整行由同一非 ASCII 字节（0xAF 等）重复构成的排版线，单独剔除。

输出三类：
  A 根级文件（equip/names/nations/strings_efile）—— 原文侧最确定的一层
  B SCENARIO/*.txt
  C 汇总反推清单（原始串 / 折写 / 语种）

只读。
"""
import os, io, glob, collections, unicodedata

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
BK = os.path.join(ROOT, 'backup')
DONE = {'EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM'}
OUT = os.path.join(ROOT, 'work', 'glossary', 'out-orig-charset.txt')

MANUAL = {'ß': 'ss', 'ø': 'o', 'Ø': 'O', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
          'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ð': 'd', 'Ð': 'D',
          'þ': 'th', 'Þ': 'Th', 'ı': 'i', 'µ': 'u'}
LANGS = [('德', set('äöüÄÖÜß')), ('法', set('éèêëàâçîïôûùœæÉÈÊÀÂÇÎÏÔÛÙ')),
         ('意', set('àèéìòù')), ('西', set('áéíóúñ¿¡')), ('葡', set('ãõçâêôà')),
         ('北欧', set('åøæÅØÆ')), ('东欧', set('čšžłńćęřůý'))]


def fold(s):
    o = []
    for ch in s:
        if ch in MANUAL:
            o.append(MANUAL[ch]); continue
        d = ''.join(c for c in unicodedata.normalize('NFKD', ch) if not unicodedata.combining(c))
        o.append(d if d else ch)
    return ''.join(o)


def lang_of(s):
    return '+'.join(n for n, cs in LANGS if any(c in cs for c in s)) or '?'


def enc_of(d):
    """高位字节占比判编码：>0.15 视为多字节中文，否则单字节原文。"""
    if not d:
        return 'ASCII', 0.0
    hi = sum(1 for x in d if x >= 0x80)
    if not hi:
        return 'ASCII', 0.0
    r = hi / len(d)
    return ('GBK' if r > 0.15 else 'CP1252'), r


def is_ruler(line):
    """整行由同一种非 ASCII 字节重复构成 ⇒ 排版分隔线。"""
    s = line.strip()
    if len(s) < 4:
        return False
    return len(set(s)) <= 2 and all(ord(c) > 127 or c in ' \t-_=*' for c in s)


rowsA, rowsB = [], []
undef = []
srccnt = collections.Counter()     # 文件编码分布
charA, charB = collections.Counter(), collections.Counter()

for ef in sorted(os.listdir(GAME)):
    if not ef.startswith('EFILE_'):
        continue
    base = os.path.join(BK, 'ORIGINAL-' + ef) if ef in DONE else os.path.join(GAME, ef)
    if not os.path.isdir(base):
        continue
    fs = [(0, r, os.path.join(base, r)) for r in
          ('equip.txt', 'names.txt', 'nations.txt', 'strings_efile.txt', 'strings_efile_tips1.txt')]
    fs += [(1, 'SCENARIO/' + os.path.basename(p), p)
           for p in glob.glob(os.path.join(base, 'SCENARIO', '*.txt'))]
    for lv, rel, p in fs:
        if not os.path.exists(p):
            continue
        b = open(p, 'rb').read()
        enc, ratio = enc_of(b)
        srccnt[(ef, lv, enc)] += 1
        if enc == 'ASCII':
            continue
        if enc == 'GBK':
            continue                       # 中文/已汉化，另议
        for i, by in enumerate(b):
            if by in (0x81, 0x8D, 0x8F, 0x90, 0x9D):
                lo = b.rfind(b'\n', 0, i) + 1
                hi2 = b.find(b'\n', i)
                undef.append((ef, rel, b[:i].count(b'\n') + 1, by,
                              b[lo:hi2 if hi2 > 0 else len(b)].decode('cp1252', 'replace')))
        t = b.decode('cp1252')
        for i, line in enumerate(t.replace('\r\n', '\n').split('\n')):
            if not any(ord(c) > 127 for c in line):
                continue
            if is_ruler(line):
                continue
            for c in line:
                if ord(c) > 127:
                    (charA if lv == 0 else charB)[c] += 1
            rec = (ef, rel, i + 1, line.strip(), fold(line.strip()), lang_of(line))
            (rowsA if lv == 0 else rowsB).append(rec)

with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write('# 原文侧编码普查 v3\n# 根级命中 %d 行；SCENARIO 命中 %d 行；真损坏字节 %d 处\n'
            % (len(rowsA), len(rowsB), len(undef)))
    f.write('\n## 0-A 根级文件编码分布\n')
    for (ef, lv, enc), n in sorted(srccnt.items()):
        if lv == 0 and enc != 'ASCII':
            f.write('  %-22s %-7s %d\n' % (ef, enc, n))
    f.write('\n## 0-B SCENARIO 文件编码分布（非 ASCII）\n')
    agg = collections.Counter()
    for (ef, lv, enc), n in srccnt.items():
        if lv == 1 and enc != 'ASCII':
            agg[(ef, enc)] += n
    for (ef, enc), n in sorted(agg.items()):
        f.write('  %-22s %-7s %d\n' % (ef, enc, n))
    if undef:
        f.write('\n## 1 cp1252 未定义字节（真损坏）\n')
        for ef, rel, ln, by, line in undef:
            f.write('  %-22s %-28s L%-5d 0x%02X | %s\n' % (ef, rel, ln, by, line))
    f.write('\n## 2-A 根级非 ASCII 字符频次（%d 种）\n' % len(charA))
    for c, n in charA.most_common():
        f.write('  %s U+%04X %-32s x%d\n' % (c, ord(c), unicodedata.name(c, '?')[:32], n))
    f.write('\n## 2-B SCENARIO 非 ASCII 字符频次（%d 种）\n' % len(charB))
    for c, n in charB.most_common():
        f.write('  %s U+%04X %-32s x%d\n' % (c, ord(c), unicodedata.name(c, '?')[:32], n))
    for tag, rows in (('3-A 根级逐行明细', rowsA), ('3-B SCENARIO 逐行明细', rowsB)):
        f.write('\n## %s\n' % tag)
        cur = None
        for ef, rel, ln, txt, fl, lg in rows:
            if (ef, rel) != cur:
                cur = (ef, rel)
                f.write('\n### %s / %s\n' % (ef, rel))
            f.write('  L%-5d [%s] %s\n' % (ln, lg, txt))
            if fl != txt:
                f.write('        -> %s\n' % fl)

print('根级 %d 行 / SCENARIO %d 行 / 损坏 %d' % (len(rowsA), len(rowsB), len(undef)))
print('根级字符 %d 种，SCENARIO 字符 %d 种' % (len(charA), len(charB)))
print('->', OUT)
