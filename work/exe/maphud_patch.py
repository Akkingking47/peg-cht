# -*- coding: utf-8 -*-
"""OpenGen.exe 地图悬浮提示 / HUD 格式串块汉化（VA 0x911F80 起，FO 0x511180）。

本块特征：串**紧凑排布、每条对齐到 4 字节边界** ⇒ 单条可用空间
        avail = 下一串起点 - FO （= ceil((len+1)/4)*4 左右），务必不要越过。

三类处理：
  1) 原地替换：len(dst_gbk)+1 <= avail ⇒ 直接覆盖，余量填 NUL。
  2) 空洞 + 改指针：avail 不够的短串，写入 .rdata 空洞，再把唯一的
     push imm32 立即数改成新 VA。
  3) 不译：纯格式串 / 符号 / 大写缩写 / 扩展名 / 偶然匹配的非文本。

用法:
  python maphud_patch.py          # 干跑（只报告，不写盘）
  python maphud_patch.py --apply  # 正式写入
"""
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib                     # PE 目录 / 空洞安全检查

EXE = r"D:/OpenPG2/OpenGen.exe"
RDATA_DELTA = 0x400E00          # VA = FO + 0x400E00  (.rdata)

# 空洞：.rdata 内连续 NUL 区 FO 0x4ECB39 / VA 0x8ED939，64 B
# 安全性以 pelib 三项检查为准（全 NUL / 不在任何 PE 数据目录内 / 0 引用）；
# ⚠️ 仅「全 NUL + 0 引用」不够 —— 见 unitpanel_patch.py 里 0x51CB31 的 LoadConfig 事故。
HOLE_FO = 0x4ECB39
HOLE_VA = HOLE_FO + RDATA_DELTA     # 0x8ED939
HOLE_LEN = 64

# 本块的串区起止（用于算 avail 与不译清单审计）
BLOCK_LO = 0x511180
BLOCK_HI = 0x511700

# ---- 1) 原地替换 (FO, 原文, 译文) ----
INPLACE = [
    (0x511184, "Press ESC key to close this intro and continue",
     "按 ESC 键关闭此简介并继续"),
    (0x5111BC, "Odds: %d-%d   ", "胜率:%d-%d   "),
    (0x5111D4, "AP:%d  Fort:%d  Port:%d  Station:%d  Bridge:%d pp",
     "行动点:%d  要塞:%d  港口:%d  车站:%d  桥梁:%d pp"),
    (0x511214, "  Fuel:%d %s", "  燃料:%d %s"),
    (0x511228, "  Ammo:- ", "  弹药:- "),
    (0x511234, "  Ammo:%d/%d ", "  弹药:%d/%d "),
    (0x511244, "KeepAir ", "保持空中 "),
    (0x5112A4, " Map: %d x %d", " 地图: %d x %d"),
    (0x5112B4, "  Ammo:%d ", "  弹药:%d "),
    (0x5112D4, "* Until T%d", "* 直到 T%d"),
    (0x5112E0, "VH to take by ", "VH 占领方："),
    (0x5112F0, "Both sides", "双方"),
    (0x5112FC, " (Friends)", " (友军)"),
    (0x511308, " (Enemy)", " (敌军)"),
    (0x511314, "Out of map boundaries", "超出地图边界"),
    (0x51132C, "EH: Land, Naval & Air", "EH: 陆、海、空"),
    (0x511344, "EH: Land & Naval", "EH: 陆、海"),
    (0x511358, "EH: Air", "EH: 空"),
    (0x511360, "Enemy", "敌军"),
    (0x511374, "Friends", "友军"),
    (0x51137C, "Enemy", "敌军"),
    (0x511384, " (Friends)", " (友军)"),
    (0x511390, " (Enemy", " (敌军"),
    (0x511398, "SH for", "SH 归属"),
    (0x5113A0, "Friends", "友军"),
    (0x5113A8, "Friends", "友军"),
    (0x5113B0, "Enemy", "敌军"),
    (0x5113D4, "Friends", "友军"),
    (0x5113DC, "Enemy", "敌军"),
    (0x5113F0, "Enemy", "敌军"),
    (0x5113F8, "Friends", "友军"),
    (0x511400, "Enemy", "敌军"),
    (0x511408, "SH for Owner", "SH 归属方"),
    (0x511418, "SH for ", "SH 归属"),
    (0x511420, "Both", "双方"),
    (0x511428, "Friends", "友军"),
    (0x511438, "PAUSED .. type P to resume or Ctrl+Q exit game",
     "已暂停 .. 按 P 继续，或 Ctrl+Q 退出游戏"),
    (0x511468, "REPLAY .. type P to pause or Enter to break",
     "回放中 .. 按 P 暂停，或 Enter 中断"),
    (0x51149C, " No prestige bonus nor penalty ", " 无声望加成或处罚 "),
    (0x5114BC, "(%d,%d)  Click to show/select choice: #%d ... %s",
     "(%d,%d)  点击显示/选择项： #%d ... %s"),
    (0x5114F0, "Playing DEBUG_AI mode (view from AI)  and  DEBUG_LG mode "
               "(can buy/resupply and add-bars for free)",
     "正在 DEBUG_AI 模式（AI 视角），且 DEBUG_LG 模式"
     "（可免费购买/补给并增加经验条）"),
    (0x511554, "(%d,%d)  Click mouse in a flag to show details / select option",
     "(%d,%d)  点击旗帜查看详情 / 选择选项"),
    (0x511594, " This option will increase your prestige %d pp ",
     " 此选项将增加你的声望 %d pp "),
    (0x5115C4, " This option will decrease your prestige! (%d pp) ",
     " 此选项将降低你的声望！(%d pp) "),
    (0x5115F8, "Playing DEBUG_AI mode: all units are revealed and F.O.W. is "
               "set for active player side",
     "正在 DEBUG_AI 模式：所有单位均可见，且战争迷雾设为当前玩家方"),
    (0x511650, "DEBUG_LG mode: can buy for free, can resupply/reinforce and "
               "add exp-bars w/t restrictions",
     "DEBUG_LG 模式：可免费购买，可自由补给/增援并增加经验条"),
]

