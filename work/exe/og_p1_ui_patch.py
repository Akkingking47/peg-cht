# -*- coding: utf-8 -*-
"""OpenGeneral OpenGen.exe —— P1：一批 exe 硬编码 UI 串汉化（原地等长替换）。

沿用 P0（og_p0_exit_patch.py）已证的方法：**只原地换字节，不挖空洞、不改指针、不碰 .text**。
本批 13 条串 / 21 个槽位，全部满足：
  · 该 VA 的 `push imm32` 立即数引用**恰好 1 处**（纯显示路径，非 strcmp 查找键）
  · 目标槽位长度 >= GBK 译文长度 + 1（NUL）
  · 不含 printf 格式符（含格式符的另立一批，见脚本内 NOTE）

⚠️ 对象与一作不同：本脚本改 D:\\OpenGeneral\\OpenGen.exe（25.02.26.0）；
   `unitpanel_patch.py` / `unitdlg_patch.py` / `maphud_patch.py` 改的是
   D:\\OpenPG2\\OpenGen.exe（26.03.30.0）—— 偏移不可照搬，本表数据全部现扫得到。

用法:
  python og_p1_ui_patch.py            # 干跑（默认，只报告不写盘）
  python og_p1_ui_patch.py --apply    # 正式写入（临时件 → 回读校验 → 才换名）
  python og_p1_ui_patch.py --verify   # 只读：报告每条串当前处于哪一态

回滚: 把 backup\\OpenGen.exe.before-p1 拷回 D:\\OpenGeneral\\OpenGen.exe
      （更彻底地回到出厂态：用 backup\\OpenGen.exe.before-p0）
"""
import hashlib
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib

EXE = r"D:\OpenGeneral\OpenGen.exe"
BAK = r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p1"
EXPECT_SIZE = 6310400
# 本批开工前的指纹 ＝ P0 落盘后的状态（防版本漂移 / 防改错对象）
EXPECT_MD5_PREFIX = "4841a46d7bee"

