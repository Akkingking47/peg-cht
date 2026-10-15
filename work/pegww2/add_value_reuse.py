#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段1 二次复用：**同串复用** + 术语总库精确命中预填。

原理：行号模式只是引擎取字方式；同一英文串在不同行号应给**同一中文**。
故：
  · 建 value→zh 字典 = ① 本工作表内 来源=PeG 的行 ② 前作全量行级映射 ③ 术语总库(128,658)
  · 对「译文为空」的行，按**原文整串**查字典 ⇒ 命中即预填（来源=PeG同串 / 词库）
只填空，**绝不覆盖**已填好的译文。
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
PEGR = os.path.join(WS, "peg", "research")
OUTD = os.path.join(WS, "pegww2", "research")
_sink = io.StringIO()


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


def rows_of(path):
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if line.startswith("#"):
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if f2 and f2[0].strip() in ("行号", "原文", "en"):
                continue
            out.append(f2)
    return out


def build_peg_value_dict():
    d = {}
    # ① 前作全量行级映射（gui/misc/tips）
    for nm in ["gui030-zh.tsv", "misc030-map.tsv", "tips030-map.tsv"]:
        p = os.path.join(PEGR, nm)
        if not os.path.isfile(p):
            continue
        for f2 in rows_of(p):
            if len(f2) >= 3 and f2[1].strip() and f2[2].strip():
                d.setdefault(f2[1].strip(), f2[2].strip())
            elif len(f2) == 2 and f2[1].strip():
                pass  # 无原文，无法做串匹配
    # ② 前作串模式映射
    for nm in ["Equip30-map.tsv", "scenario-map.tsv", "scenario-long-zh.tsv", "ui-glossary.tsv"]:
        p = os.path.join(PEGR, nm)
        if not os.path.isfile(p):
            continue
        for f2 in rows_of(p):
            if len(f2) >= 2 and f2[0].strip() and f2[1].strip() and not re.fullmatch(r"\d+", f2[0].strip()):
                d.setdefault(f2[0].strip(), f2[1].strip())
    return d


def build_glossary():
    d = {}
    for p in [os.path.join(WS, "glossary", "standard-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-words.tsv")]:
        if not os.path.isfile(p):
            continue
        for f2 in rows_of(p):
            if len(f2) >= 2 and f2[0].strip() and f2[1].strip():
                k = f2[0].strip()
                if k != f2[1].strip():
                    d.setdefault(k, f2[1].strip())
    return d


def process(name, line_mode):
    p = os.path.join(OUTD, name)
    if not os.path.isfile(p):
        print(f"  {name}: 缺，跳过")
        return
    shutil.copy2(p, p + ".pre-reuse")
    pegv = build_peg_value_dict()
    glos = build_glossary()
    glos_lc = {k.lower(): v for k, v in glos.items()}
    out, fill_peg, fill_glos, empty = [], 0, 0, 0
    for f2 in rows_of(p):
        if len(f2) < 3:
            out.append(f2)
            continue
        f2 = list(f2)
        key = f2[1] if line_mode else f2[0]
        if len(f2) >= 3 and f2[-2].strip() == "" and f2[-1].strip() not in ("保留",):
            if key in pegv:
                f2[-2], f2[-1] = pegv[key], "PeG同串"
                fill_peg += 1
            elif key.lower() in glos_lc:
                f2[-2], f2[-1] = glos_lc[key.lower()], "词库"
                fill_glos += 1
            else:
                empty += 1
        elif len(f2) >= 3 and f2[-2].strip() == "":
            empty += 1
        out.append(f2)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {name}（行号模式={'是' if line_mode else '否'}）\n")
        f.write("# 来源：PeG=前作行级已验 / PeG同串=同英文串在前作别处的已验译法 / 词库=术语总库精确命中\n")
        f.write("#      新译=待人工填 / 保留=按型号规范原样保留\n")
        f.write(("行号\t原文\t译文\t来源\n" if line_mode else "原文\t译文\t来源\n"))
        for f2 in out:
            f.write("\t".join(f2) + "\n")
    print(f"  {name}: 同串补 {fill_peg} + 词库补 {fill_glos}；**仍待填 {empty}**")


def main():
    print("=" * 92)
    print("二次复用（同串 + 词库精确命中）")
    print("=" * 92)
    process("WW2Gui-map.tsv", True)
    process("WW2Misc-map.tsv", True)
    process("WW2Tips-map.tsv", True)
    process("ww2-eqp-map.tsv", False)
    process("WW2NAME-map.tsv", False)


if __name__ == "__main__":
    main()
    with open(os.path.join(OUTD, "evidence", "reuse2.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
