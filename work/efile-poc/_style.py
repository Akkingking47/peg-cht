# -*- coding: utf-8 -*-
import pathlib, re
ROOT = pathlib.Path(r"D:\OpenPG2")
def lines(p):
    return p.read_bytes().decode("gbk", errors="replace").splitlines()
for ef in ("EFILE_OLGWW2", "EFILE_OPENPG"):
    a = lines(ROOT / ef / "equip.txt")
    b = lines(ROOT / ef / "TEXT-ZH" / "equip.txt")
    print("=" * 70); print("###", ef, "equip.txt 译法样例"); print("=" * 70)
    pats = [r"^SS[ ]", r"^Pz[ ]", r"Inf$", r"Pioneer", r"Supply", r"^MG", r"FlaK|Flak", r"Cruiser", r"Recon", r"Engineer", r"Artillery|Arty", r"Mortar", r"^FJ "]
    seen = set()
    for x, y in zip(a, b):
        for p in pats:
            if re.search(p, x) and x not in seen:
                seen.add(x)
                print(f"  {x:34s} -> {y}")
                break
    print()
# 国名样式
print("=" * 70); print("### OLGWW2 nations.txt 译法"); print("=" * 70)
a = lines(ROOT / "EFILE_OLGWW2" / "nations.txt")
b = lines(ROOT / "EFILE_OLGWW2" / "TEXT-ZH" / "nations.txt")
for i,(x,y) in enumerate(zip(a,b)):
    if x.strip() and not x.strip().startswith("*") and not x.startswith("*"):
        print(f"  {x:36s} -> {y}")
