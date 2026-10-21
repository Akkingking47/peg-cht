#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按**已部署**的 `_m.txt` 行0 / 实际 `*.MAP` 重生成场景列表文档（保表结构与组内顺序不动）。

背景：`_场景列表_最终序号.md` 的「显示名」列落后于后续 per-file 覆盖后的部署态（5 处）。
本工具只刷新「显示名」与「地图」两列，不动分组、序号、归属。
用法: python regen_scn_list_doc.py [--apply]     （默认 dry-run，仅打印差异）
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
DIRS = [os.path.join(G, "SCENARIO"), os.path.join(G, "USERSCEN")]
DOC = os.path.join(WS, "pegww2", "research", "_场景列表_最终序号.md")
ROW = re.compile(r"^(\|\s*`[^`]+`\s*\|\s*)([^|]*?)(\s*\|\s*`[^`]+`\s*\|\s*)([^|]*?)(\s*\|)\s*$")


def idx(d):
    return {n.lower(): os.path.join(d, n) for n in os.listdir(d) if os.path.isfile(os.path.join(d, n))}


IDX = {}
for d in DIRS:
    for k, v in idx(d).items():
        IDX.setdefault(k, v)


def l0(name, enc="gbk"):
    p = IDX.get(name.lower())
    if not p:
        return ""
    try:
        ls = io.open(p, encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return ""
    return ls[0].strip() if ls else ""


def mapline(stem):
    p = IDX.get((stem + ".scn").lower())
    if not p:
        return ""
    b = io.open(p, "rb").read()
    ms = sorted({t.decode("latin1").upper()[:-4] for t in re.findall(rb"[ -~]{4,}", b)
                 if t.lower().endswith(b".map")})
    return ms[0] if ms else ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_ = "--apply" in sys.argv
    out, diffs = [], []
    for l in io.open(DOC, encoding="utf-8"):
        m = ROW.match(l.rstrip("\n"))
        if not m:
            out.append(l)
            continue
        stem = re.search(r"`([^`]+)`", m.group(3)).group(1).strip()
        newname, newmap = l0(stem + "_m.txt"), mapline(stem)
        oldname, oldmap = m.group(2).strip(), m.group(4).strip()
        name = newname or oldname
        mp = newmap or oldmap
        if (name, mp) != (oldname, oldmap):
            diffs.append((stem, oldname, name, oldmap, mp))
        out.append(m.group(1) + name + m.group(3) + mp + m.group(5) + "\n")

    print("差异 %d 处：" % len(diffs))
    for d in diffs:
        print("  %-14s 名：%s → %s | 地图：%s → %s" % d)
    if apply_ and diffs:
        io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(out))
        print("已写回 %s" % DOC)
    elif diffs:
        print("(dry-run，未写回；加 --apply 落盘)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