# ---- 2) 空洞 + 改指针 (原文FO, 引用处FO, 原文, 译文) ----
# 三条引用点均为 push imm32，全 exe 唯一
REDIRECT = [
    (0x511250, 0x4038A0, " Mov:%d Mnt:%d", " 机动:%d 山地:%d"),
    (0x511260, 0x4038E1, " Mov:%d", " 机动:%d"),
    (0x511268, 0x40391D, " %s%d/%d Exp:%d  Ent:%d",
     " %s%d/%d 经验:%d  工事:%d"),
]

# ---- 3) 明确不译清单（审计用）----
SKIP_NOTE = (
    "纯格式串/符号：' %s ' ' %s' ' %s (%s)' ' %s%d/%d' ' [S:%d H:%d]' "
    "' {Sab}' ' OH(%d,%d)' ' OH(%d,%d)>U:%d' ' * ' '  ***  ' ' ... ' '><' "
    "' P1..P4 (%s)' · 大写缩写：'U:%d' 'pp' 'EH' 'SH' 'F.O.W.'→战争迷雾(内联已译) "
    "· 非文本：'s2' ':' '>' '.jpg' '.png' '.bmp' '.gif'"
)


def scan_avail(d):
    """（仅用于首次生成 AVAIL 表，勿在已汉化文件上调用）

    逐 Tout C 串扫描：可打印 ASCII **或 GBK 字节(>=0x81)** 都算串内容，
    这样中英混合状态都能得到同一套边界。
    """
    i = BLOCK_LO
    starts = []
    while i < BLOCK_HI:
        b = d[i]
        if 0x20 <= b < 0x7F or b >= 0x81 or b in (9, 10, 13):
            j = i
            while j < BLOCK_HI and (0x20 <= d[j] < 0x7F or d[j] >= 0x81
                                    or d[j] in (9, 10, 13)):
                j += 1
            starts.append(i)
            i = j
        else:
            i += 1
    av = {}
    for k, s in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else BLOCK_HI
        av[s] = nxt - s
    return av


# 每条串的可用空间 = 下一串起点 - FO（**原始英文状态下**测得）。
# ⚠️ 这是原文件的静态属性，必须硬编码：avail 若在运行期动态扫描，
#    中文 GBK 字节(0xA1-0xFE) 不在 [0x20,0x7F) 内 ⇒ 已汉化后算出的边界全错。
AVAIL = {
    0x511184: 48, 0x5111BC: 16, 0x5111D4: 52, 0x511214: 16,
    0x511228: 12, 0x511234: 16, 0x511244: 12, 0x511250: 16,
    0x511260: 8,  0x511268: 24, 0x5112A4: 16, 0x5112B4: 12,
    0x5112D4: 12, 0x5112E0: 16, 0x5112F0: 12, 0x5112FC: 12,
    0x511308: 12, 0x511314: 24, 0x51132C: 24, 0x511344: 20,
    0x511358: 8,  0x511360: 8,  0x511374: 8,  0x51137C: 8,
    0x511384: 12, 0x511390: 8,  0x511398: 8,  0x5113A0: 8,
    0x5113A8: 8,  0x5113B0: 8,  0x5113D4: 8,  0x5113DC: 8,
    0x5113F0: 8,  0x5113F8: 8,  0x511400: 8,  0x511408: 16,
    0x511418: 8,  0x511420: 8,  0x511428: 8,  0x511438: 48,
    0x511468: 44, 0x51149C: 32, 0x5114BC: 52, 0x5114F0: 100,
    0x511554: 64, 0x511594: 48, 0x5115C4: 52, 0x5115F8: 88,
    0x511650: 92,
}


