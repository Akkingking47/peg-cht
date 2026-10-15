# -*- coding: utf-8 -*-
"""修 diag_ddraw.py 里 f.write(...) 被弄成非法的字符串隐式拼接。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
NL = chr(92) + "n"

needle = ('        f.write("; written by diag script (temporary, deleted after the run)'
          + NL + '"\n                INI_SETTINGS)')
repl = ('        f.write("; written by diag script (temporary, deleted after the run)'
        + NL + '" + INI_SETTINGS)')
print("找到待修语句：", src.count(needle))
assert src.count(needle) == 1
src = src.replace(needle, repl, 1)
io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
for i, ln in enumerate(chk.splitlines(), 1):
    if "f.write(\"; written" in ln or ln.strip().startswith("+ INI_SETTINGS"):
        print("  %d| %s" % (i, ln))
