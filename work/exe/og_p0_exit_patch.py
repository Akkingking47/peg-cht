# -*- coding: utf-8 -*-
"""OpenGeneral（波兰发行版）OpenGen.exe —— P0 可行性 POC：退出确认框串汉化。

⚠️ 本脚本的对象与既有 4 个 exe 补丁**不同**：
   `unitpanel_patch.py` / `unitdlg_patch.py` / `maphud_patch.py` / `exe_zhfix.py`
   改的是一作 `D:\\OpenPG2\\OpenGen.exe`（26.03.30.0）。
   本脚本改的是二作 `D:\\OpenGeneral\\OpenGen.exe`（**25.02.26.0**，比 PG2 小 5,632 B，
   偏移**不能照搬**，本节数据全部在本 exe 上现扫得到）。

对象 EXE : D:\\OpenGeneral\\OpenGen.exe   ver 25.02.26.0 · 6,310,400 B
           · md5 前缀 5b0eb96efa（原始态）
目标串   : FO 0x50DDF4 / VA 0x0090EDF4   'Do you really want to exit ? ... '（33 B）
引用点   : 全 exe 内该 VA 立即数**仅 1 处** —— 指令 FO 0x3F94C3 / VA 0x007FA0C3，
           前导字节 0x68 ⇒ `push imm32`（纯显示路径，**不是** strcmp 查找键）
槽位     : 原文 NUL 之后另有 2 个 0x00，下一串 'LAST COMBAT ' 起于 FO+36
           ⇒ 可用 **36 B**；译文 GBK 21 B + NUL = 22 B ⇒ **原地等长替换**

为什么这条路比既有补丁更安全：
  · 不需要 `.rdata`/`.data` 空洞，**不需要改任何指针** ⇒ 没有「把
    IMAGE_LOAD_CONFIG_DIRECTORY 当空洞写坏」那类风险（见 pelib.py 头部血泪教训）
  · **完全不碰 `.text`** ⇒ 不可能破坏控制流
  · 文件大小不变，除这 36 B 外逐字节不动（脚本会逐字节审计证明这一点）

用法:
  python og_p0_exit_patch.py            # 干跑（默认，只报告不写盘）
  python og_p0_exit_patch.py --apply    # 正式写入（先写临时件 → 回读校验 → 才换名）
  python og_p0_exit_patch.py --verify   # 只读：报告当前 exe 处于哪一态

回滚: 把 backup\\OpenGen.exe.before-p0 拷回 D:\\OpenGeneral\\OpenGen.exe 即可。
"""
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pelib

EXE = r"D:\OpenGeneral\OpenGen.exe"
BAK = r"D:\DSH\军事游戏汉化\backup\OpenGen.exe.before-p0"
EXPECT_SIZE = 6310400
EXPECT_MD5_PREFIX = "5b0eb96efa"        # 原始态指纹（防版本漂移 / 防改错对象）

FO = 0x50DDF4                           # 目标串起始文件偏移
VA = 0x0090EDF4
SLOT = 36                               # FO 起可用字节（到下一串 'LAST COMBAT ' 为止）
REF_INSN_FO = 0x3F94C3                  # 唯一引用指令（push imm32）
REF_INSN_VA = 0x007FA0C3

SRC = "Do you really want to exit ? ... "
DST = "你真的想退出吗 ? ... "


def md5(b):
    return hashlib.md5(b).hexdigest()


def state(d):
    """返回 ('orig'|'patched'|'unknown', 说明)。"""
    seg = d[FO:FO + SLOT]
    if seg[:len(SRC) + 1] == SRC.encode("ascii") + b"\x00":
        return "orig", "原文英文在位"
    zero = seg.find(b"\x00")
    if zero > 0:
        try:
            txt = seg[:zero].decode("gbk")
        except UnicodeDecodeError:
            return "unknown", "槽位既非原文也非合法 GBK"
        if txt == DST:
            return "patched", "已是汉化版：%r" % txt
        return "unknown", "槽位是别的 GBK 文本：%r" % txt
    return "unknown", "槽位无 NUL 终结"


