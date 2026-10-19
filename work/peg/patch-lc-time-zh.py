# -*- coding: utf-8 -*-
"""PeG 日期「月份名 / 星期名」汉化补丁（第 30 轮）
================================================================================
问题：游戏信息面板的日期形如 `5 November 2012`，月份为英文。
      `Gui030.txt` 第 174–185 行虽已汉化为「一月…十二月」，但**日期格式化不读它**，
      而是走 **exe 内建的 MSVC CRT `lc_time` 表**（`strftime` 的 `%B`/`%A` 数据源）。

`lc_time` 数据区（PeG030.exe，.rdata）：
    0x8B474  "PM"            0x8B478  "AM"
    0x8B47C  月份全名  December..January（倒序，槽 12/12/8/12/8/8/8/8/8/12/8）
    0x8B4E4  月份缩写  Dec..Jan（槽 4B）
    0x8B514  星期全名  Saturday..Sunday（槽 12/8/12/12/8/8/8）
    0x8B558  星期缩写  Sat..Sun（槽 4B）
    0x8B578  "SunMonTueWedThuFriSat"（紧凑，3B/项）
    0x8B590  "JanFebMarAprMayJunJulAugSepOctNovDec"（紧凑，3B/项）
    指针数组在 .data：0xAC588（缩写）/ 0xAC5B8（全名）

做法：**原地替换「月份全名」与「星期全名」为中文 + NUL 填充**，长度与指针均不变。
      ⚠️ **缩写表与紧凑表保持英文** —— 槽位仅 3–4 字节，放不下汉字（改了会越界）。
      ⚠️ MBCS 已启用（见 patch-mbcs.py），中文能被正确渲染。
      ⚠️ 幂等：已是中文的项目自动跳过。

用法：
    python work/peg/patch-lc-time-zh.py            # dry-run
    python work/peg/patch-lc-time-zh.py --apply    # 写入（首次先备份 <exe>.pre-month-zh）
"""
import hashlib
import os
import shutil
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
EXE = os.path.join(GAME, "PeG030.exe")
SNAP = os.path.join(ROOT, r"peg\testbed\PeG030.exe.pre-month-zh")

# (偏移, 原英文, 中文, 槽位终点)
ITEMS = [
    # ---- 月份全名 ----
    (0x8B47C, "December",  "十二月", 0x8B488),
    (0x8B488, "November",  "十一月", 0x8B494),
    (0x8B494, "October",   "十月",   0x8B49C),
    (0x8B49C, "September", "九月",   0x8B4A8),
    (0x8B4A8, "August",    "八月",   0x8B4B0),
    (0x8B4B0, "July",      "七月",   0x8B4B8),
    (0x8B4B8, "June",      "六月",   0x8B4C0),
    (0x8B4C0, "April",     "四月",   0x8B4C8),
    (0x8B4C8, "March",     "三月",   0x8B4D0),
    (0x8B4D0, "February",  "二月",   0x8B4DC),
    (0x8B4DC, "January",   "一月",   0x8B4E4),
    # ---- 星期全名 ----
    (0x8B514, "Saturday",  "星期六", 0x8B520),
    (0x8B520, "Friday",    "星期五", 0x8B528),
    (0x8B528, "Thursday",  "星期四", 0x8B534),
    (0x8B534, "Wednesday", "星期三", 0x8B540),
    (0x8B540, "Tuesday",   "星期二", 0x8B548),
    (0x8B548, "Monday",    "星期一", 0x8B550),
    (0x8B550, "Sunday",    "星期日", 0x8B558),
]


def main():
    apply = "--apply" in sys.argv
    b = bytearray(open(EXE, "rb").read())
    print(f"exe {len(b)}B  md5 {hashlib.md5(bytes(b)).hexdigest()}\n")

    plan, skip, bad = [], 0, 0
    for off, en, zh, end in ITEMS:
        slot = end - off
        nb = zh.encode("gbk") + b"\x00"
        cur = bytes(b[off:off + len(nb)])
        if cur == nb:                                  # 已是中文 ⇒ 幂等跳过
            skip += 1
            continue
        if not bytes(b[off:off + len(en)]).startswith(en.encode("ascii")):
            print(f"  ❌ 0x{off:06X} 期望 {en!r}，实际 {bytes(b[off:off+12])!r}")
            bad += 1
            continue
        if len(nb) > slot:
            print(f"  ❌ 0x{off:06X} {zh} 需 {len(nb)}B > 槽位 {slot}B")
            bad += 1
            continue
        plan.append((off, end, nb + b"\x00" * (slot - len(nb)), en, zh, slot, len(nb)))

    if bad:
        print(f"\n有 {bad} 项不匹配，未做任何修改。")
        return

    print(f"{'偏移':>9}  {'槽':>3}  {'原英文':<10} → 中文")
    for off, end, new, en, zh, slot, ln in plan:
        print(f"  0x{off:06X}  {slot:3d}B  {en:<10} → {zh:<6} ({ln}B)")
    if skip:
        print(f"  （{skip} 项已是中文，跳过）")

    if not plan:
        print("\n✅ 全部已是中文，无需修改。")
        return
    if not apply:
        print(f"\n[dry-run] 共 {len(plan)} 项未写入。加 --apply 执行。")
        return

    if not os.path.exists(SNAP):
        shutil.copy2(EXE, SNAP)
        print(f"\n已备份 → {SNAP}")
    else:
        print(f"\n备份已存在，跳过 → {SNAP}")
    for off, end, new, *_ in plan:
        b[off:end] = new
    tmp = EXE + ".tmp"
    open(tmp, "wb").write(bytes(b))
    chk = open(tmp, "rb").read()
    assert len(chk) == len(b), "长度变化"
    for off, end, new, en, zh, slot, ln in plan:
        gb = zh.encode("gbk")
        assert chk[off:off + len(gb)] == gb, f"回读失败 @0x{off:X}"
        assert chk[off + len(gb):end] == b"\x00" * (slot - len(gb)), f"NUL 填充失败 @0x{off:X}"
        assert chk[end:end + 4] != b"", f"槽尾越界 @0x{off:X}"
    shutil.move(tmp, EXE)
    print(f"✅ 已写入 {len(plan)} 项 → {EXE}")
    print(f"   新 md5 {hashlib.md5(open(EXE,'rb').read()).hexdigest()}")


if __name__ == "__main__":
    main()
