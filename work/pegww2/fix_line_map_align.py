#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2：行号模式映射的**对齐审计**（防「前作译文错配到本作另一行」）。

背景（踩坑）：前作 `misc030-map.tsv` / `tips030-map.tsv` 是 **2 列（行号/译文，无原文）**，
只能靠「行号相同」假设对齐。本作 `WW2Misc.txt`(45 行) / `WW2Tips.TXT`(43 行) 的行内容与前作**并不逐行相同**
（misc 12 = FORTIFICATION vs DENSE URBAN；tips 22/25/27/33/34/38 句意不同），
且前作 tips 原文自带 `(N)   ` 前缀而本作没有 ⇒ 直接沿用会**静默错配**。

判据：逐行比对**前作原文备份**与**本作原文备份**：
  · 相同 ⇒ 译文可用（保留）
  · 不同 ⇒ 译文清空、来源=待重译（必须重写）
  · 另：译文若带 `(N)   ` 前缀而本作原文无此前缀 ⇒ **剥掉前缀**
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
PEGBK = os.path.join(WS, "peg", "testbed", "backup")
WW2BK = os.path.join(WS, "pegww2", "testbed", "backup", "text")
RES = os.path.join(WS, "pegww2", "research")
# (map 文件, 前作原文备份, 本作原文备份)
JOBS = [
    ("WW2Misc-map.tsv", "misc030.txt", "WW2Misc.txt"),
    ("WW2Tips-map.tsv", "tips030.txt", "WW2Tips.TXT"),
]
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


def lines_of(p):
    raw = open(p, "rb").read()
    return [x.decode("cp1252").rstrip() for x in re.split(rb"\r\n|\r|\n", raw)]


def main():
    for mapn, pegbk, ww2bk in JOBS:
        mp = os.path.join(RES, mapn)
        peg = lines_of(os.path.join(PEGBK, pegbk))
        ww2 = lines_of(os.path.join(WW2BK, ww2bk))
        head, rowses = [], []
        with open(mp, encoding="utf-8-sig") as f:
            for line in f:
                s = line.rstrip("\r\n")
                if s.startswith("#") or s.split("\t")[0].strip() in ("行号", "原文"):
                    head.append(s)
                else:
                    rowses.append(s.split("\t"))
        print("=" * 92)
        print(f"{mapn}  （前作 {pegbk} {len(peg)} 行 · 本作 {ww2bk} {len(ww2)} 行）")
        print("=" * 92)
        blank = strip = ok = 0
        for f2 in rowses:
            if len(f2) < 4 or not re.fullmatch(r"\d+", f2[0].strip()):
                continue
            i = int(f2[0])
            cur_ww2 = ww2[i - 1] if i - 1 < len(ww2) else ""
            cur_peg = peg[i - 1] if i - 1 < len(peg) else ""
            # ⚠️ 先**归一化**：前作原文常带 '(N)   ' 序号前缀，本作没有；必须剥掉再比对，
            #    否则每一行都会因前缀被判为「错配」（本项目实测踩过：tips 43 行全被误清空）
            peg_core = re.sub(r"^\(\d+\)\s*", "", cur_peg)
            ww2_core = re.sub(r"^\(\d+\)\s*", "", cur_ww2)
            if ww2_core != peg_core:
                if f2[2].strip():
                    print(f"  ❌ 错配 行{i}: 前作原文={peg_core[:58]!r}")
                    print(f"             本作原文={ww2_core[:58]!r}")
                    print(f"             前作译文={f2[2][:58]!r} ⇒ 清空待重译")
                    blank += 1
                elif f2[3].strip() == "待重译":
                    blank += 1
                f2[2], f2[3] = "", "待重译"
                continue
            # 原文一致 ⇒ 译文可用；若前作带序号前缀而本作不带，把译文里的前缀剥掉
            if re.match(r"^\(\d+\)\s*", cur_peg) and not re.match(r"^\(\d+\)", cur_ww2):
                new = re.sub(r"^\(\d+\)\s*", "", f2[2])
                if new != f2[2]:
                    f2[2] = new
                    f2[3] = (f2[3] + "+剥前缀") if f2[3] else "剥前缀"
                    strip += 1
            ok += 1
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(head + ["\t".join(x) for x in rowses]) + "\n")
        print(f"  ⇒ 对齐可用 {ok} · 错配清空 {blank} · 剥前缀 {strip}")
        print()


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "align-audit.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