# (虚拟地址, 原文, 译文, 预期槽位)
#
# NOTE 未纳入本批：
#   · 含 printf 格式符的串（`%s * Mode: %d x %d x %d bpp (Click to show Credits)`、
#     `   File: %s   [%d scenarios]`、`Frozen/Mud ground condition supply: %+d%%`
#     —— 另立 P2，须逐字保留格式符并机检个数一致）
#   · `Toggles terrain labels` 等（push 引用 = 0，走指针表/资源，需先探承载方式）
#   · `Change to` / `Tables` / `Disable Campaigns Dialog at start` /
#     `Hide windows' task bar` / `Files in folder` / `CREDITS` / `DISCLAIMER`
#     （ASCII 扫描找不到 ⇒ 在 `.rsrc` 的 UTF-16 对话框模板里，另一套机制）
TABLE = [
    # --- 底栏悬停提示 ---
    (0x009114B0, "Campaigns' catalog", "战役目录", 20),
    (0x009115EC, "Campaigns' catalog", "战役目录", 20),
    # --- 关卡详情面板底部 ---
    (0x009180A0, "OG Mode", "OG 模式", 8),
    # --- 单位面板：运动力表头（4 份副本） ---
    (0x008F5034, "dry - ice - mud - terrain", "干燥 - 结冰 - 泥泞 - 地形", 28),
    (0x00913790, "dry - ice - mud - terrain", "干燥 - 结冰 - 泥泞 - 地形", 28),
    (0x00914310, "dry - ice - mud - terrain", "干燥 - 结冰 - 泥泞 - 地形", 28),
    (0x00914DB8, "dry - ice - mud - terrain", "干燥 - 结冰 - 泥泞 - 地形", 28),
    # --- 单位面板：铁路运输（RTP）同族 5 条 ---
    (0x008F2B28, "No RTP pool", "无 RTP 池", 12),
    (0x008F2B00, "Can't use RTP", "无法使用 RTP", 16),
    (0x008F2B34, "No RTP available in pool", "运输池中无 RTP", 28),
    (0x008F2B50, "No RTP matching front/weight", "无匹配阵营/重量的 RTP", 32),
    (0x008F2BA0, "Can use: RTP", "可用: RTP", 16),
    # --- 天气 / 地面状况提示 ---
    (0x008FA550, "Weather can change ground condition", "天气会改变地面状况", 36),
    (0x008F4ED8, "Ground condition changed! ... ", "地面状况已改变! ... ", 32),
    # --- 设置对话框（.rdata 里的字面量那一部分） ---
    (0x00907B04, "No file loaded", "未载入文件", 16),
    (0x008FBC98, "Keep current", "保持当前", 16),
    (0x00888B80, "Normal", "普通", 8),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def regions(p):
    """把 TABLE 解析成 [(fo, va, slot, src, dst)]，并校验内部一致性。"""
    out = []
    for va, src, dst, slot in TABLE:
        fo, sec = p.rva2fo(va - 0x400000)
        if fo is None:
            raise SystemExit("❌ VA 0x%08X 无法映射到文件偏移" % va)
        out.append((fo, va, slot, src, dst))
    out.sort()
    for a, b in zip(out, out[1:]):
        if a[0] + a[2] > b[0]:
            raise SystemExit("❌ 槽位重叠：VA 0x%08X 与 0x%08X" % (a[1], b[1]))
    return out


def region_state(d, fo, slot, src, dst):
    seg = d[fo:fo + slot]
    if seg[:len(src) + 1] == src.encode("ascii") + b"\x00":
        return "orig"
    z = seg.find(b"\x00")
    if z > 0:
        try:
            if seg[:z].decode("gbk") == dst:
                return "patched"
        except UnicodeDecodeError:
            pass
        return "unknown"
    return "unknown"


def build(d, regs, p, verbose=True):
    rep = []
    new = bytearray(d)
    slots = []
    for fo, va, slot, src, dst in regs:
        dstb = dst.encode("gbk")
        need = len(dstb) + 1
        if need > slot:
            raise SystemExit("❌ VA 0x%08X 译文 %d B > 槽位 %d B（%r）"
                             % (va, need, slot, dst))
        # 开工前：原文必须在位（幂等由调用方保证）
        if region_state(d, fo, slot, src, dst) != "orig":
            raise SystemExit("❌ VA 0x%08X 槽位不是原文态，拒绝写入" % va)
        # 引用自证：该 VA 的 push imm32 必须恰好 1 处
        pat = struct.pack("<I", va)
        npush = d.count(b"\x68" + pat)
        if npush != 1:
            raise SystemExit("❌ VA 0x%08X 的 push 引用数 = %d（要求 1）" % (va, npush))
        new[fo:fo + slot] = dstb + b"\x00" + b"\x00" * (slot - need)
        slots.append((fo, va, slot, dst))
        if verbose:
            rep.append("  VA 0x%08X  FO 0x%06X  %-38r → %-20r  GBK %2dB/槽 %2dB  push=1"
                       % (va, fo, src, dst, len(dstb) + 1, slot))
    new = bytes(new)

    # ---- 自证 1：文件大小不变 ----
    if len(new) != len(d):
        raise SystemExit("❌ 文件大小改变")
    rep.append("✅ 文件大小不变：%d B" % len(new))

    # ---- 自证 2：逐字节差异必须完全落在槽位并集内 ----
    diffs = [i for i in range(len(d)) if d[i] != new[i]]
    if not diffs:
        raise SystemExit("❌ 无任何差异")
    allow = set()
    for fo, va, slot, dst in slots:
        allow.update(range(fo, fo + slot))
    stray = [i for i in diffs if i not in allow]
    if stray:
        raise SystemExit("❌ 有 %d 处差异越出槽位，首处 FO 0x%X" % (len(stray), stray[0]))
    rep.append("✅ 逐字节审计：差异 %d 处，全部落在 %d 个槽位内（越界 0 处）"
               % (len(diffs), len(slots)))

    # ---- 自证 3：`.text` 零差异 ----
    tsec = [s for s in p.sections if s[0] == ".text"][0]
    tlo, thi = tsec[3], tsec[3] + tsec[4]
    ntext = sum(1 for i in diffs if tlo <= i < thi)
    if ntext:
        raise SystemExit("❌ `.text` 有 %d 处差异 —— 本补丁不应改代码" % ntext)
    rep.append("✅ `.text` (FO 0x%X..0x%X) 差异 **0** 字节（未碰代码）" % (tlo, thi))

    # ---- 自证 4：逐槽位 GBK 回读 + 槽外后继字节未动 ----
    # ⚠️ RTP 同族几条串在 .rdata 里**首尾相邻**（如 'No RTP pool' 槽尾正是
    #    'No RTP available in pool' 的起点）⇒ 槽后 8 B 检查必须**跳过落在本批其它
    #    槽位内的位置**，否则会把「有意写入的邻串」误报成越界改动。
    for fo, va, slot, dst in slots:
        z = new.index(b"\x00", fo)
        back = new[fo:z].decode("gbk")
        if back != dst:
            raise SystemExit("❌ VA 0x%08X GBK 回读不符：%r" % (va, back))
        for k in range(8):
            pos = fo + slot + k
            if pos in allow:
                continue
            if new[pos] != d[pos]:
                raise SystemExit("❌ VA 0x%08X 槽位之后（非本批槽位）FO 0x%X 被改动"
                                 % (va, pos))
    rep.append("✅ %d 个槽位 GBK 回读全部一致，槽外后继字节逐字节未动" % len(slots))

    # ---- 自证 5：所有引用指令（push imm32）原样保留 ----
    for fo, va, slot, dst in slots:
        pat = struct.pack("<I", va)
        if new.count(b"\x68" + pat) != 1:
            raise SystemExit("❌ VA 0x%08X 的 push 引用在写入后丢失/变化" % va)
    rep.append("✅ %d 个 push imm32 引用指令全部原样保留" % len(slots))
    return new, rep


def main():
    apply_ = "--apply" in sys.argv
    verify_ = "--verify" in sys.argv
    if not os.path.exists(EXE):
        raise SystemExit("❌ 找不到 %s" % EXE)
    d = open(EXE, "rb").read()
    p = pelib.PE(d)
    regs = regions(p)
    print("EXE  %s" % EXE)
    print("      %d B  md5 %s" % (len(d), md5(d)))
    print("本批 %d 个槽位 / %d 条不同文案"
          % (len(regs), len(set(r[3] for r in regs))))
    print("-" * 108)

    states = [(r, region_state(d, r[0], r[2], r[3], r[4])) for r in regs]
    for (fo, va, slot, src, dst), st in states:
        tag = {"orig": "原文", "patched": "已汉化", "unknown": "❗未知"}[st]
        print("  [%-4s] VA 0x%08X  FO 0x%06X  %-38r → %r"
              % (tag, va, fo, src, dst))
    n_orig = sum(1 for _, s in states if s == "orig")
    n_pat = sum(1 for _, s in states if s == "patched")
    n_unk = sum(1 for _, s in states if s == "unknown")
    print("-" * 108)
    print("状态汇总：原文 %d / 已汉化 %d / 未知 %d" % (n_orig, n_pat, n_unk))
    if verify_:
        return
    if n_unk:
        raise SystemExit("❌ 有未知态槽位，拒绝写入。请人工核对后再跑。")
    if n_orig == 0:
        print("\n✅ 全部已是汉化版，跳过（幂等）。无任何写入。")
        return
    if n_pat:
        raise SystemExit("❌ 部分已汉化部分未汉化 —— 中间态，拒绝写入（请先回滚到一致态）")

    if len(d) != EXPECT_SIZE:
        print("⚠ 文件大小 %d ≠ 预期 %d（版本漂移？）" % (len(d), EXPECT_SIZE))
    if not md5(d).startswith(EXPECT_MD5_PREFIX):
        print("⚠ md5 前缀不是 %s —— 开工前状态与预期不符，请先核对！" % EXPECT_MD5_PREFIX)

    new, rep = build(d, regs, p)
    print("\n译文表：")
    for r in rep:
        print(r)

    if not apply_:
        print("\n[干跑] 未写盘。确认以上自证后加 --apply 落盘。")
        return

    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if os.path.exists(BAK):
        print("\n备份已存在，不覆盖：%s  md5 %s" % (BAK, md5(open(BAK, "rb").read())))
    else:
        shutil.copy2(EXE, BAK)
        print("\n备份：%s  md5 %s" % (BAK, md5(open(BAK, "rb").read())))

    # 硬纪律①：先写临时件 → 回读校验 → 才换名
    tmp = EXE + ".p1.tmp"
    with open(tmp, "wb") as f:
        f.write(new)
    got = open(tmp, "rb").read()
    if got != new:
        os.remove(tmp)
        raise SystemExit("❌ 临时件回读不符，已删除，未动正式文件")
    print("临时件回读校验：✅ 逐字节一致")
    os.replace(tmp, EXE)
    fin = open(EXE, "rb").read()
    if fin != new:
        raise SystemExit("❌ 落盘后回读不符！请立刻从备份还原：%s" % BAK)
    print("落盘后回读校验：✅ 逐字节一致")
    print("\n完成：%s  %d B  md5 %s" % (EXE, len(fin), md5(fin)))
    print("回滚：copy '%s' '%s'" % (BAK, EXE))


if __name__ == "__main__":
    main()
