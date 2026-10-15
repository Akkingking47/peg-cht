#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**OpenPG2 前作汉化 · 单位名体检**（用户 2026-10-12 指出"有很多乱码没完全翻译的单位名"）。

判据（逐行，原文 cp1252 ↔ 汉化 GBK）：
  `变音剥离`  汉化行 == 原文行把变音字母换成 ASCII 基字（ó→o、ä→a、ü→u、ß→s…）  ← **本次主发现**
  `残留乱码`  汉化行的 **GBK 字节按 cp1252 解**能还原出拉丁词（cp1252 原文被搬进 GBK 文件）
  `未译`      汉化行 == 原文行（排除 `VERSION:`/`Error!` 版本头）
  `部分译`    中文里还夹着长拉丁串
  `已译`      其余

用法: python survey_openpg_units.py
"""
import collections
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
G = r"D:\OpenPG2"
BK = r"D:\DSH\军事游戏汉化\backup"
EVID = r"D:\DSH\军事游戏汉化\glossary\evidence"
ACC = "áàâäãåéèêëíìîïóòôöõúùûüñçøæœÁÀÂÄÉÈÊËÍÎÏÓÒÔÖÚÙÛÜÑÇ"
BASE = str.maketrans("áàâäãåéèêëíìîïóòôöõúùûüñçøæœÁÀÂÄÉÈÊËÍÎÏÓÒÔÖÚÙÛÜÑÇ",
                     "aaaaaaeeeeiiiiooooouuuuncsoaeoAAAAEEEEIIIOOOUUUNC")
CJK = re.compile(r"[\u4e00-\u9fff]")
LATRUN = re.compile(r"[A-Za-z][A-Za-z'\-\.]{7,}")
HEAD = re.compile(r"(?i)(VERSION\s*:|Error!|^#)")
FILENAME = None


def latinish(s):
    """GBK 字节按 cp1252 解，是否"像拉丁词"（字母占比高）⇒ 判 cp1252 残留。"""
    if not s.strip():
        return False
    try:
        back = s.encode("gbk", "replace").decode("cp1252", "replace")
    except Exception:
        return False
    letters = sum(1 for c in back if c.isascii() and c.isalpha())
    return letters >= 0.6 * max(1, len(back.strip())) and letters >= 3


def classify(a, z):
    if not z.strip():
        return None
    if HEAD.search(a.strip()) and HEAD.search(z.strip()):
        return "表头"
    # ① 纯 ASCII 行：只可能是"未译"（**不能**判残留乱码——ASCII 的 GBK 字节按 cp1252 解当然还是字母）
    if a.strip() and z.strip() == a.strip():
        return "未译"
    # ② 变音剥离：原文把变音换成 ASCII 基字
    if a.strip() and z.strip() == a.strip().translate(BASE) and z.strip() != a.strip():
        return "变音剥离"
    # ③ 残留乱码：汉化行**含非 ASCII**，且其 GBK 字节按 cp1252 解能还原成拉丁词
    if not z.isascii() and LATRUN.match(z.strip()) and latinish(z) and a.strip() and not CJK.search(a):
        return "残留乱码"
    if CJK.search(z) and LATRUN.search(z):
        return "部分译"
    return "已译"


def scan(ef, fn):
    zhp = os.path.join(G, ef, "TEXT-ZH", fn)
    enp = os.path.join(BK, "ORIGINAL-" + ef, fn)
    if not os.path.isfile(zhp):
        return None
    zh = io.open(zhp, encoding="gbk", errors="replace").read().split("\n")
    en = io.open(enp, encoding="cp1252", errors="replace").read().split("\n") if os.path.isfile(enp) else None
    if en is None:
        return None
    c, rows = collections.Counter(), []
    for i, z in enumerate(zh):
        if not z.strip() or i >= len(en):
            continue
        a = en[i]
        k = classify(a, z)
        if k is None:
            continue
        c[k] += 1
        if k in ("变音剥离", "残留乱码", "部分译"):
            rows.append((k, ef, fn, i, a, z))
    return c, rows


def main():
    allrows = []
    tot = collections.Counter()
    for fn in ("equip.txt", "names.txt"):
        print("=== %s ===" % fn)
        print("%-22s %7s %9s %8s %7s %7s" % ("EFILE", "行", "变音剥离", "残留乱码", "未译", "部分译"))
        print("-" * 68)
        sub = collections.Counter()
        for ef in sorted(os.listdir(G)):
            if not ef.startswith("EFILE_"):
                continue
            r = scan(ef, fn)
            if not r:
                continue
            c, rows = r
            allrows += rows
            print("%-22s %7d %9d %8d %7d %7d" % (ef, sum(c.values()), c["变音剥离"], c["残留乱码"], c["未译"], c["部分译"]))
            for k in ("变音剥离", "残留乱码", "未译", "部分译", "已译"):
                sub[k] += c[k]
        print("-" * 68)
        print("%-22s %7d %9d %8d %7d %7d" % ("小计", sum(sub.values()), sub["变音剥离"], sub["残留乱码"], sub["未译"], sub["部分译"]))
        print()
        for k in sub:
            tot[k + "|" + fn] += sub[k]

    print("=== 变音剥离样例（每个 EFILE 至多 3 条）===")
    seen = collections.Counter()
    for k, ef, fn, i, a, z in allrows:
        if k == "变音剥离" and seen[ef] < 3:
            seen[ef] += 1
            print("   %-18s %-10s 行%-5d %-32s → %s" % (ef, fn, i, a[:32], z[:32]))
    print("\n=== 残留乱码样例 ===")
    for k, ef, fn, i, a, z in [r for r in allrows if r[0] == "残留乱码"][:10]:
        print("   %-18s %-10s 行%-5d 原文=%r 汉化=%r" % (ef, fn, i, a[:30], z[:30]))
    os.makedirs(EVID, exist_ok=True)
    with io.open(os.path.join(EVID, "openpg-unit-audit.txt"), "w", encoding="utf-8", newline="\n") as w:
        w.write("# OpenPG2 前作 · 单位名体检（变音剥离 / 残留乱码 / 部分译）\n")
        w.write("类\tEFILE\t文件\t行号\t原文\t汉化\n")
        for k, ef, fn, i, a, z in allrows:
            w.write("%s\t%s\t%s\t%d\t%s\t%s\n" % (k, ef, fn, i, a, z))
    print("\n报告 → glossary/evidence/openpg-unit-audit.txt（%d 行）" % len(allrows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
