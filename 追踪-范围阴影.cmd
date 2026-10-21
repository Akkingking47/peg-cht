@echo off
title PeG tracer - waiting for game
cd /d D:\DSH\军事游戏汉化
echo.
echo  [1] This window is the TRACER. It is waiting for PeG030.exe right now.
echo  [2] Start the game the way you normally do (your 16:9 entry).
echo  [3] In game: enter a battle, click a unit, move the mouse a bit, then quit the game normally.
echo  [4] Back in this window: it prints HIT lines + hit counts. Send them to me.
echo.
python work\peg\diag_trace.py --wait PeG030.exe --bp 410E66 --bp 410F2B --bp 423849 --bp 423CD6 --max 20
echo.
echo === tracer finished (original bytes restored) ===
pause
