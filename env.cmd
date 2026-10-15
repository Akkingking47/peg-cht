@echo off
chcp 936 >nul
REM ===========================================================================
REM  汉化工程 · 运行环境固化（唯一真源）    D:\DSH\军事游戏汉化\env.cmd
REM ---------------------------------------------------------------------------
REM  用法： call env.cmd             注入 UTF-8 环境变量，对当前 cmd 会话生效
REM         call env.cmd check       自检解释器版本 + 核心依赖能否 import
REM         call env.cmd install     按 requirements.txt 安装依赖
REM  解释器：C:\Python314\python.exe（实测 Python 3.14.7）
REM  说明：旧托管 venv（.workbuddy\...\envs\default）已失效，勿再引用。
REM  纪律：改环境 = 改本文件 ＋ requirements.txt；别处只指向这两处。
REM ===========================================================================

set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PY=C:\Python314\python.exe"
set "PYTHON=C:\Python314\python.exe"

REM 解释器置于 PATH 最前；幂等：已在 PATH 中就不重复追加
echo %PATH% | findstr /I /C:"C:\Python314" >nul 2>&1 || set "PATH=C:\Python314;C:\Python314\Scripts;%PATH%"

if /I "%~1"=="check" goto :envcheck
if /I "%~1"=="install" goto :envinstall

echo [env] PYTHONIOENCODING=utf-8  PYTHONUTF8=1
echo [env] PY=%PY%
echo [env] 依赖清单真源：%~dp0requirements.txt
exit /b 0

:envcheck
"%PY%" --version
"%PY%" -c "import PIL, pefile, numpy"
if errorlevel 1 (echo [WARN] 核心依赖缺失 - 请跑 call env.cmd install) else (echo [OK] 核心依赖可 import)
exit /b 0

:envinstall
"%PY%" -m pip install -r "%~dp0requirements.txt"
exit /b 0
