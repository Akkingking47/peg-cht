# -*- coding: utf-8 -*-
"""build_v5.py —— 在 v4 基础上，构造 v5 诊断变体（面板/布局代码侧补丁）

背景（见 docs\\54 / docs\\55）：
  v4 产物 = 母本 + 259 处「尺寸常量/数据记录」替换，其中 207 处在 .data
  （163 处 dx = x+224 的控件记录横向位移）。实机截图证明：地图铺满 1024 是对的，
  但界面（右侧工具列、底栏）没有跟着走 —— 因为界面布局在**代码里**按
  硬编码的 799/571/620/796/570 重新算（0x41C4D4 起的面板矩形 + 视口裁剪三组），
  而 v4 从未碰这条链。

本脚本只做一件事：把代码侧那 10 处立即数补上，产出可实机试跑的变体。

变体：
  a = v4 + 面板矩形 2 处（0x41C4D7 571→740、0x41C4DE 799→1023）      ← 最小诊断
  b = v4 + 面板矩形 + 屏幕边框 + 视口裁剪（共 10 处）
  c = 母本 + 全部 .text 站点(52) + 除 dx 外的 .data 站点(44) + 同一批 10 处代码补丁
      ← 「代码驱动布局、记录不做横向位移」这条更自洽的假设

纪律（与 patch_resolution.py 一致）：
  1. 默认干跑，--apply 才写盘；只写新文件，绝不覆盖母本与 v4 产物。
  2. 每个站点先做内容断言（当前值必须等于预期旧值），不符即整体拒绝。
  3. 先改内存 → 回读校验 → 才落盘（写到 .tmp 再 os.replace）。
  4. 落盘后复核中文补丁三处仍在。
"""
import argparse
import hashlib
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SRC = r"D:\Program Files\PeG\PeG030.exe"          # 母本（已含中文补丁）
V4 = r"D:\Program Files\PeG-1\PeG030res.exe"      # v4 产物
SRC_MD5 = "c462e897b3aa1c384870c857ce9e01df"
V4_MD5 = "2107b73bbfd4213719b622a1a9d4c6ad"
TSV = os.path.join(OUT, "res_diff_v4.tsv")

PW, PH = 1024, 768

# ---- 代码侧补丁（imm32 地址都已用 show_bytes.py 在产物里亲眼核对过）----
# (imm32 VA, 旧值, 新值, 说明)
PANEL_EDITS = [
    (0x41C4D7, 0x23B, 0x2E4, "面板矩形 bottom 571->740  (c7 45 f8 3b020000)"),
    (0x41C4DE, 0x31F, 0x3FF, "面板矩形 right  799->1023 (c7 45 f4 1f030000)"),
]
BORDER_EDITS = [
    (0x44C5CD, 0x23A, 0x2E2, "屏幕边框 push 570->738 (68 3a020000)"),
    (0x44C5D2, 0x31C, 0x3FC, "屏幕边框 push 796->1020 (68 1c030000)"),
]
CLIP_EDITS = [
    (0x44C731, 0x320, 0x400, "视口裁剪组1 mov eax,800->1024 (b8 20030000)"),
    (0x44C778, 0x258, 0x300, "视口裁剪组1 mov edx,600->768  (ba 58020000)"),
    (0x44C86A, 0x320, 0x400, "视口裁剪组2 mov edx,800->1024"),
    (0x44C8B1, 0x258, 0x300, "视口裁剪组2 mov ecx,600->768"),
    (0x44CC68, 0x320, 0x400, "视口裁剪组3 mov edx,800->1024"),
    (0x44CCAF, 0x258, 0x300, "视口裁剪组3 mov ecx,600->768"),
]
CODE_EDITS = PANEL_EDITS + BORDER_EDITS + CLIP_EDITS

# ---- 地图界面右侧工具列 7 个按钮记录（步长 36；每条的 x=+2、right=+6）----
# 母本内容：flags=0x1045, x=762, right=787, y=71/428/140/212/284/356/527, bottom=y+25
BTN_RECS = [0x490494, 0x4904B8, 0x4904DC, 0x490500, 0x490524, 0x490548, 0x49056C]
BTN_FIELD_VAS = set()
for _b in BTN_RECS:
    BTN_FIELD_VAS.add(_b + 2)   # x
    BTN_FIELD_VAS.add(_b + 6)   # right

# ---- 中文补丁三处（只复核，不改）----
CN_CHECKS = [
    (0x070CE3, bytes.fromhex("6a86"), "charset 0x86 GB2312"),
    (0x0A948C, bytes.fromhex("a803"), "__mbcodepage 936"),
    (0x07BE86, bytes.fromhex("b804080000"), "GetDateFormatA LCID 0x0804"),
]

# ---- 节表（本工程实测）----
SECS = [
    (".text", 0x401000, 0x400, 0x8A200),
    (".rdata", 0x48C000, 0x8A600, 0x1200),
    (".data", 0x48E000, 0x8B800, 0x21400),
    (".idata", 0x6AA000, 0xACC00, 0x5E00),
    (".rsrc", 0x6AC000, 0xAE200, 0x5600),
]


