# -*- coding: utf-8 -*-
"""EFILE_ATOMIC `.xscn` 映射表装配器。

合并来源（优先级从低到高，后者覆盖前者）：
  1. 跨 efile 复用（_xscn-crossmap.json，来自 AG/AO/OPENPG/OLGWW2/NASHORNPBEM 已交付件的原→中）
  2. 本层 20 片新译文（work/atomic/zh/part-01..20.tsv）

产出：work/atomic/atomic-xscn-map.tsv（src<TAB>dst<TAB>note，UTF-8 BOM）
用法：python build_map.py
"""
import io, os, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ZH = os.path.join(HERE, 'zh')
CROSS = os.path.join(HERE, '_xscn-crossmap.json')
OUT = os.path.join(HERE, 'atomic-xscn-map.tsv')


def main():
    cross = json.load(io.open(CROSS, encoding='utf-8'))
    m = collections.OrderedDict()
    for k, v in cross.items():
        m[k] = (v, 'cross')

    npart = 0
    for i in range(1, 21):
        p = os.path.join(ZH, 'part-%02d.tsv' % i)
        if not os.path.exists(p):
            print('MISS part', p); continue
        npart += 1
        for ln in io.open(p, encoding='utf-8', newline='').read().split('\r\n'):
            if not ln.strip():
                continue
            c = ln.split('\t')
            if len(c) < 2 or not c[0]:
                continue
            src, dst = c[0], c[1]
            if dst.strip() == src.strip():
                continue          # 保留原文 -> 不写入映射（无变化）
            m[src] = (dst, 'atomic')

    with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('src\tdst\tnote\r\n')
        for k, (v, src) in m.items():
            f.write('%s\t%s\t%s\r\n' % (k, v, src))
    print('映射表 %d 条（跨复用 %d + 本层 %d）-> %s'
          % (len(m), len(cross), sum(1 for v, s in m.values() if s == 'atomic'), OUT))


if __name__ == '__main__':
    main()
