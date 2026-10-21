# -*- coding: utf-8 -*-
"""R1 字体映射探针 v2 —— 每个方案独立成图，便于目视判定「正常出字 / 豆腐块 / 空白」
复刻 PeG030.exe 的 CreateFontA：CreateFontA(-12,0,0,0,400,0,0,0, ANSI_CHARSET,0,0, PROOF_QUALITY,2, NULL)
"""
import ctypes, os, sys
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
gdi = ctypes.WinDLL("gdi32"); user = ctypes.WinDLL("user32"); k32 = ctypes.WinDLL("kernel32")

gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]; gdi.CreateCompatibleDC.restype = wintypes.HDC
gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT, ctypes.c_void_p,
                                 wintypes.HANDLE, wintypes.DWORD]
gdi.CreateDIBSection.restype = wintypes.HBITMAP
gdi.CreateFontA.argtypes = [ctypes.c_int]*5 + [wintypes.DWORD]*8 + [wintypes.LPCSTR]
gdi.CreateFontA.restype = wintypes.HGDIOBJ
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]; gdi.SelectObject.restype = wintypes.HGDIOBJ
gdi.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
gdi.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
gdi.GetTextFaceA.argtypes = [wintypes.HDC, ctypes.c_int, wintypes.LPSTR]
gdi.GetTextExtentPoint32A.argtypes = [wintypes.HDC, wintypes.LPCSTR, ctypes.c_int, ctypes.c_void_p]
gdi.GetGlyphIndicesW.argtypes = [wintypes.HDC, ctypes.c_wchar_p, ctypes.c_int,
                                 ctypes.POINTER(wintypes.WORD), wintypes.DWORD]
user.DrawTextExA.argtypes = [wintypes.HDC, wintypes.LPCSTR, ctypes.c_int,
                             ctypes.POINTER(wintypes.RECT), wintypes.UINT, ctypes.c_void_p]
k32.GetACP.restype = wintypes.UINT
k32.MultiByteToWideChar.argtypes = [wintypes.UINT, wintypes.DWORD, wintypes.LPCSTR,
                                    ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]

class BIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

W, H = 700, 150

def mkW(b):
    n = k32.MultiByteToWideChar(936, 0, b, len(b), None, 0)
    if n <= 0: return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    k32.MultiByteToWideChar(936, 0, b, len(b), buf, n)
    return buf.value

def run(tag, hf, lines, fname):
    bi = BIH(); bi.biSize = ctypes.sizeof(bi); bi.biWidth = W; bi.biHeight = -H
    bi.biPlanes = 1; bi.biBitCount = 32
    hdc = gdi.CreateCompatibleDC(None)
    bits = ctypes.c_void_p()
    hb = gdi.CreateDIBSection(hdc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
    gdi.SelectObject(hdc, hb)
    buf = (ctypes.c_ubyte * (W*H*4)).from_address(bits.value)
    for i in range(0, W*H*4, 4):
        buf[i], buf[i+1], buf[i+2], buf[i+3] = 0x32, 0x2A, 0x22, 0xFF
    old = gdi.SelectObject(hdc, hf)
    face = ctypes.create_string_buffer(64); gdi.GetTextFaceA(hdc, 64, face)
    lf = ctypes.create_string_buffer(128)
    print(f"\n--- {tag} ---")
    print(f"  GDI 选中字面名 = {face.value.decode('latin-1')!r}")
    y = 12
    for txt, col in lines:
        b = txt.encode("gbk", "replace")
        sz = (ctypes.c_long*2)()
        gdi.GetTextExtentPoint32A(hdc, b, len(b), ctypes.byref(sz))
        es = mkW(b)
        gi = (wintypes.WORD * (len(es)+1))()
        gdi.GetGlyphIndicesW(hdc, es, len(es), gi, 1)
        miss = sum(1 for i in range(len(es)) if gi[i] == 0xFFFF)
        gdi.SetBkMode(hdc, 1)
        gdi.SetTextColor(hdc, col)
        rc = wintypes.RECT(8, y, W-4, y+30)
        user.DrawTextExA(hdc, b, len(b), ctypes.byref(rc), 0, None)
        print(f"   {txt!r}")
        print(f"      B={len(b):3d} 字={len(txt):2d} 度量={sz[0]}x{sz[1]}px "
              f"({sz[0]/max(len(txt),1):.1f}px/字) 缺失字形={miss}/{len(es)}")
        y += 34
    n = sum(1 for i in range(0, W*H*4, 4)
            if abs(buf[i]-0x32) > 22 or abs(buf[i+1]-0x2A) > 22 or abs(buf[i+2]-0x22) > 22)
    print(f"   非背景像素合计 = {n}")
    gdi.SelectObject(hdc, old)
    from PIL import Image
    im = Image.new("RGB", (W, H))
    raw = bytes(buf)
    im.putdata([(raw[i+2], raw[i+1], raw[i]) for i in range(0, W*H*4, 4)])
    p = os.path.join(OUT, fname); im.save(p); print("   写出:", p)

print("GetACP() =", k32.GetACP())
EN  = ("United States  Russia  China  Vietnam  Next Unit", 0x00D8D8D8)
ZH1 = ("美国 俄罗斯 中国 越南 朝鲜 韩国 泰国 统一", 0x00FFFFFF)
ZH2 = ("战斗工兵 防空 装甲 侦察 战列巡洋舰 移动", 0x0060FFA0)

f1 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 2, 2, None)          # exe 原参数
run("① exe 原参数 face=NULL + ANSI_CHARSET(0) + 12px", f1, [EN, ZH1, ZH2], "R1-a-original.png")

f2 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 134, 0, 0, 2, 2, b"SimSun")   # 补丁 A
run("② 补丁 A：face=\"SimSun\" + GB2312_CHARSET(134)", f2, [EN, ZH1, ZH2], "R1-b-simsun-134.png")

f3 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 2, 2, b"SimSun")     # 补丁 B：仅换字面名
run("③ 补丁 B：face=\"SimSun\" + ANSI_CHARSET(0)", f3, [EN, ZH1, ZH2], "R1-c-simsun-ansi.png")

f4 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 0, 0, 0, 2, 2, b"\xcb\xce\xcc\xe5")  # 宋体(GBK)
run("④ 补丁 C：face=\"宋体\"(GBK 字节) + ANSI_CHARSET(0)", f4, [EN, ZH1, ZH2], "R1-d-songti.png")

f5 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 134, 0, 0, 2, 2,
                     b"\xcb\xce\xcc\xe5")                                       # 宋体 + 134
run("⑤ 补丁 D：face=\"宋体\" + GB2312_CHARSET(134)", f5, [EN, ZH1, ZH2], "R1-e-songti-134.png")

f6 = gdi.CreateFontA(-12, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 2, 2, b"MS Sans Serif")
run("⑥ 对话框字体 MS Sans Serif 8pt + DEFAULT_CHARSET(1)", f6, [EN, ZH1, ZH2], "R1-f-dialog.png")
print("\ndone")
