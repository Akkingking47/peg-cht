# -*- coding: utf-8 -*-
r"""输入诊断：光标能否设置、目标点归属哪个窗口、窗口/进程/前台状态。"""
import ctypes
import subprocess
import time
from ctypes import wintypes

user = ctypes.windll.user32
user.SetProcessDPIAware()

p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
print('launched pid=%d' % p.pid)
time.sleep(8)

hwnd = None
res = {}


@ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def cb(h, l):
    if user.IsWindowVisible(h):
        n = user.GetWindowTextLengthW(h) + 1
        b = ctypes.create_unicode_buffer(n)
        user.GetWindowTextW(h, b, n)
        if b.value.startswith('PG Forever'):
            res['h'] = h
            res['t'] = b.value
    return True


user.EnumWindows(cb, 0)
hwnd = res.get('h')
print('game hwnd=%s title=%r' % (hwnd, res.get('t')))

pid = wintypes.DWORD()
user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
print('game window pid=%d   launched pid=%d   match=%s' % (pid.value, p.pid, pid.value == p.pid))

r = wintypes.RECT()
user.GetWindowRect(hwnd, ctypes.byref(r))
print('window rect %d,%d %dx%d' % (r.left, r.top, r.right - r.left, r.bottom - r.top))
print('IsWindowEnabled=%s  IsWindowVisible=%s' % (user.IsWindowEnabled(hwnd), user.IsWindowVisible(hwnd)))

fg = user.GetForegroundWindow()
nb = ctypes.create_unicode_buffer(256)
user.GetWindowTextW(fg, nb, 256)
print('foreground hwnd=%s title=%r' % (fg, nb.value))

# 关键：目标点归属哪个窗口
pt = wintypes.POINT(956, 1019)
target = user.WindowFromPoint(pt)
tpid = wintypes.DWORD()
user.GetWindowThreadProcessId(target, ctypes.byref(tpid))
tb = ctypes.create_unicode_buffer(256)
user.GetWindowTextW(target, tb, 256)
print('WindowFromPoint(956,1019) -> hwnd=%s pid=%s title=%r' % (target, tpid.value, tb.value))

# 光标设置验证
ok = user.SetCursorPos(956, 1019)
time.sleep(0.3)
cur = wintypes.POINT()
user.GetCursorPos(ctypes.byref(cur))
print('SetCursorPos=%s  GetCursorPos=(%d,%d)' % (ok, cur.x, cur.y))

# 窗口所在桌面 / 会话
print('GetWindowThreadProcessId -> thread=%d' % user.GetWindowThreadProcessId(hwnd, None))

# 尝试激活
user.SetForegroundWindow(hwnd)
time.sleep(0.5)
print('after SetForegroundWindow, foreground=%s' % user.GetForegroundWindow())

# 试一次点击并观察窗口是否收到（用 DefWindowProc 无法验证，改看窗口是否变化）
user.SetCursorPos(956, 1019)
time.sleep(0.2)
user.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(0.1)
user.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(1.0)
print('clicked; game alive=%s' % (p.poll() is None))
print('foreground now=%s' % user.GetForegroundWindow())
