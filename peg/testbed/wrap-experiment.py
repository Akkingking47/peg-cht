# -*- coding: utf-8 -*-
"""离线实验：复刻 exe 的绘制方式（DT_WORDBREAK 强制 + 固定矩形），
扫描矩形宽度/高度，看中文标签会怎样折行/截断，与实机截图比对，反推矩形尺寸。
"""
import ctypes, os
from ctypes import wintypes
from PIL import Image

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


OUT = os.path.join(WS, "peg", "testbed", "out")
os.makedirs(OUT, exist_ok=True)
gdi = ctypes.WinDLL("gdi32"); user = ctypes.WinDLL("user32")

gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]; gdi.CreateCompatibleDC.restype = wintypes.HDC
gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p,
                                 wintypes.HANDLE, wintypes.DWORD]
gdi.CreateDIBSection.restype = wintypes.HBITMAP
gdi.CreateFontA.argtypes = [ctypes.c_int]*5 + [wintypes.DWORD]*8 + [wintypes.LPCSTR]
gdi.CreateFontA.restype = wintypes.HGDIOBJ
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]; gdi.SelectObject.restype = wintypes.HGDIOBJ
gdi.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
user.DrawTextExA.argtypes = [wintypes.HDC, wintypes.LPCSTR, ctypes.c_int,
                             ctypes.POINTER(wintypes.RECT), wintypes.UINT, ctypes.c_void_p]
user.DrawTextExA.restype = ctypes.c_int

class BIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

W, H = 260, 420
bi = BIH(); bi.biSize = ctypes.sizeof(bi); bi.biWidth = W; bi.biHeight = -H
bi.biPlanes = 1; bi.biBitCount = 32
hdc = gdi.CreateCompatibleDC(None)
bits = ctypes.c_void_p()
hb = gdi.CreateDIBSection(hdc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
gdi.SelectObject(hdc, hb)
buf = (ctypes.c_ubyte * (W*H*4)).from_address(bits.value)
for i in range(0, W*H*4, 4):
    buf[i], buf[i+1], buf[i+2], buf[i+3] = 0x40, 0x38, 0x30, 0xFF

hf = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 2, 2, None)
gdi.SelectObject(hdc, hf)
gdi.SetBkMode(hdc, 1)
gdi.SetTextColor(hdc, 0x00FFFFFF)

# 复刻 helper 0x4717FD：format = 调用方 flags | 0x10
DT_WORDBREAK = 0x10
print("矩形宽度扫描（高 14px，DT_WORDBREAK 强制），串='购买单位'(8B):")
DATA = b"\xb9\xba\xc2\xf2\xb5\xa5\xce\xbb"
y = 6
for w in (16, 20, 24, 28, 32, 36, 40, 44, 48, 56):
    rc = wintypes.RECT(12, y, 12 + w, y + 14)
    r = user.DrawTextExA(hdc, DATA, len(DATA), ctypes.byref(rc), DT_WORDBREAK, None)
    print(f"  W={w:3d} 返回值(行高)={r}")
    y += 40
# 再画一列：不同高度
y = 6
for w, h in ((36, 14), (36, 20), (36, 26), (48, 14), (24, 14), (30, 14)):
    rc = wintypes.RECT(150, y, 150 + w, y + h)
    user.DrawTextExA(hdc, DATA, len(DATA), ctypes.byref(rc), DT_WORDBREAK, None)
    print(f"  右列 W={w} H={h} @y={y}")
    y += 60

im = Image.new("RGB", (W, H)); raw = bytes(buf)
im.putdata([(raw[i+2], raw[i+1], raw[i]) for i in range(0, W*H*4, 4)])
p = os.path.join(OUT, "wrap-experiment.png"); im.save(p)
print("写出:", p, im.size)

# 同时给出「每行可容字数」表
print("\n理论每行字数 = floor(矩形宽 / 12px)：")
for w in (16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 96):
    print(f"   W={w:3d} -> {w//12} 字")
