# -*- coding: utf-8 -*-
"""生成「原文侧 cp1252 变音符」反推对照表。

起因（本类乱码的真实机制）：
  原文侧是 **cp1252 单字节**（`é`=0xE9、`ä`=0xE4、`ü`=0xFC…）。
  用中文工具（GBK）打开时，0xE9 0x67 会被当成一个 GBK 汉字 `間` ⇒ `Légion` 显示成 `L間ion`。
  这不是"文件坏了"，按 cp1252/latin-1 解码即得真值。

输出 glossary/glossary-orig-charset-fix.tsv：
  efile / file / line / GBK误读 / cp1252真值 / ASCII折写 / 语种 / 有效侧
其中「有效侧」：原文侧文件在游戏里是否被读取（已汉化 efile 的根文件由 TEXT-ZH 覆盖）。
只读。
"""
import os, io, glob, csv, collections, unicodedata

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
BK = os.path.join(ROOT, 'backup')
DONE = {'EFILE_OLGWW2', 'EFILE_OPENPG', 'EFILE_NASHORNPBEM'}
OUT = os.path.join(ROOT, 'glossary', 'glossary-orig-charset-fix.tsv')

MANUAL = {'ß': 'ss', 'ø': 'o', 'Ø': 'O', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
          'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ð': 'd', 'Ð': 'D',
          'þ': 'th', 'Þ': 'Th', 'ı': 'i', 'µ': 'u'}
LANGS = [('德', set('äöüÄÖÜß')), ('法', set('éèêëàâçîïôûùœæÉÈÊÀÂÇÎÏÔÛÙ')),
         ('西', set('áéíóúñÁÉÍÓÚÑ¿¡')), ('意', set('àèéìòùÀÈÉÌÒÙ')),
         ('葡', set('ãõÃÕ')), ('北欧', set('åøæÅØÆ')), ('匈牙利', set('őűŐŰ')),
         ('波兰', set('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ')), ('捷克', set('čšžřěůýČŠŽŘĚŮÝ')),
         ('土耳其', set('ğışĞİŞ'))]


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


recs = []
for ef in sorted(os.listdir(GAME)):
    if not ef.startswith('EFILE_'):
        continue
    base = os.path.join(BK, 'ORIGINAL-' + ef) if ef in DONE else os.path.join(GAME, ef)
    if not os.path.isdir(base):
        continue
    fs = [(r, os.path.join(base, r)) for r in
          ('equip.txt', 'names.txt', 'nations.txt', 'strings_efile.txt')]
    fs += [('SCENARIO/' + os.path.basename(p), p)
           for p in glob.glob(os.path.join(base, 'SCENARIO', '*.txt'))]
    for rel, p in fs:
        if not os.path.isfile(p):
            continue
        raw = open(p, 'rb').read()
        if not any(x >= 0x80 for x in raw):
            continue
        for i, ln in enumerate(raw.replace(b'\r\n', b'\n').split(b'\n')):
            if not any(x >= 0x80 for x in ln):
                continue
            t = ln.decode('cp1252', 'replace')
            if not any(ord(c) > 127 and c.isalpha() for c in t):
                continue                       # 纯符号行（分隔线等）不算变音符
            garbled = ln.decode('gbk', 'replace')
            # 只有 GBK 读出来确实"歪"了才记（真值里的变音符在 GBK 下变成汉字/其它）
            if garbled == t:
                continue
            recs.append((ef, rel, i + 1, garbled.strip(), t.strip(), fold(t.strip()),
                         lang_of(t), 'TEXT-ZH 覆盖' if ef in DONE else '生效'))

with io.open(OUT, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\r\n')
    w.writerow(['efile', 'file', 'line', 'GBK误读', 'cp1252真值', 'ASCII折写', '语种', '有效侧'])
    for r in recs:
        w.writerow([str(x).replace('\t', ' ').replace('\n', ' ') for x in r])

print('对照行 %d -> %s' % (len(recs), OUT))
byef = collections.Counter(r[0] for r in recs)
print('\n按 efile:')
for k, v in byef.most_common():
    eff = '已汉化(原文侧不生效)' if k in DONE else '★未汉化(原文侧生效)'
    print('  %-22s %4d  %s' % (k, v, eff))
lg = collections.Counter(r[6] for r in recs)
print('\n按语种:', dict(lg.most_common(12)))
