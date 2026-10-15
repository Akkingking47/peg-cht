# -*- coding: utf-8 -*-
import pathlib
ROOT = pathlib.Path(r"D:\OpenPG2")
base = ROOT / "EFILE_OLGWW2"

for name in ("names.txt", "equip.txt"):
    o = base / name
    z = base / "TEXT-ZH" / name
    ob = o.read_bytes(); zb = z.read_bytes()
    print("=" * 60)
    print(name, "orig", len(ob), "zh", len(zb))
    # 编码探测
    for lbl, b in (("orig", ob), ("zh", zb)):
        head = b[:200]
        print(f"  {lbl} 前 200 字节: {head[:80]!r}")
    a = ob.decode("gbk", errors="replace").splitlines()
    c = zb.decode("gbk", errors="replace").splitlines()
    print("  行数", len(a), len(c))
    diffs = [(i, a[i], c[i]) for i in range(min(len(a), len(c))) if a[i] != c[i]]
    print("  差异行数:", len(diffs))
    for i, x, y in diffs[:5]:
        print(f"    L{i+1}: {x!r} -> {y!r}")
    print("  非 ASCII 行数(zh):", sum(1 for l in c if any(ord(ch) > 127 for ch in l)))
