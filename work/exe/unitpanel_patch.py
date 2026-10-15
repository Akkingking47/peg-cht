# -*- coding: utf-8 -*-
"""OpenGen.exe 单位信息面板格式串块汉化。

两块内容：
  1) 原地替换：GBK 字节数 <= 原文 ASCII 长度+1 的串，直接覆盖，余量填 NUL。
  2) 空洞 + 改指针：放不下的短串写入 .rdata 空洞，再把唯一的那条
     push imm32 / mov [ebp-x], imm32 立即数改成新 VA。

用法:
  python unitpanel_patch.py          # 干跑（只报告，不写盘）
  python unitpanel_patch.py --apply  # 正式写入
"""
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib                     # PE 目录 / 空洞安全检查

EXE = r"D:/OpenPG2/OpenGen.exe"
IMAGEBASE = 0x400000
RDATA_DELTA = 0x400E00          # VA = FO + 0x400E00  (.rdata)

# ⚠️ 空洞选址（2026-09-24 事故后修正）
# 旧值 0x51CB31 落在 **IMAGE_LOAD_CONFIG_DIRECTORY**（FO 0x51CB30..0x51CB70）内：
#   写入偏移 +16 = FO 0x51CB40 命中该结构的 GlobalFlagsSet 字段，
#   加载器把它 |= 进 ntdll!NtGlobalFlag，打开 loader snaps 等调试标志，
#   进程初始化阶段在 ntdll 里 0xC0000005，游戏窗都出不来。
# 新址 0x4B1A9A：rtdialog 已汉化长文本（0x4B19CF 起 203 B）之后的 NUL 填充，
#   不在任何 PE 数据目录内、0 引用，且同族区域已实机验证可启动。
HOLE_FO = 0x4B1A9A
HOLE_VA = HOLE_FO + RDATA_DELTA  # 0x8B289A
HOLE_LEN = 54

# ---- 1) 原地替换 (FO, 原文, 译文) ----
INPLACE = [
    (0x513A14, "%d/%d hangars full", "%d/%d 机库已满"),
    (0x513A28, "Embark: %s [%s]", "搭载：%s [%s]"),
    (0x513AF4, "%s in U:%d hangar", "%s 在 U:%d 机库"),
    (0x513B08, "%s %d/%d hangars full", "%s %d/%d 机库已满"),
    (0x513B38, "%s unit - Target: %s", "%s 单位 - 目标：%s"),
    (0x513B80, "dry - ice - mud - terrain", "干燥 - 结冰 - 泥泞 - 地形"),
    (0x513B9C, "%3d - %3d - %3d   (when using RTP)",
     "%3d - %3d - %3d   (使用RTP时)"),
    (0x513BD8, "Range Air Defense: %d", "防空射程：%d"),
    (0x513BF0, "Range Air Attack: %d", "空袭射程：%d"),
    (0x513C10, "Hangar cap=%d", "机库容量=%d"),
    (0x513C3C, " *** can't use RTP ***", " *** 无法使用 RTP ***"),
    (0x513C54, "%s:  cost:%d  %s", "%s:  花费:%d  %s"),
    (0x513C70, "%s:  cost:%d  %s", "%s:  花费:%d  %s"),
]

# ---- 2) 空洞 + 改指针 (原文FO, 引用处FO, 原文, 译文) ----
REDIRECT = [
    (0x5139BC, 0x412D26, "TBD", "待定"),
    (0x513A04, 0x419A3E, "OTP", "他方"),
    (0x513AD4, 0x41ADCF, "Gnd", "地面"),
    (0x513AD8, 0x41ADC6, "Air", "空中"),
    (0x513B50, 0x41801D, "%s (Mv=%d)", "%s (机动=%d)"),
]


