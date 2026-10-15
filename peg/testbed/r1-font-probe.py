# -*- coding: utf-8 -*-
"""R1 字体映射探针 —— 精确复刻 PeG030.exe 的 CreateFontA 调用，离线测中文是否可渲染
复刻参数（VA 0x4718FA，反汇编实证）：
  CreateFontA(-12, 0,0,0, FW_NORMAL(400), 0,0,0, ANSI_CHARSET(0), 0,0,
              PROOF_QUALITY(2), DEFAULT_PITCH|FF_DONTCARE(2), NULL)
输出：peg/testbed/out/*.png + 控制台度量
"""
import ctypes, os, sys, struct
from ctypes import wintypes

OUT = r"D:\DSH\军事游戏汉化\peg\testbed\out"
os.makedirs(OUT, exist_ok=True)

gdi = ctypes.WinDLL("gdi32")
user = ctypes.WinDLL("user32")
k32 = ctypes.WinDLL("kernel32")

gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]; gdi.CreateCompatibleDC.restype = wintypes.HDC
gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                 ctypes.c_void_p, wintypes.HANDLE, wintypes.DWORD]
gdi.CreateDIBSection.restype = wintypes.HBITMAP
gdi.CreateFontA.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD] * 8 + [wintypes.LPCSTR]
gdi.CreateFontA.restype = wintypes.HGDIOBJ
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]; gdi.SelectObject.restype = wintypes.HGDIOBJ
gdi.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi.GetTextFaceA.argtypes = [wintypes.HDC, ctypes.c_int, wintypes.LPSTR]
gdi.GetTextExtentPoint32A.argtypes = [wintypes.HDC, wintypes.LPCSTR, ctypes.c_int, ctypes.c_void_p]
gdi.GetGlyphIndicesW.argtypes = [wintypes.HDC, ctypes.c_wchar_p, ctypes.c_int,
                                 ctypes.POINTER(wintypes.WORD), wintypes.DWORD]
gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
user.DrawTextExA.argtypes = [wintypes.HDC, wintypes.LPCSTR, ctypes.c_int,
                             ctypes.POINTER(wintypes.RECT), wintypes.UINT, ctypes.c_void_p]
k32.GetACP.restype = wintypes.UINT
k32.MultiByteToWideChar.argtypes = [wintypes.UINT, wintypes.DWORD, wintypes.LPCSTR,
                                    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]

W, H = 760, 260
class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]

print("=== 环境 ===")
print("  GetACP() =", k32.GetACP(), "(936 = 简体中文 GBK)")
print("  GetOEMCP()=", k32.GetOEMCP())
print("  python  :", sys.version.split()[0])

