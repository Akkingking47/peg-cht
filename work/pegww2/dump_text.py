#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 DOCS · 从**建出的成品** RTF 中抽「读者所见」正文（用于人工审阅与 G5 审计）。

与 `doc_rtf.parse` 的区别：
  · 还原 `\\uN?` 为字符（否则中文全显示成 `?` —— 那只是兜底字符，不是文件错误）
  · `\\'xx` 按 cp1252 还原
  · 跳过头部元数据组（fonttbl/colortbl/stylesheet/info/…）、`{\\*…}` 可忽略组、`\\fldinst` 字段指令
  · `\\par` 断段；折叠多余空白

用法: python dump_text.py <rel> [起始段] [条数]
"""
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(WS, "pegww2", "docs-zh")
sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
import doc_rtf as R          # noqa: E402


def display_lines(path):
    raw = open(path, "rb").read()
    s = raw.decode("latin-1")
    chunks, offs = R.parse_off(raw)
    star = R.star_spans(s)
    # 头部组区间：⚠️ 必须从**紧邻控制字之前的那个 `{`** 开始走，
    # 否则从 `\fonttbl` 起走会在**第一个字体条目闭合时就早退**，后面的字体名会漏出来
    head_ranges = []
    for g in ("fonttbl", "colortbl", "stylesheet", "info", "listtable",
              "listoverridetable", "rsidtbl", "generator", "latentstyles",
              "datastore", "mmathPr", "themedata", "xmlnstbl"):
        j = s.find("\\" + g)
        while j >= 0:
            k = s.rfind("{", 0, j)          # 该组自身的开括号
            if k < 0:
                k = j
            depth = 0
            while k < len(s):
                if s[k] == "\\":
                    k += 2
                    continue
                if s[k] == "{":
                    depth += 1
                elif s[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            head_ranges.append((j, min(k + 1, len(s))))
            j = s.find("\\" + g, k + 1)
    # 字段指令区间
    fld_ranges = []
    j = s.find("\\fldinst")
    while j >= 0:
        k = j
        depth = 0
        while k < len(s):
            if s[k] == "\\":
                k += 2
                continue
            if s[k] == "{":
                depth += 1
            elif s[k] == "}":
                depth -= 1
                if depth <= 0:
                    break
            k += 1
        fld_ranges.append((j, min(k + 1, len(s))))
        j = s.find("\\fldinst", k + 1)
    skip = head_ranges + star + fld_ranges

    def inside(o):
        return any(a <= o < b for a, b in skip)

    lines, cur = [], []
    i = 0
    while i < len(chunks):
        k, t = chunks[i]
        o = offs[i]
        if k == "ctrl" and re.fullmatch(r"\\u-?\d+", t):
            n = int(t[2:])
            ch = chr(n + 65536 if n < 0 else n)
            # 其后紧跟的 `?` 或单字符是兜底，丢弃
            if i + 1 < len(chunks) and chunks[i + 1][0] == "text":
                nx = chunks[i + 1][1]
                chunks[i + 1] = ("text", nx[1:])
                if not chunks[i + 1][1]:
                    i += 1
            if not inside(o):
                cur.append(ch)
            i += 1
            continue
        if k == "text" and not inside(o):
            cur.append(t)
        elif k == "ctrl" and t in ("\\\\", "\\{", "\\}"):
            if not inside(o):
                cur.append(t[1:])          # 文本里的转义字符还原
        elif k == "ctrl" and t.startswith("\\par"):
            if "".join(cur).strip():
                lines.append(re.sub(r"[ \t]{2,}", " ", "".join(cur).strip()))
            cur = []
        i += 1
    if "".join(cur).strip():
        lines.append(re.sub(r"[ \t]{2,}", " ", "".join(cur).strip()))
    return lines


def main():
    rel = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    cnt = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    ls = display_lines(os.path.join(OUT, rel))
    print("== %s：正文档数 %d ==" % (rel, len(ls)))
    for n, x in enumerate(ls[start:start + cnt], start):
        print("  %3d| %s" % (n, x[:108]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
