# -*- coding: utf-8 -*-
"""BASEKORP `.xscn` 跨 efile 复用词典构建器。

原理：已交付 efile 的 `.xscn` 是**原地改**的 ——
  * 原文英文：backup/ORIGINAL-EFILE_<E>/SCENARIO/*.xscn
  * 当前中文：D:/OpenPG2/EFILE_<E>/SCENARIO/*.xscn
两边按 (文件, 标题槽, 组号, 组内序号) 对齐即得到 英→中 对译。

只收「中文侧含汉字且英中不同」的条目；同一英文有多个中文译法时**按出现次数投票**，
若票数相同则按 efile 优先级取（ATOMIC > AO > AG > OLGWW2 > OPENPG > NASHORNPBEM）。

产出：work/basekorp/_xscn-crossmap.json（UTF-8，{src: dst}）
用法：python build_crossmap.py
"""
import io, os, sys, json, collections

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'xscn'))
import xscn as X

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_xscn-crossmap.json')

# 优先级从高到低
EFILES = ['ATOMIC', 'AO', 'AG', 'OLGWW2', 'OPENPG', 'NASHORNPBEM']
PRIO = {e: i for i, e in enumerate(EFILES)}


def han(s):
    return sum(1 for c in s if '\u4e00' <= c <= '\u9fff')


def slots(path):
    """返回 [(key, text)]，key=(gi, idx)，标题用 gi=-1。"""
    data, items, meta = X.parse(path)
    if meta is None:
        return []
    out = []
    for (gi, idx, off, L) in X.slots_of(data, items, meta):
        raw = X.raw_at(data, off, L)
        enc, s = X.decode(raw)
        out.append(((gi, idx), s))
    return out


def main():
    votes = collections.defaultdict(collections.Counter)
    prio = {}
    for ef in EFILES:
        c = X.Ctx(ef)
        if not os.path.isdir(c.bak):
            print('SKIP (无备份): %s' % ef)
            continue
        n = 0
        for fn in c.files():
            po = os.path.join(c.bak, fn)
            pg = os.path.join(c.game, fn)
            if not os.path.exists(po) or not os.path.exists(pg):
                continue
            so, sg = slots(po), slots(pg)
            if len(so) != len(sg):
                continue
            for (ko, to), (kg, tg) in zip(so, sg):
                if ko != kg:
                    continue
                a, b = to.strip(), tg.strip()
                if not a or not b or a == b:
                    continue
                if han(b) == 0:
                    continue
                votes[a][b] += 1
                if a not in prio or PRIO[ef] < prio[a]:
                    prio[a] = PRIO[ef]
                n += 1
        print('%-12s 对齐对 %d' % (ef, n))

    m = {}
    for a, cnt in votes.items():
        best = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        m[a] = best
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=0)
    print('\n跨 efile 复用词典 %d 条 -> %s' % (len(m), OUT))

    # 冲突报告
    amb = {a: dict(c) for a, c in votes.items() if len(c) > 1}
    if amb:
        p = os.path.join(HERE, '_xscn-crossmap-conflicts.json')
        with io.open(p, 'w', encoding='utf-8') as f:
            json.dump(amb, f, ensure_ascii=False, indent=1)
        print('⚠️ 一词多译 %d 条 -> %s' % (len(amb), p))


if __name__ == '__main__':
    main()
