# -*- coding: utf-8 -*-
"""终检：最终 exe vs 原版
  ① 所有改动区间是否落在 PE 数据目录内（LoadConfig/Debug/Import/IAT…）
  ② 长度 / PE 签名 / 段表是否完好
  ③ 踩坑空洞 0x51CB31 是否已恢复全 NUL
  ④ 新空洞内容核对
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\exe")
import pelib

FINAL = r"D:\OpenPG2\OpenGen.exe"
ORIG = r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.original"

a = open(ORIG, "rb").read()
b = open(FINAL, "rb").read()
print("原版 md5 %s" % hashlib.md5(a).hexdigest())
print("最终 md5 %s" % hashlib.md5(b).hexdigest())
print("长度 %d -> %d  %s" % (len(a), len(b), "一致 ✅" if len(a) == len(b) else "不一致 ❌"))
print("PE 签名/段表一致: %s" % ("✅" if a[:0x400] == b[:0x400] else "❌（前 1KB 有改动）"))

p = pelib.PE(b)
print("\n== ① 改动区间 vs PE 数据目录 ==")
n = min(len(a), len(b))
pts = [i for i in range(n) if a[i] != b[i]]
runs = []
for i in pts:
    if runs and i - runs[-1][1] <= 16:
        runs[-1][1] = i
    else:
        runs.append([i, i])
print("差异字节 %d，区间 %d 个" % (len(pts), len(runs)))
bad = 0
sec_count = {}
for lo, hi in runs:
    sec, _ = p.fo2sec(lo)
    sec_count[sec] = sec_count.get(sec, 0) + 1
    hit = [nm for nm, rva, size, dfo, deo in p.dirs
           if lo < deo + 32 and hi + 1 > dfo - 32]
    if hit:
        bad += 1
        print("  ❌ FO 0x%06X..0x%06X 命中数据目录 %s" % (lo, hi, hit))
print("  按段统计: %s" % sec_count)
print("  %s" % ("✅ 无任何改动落在数据目录内" if bad == 0 else "❌ 有 %d 处落入数据目录" % bad))

print("\n== ③ 踩坑空洞 0x51CB31..0x51CB70 (LoadConfig) ==")
seg = b[0x51CB30:0x51CB70]
print("  %s" % ("✅ 已恢复全 NUL（与原版逐字节相同: %s）"
              % (a[0x51CB30:0x51CB70] == seg) if seg.count(0) == len(seg)
              else "❌ 仍有非 0 内容: %s" % seg.hex()))
print("  与原版逐字节相同: %s" % (a[0x51CB30:0x51CB70] == seg))

print("\n== ④ 新空洞 0x4B1A9A ==")
seg = b[0x4B1A9A:0x4B1A9A + 54]
print("  %s" % " ".join("%02X" % x for x in seg))
i = 0
while i < 54:
    if seg[i]:
        j = seg.find(b"\x00", i)
        print("   +%-2d %r" % (i, seg[i:j].decode("gbk", "replace")))
        i = j + 1
    else:
        i += 1

print("\n== 五条短串的指针 ==")
for ref_fo, name in [(0x412D26, "TBD"), (0x419A3E, "OTP"), (0x41ADCF, "Gnd"),
                     (0x41ADC6, "Air"), (0x41801D, "%s (Mv=%d)")]:
    va, = struct.unpack_from("<I", b, ref_fo)
    fo = va - 0x400E00
    s = b[fo:b.find(b"\x00", fo)].decode("gbk", "replace")
    print("  %-14s push/mov@FO 0x%X -> VA 0x%08X  %r  (FO 0x%X)" % (name, ref_fo, va, s, fo))
