# -*- coding: utf-8 -*-
"""BASEKORP `.xscn` 映射表装配器（三层合并）。

  0. 场景标题人工修正（chunks/zh-title.tsv）         —— 战役序号不得译作番号
  1. 跨 efile 复用（_xscn-crossmap.json）            —— 与已交付 6 个 efile 完全一致
  2. 确定性引擎（det.py：罗马/序数/数字后缀/编制词典）
  3. LLM 分块译文（chunks/zh-*.tsv）                —— 覆盖 2 的残留
优先级：0 > 3 > 1 > 2（标题修正 > LLM 已复核过 draft；跨复用是硬先例）。

产出 work/basekorp/bk-xscn-map.tsv（src<TAB>dst<TAB>note，UTF-8 BOM/CRLF）
"""
import io, os, re, sys, json, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import det

CROSS = os.path.join(HERE, '_xscn-crossmap.json')
OUT = os.path.join(HERE, 'bk-xscn-map.tsv')


def load_llm():
    m = {}
    files = sorted(glob.glob(os.path.join(HERE, 'chunks', 'zh-*.tsv')))
    for fp in files:
        n = 0
        for ln in io.open(fp, encoding='utf-8', newline='').read().split('\r\n'):
            if not ln.strip():
                continue
            c = ln.split('\t')
            if len(c) < 2 or not c[0]:
                continue
            src, dst = c[0], c[1].strip()
            if not dst:
                continue
            m[src] = dst
            n += 1
        print('  %-16s %d' % (os.path.basename(fp), n))
    return m


def load_title():
    m = {}
    fp = os.path.join(HERE, 'chunks', 'zh-title.tsv')
    for ln in io.open(fp, encoding='utf-8', newline='').read().split('\r\n'):
        ln = ln.rstrip('\r')
        if not ln.strip():
            continue
        c = ln.split('\t')
        if len(c) < 2 or not c[0]:
            continue
        m[c[0]] = c[1].strip()
    return m


def main():
    cross = json.load(io.open(CROSS, encoding='utf-8'))
    print('跨 efile 复用 %d' % len(cross))
    llm = load_llm()
    print('LLM 分块合计 %d' % len(llm))
    title = load_title()
    print('标题人工修正 %d' % len(title))

    rows = [l.rstrip('\n').split('\t') for l in
            io.open(os.path.join(HERE, 'bk-xscn-full.tsv'), encoding='utf-8')][1:]
    total = 0
    stat = collections.Counter()
    miss = []
    out = []
    for src, freq, groups, ex in rows:
        key = src.strip()
        total += 1
        if key in title:
            out.append((src, title[key], 'title')); stat['title'] += 1
        elif key in llm:
            out.append((src, llm[key], 'llm')); stat['llm'] += 1
        elif key in cross:
            out.append((src, cross[key], 'cross')); stat['cross'] += 1
        else:
            zh, rs = det.translate(src)
            clean = not any(c.isalpha() and ord(c) < 128
                            for c in re.sub(r'\[[^\]]*\]', '', zh))
            out.append((src, zh, 'det' if clean else 'det-resid'))
            stat['det' if clean else 'det-resid'] += 1
    with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('src\tdst\tnote\r\n')
        for s, d, n in out:
            f.write('%s\t%s\t%s\r\n' % (s, d, n))
    print('\n映射表 %d 条 -> %s' % (len(out), OUT))
    for k in ('title', 'llm', 'cross', 'det', 'det-resid'):
        print('  %-10s %6d  (%.1f%%)' % (k, stat[k], 100.0 * stat[k] / total))


if __name__ == '__main__':
    main()