def va_to_fo(va):
    for name, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva)
    raise ValueError("VA %#x 不在任何已知节内" % va)


def rd_u32(b, fo):
    return struct.unpack_from("<I", b, fo)[0]


def rd_u16(b, fo):
    return struct.unpack_from("<H", b, fo)[0]


def load_tsv():
    rows = []
    with open(TSV, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            rec = dict(zip(head, parts))
            rows.append({
                "section": rec["section"],
                "va": int(rec["va"], 16),
                "fo": int(rec["file_off"], 16),
                "width": int(rec["width"]),
                "old": int(rec["old"]),
                "new": int(rec["new"]),
                "tag": rec["tag"],
                "note": rec["note"],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=["a", "b", "c", "d"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = bytearray(open(SRC, "rb").read())
    cur_md5 = hashlib.md5(data).hexdigest()

    plan = []          # (fo, width, old, new, label)
    if args.variant in ("c", "d"):
        if cur_md5 != SRC_MD5:
            print("母本 md5 不符：期望 %s，实际 %s —— 中止" % (SRC_MD5, cur_md5))
            return 2
        rows = load_tsv()
        skip_dx = 0
        btn_dx = 0
        for r in rows:
            if r["section"] == ".data" and r["tag"] == "dx":
                if args.variant == "d" and r["va"] in BTN_FIELD_VAS:
                    btn_dx += 1          # 变体 d：只保留工具列 7 条按钮记录的位移
                else:
                    skip_dx += 1
                    continue          # dx = 控件记录横向位移：本变体刻意不做
            plan.append((r["fo"], r["width"], r["old"], r["new"],
                         "%s %s (%s)" % (r["section"], r["tag"], r["note"][:40])))
        print("变体 %s：采用站点 %d 条（跳过 dx 位移 %d 条，其中按钮记录字段 %d 条）"
              % (args.variant, len(plan), skip_dx, btn_dx))
    else:
        v4 = open(V4, "rb").read()
        if hashlib.md5(v4).hexdigest() != V4_MD5:
            print("v4 产物 md5 不符，中止")
            return 2
        data = bytearray(v4)
        cur_md5 = V4_MD5
        print("变体 %s：基准 = v4 产物（md5 %s）" % (args.variant, V4_MD5))

    edits = PANEL_EDITS if args.variant == "a" else CODE_EDITS
    for va, old, new, note in edits:
        plan.append((va_to_fo(va), 4, old, new, note))

    # ---- 逐站点内容断言 ----
    bad = 0
    print("\n---- 站点检查 ----")
    for i, (fo, width, old, new, label) in enumerate(plan):
        cur = rd_u16(data, fo) if width == 2 else rd_u32(data, fo)
        ok = (cur == old)
        if not ok:
            bad += 1
            print("  [%3d] 0x%08X 期望 %d 实际 %d  ✗ %s" % (i, fo, old, cur, label))
        elif i < 6 or i > len(plan) - 11:
            print("  [%3d] 0x%08X %d -> %d  ✓ %s" % (i, fo, old, new, label))
    print("  共 %d 条，断言失败 %d 条" % (len(plan), bad))
    if bad:
        print("断言未通过 —— 整体拒绝，未做任何修改。")
        return 3

    # ---- 改内存 ----
    for fo, width, old, new, label in plan:
        struct.pack_into("<H" if width == 2 else "<I", data, fo, new)

    # ---- 回读校验 ----
    for fo, width, old, new, label in plan:
        cur = rd_u16(data, fo) if width == 2 else rd_u32(data, fo)
        if cur != new:
            print("回读失败 @0x%08X" % fo)
            return 4
    print("回读校验：全部 %d 条已就位" % len(plan))

    # ---- 中文补丁复核 ----
    for fo, want, label in CN_CHECKS:
        got = bytes(data[fo:fo + len(want)])
        print("  中文补丁 %-28s %s %s" % (label, got.hex(" "), "✓" if got == want else "✗"))
        if got != want:
            return 5

    # ---- 差异统计 ----
    base = open(SRC if args.variant in ("c", "d") else V4, "rb").read()
    diffs = [i for i in range(len(base)) if base[i] != data[i]]
    runs = 0
    prev = -9
    for i in diffs:
        if i != prev + 1:
            runs += 1
        prev = i
    print("\n与基准差异：%d 字节 / %d 段" % (len(diffs), runs))
    print("输出 md5：%s" % hashlib.md5(bytes(data)).hexdigest())

    if not args.apply:
        print("\n[dry-run] 未写盘。加 --apply 执行。")
        return 0

    out = os.path.abspath(args.out)
    tmp = out + ".tmp"
    with open(tmp, "wb") as f:
        f.write(bytes(data))
    chk = open(tmp, "rb").read()
    assert len(chk) == len(base), "长度变化"
    for fo, width, old, new, label in plan:
        cur = rd_u16(chk, fo) if width == 2 else rd_u32(chk, fo)
        assert cur == new, "落盘回读失败 @0x%08X" % fo
    os.replace(tmp, out)
    print("已写出：%s（%d 字节）" % (out, os.path.getsize(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
