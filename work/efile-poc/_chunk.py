# -*- coding: utf-8 -*-
"""生成 NASHORNPBEM 翻译分块。编号 = 文件行号(1-based)，便于回填。"""
import pathlib

ROOT = pathlib.Path(r"D:\OpenPG2")
EF = ROOT / "EFILE_NASHORNPBEM"
OUT = pathlib.Path(r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")

def lines(p):
    return p.read_bytes().decode("gbk", errors="replace").splitlines()

def reuse(efile, fname):
    a = lines(ROOT / efile / fname)
    b = lines(ROOT / efile / "TEXT-ZH" / fname)
    m = {}
    for x, y in zip(a, b):
        if x != y and y.strip():
            m.setdefault(x, y)
    return m

def chunk(items, n):
    k = (len(items) + n - 1) // n
    return [items[i * k:(i + 1) * k] for i in range(n)]

report = []
# --- equip / names / nations ---
for fname, nblk in (("equip.txt", 3), ("names.txt", 3), ("nations.txt", 1)):
    src = lines(EF / fname)
    r1 = reuse("EFILE_OLGWW2", fname)
    r2 = reuse("EFILE_OPENPG", fname)
    todo = []
    reuse_cnt = 0
    for i, l in enumerate(src, 1):
        s = l.rstrip("\r")
        if not s.strip() or s.strip().startswith("*"):
            continue
        if s in r1 or s in r2:
            reuse_cnt += 1
            continue
        todo.append((i, s))
    if fname == "nations.txt":
        # 与 strings_efile 合并成 1 块，前缀 N
        out = OUT / "ui-blk1.tsv"
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            for ln, s in todo:
                fh.write(f"N{ln}\t{s}\n")
        report.append((out.name, len(todo), f"nations.txt（复用 {reuse_cnt}）"))
    else:
        blks = chunk(todo, nblk)
        tag = "equip" if fname.startswith("equip") else "names"
        for bi, blk in enumerate(blks, 1):
            out = OUT / f"{tag}-blk{bi}.tsv"
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                for ln, s in blk:
                    fh.write(f"{ln}\t{s}\n")
            report.append((out.name, len(blk), f"{fname} 第 {bi}/{len(blks)} 块（复用 {reuse_cnt}）"))

# --- strings_efile.txt：追加到 ui-blk1 ---
src = lines(EF / "strings_efile.txt")
todo = []
for i, l in enumerate(src, 1):
    s = l.rstrip("\r")
    if not s.strip() or s.strip().startswith("*") or s.strip().startswith("["):
        continue
    todo.append((i, s))
out = OUT / "ui-blk1.tsv"
with open(out, "a", encoding="utf-8", newline="\n") as fh:
    for ln, s in todo:
        fh.write(f"S{ln}\t{s}\n")
for r in report:
    if r[0] == "ui-blk1.tsv":
        report[report.index(r)] = (r[0], r[1] + len(todo), r[2] + f" + strings_efile.txt({len(todo)})")
        break

# --- 场景介绍 intro.txt ---
src = lines(EF / "SCENARIO" / "utopianparadoxintro.txt")
out = OUT / "intro-blk1.tsv"
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    n = 0
    for i, l in enumerate(src, 1):
        s = l.rstrip("\r")
        if not s.strip():
            continue
        fh.write(f"{i}\t{s}\n"); n += 1
report.append((out.name, n, "utopianparadoxintro.txt 全文"))

print("=" * 72)
print("生成的分块：")
for name, n, note in report:
    print(f"  {name:16s} {n:5d} 条   {note}")
print()
print("=== 各分块前 3 行预览 ===")
for name, n, note in report:
    p = OUT / name
    ls = p.read_text(encoding="utf-8").splitlines()
    print(f"\n-- {name} ({len(ls)} 行) --")
    for l in ls[:3]:
        print("   ", l)
