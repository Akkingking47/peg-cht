# -*- coding: utf-8 -*-
"""用与 ef.exe 完全相同的 CreateFontA 参数，验证 GDI 在 ACP=936 下能否渲染 GBK 汉字。
不修改任何游戏文件；只在本进程内建内存 DC 与 DIB 做渲染像素统计。"""
import ctypes
from ctypes import wintypes as wt

gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_last_error=True)

gdi32.CreateCompatibleDC.restype = wt.HDC
gdi32.CreateCompatibleDC.argtypes = [wt.HDC]
gdi32.CreateDIBSection.restype = wt.HBITMAP
gdi32.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
gdi32.DeleteDC.argtypes = [wt.HDC]
gdi32.CreateFontA.restype = wt.HFONT
gdi32.CreateFontA.argtypes = [ctypes.c_int] * 5 + [wt.DWORD] * 8 + [ctypes.c_char_p]
gdi32.SelectObject.restype = wt.HGDIOBJ
gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
gdi32.GetTextExtentPoint32A.argtypes = [wt.HDC, ctypes.c_char_p, ctypes.c_int,
                                        ctypes.POINTER(wt.SIZE)]
gdi32.ExtTextOutA.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, wt.UINT,
                              ctypes.c_void_p, ctypes.c_char_p, wt.UINT, ctypes.c_void_p]
gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
gdi32.CreateDIBSection.restype = wt.HBITMAP

BMPINFO = None


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG),
                ('biPlanes', wt.WORD), ('biBitCount', wt.WORD),
                ('biCompression', wt.DWORD), ('biSizeImage', wt.DWORD),
                ('biXPelsPerMeter', wt.LONG), ('biYPelsPerMeter', wt.LONG),
                ('biClrUsed', wt.DWORD), ('biClrImportant', wt.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wt.DWORD * 3)]


W, H = 320, 60


def render(face, height, weight, text_bytes, charset=0, label=''):
    dc = gdi32.CreateCompatibleDC(None)
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = W
    bi.bmiHeader.biHeight = -H          # top-down
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 24
    bi.bmiHeader.biCompression = 0
    bits = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(dc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
    old = gdi32.SelectObject(dc, hbmp)
    # 全白
    buf = (ctypes.c_ubyte * (W * H * 3)).from_address(bits.value)
    for i in range(len(buf)):
        buf[i] = 0xFF
    hf = gdi32.CreateFontA(height, 0, 0, 0, weight, 0, 0, 0, charset, 0, 0, 0, 0, face)
    oldf = gdi32.SelectObject(dc, hf)

    sz = wt.SIZE()
    gdi32.GetTextExtentPoint32A(dc, text_bytes, len(text_bytes), ctypes.byref(sz))
    gdi32.ExtTextOutA(dc, 4, 6, 0, None, text_bytes, len(text_bytes), None)

    ink = 0
    cols = set()
    for y in range(H):
        for x in range(W):
            o = (y * W + x) * 3
            if buf[o] != 0xFF or buf[o + 1] != 0xFF or buf[o + 2] != 0xFF:
                ink += 1
                cols.add((buf[o], buf[o + 1], buf[o + 2]))
    gdi32.SelectObject(dc, oldf)
    gdi32.DeleteObject(hf)
    gdi32.SelectObject(dc, old)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(dc)
    print('%-26s face=%-16s h=%-3d charset=%-3d 测量宽=%-3d 高=%-2d 墨点数=%-5d 用色数=%d'
          % (label, face, height, charset, sz.cx, sz.cy, ink, len(cols)))
    return sz.cx, ink


print('=== 系统 ACP ===')
k32 = ctypes.WinDLL('kernel32')
print('GetACP() =', k32.GetACP())

cases = [
    (b'\xD7\xB0\xBC\xD7\xCA\xA6', '装甲师 (GBK)'),
    (b'\xB5\xDA1\xD7\xB0\xBC\xD7\xCA\xA6', '第1装甲师 (GBK)'),
    (b'Armor', 'Armor (ASCII)'),
]
for face, hh in ((b'Times New Roman', 18), (b'Times New Roman', 14),
                 (b'MS Sans Serif', 14), (b'MS Sans Serif', 10)):
    print('--- 字体 %s 高度 %d ---' % (face.decode(), hh))
    for tb, lb in cases:
        render(face, hh, 700, tb, 0, lb)

print('--- 对照：charset=134 (GB2312) ---')
for tb, lb in cases:
    render(b'Times New Roman', 18, 700, tb, 134, lb)
print('--- 对照：face=SimSun charset=0 ---')
for tb, lb in cases:
    render(b'SimSun', 18, 700, tb, 0, lb)
print('--- 对照：face=SimSun charset=134 ---')
for tb, lb in cases:
    render(b'SimSun', 18, 700, tb, 134, lb)
