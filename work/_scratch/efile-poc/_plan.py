# -*- coding: utf-8 -*-
"""NASHORNPBEM 汉化要素全景分析 + 复用映射。"""
import pathlib, re, collections

ROOT = pathlib.Path(r"D:\OpenPG2")
EF = ROOT / "EFILE_NASHORNPBEM"
OUT = pathlib.Path(r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
OUT.mkdir(parents=True, exist_ok=True)

def read_lines(p):
    if not p.exists():
        return None
    return p.read_bytes().decode("gbk", errors="replace").splitlines()

def load_reuse(efile, fname):
    """返回 {原文: 译文}，仅含真实改动的行。"""
    base = ROOT / efile
    a = read_lines(base / fname)
    b = read_lines(base / "TEXT-ZH" / fname)
    if a is None or b is None:
        return {}
    m = {}
    for x, y in zip(a, b):
        if x != y and y.strip():
            m.setdefault(x, y)
    return m

print("=" * 78)
print("### 一、NASHORNPBEM 文件清单")
print("=" * 78)
for p in sorted(EF.rglob("*")):
    if p.is_file():
        rel = p.relative_to(EF).as_posix()
        print(f"  {rel:46s} {p.stat().st_size:8d} B")

print()
print("=" * 78)
print("### 二、逐行可译性分析（根级文本文件）")
print("=" * 78)
FORCE = ("equip.txt", "names.txt", "nations.txt", "strings_efile.txt",
         "TerrainEx.txt", "weather.txt", "colors.txt", "fronts.txt", "efile.xml")
for f in FORCE:
    p = EF / f
    if not p.exists():
        continue
    lines = read_lines(p)
    total = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comment = sum(1 for l in lines if l.strip().startswith(("*", "//")))
    ascii_alpha = sum(1 for l in lines if l.strip() and re.fullmatch(r"[A-Za-z][A-Za-z0-9 .\-\'&/()]*", l.strip()))
    print(f"  {f:20s} 行={total:5d} 空={blank:4d} 注释={comment:4d} 纯英文行={ascii_alpha:4d}")

print()
print("=" * 78)
print("### 三、复用映射（OLGWW2 / OPENPG 已译表）")
print("=" * 78)
plan = {}
for f in ("equip.txt", "names.txt", "nations.txt"):
    lines = read_lines(EF / f) or []
    r1 = load_reuse("EFILE_OLGWW2", f)
    r2 = load_reuse("EFILE_OPENPG", f)
    hit1 = hit2 = miss = 0
    rows = []
    for i, l in enumerate(lines, 1):
        s = l.rstrip("\r")
        if not s.strip() or s.strip().startswith("*"):
            continue
        if s in r1:
            rows.append((s, r1[s], "OLGWW2")); hit1 += 1
        elif s in r2:
            rows.append((s, r2[s], "OPENPG")); hit2 += 1
        else:
            rows.append((s, "", "")); miss += 1
    plan[f] = rows
    print(f"  {f:14s} 待处理行={len(rows):5d}  复用OLGWW2={hit1:4d}  复用OPENPG={hit2:4d}  需新译={miss:4d}")

# 输出工作稿
for f, rows in plan.items():
    o = OUT / (f.replace(".txt", "") + "-orig.tsv")
    with open(o, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("#\t原文\t复用译文\t来源\n")
        for i, (a, b, src) in enumerate(rows, 1):
            fh.write(f"{i}\t{a}\t{b}\t{src}\n")
    print(f"  写出 {o.name}  ({len(rows)} 行)")

# 需新译清单
print()
print("=" * 78)
print("### 四、需新译条目（未命中任何既有译表）")
print("=" * 78)
for f in ("equip.txt", "names.txt", "nations.txt"):
    miss = [(i, a) for i, (a, b, s) in enumerate(plan[f], 1) if not b]
    print(f"\n--- {f}  共 {len(miss)} 条 ---")
    # equip 太长只打印前 40，names/nations 全打印
    lim = 40 if f == "equip.txt" else len(miss)
    for i, a in miss[:lim]:
        print(f"    {i:4d}  {a}")
    if len(miss) > lim:
        print(f"    ...（另 {len(miss)-lim} 条见文件）")
    o = OUT / (f.replace(".txt", "") + "-todo.txt")
    with open(o, "w", encoding="utf-8", newline="\n") as fh:
        for i, a in miss:
            fh.write(f"{a}\n")
