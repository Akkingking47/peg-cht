# -*- coding: utf-8 -*-
"""批次 6 出稿辅助：对 freq>=2 待译条目，先用「标准译名库 + 词典」机械取证，
再把「专名+通名」拆开查专名，输出候选表供人工定稿。"""
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
DICT = r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv"

NORM = lambda x: re.sub(r"\s+", " ", x.strip().rstrip(".").lower())
# 通名（POLICY 规则 5）
TYPE_TAIL = {
    "Airfield": "机场", "Air Base": "空军基地", "Forward Air Base": "前进机场",
    "River": "河", "Lake": "湖", "Sea": "海", "Canal": "运河", "Canal ": "运河",
    "Station": "车站", "Sta.": "车站", "Harbour": "港", "Port": "港",
    "Island": "岛", "Mine": "矿", "Mines": "矿", "Oilfields": "油田",
    "Defences": "防御工事", "Defenses": "防御工事", "Fortifications": "要塞",
    "Supply Base": "补给基地", "Base": "基地", "Outpost": "哨所", "Perimeter": "环形防线",
    "Bridge": "桥", "Factory": "工厂", "Work": "工厂", "Works": "工厂",
    "Rail Workshops": "铁路工厂", "Militia": "民兵", "Defense Force": "防卫部队",
}
SUFFIX_HEADS = ["Lake ", "Forward ", "Damaged ", "Destroyed ", "Reserve ", "Outer ", "Old ",
                "New ", "Nizhniy ", "Nizhne-", "Starjy ", "Port ", "Stalag "]


def rd(p):
    out = []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                out.append(c)
    return out


def main():
    G, GN = {}, {}
    for c in rd(GLOSS):
        G.setdefault(c[0].strip(), c[1].strip())
        GN.setdefault(NORM(c[0]), c[1].strip())
    D, DN = {}, {}
    for c in rd(DICT):
        D.setdefault(c[0].strip(), c[1].strip())
        DN.setdefault(NORM(c[0]), c[1].strip())
    print("标准译名库 %d / 词典 %d" % (len(G), len(D)))

    todo = []
    for i, ln in enumerate(io.open(os.path.join(HERE, "_b6_todo.tsv"), encoding="utf-8")):
        if i == 0:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 2 and int(c[1]) >= 2:
            todo.append((c[0], int(c[1])))
    print("freq>=2 待译 %d 条\n" % len(todo))

    exact, norm, comp, none = [], [], [], []
    for s, f in todo:
        d = G.get(s) or D.get(s)
        if d and d != s:
            exact.append((s, d, f)); continue
        n = NORM(s)
        d = GN.get(n) or DN.get(n)
        if d and d != s:
            norm.append((s, d, f)); continue
        # 拆「专名+通名」
        hit = None
        for tail, zh in sorted(TYPE_TAIL.items(), key=lambda x: -len(x[0])):
            if s.endswith(" " + tail) or s.endswith(tail) and len(s) > len(tail):
                head = s[: len(s) - len(tail)].strip()
                if head:
                    hz = G.get(head) or D.get(head) or GN.get(NORM(head)) or DN.get(NORM(head))
                    if hz:
                        hit = (head, hz, tail, zh, hz + zh)
                break
        if hit:
            comp.append((s, hit[4], f, hit[0], hit[1], hit[2]))
            continue
        none.append((s, f))

    def dump(name, arr):
        print("=== %s : %d ===" % (name, len(arr)))
        for x in arr[:400]:
            if name == "组合（专名译名＋通名）":
                s, d, f, h, hz, t = x
                print("   %-32s -> %-22s (由 %s=%s + %s=%s)" % (s[:32], d, h, hz, t, ""))
            else:
                print("   %-32s -> %-24s x%d" % (x[0][:32], x[1][:24], x[2]))
        print()
    dump("精确命中", exact)
    dump("归一化命中", norm)
    dump("组合（专名译名＋通名）", comp)
    print("=== 完全未命中 : %d ===" % len(none))
    for s, f in none:
        print("   %-34s x%d" % (s[:34], f))

    with io.open(os.path.join(HERE, "_b6_probe.tsv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("kind\tsrc\tdst\tfreq\n")
        for s, d, f in exact:
            fh.write("exact\t%s\t%s\t%d\n" % (s, d, f))
        for s, d, f in norm:
            fh.write("norm\t%s\t%s\t%d\n" % (s, d, f))
        for s, d, f, h, hz, t in comp:
            fh.write("comp\t%s\t%s\t%d\n" % (s, d, f))
        for s, f in none:
            fh.write("none\t%s\t\t%d\n" % (s, f))
    print("\n已写 _b6_probe.tsv")


if __name__ == "__main__":
    main()
