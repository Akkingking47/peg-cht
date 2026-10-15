# -*- coding: utf-8 -*-
"""定位游戏的日志格式串引用点，进而找出日志函数（只读，不碰游戏本体）。"""
import re

EXE = r"D:\Program Files\PeG\PeG030.exe"
# 节表（来自既有逆向记录）
SECS = [
    (".text",  0x401000, 0x400,   0x8A200),
    (".rdata", 0x48C000, 0x8A600, 0x1200),
    (".data",  0x48E000, 0x8B800, 0x21400),
    (".idata", 0x6AA000, 0xACC00, 0x5E00),
]


def va2off(va):
    for _, base, raw, size in SECS:
        if base <= va < base + size:
            return raw + (va - base)
    return None


def off2va(off):
    for _, base, raw, size in SECS:
        if raw <= off < raw + size:
            return base + (off - raw)
    return None


d = open(EXE, "rb").read()
text_va, text_raw, text_size = 0x401000, 0x400, 0x8A200

print("== 候选日志串 ==")
strs = {}
for pat in (b"objectIx = %d", b"hotX = %d", b"ERROR : %s", b"ERROR : ",
            b"Failed to draw unit without rot", b"Ran out of objects for firing"):
    for m in re.finditer(re.escape(pat), d):
        off = m.start()
        s = off
        while s > 0 and d[s - 1] != 0:
            s -= 1
        e = off + len(pat)
        while e < len(d) and d[e] != 0:
            e += 1
        full = d[s:e]
        strs.setdefault(off2va(s), full)
        break

for va, s in sorted(strs.items()):
    print("  %#010x  %r" % (va, s[:80]))

print("\n== 这些串的引用点（.text 中的 4 字节立即数）==")
try:
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
except Exception as exc:                                   # noqa: BLE001
    md = None
    print("  (无 capstone：%s)" % exc)

for va, s in sorted(strs.items()):
    pat = va.to_bytes(4, "little")
    hits = [m.start() for m in re.finditer(re.escape(pat), d[text_raw:text_raw + text_size])]
    print("  %#010x %r ← %d 处引用: %s" % (va, s[:40], len(hits),
                                       [hex(off2va(text_raw + h)) for h in hits[:6]]))
    for h in hits[:2]:
        hva = off2va(text_raw + h)
        if not md:
            continue
        start = max(text_raw, h - 64)
        code = d[start:text_raw + h + 48]
        print("     --- 反汇编 %#x 起 ---" % off2va(start))
        for ins in md.disasm(code, off2va(start)):
            mark = "  <== 引用" if ins.address <= hva < ins.address + ins.size else ""
            print("       %#08x  %-24s %s %s%s"
                  % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
