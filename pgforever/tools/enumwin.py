# -*- coding: utf-8 -*-
r"""枚举顶层窗口（标题/类名/矩形/进程），并识别特定句柄，用于排查遮挡与焦点问题。"""
import ctypes
import subprocess
import time
from ctypes import wintypes

user = ctypes.windll.user32
user.SetProcessDPIAware()

p = subprocess.Popen([r'D:\PGForever1.021\PGForever.exe', '/game', 'pg'], cwd=r'D:\PGForever1.021')
print('launched pid=%d' % p.pid)
time.sleep(7)

items = []


@ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def cb(h, l):
    r = wintypes.RECT()
    user.GetWindowRect(h, ctypes.byref(r))
    n = user.GetWindowTextLengthW(h) + 1
    b = ctypes.create_unicode_buffer(n)
    user.GetWindowTextW(h, b, n)
    c = ctypes.create_unicode_buffer(256)
    user.GetClassNameW(h, c, 256)
    pid = wintypes.DWORD()
    user.GetWindowThreadProcessId(h, ctypes.byref(pid))
    items.append({
        'hwnd': h, 'title': b.value, 'cls': c.value, 'pid': pid.value,
        'rect': (r.left, r.top, r.right - r.left, r.bottom - r.top),
        'vis': user.IsWindowVisible(h), 'enabled': user.IsWindowEnabled(h),
        'topmost': bool(user.GetWindowLongW(h, -20) & 0x00000008),
    })
    return True


user.EnumWindows(cb, 0)
print('顶层窗口总数 %d' % len(items))
print()
print('%-10s %-8s %-22s %-24s %-26s %s' % ('hwnd', 'pid', 'class', 'title', 'rect(x,y,w,h)', 'flags'))
for it in sorted(items, key=lambda x: (not x['vis'], x['pid'])):
    if not it['vis']:
        continue
    print('%-10s %-8s %-22s %-24s %-26s topmost=%s enabled=%s' % (
        it['hwnd'], it['pid'], it['cls'][:22], it['title'][:24], str(it['rect']), it['topmost'], it['enabled']))

fg = user.GetForegroundWindow()
print()
print('当前前台窗口 = %s' % fg)
for it in items:
    if it['hwnd'] == fg:
        print('  -> %s' % it)

for probe in (1444772, 132632):
    print()
    print('探针句柄 %s:' % probe)
    hit = [it for it in items if it['hwnd'] == probe]
    print('  %s' % (hit[0] if hit else '不在顶层窗口列表中（可能是子窗口）'))
    if not hit:
        c = ctypes.create_unicode_buffer(256)
        user.GetClassNameW(probe, c, 256)
        n = user.GetWindowTextLengthW(probe) + 1
        b = ctypes.create_unicode_buffer(n)
        user.GetWindowTextW(probe, b, n)
        r = wintypes.RECT()
        user.GetWindowRect(probe, ctypes.byref(r))
        pid = wintypes.DWORD()
        user.GetWindowThreadProcessId(probe, ctypes.byref(pid))
        print('    class=%r title=%r rect=%s pid=%s' % (c.value, b.value, (r.left, r.top, r.right-r.left, r.bottom-r.top), pid.value))

# 桌面信息
print()
print('屏幕 %dx%d  虚拟屏幕 %dx%d' % (
    user.GetSystemMetrics(0), user.GetSystemMetrics(1),
    user.GetSystemMetrics(78), user.GetSystemMetrics(79)))
hdesk = user.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
buf = ctypes.create_unicode_buffer(256)
needed = wintypes.DWORD()
user.GetUserObjectInformationW(hdesk, 2, buf, 256, ctypes.byref(needed))
print('本线程桌面 = %r' % buf.value)
print('OpenInputDesktop 可取 = %s' % bool(user.OpenInputDesktop(0, False, 0x0001)))
