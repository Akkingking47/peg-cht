#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""PeG-WW2 场景层：**TSV 安全转义**（因为原文串里真的存在控制字符）。

背景（踩坑）：本作散文里夹着 `\x00`/`\x01`/`\x11`/`\x12` 等控制字符（实测 34 行），
若原样写进 TSV，读回时列会错位 ⇒ 键被截断 ⇒ **生成器永远匹配不上该行**
（表现为「该行仍是英文」，且**不报错**，属静默缺口）。

规则：`\` → `\\` ；TAB → `\t` ；CR → `\r` ；LF → `\n` ；其它 C0 控制字符 → `\xNN`
⇒ 写盘安全、可逆、肉眼可辨。
"""


def esc(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\n":
            out.append("\\n")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append("\\x%02x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def unesc(s: str) -> str:
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\" and i + 1 < n:
            nxt = s[i + 1]
            if nxt == "\\":
                out.append("\\")
                i += 2
                continue
            if nxt == "t":
                out.append("\t")
                i += 2
                continue
            if nxt == "r":
                out.append("\r")
                i += 2
                continue
            if nxt == "n":
                out.append("\n")
                i += 2
                continue
            if nxt == "x" and i + 3 < n:
                try:
                    out.append(chr(int(s[i + 2:i + 4], 16)))
                    i += 4
                    continue
                except ValueError:
                    pass
        out.append(ch)
        i += 1
    return "".join(out)


if __name__ == "__main__":
    tests = ["Plain", "a\tb", "x\\y", "line\r\nbreak", "ctl\x01end", "E\\tF"]
    for t in tests:
        e = esc(t)
        assert unesc(e) == t, (t, e, unesc(e))
    print("esc/unesc 往返自测通过：", [(t, esc(t)) for t in tests])
