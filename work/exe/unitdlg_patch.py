# -*- coding: utf-8 -*-
"""OpenGen.exe 单位升级 / 指挥官对话框串块汉化（第二批）。

- INPLACE：单行串，GBK 字节数 <= 原文长度+1，原地覆盖、余量填 NUL。
- BLOCKS：多行消息块。块内的子串偏移（如 0x514294 / 0x514527）经查 **0 引用**，
          只是块内子串，故可整块覆盖而不破坏指针。
- REDIRECT：放不下的短串写入 .rdata 空洞 2，并把唯一的立即数改成新 VA。

用法:
  python unitdlg_patch.py           # 干跑
  python unitdlg_patch.py --apply   # 写入
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib                     # PE 目录 / 空洞安全检查

EXE = r"D:/OpenPG2/OpenGen.exe"
DELTA = 0x400E00                 # .rdata: VA = FO + 0x400E00

# 空洞 2：rtdialog 长文本之后的 NUL 填充；已过 pelib 三项检查
# ① 全 NUL ② 不与任何 PE 数据目录相交 ③ 区内 4B 对齐点 0 引用
HOLE2_FO = 0x4B1C86
HOLE2_VA = HOLE2_FO + DELTA      # 0x8B2A86
HOLE2_LEN = 76

INPLACE = [
    (0x513CE8, "*%s*   %s   Cost:  %d + %d%% unit's cost ",
     "*%s*   %s   花费:  %d + %d%% 单位成本 "),
    (0x513D14, " >> (disabled)", " >> (已禁用)"),
    (0x513D24, "*%s*   %s   Cost: %dpp (%d + %d)",
     "*%s*   %s   花费: %d点 (%d + %d)"),
    (0x514104, "%s * idx:%d - Fronts: %d Factns: %d - %s",
     "%s * 序号:%d - 战线:%d 阵营:%d - %s"),
    (0x514184, "Unit: %s", "单位：%s"),
    (0x514190, "Unit: %s  (%s)", "单位：%s  (%s)"),
    (0x5141A0, "Main country: %s", "主国：%s"),
    (0x5141B4, "Support country %d: %s", "支援国 %d：%s"),
    (0x51430C, "  .. E:%04d  Fronts: %d  Factns: %d",
     "  .. E:%04d  战线:%d  阵营:%d"),
    (0x514330, " -- Avail:%s -> %s", " -- 可用:%s -> %s"),
    (0x514344, "Upgrading will remove %d attachments. Do you want to continue",
     "升级将移除 %d 个附属单位。是否继续？"),
    (0x514388, "Cannot reassign unit!", "无法重新分配单位！"),
    (0x51458C, "%s  Bomb Size:%d", "%s  载弹量:%d"),
    (0x514600, "No hangars", "无可用机库"),
    (0x51461C, "Number of hangars: %d", "机库数量：%d"),
    (0x5146BC, "Units matching hangar's weight", "符合机库载重的单位"),
    (0x5146E0, "Hangar cap=%d", "机库容量=%d"),
]

BLOCKS = [
    (0x5141D4, "The new unit cannot attack any target! \n\n",
     "新单位无法攻击任何目标！\n\n"),
    (0x514258,
     "The current leader is useless for the new unit, so you can:\n"
     "* if you want to change leader losing 1 bar: press OK\n"
     "* if you want to upgrade keeping leader and bars: press CANCEL\n",
     "当前指挥官对新单位无用，你可以：\n"
     "* 若想更换指挥官并损失 1 条经验条：按 OK\n"
     "* 若想保留指挥官与经验条升级：按 CANCEL\n"),
    (0x5143A0,
     "Leader's random attribute changed. Unit's exp-bars reduced to: %d\n",
     "指挥官随机属性已更改，单位经验条降至：%d\n"),
    (0x5143E8,
     "Upgrading to this new equipment, will result in losing 1 exp-bar "
     "to change leader's random attribute\nAre you sure to continue ?",
     "升级到此新装备将损失 1 条经验条，以更改指挥官的随机属性\n确定要继续吗？"),
    (0x514468,
     "Unit set exp-level: %d and exp-bar:%d, after losing its leader\n",
     "失去指挥官后单位经验等级设为 %d，经验条 %d\n"),
    (0x5144A8,
     "Upgrading to this new equipment, will remove the leader,\n"
     "resulting:  exp-level = %d ; exp-bar = %d and chance-to-leader = 70%%\n"
     "so it can get another leader later\nAre you sure to continue ? ",
     "升级到此新装备将移除指挥官，\n"
     "结果：经验等级 = %d ；经验条 = %d ；获得指挥官几率 = 70%%\n"
     "以便日后获得新的指挥官\n确定要继续吗？ "),
]

REDIRECT = [
    (0x514140, 0x422EF1, "U:%d  %s  [Exp:%d] - %s * %s",
     "U:%d  %s  [经验:%d] - %s * %s"),
    (0x514160, 0x422E91, "U:%d  %s  [Exp:%d] <%s> - %s * %s",
     "U:%d  %s  [经验:%d] <%s> - %s * %s"),
]


EXTRA = [
    (0x5139C0, "%s not found, neither external nor in DatFile.dat\n",
     "%s 未找到，外部与 DatFile.dat 中均无\n"),
    (0x514200,
     "Leader's random attribute is not valid for this leader "
     "and will be changed or removed",
     "该指挥官的随机属性无效，将被更改或移除"),
]


def put(d, fo, src, dst, errs, tag):
    old = src.encode("latin-1") + b"\x00"
    cur = bytes(d[fo:fo + len(old)])
    if cur != old:
        # 幂等：已经是目标译文就跳过（重跑安全）
        new_chk = dst.encode("gbk") + b"\x00"
        if cur[:len(new_chk)] == new_chk:
            return 0
        errs.append("%s 原文不符 FO 0x%X" % (tag, fo))
        return 0
    new = dst.encode("gbk") + b"\x00"
    if len(new) > len(old):
        errs.append("%s 超长 FO 0x%X %d>%d" % (tag, fo, len(new), len(old)))
        return 0
    d[fo:fo + len(old)] = new + b"\x00" * (len(old) - len(new))
    return 1


def main():
    apply_ = "--apply" in sys.argv
    d = bytearray(open(EXE, "rb").read())
    orig_len = len(d)
    errs = []

    pe = pelib.PE(bytes(d))
    probs = pe.check_hole(HOLE2_FO, HOLE2_LEN)
    fatal = [p for p in probs if "相交" in p]
    if fatal:
        print("!! 空洞不安全，拒绝执行：")
        for p in fatal:
            print("   " + p)
        return
    if probs:
        print("[提示] 空洞检查：%s（首跑应为空；重跑时因已写入而属正常）" % probs)

    print("=== 单行原地 (%d) ===" % len(INPLACE))
    n = 0
    for fo, src, dst in INPLACE:
        if put(d, fo, src, dst, errs, "IN"):
            n += 1
            print("  0x%06X %-46r -> %s" % (fo, src[:46], dst))
    print("  成功 %d" % n)

    print("=== 补遗 (%d) ===" % len(EXTRA))
    n = 0
    for fo, src, dst in EXTRA:
        if put(d, fo, src, dst, errs, "EX"):
            n += 1
            print("  0x%06X %-50r -> %s" % (fo, src[:50], dst))
    print("  成功 %d" % n)

    print("=== 多行整块 (%d) ===" % len(BLOCKS))
    n = 0
    for fo, src, dst in BLOCKS:
        if put(d, fo, src, dst, errs, "BLK"):
            n += 1
            print("  0x%06X  %d行  %d->%dB  %s" %
                  (fo, src.count("\n") + 1, len(src) + 1,
                   len(dst.encode("gbk")) + 1, dst.split("\n")[0]))
    print("  成功 %d" % n)

    print("=== 空洞改写 (%d) ===" % len(REDIRECT))
    off = 0
    for src_fo, ref_fo, src, dst in REDIRECT:
        old_va = src_fo + DELTA
        new = dst.encode("gbk") + b"\x00"
        new_va = HOLE2_VA + off
        cur_va = struct.unpack_from("<I", d, ref_fo)[0]
        # 幂等：指针已指向目标空洞且内容一致 -> 跳过
        if cur_va == new_va and bytes(d[HOLE2_FO + off:HOLE2_FO + off + len(new)]) == new:
            print("  0x%06X %-32r -> %-30s 已生效，跳过" % (src_fo, src, dst))
            off += len(new)
            continue
        if cur_va != old_va:
            errs.append("引用处不符 FO 0x%X (现值 0x%X)" % (ref_fo, cur_va))
            off += len(new)
            continue
        if d.count(struct.pack("<I", old_va)) != 1:
            errs.append("引用不唯一 VA 0x%X" % old_va)
            off += len(new)
            continue
        if bytes(d[src_fo:src_fo + len(src) + 1]) != src.encode("latin-1") + b"\x00":
            errs.append("原文不符 FO 0x%X" % src_fo)
            off += len(new)
            continue
        if off + len(new) > HOLE2_LEN:
            errs.append("空洞2 不足")
            continue
        if bytes(d[HOLE2_FO + off:HOLE2_FO + off + len(new)]) != b"\x00" * len(new):
            errs.append("空洞2 已被占用 @+%d" % off)
            continue
        d[HOLE2_FO + off:HOLE2_FO + off + len(new)] = new
        struct.pack_into("<I", d, ref_fo, new_va)
        print("  0x%06X %-32r -> %-30s 新VA 0x%06X" % (src_fo, src, dst, new_va))
        off += len(new)
    print("  空洞2 占用 %d/%d" % (off, HOLE2_LEN))

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
    print("\n已写入 %s  长度 %d (原 %d) %s" %
          (EXE, len(d), orig_len, "一致" if len(d) == orig_len else "不一致!"))

    c = open(EXE, "rb").read()
    ok = True
    for fo, src, dst in INPLACE + BLOCKS + EXTRA:
        got = c[fo:c.find(b"\x00", fo)].decode("gbk", "replace")
        if got != dst:
            print("  !! 校验失败 0x%X %r" % (fo, got))
            ok = False
    for src_fo, ref_fo, src, dst in REDIRECT:
        va = struct.unpack_from("<I", c, ref_fo)[0]
        fo = va - DELTA
        got = c[fo:c.find(b"\x00", fo)].decode("gbk", "replace")
        if got != dst:
            print("  !! 校验失败 VA 0x%X %r" % (va, got))
            ok = False
    print("回读校验: %s" % ("全部通过" if ok else "有失败"))


if __name__ == "__main__":
    main()
