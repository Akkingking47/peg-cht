@echo off
setlocal
title PeG 16:9 + T组（移动范围每帧重算）测试
chcp 936 >nul
set "PY=C:\Python314\python.exe"
if not exist "%PY%" set "PY=python"
set "LOG=D:\DSH\军事游戏汉化\work\peg\out\launcher-log-T.txt"
echo ============================================================
echo   PeG 1920x1080 + T 组测试（原版 PeG030.exe 不会被修改）
echo   本次新增：每帧重算移动范围（鼠标不动也应显示阴影）
echo ============================================================
echo.
"%PY%" "D:\DSH\军事游戏汉化\work\peg\peg_launcher.py" --w 1920 --h 1080 --range-every --exe "D:\Program Files\PeG\PeG030.exe" --cwd "D:\Program Files\PeG" --log "%LOG%"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo [启动失败] 返回码 %RC%，请把本窗口内容或日志发我。
if "%RC%"=="0" echo [已放行] 游戏窗口几秒内出现，本窗口可以关掉。
echo.
pause
