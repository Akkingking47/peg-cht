#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读：定位残留（库里 / 初代）到底落在哪些文件的哪些行。"""
import os

WS = r"D:\DSH\军事游戏汉化"
DIRS = [
    ("PeG 生成产物", os.path.join(WS, "peg", "testbed", "scn-zh")),
    ("PeG 游戏目录", r"D:\Program Files\PeG"),
    ("WW2 生成产物", os.path.join(WS, "pegww2", "testbed", "out")),
    ("WW2 游戏目录", r"D:\Program Files\PeG-WW2"),
]
# (关键词, 需排除的更长词)
CASES = [("库里", "库里纳河"), ("初代", None)]

for label, root in DIRS:
    if not os.path.isdir(root):
        continue
    print(f"\n########## {label}  ({root})")
    for needle, excl in CASES:
        rows = []
        for dp, _dn, fns in os.walk(root):
            for fn in fns:
                p = os.path.join(dp, fn)
                try:
                    t = open(p, "rb").read().decode("gbk", errors="replace")
                except OSError:
                    continue
                if needle not in t:
                    continue
                for i, ln in enumerate(t.splitlines(), 1):
                    if needle not in ln:
                        continue
                    if excl and ln.replace(excl, "") .find(needle) < 0:
                        continue          # 只由排除词贡献 ⇒ 跳过
                    rows.append((os.path.relpath(p, root).replace("\\", "/"), i, ln.strip()[:90]))
        print(f"  ── {needle}：真残留 {len(rows)} 行")
        for rel, i, ln in rows[:25]:
            print(f"     {rel}:{i}  {ln!r}")
        if len(rows) > 25:
            print(f"     … 另 {len(rows)-25} 行")
