#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段2.3：最小试点 WW2Gui.txt（只改 6 行标签，隔离"字体成像"这一个变量）。

纪律：
  · 从 **备份原文** 读（pegww2/testbed/backup/text/WW2Gui.txt），绝不从游戏目录读
  · 译文取自前作 `peg/research/gui030-zh.tsv` 的行级映射（**已实机验证过的字串**），不另创译法
  · 行数必须与原文件严格一致；出稿 GBK(936) 无 BOM，沿用原文 CRLF
  · 试点行选「主地图界面就能看见」的短标签 ⇒ 一张截图即可判定
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
SRC = os.path.join(WS, "pegww2", "testbed", "backup", "text", "WW2Gui.txt")
MAP = os.path.join(WS, "peg", "research", "gui030-zh.tsv")
DST = os.path.join(WS, "pegww2", "testbed", "out", "text", "WW2Gui.txt")
_REPORT = os.path.join(WS, "pegww2", "research", "evidence", "trial-report.txt")
_sink = io.StringIO()

# 试点行（1-based）：主地图/菜单上可见的短标签
TRIAL = [40, 44, 46, 54, 61, 63]


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


def load_map():
    m = {}
    with open(MAP, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if len(f2) >= 3 and re.fullmatch(r"\d+", f2[0].strip()):
                m[int(f2[0])] = (f2[1].strip(), f2[2].strip())
    return m


def main():
    raw = open(SRC, "rb").read()
    parts = re.split(rb"(\r\n|\r|\n)", raw)          # 三态拆行，保留分隔符
    lines, seps = parts[0::2], parts[1::2]
    nlines = len(lines)
    print(f"源: {os.path.relpath(SRC, WS)}")
    print(f"  字节 {len(raw):,}  行元素 {nlines}（原版 605）")
    m = load_map()

    changes = []
    for ln in TRIAL:
        i = ln - 1
        if i >= nlines:
            print(f"  ⚠ 行 {ln} 超界，跳过")
            continue
        en = lines[i].decode("cp1252")
        ent = m.get(ln)
        if not ent:
            print(f"  ⚠ 行 {ln} 前作映射缺失，跳过（原文 {en!r}）")
            continue
        sen, zh = ent
        if sen and sen != en:
            print(f"  ⚠ 行 {ln} 原文不一致：前作 {sen!r} ≠ 本作 {en!r} ⇒ 跳过（保守）")
            continue
        changes.append((ln, en, zh))
        lines[i] = zh.encode("gbk")

    out = seps[0].join([]) if False else b""
    buf = bytearray()
    for i, ln in enumerate(lines):
        buf += ln
        if i < len(seps):
            buf += seps[i]
    assert len(buf) > 0
    # 行数一致性硬校验（元素数不变即行数不变）
    newparts = re.split(rb"(\r\n|\r|\n)", bytes(buf))
    assert len(newparts[0::2]) == nlines, "行数不一致，拒绝落盘"
    assert b"\r\n" in bytes(buf) or b"\n" in bytes(buf), "换行丢失"
    for bad in (b"\x00",):
        assert bad not in bytes(buf), "混入控制字符"

    print(f"\n将改 {len(changes)} 行（行数保持 {nlines}）：")
    for ln, en, zh in changes:
        print(f"  行{ln:<4d} {en:22s} → {zh}   [{len(zh)} 字 / 原文 {len(en)} 字符]")
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, "wb") as f:
        f.write(bytes(buf))
    back = open(DST, "rb").read()
    assert back == bytes(buf), "回读校验失败"
    # 非试点行必须逐字节等于原文
    for i in range(nlines):
        if (i + 1) in TRIAL:
            continue
        if lines[i] != parts[0::2][i]:
            print(f"  ❌ 行 {i + 1} 被误改，拒绝")
            raise SystemExit(1)
    print(f"\n产物: {os.path.relpath(DST, WS)}  {len(back):,} B  （行数一致 ✅ 回读一致 ✅）")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
