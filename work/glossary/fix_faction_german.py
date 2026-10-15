#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""阵营视角修正 · 第二批（德方文本误用罗方名）。

审计（`work/glossary/faction_audit.py`）抓出：
   · `DTR3L.TXT` / `GE50V.TXT`：德方文本（`Herr General, Kishinev is secure…`）
     却用罗方名「基希讷乌」⇒ 按约定（德方称 Kischinew）应为「基什尼奥夫」。

做法：登记 per-file 覆盖（期望原文＝英文原件该行，译文＝现中文行替换该名），
      随后由 `gen_scn.py build` + `deploy_scn.py --apply` 落地。

用法: python fix_faction_german.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
FILES = [("DTR3L.TXT", 0), ("GE50V.TXT", 0)]
OLD, NEW = "基希讷乌", "基什尼奥夫"


def main():
    apply_ = "--apply" in sys.argv
    rows, show = [], []
    for fn, idx in FILES:
        en = io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read().split("\n")[idx]
        zh = io.open(os.path.join(GAME, fn), encoding="gbk", errors="replace").read().split("\n")[idx]
        if OLD not in zh:
            print("   ⚠️ %s 行%d 里没有「%s」，跳过" % (fn, idx, OLD))
            continue
        new = zh.replace(OLD, NEW)
        rows.append(("SCENARIO", fn, str(idx), en, new))
        show.append((fn, idx, en, zh, new))
    print("=== 追加 per-file 覆盖 %d 条 ===" % len(rows))
    for fn, idx, en, zh, new in show:
        print("   %s 行%d" % (fn, idx))
        print("      原文: %s" % en[:80])
        print("      旧译: %s" % zh[:80])
        print("      新译: %s" % new[:80])
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
