# -*- coding: utf-8 -*-
"""PeG 日期「月份名」汉化补丁（第 30 轮）
================================================================================
问题：游戏信息面板显示的日期形如 `5 November 2012`，月份是英文。
      而 `Gui030.txt` 第 174–185 行早已汉化为「一月…十二月」——说明
      **日期格式化并不读 GUI 文本**，而用 **exe 内建的 CRT 日期表**。

定位（PeG030.exe，.rdata）：
    NUL 分隔的月份全名池（倒序存放）：
        0x8B47C December   0x8B488 November   0x8B494 October    0x8B49C September
        0x8B4A8 August     0x8B4B0 July       0x8B4B8 June       0x8B4C0 April
        0x8B4C8 March      0x8B4D0 February   0x8B4DC January
    其正序指针数组在 .data 0xAC5B8（Jan..Dec）。
    （另有 3 字节/项的缩写表 0x8B590 = CRT 的 `%b`；槽位仅 3B，放不下汉字，**不动**。）

做法：**原地替换这 11 个字符串为中文 + NUL 填充**，不改长度、不改指针。
      槽位：December/November/September/February 各 12B，其余各 8B；
      「十一月」（6B+NUL=7B）也放得下。
      ⚠️ MBCS 已启用（见 patch-mbcs.py），中文能被正确渲染。

用法：
    python work/peg/patch-month-zh.py            # dry-run
    python work/peg/patch-month-zh.py --apply    # 写入（先备份到 <exe>.pre-month-zh）
"""
import hashlib
import os
import shutil
import sys

ROOT = r"D:\DSH\军事游戏汉化"
EXE = r"D:\Program Files\PeG\PeG030.exe"
SNAP = os.path.join(ROOT, r"peg\testbed\PeG030.exe.pre-month-zh")

# (偏移, 原英文, 中文)
MONTHS = [
    (0x8B47C, "December",  "十二月"),
    (0x8B488, "November",  "十一月"),
    (0x8B494, "October",   "十月"),
    (0x8B49C, "September", "九月"),
    (0x8B4A8, "August",    "八月"),
    (0x8B4B0, "July",      "七月"),
    (0x8B4B8, "June",      "六月"),
    (0x8B4C0, "April",     "四月"),
    (0x8B4C8, "March",     "三月"),
    (0x8B4D0, "February",  "二月"),
    (0x8B4DC, "January",   "一月"),
]
# 槽位终点（下一个字符串起点；最后一个到缩写表 0x8B4E4）
SLOT_END = [0x8B488, 0x8B494, 0x8B49C, 0x8B4A8, 0x8B4B0, 0x8B4B8,
            0x8B4C0, 0x8B4C8, 0x8B4D0, 0x8B4DC, 0x8B4E4]


def main():
    apply = "--apply" in sys.argv
    b = bytearray(open(EXE, "rb").read())
    print(f"exe 大小 {len(b)}B  md5 {hashlib.md5(bytes(b)).hexdigest()}\n")

    ok = True
    for (off, en, zh), end in zip(MONTHS, SLOT_END):
        cur = bytes(b[off:end])
        want_en = en.encode("ascii")
        if not cur.startswith(want_en):
            print(f"  ❌ 0x{off:06X} 期望 {en!r}，实际 {cur[:12]!r} —— 不匹配，中止")
            ok = False
    if not ok:
        print("\n文件与预期不符（可能已打过补丁或版本不同），未做任何修改。")
        return

    print(f"{'偏移':>9}  {'槽位':>4}  {'原英文':<10} → 中文(GBK)  新字节数")
    plan = []
    for (off, en, zh), end in zip(MONTHS, SLOT_END):
        slot = end - off
        nb = zh.encode("gbk") + b"\x00"
        if len(nb) > slot:
            print(f"  ❌ 0x{off:06X} {zh} 需 {len(nb)}B > 槽位 {slot}B")
            return
        new = nb + b"\x00" * (slot - len(nb))
        plan.append((off, end, new))
        print(f"  0x{off:06X}  {slot:4d}B  {en:<10} → {zh:<5}      {len(nb)}B")

    if not apply:
        print("\n[dry-run] 未写入。加 --apply 执行。")
        return

    if not os.path.exists(SNAP):
        shutil.copy2(EXE, SNAP)
        print(f"\n已备份 → {SNAP}")
    else:
        print(f"\n备份已存在，跳过 → {SNAP}")
    for off, end, new in plan:
        b[off:end] = new
    tmp = EXE + ".tmp"
    open(tmp, "wb").write(bytes(b))
    # 回读校验
    chk = open(tmp, "rb").read()
    assert len(chk) == len(b)
    for (off, en, zh), end in zip(MONTHS, SLOT_END):
        seg = chk[off:off + len(zh.encode('gbk'))]
        assert seg == zh.encode("gbk"), f"回读校验失败 @0x{off:X}: {seg!r}"
    shutil.move(tmp, EXE)
    print(f"✅ 已写入 {EXE}")
    print(f"   新 md5 {hashlib.md5(open(EXE,'rb').read()).hexdigest()}")


if __name__ == "__main__":
    main()
