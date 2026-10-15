#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**齐步译 · 部队番号（第一批：美第101空降师家族）**

依据（用户 2026-10-12「2.齐步译」）：
  · 项目**已有**同类译法：`1/A/321st GFAB/101st` → 「第1营/A连/第321滑翔野战炮兵营/空降第101师」；
    `33 Pio/15 Pz/[DAK]` → 「第33工兵营/第15装甲师/[非洲军]」；
    但 `A/I/327th GIR/101st` 家族却登记为"保留" ⇒ **口径不一致**，本批补齐。
  · **段级词典**（仅本家族，避免"同码不同部队"的风险）：
      `327th GIR`→第327滑翔步兵团 · `502nd`→第502伞降步兵团 · `501st`→第501伞降步兵团
      `101st`→第101空降师 · `USAAF`→美国陆军航空队
      连字母 `A`–`K`→`X连`；罗马营号 `I/II/III`→`X营`；纯数字段（兵力/编号）**原样保留**
  · 只动**含本家族记号**的行；其余番号（同码不同部队）**不动**，另批处理。

用法: python fix_roster_us.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BK = r"D:\DSH\军事游戏汉化\pegww2\testbed\backup"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
CBK = os.path.join(WS, "backup", "before-roster-us")
CJK = re.compile(r"[\u4e00-\u9fff]")
FAM = re.compile(r"(?i)(327th GIR|502nd|501st|101st|USAAF)")
SEG = {"327th GIR": "第327滑翔步兵团", "502nd": "第502伞降步兵团", "501st": "第501伞降步兵团",
       "101st": "第101空降师", "USAAF": "美国陆军航空队"}
CO = set("ABCDEFGHIJK") | {"I", "II", "III"}


def tr(s):
    out = []
    for part in s.split("/"):
        p = part.strip()
        if not p:
            continue
        if p in SEG:
            out.append(SEG[p])
        elif p in CO:
            out.append(p + ("营" if p in ("I", "II", "III") else "连"))
        else:
            out.append(p)                      # 纯数字/其它段原样保留
    return "/".join(out)


def main():
    apply_ = "--apply" in sys.argv
    rows = []
    for d in ("SCENARIO", "USERSCEN"):
        p = os.path.join(GAME, d)
        if not os.path.isdir(p):
            continue
        for fn in sorted(os.listdir(p)):
            if not fn.lower().endswith(".txt"):
                continue
            t = io.open(os.path.join(p, fn), encoding="gbk", errors="replace").read().split("\n")
            for i, l in enumerate(t):
                s = l.strip()
                if not s or CJK.search(s) or not FAM.search(s):
                    continue
                nt = tr(s)
                if nt == s:
                    continue
                bp = os.path.join(BK, d, fn)
                src = io.open(bp, encoding="cp1252", errors="replace").read().split("\n") if os.path.isfile(bp) else t
                if i >= len(src):
                    continue
                rows.append((d, fn, i, src[i].rstrip("\r\n"), nt))
    print("=== 待落 %d 条（%d 个文件）===" % (len(rows), len({r[1] for r in rows})))
    seen = set()
    for d, fn, i, en, nt in rows[:18]:
        p = os.path.join(d, fn)
        print("   %-22s 行%-4d %-28s → %s" % (fn, i + 1, en[:28], nt[:44]))
    if len(rows) > 18:
        print("   …（其余 %d 条）" % (len(rows) - 18))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(l.split("\t")[:3]) for l in t.split("\n") if not l.startswith("#")}
    add = [r for r in rows if (r[0], r[1], str(r[2])) not in have]
    os.makedirs(CBK, exist_ok=True)
    bk = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(bk):
        shutil.copy2(OVF, bk)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join((r[0], r[1], str(r[2]), r[3], r[4])) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已追加 %d 条到 per-file 覆盖表" % len(add))
    return 0


if __name__ == "__main__":
    sys.exit(main())
