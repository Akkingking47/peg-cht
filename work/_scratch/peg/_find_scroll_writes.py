# -*- coding: utf-8 -*-
"""扫描母本 .text 里所有引用 0x4af2f8(scrollX) / 0x4af2fc(scrollY) 的绝对地址指令，
并按指令形式分类（写入 / 读取），用于找出「谁把 scrollX 设成负数」。
只读，不改任何文件。
"""
import struct, sys

EXE = r"D:\Program Files\PeG\PeG030.exe"
TARGETS = {0x4AF2F8: "scrollX", 0x4AF2FC: "scrollY"}

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

def va_of(foff):
    for name, rva, vsize, rawptr, rawsize in secs:
        if rawptr <= foff < rawptr + rawsize:
            return imgbase + rva + (foff - rawptr)
    return None

def sec_of(foff):
    for name, rva, vsize, rawptr, rawsize in secs:
        if rawptr <= foff < rawptr + rawsize:
            return name
    return "?"

# 指令形式：(前缀字节, 名称, 是否写入, 操作数长度)
FORMS = [
    (b"\x66\x89\x15", "mov [m], dx", True, 2),
    (b"\x66\x89\x0d", "mov [m], cx", True, 2),
    (b"\x66\x89\x1d", "mov [m], bx", True, 2),
    (b"\x66\x89\x05", "mov [m], ax", True, 2),
    (b"\x66\x89\x35", "mov [m], si", True, 2),
    (b"\x66\x89\x3d", "mov [m], di", True, 2),
    (b"\x66\xa3",     "mov [m], ax", True, 2),
    (b"\x89\x15",     "mov [m], edx", True, 4),
    (b"\x89\x0d",     "mov [m], ecx", True, 4),
    (b"\x89\x05",     "mov [m], eax", True, 4),
    (b"\xa3",         "mov [m], eax", True, 4),
    (b"\x66\xc7\x05", "mov word [m], imm16", True, 2),
    (b"\xc7\x05",     "mov dword [m], imm32", True, 4),
    (b"\x66\x8b\x15", "mov dx, [m]", False, 2),
    (b"\x66\x8b\x0d", "mov cx, [m]", False, 2),
    (b"\x66\x8b\x05", "mov ax, [m]", False, 2),
    (b"\x8b\x15",     "mov edx, [m]", False, 4),
    (b"\x8b\x0d",     "mov ecx, [m]", False, 4),
    (b"\x8b\x05",     "mov eax, [m]", False, 4),
    (b"\x66\xa1",     "mov ax, [m]", False, 2),
    (b"\xa1",         "mov eax, [m]", False, 4),
]

for addr, label in TARGETS.items():
    pat = struct.pack("<I", addr)
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    print("=== %s  0x%08X  .text 引用 %d 处 ===" % (label, addr, len(hits)))
    for i in hits:
        va = va_of(i)
        if va is None or sec_of(i) != ".text":
            continue
        kind, name = "?", "?"
        for pre, nm, wr, ln in FORMS:
            j = i - len(pre)
            if j >= 0 and data[j:i] == pre:
                kind = "写" if wr else "读"
                name = nm
                break
        ctx = data[max(0, i - 16):i + 12]
        print("  %-4s %-16s VA=0x%08X  ctx=%s" % (kind, name, va, ctx.hex(" ")))
