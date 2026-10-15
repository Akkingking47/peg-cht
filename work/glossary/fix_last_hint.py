#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾 · 最后一处提示：`RM_usvsruss15b.txt` 行1 用**登记全称**替代简称。

背景：该行原为德方代号「堡垒」攻势，我按用户裁决（苏方文本用苏方战法名）改成「库尔斯克」攻势；
但登记表里苏方名是**全称**「库尔斯克会战」⇒ 审计持续提示。
⚠️ 曾试把简称「库尔斯克」也登记为苏方作战名 ⇒ 引发 9 处假阳（它是**地名**，别方文本提到它就误报）⇒ 已撤回。
正解：把这行改成**含全称**的写法（「库尔斯克会战」(Zitadelle)已耗尽自身！），语义通顺且与登记一致。

用法: python fix_last_hint.py [--apply]
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-last-hint")
FN, IDX = "RM_usvsruss15b.txt", 0
OLD, NEW = "「库尔斯克」(Zitadelle)攻势", "「库尔斯克会战」(Zitadelle)"


def main():
    apply_ = "--apply" in sys.argv
    zh = io.open(os.path.join(GAME, FN), encoding="gbk", errors="replace").read().split("\n")
    cur = zh[IDX]
    if OLD not in cur:
        print("   ⚠️ 未见「%s」，现值：%s" % (OLD, cur[:70]))
        return 1
    new = cur.replace(OLD, NEW)
    en = io.open(os.path.join(BK, FN), encoding="cp1252", errors="replace").read().split("\n")[IDX]
    print("   行%d\n     旧: %s\n     新: %s" % (IDX + 1, cur[:80], new[:80]))
    if not apply_:
        print("\n（dry-run；加 --apply）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(x.split("\t")[:3]) for x in t.split("\n") if not x.startswith("#")}
    if ("SCENARIO", FN, str(IDX)) in have:
        print("   （覆盖表已有该行，改为替换其译文）")
        out = []
        for l in t.split("\n"):
            c = l.split("\t")
            if len(c) >= 5 and (c[0], c[1], c[2]) == ("SCENARIO", FN, str(IDX)):
                l = "\t".join(("SCENARIO", FN, str(IDX), en.rstrip("\r\n"), new))
            out.append(l)
        t = "\n".join(out)
    else:
        if not t.endswith("\n"):
            t += "\n"
        t += "\t".join(("SCENARIO", FN, str(IDX), en.rstrip("\r\n"), new)) + "\n"
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s" % OVF)
    return 0


if __name__ == "__main__":
    sys.exit(main())
