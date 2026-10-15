# -*- coding: utf-8 -*-
"""生成「原文乱码 -> UTF-8 真值 -> 中文」三列对照表。

起因：本轮发现部分 efile 的原文文件混用编码 —— 少数条目以 **UTF-8** 存储，
而引擎按**单字节(latin-1/cp1252)**读，于是 `ó`(C3 B3) 被读成 `Ã³` 双字符乱码。
对未汉化的 efile（无 TEXT-ZH\\），这类乱码会**直接在游戏里显示**。

本脚本只读，产出对照清单：
  glossary/glossary-orig-utf8-fix.tsv
字段：efile / file / line / 乱码原样 / UTF-8真值 / ASCII折写 / 中文（已有或空） / 备注
"""
import os, io, glob, csv, unicodedata

GAME = r'D:\OpenPG2'
ROOT = r'D:\DSH\军事游戏汉化'
OUT = os.path.join(ROOT, 'glossary', 'glossary-orig-utf8-fix.tsv')

MANUAL = {'ß': 'ss', 'ø': 'o', 'Ø': 'O', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
          'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ð': 'd', 'Ð': 'D',
          'þ': 'th', 'Þ': 'Th', 'ı': 'i', 'µ': 'u'}
# 上游作者打错的字符（用波兰/捷克字母冒充西语）
TYPO = {'ń': 'ñ', 'Ń': 'Ñ'}


def fold(s):
    o = []
    for ch in s:
        if ch in MANUAL:
            o.append(MANUAL[ch]); continue
        d = ''.join(c for c in unicodedata.normalize('NFKD', ch) if not unicodedata.combining(c))
        o.append(d if d else ch)
    return ''.join(o)


def zh_map(ef, rel):
    """读该 efile 的中文侧同名文件，返回 {行号: 值}。"""
    p = os.path.join(GAME, ef, 'TEXT-ZH', rel)
    if not os.path.exists(p):
        return {}
    try:
        t = io.open(p, encoding='gbk', errors='replace', newline='').read().replace('\r\n', '\n')
    except Exception:
        return {}
    return {i + 1: x.strip() for i, x in enumerate(t.split('\n'))}


recs = []
for ef in sorted(os.listdir(GAME)):
    if not ef.startswith('EFILE_'):
        continue
    fs = [(r, os.path.join(GAME, ef, r)) for r in
          ('equip.txt', 'names.txt', 'nations.txt', 'strings_efile.txt')]
    fs += [('SCENARIO/' + os.path.basename(p), p)
           for p in glob.glob(os.path.join(GAME, ef, 'SCENARIO', '*.txt'))]
    for rel, p in fs:
        if not os.path.exists(p):
            continue
        zh = zh_map(ef, rel)
        raw = open(p, 'rb').read()
        for i, ln in enumerate(raw.replace(b'\r\n', b'\n').split(b'\n')):
            if not any(x >= 0x80 for x in ln):
                continue
            try:
                t = ln.decode('utf-8')
            except Exception:
                continue
            if not any(ord(c) > 127 for c in t):
                continue
            garbled = ln.decode('cp1252', 'replace')
            note = ''
            if any(c in TYPO for c in t):
                note = '上游笔误: ' + ','.join('%s应为%s' % (k, v) for k, v in TYPO.items() if k in t)
            recs.append((ef, rel, i + 1, garbled.strip(), t.strip(), fold(t.strip()),
                         zh.get(i + 1, ''), note))

with io.open(OUT, 'w', encoding='utf-8-sig', newline='\r\n') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\r\n')
    w.writerow(['efile', 'file', 'line', '乱码原样(cp1252读)', 'UTF-8真值', 'ASCII折写', '中文(已有)', '备注'])
    for r in recs:
        w.writerow([str(x).replace('\t', ' ').replace('\n', ' ') for x in r])

print('乱码行 %d -> %s' % (len(recs), OUT))
byef = {}
for r in recs:
    byef.setdefault(r[0], []).append(r)
for k, v in sorted(byef.items()):
    withzh = sum(1 for x in v if x[6])
    print('  %-20s %4d 行，其中中文侧已有译文 %d' % (k, len(v), withzh))
