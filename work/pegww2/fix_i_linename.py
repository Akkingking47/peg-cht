#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复战役选择画面战役名异常：
  A. 日期当名（12个）：行0=纯日期，战役名在行2 ⇒ 交换，行0=战役名
  B. 散文当名（9个）：行0=散文无战役名 ⇒ 从 _m.txt 行0取战役名插入行0

修改 backup 原文（gen_scn 从 backup 读），原文件存为 .broken-orig。
用法: python fix_i_linename.py [--apply]
"""
import io, os, re, shutil, sys

BK = r"d:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
SCN = r"D:\Program Files\PeG-WW2\SCENARIO"
LOG = r"d:\DSH\军事游戏汉化\pegww2\research\_战役名修复-20261020.tsv"

# A. 日期前置型：(文件, 战役名所在行号)
DATE_CASES = [
    ("ATM_scn01_i.txt", 2), ("ATM_scn02_i.txt", 2), ("ATM_scn04_i.txt", 2),
    ("ATM_scn05_i.txt", 2), ("ATM_scn06_i.txt", 2), ("ATM_scn07_i.txt", 2),
    ("ATM_scn08_i.txt", 2), ("ATM_scn09_i.txt", 2), ("ATM_scn10_i.txt", 2),
    ("ATM_scn11_i.txt", 2), ("ATM_scn14_i.txt", 2), ("ZS_woronez_i.txt", 2),
]
# B. 散文起首型：(文件, 英文战役名，从 _m 行0/游戏目录反查)
PROSE_CASES = [
    ("RM_usvsruss1_i.txt", "Windsor"),
    ("RM_usvsruss4_i.txt", "Volturno (#17v)"),
    ("RM_usvsruss6_i.txt", "Riga (RTB#24)"),
    ("RM_usvsruss15_i.txt", "Holding the line"),
    ("RM_usvsruss17_i.txt", "Italy Coast"),
    ("RM_usvsruss18_i.txt", "Kalatsch (#1)"),
    ("RG_usvsruss15_i.txt", "Holding the line"),
    ("wddday_i.txt", "D-Day+2"),
    ("wdarde_i.txt", "Ardennes-The Bulge"),
]

def rd(p):
    return io.open(p, encoding="gbk", errors="replace").read().splitlines()

def wr(p, lines):
    with io.open(p, "w", encoding="gbk", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    apply_ = "--apply" in sys.argv
    rows = []
    print(f"{'[APPLY]' if apply_ else '[DRY-RUN]'} 修改目录: {BK}\n")

    # A. 日期前置型
    print("=== A. 日期当名 → 战役名上移 ===")
    for fname, name_line in DATE_CASES:
        p = os.path.join(BK, fname)
        if not os.path.isfile(p):
            print(f"  ❌ {fname} 不存在于 backup"); continue
        ls = rd(p)
        if len(ls) <= name_line:
            print(f"  ⚠ {fname} 行数不足"); continue
        date = ls[0].strip()
        cname = ls[name_line].strip()
        if not re.match(r"\s*\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4}\s*$", date):
            print(f"  ⚠ {fname} 行0不是日期: {date[:30]}"); continue
        # 新结构：行0=战役名, 行1=日期, 行2=空, 行3+=原行3+
        new = [cname, date, ""] + ls[name_line+1:]
        rows.append(("A", fname, ls[0][:30], cname))
        print(f"  {fname}: '{date}' → '{cname}'")
        if apply_:
            arc = p + ".broken-orig"
            if not os.path.isfile(arc):
                shutil.copy2(p, arc)
            wr(p, new)

    # B. 散文起首型
    print("\n=== B. 散文当名 → 插入指定英文战役名 ===")
    for fname, cname in PROSE_CASES:
        p = os.path.join(BK, fname)
        if not os.path.isfile(p):
            print(f"  ❌ {fname} 不存在于 backup"); continue
        ls = rd(p)
        # 新结构：行0=英文战役名, 行1=空, 行2+=原文
        new = [cname, ""] + ls
        rows.append(("B", fname, ls[0][:30], cname))
        print(f"  {fname}: 插入 '{cname}'")
        if apply_:
            arc = p + ".broken-orig"
            if not os.path.isfile(arc):
                shutil.copy2(p, arc)
            wr(p, new)

    if rows:
        head = not os.path.isfile(LOG)
        with io.open(LOG, "a", encoding="utf-8", newline="\n") as f:
            if head:
                f.write("# 战役选择画面战役名修复（_i.txt 行0）\n类型\t文件\t原行0\t新行0\n")
            for r in rows:
                f.write("\t".join(r) + "\n")
        print(f"\n→ 留痕: {LOG}")
    print(f"\n共 {len(rows)} 项 {'已应用' if apply_ else '（dry-run）'}")

if __name__ == "__main__":
    main()
