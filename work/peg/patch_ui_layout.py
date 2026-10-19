# -*- coding: utf-8 -*-
"""PeG UI 重排：把 0x4A22F8 的界面记录挪到新分辨率四边（控件尺寸不变）。

推导依据（静态读穿，母本未改）：
  * 记录表 0x4A22F8，步长 0x24，条数 = word[0x4af460]
      +0 u16 flags / +2 i16 x / +4 i16 y / +6 i16 right / +8 i16 bottom
      +0xa i16 / +0xc i16 / +0x10..+0x20 = 5 个回调指针（+0x10 = 0x44ACDA 绘制）
  * idx0..12 = 右侧 13 个按钮（x=762..787，y=41+36i，高 25）
    idx13    = 左上动作条 (20..334 x 43..54)
    idx14    = 底栏 (10..790 x 576..594)
    idx15    = 地图视口 (0..799 x 22..571)  ← 本版不动
  * 绘制处理器 0x44ACDA：rect = {x, y-1, right+1, bottom+1}；
    dx = 0x2ef(751) - rec.x，dy = 0x16(22) - (rec.y-1)（仅 idx1/idx4 且
    (word[0x4c90e0]>>1)&1 时使用）。记录右移后 dx 变得更负，走 0x47E4E0 里
    “dx<0 时保持 rect.left” 的分支，因此本版**不改**这两处常量。

用法：
  python patch_ui_layout.py                 # 干跑（默认）
  python patch_ui_layout.py --apply
  python patch_ui_layout.py --w 1600 --h 900 --base <exe> --out <exe> --apply
"""
import argparse
import hashlib
import os
import struct
import sys

import pefile

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


TABLE = 0x4A22F8
STRIDE = 0x24
BASE_W, BASE_H = 800, 600
MOTHER = os.path.join(GAME, "PeG030.exe")
MOTHER_MD5 = "c462e897b3aa1c384870c857ce9e01df"
DEFAULT_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "out", "PeG030-1920x1080.exe")
DEFAULT_BASE_MD5 = "44ac5cfe5a5875aa5ef51efd3d1afcf4"
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "out", "PeG030-1920x1080-UIa.exe")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_sites(w, h, grow_viewport=False):
    """返回 [(va, field_name, delta, idx, tag, field_off)]"""
    dx = w - BASE_W
    dy = h - BASE_H
    sites = []

    def add(idx, field_off, name, delta, why):
        va = TABLE + idx * STRIDE + field_off
        sites.append((va, name, delta, idx, why, field_off))

    for idx in range(13):                      # 右侧 13 个按钮：整体右移，贴右缘
        add(idx, 2, "x", dx, "toolbar-button")
        add(idx, 6, "right", dx, "toolbar-button")
    add(13, 2, "x", dx // 2, "action-box")     # 左上动作条：水平居中
    add(13, 6, "right", dx // 2, "action-box")
    add(14, 4, "y", dy, "bottom-bar")          # 底栏：下移贴底
    add(14, 8, "bottom", dy, "bottom-bar")
    add(14, 6, "right", dx, "bottom-bar")      # 底栏：右端拉到新右缘
    if grow_viewport:                          # idx15 地图视口记录：撑到新视口
        add(15, 6, "right", dx, "viewport")
        add(15, 8, "bottom", dy, "viewport")
    return sites


def mother_old(idx, field_off):
    """母本里的原值（96 版实测）。基准可以是母本，也可以是已打 16:9 尺寸补丁的
    产物（那批补丁里已含 idx14 的 dy 位移），所以只断言现值 == 母本值或 == 目标值。"""
    if 0 <= idx <= 12:
        return {2: 762, 6: 787}[field_off]
    if idx == 13:
        return {2: 20, 6: 334}[field_off]
    if idx == 14:
        return {4: 576, 8: 594, 6: 790}[field_off]
    if idx == 15:
        return {6: 799, 8: 571}[field_off]
    raise KeyError(idx)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--grow-viewport", action="store_true",
                    help="同时把 idx15 地图视口记录撑到新视口（变体 B）")
    args = ap.parse_args()

    base_md5 = md5(MOTHER)
    if base_md5 != MOTHER_MD5:
        sys.exit("母本 md5 不符：%s" % base_md5)
    if not os.path.exists(args.base):
        sys.exit("基准产物不存在：%s" % args.base)
    bmd5 = md5(args.base)
    if os.path.abspath(args.base) == os.path.abspath(DEFAULT_BASE) and bmd5 != DEFAULT_BASE_MD5:
        sys.exit("16:9 基准 md5 不符：%s" % bmd5)

    with open(args.base, "rb") as f:
        buf = bytearray(f.read())
    pe = pefile.PE(data=bytes(buf), fast_load=True)
    img = pe.OPTIONAL_HEADER.ImageBase
    secs = [(img + s.VirtualAddress, s.VirtualAddress,
             max(s.Misc_VirtualSize, s.SizeOfRawData),
             s.PointerToRawData) for s in pe.sections]

    def raw_off(va):
        for a, rva, sz, praw in secs:
            if a <= va < a + sz:
                return praw + (va - a)
        sys.exit("VA 不在任何节区：0x%08x" % va)

    def rd_i16(va):
        o = raw_off(va)
        return struct.unpack_from("<h", buf, o)[0]

    sites = build_sites(args.w, args.h, args.grow_viewport)
    ok = 0
    expected = []
    for va, name, delta, idx, why, field_off in sites:
        m_old = mother_old(idx, field_off)
        target = m_old + delta
        cur = rd_i16(va)
        if cur not in (m_old, target):
            sys.exit("内容断言失败：0x%08x idx%d %s 现值 %d，既不是母本值 %d 也不是目标值 %d"
                     % (va, idx, name, cur, m_old, target))
        if not (-32768 <= target <= 32767):
            sys.exit("越界：0x%08x %s %d" % (va, name, target))
        print("idx%-2d %-8s %+5d  0x%08x  %6d -> %6d   %s"
              % (idx, name, delta, va, cur, target, why))
        expected.append((va, cur, target))
        if args.apply:
            struct.pack_into("<h", buf, raw_off(va), target)
        ok += 1

    print("站点 %d 条，基准 %s (md5 %s)" % (ok, os.path.basename(args.base), bmd5))
    if not args.apply:
        print("干跑完成（未写盘）。加 --apply 落盘。")
        return

    # 回读校验
    bad = 0
    for va, exp_old, exp_new in expected:
        got = struct.unpack_from("<h", buf, raw_off(va))[0]
        if got != exp_new:
            bad += 1
            print("回读不符：0x%08x 期望 %d，实际 %d" % (va, exp_new, got))
    print("回读校验：%d/%d 通过" % (ok - bad, ok))
    if bad:
        sys.exit("存在回读不符，已中止写盘")

    tmp = args.out + ".tmp"
    with open(tmp, "wb") as f:
        f.write(bytes(buf))
    with open(tmp, "rb") as f:
        if f.read() != bytes(buf):
            sys.exit("临时文件回读不一致")
    os.replace(tmp, args.out)
    print("已写出 %s  md5 %s" % (args.out, md5(args.out)))
    tsv = os.path.join(os.path.dirname(args.out), "ui_layout_v9.tsv")
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("idx\tfield\tva\tdelta\tnew_value\ttag\n")
        for va, name, delta, idx, why, field_off in sites:
            f.write("%d\t%s\t0x%08x\t%+d\t%d\t%s\n"
                    % (idx, name, va, delta, rd_i16(va), why))
    print("站点表 %s" % tsv)


if __name__ == "__main__":
    main()
