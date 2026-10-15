# -*- coding: utf-8 -*-
"""对比 OLGWW2 / OPENPG 的 TEXT-ZH 与原文，得出 efile 汉化要素清单。"""
import pathlib

ROOT = pathlib.Path(r"D:\OpenPG2")

def read_lines(p):
    try:
        return p.read_text(encoding="gbk", errors="replace").splitlines()
    except Exception:
        return None

def diff_report(efile):
    base = ROOT / efile
    tz = base / "TEXT-ZH"
    print("=" * 70)
    print(f"### {efile}")
    print("=" * 70)
    if not tz.is_dir():
        print("  无 TEXT-ZH")
        return
    # 根级文件
    for f in sorted(tz.iterdir()):
        if f.is_dir():
            continue
        orig = base / f.name
        a = read_lines(orig) if orig.exists() else None
        b = read_lines(f)
        if a is None:
            print(f"  [根] {f.name:22s} 原文缺失，译文 {len(b)} 行")
            continue
        n = min(len(a), len(b))
        changed = sum(1 for i in range(n) if a[i] != b[i])
        print(f"  [根] {f.name:22s} orig={len(a):5d} zh={len(b):5d} 行数{'一致' if len(a)==len(b) else '★不一致'} 改动={changed}")
    # SCENARIO
    sc = tz / "SCENARIO"
    if sc.is_dir():
        files = list(sc.iterdir())
        exts = {}
        for f in files:
            e = f.suffix.lower()
            exts[e] = exts.get(e, 0) + 1
        # 抽样几个 txt 对比
        tot_changed = 0
        txts = [f for f in files if f.suffix.lower() == ".txt"]
        for f in txts:
            orig = base / "SCENARIO" / f.name
            if not orig.exists():
                continue
            a = read_lines(orig); b = read_lines(f)
            if a is None or b is None: continue
            if a != b:
                tot_changed += 1
        print(f"  [SCN] 副本共 {len(files)} 个，扩展名分布: {exts}")
        print(f"  [SCN] .txt 中与 SCENARIO 原文不同的: {tot_changed}/{len(txts)}")

for e in ("EFILE_OLGWW2", "EFILE_OPENPG"):
    diff_report(e)

print()
print("=" * 70)
print("### NASHORNPBEM 与 OLGWW2 的 equip/names/nations 重合度")
print("=" * 70)
nash = ROOT / "EFILE_NASHORNPBEM"
olg = ROOT / "EFILE_OLGWW2"
def load_set(p, skip_comment=True):
    s = set()
    for ln in read_lines(p) or []:
        ln = ln.strip()
        if not ln: continue
        if skip_comment and ln.startswith("*"): continue
        s.add(ln)
    return s

for f in ("equip.txt", "names.txt", "nations.txt"):
    a = load_set(nash / f)
    b = load_set(olg / f)
    inter = a & b
    print(f"  {f:16s} NASH={len(a):5d}  OLGWW2={len(b):5d}  交集={len(inter):5d}  重合率={len(inter)/max(1,len(a))*100:.1f}%")
