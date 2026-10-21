# -*- coding: utf-8 -*-
"""扫描母本 .text 里残留的「旧屏幕尺寸」立即数（800/600/572/796/550 等），
并与 peg_launcher 的现有计划做差集 => 列出**还没打**的屏幕尺寸常量，作为下一组（O 组）候选。
只读。
"""
import sys, struct
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import peg_launcher as PL

EXE = r"D:\Program Files\PeG\PeG030.exe"
CONSTS = [
    (0x320, "800", 4), (0x258, "600", 4), (0x23C, "572", 4), (0x31C, "796", 4),
    (0x226, "550", 4), (0x2FA, "762", 4), (0x313, "787", 4), (0x2BC, "700", 4),
    (0x1F4, "500", 4), (0x2D0, "720", 4), (0x190, "400", 4), (0x12C, "300", 4),
    (0xE1, "225", 4), (0x64, "100", 4),
]

entries, notes = PL.build_plan(1920, 1080)
planned = {}
for e in entries:
    if isinstance(e, dict):
        planned[e["va"]] = e.get("size", 0)
print("计划条目：%d" % len(entries))

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

def loc(foff):
    for name, rva, vsize, rawptr, rawsize in secs:
        if rawptr <= foff < rawptr + rawsize:
            return name, imgbase + rva + (foff - rawptr)
    return None, None

for val, label, _ in CONSTS:
    pat = struct.pack("<I", val)
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    out = []
    for i in hits:
        name, va = loc(i)
        if name != ".text":
            continue
        covered = (va in planned) or ((va - 2) in planned) or ((va + 2) in planned)
        if not covered:
            ctx = data[max(0, i - 12):i + 10]
            out.append("0x%08X  ctx=%s" % (va, ctx.hex(" ")))
    print("=== %s (0x%X)  .text 未打补丁共 %d 处 ===" % (label, val, len(out)))
    for line in out[:40]:
        print("   " + line)
