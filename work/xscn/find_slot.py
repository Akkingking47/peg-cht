# -*- coding: utf-8 -*-
r"""查某个残槽串在某个 efile `.xscn` 里的上下文（同组前后各 N 条），用于判定该条性质。

用法: python find_slot.py --efile ATOMIC --sub 32Para [--ctx 6] [--all]
      --sub 可给多次；--all 打印全部命中（默认每组最多 2 处）。
"""
import importlib.util
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"D:\OpenPG2"
spec = importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(xscn)
except SystemExit:
    pass


def main():
    a = sys.argv
    if "--efile" not in a or "--sub" not in a:
        print(__doc__)
        return 2
    EF = xscn.norm_efile(a[a.index("--efile") + 1])
    subs = [a[i + 1] for i, x in enumerate(a) if x == "--sub"]
    ctx = int(a[a.index("--ctx") + 1]) if "--ctx" in a else 5
    showall = "--all" in a
    D = os.path.join(GAME, EF, "SCENARIO")
    for sub in subs:
        sb = sub.encode("cp1252", "replace")
        print("=== %s : %r ===" % (EF, sub))
        n = 0
        for fn in sorted(os.listdir(D)):
            if not fn.lower().endswith(".xscn"):
                continue
            data, items, meta = xscn.parse(os.path.join(D, fn))
            if items is None:
                continue
            slots = xscn.slots_of(data, items, meta)
            for i, (gi, idx, off, L) in enumerate(slots):
                raw = xscn.raw_at(data, off, L)
                if sb not in raw:
                    continue
                n += 1
                print("  [%s g%d.%d] 命中: %r" % (fn, gi, idx, raw.decode("cp1252", "replace")))
                for j in range(max(0, i - ctx), min(len(slots), i + ctx + 1)):
                    g2, i2, o2, L2 = slots[j]
                    mark = " <<<" if j == i else ""
                    print("      %-10s %r%s" % ("g%d.%d" % (g2, i2),
                          xscn.raw_at(data, o2, L2).decode("cp1252", "replace"), mark))
                if not showall and n >= 2:
                    break
            if not showall and n >= 2:
                break
        if n == 0:
            print("  （未命中）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