def main():
    apply_ = "--apply" in sys.argv
    d = bytearray(open(EXE, "rb").read())
    orig_len = len(d)
    errs = []

    # ---- 空洞安全预检（PE 数据目录相交 = 致命；其余项重跑时会因我方已写入而报警）----
    pe = pelib.PE(bytes(d))
    probs = pe.check_hole(HOLE_FO, HOLE_LEN)
    fatal = [p for p in probs if "相交" in p]
    if fatal:
        print("!! 空洞不安全，拒绝执行：")
        for p in fatal:
            print("   " + p)
        return
    if probs:
        print("[提示] 空洞检查：%s（首跑应为空；重跑时因已写入而属正常）" % probs)

    # ---------- 原地 ----------
    print("=== 原地替换 (%d 条) ===" % len(INPLACE))
    for fo, src, dst in INPLACE:
        old = src.encode("latin-1") + b"\x00"
        cur = bytes(d[fo:fo + len(old)])
        if cur != old:
            # 幂等：已是目标译文则跳过
            chk = dst.encode("gbk") + b"\x00"
            if cur[:len(chk)] == chk:
                print("  0x%06X  %-34r -> %-22s  已生效，跳过" % (fo, src, dst))
                continue
            errs.append("原文不符 FO 0x%X %r != %r" % (fo, cur, old))
            continue
        new = dst.encode("gbk") + b"\x00"
        if len(new) > len(old):
            errs.append("超长 FO 0x%X %d>%d" % (fo, len(new), len(old)))
            continue
        pad = len(old) - len(new)
        d[fo:fo + len(old)] = new + b"\x00" * pad
        print("  0x%06X  %-34r -> %-22s  %d/%dB"
              % (fo, src, dst, len(new), len(old)))

    # ---------- 空洞 ----------
    print("=== 空洞改写 (%d 条) ===" % len(REDIRECT))
    off = 0
    for src_fo, ref_fo, src, dst in REDIRECT:
        old_va = src_fo + RDATA_DELTA
        new = dst.encode("gbk") + b"\x00"
        new_va = HOLE_VA + off
        cur_va = struct.unpack_from("<I", d, ref_fo)[0]
        # 幂等：指针已指向目标空洞且内容一致 -> 跳过
        if cur_va == new_va and bytes(d[HOLE_FO + off:HOLE_FO + off + len(new)]) == new:
            print("  0x%06X  %-14r -> %-14s  已生效，跳过" % (src_fo, src, dst))
            off += len(new)
            continue
        if cur_va != old_va:
            errs.append("引用处不符 FO 0x%X (现值 0x%X)" % (ref_fo, cur_va))
            off += len(new)
            continue
        if d.count(struct.pack("<I", old_va)) != 1:
            errs.append("引用不唯一 VA 0x%X (%d 处)" % (old_va, d.count(struct.pack("<I", old_va))))
            off += len(new)
            continue
        if bytes(d[src_fo:src_fo + len(src) + 1]) != src.encode("latin-1") + b"\x00":
            errs.append("原文不符 FO 0x%X %r" % (src_fo, src))
            off += len(new)
            continue
        if off + len(new) > HOLE_LEN:
            errs.append("空洞不足")
            continue
        if bytes(d[HOLE_FO + off:HOLE_FO + off + len(new)]) != b"\x00" * len(new):
            errs.append("空洞已被占用 @+%d" % off)
            continue
        d[HOLE_FO + off:HOLE_FO + off + len(new)] = new
        struct.pack_into("<I", d, ref_fo, new_va)
        print("  0x%06X  %-14r -> %-14s  新VA 0x%06X  hole+%d (%dB)"
              % (src_fo, src, dst, new_va, off, len(new)))
        off += len(new)
    print("  空洞占用 %d/%d 字节" % (off, HOLE_LEN))

    if errs:
        print("\n!! 错误 %d 条，未写盘：" % len(errs))
        for e in errs:
            print("   " + e)
        return

    if not apply_:
        print("\n[干跑] 未写盘。加 --apply 正式写入。")
        return

    with open(EXE, "wb") as f:
        f.write(bytes(d))
    print("\n已写入 %s" % EXE)

    # 回读校验
    c = open(EXE, "rb").read()
    print("文件长度 %d (原 %d) %s" % (len(c), orig_len,
                                      "一致" if len(c) == orig_len else "不一致!"))
    ok = True
    for fo, src, dst in INPLACE:
        got = c[fo:c.find(b"\x00", fo)].decode("gbk", "replace")
        if got != dst:
            print("  !! 校验失败 0x%X %r" % (fo, got))
            ok = False
    for src_fo, ref_fo, src, dst in REDIRECT:
        va = struct.unpack_from("<I", c, ref_fo)[0]
        fo = va - RDATA_DELTA
        got = c[fo:c.find(b"\x00", fo)].decode("gbk", "replace")
        if got != dst:
            print("  !! 校验失败 VA 0x%X %r" % (va, got))
            ok = False
    print("回读校验: %s" % ("全部通过" if ok else "有失败"))


if __name__ == "__main__":
    main()
