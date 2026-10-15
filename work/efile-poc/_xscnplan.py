# -*- coding: utf-8 -*-
"""NASHORNPBEM 场景地名复用分析 + 待译清单。"""
import pathlib

W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")
OUT = W / "efile-nashornpbem"

# intro 已确立的地名（必须强制一致）
OVERRIDE = {
    "Dropov": "德罗波夫", "Dropov's": "德罗波夫的",
    "Rostoff": "罗斯托夫", "Slevminska": "斯列夫明斯卡",
    "Vladis": "弗拉迪斯", "Arras": "阿拉斯",
    "Salem": "萨勒姆", "Alvaron": "阿尔瓦隆",
    "Maikop": "迈科普", "Murmansk": "摩尔曼斯克",
    "Labinsk": "拉宾斯基",
}

def load_map(p):
    m = {}
    if not p.exists():
        return m
    for l in p.read_bytes().decode("gbk", errors="replace").splitlines():
        c = l.split("\t")
        if len(c) >= 5 and c[3].strip():
            m.setdefault(c[3], c[4])
    return m

M1 = load_map(W / "xscn-all-map.tsv")
M2 = load_map(W / "xscn-openpg" / "openpg-map.tsv")
print(f"复用源：OLGWW2 {len(M1)} 条 / OPENPG {len(M2)} 条")

rows = []
for l in (OUT / "xscn-orig.tsv").read_bytes().decode("gbk", errors="replace").splitlines():
    if not l.strip():
        continue
    c = l.split("\t")
    if len(c) < 5:
        continue
    rows.append((c[0], c[1], c[2], c[3], c[4]))
print(f"导出条目：{len(rows)}")

hit1 = hit2 = hit3 = miss = 0
out_rows, todo = [], []
for fn, g, i, orig, cur in rows:
    if g == "-1":      # 标题行
        out_rows.append((fn, g, i, orig, orig)); continue
    t = M1.get(orig) or M2.get(orig)
    if t:
        src = "OLGWW2" if M1.get(orig) else "OPENPG"
        hit1 += 1
        out_rows.append((fn, g, i, orig, t))
    else:
        # 词级强制替换（intro 已确立的地名）
        t = orig
        for k, v in OVERRIDE.items():
            if k in t:
                t = t.replace(k, v)
        if t != orig:
            hit3 += 1
            out_rows.append((fn, g, i, orig, t))
        else:
            miss += 1
            out_rows.append((fn, g, i, orig, orig))
            todo.append((fn, g, i, orig))

print(f"复用 OLGWW2/OPENPG={hit1}  词级强制={hit3}  需新译={miss}")

with open(OUT / "xscn-map.tsv", "w", encoding="utf-8", newline="\n") as fh:
    for r in out_rows:
        fh.write("\t".join(r) + "\n")
print(f"写出 xscn-map.tsv（{len(out_rows)} 行）")

with open(OUT / "xscn-todo.tsv", "w", encoding="utf-8", newline="\n") as fh:
    for n, (fn, g, i, orig) in enumerate(todo, 1):
        fh.write(f"{n}\t{orig}\n")
print(f"写出 xscn-todo.tsv（{len(todo)} 条待译）")

print()
print("=== 待译地名（全部）===")
for n, (fn, g, i, orig) in enumerate(todo, 1):
    print(f"  {n:4d}  {orig}")
