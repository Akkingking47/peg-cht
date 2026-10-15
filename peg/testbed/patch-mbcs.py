# -*- coding: utf-8 -*-
"""PeG030.exe 治本补丁 #3：按汉化界标准范式，把「单字节引擎」改成「双字节引擎」

用法:
  python patch-mbcs.py patch    # 由原版生成补丁版（含 #1 + #3）
  python patch-mbcs.py verify
  python patch-mbcs.py remove   # 退回原版

三项改动（全部是社区通行做法，见 peg/testbed/汉化技术路线.md）：

 ① 字体字符集：CreateFontA 的 iCharSet  0(ANSI_CHARSET) → 134(GB2312_CHARSET)
    VA 0x4718E3  push 0 (6A 00) → push 134 (6A 86)          —— 同长度 2 字节
    （参考：RealLive 引擎汉化笔记「将 iCharSet 更改为 134」）

 ② _pctype 标出前导字节：表 @VA 0x4ABA8A（[0x4ABA80] 指向它 = CRT 的 _pctype）
    _pctype[c] 的 bit15 (0x8000) = _LEADBYTE（「这是双字节前导字节」）
    原版 0x80–0xFF 全为 0x0000 ⇒ 引擎/CRT 都不认中文 ⇒ 逐字节逻辑全部错乱
    改为 0x81–0xFE = 0x8040（_BLANK | _LEADBYTE）；0x80 / 0xFF = 0x0040
    （参考：「扩大前导字节判定范围」，GBK 前导字节 = 0x81–0xFE）

 ③ 启用 MBCS：CRT 全局 __mbcodepage @VA 0x4ABC8C  1 → 936
    加载器等 20 处都是 `cmp [0x4ABC8C],1 / jle <走内联 ASCII 表>`，
    值 >1 才走 _isctype() 双字节路径。原版是 1 ⇒ 走的是 ASCII 表
    （参考：Q75439「Tips for Writing DBCS-Compatible Applications」）

安全性：纯 ASCII 文本下，②③ 的前导字节判定永不触发、_isctype 结果与内联表完全一致
        ⇒ 对原版英文行为零影响。
"""
import os, sys, shutil, hashlib

GAME = r"D:\Program Files\PeG"
ORIG = os.path.join(GAME, "PeG030.exe.orig-backup")
OUT  = os.path.join(GAME, "PeG030zh.exe")

PCTYPE_VA   = 0x4ABA8A          # _pctype 表（256 × WORD）
MBCODE_VA   = 0x4ABC8C          # __mbcodepage
CHARSET_VA  = 0x4718E3          # push iCharSet
CHARSET_OLD = bytes.fromhex("6a 00")
CHARSET_NEW = bytes.fromhex("6a 86")   # 134 = GB2312_CHARSET
LEAD_LO, LEAD_HI = 0x81, 0xFE
VAL_LEAD, VAL_PLAIN, VAL_NEUTRAL = 0x8040, 0x0040, 0x0040
MBCP = 936


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def _pe(path):
    import pefile
    pe = pefile.PE(path, fast_load=True)
    return pe, bytearray(pe.__data__)


def va2fo(pe, va):
    for s in pe.sections:
        sv = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if sv <= va < sv + s.SizeOfRawData:
            return s.PointerToRawData + (va - sv)
    return None


def cmd_patch():
    import struct
    pe, d = _pe(ORIG)
    # ① charset
    o = va2fo(pe, CHARSET_VA)
    cur = bytes(d[o:o + 2])
    assert cur == CHARSET_OLD, f"0x{CHARSET_VA:X} 处为 {cur.hex(' ')}, 预期 {CHARSET_OLD.hex(' ')}"
    d[o:o + 2] = CHARSET_NEW
    # ② _pctype —— ⚠️ 只动 0x80–0xFF 那一片，0x00–0x7F 原样保留！
    #    （ASCII 的 _UPPER/_LOWER/_DIGIT/_SPACE/_PUNCT 分类位绝不能碰，
    #      否则 isalpha/isdigit/isspace/判词边界 全废）
    base = va2fo(pe, PCTYPE_VA)
    for c in range(0x100):
        old = struct.unpack_from('<H', d, base + c * 2)[0]
        if c < 0x80:
            assert old != 0, f"_pctype[{c:#x}] 原值为 0，异常"
            continue                      # ← 保持原值，一个字都不改
        v = VAL_LEAD if LEAD_LO <= c <= LEAD_HI else VAL_NEUTRAL
        struct.pack_into('<H', d, base + c * 2, v)
    # ③ __mbcodepage
    struct.pack_into('<I', d, va2fo(pe, MBCODE_VA), MBCP)
    open(OUT, "wb").write(bytes(d))
    print(f"[ok] 补丁版 → {OUT}")
    print(f"     ① iCharSet 0x{CHARSET_VA:X}: {CHARSET_OLD.hex(' ')} → {CHARSET_NEW.hex(' ')}  (134 GB2312_CHARSET)")
    print(f"     ② _pctype 0x{LEAD_LO:02X}-0x{LEAD_HI:02X} = 0x{VAL_LEAD:04X}（_BLANK|_LEADBYTE），其余 0x{VAL_NEUTRAL:04X}")
    print(f"     ③ __mbcodepage 0x{MBCODE_VA:X} = {MBCP}")
    print(f"     md5 = {md5(OUT)}")
    cmd_verify()


def cmd_verify():
    import struct
    print(f"  原版   {ORIG}  md5={md5(ORIG)[:12]}…")
    if not os.path.exists(OUT):
        print("  补丁版 不存在"); return
    print(f"  补丁版 {OUT}  md5={md5(OUT)[:12]}…")
    pe, d = _pe(OUT)
    base = va2fo(pe, PCTYPE_VA)
    lead_cnt = sum(1 for c in range(0x100) if struct.unpack_from('<H', d, base + c * 2)[0] & 0x8000)
    cs = bytes(d[va2fo(pe, CHARSET_VA):va2fo(pe, CHARSET_VA) + 2]).hex(' ')
    mb = struct.unpack_from('<I', d, va2fo(pe, MBCODE_VA))[0]
    print(f"  ① 0x{CHARSET_VA:X} = {cs}             {'✅' if cs == CHARSET_NEW.hex(' ') else '❌'}（应 6a 86）")
    print(f"  ② 前导字节个数 = {lead_cnt}                {'✅' if lead_cnt == LEAD_HI - LEAD_LO + 1 else '❌'}（应 {LEAD_HI - LEAD_LO + 1}）")
    print(f"  ③ 0x{MBCODE_VA:X} = {mb}               {'✅' if mb == MBCP else '❌'}（应 936）")
    print(f"     ASCII 抽查: _pctype[0x41]=0x{struct.unpack_from('<H', d, base + 0x41*2)[0]:04X}(应 0081) "
          f"_pctype[0x20]=0x{struct.unpack_from('<H', d, base + 0x20*2)[0]:04X}(应 0048)")


def cmd_remove():
    if not os.path.exists(ORIG):
        sys.exit("!! 找不到原版备份")
    shutil.copy2(ORIG, OUT)
    print(f"[ok] 已用原版覆盖 {OUT}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    {"patch": cmd_patch, "verify": cmd_verify, "remove": cmd_remove}.get(cmd, cmd_verify)()
