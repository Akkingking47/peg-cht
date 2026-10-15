# -*- coding: utf-8 -*-
"""生成「诊断-16比9取证.cmd」：GBK(cp936) 编码 + CRLF + 命令全 ASCII（中文只在 echo 里）。
教训：cmd.exe 解析批处理依赖 CRLF，UTF-8/LF-only 的 .cmd 会一闪而过。
"""
import os

PEg = r"D:\Program Files\PeG"
SCRIPT = r"D:\DSH\军事游戏汉化\work\peg\peg_trace.py"
LOG = r"D:\DSH\军事游戏汉化\work\peg\out\trace-log.txt"

lines = [
    "@echo off",
    "chcp 936 >nul",
    "title PeG 16:9 取证模式",
    'cd /d "%~dp0"',
    "echo ============================================================",
    "echo  PeG 16:9 取证模式（临时调试启动；不改动任何文件）",
    "echo.",
    "echo  请在游戏里依次做这几件事（约 2 分钟）：",
    "echo   1) 进入战斗地图，把鼠标移到画面右侧 / 下侧（原 800x600 之外）点几个格子",
    "echo   2) 顺带打开看一眼「更多选项」面板和「战略地图」",
    "echo   3) 然后正常退出游戏（游戏退出后本窗口会自己收尾）",
    "echo.",
    "echo  日志文件：%s" % LOG,
    "echo ============================================================",
    "echo.",
    '"C:\\Python314\\python.exe" "%s" --exe "%%~dp0PeG030.exe"' % SCRIPT,
    "echo.",
    "echo [完成] 日志已写入 %s" % LOG,
    "pause",
    "",
]
text = "\r\n".join(lines)
path = os.path.join(PEg, "诊断-16比9取证.cmd")
with open(path, "w", encoding="gbk", newline="") as f:
    f.write(text)
data = open(path, "rb").read()
print("已写：%s（%d 字节；CRLF=%d 个，无 BOM=%s）" % (
    path, len(data), data.count(b"\r\n"), not data.startswith(b"\xef\xbb\xbf")))
