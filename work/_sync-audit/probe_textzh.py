#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探明 EFILE_OLGWW2 / EFILE_OPENPEG 里 `SCENARIO` 与 `TEXT-ZH\\SCENARIO` 的关系（只读）。

问：TEXT-ZH 是中文侧镜像，还是**英文原文**备份？（.txt 与 .xscn 可能不同！）
"""
import collections
import io
import os
import sys

GAME = r'D:\OpenPG2'
sys.path.insert(0, r'D:\DSH\军事游戏汉化\work\efile-nashornpbem')
from apply_residual import parse  # noqa: E402


def count_by_ext(d):
    c = collections.Counter()
    if not os.path.isdir(d):
        return c
    for fn in os.listdir(d):
        p = os.path.join(d, fn)
        if os.path.isfile(p):
            c[os.path.splitext(fn)[1].lower()] += 1
    return c


def slot(path, gk):
    data, items, meta = parse(path)
    for g, k, off, ln in items:
        if (g, k) == gk:
            raw = data[off + 2:off + 2 + ln]
            out = {}
            for enc in ('gbk', 'cp1252'):
                try:
                    out[enc] = raw.decode(enc)
                except Exception as e:
                    out[enc] = '<%s>' % e
            return out
    return None


for efile in ('EFILE_OLGWW2', 'EFILE_OPENPEG'):
    print('=' * 20, efile)
    for sub in ('SCENARIO', os.path.join('TEXT-ZH', 'SCENARIO')):
        d = os.path.join(GAME, efile, sub)
        print('  %-22s %s' % (sub, dict(count_by_ext(d)) if os.path.isdir(d) else 'MISSING'))
    for fn in ('equip.txt', 'names.txt', 'nations.txt', 'strings_efile.txt'):
        for sub in ('', 'TEXT-ZH'):
            p = os.path.join(GAME, efile, sub, fn)
            if os.path.isfile(p):
                raw = open(p, 'rb').read()
                txt = None
                for enc in ('gbk', 'cp1252'):
                    try:
                        txt = raw.decode(enc)
                        break
                    except Exception:
                        pass
                line = (txt or '').replace('\r\n', '\n').split('\n')[:1]
                n_cjk = sum(1 for ch in (txt or '') if '\u4e00' <= ch <= '\u9fff')
                print('  %-12s %-8s %8d B  汉字 %6d  首行: %s' %
                      (fn, sub or '(root)', len(raw), n_cjk, (line[0] if line else '')[:60] if line else ''))

    # .xscn 对称抽查
    for fn, gk in (('18days11.xscn', (1, 153)), ('18days0l.txt', None)):
        if gk:
            a = os.path.join(GAME, efile, 'SCENARIO', fn)
            b = os.path.join(GAME, efile, 'TEXT-ZH', 'SCENARIO', fn)
            for tag, p in (('SCENARIO', a), ('TEXT-ZH', b)):
                if os.path.isfile(p):
                    s = slot(p, gk)
                    print('  [xscn %s] %s %s  g%d#%d' % (fn, tag, os.path.getsize(p), gk[0], gk[1]))
                    for enc, v in (s or {}).items():
                        print('        %-7s %s' % (enc, (v or '')[:90]))
        else:
            a = os.path.join(GAME, efile, 'SCENARIO', fn)
            b = os.path.join(GAME, efile, 'TEXT-ZH', 'SCENARIO', fn)
            for tag, p in (('SCENARIO', a), ('TEXT-ZH', b)):
                if os.path.isfile(p):
                    raw = open(p, 'rb').read()
                    same = '同' if (os.path.isfile(a) and os.path.isfile(b) and
                                    open(a, 'rb').read() == raw) else '异'
                    print('  [txt %s] %s %d B (%s)' % (fn, tag, len(raw), same))
