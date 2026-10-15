#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**番号第二批 · 提案校验并并入 per-file 覆盖表**（串行步骤的第一半）。

输入：
  `pegww2/research/_番号第二批-提案.tsv`（子代理交付，303 行）
  `work/glossary/_番号第二批-提案-补充.tsv`（captain 裁决补充）
  列：子目录 / 文件 / 行号(0-based) / 期望原文 / 拟译 / 依据

并入前**逐条硬校验**（任一不过即拒收并打印原因）：
  ① 行号是数字 ② 备份与成品都确有该文件 ③ 行号在界内
  ④ 期望原文 == 备份该行（去尾部控制字符后一致）——防**行号错位**
  ⑤ 拟译非空、无 `\r\n\t`、**GBK 可编码**、 != 原文（真译了）
  ⑥ 该行成品**仍"未译"**（不含汉字）——防**覆盖已译**
  ⑦ 同 (子目录,文件,行号) 已有登记则跳过

用法: python merge_roster_batch2.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
PROP = os.path.join(WS, "pegww2", "research", "_番号第二批-提案.tsv")
SUPP = os.path.join(WS, "work", "glossary", "_番号第二批-提案-补充.tsv")
SUPP2 = os.path.join(WS, "work", "glossary", "_番号第二批-提案-补充2.tsv")
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup")
GAME = r"D:\Program Files\PeG-WW2"
CBK = os.path.join(WS, "backup", "before-roster2")
CJK = re.compile(r"[\u4e00-\u9fff]")


def check(sub, fn, no, en, zh):
    """返回 (ok_bool, 原因/结果行)。"""
    if not no.isdigit():
        return False, "行号非数字"
    bp, gp = os.path.join(BK, sub, fn), os.path.join(GAME, sub, fn)
    if not os.path.isfile(bp):
        return False, "备份缺此文件"
    if not os.path.isfile(gp):
        return False, "成品缺此文件"
    idx = int(no)
    src = io.open(bp, encoding="cp1252", errors="replace").read().split("\n")
    cur = io.open(gp, encoding="gbk", errors="replace").read().split("\n")
    if idx >= len(src) or idx >= len(cur):
        return False, "行号越界（备份 %d 行 / 成品 %d 行）" % (len(src), len(cur))
    a = src[idx].rstrip("\r\n").rstrip("\x00")
    if a.rstrip() != en.rstrip():
        return False, "期望原文与备份不符：备份=%r" % a[:40]
    if not zh.strip():
        return False, "拟译为空"
    if any(ch in zh for ch in ("\r", "\n", "\t")):
        return False, "拟译含控制字符"
    try:
        zh.encode("gbk")
    except UnicodeEncodeError as e:
        return False, "GBK 不可编码：%s" % e
    if zh.strip() == en.strip():
        return False, "拟译==原文（未译，no-op）"
    # ⑥ 防覆盖已译：把成品该行的**汉字/全角标点去掉**，应仍含"待译的拉丁片段"。
    #    ⚠️ 不能用"该行不含汉字"当判据——半译行（如「利摩日FTP」）含汉字但**FTP 仍未译**，
    #       正是要补译的对象；用"拉丁片段是否仍在"才精确。
    latin_only = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", "", cur[idx])
    toks = re.findall(r"[A-Za-z][A-Za-z0-9\.\-]*", en)
    # ⚠️ 判据是"**任一片段仍未译**"而非"最长片段"：`Limoge FTP` 里 Limoge 已作「利摩日」、
    #    FTP 仍未译 ⇒ 该行正是要补译的对象（取最长片段会误拒）。
    if toks and not any(t in latin_only for t in toks):
        return False, "该行各拉丁片段均已译（疑已译）：%r" % cur[idx][:30]
    return True, a


def main():
    apply_ = "--apply" in sys.argv
    srcs = [p for p in (PROP, SUPP, SUPP2) if os.path.isfile(p)]
    if not srcs:
        print("❌ 没有提案文件")
        return 1
    print("读入：%s" % " · ".join(os.path.basename(p) for p in srcs))
    ok, bad = [], []
    for path in srcs:
        for i, l in enumerate(io.open(path, encoding="utf-8"), 1):
            if l.startswith("#") or not l.strip():
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) < 5:
                bad.append((os.path.basename(path), i, "列数不足 %d" % len(c), l.strip()[:40]))
                continue
            good, info = check(c[0].strip(), c[1].strip(), c[2].strip(), c[3], c[4])
            if good:
                ok.append((c[0].strip(), c[1].strip(), c[2].strip(), info, c[4]))
            else:
                bad.append((os.path.basename(path), i, info, "%s|%s|%s" % (c[1], c[2], c[3][:24])))
    print("=== 校验：通过 %d 条 · 拒收 %d 条 ===" % (len(ok), len(bad)))
    for p, i, w, ctx in bad[:24]:
        print("   拒收 %s 行%d：%s  ← %s" % (p, i, w, ctx))
    if len(bad) > 24:
        print("   …（其余 %d 条）" % (len(bad) - 24))
    if not apply_:
        print("\n（dry-run；加 --apply 并入）")
        return 0
    t = io.open(OVF, encoding="utf-8").read()
    have = {tuple(x.split("\t")[:3]) for x in t.split("\n") if not x.startswith("#")}
    add = [r for r in ok if (r[0], r[1], r[2]) not in have]
    print("并入 %d 条（跳过已存在 %d 条）" % (len(add), len(ok) - len(add)))
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not t.endswith("\n"):
            t += "\n"
        t += "".join("\t".join(r) + "\n" for r in add)
        io.open(OVF, "w", encoding="utf-8", newline="\n").write(t)
    print("✅ 已写 %s" % OVF)
    return 0


if __name__ == "__main__":
    sys.exit(main())
