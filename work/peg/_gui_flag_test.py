# -*- coding: utf-8 -*-
"""验证假设：CreateProcess 的标志（CREATE_NO_WINDOW / DEBUG_ONLY_THIS_PROCESS）
是否会让一个 GUI 程序（用 notepad.exe 代替游戏）的窗口不出现或提前退出。

绝不动游戏：本脚本只启动 notepad.exe，跑完立刻结束它。
"""
import ctypes
import ctypes.wintypes as wt
import os
import time

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)

DEBUG_ONLY_THIS_PROCESS = 0x00000002
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000

NOTEPAD = r"C:\Windows\System32\notepad.exe"


def _de_u32(buf, off):
    return ctypes.c_uint32.from_buffer(buf, off).value


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
                ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wt.HANDLE),
                ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


def windows_of(pid, only_visible=True):
    out = []
    def cb(hwnd, _lp):
        q = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(q))
        if q.value == pid:
            vis = bool(u32.IsWindowVisible(hwnd))
            if vis or not only_visible:
                cls = ctypes.create_unicode_buffer(256)
                txt = ctypes.create_unicode_buffer(256)
                u32.GetClassNameW(hwnd, cls, 256)
                u32.GetWindowTextW(hwnd, txt, 256)
                r = wt.RECT()
                u32.GetWindowRect(hwnd, ctypes.byref(r))
                out.append((cls.value, txt.value, vis,
                            (r.left, r.top, r.right, r.bottom)))
        return True
    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def visible_windows(pid, timeout=6.0):
    """轮询该 pid 是否有可见窗口，返回 (类名, 标题, 矩形) 列表。"""
    found = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = []
        def cb(hwnd, _lp):
            p = wt.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
            if p.value == pid and u32.IsWindowVisible(hwnd):
                cls = ctypes.create_unicode_buffer(256)
                txt = ctypes.create_unicode_buffer(256)
                u32.GetClassNameW(hwnd, cls, 256)
                u32.GetWindowTextW(hwnd, txt, 256)
                r = wt.RECT()
                u32.GetWindowRect(hwnd, ctypes.byref(r))
                found.append((cls.value, txt.value,
                              (r.left, r.top, r.right, r.bottom)))
            return True
        u32.EnumWindows(WNDENUMPROC(cb), 0)
        if found:
            return found
        time.sleep(0.1)
    return found


def debug_loop_watch(pid, seconds):
    """调试循环 + 同时观察该 pid 的可见窗口；返回 (窗口列表, 备注)。"""
    de = ctypes.create_string_buffer(256)
    end = time.time() + seconds
    last_poll = 0.0
    while time.time() < end:
        if not k32.WaitForDebugEvent(de, 100):
            pass
        else:
            c, p, t = _de_u32(de, 0), _de_u32(de, 4), _de_u32(de, 8)
            if c == 5:                                # EXIT_PROCESS
                k32.ContinueDebugEvent(p, t, 1)
                return [], "程序自身退出"
            cont = 1
            if c == 1:                                # EXCEPTION
                code = ctypes.c_uint32.from_buffer(de, 0x10).value
                cont = 1 if code in (0x80000003, 0x4000001F) else 0x80000001
            k32.ContinueDebugEvent(p, t, cont)
        if time.time() - last_poll > 0.2:
            last_poll = time.time()
            wins = []
            def cb(hwnd, _lp):
                q = wt.DWORD()
                u32.GetWindowThreadProcessId(hwnd, ctypes.byref(q))
                if q.value == pid and u32.IsWindowVisible(hwnd):
                    cls = ctypes.create_unicode_buffer(256)
                    txt = ctypes.create_unicode_buffer(256)
                    u32.GetClassNameW(hwnd, cls, 256)
                    u32.GetWindowTextW(hwnd, txt, 256)
                    r = wt.RECT()
                    u32.GetWindowRect(hwnd, ctypes.byref(r))
                    wins.append((cls.value, txt.value, (r.left, r.top, r.right, r.bottom)))
                return True
            u32.EnumWindows(WNDENUMPROC(cb), 0)
            if wins:
                return wins, "窗口已出现"
    return [], "超时（仍在运行，无可见窗口）"


def trial(name, flags, debug):
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    ok = k32.CreateProcessW(ctypes.c_wchar_p(NOTEPAD), None, None, None, False,
                            flags, None, ctypes.c_wchar_p(os.path.dirname(NOTEPAD)),
                            ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("  %-42s ❌ CreateProcess 失败 %s" % (name, ctypes.WinError(ctypes.get_last_error())))
        return
    if flags & CREATE_SUSPENDED:
        k32.ResumeThread(pi.hThread)
    if debug:
        wins, note = debug_loop_watch(pi.dwProcessId, 4.0)
    else:
        wins = visible_windows(pi.dwProcessId, timeout=3.0)
        note = ""
    print("  %-42s 窗口=%-3s %s  %s" % (
        name, ("是" if wins else "否"),
        (wins[0][0] if wins else "-"), (("（%s）" % note) if note else "")))
    k32.TerminateProcess(pi.hProcess, 0)
    k32.CloseHandle(pi.hThread)
    k32.CloseHandle(pi.hProcess)
    time.sleep(0.4)


if __name__ == "__main__":
    print("用 notepad.exe 测试 CreateProcess 标志是否影响 GUI 窗口出现：")
    trial("普通启动（无标志）", 0, False)
    trial("CREATE_SUSPENDED + ResumeThread（启动器方式）", CREATE_SUSPENDED, False)
    trial("DEBUG_ONLY_THIS_PROCESS", DEBUG_ONLY_THIS_PROCESS, True)
    trial("DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW", DEBUG_ONLY_THIS_PROCESS | CREATE_NO_WINDOW, True)
    trial("CREATE_NO_WINDOW（无调试）", CREATE_NO_WINDOW, False)
