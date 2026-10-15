# -*- coding: utf-8 -*-
"""梳理 DOCS 层：投放成品逐个体检（旧译法/番号残留/未译）"""
import io, os, re, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = r'D:\Program Files\PeG-WW2\DOCS'
WS = r'D:\DSH\军事游戏汉化'
CJK = re.compile(r'[\u4e00-\u9fff]')
ABBR = re.compile(r'\b(\d{1,3}(?:st|nd|rd|th))\s+'
                  r'(GIR|PIR|AB|AIR|Armd|Cav|Inf|Bde|Div|Para|SS|Pz|Gd|Mot|Mech|Rgt|Bn|Kav|Ski|Mtn|Mar|Eng|Sig|Recon|TD|AT)\b')
RULE = [('声望', '威望'), ('海军攻击', '对海杀伤'), ('空中出击', '空中任务'),
        ('前进观测官', '炮兵观测/前沿观测'), ('光荣胜利', '辉煌胜利'), ('国力', '威望'),
        ('武装攻击', '硬目标杀伤'), ('非武装攻击', '软目标杀伤')]

files = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        p = os.path.join(dp, f)
        if os.path.getsize(p) < 40:
            continue
        files.append(p)
print('DOCS 树共 %d 个非空文件' % len(files))
zh_files = 0
tot = collections.Counter()
detail = []
for p in files:
    raw = io.open(p, 'rb').read()
    txt = None
    for enc in ('utf-8-sig', 'gbk', 'latin-1'):
        try:
            t = raw.decode(enc)
            if CJK.search(t):
                txt = t
                break
        except Exception:
            pass
    if txt is None:
        continue
    zh_files += 1
    rel = p.replace(ROOT + os.sep, '')
    a = ABBR.findall(txt)
    r = [(b, g) for b, g in RULE if b in txt]
    if a or r:
        detail.append((rel, a[:5], r[:5]))
    tot['ab'] += len(a)
    tot['ru'] += len(r)
print('含中文成品 %d 个 · 番号残留 %d · 旧译法 %d' % (zh_files, tot['ab'], tot['ru']))
print()
for rel, a, r in detail:
    print('◆ %s' % rel)
    for x in a:
        print('    番号: %s' % ' '.join(x))
    for b, g in r:
        print('    旧译: %s → %s' % (b, g))
