# -*- coding: utf-8 -*-
"""只读字符串清单提取：ASCII / UTF-16LE，按节统计，输出 TSV。"""
import struct, sys, re, os, collections
from pe_probe import PE

PRINT = set(range(0x20, 0x7f))


def runs(d, lo, hi, minlen=3):
    out = []
    i = lo
    while i < hi:
        if d[i] in PRINT or d[i] in (9,):
            j = i
            while j < hi and (d[j] in PRINT or d[j] == 9):
                j += 1
            if j - i >= minlen:
                out.append((i, d[i:j].decode('latin1')))
            i = j
        else:
            i += 1
    return out


def runs16(d, lo, hi, minlen=3):
    out = []
    i = lo
    while i + 1 < hi:
        ok = (d[i] in PRINT and d[i + 1] == 0)
        if ok:
            j = i
            buf = []
            while j + 1 < hi and d[j] in PRINT and d[j + 1] == 0:
                buf.append(chr(d[j]))
                j += 2
            if len(buf) >= minlen:
                out.append((i, ''.join(buf)))
            i = j
        else:
            i += 2 if d[i] == 0 and i + 1 < hi and d[i + 1] == 0 else 1
    return out


def main(path, outdir):
    p = PE(path)
    base = os.path.basename(path)
    stats = {}
    allstr = []
    for s in p.sections:
        if s['name'] in ('.rsrc', '.reloc'):
            continue
        lo, hi = s['roff'], s['roff'] + s['rsize']
        a = runs(p.d, lo, hi)
        w = runs16(p.d, lo, hi)
        stats[s['name']] = (len(a), len(w))
        for off, t in a:
            allstr.append((s['name'], off, 'A', t))
        for off, t in w:
            allstr.append((s['name'], off, 'W', t))
    print('%-10s %8s %8s' % ('节', 'ASCII', 'UTF16'))
    for k, v in stats.items():
        print('%-10s %8d %8d' % (k, v[0], v[1]))
    tot_a = sum(1 for x in allstr if x[2] == 'A')
    tot_w = sum(1 for x in allstr if x[2] == 'W')
    print('合计 ASCII=%d  UTF16=%d' % (tot_a, tot_w))

    # 文件名类
    fn = [t for _, _, _, t in allstr if re.search(r'\.(bmp|bit|wav|ogg|dat|txt|scn|map|org|hlp|ini|ply|pdx|pdt|scl|exe)$', t, re.I)]
    print('文件名串: %d，去重 %d' % (len(fn), len(set(x.lower() for x in fn))))
    ext = collections.Counter(os.path.splitext(t)[1].lower() for t in fn)
    print('  ', dict(ext.most_common(15)))

    # 人类可读文本（含空格或长度>=6 的字母串）
    human = [t for _, _, _, t in allstr if (' ' in t and re.search(r'[A-Za-z]{3}', t)) or len(t) >= 14]
    print('候选可译文本串(含空格/较长): %d' % len(human))

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, base + '.strings.tsv'), 'w', encoding='utf-8') as f:
        f.write('sec\toff\tkind\ttext\n')
        for sec, off, kind, t in allstr:
            f.write('%s\t%X\t%s\t%s\n' % (sec, off, kind, t.replace('\t', ' ')))
    print('已写:', os.path.join(outdir, base + '.strings.tsv'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'out')
