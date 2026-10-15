# -*- coding: utf-8 -*-
"""重新生成 NASHORNPBEM 场景地名待译清单（全部条目，弃用词级替换）。"""
import pathlib
W = pathlib.Path(r"D:\DSH\军事游戏汉化\work")
OUT = W / "efile-nashornpbem"

rows = []
for l in (OUT / "xscn-orig.tsv").read_bytes().decode("gbk", errors="replace").splitlines():
    if not l.strip():
        continue
    c = l.split("\t")
    if len(c) >= 5 and c[1] != "-1":     # 排除标题行
        rows.append((c[3], c[4]))

with open(OUT / "xscn-todo.tsv", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("#\t原文\n")
    for n, (orig, _) in enumerate(rows, 1):
        fh.write(f"{n}\t{orig}\n")

print(f"待译地名：{len(rows)} 条")
# 去重统计
uniq = len(set(o for o, _ in rows))
print(f"其中唯一：{uniq} 条")
print()
print("=== 前 10 条 ===")
for n, (o, _) in enumerate(rows[:10], 1):
    print(f"  {n:4d}  [{o}]")
# 检查独特字符
import re
weird = sorted({o for o, _ in rows if re.search(r'["\']', o)})
print()
print(f"=== 含引号/撇号的条目 ({len(weird)}) ===")
for o in weird:
    print(f"  [{o}]")
trail = sorted({o for o, _ in rows if o != o.rstrip()})
print()
print(f"=== 含尾随空格的条目 ({len(trail)}) ===")
for o in trail:
    print(f"  [{o}]")
