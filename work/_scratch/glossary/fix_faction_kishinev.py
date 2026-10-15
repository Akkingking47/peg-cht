#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**阵营视角修正**（用户 2026-10-12 约定）：罗马尼亚视角文本里的城市名用**罗方名**。

依据：`glossary/阵营视角-约定.md` —— 同一事物按"这段文本是谁在说话"取名字。
实证（`work/glossary/faction_audit.py` 抓出）：
  · `G7Pzra715_i.txt` **自身不一致**：名栏「基什尼奥夫」(俄方名) vs 正文「基希讷乌」(罗方名)
  · `Kv-R.TXT` 名栏与正文都用俄方名「基什尼奥夫」
⇒ 罗马尼亚视角的这两份文本统一用 **基希讷乌**(Chişinău)；`Kishinev`(俄/苏方名) 留给德/苏方文本。

用法: python fix_faction_kishinev.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "backup", "before-faction-fix")

ROWS = [
    ("SCENARIO", "G7Pzra715_i.txt", "0", "Kishinev", "基希讷乌"),
    ("SCENARIO", "Kv-R.TXT", "0", "Kishinev", "基希讷乌"),
    ("SCENARIO", "Kv-R.TXT", "5", "to capture the Soviet controlled city of Kishinev.",
     "以夺取苏联控制的基希讷乌(Kishinev)城。"),
]


def main():
    apply_ = "--apply" in sys.argv
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(l.split("\t")[:3]) for l in t.split("\n") if not l.startswith("#")}
    add = [r for r in ROWS if tuple(r[:3]) not in have]
    print("=== 追加 per-file 覆盖 %d 条 / 共 %d 条 ===" % (len(add), len(ROWS)))
    for d, f, no, en, zh in add:
        print("   %s/%s 行%s  原文=%s ⇒ %s" % (d, f, no, en[:44], zh[:40]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    os.makedirs(BK, exist_ok=True)
    b = os.path.join(BK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s（备份 %s）" % (OVF, b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
