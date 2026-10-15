# -*- coding: utf-8 -*-
"""换显示层采日志：临时把 DDrawCompat v0.7.1 换进游戏目录（原 Svens 包装备份在旁），
以 trace 级别记录**每一次 DirectDraw 调用**，跑完游戏后自动换回原 dll。

安全设计：
  * 只碰 ddraw.dll / DDrawCompat.ini 两个文件，母本 PeG030.exe 一个字节都不动；
  * 换入前必须确认当前 ddraw.dll 是已知的 Svens 包装（md5 校验），否则直接退出不动手；
  * 无论游戏怎么结束（正常退出/Ctrl+C/异常）都走 finally 换回，并再校验一次 md5；
  * `--restore` 可单独把目录还原；`--selftest` 只验证换入/换回链路（不跑游戏）。
"""
import argparse
import ctypes
import glob
import hashlib
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import diag_run as DR                                        # noqa: E402
import peg_launcher as PL                                    # noqa: E402

PEG_DIR = r"D:\Program Files\PeG"
DDRAW = os.path.join(PEG_DIR, "ddraw.dll")
BAK = os.path.join(PEG_DIR, "ddraw-Svens.dll.bak")
INI = os.path.join(PEG_DIR, "DDrawCompat.ini")
OUT = os.path.join(HERE, "out")
GAME_LOG = os.path.join(OUT, "game-debugview.txt")
DDC_SRC = r"D:\DSH\军事游戏汉化\archive\ddraw\ddraw-DDrawCompat-0.7.1.dll"
SVENS_MD5 = "337866f0c870384f5a16c8a11c46a963"
DDC_MD5 = "26275ed572a4df16141b26e952b50106"

# ini 内容：默认只采日志；--play 时按 --mode 生成试玩配置
def play_settings(mode):
    """试玩用 ini：mode = exclusive | borderless"""
    fs = "exclusive(0)" if mode == "exclusive" else "borderless"
    return ("; play test (%s)\n"
            "LogLevel = trace\n"
            "FullscreenMode = %s\n"
            "MouseSensitivity = native\n"
            "MousePollingRate = native\n"
            "GdiInterops = all\n") % (mode, fs)


INI_SETTINGS = os.environ.get("DDC_INI_SETTINGS", "LogLevel = trace\n")


def md5(path):
    """文件 md5（十六进制小写）；失败返回空串。"""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return ""

def swap_in():
    """返回 True 表示已换入 DDrawCompat；失败返回 False（不做任何改动）。"""
    if not os.path.exists(DDC_SRC):
        print("❌ 找不到 DDrawCompat dll：%s" % DDC_SRC)
        return False
    if not os.path.exists(DDRAW):
        print("❌ 游戏目录里没有 ddraw.dll（%s）" % DDRAW)
        return False
    cur = md5(DDRAW)
    if cur == DDC_MD5:
        print("· 目录里已经是 DDrawCompat（无需换入）")
        return True
    if cur != SVENS_MD5:
        if os.path.exists(BAK) and md5(BAK) == SVENS_MD5:
            print("· 当前 ddraw.dll 不是已知包装，但旁边有 Svens 备份 → 先还原再换入")
            shutil.copy2(BAK, DDRAW)
        else:
            print("❌ 当前 ddraw.dll 的 md5 是 %s，既不是 Svens 包装也不是 DDrawCompat。\n"
                  "   为安全起见不动手，请先告诉我这个文件是怎么来的。" % cur)
            return False
    if not os.path.exists(BAK):
        shutil.copy2(DDRAW, BAK)
        print("· 已备份原 ddraw.dll → %s" % os.path.basename(BAK))
    shutil.copy2(DDC_SRC, DDRAW)
    # DDrawCompat 的 ini 是扁平 key = value（写节头会报 unknown setting）
    with open(INI, "w", encoding="ascii") as f:
        f.write("; written by diag script (temporary, deleted after the run)\n" + INI_SETTINGS)
    if md5(DDRAW) != DDC_MD5:
        print("❌ 换入后 md5 不符，立即还原")
        swap_out()
        return False
    print("· 已换入 DDrawCompat v0.7.1（%d 字节）+ DDrawCompat.ini：%s"
          % (os.path.getsize(DDRAW), INI_SETTINGS.strip().replace("\n", " | ")))
    return True


