# -*- coding: utf-8 -*-
"""补回 diag_ddraw.py 里被误删的 md5() 函数。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
assert "def md5(" not in src, "md5 已存在"
anchor = 'INI_SETTINGS = os.environ.get("DDC_INI_SETTINGS", "LogLevel = trace' + chr(92) + 'n")\n'
assert anchor in src, "找不到 INI_SETTINGS 定义"
src = src.replace(anchor, anchor + '''

def md5(path):
    """文件 md5（十六进制小写）；失败返回空串。"""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return ""
''', 1)
io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
import re
print("函数：", re.findall(r"^def (\w+)", chk, re.M))
