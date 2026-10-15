#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 PeG 的经验定位「描述框显示成地图格名列表」：

PeG 实证：开局简报由 `.SCN@11329`（stem）+ `.SCN@11349`（位置/扩展名标志）**共同**决定：
    @11349 = 0 ⇒ `SCENARIO\\<stem>.TXT`
    @11349 = 1 ⇒ `USERSCEN\\<stem>.PLY`
文件不存在时引擎会**回退**（本项目表现为展示 `_m.txt` 的地名列表）。
"""
import os
import re

G = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(G, "SCENARIO")
USR = os.path.join(G, "USERSCEN")


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def main():
    rows = []
    for fn in sorted(os.listdir(SCN)):
        if not fn.lower().endswith(".scn"):
            continue
        stem = fn[:-4]
        b = open(os.path.join(SCN, fn), "rb").read()
        if len(b) < 11350:
            continue
        intro = fld(b, 11329)
        flag = b[11349]
        # 引擎按 flag 决定去哪找
        if flag == 1:
            want_dir, want_name = USR, intro + ".ply"
        else:
            want_dir, want_name = SCN, intro + ".TXT"
        cands = [want_name, want_name.lower(), want_name.upper(), want_name.title()]
        found = [c for c in cands if os.path.isfile(os.path.join(want_dir, c))]
        rows.append((stem, intro, flag, want_dir, want_name, bool(found), found[:1]))
    miss = [r for r in rows if not r[5]]
    print(f".scn 共 {len(rows)} 个 · 引擎要读的说明文件**缺失** {len(miss)} 个")
    print("=" * 100)
    for stem, intro, flag, d, n, ok, f in miss:
        print(f"  {stem:16s} @11329={intro!r:14s} @11349={flag} ⇒ 需 {'USERSCEN' if flag else 'SCENARIO'}/{n}")
    print()
    print("已具备说明文件的：", len(rows) - len(miss))
    print()
    print("=== 抽样：有 flag=1 的场景 ===")
    for stem, intro, flag, d, n, ok, f in rows:
        if flag == 1:
            print(f"  {stem:16s} @11329={intro!r} 需 {os.path.basename(d)}/{n}  {'✅' if ok else '❌ 缺'}")


if __name__ == "__main__":
    main()
