# -*- coding: utf-8 -*-
"""PeG030.exe 治本补丁 #2：关掉「标签按字节丢前 N 行」的裁剪

用法:
  python patch-labeldrop.py patch    # 由原版生成补丁版（同时含补丁 #1）
  python patch-labeldrop.py verify   # 校验补丁位
  python patch-labeldrop.py remove   # 从补丁版还原成原版

背景（反汇编实证，sub_46FEDD @VA 0x46FEDD）：
  n = 该串在目标矩形里需要几行（sub_471696 → sub_47010B → DrawTextExA(DT_CALCRECT)）
  if (idx <= 0 || idx >= n) return str;         ; 装得下 ⇒ 原样返回
  else  二分查找【字节偏移】mid，返回 str+mid    ; 装不下 ⇒ 丢前 idx 行
  ⚠️ 英文有空格 ⇒ 换行只发生在词间 ⇒ n 一般 = 1 ⇒ 永不裁剪；
     中文可在任意字间断行 ⇒ n 常 > 1 ⇒ 落进「丢前 N 行」，而二分是按【字节】找的
     ⇒ 起点落在半个汉字上 ⇒ 显示成别的字 / 掉字 / 方块。

补丁点（text 段）:
  0x46FF1C  7C 08   jl  0x46FF26   ; idx < n ⇒ 去做裁剪
      →     EB 00   jmp 0x46FF1E   ; 无条件跳到「返回原串」
  同长度、同位置，仅改 2 字节，不破坏任何指令边界。

副作用：极长标签会从「显示尾部」变成「显示头部」（矩形仍会纵向裁剪）。
        英文本就 n=1 不受影响。
"""
import os, sys, shutil, hashlib

GAME = r"D:\Program Files\PeG"
ORIG = os.path.join(GAME, "PeG030.exe.orig-backup")   # 原版（2026-10-10 备份）
OUT  = os.path.join(GAME, "PeG030zh.exe")             # 补丁版（同时含补丁 #1 的行尾类别表）
LIVE = os.path.join(GAME, "PeG030.exe")

# 补丁 #1：字符类别表 0x80–0xFF: 0x0000 -> 0x0040
T1_VA, T1_OFF, T1_CNT, T1_NEW = 0x4ABA8A, 0x80, 128, 0x0040
# 补丁 #2：关掉丢行分支
T2_VA = 0x46FF1C
T2_OLD = bytes.fromhex("7c 08")   # jl  0x46FF26
T2_NEW = bytes.fromhex("eb 00")   # jmp 0x46FF1E


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def load():
    import pefile
    pe = pefile.PE(ORIG, fast_load=True)
    return pe, bytearray(pe.__data__)


def va2fo(pe, va):
    for s in pe.sections:
        sv = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
        if sv <= va < sv + s.SizeOfRawData:
            return s.PointerToRawData + (va - sv)
    return None


def cmd_patch():
    pe, d = load()
    # #1 类别表
    o = va2fo(pe, T1_VA + T1_OFF * 2)
    for i in range(T1_CNT):
        d[o + i * 2] = T1_NEW & 0xFF
        d[o + i * 2 + 1] = (T1_NEW >> 8) & 0xFF
    # #2 关掉丢行
    o2 = va2fo(pe, T2_VA)
    cur = bytes(d[o2:o2 + 2])
    assert cur == T2_OLD, f"0x{T2_VA:X} 处字节为 {cur.hex(' ')}，预期 {T2_OLD.hex(' ')}"
    d[o2:o2 + 2] = T2_NEW
    open(OUT, "wb").write(bytes(d))
    print(f"[ok] 补丁版 → {OUT}")
    print(f"     补丁#1 类别表: VA 0x{T1_VA:X}+0x100，{T1_CNT} 项 → 0x{T1_NEW:04X}")
    print(f"     补丁#2 丢行分支: VA 0x{T2_VA:X}  {T2_OLD.hex(' ')} → {T2_NEW.hex(' ')}")
    print(f"     md5 = {md5(OUT)}")
    cmd_verify()


def cmd_verify():
    import pefile
    print(f"  原版   {ORIG}  md5={md5(ORIG)[:12]}…")
    if not os.path.exists(OUT):
        print("  补丁版 不存在"); return
    print(f"  补丁版 {OUT}  md5={md5(OUT)[:12]}…")
    po, do = load()
    pe2 = pefile.PE(OUT)
    d2 = pe2.__data__
    a = bytes(d2[va2fo(pe2, T2_VA):va2fo(pe2, T2_VA) + 2])
    o = va2fo(pe2, T1_VA + 0x80 * 2)
    b80 = (d2[o] | (d2[o + 1] << 8))
    print(f"  校验: 0x{T2_VA:X} = {a.hex(' ')}  （应 {T2_NEW.hex(' ')}）"
          f"{'✅' if a == T2_NEW else '❌'}   类别表 idx0x80 = 0x{b80:04X}"
          f"{'✅' if b80 == T1_NEW else '❌'}")
    diff = sum(1 for i in range(len(do)) if do[i] != d2[i]) if len(do) == len(d2) else -1
    print(f"  与原版差异字节数 = {diff}（应 130 = 128 + 2）")


def cmd_remove():
    if not os.path.exists(ORIG):
        sys.exit("!! 找不到原版备份")
    shutil.copy2(ORIG, OUT)
    print(f"[ok] 已用原版覆盖 {OUT}（补丁版退化为原版）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    {"patch": cmd_patch, "verify": cmd_verify, "remove": cmd_remove}.get(cmd, cmd_verify)()
