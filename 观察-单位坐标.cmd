@echo off
title PeG watch - unit coords (read only)
cd /d D:\DSH\军事游戏汉化
echo Waiting for PeG030.exe ... now start the game (memory entry)
python work\peg\diag_watch2.py --wait PeG030.exe
echo.
echo Python exit code %ERRORLEVEL%
pause
