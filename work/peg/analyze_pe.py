# -*- coding: utf-8 -*-
"""PeG (People's General) 汉化可行性 - PE 层静态分析
分析：子系统的渲染/文本/输入相关导入，字符集，字体线索。
"""
import pefile, sys, os, re, collections

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────



# 关注的关键 API（按用途分组）
WATCH = {
    "GDI-文本输出": ["TextOutA", "TextOutW", "ExtTextOutA", "ExtTextOutW", "DrawTextA",
                    "DrawTextW", "DrawTextExA", "DrawTextExW", "GetTextExtentPoint32A",
                    "GetTextExtentPoint32W", "GetTextExtentPointA", "GetCharWidth32A",
                    "GetCharWidthA", "SetTextColor", "SetBkColor", "SelectObject"],
    "GDI-字体创建": ["CreateFontA", "CreateFontW", "CreateFontIndirectA",
                    "CreateFontIndirectW", "CreateFontIndirectExA", "EnumFontFamiliesA",
                    "EnumFontFamiliesExA", "GetStockObject", "AddFontResourceA",
                    "CreateFontIndirect", "GetGlyphOutlineA", "GetFontData"],
    "GDI-位图/表面": ["CreateCompatibleDC", "CreateCompatibleBitmap", "BitBlt",
                     "StretchBlt", "CreateDIBSection", "SetDIBitsToDevice",
                     "StretchDIBits", "GetDIBits", "CreateBitmap", "CreatePalette",
                     "SelectPalette", "RealizePalette", "GetSystemPaletteEntries",
                     "SetSystemPaletteUse", "CreateHalftonePalette"],
    "Unicode/编码": ["MultiByteToWideChar", "WideCharToMultiByte", "GetACP",
                    "GetOEMCP", "GetCPInfo", "GetCPInfoExA", "IsDBCSLeadByte",
                    "GetStringTypeA", "GetStringTypeW", "LCMapStringA", "LCMapStringW",
                    "CharToOemA", "OemToCharA", "GetLocaleInfoA"],
    "键盘/输入": ["GetKeyboardState", "GetAsyncKeyState", "MapVirtualKeyA",
                "MapVirtualKeyExA", "ToAscii", "ToAsciiEx", "ToUnicode",
                "GetKeyNameTextA", "TranslateAcceleratorA", "GetKeyboardLayout",
                "ActivateKeyboardLayout", "PeekMessageA", "PeekMessageW",
                "GetMessageA", "GetMessageW", "DispatchMessageA", "DispatchMessageW",
                "IME", "ImmGetContext", "ImmSetCompositionFontA"],
    "窗口": ["CreateWindowExA", "CreateWindowExW", "RegisterClassA", "RegisterClassW",
             "DefWindowProcA", "DefWindowProcW", "SendMessageA", "SendMessageW",
             "WindowFromPoint", "SetWindowsHookExA"],
    "DirectX": ["DirectDrawCreate", "DirectDrawCreateEx", "DirectDrawEnumerateA",
                "DirectDrawEnumerateExA", "DirectDrawEnumerateW",
                "DirectInputCreateA", "DirectInput8Create", "DirectSoundCreate",
                "CreateSurface", "SetCooperativeLevel", "SetDisplayMode"],
    "音频/其他": ["MciSendStringA", "PlaySoundA", "sndPlaySoundA", "mciSendCommandA",
                 "GetPrivateProfileStringA", "WritePrivateProfileStringA",
                 "RegQueryValueExA", "GetModuleFileNameA"],
}

ALL_WATCH = {}
for grp, names in WATCH.items():
    for n in names:
        ALL_WATCH[n.lower()] = grp


def analyze(path):
    print("=" * 78)
    print("FILE:", path, f"({os.path.getsize(path)} bytes)")
    try:
        pe = pefile.PE(path, fast_load=True)
        pe.parse_data_directories(directories=[
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
            pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'],
        ])
    except Exception as e:
        print("  !! parse error:", e)
        return

    print(f"  Machine        : {pe.FILE_HEADER.Machine:#x} ({'PE32' if pe.FILE_HEADER.Machine==0x14c else 'PE32+'})")
    print(f"  Subsystem      : {pe.OPTIONAL_HEADER.Subsystem} "
          f"({'GUI' if pe.OPTIONAL_HEADER.Subsystem==2 else 'CONSOLE' if pe.OPTIONAL_HEADER.Subsystem==3 else '?'})")
    print(f"  ImageBase      : {pe.OPTIONAL_HEADER.ImageBase:#x}")
    print(f"  EntryPoint     : {pe.OPTIONAL_HEADER.AddressOfEntryPoint:#x}")
    timestamp = pe.FILE_HEADER.TimeDateStamp
    import datetime
    try:
        print(f"  TimeDateStamp  : {datetime.datetime.utcfromtimestamp(timestamp)} UTC")
    except Exception:
        pass
    print(f"  Checksum       : {pe.OPTIONAL_HEADER.CheckSum:#x}")
    # 是否声明 Unicode 子系统 / 代码页相关
    print(f"  DllCharacteristics: {pe.OPTIONAL_HEADER.DllCharacteristics:#x}")
    print(f"  SizeOfImage    : {pe.OPTIONAL_HEADER.SizeOfImage:#x}")
    print(f"  SizeOfCode/InitData/UninitData : "
          f"{pe.OPTIONAL_HEADER.SizeOfCode:#x}/{pe.OPTIONAL_HEADER.SizeOfInitializedData:#x}/"
          f"{pe.OPTIONAL_HEADER.SizeOfUninitializedData:#x}")

    # 节表
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode("latin-1")
        print(f"    sect {nm:9s} VA={pe.OPTIONAL_HEADER.ImageBase+s.VirtualAddress:#010x} "
              f"VS={s.Misc_VirtualSize:#08x} RAW={s.SizeOfRawData:#08x} "
              f"PtrRaw={s.PointerToRawData:#08x} Ch={s.Characteristics:#010x}")

    # 导入表
    imports = collections.OrderedDict()
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll = entry.dll.decode("latin-1", "replace")
            fns = []
            for imp in entry.imports:
                fns.append(imp.name.decode("latin-1") if imp.name else f"ord#{imp.ordinal}")
            imports[dll] = fns
    print("  --- 导入的 DLL ---")
    for dll, fns in imports.items():
        print(f"    {dll}  ({len(fns)} fns)")
    print("  --- 命中的关键 API ---")
    hits = collections.defaultdict(list)
    total = 0
    for dll, fns in imports.items():
        for f in fns:
            base = f.split(".")[0]
            g = ALL_WATCH.get(base.lower())
            if g:
                hits[g].append(f"{dll}!{f}")
                total += 1
    for grp in WATCH:
        if hits[grp]:
            print(f"    [{grp}] {len(hits[grp])}")
            for h in hits[grp]:
                print(f"        {h}")
    print(f"  (关键 API 命中合计 {total})")
    return pe, imports


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else [
        "PeG030.exe", "LG_SuitePeG.exe", "PeG010.exe", "PeG020.exe",
    ]
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(GAME, t)
        if os.path.exists(p):
            analyze(p)
        else:
            print("MISSING:", p)
