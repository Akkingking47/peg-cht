# -*- coding: utf-8 -*-
"""只读扫描：找出母本 .text 里对若干目标函数的直接 call 点，以及「整屏刷新标志 0x498D74」的全部引用。
目的：弄清地图/覆盖层（移动范围阴影）到底由谁触发重绘，为什么鼠标不动就不刷新。
"""
import struct

EXE = r"D:\Program Files\PeG\PeG030.exe"
CALL_TARGETS = {
    0x41FF8A: "地图上屏 blit(源矩形/视口)",
    0x41F2C0: "滚动+已绘范围更新器",
    0x41FA85: "整块重绘(逐格)",
    0x41F41C: "逐格绘制 A",
    0x41F685: "逐格绘制 B",
    0x44AC45: "整屏刷新(顶栏/底栏/控件)",
    0x423CD6: "控件循环",
}
FLAG = 0x498D74

data = open(EXE, "rb").read()
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
opt = pe + 24
imgbase = struct.unpack_from("<I", data, opt + 28)[0]
secs = []
off = opt + struct.unpack_from("<H", data, pe + 20)[0]
for i in range(nsec):
    s = off + i * 40
    name = data[s:s + 8].rstrip(b"\x00").decode("latin1")
    vsize, rva, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
    secs.append((name, rva, vsize, rawptr, rawsize))

for name, rva, vsize, rawptr, rawsize in secs:
    if name == ".text":
        t0, t1, tva = rawptr, rawptr + rawsize, imgbase + rva
        break

print("== 直接 call 点 ==")
for target, label in sorted(CALL_TARGETS.items()):
    hits = []
    for i in range(t0, t1 - 5):
        if data[i] == 0xE8:
            rel = struct.unpack_from("<i", data, i + 1)[0]
            va = tva + (i - t0)
            if va + 5 + rel == target:
                hits.append(va)
    print("--- 0x%08X %s : %d 处" % (target, label, len(hits)))
    for va in hits:
        print("      caller VA=0x%08X" % va)

print("== 标志 0x%08X 的引用 ==" % FLAG)
pat = struct.pack("<I", FLAG)
start = 0
n = 0
while True:
    i = data.find(pat, start)
    if i < 0:
        break
    start = i + 1
    if not (t0 <= i < t1):
        continue
    va = tva + (i - t0)
    ctx = data[max(0, i - 8):i + 10]
    print("   VA=0x%08X ctx=%s" % (va, ctx.hex(" ")))
    n += 1
print("   共 %d 处" % n)
