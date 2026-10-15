# -*- coding: utf-8 -*-
"""启动测试：判断 exe 是「正常启动」还是「启动即崩」。

判据：
  - 进程存活 且 存在属于它的可见顶层窗口  => OK（启动成功）
  - 进程存活 但 无窗口                    => DIALOG（多半是崩溃对话框）
  - 进程已退出                            => CRASH，退出码即异常码
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

GAME = r"D:\OpenPG2"
user32 = ctypes.windll.user32
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def windows_of(pid):
    out = []

    def cb(hwnd, l):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid:
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 2)
            user32.GetWindowTextW(hwnd, buf, n + 2)
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            out.append((hwnd, cls.value, buf.value,
                        bool(user32.IsWindowVisible(hwnd))))
        return True

    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return out


def main():
    exe = os.path.join(GAME, "OpenGen.exe")
    wait = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    print("测试 exe: %s" % exe)
    print("MD5: ", end="")
    import hashlib
    print(hashlib.md5(open(exe, "rb").read()).hexdigest())
    p = subprocess.Popen([exe], cwd=GAME, close_fds=True)
    print("launched pid=%d, 等待 %d 秒..." % (p.pid, wait))
    time.sleep(wait)
    rc = p.poll()
    wins = windows_of(p.pid)
    if rc is not None:
        print("=> 进程已退出  rc=%d (0x%08X)" % (rc, rc & 0xFFFFFFFF))
        print("=> 判定：CRASH")
    else:
        print("=> 进程存活，窗口 %d 个：" % len(wins))
        for h, cls, t, vis in wins:
            print("     hwnd=0x%08X class=%-24s visible=%s title=%r" %
                  (h, cls, vis, t))
        ok = any(v and t for _, _, t, v in wins)
        print("=> 判定：%s" % ("OK（已出现可见窗口）" if ok
                               else "DIALOG / 无窗口（疑似崩溃对话框）"))
    # 清理
    if rc is None:
        subprocess.run(["taskkill", "/F", "/IM", "OpenGen.exe"],
                       capture_output=True)
        time.sleep(1)
        print("已结束进程")


if __name__ == "__main__":
    main()