def build_patched(d):
    """构造新内容并自证，返回 (newbytes, 报告行列表)。"""
    rep = []
    dst_gbk = DST.encode("gbk")
    need = len(dst_gbk) + 1
    if need > SLOT:
        raise SystemExit("❌ 译文 %d B > 槽位 %d B" % (need, SLOT))
    new = bytearray(d)
    seg = dst_gbk + b"\x00" + b"\x00" * (SLOT - need)
    new[FO:FO + SLOT] = seg
    new = bytes(new)

    # ---- 自证 1：文件大小不变 ----
    if len(new) != len(d):
        raise SystemExit("❌ 文件大小改变")
    rep.append("✅ 文件大小不变：%d B" % len(new))

    # ---- 自证 2：逐字节审计，差异必须完全落在槽位内，且 .text 零差异 ----
    diffs = [i for i in range(len(d)) if d[i] != new[i]]
    if not diffs:
        raise SystemExit("❌ 无任何差异")
    lo, hi = diffs[0], diffs[-1] + 1
    if lo < FO or hi > FO + SLOT:
        raise SystemExit("❌ 差异 0x%X..0x%X 越出槽位 0x%X..0x%X"
                         % (lo, hi, FO, FO + SLOT))
    rep.append("✅ 逐字节审计：差异 %d 处，全部落在槽位内 0x%06X..0x%06X"
               % (len(diffs), lo, hi))
    rep.append("   （槽位尾 %d B 原文本就是 0x00，故不产生差异 —— 非异常）"
               % (FO + SLOT - hi))
    tsec = [s for s in pelib.PE(d).sections if s[0] == ".text"][0]
    tlo, thi = tsec[3], tsec[3] + tsec[4]
    ntext = sum(1 for i in diffs if tlo <= i < thi)
    if ntext:
        raise SystemExit("❌ `.text` 有 %d 处差异 —— 本补丁不应改代码" % ntext)
    rep.append("✅ `.text` (FO 0x%X..0x%X) 差异 **0** 字节（未碰代码）" % (tlo, thi))

    # ---- 自证 3：GBK 回读 ----
    z = new.index(b"\x00", FO)
    back = new[FO:z].decode("gbk")
    if back != DST:
        raise SystemExit("❌ GBK 回读不符：%r" % back)
    rep.append("✅ GBK 回读：FO 0x%06X = %r（%d B + NUL）" % (FO, back, z - FO))

    # ---- 自证 4：下一串未被动到 ----
    nxt = new[FO + SLOT:FO + SLOT + 12]
    if not nxt.startswith(b"LAST COMBAT"):
        raise SystemExit("❌ 槽位之后不再以 'LAST COMBAT' 起头：%r" % nxt)
    rep.append("✅ 下一串完好：FO 0x%06X 起 %r" % (FO + SLOT, nxt))

    # ---- 自证 5：唯一引用指令的立即数仍指向本串 ----
    insn = new[REF_INSN_FO:REF_INSN_FO + 5]
    if insn[0] != 0x68 or insn[1:] != VA.to_bytes(4, "little"):
        raise SystemExit("❌ 引用指令已被改动：%s" % insn.hex(" "))
    rep.append("✅ 引用指令未动：VA 0x%08X  %s  (push imm32 → 本串)"
               % (REF_INSN_VA, insn.hex(" ")))
    return new, rep


def main():
    apply_ = "--apply" in sys.argv
    verify_ = "--verify" in sys.argv
    if not os.path.exists(EXE):
        raise SystemExit("❌ 找不到 %s" % EXE)
    d = open(EXE, "rb").read()
    h = md5(d)
    print("EXE  %s" % EXE)
    print("      %d B  md5 %s" % (len(d), h))
    print("译文  %r → %r  (GBK %d B + NUL)" % (SRC, DST, len(DST.encode("gbk"))))
    print("槽位  FO 0x%06X / VA 0x%08X  可用 %d B" % (FO, VA, SLOT))
    print("引用  指令 FO 0x%06X / VA 0x%08X（全 exe 唯一）" % (REF_INSN_FO, REF_INSN_VA))
    print("-" * 74)

    st, why = state(d)
    print("当前状态：%s —— %s" % (st, why))

    if verify_:
        return

    if len(d) != EXPECT_SIZE:
        print("⚠ 文件大小 %d ≠ 预期 %d（版本漂移？）" % (len(d), EXPECT_SIZE))
    if st == "orig" and not h.startswith(EXPECT_MD5_PREFIX):
        print("⚠ md5 前缀不是 %s —— 目标 exe 可能不是预期版本，请先核对！" % EXPECT_MD5_PREFIX)

    if st == "patched":
        print("\n✅ 已是汉化版，跳过（幂等）。无任何写入。")
        return
    if st == "unknown":
        raise SystemExit("\n❌ 槽位状态未知，拒绝写入。请人工核对 FO 0x%06X。" % FO)

    new, rep = build_patched(d)
    print("\n干跑自证：")
    for r in rep:
        print("  " + r)

    if not apply_:
        print("\n[干跑] 未写盘。确认以上自证后加 --apply 落盘。")
        return

    # ---- 备份（已存在则不覆盖，保留最初原始件）----
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if os.path.exists(BAK):
        bh = md5(open(BAK, "rb").read())
        print("\n备份已存在，不覆盖：%s  md5 %s" % (BAK, bh))
    else:
        shutil.copy2(EXE, BAK)
        print("\n备份：%s  md5 %s" % (BAK, md5(open(BAK, "rb").read())))

    # ---- 硬纪律①：先写临时件 → 回读校验 → 才换名 ----
    tmp = EXE + ".p0.tmp"
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
