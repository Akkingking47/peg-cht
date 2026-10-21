#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段3 场景层：建**译法真源工作表**（值模式，整行直出）。

为什么用「整行精确匹配」而不是「行内子串替换」：
  前作踩过「内嵌替换误伤」的坑（`Type 05-I Taliban` 只替换行内 Taliban ⇒ 括号里只剩 (Taliban)）。
  ⇒ 本作 v1 只做**整行精确匹配**：译文按「整行」登记，未命中即原样保留（绝不局部改写）。

产出：
  pegww2/research/ww2-scn-map.tsv    原文(整行) \t 译文 \t 来源
  pegww2/research/_scn-stats.tsv     原文 \t 类 \t 出现文件数 \t 出现次数   （规划用，不参与生成）
排除：说明/自述类文件（info.txt / *ReadMe* / *REPORT*）与 `.ply`（定长 501B，另案处理）
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsv_esc import esc  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改）
PEGR = os.path.join(WS, "peg", "research")
OUTMAP = os.path.join(RES, "ww2-scn-map.tsv")
OUTSTAT = os.path.join(DER, "_scn-stats.tsv")
os.makedirs(DER, exist_ok=True)
_sink = io.StringIO()

EXCLUDE = re.compile(r"(?i)(^info\.txt$|read ?me|report)")
CLASSES = [("_m.txt", "m 地图格名"), ("_u.txt", "u 部队名"), ("_i.txt", "i 战役内简报"),
           ("_cb.txt", "cb 战役内简报"), ("_bv.txt", "bv 大胜评述"), ("_tv.txt", "tv 战术胜评述"),
           ("_l.txt", "l 败报"), ("_v.txt", "v 胜报"), (".log", "log 评述"),
           (".tx", "tx 评述"), (".t", "t 评述"), (".txt", "txt 场景简报")]


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def classify(name):
    n = name.lower()
    for suf, tag in CLASSES:
        if n.endswith(suf):
            return tag
    return "其他"


def has_letters(s):
    return bool(re.search(r"[A-Za-z]", s))


def looks_like_text(s):
    """过滤二进制垃圾：本作有些 `.txt` 里其实是二进制块（实测有含 TAB 与 NUL 的乱码串）。
    判据：可打印字符占比 ≥ 0.9，且含 ≥2 个 ASCII 字母。"""
    if len(s) < 2:
        return False
    printable = sum(1 for ch in s if 0x20 <= ord(ch) < 0x7F or ord(ch) >= 0xA0)
    letters = sum(1 for ch in s if ch.isascii() and ch.isalpha())
    return printable / len(s) >= 0.9 and letters >= 2


def load_value_map(path):
    m = {}
    if not os.path.isfile(path):
        return m
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() in ("原文", "行号", "en"):
                continue
            f2 = s.split("\t")
            if len(f2) >= 2 and f2[0].strip() and f2[1].strip() and not re.fullmatch(r"\d+", f2[0].strip()):
                m.setdefault(f2[0].strip(), f2[1].strip())
    return m


def main():
    files = []
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(GAME, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if not os.path.isfile(p) or not re.search(r"(?i)\.(txt|tx|t|log|ply)$", f):
                continue
            if f.lower().endswith(".ply") or EXCLUDE.search(f):
                continue
            files.append((sub, f, p))
    print(f"纳入生成的场景文本文件: {len(files)}（已排除 .ply 与 info/readme/report）")

    occ = Counter()                      # 原文 -> 出现次数
    filecnt = defaultdict(set)           # 原文 -> 出现文件集合
    cls = {}
    for sub, f, p in files:
        tag = classify(f)
        with open(p, "rb") as fh:
            raw = fh.read()
        for ln in re.split(rb"\r\n|\r|\n", raw):
            # ⚠️ 用 **latin-1** 解码：与字节 1:1 可逆（cp1252 有未定义字节 0x81/0x8D/0x8F/0x90/0x9D，
            # 用 replace 会让不同字节塌成同一个键 ⇒ 静默错配）。键只用于匹配，文件字节才是真源。
            s = ln.decode("latin-1").strip()
            if not s or not has_letters(s) or not looks_like_text(s):
                continue
            occ[s] += 1
            filecnt[s].add(f"{sub}/{f}")
            cls.setdefault(s, set()).add(tag)
    print(f"场景层「可译唯一整行」: {len(occ)}  （出现总次数 {sum(occ.values())}）"
          f"  ·已滤除二进制垃圾")

    peg = {}
    for nm in ("scenario-map.tsv", "scenario-long-zh.tsv"):
        for k, v in load_value_map(os.path.join(PEGR, nm)).items():
            peg.setdefault(k, v)
    glos = {}
    for p in (os.path.join(WS, "glossary", "standard-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-words.tsv")):
        for k, v in load_value_map(p).items():
            glos.setdefault(k, v)
    glos_lc = {k.lower(): v for k, v in glos.items()}
    print(f"前作场景译文 {len(peg)} 条 · 术语总库 {len(glos)} 条")

    if os.path.isfile(OUTMAP):
        print(f"  {os.path.basename(OUTMAP)} 已存在 ⇒ 跳过（保护人工已填）")
    else:
        n_peg = n_glos = n_new = 0
        with open(OUTMAP, "w", encoding="utf-8", newline="\n") as f:
            f.write("# ww2-scn-map.tsv —— 场景层译法真源（**值模式：整行精确匹配**，未列出即原样保留）\n")
            f.write("# 来源：PeG=前作场景已验译文 / 词库=术语总库精确命中 / 新译=待填\n")
            f.write("# ⚠️ 生成器只做整行替换，**绝不做行内子串替换**（防前作「内嵌替换误伤」重演）\n")
            f.write("原文\t译文\t来源\n")
            for s, c in occ.most_common():
                # ⚠️ 原文一律 esc()：散文里含 TAB/控制字符（实测），不转义会列错位 ⇒ 键被静默截断
                if s in peg:
                    f.write(f"{esc(s)}\t{esc(peg[s])}\tPeG\n")
                    n_peg += 1
                elif s.lower() in glos_lc:
                    f.write(f"{esc(s)}\t{esc(glos_lc[s.lower()])}\t词库\n")
                    n_glos += 1
                else:
                    f.write(f"{esc(s)}\t\t新译\n")
                    n_new += 1
        print(f"  ⇒ {os.path.basename(OUTMAP)}: PeG 预填 {n_peg} · 词库预填 {n_glos} · **待填 {n_new}**")

    with open(OUTSTAT, "w", encoding="utf-8", newline="\n") as f:
        f.write("原文\t类\t出现文件数\t出现次数\n")
        for s, c in occ.most_common():
            f.write(f"{esc(s)}\t{'+'.join(sorted(cls.get(s, [])))}\t{len(filecnt[s])}\t{c}\n")
    print(f"  ⇒ {os.path.basename(OUTSTAT)}（规划用：类 / 出现文件数 / 出现次数）")

    print()
    print("=" * 88)
    print("按类统计（可译唯一整行）")
    print("=" * 88)
    per = Counter()
    for s in occ:
        for t in cls.get(s, []):
            per[t] += 1
    for t, c in per.most_common():
        print(f"  {t:16s} {c:>7d}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-worksheet.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
