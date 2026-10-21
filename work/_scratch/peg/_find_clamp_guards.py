# -*- coding: utf-8 -*-
"""找出「把 scrollX/scrollY 钳到 max（可能为负）」的站点及其守卫 cmp+jcc。

站点特征：紧邻 store 之前的计算形如
    sub edx, eax / add edx, 1 / sub ecx, edx / sub ecx, 1    (或 sub eax,ecx 变体)
守卫特征：store 之前 ~40 字节内有一条 `3b <reg>` (cmp r32,r32) 紧跟 `7e/7d/7f/7c` (jle/jge/jg/jl)，
          且跳转目标落在 store 之后。把 cmp 改成 `3b c0` (cmp eax,eax) 即可让 ZF=1 恒跳，跳过 store。
只读。
"""
import struct

EXE = r"D:\Program Files\PeG\PeG030.exe"
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

def foff_of(va):
    r = va - imgbase
    for name, rva, vsize, rawptr, rawsize in secs:
        if rva <= r < rva + vsize:
            return rawptr + (r - rva)
    return None

JCC = {0x7E: "jle", 0x7D: "jge", 0x7F: "jg", 0x7C: "jl", 0x74: "je", 0x75: "jne"}

for addr, label in ((0x4AF2F8, "scrollX"), (0x4AF2FC, "scrollY")):
    pat = struct.pack("<I", addr)
    print("=== %s 0x%08X ===" % (label, addr))
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    for i in hits:
        va = va_of(i)
        if va is None:
            continue
        # store 指令起点
        kind = None
        for pre, nm in ((b"\x66\x89\x15", "mov [m],dx"), (b"\x66\x89\x0d", "mov [m],cx"),
                        (b"\x66\x89\x1d", "mov [m],bx"), (b"\x66\x89\x05", "mov [m],ax"),
                        (b"\x66\xa3", "mov [m],ax"), (b"\x66\x89\x35", "mov [m],si"),
                        (b"\x66\x89\x3d", "mov [m],di")):
            j = i - len(pre)
            if j >= 0 and data[j:i] == pre:
                kind = (j, nm, len(pre))
                break
        if not kind:
            continue
        sto, nm, ln = kind
        store_va = va_of(i)
        pre_window = data[max(0, i - 46):sto]
        # 计算特征：sub/add 系列的钳位（含 83 c2 01 / 83 c0 01 / 83 e9 01 / 83 ea 01）
        has_clamp_calc = (b"\x83\xc2\x01" in pre_window and b"\x83\xe9\x01" in pre_window) or \
                         (b"\x83\xc0\x01" in pre_window and b"\x83\xea\x01" in pre_window) or \
                         (b"\x83\xc0\x01" in pre_window and b"\x83\xe9\x01" in pre_window) or \
                         (b"\x83\xc2\x01" in pre_window and b"\x83\xea\x01" in pre_window)
        # 守卫：窗口里找 3b ?? + jcc
        guard = None
        for k in range(len(pre_window) - 1):
            if pre_window[k] == 0x3B and pre_window[k + 1] not in (0x00,):
                if k + 3 < len(pre_window) and pre_window[k + 2] in JCC:
                    gva = va_of(max(0, i - 46) + k)
                    disp = struct.unpack_from("<b", pre_window, k + 3)[0]
                    tgt = gva + 4 + disp
                    if tgt > store_va and tgt <= store_va + 0x40 and gva < store_va:
                        guard = (gva, pre_window[k:k + 4], JCC[pre_window[k + 2]], tgt)
        mark = "CLAMP" if has_clamp_calc else "     "
        if guard:
            gva, gb, gname, tgt = guard
            print("  %s %-12s store=0x%08X  guard=0x%08X [%s %s -> 0x%08X]  cmpbytes=%s" %
                  (mark, nm, store_va, gva, gb.hex(" "), gname, tgt,
                   "3b %02x" % gb[1]))
        else:
            print("  %s %-12s store=0x%08X  (无守卫模式)" % (mark, nm, store_va))
