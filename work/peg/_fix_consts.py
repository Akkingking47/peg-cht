# -*- coding: utf-8 -*-
"""补回 diag_ddraw.py 里被误删的 OUT / GAME_LOG 常量。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
anchor = 'INI = os.path.join(PEG_DIR, "DDrawCompat.ini")\n'
assert anchor in src, "找不到 INI 定义"
assert "OUT = " not in src and "GAME_LOG = " not in src, "OUT/GAME_LOG 已存在，无需补"
src = src.replace(anchor, anchor +
                  'OUT = os.path.join(HERE, "out")\n'
                  'GAME_LOG = os.path.join(OUT, "game-debugview.txt")\n', 1)
io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
for i, ln in enumerate(chk.splitlines(), 1):
    if ln.startswith(("OUT =", "GAME_LOG =", "INI =", "PEG_DIR =")):
        print("  %d| %s" % (i, ln))
