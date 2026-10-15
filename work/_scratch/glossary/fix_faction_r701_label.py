#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阵营视角修正 · 第三批：罗马尼亚战役的**地图标签**随场景阵营。

审计（`faction_audit.py`，已加"同场景 stem 继承"）抓出：
  · `r701_m.txt` 行28（0-based）地图标签「基什尼奥夫」—— 而该场景 `r701_i.txt` 是**罗马尼亚视角**
    （「将军，领袖(Conducator)安东内斯库对你期望很高…」），同战役的 `G7Pzra715` 已用罗方名「基希讷乌」
  ⇒ 地图标签**跟随场景所属阵营**，改为「基希讷乌」。

反证（不该改的）：
  · 德方文本（`DTR3L/GE50V/GE47I/GE48I/DTR14BV`）用「基什尼奥夫」✔ 正确
  · 苏方文本（`RTB31_i.txt`「雅西-基什尼奥夫行动」）用「基什尼奥夫」✔ 正确（苏方即俄方名）

用法: python fix_faction_r701_label.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
TARGETS = [("r701_m.txt", 28)]
OLD, NEW = "基什尼奥夫", "基希讷乌"


def main():
    apply_ = "--apply" in sys.argv
    rows, show = [], []
    for fn, idx in TARGETS:
        en = io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read().split("\n")[idx]
        zh = io.open(os.path.join(GAME, fn), encoding="gbk", errors="replace").read().split("\n")[idx]
        if OLD not in zh:
            print("   ⚠️ %s 行%d 里没有「%s」，跳过" % (fn, idx, OLD))
            continue
        rows.append(("SCENARIO", fn, str(idx), en, zh.replace(OLD, NEW)))
        show.append((fn, idx, en, zh, zh.replace(OLD, NEW)))
    print("=== 追加 per-file 覆盖 %d 条 ===" % len(rows))
    for fn, idx, en, zh, new in show:
        print("   %s 行%d  英文=%r" % (fn, idx, en[:40]))
        print("      旧译 %s → 新译 %s" % (zh[:40], new[:40]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(l.split("\t")[:3]) for l in t.split("\n") if not l.startswith("#")}
    add = [r for r in rows if tuple(r[:3]) not in have]
    os.makedirs(BK, exist_ok=True)
    b = os.path.join(BK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s（新增 %d 条）" % (OVF, len(add)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
