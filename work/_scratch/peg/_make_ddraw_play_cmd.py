# -*- coding: utf-8 -*-
"""生成 DDrawCompat 试玩入口 .cmd（GBK + CRLF + 命令全 ASCII，中文只在 echo 里）。"""
import io, os

PEG = r"D:\Program Files\PeG"
CMD = os.path.join(PEG, "进游戏-16比9-DDrawCompat试玩.cmd")

TEXT = """@echo off
setlocal
title PeG 16:9 DDrawCompat test
chcp 936 >nul
set "PY=C:\\Python314\\python.exe"
if not exist "%PY%" set "PY=python"
echo ============================================================
echo   PeG 1920x1080 显示层测试：DDrawCompat 0.7.1
echo   本次配置：borderless（窗口化全屏，可截图）+ 原生鼠标
echo   游戏退出后自动换回原显示层
echo ============================================================
echo.
"%PY%" "D:\\DSH\\军事游戏汉化\\work\\peg\\diag_ddraw.py" --play --mode borderless --w 1920 --h 1080 --exe "%~dp0PeG030.exe"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo [失败] 退出码 %RC%，请把本窗口内容截图发我。
if "%RC%"=="0" echo [已还原] 显示层已换回原 ddraw.dll。
echo.
echo 提示：若本窗口被强制关闭而没换回，请双击 还原显示层.cmd
echo.
pause
"""

with io.open(CMD, "wb") as f:
    f.write(TEXT.replace("\n", "\r\n").encode("gbk"))

b = open(CMD, "rb").read()
print("已写 %s（%d 字节，CRLF=%s，GBK 可解=%s）"
      % (CMD, len(b), b"\r\n" in b, bool(b.decode("gbk", "strict"))))
