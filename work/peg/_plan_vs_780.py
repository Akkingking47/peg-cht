# -*- coding: utf-8 -*-
"""_plan_vs_780.py — 把「启动器计划里的立即数地址」与「母本 .text 里 dword 0x780 的出现点」做差集。

目的：确定哪些 0x780(=1920) 站点是「母本原有的地图面尺寸」，哪些是「我们补丁改成 1920 的屏幕尺寸」。
后者绝不能再被 M 组改成 0x1000。
只读，不改任何文件。
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import peg_launcher as PL  # noqa: E402

EXE = r"D:\Program Files\PeG\PeG030.exe"
IMAGE_BASE = 0x400000

SITES_780 = [
    0x41F3FA, 0x424AD3, 0x424ADA, 0x424B31, 0x424B38, 0x424BA6, 0x424BB1,
    0x424BE9, 0x424BF4, 0x43D733, 0x43D747, 0x43DB03, 0x43DB72, 0x43DB83,
    0x43DEC7, 0x43DF37, 0x43DF48, 0x43E2F0, 0x43E360, 0x43E371, 0x43E6B5,
    0x43E725, 0x43E736, 0x441BFD, 0x441C04, 0x441C90, 0x441C97, 0x455BB6,
    0x455BBD, 0x455BE1, 0x455BE8,
]


def main():
    entries, notes = PL.build_plan(1920, 1080, tooltip=False, extra=True,
                                   panel=True, dxdy=False)
    print("计划条目数：%d" % len(entries))
    print("首条示例：%r" % (entries[0],))
    print("类型：%s" % type(entries[0]))
    print("备注：%r" % (notes[:6],))
    print()

    planned = set()
    for e in entries:
        if isinstance(e, (tuple, list)):
            for item in e:
                if isinstance(item, int) and IMAGE_BASE <= item < 0x80000000:
                    planned.add(item)
        elif isinstance(e, dict):
            for k, v in e.items():
                if isinstance(v, int) and IMAGE_BASE <= v < 0x80000000:
                    planned.add(v)
    print("计划里可识别的地址数：%d" % len(planned))
    print()

    with open(EXE, "rb") as f:
        data = f.read()

    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec0 = e_lfanew + 24 + opt_size
    secs = []
    for i in range(nsec):
        off = sec0 + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        secs.append(dict(name=name, va=va, vsize=vsize, raw=raw, rawsize=rawsize))

    def fo(va):
        rva = va - IMAGE_BASE
        for s in secs:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s["raw"] + (rva - s["va"])
        return None

    overlap, free = [], []
    for va in SITES_780:
        o = fo(va)
        cur = data[o:o + 4]
        (overlap if va in planned else free).append((va, cur.hex(" ")))
    print("=== 与计划重叠（说明这是我们补丁改出来的 1920，M 组必须跳过）：%d ===" % len(overlap))
    for va, h in overlap:
        print("  0x%08X  %s" % (va, h))
    print()
    print("=== 不在计划里（母本原有 1920；地图面候选）：%d ===" % len(free))
    for va, h in free:
        print("  0x%08X  %s" % (va, h))


if __name__ == "__main__":
    main()
