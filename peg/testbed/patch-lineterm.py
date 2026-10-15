# -*- coding: utf-8 -*-
"""⭐ 治本补丁：修 PeG 引擎的「行终止字符表」，让 ≥0x80 的字节不再被当成换行
————————————————————————————————————————————————————————————
原理（反汇编实证，Text.c 的文本加载器 @VA 0x46E800）：
  引擎把整个 .txt 读进内存，逐字节扫描；判定「行尾」的依据是
      (classTable[byte] & 0x157) == 0
  该表位于 VA 0x4ABA8A（.data，256 × WORD；全局指针 [0x4ABA80] 指向它，[0x4ABC8C]=1 走内联分支）
  实测：'A'=0x0081  '0'=0x0084  '.'=0x0010  ' '=0x0048  '\\t\\n\\v\\f\\r'=0x0028
        控制字符=0x0020   而 **0x80–0xFF 全部 = 0x0000**
  ⇒ 0x0000 & 0x157 == 0 ⇒ **任何 ≥0x80 的字节都被判为行尾！**
  GBK 汉字的每个字节都 ≥0x80 ⇒ 中文行在第一个字节就被截断，
  且「长度为 0 的行被跳过、不占行号」⇒ **其后所有行号整体错位**
  ⇒ 标签显示到别的行（用户报的「英文选项对应位置漂移 / 原来的英文也不对了」）

补丁：
  把表中 0x80–0xFF 共 128 项由 0x0000 改为 **0x0040**（MSVC _BLANK）。
  0x0040 & 0x157 = 0x0040 ≠ 0 ⇒ 高位字节成为「普通字符」，不再断行。
  ⚠️ 选 0x0040 的理由：只置 _BLANK 位，不置 _UPPER/_LOWER/_DIGIT，
     因此其它 25 处使用该表的代码对高位字节的 isalpha/isdigit 结果仍为 false，
     且原版数据（纯 ASCII）**行为完全不变**（该补丁只影响 0x80–0xFF 这一片）。

产物：`PeG030zh.exe`（**游戏目录内新增，原 PeG030.exe 零改动**）
"""
import os, sys, hashlib, shutil, struct

GAME  = r"D:\Program Files\PeG"
SRC   = os.path.join(GAME, "PeG030.exe.orig-backup")   # ⚠️ 必须以【原版备份】为源，不能用已被覆盖的 PeG030.exe
DST   = os.path.join(GAME, "PeG030zh.exe")

TBL_VA   = 0x4ABA8A
FO_BASE  = 0xA928A          # = TBL_VA - 0x402800 (.data: VA = FO + 0x402800)
LO, HI   = 0x80, 0x100
NEWVAL   = 0x0040

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()

def show(p, tag):
    d = open(p, "rb").read()
    vals = struct.unpack_from("<128H", d, FO_BASE + LO * 2)
    print(f"  {tag}: {os.path.basename(p)}  {len(d)} B  md5={md5(p)[:12]}…")
    print(f"        0x80..0xFF 前8项 = {[hex(v) for v in vals[:8]]}")
    return vals

def cmd_patch():
    if not os.path.exists(SRC):
        sys.exit("找不到 PeG030.exe")
    show(SRC, "原始")
    shutil.copy2(SRC, DST)
    d = bytearray(open(DST, "rb").read())
    # 先自检：确认目标区确实是全 0
    cur = struct.unpack_from("<128H", d, FO_BASE + LO * 2)
    if all(v == NEWVAL for v in cur):
        print("[skip] 已是补丁版（幂等）")
        show(DST, "补丁"); return
    if not all(v == 0 for v in cur):
        sys.exit(f"!! 目标区不是全 0（{set(cur)}），拒绝写补丁")
    for i in range(LO, HI):
        struct.pack_into("<H", d, FO_BASE + i * 2, NEWVAL)
    open(DST, "wb").write(bytes(d))
    print(f"[ok] 已生成补丁版 → {DST}")
    show(DST, "补丁")

def cmd_verify():
    if not os.path.exists(DST):
        print("补丁版不存在（跑 patch 生成）"); return
    a = open(SRC, "rb").read(); b = open(DST, "rb").read()
    diff = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    print(f"原始 md5 = {md5(SRC)}")
    print(f"补丁 md5 = {md5(DST)}")
    print(f"差异字节数 = {len(diff)}  范围 = {hex(min(diff)) if diff else '-'}..{hex(max(diff)) if diff else '-'}")
    # 0x0000 -> 0x0040：小端下只改每个 WORD 的高字节 ⇒ 恰好 128 个字节不同，且都为偶偏移
    ok = (len(diff) == 128
          and all(FO_BASE + LO*2 <= i < FO_BASE + HI*2 for i in diff)
          and all((i - (FO_BASE + LO*2)) % 2 == 0 for i in diff))
    print(f"  （应为 128 个偶偏移字节，落在 0x{FO_BASE+LO*2:X}..0x{FO_BASE+HI*2-1:X} 内）")
    print("  ⇒", "✅ 差异范围正确" if ok else "❌ 差异范围异常")
    show(DST, "补丁")

def cmd_remove():
    if os.path.exists(DST):
        os.remove(DST); print("[ok] 已移除补丁版（原始未动）")
    else:
        print("补丁版不存在")

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else "verify"
    {"patch": cmd_patch, "verify": cmd_verify, "remove": cmd_remove}.get(c, cmd_verify)()