def main():
    apply_ = "--apply" in sys.argv
    d = bytearray(open(EXE, "rb").read())
    orig_len = len(d)
    errs = []
    avail = AVAIL

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
        # ⚠️ 读写窗口都必须用 avail（下一串起点 - FO），不能用 len(old)：
        #    ① 写入：new 常比 old 长（中文占双字节而英文一行显示更窄），
        #       用 len(old) 做切片 ⇒ pad 变负 ⇒ 切片赋值撑长整个 bytearray，
        #       后续所有字节位移、文件错乱（本脚本首版就踩过）；
        #    ② 幂等检查：若窗口取 len(old)，而译文恰好比 old 长，
        #       cur 会被截断到比 chk 还短 ⇒ 永远比不上 ⇒ 重跑误报"原文不符"。
        lim = AVAIL.get(fo, len(old))
        cur = bytes(d[fo:fo + lim])
        if cur[:len(old)] != old:
            chk = dst.encode("gbk") + b"\x00"
            if cur[:len(chk)] == chk:
                print("  0x%06X  %-34r -> %-24s  已生效，跳过" % (fo, src, dst))
                continue
            errs.append("原文不符 FO 0x%X %r != %r" % (fo, cur[:40], old[:40]))
            continue
        new = dst.encode("gbk") + b"\x00"
        # 写入窗口必须是 avail（下一串起点 - FO），不能是 len(old)：
        # 这批串 4 字节对齐紧凑排布，new 常大于 old+1；若用 len(old) 做切片，
        # pad 变负数 ⇒ 切片赋值会撑长整个 bytearray，后续全部位移、文件错乱。
        lim = AVAIL.get(fo, len(old))
        if len(new) > lim:
            errs.append("超长 FO 0x%X %d>%d (avail)" % (fo, len(new), lim))
            continue
        d[fo:fo + lim] = new + b"\x00" * (lim - len(new))
        print("  0x%06X  %-34r -> %-24s  %2d/%2dB (avail %2d)"
              % (fo, src[:34], dst[:24], len(new), lim, lim))

    # ---------- 空洞 ----------
    print("=== 空洞改写 (%d 条) ===" % len(REDIRECT))
    off = 0
    for src_fo, ref_fo, src, dst in REDIRECT:
        old_va = src_fo + RDATA_DELTA
        new = dst.encode("gbk") + b"\x00"
        new_va = HOLE_VA + off
        cur_va = struct.unpack_from("<I", d, ref_fo)[0]
        if cur_va == new_va and \
                bytes(d[HOLE_FO + off:HOLE_FO + off + len(new)]) == new:
            print("  0x%06X  %-32r -> %-22s  已生效，跳过" % (src_fo, src, dst))
            off += len(new)
            continue
        if cur_va != old_va:
            errs.append("引用处不符 FO 0x%X (现值 0x%X)" % (ref_fo, cur_va))
            off += len(new)
            continue
        if d.count(struct.pack("<I", old_va)) != 1:
            errs.append("引用不唯一 VA 0x%X (%d 处)"
                        % (old_va, d.count(struct.pack("<I", old_va))))
            off += len(new)
            continue
        if bytes(d[src_fo:src_fo + len(src) + 1]) != src.encode("latin-1") + b"\x00":
            errs.append("原文不符 FO 0x%X %r" % (src_fo, src))
            off += len(new)
            continue
        if off + len(new) > HOLE_LEN:
            errs.append("空洞不足 (需 %d, 余 %d)" % (len(new), HOLE_LEN - off))
            continue
        if bytes(d[HOLE_FO + off:HOLE_FO + off + len(new)]) != b"\x00" * len(new):
            errs.append("空洞已被占用 @+%d" % off)
            continue
        d[HOLE_FO + off:HOLE_FO + off + len(new)] = new
        struct.pack_into("<I", d, ref_fo, new_va)
        print("  0x%06X  %-32r -> %-22s  新VA 0x%06X  hole+%d (%dB)"
              % (src_fo, src, dst, new_va, off, len(new)))
        off += len(new)
    print("  空洞占用 %d/%d 字节" % (off, HOLE_LEN))

    print("\n不译清单：%s" % SKIP_NOTE)

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