bi = BITMAPINFOHEADER()
bi.biSize = ctypes.sizeof(bi); bi.biWidth = W; bi.biHeight = -H
bi.biPlanes = 1; bi.biBitCount = 32; bi.biCompression = 0
hdc = gdi.CreateCompatibleDC(None)
bits = ctypes.c_void_p()
hbmp = gdi.CreateDIBSection(hdc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
gdi.SelectObject(hdc, hbmp)
# 背景：深灰（模拟游戏底图）
buf = (ctypes.c_ubyte * (W * H * 4)).from_address(bits.value)
for i in range(0, W * H * 4, 4):
    buf[i], buf[i+1], buf[i+2], buf[i+3] = 0x30, 0x28, 0x20, 0xFF

def gbk(s):
    return s.encode("gbk", "replace")

def mkW(b):
    """GBK 字节 -> UTF-16 (经 CP936)，复刻 GDI 内部 A->W 转换"""
    n = k32.MultiByteToWideChar(936, 0, b, len(b), None, 0)
    if n <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    k32.MultiByteToWideChar(936, 0, b, len(b), buf, n)
    return buf.value

def extent(hdc, b):
    sz = (ctypes.c_long * 2)()
    gdi.GetTextExtentPoint32A(hdc, b, len(b), ctypes.byref(sz))
    return sz[0], sz[1]

def make_font(height, weight, charset, quality, pitch, face):
    return gdi.CreateFontA(height, 0, 0, 0, weight, 0, 0, 0, charset, 0, 0,
                           quality, pitch, face)

def measure_and_draw(tag, hf, lines, clip=True):
    """lines: [(文本, 颜色)]"""
    old = gdi.SelectObject(hdc, hf)
    face = ctypes.create_string_buffer(64)
    gdi.GetTextFaceA(hdc, 64, face)
    gdi.SetBkMode(hdc, 1)  # TRANSPARENT
    print(f"\n--- {tag} ---")
    print(f"  GDI 实际选中的字面名: {face.value.decode('latin-1')!r}")
    y = 20
    for txt, col in lines:
        b = gbk(txt)
        w, h = extent(hdc, b)
        # 字形覆盖
        ws = mkW(b)
        gi = (wintypes.WORD * (len(ws) + 1))()
        gdi.GetGlyphIndicesW(hdc, ws, len(ws), gi, 1)  # GGI_MARK_NONEXISTING_GLYPHS
        miss = sum(1 for i in range(len(ws)) if gi[i] == 0xFFFF)
        gdi.SetTextColor(hdc, col)
        rc = wintypes.RECT(16, y, W - 8, y + 26)
        user.DrawTextExA(hdc, b, len(b), ctypes.byref(rc), 0, None)
        print(f"   {txt[:52]!r}")
        print(f"      bytes={len(b):3d}  chars={len(txt):2d}  "
              f"GetTextExtent={w}x{h}px (平均 {w/max(len(txt),1):.1f} px/字)  "
              f"缺失字形={miss}/{len(ws)}")
        y += 30
    gdi.SelectObject(hdc, old)
    return y

# ---- 1) 游戏内正文：完全复刻 exe 参数 ----
hf_game = make_font(-12, 400, 0, 2, 2, None)
yb = 0
measure_and_draw("① 游戏内正文（exe 原参数：face=NULL, ANSI_CHARSET, 12px, PROOF_QUALITY）",
                 hf_game,
                 [("United States  Russia  China  Vietnam", 0x00E0E0E0),
                  ("美国 俄罗斯 中国 越南 朝鲜 韩国", 0x00FFFFFF),
                  ("战斗工兵 防空 装甲 侦察 战列巡洋舰", 0x0060FFA0)])
y1 = 20 + 3 * 30

# ---- 2) 若补丁为 GB2312_CHARSET(134) + face="SimSun" ----
hf_patch = make_font(-12, 400, 134, 2, 2, b"SimSun")
measure_and_draw("② 补丁方案 A：face=\"SimSun\", GB2312_CHARSET(134)",
                 hf_patch,
                 [("美国 俄罗斯 中国 越南 朝鲜 韩国", 0x00FFFFFF),
                  ("战斗工兵 防空 装甲 侦察 战列巡洋舰", 0x0060FFA0)])

# ---- 3) 对话框字体 MS Sans Serif 8pt ----
hf_dlg = make_font(-11, 400, 1, 2, 2, b"MS Sans Serif")
measure_and_draw("③ 对话框字体：MS Sans Serif 8pt, DEFAULT_CHARSET(1)",
                 hf_dlg,
                 [("Enter number", 0x00E0E0E0),
                  ("输入数量", 0x00FFFFFF),
                  ("选择国家  创建军团", 0x0060FFA0)])

# ---- 4) 20 字节字段容量实测（R12）----
print("\n--- ④ R12 定长字段容量实测（字段 20 B，含 NUL）---")
old = gdi.SelectObject(hdc, hf_game)
for s in ["美国", "英国", "战列巡洋舰", "United States", "Battle Cruiser"]:
    b = gbk(s)
    fit = "OK" if len(b) <= 19 else "!! 超长"
    print(f"   {s!r:24s} GBK {len(b):2d} B  {fit}")
gdi.SelectObject(hdc, old)
gdi.DeleteObject(hf_game); gdi.DeleteObject(hf_patch); gdi.DeleteObject(hf_dlg)

# ---- 存 PNG ----
from PIL import Image
im = Image.new("RGB", (W, H))
raw = bytes(buf)
px = [(raw[i+2], raw[i+1], raw[i], 255) for i in range(0, W*H*4, 4)]
im.putdata(px)
p = os.path.join(OUT, "R1-font-probe.png"); im.save(p)
print("\n写出:", p, im.size)

# 中文像素上色统计
def nonbg(y0, y1):
    n = 0
    for y in range(y0, y1):
        for x in range(W):
            i = (y*W+x)*4
            if abs(raw[i]-0x30) > 24 or abs(raw[i+1]-0x28) > 24 or abs(raw[i+2]-0x20) > 24:
                n += 1
    return n
print("各行带非背景像素（画出东西了）统计，供判「不出字/空白」：")
print("  行1 英文  :", nonbg(20, 44))
print("  行2 中文  :", nonbg(50, 74))
print("  行3 中文  :", nonbg(80, 104))
