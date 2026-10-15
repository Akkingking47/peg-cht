# -*- coding: utf-8 -*-
"""PeG 日期汉化 · 强制 GetDateFormatA 使用中文区域（第 31 轮 · 真正生效的一刀）
================================================================================
前情：第 30 轮改了 exe 内建 CRT `lc_time` 月份/星期表，**无效**。

真因（反汇编定位）：
    日期由 **Windows API `GetDateFormatA`** 生成，调用点 文件偏移 0x7BE7F：
        0x7BE75  push 0x96                  ; cchDate = 150
        0x7BE7A  push 0x65A3A0              ; lpDateStr
        0x7BE7F  push 0                    ; lpFormat = NULL（用系统长日期格式）
        0x7BE81  lea/push [ebp-0x24]        ; SYSTEMTIME（自 .SCN 起止日期 year+2000/month/day）
        0x7BE85  push 2                    ; dwFlags = DATE_LONGDATE
        0x7BE86  mov eax, [0x499148]        ; ★ LCID 取自全局「语言」变量
        0x7BE8B  push eax
        0x7BE8C  call [0x6AA460]           ; = GetDateFormatA
    全局 0x499148（.data，文件 0x96948）：
        初值 **9 = LANG_ENGLISH**；语言配置遇德语写 7 (LANG_GERMAN)、法语写 12 (LANG_FRENCH)
        （见 0x4273A / 0x42778，及 0x708E0 的语言分支 ".deu"/"french"）
    ⇒ `GetDateFormatA(9, DATE_LONGDATE, 2006-4-3, NULL, …, 150)` = **"Monday, April 3, 2006"**
      —— 与截图完全一致。**这就是之前两次修改都不生效的原因：名字来自 Windows，不在 exe 里。**

补丁（**5 字节，等长替换，不动其他任何字节**）：
        0x7BE86:  A1 48 91 49 00   (mov eax,[0x499148])   ← 原
             ↓
                  B8 04 08 00 00   (mov eax,0x0804)      ← 强制 zh-CN
    ⇒ 输出变为 **"2006年4月3日"**（GBK，MBCS 已启用可直接显示）。

用法：
    python work/peg/patch-date-lcid-zh.py            # dry-run
    python work/peg/patch-date-lcid-zh.py --apply    # 写入（先备份 <exe>.pre-lcid-zh）
"""
import hashlib
import os
import shutil
import sys

ROOT = r"D:\DSH\军事游戏汉化"
EXE = r"D:\Program Files\PeG\PeG030.exe"
SNAP = os.path.join(ROOT, r"peg\testbed\PeG030.exe.pre-lcid-zh")

OFF = 0x7BE86
OLD = bytes.fromhex("a148914900")       # mov eax,[0x499148]
NEW = bytes.fromhex("b804080000")       # mov eax,0x0804  (zh-CN)
LCID = 0x0804


def main():
    apply = "--apply" in sys.argv
    b = bytearray(open(EXE, "rb").read())
    print(f"exe {len(b)}B  md5 {hashlib.md5(bytes(b)).hexdigest()}\n")

    cur = bytes(b[OFF:OFF + 5])
    if cur == NEW:
        print(f"✅ 0x{OFF:06X} 已是 mov eax,0x{LCID:04X}，无需修改。")
        return
    if cur != OLD:
        print(f"❌ 0x{OFF:06X} 期望 {OLD.hex(' ')}，实际 {cur.hex(' ')} —— 不匹配，中止，未做修改。")
        return

    print(f"{'偏移':>9}  原指令                    → 新指令")
    print(f"  0x{OFF:06X}  {OLD.hex(' ')}  mov eax,[0x499148]  →  {NEW.hex(' ')}  mov eax,0x{LCID:04X} (zh-CN)")
    print(f"\n效果：GetDateFormatA(0x{LCID:04X}, DATE_LONGDATE, …) ⇒ 「2006年4月3日」")

    if not apply:
        print("\n[dry-run] 未写入。加 --apply 执行。")
        return

    if not os.path.exists(SNAP):
        shutil.copy2(EXE, SNAP)
        print(f"\n已备份 → {SNAP}")
    else:
        print(f"\n备份已存在，跳过 → {SNAP}")

    b[OFF:OFF + 5] = NEW
    tmp = EXE + ".tmp"
    open(tmp, "wb").write(bytes(b))
    chk = open(tmp, "rb").read()
    assert len(chk) == len(b), "长度变化"
    assert chk[OFF:OFF + 5] == NEW, "回读校验失败"
    shutil.move(tmp, EXE)
    print(f"✅ 已写入 → {EXE}")
    print(f"   新 md5 {hashlib.md5(open(EXE,'rb').read()).hexdigest()}")


if __name__ == "__main__":
    main()
