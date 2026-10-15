#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一「本体 vs ': Redux'」的译法：Redux 必须 = 本体译法 + 「：重制版」。

用户实测：同一战役本体译「北风」、重制版译「北风行动：重制版」；或本体「维堡」、Redux「维普里」。
另修：`：重制`（漏「版」字）⇒ `：重制版`。
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
OUT = os.path.join(RES, "_scn-fill-redux-consist.tsv")


def main():
    rows, mp = [], {}
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows.append(f)
            if f[1].strip():
                mp[f[0]] = f[1]
    fixes = []
    # ① 所有 : Redux 键 ⇒ 本体译法 + ：重制版
    for k, v in mp.items():
        if not k.endswith(": Redux"):
            continue
        base = k[:-7].strip()
        if base not in mp:
            continue
        want = mp[base].rstrip("：: ") + "：重制版"
        if v.strip() != want:
            fixes.append((k, want, f"对齐本体「{mp[base][:20]}」"))
    # ② 任何译法里漏「版」的「：重制」
    for r in rows:
        if len(r) >= 2 and r[1].strip() and re.search(r"：重制(?!版)", r[1]):
            nv = re.sub(r"：重制(?!版)", "：重制版", r[1])
            if all(k != r[0] for k, _, _ in fixes):
                fixes.append((r[0], nv, "补「版」字"))
    seen = {}
    for k, v, why in fixes:
        seen[k] = (v, why)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# 「：重制版」体例统一（{len(seen)} 条）\n原文\t译文\t说明\n")
        for k, (v, why) in seen.items():
            f.write(f"{k}\t{v}\t{why}\n")
    print(f"待修正 {len(seen)} 条 → {os.path.relpath(OUT, WS)}")
    for k, (v, why) in list(seen.items())[:16]:
        print(f"  {k[:44]:46s} → {v[:26]:28s} （{why}）")


if __name__ == "__main__":
    main()
