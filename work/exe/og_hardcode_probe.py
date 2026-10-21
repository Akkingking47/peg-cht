# -*- coding: utf-8 -*-
"""OpenGeneral OpenGen.exe —— exe 硬编码串候选普查（只读）。

对每条候选串，报出：
  · 每次出现的 文件偏移 FO / 虚拟地址 VA / 所在段 / **可用槽位**
  · 该 VA 的 `push imm32` 立即数引用数（=1 才属最低风险可改档）
  · 该 VA 的任意 4 字节引用数（>push 数说明还有指针表/其他引用）

槽位算法：串尾的 NUL 之后再吃连续的 0x00 作 padding，直到下一个非 0 字节
（= 下一串的起点）⇒ 可用字节数。译文 `len(gbk)+1 <= 槽位` 才可原地替换。

用法: python og_hardcode_probe.py [目标exe路径]
"""
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\exe")
import pelib

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\OpenGeneral\OpenGen.exe"

CANDIDATES = [
    # --- 已定位 / P0 已改 ---
    "Do you really want to exit ? ... ",
    # --- 底栏与 HUD ---
    "Campaigns' catalog",
    "OG Mode",
    "OG Mode Less",
    "%s * Mode: %d x %d x %d bpp (Click to show Credits)",
    "Click to show Credits",
    "Show tips.",
    "Toggles terrain labels",
    "Show Terrain labels and data",
    "Show terrain labels and roads",
    # --- 单位面板：运动力 / 运输 ---
    "dry - ice - mud - terrain",
    "No RTP pool",
    "Can't use RTP",
    "No RTP available in pool",
    "No RTP matching front/weight",
    "Can use: RTP",
    # --- 天气 / 地面状况 ---
    "Weather is: %s  *  Ground condition: %s",
    "Ground condition: %s",
    "Weather can change ground condition",
    "Ground condition changed! ... ",
    "Frozen ground condition supply: %+d%%",
    "Mud ground condition supply: %+d%%",
    # --- 设置对话框（实机截图里仍是英文） ---
    "Disable Campaigns Dialog at start",
    "Hide windows' task bar",
    "Change to",
    "Keep current",
    "Normal",
    "Tables",
    "No file loaded",
    "No image (%d x %d)",
    # --- efile 选择框 ---
    "   File: %s   [%d scenarios]",
    "Files in folder",
    "Check campaigns & DL missing maps",
]


def main():
    d = open(EXE, "rb").read()
    p = pelib.PE(d)
    print("EXE  %s  %d B" % (EXE, len(d)))
    print("=" * 118)
    print("%-52s %-10s %-11s %-6s %-6s %-5s %s"
          % ("候选串", "FO", "VA", "段", "槽位", "push", "其它4B引用"))
    print("-" * 118)
    for s in CANDIDATES:
        raw = s.encode("ascii")
        hits = []
        i = d.find(raw)
        while i != -1:
            # 必须是完整的 NUL 终结串（前一字节为 0 或段首），避免子串误命中
            if d[i + len(raw)] == 0 and (i == 0 or d[i - 1] == 0):
                hits.append(i)
            i = d.find(raw, i + 1)
        if not hits:
            print("%-52s  ——  未找到" % ("%r" % s)[:52])
            continue
        for fo in hits:
            va = p.fo2va(fo)
            sec, _ = p.fo2sec(fo)
            # 槽位
            j = fo + len(raw) + 1
            while j < len(d) and d[j] == 0:
                j += 1
            slot = j - fo
            # 引用统计
            pat = struct.pack("<I", va)
            n4 = d.count(pat)
            npush = d.count(b"\x68" + pat)
            gbk = len(s.encode("gbk", "ignore")) if s.isascii() else 0
            flag = "✅" if npush == 1 else ("⚠️" if npush == 0 else "❗")
            print("%-52s 0x%06X  0x%08X  %-6s %-6d %-5d %d  gbk原%d"
                  % ((s[:50] + "…" if len(s) > 50 else s), fo, va, sec, slot,
                     npush, n4, len(s)))
            if flag != "✅":
                pass
        print()


if __name__ == "__main__":
    main()
