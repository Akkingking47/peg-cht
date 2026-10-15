#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按史料审计报告**自动落 per-file 覆盖**（通用工具，可反复用）。

输入：`glossary/evidence/faction-place-audit.txt`（faction_place_audit.py 产出）
规则：只取 `地名` 类、且"现用名"能在该行里找到的行 ⇒ 用「史称」替换；
      期望原文取**备份**（原件）同一行；行号 1-based → 覆盖表 0-based。
跳过：`作战` 类（需人工判断措辞）与已修过的行。

用法: python fix_from_audit.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
REP = os.path.join(WS, "glossary", "evidence", "faction-place-audit.txt")
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-audit-fix")


def main():
    apply_ = "--apply" in sys.argv
    rows, skip = [], 0
    for l in io.open(REP, encoding="utf-8"):
        if l.startswith("#") or l.startswith("类\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 7 or c[0] != "地名":
            continue
        _cls, fn, no, _pid, used, _side, want = c[0], c[1], c[2], c[3], c[4], c[5], c[6]
        want = want.split("|")[0]
        if not used or not want or used == want:
            skip += 1
            continue
        idx = int(no) - 1
        p = os.path.join(GAME, fn)
        if not os.path.isfile(p):
            continue
        zh = io.open(p, encoding="gbk", errors="replace").read().split("\n")
        if idx >= len(zh) or used not in zh[idx]:
            skip += 1
            continue
        bp = os.path.join(BK, fn)
        if not os.path.isfile(bp):
            print("   ⚠️ 无备份 %s" % fn)
            continue
        en = io.open(bp, encoding="cp1252", errors="replace").read().split("\n")[idx]
        rows.append(("SCENARIO", fn, str(idx), en.rstrip("\n"), zh[idx].replace(used, want)))
    print("=== 待落 %d 条（跳过 %d）===" % (len(rows), skip))
    for d, fn, idx, en, nt in rows[:14]:
        print("   %-22s 行%-4d → %s" % (fn, int(idx) + 1, nt.strip()[:52]))
    if len(rows) > 14:
        print("   …（其余 %d 条）" % (len(rows) - 14))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(x.split("\t")[:3]) for x in t.split("\n") if not x.startswith("#")}
    add = [r for r in rows if (r[0], r[1], r[2]) not in have]
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已追加 %d 条" % len(add))
    return 0


if __name__ == "__main__":
    sys.exit(main())
