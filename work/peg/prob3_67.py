# -*- coding: utf-8 -*-
"""prob3_67.py — 转储 0x441Dxx..0x4422xx 区域（已知 SetColorKey + 画布描述符），
并用结构化扫描定位「写 [0x6769B0]」的指令。"""
import sys
sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\peg")
import hint_pe as H

base = H.load(H.SRC)
port = H.load(H.PORT)

KEY = 0x6769B0

print("========== [0x6769B0] 内容 ==========")
for tag, d in (("SRC", base), ("PORT", port)):
    print("  %-4s in_file=%s is_bss=%s  -> 磁盘上不存在（BSS），运行期由代码写入"
          % (tag, H.in_file(KEY), H.is_bss(KEY)))
print("  [0x676980..0x6769D0] 是否落在 BSS：")
for va in range(0x676980, 0x6769D0, 0x10):
    print("      0x%06X: %s" % (va, (H.blob(base, va, 16).hex(" ") if H.in_file(va) else "<BSS 无字节>")))



print("\n========== 全镜像里所有指向 0x6769B0 的 dword ==========")
for tag, d in (("SRC", base), ("PORT", port)):
    hits = H.find_dword_refs(d, KEY)
    print("  %-4s %d 处" % (tag, len(hits)))
    for fo, va in hits:
        sec = H.sec_of(va)
        ctx = H.dis(va, 4, d)
        print("     ref@va=0x%06X %-7s  ctx: %s" % (va, sec, H.fmt(ctx, 4)))

print("\n========== 0x441D80 .. 0x442290 反汇编（SRC）==========")
for ins in H.dis_all(0x441D80, 0x442290, base):
    b = H.blob(base, ins.address, ins.size)
    print("0x%06X  %-22s %-34s  %s" % (ins.address, b.hex(" "), ins.mnemonic + " " + ins.op_str, ""))