def swap_out():
    if os.path.exists(BAK):
        shutil.copy2(BAK, DDRAW)
    if os.path.exists(INI):
        os.remove(INI)
    if os.path.exists(DDRAW):
        cur = md5(DDRAW)
        ok = cur == SVENS_MD5
        print("· 已换回原 ddraw.dll（md5=%s %s）" % (cur, "✓ 与 Svens 包装一致" if ok else "⚠ 与记录不一致"))
        return ok
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=os.path.join(PEG_DIR, "PeG030.exe"))
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--restore", action="store_true", help="只把目录还原（应急用）")
    ap.add_argument("--selftest", action="store_true", help="只验证换入/换回链路，不跑游戏")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mode", default="exclusive",
                    choices=["exclusive", "borderless"],
                    help="--play 时的全屏模式（exclusive 修输入；borderless 画面/截图正常）")
    ap.add_argument("--play", action="store_true",
                    help="用可操作配置（独占全屏 + 原生鼠标 + info 日志）换层，供人工试玩")
    a = ap.parse_args()
    if getattr(a, "play", False):
        global INI_SETTINGS
        INI_SETTINGS = play_settings(a.mode)
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    if a.restore:
        print("=== 还原显示层 ===")
        return 0 if swap_out() else 3

    if a.selftest:
        print("=== 换层链路自测（不跑游戏）===")
        print("换入前 ddraw.dll md5 = %s" % md5(DDRAW))
        if not swap_in():
            return 3
        ok_in = md5(DDRAW) == DDC_MD5
        print("换入后 md5 = %s  %s" % (md5(DDRAW), "✓" if ok_in else "❌"))
        ok_out = swap_out()
        print("换回后 md5 = %s  %s" % (md5(DDRAW), "✓" if ok_out else "❌"))
        return 0 if (ok_in and ok_out) else 3

    if a.dry_run:
        print("计划：备份 %s → %s；%s → ddraw.dll；写 %s；跑游戏；最后换回。"
              % (DDRAW, BAK, DDC_SRC, INI))
        return 0

    print("===== 换显示层采日志 %s =====" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for old in glob.glob(os.path.join(PEG_DIR, "DDrawCompat*.log")):
        try:
            os.remove(old)
        except OSError:
            pass
    lis = DR.Listener(GAME_LOG, only_pid=None, echo=True)
    if not lis.start():
        print("❌ 游戏日志监听启动失败：%s" % lis.err)
        return 3
    swapped = False
    try:
        if not swap_in():
            return 3
        swapped = True
        pid, hp = DR.launch_patched(a.exe, a.w, a.h)
        if pid is None:
            return 3
        lis.only_pid = pid
        k32.WaitForSingleObject(ctypes.c_void_p(hp), 0xFFFFFFFF)
        code = ctypes.c_uint32()
        k32.GetExitCodeProcess(ctypes.c_void_p(hp), ctypes.byref(code))
        print("\n游戏已退出（pid=%d，退出码=%d）。" % (pid, code.value))
        k32.CloseHandle(ctypes.c_void_p(hp))
    except KeyboardInterrupt:
        print("\n（被 Ctrl+C 中断）")
    finally:
        time.sleep(0.5)
        lis.close()
        if swapped:
            print("\n=== 还原显示层 ===")
            swap_out()

    logs = sorted(glob.glob(os.path.join(PEG_DIR, "DDrawCompat*.log")))
    print("\n游戏自身日志：%s（%d 条）" % (GAME_LOG, lis.count))
    if logs:
        for p in logs:
            n = sum(1 for _ in open(p, "rb"))
            print("DDrawCompat 调用日志：%s（%d 行，%.1f KB）" % (p, n, os.path.getsize(p) / 1024.0))
    else:
        print("⚠ 没找到 DDrawCompat*.log（可能 ini 位置/键名不对，或该版本不写文件）")
    print("两个日志都留着，直接把路径发我即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
