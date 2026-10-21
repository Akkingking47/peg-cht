# -*- coding: utf-8 -*-
"""渲染对照图：不同字体名/高度下 GBK 汉字的实际效果（只读，不影响游戏）。"""
import ctypes
from ctypes import wintypes as wt
from PIL import Image

g = ctypes.WinDLL('gdi32', use_last_error=True)
g.CreateCompatibleDC.restype = wt.HDC
g.CreateCompatibleDC.argtypes = [wt.HDC]
g.CreateDIBSection.restype = wt.HBITMAP
g.CreateDIBSection.argtypes = [wt.HDC, ctypes.c_void_p, wt.UINT,
                               ctypes.POINTER(ctypes.c_void_p), wt.HANDLE, wt.DWORD]
g.CreateFontA.restype = wt.HFONT
g.CreateFontA.argtypes = [ctypes.c_int] * 5 + [wt.DWORD] * 8 + [ctypes.c_char_p]
g.SelectObject.restype = wt.HGDIOBJ
g.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
g.ExtTextOutA.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int, wt.UINT,
                          ctypes.c_void_p, ctypes.c_char_p, wt.UINT, ctypes.c_void_p]
g.GetTextExtentPoint32A.argtypes = [wt.HDC, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(wt.SIZE)]
g.DeleteObject.argtypes = [wt.HGDIOBJ]
g.DeleteObject.restype = wt.BOOL
g.DeleteDC.argtypes = [wt.HDC]


class BIH(ctypes.Structure):
    _fields_ = [('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG),
                ('biPlanes', wt.WORD), ('biBitCount', wt.WORD), ('biCompression', wt.DWORD),
                ('biSizeImage', wt.DWORD), ('biXPelsPerMeter', wt.LONG),
                ('biYPelsPerMeter', wt.LONG), ('biClrUsed', wt.DWORD), ('biClrImportant', wt.DWORD)]


class BI(ctypes.Structure):
    _fields_ = [('bmiHeader', BIH), ('bmiColors', wt.DWORD * 3)]


def shot(face, h, cs, txt, out, W=560, H=44):
    dc = g.CreateCompatibleDC(None)
    bi = BI()
    bi.bmiHeader.biSize = ctypes.sizeof(BIH)
    bi.bmiHeader.biWidth = W
    bi.bmiHeader.biHeight = -H
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 24
    bits = ctypes.c_void_p()
    hb = g.CreateDIBSection(dc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
    g.SelectObject(dc, hb)
    buf = (ctypes.c_ubyte * (W * H * 3)).from_address(bits.value)
    for i in range(len(buf)):
        buf[i] = 0xFF
    hf = g.CreateFontA(h, 0, 0, 0, 700, 0, 0, 0, cs, 0, 0, 0, 0, face)
    g.SelectObject(dc, hf)
    sz = wt.SIZE()
    g.GetTextExtentPoint32A(dc, txt, len(txt), ctypes.byref(sz))
    g.ExtTextOutA(dc, 3, 3, 0, None, txt, len(txt), None)
    Image.frombytes('RGB', (W, H), bytes(buf)).save(out)
    print('%-22s h=%-3d cs=%-3d 宽=%-4d 高=%-3d -> %s'
          % (face.decode(), h, cs, sz.cx, sz.cy, out))
    g.DeleteObject(hf)
    g.DeleteObject(hb)
    g.DeleteDC(dc)


T = b'\xD7\xB0\xBC\xD7\xCA\xA6'          # 装甲师
T2 = b'\xB5\xDA1\xD7\xB0\xBC\xD7\xCA\xA6 Armor'  # 第1装甲师
shot(b'MS Sans Serif', 14, 0, T, 'view/p_msss14.png')
shot(b'MS Sans Serif', 12, 0, T, 'view/p_msss12.png')
shot(b'MS Sans Serif', 10, 0, T, 'view/p_msss10.png')
shot(b'Times New Roman', 14, 0, T2, 'view/p_tnr14.png')
shot(b'Times Roman', 10, 0, T, 'view/p_tr10.png')
shot(b'Times New Roman', 24, 0, T2, 'view/p_tnr24.png')
