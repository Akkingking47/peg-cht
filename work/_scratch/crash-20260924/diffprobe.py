# -*- coding: utf-8 -*-
"""崩溃定位：逐字节差异审计 + .text 站点反汇编。

用法:
  python diffprobe.py <A.exe> <B.exe> [--dis]
A = 已知可用 (baseline)，B = 待检。
"""
import sys

SECTIONS = [
    # name, VA, VirtSize, RawPtr, RawSize
    (".text",  0x401000, 0x476C00, 0x400,    0x476C00),
    (".rdata", 0x878000, 0x477200, 0x477200, 0x477200),
    (".data",  0x971000, 0x56FA00, 0x8EE400, 0x56FA00),
    (".rsrc",  0x12AB000, 0x5BEC00, 0xE5DE00, 0x5BEC00),
]


def sec_of(fo):
    for n, va, vs, rp, rs in SECTIONS:
        if rp <= fo < rp + rs:
            return n, va + (fo - rp)
    return "?", 0


def disasm(data, start, length):
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    except ImportError:
        return ["      (capstone 未安装)"]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    out = []
    for ins in md.disasm(data[start:start + length], start):
        out.append("      0x%08X  %-24s %s" % (
            ins.address, " ".join("%02X" % b for b in ins.bytes), ins.mnemonic + " " + ins.op_str))
    return out


def main():
    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()
    show_dis = "--dis" in sys.argv
    print("A = %s  (%d B)" % (sys.argv[1], len(a)))
    print("B = %s  (%d B)" % (sys.argv[2], len(b)))
    if len(a) != len(b):
        print("!! 长度不同")
    n = min(len(a), len(b))
    # 收集差异点
    pts = [i for i in range(n) if a[i] != b[i]]
    print("差异字节总数: %d" % len(pts))
    # 归并成区间（间隔 <= 12 视为同一区间）
    runs = []
    for i in pts:
        if runs and i - runs[-1][1] <= 12:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    print("差异区间数: %d\n" % len(runs))
    for i, (lo, hi) in enumerate(runs, 1):
        name, va = sec_of(lo)
        pad = 8
        s = max(0, lo - pad)
        e = min(n, hi + 1 + pad)
        print("[%2d] FO 0x%06X-0x%06X (%d B)  %s VA 0x%08X" %
              (i, lo, hi, hi - lo + 1, name, va))
        print("     old: %s" % " ".join("%02X" % x for x in a[s:e]))
        print("     new: %s" % " ".join("%02X" % x for x in b[s:e]))
        try:
            so = a[s:e].split(b"\x00")[0].decode("gbk", "replace")
            sn = b[s:e].split(b"\x00")[0].decode("gbk", "replace")
            print("     old.txt: %r" % so)
            print("     new.txt: %r" % sn)
        except Exception:
            pass
        if show_dis and name == ".text":
            print("     --- B 侧反汇编 ---")
            for line in disasm(b, max(0, lo - 24), 48):
                print(line)
        print()


if __name__ == "__main__":
    main()
