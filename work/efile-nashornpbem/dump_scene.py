# -*- coding: utf-8 -*-
"""并排打印某场景的 .xscn 组0 与 场景 .txt 地名清单（含原始英文对照）。

用法: python dump_scene.py MAO14_2
      python dump_scene.py MAO14_2 -f 0     (只看第 0 段)
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match_txt_names import parse_g0, dec, zh, load_txt, is_unit_line, SCN

ORIG = r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_OLGWW2/SCENARIO"


def load_orig(fn):
    for c in (fn[:-5] + ".txt", fn[:-5].lower() + ".txt"):
        p = os.path.join(ORIG, c)
        if os.path.exists(p):
            return [t.strip() for t in io.open(p, encoding="cp1252", errors="replace").read().splitlines() if t.strip()]
    return None


def main():
    fn = sys.argv[1]
    if not fn.endswith(".xscn"):
        fn += ".xscn"
    cur = [dec(r) for r in parse_g0(os.path.join(SCN, fn))]
    T = [t for t in load_txt(fn) if not is_unit_line(t)]
    O = load_orig(fn)
    Of = [t for t in (O or []) if not is_unit_line(t)]

    print("### %s" % fn)
    print("  xscn 组0: %d 条 | txt地名行: %d 条 | 原始英文地名行: %d 条" % (len(cur), len(T), len(Of)))
    print()
    n = max(len(cur), len(T), len(Of))
    print("%-4s %-30s | %-28s | %s" % ("i", "xscn组0", "txt(中文清单)", "orig(英文清单)"))
    print("-" * 110)
    for i in range(n):
        a = cur[i] if i < len(cur) else ""
        b = T[i] if i < len(T) else ""
        c = Of[i] if i < len(Of) else ""
        mark = ""
        if zh(a) and b and a != b:
            mark = "  <<<"
        print("%-4d %-30s | %-28s | %s%s" % (i, a[:30], b[:28], c[:34], mark))


if __name__ == "__main__":
    main()
