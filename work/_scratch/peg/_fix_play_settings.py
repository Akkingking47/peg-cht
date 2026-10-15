# -*- coding: utf-8 -*-
"""修 diag_ddraw.py 里被写坏的多行字符串：把 PLAY_SETTINGS/INI_SETTINGS 一段重写成正确的转义形式。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()

start_marker = "# ini 内容：默认只采日志；--play 时换成「可操作」配置"
end_marker = "def swap_in():"
i = src.find(start_marker)
j = src.find(end_marker)
print("定位 start=%d end=%d" % (i, j))
assert i >= 0 and j > i, "定位失败"

NL = chr(92) + "n"  # 目标文件里要出现的两字符序列：反斜杠 + n
block = "\n".join([
    start_marker,
    "PLAY_SETTINGS = (",
    '    "; play test%s"' % NL,
    '    "LogLevel = info%s"' % NL,
    '    "FullscreenMode = exclusive%s"' % NL,
    '    "MouseSensitivity = native%s"' % NL,
    '    "MousePollingRate = native%s"' % NL,
    '    "GdiInterops = all%s")' % NL,
    'INI_SETTINGS = os.environ.get("DDC_INI_SETTINGS", "LogLevel = trace' + NL + '")',
    "",
    "def swap_in():",
])
src = src[:i] + block + src[j + len(end_marker):]

# 顺带确认 --play 的 main 钩子存在
assert 'global INI_SETTINGS' in src, "缺少 main 里的 global 钩子"
io.open(P, "w", encoding="utf-8", newline="").write(src)

chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
for ln in chk.splitlines():
    if "FullscreenMode" in ln or "play test" in ln or "INI_SETTINGS = os.environ" in ln:
        print("  |", ln)
