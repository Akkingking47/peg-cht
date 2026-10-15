# -*- coding: utf-8 -*-
"""把试玩配置改成 exclusive(0)，并让自测打印真正会写入的 ini 内容。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
NL = chr(92) + "n"

old_fs = '"FullscreenMode = exclusive' + NL + '"'
new_fs = '"FullscreenMode = exclusive(0)' + NL + '"'
print("改 FullscreenMode：", src.count(old_fs))
assert src.count(old_fs) == 1
src = src.replace(old_fs, new_fs, 1)

old_print = ('    print("· 已换入 DDrawCompat v0.7.1（%d 字节）+ DDrawCompat.ini（LogLevel = trace）"\n'
             '          % os.path.getsize(DDRAW))')
new_print = ('    print("· 已换入 DDrawCompat v0.7.1（%d 字节）+ DDrawCompat.ini：%s"\n'
             '          % (os.path.getsize(DDRAW), INI_SETTINGS.strip().replace("' + NL + '", " | ")))')
print("改打印语句：", src.count(old_print))
if src.count(old_print) == 1:
    src = src.replace(old_print, new_print, 1)

io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
