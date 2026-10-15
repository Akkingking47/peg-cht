#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段2.2：exe 双字节补丁（12 个 efile）。

纪律：
  · **从工作区备份读原文**（pegww2/testbed/backup/exe/），绝不从游戏目录读
  · 默认 **dry-run**，`--apply` 才落盘；**幂等**（已打则 no-op）
  · 参照系 = 已实机验证成功的 `PeG030.exe`（其 ② 区域字节直接沿用，保证与验证过的形态逐字节一致）
  · 落盘后**回读校验** + 报告差异 FO 清单

补丁（FO 制）：
  ① 0x70CE4            00 → 86            CreateFontA iCharSet = GB2312_CHARSET
  ② 0xA938A–0xA9489    _pctype 高字节区    → 取参照成品同区字节（0x8040 交替）
  ③ 0xA948C–0xA948D    01 00 → A8 03      __mbcodepage = 936
  ④ 0x7BE86–0x7BE89    A1 48 91 49 → B8 04 08 00   日期 LCID = zh-CN
（⑤ CRT lc_time 表：前作实测无效 ⇒ **本作不打**，见 docs/40 §三.2）

用法:
  python patch-mbcs-ww2.py            # dry-run（打印将要改的字节）
  python patch-mbcs-ww2.py --apply    # 落盘到 testbed/out/exe/
"""
import hashlib
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
SRC = os.path.join(WS, "pegww2", "testbed", "backup", "exe")
DST = os.path.join(WS, "pegww2", "testbed", "out", "exe")
REF_PATCHED = r"D:\Program Files\PeG\PeG030.exe"                 # 已实机成功的成品
REF_ORIG = r"D:\Program Files\PeG\PeG030.exe.orig-backup"        # 其原版
HERE = os.path.dirname(os.path.abspath(__file__))
_REPORT = os.path.join(WS, "pegww2", "research", "evidence", "patch-report.txt")

# (名称, 起点 FO, 长度)
P_PCTYPE = ("_pctype 高字节区", 0xA938A, 0x100)
P_OTHER = [
    ("iCharSet", 0x70CE4, bytes([0x86]), bytes([0x00])),
    ("__mbcodepage", 0xA948C, bytes([0xA8, 0x03]), bytes([0x01, 0x00])),
    ("date_LCID", 0x7BE86, bytes([0xB8, 0x04, 0x08, 0x00]), bytes([0xA1, 0x48, 0x91, 0x49])),
]
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def diffs(a, b):
    return [i for i in range(min(len(a), len(b))) if a[i] != b[i]]


def main():
    apply_ = "--apply" in sys.argv
    refp = open(REF_PATCHED, "rb").read()
    refo = open(REF_ORIG, "rb").read()
    # ② 区域直接取参照成品，并断言参照原版在该区与「原版 efile」一致
    pct_new = refp[P_PCTYPE[1]:P_PCTYPE[1] + P_PCTYPE[2]]
    pct_old = refo[P_PCTYPE[1]:P_PCTYPE[1] + P_PCTYPE[2]]
    print("=" * 92)
    print("参照系（已实机成功的 PeG030.exe）")
    print("=" * 92)
    print(f"  ② 新字节: {pct_new[:24].hex(' ')} …（{len(pct_new)} B）")
    print(f"  ② 旧字节: {pct_old[:24].hex(' ')} …（{len(set(pct_old))} 种取值）")

    exes = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".exe"))
    print(f"\n待处理 efile: {len(exes)} 个（源：{os.path.relpath(SRC, WS)}）")
    if apply_:
        os.makedirs(DST, exist_ok=True)

    print()
    print("=" * 92)
    print(f"{'efile':24s} {'状态':10s} {'①':4s} {'②':4s} {'③':4s} {'④':4s} 差异字节  产物")
    print("=" * 92)
    ok = 0
    for f in exes:
        src = os.path.join(SRC, f)
        d = bytearray(open(src, "rb").read())
        marks = {}
        already = True
        for nm, fo, new, old in P_OTHER:
            cur = bytes(d[fo:fo + len(new)])
            if cur == new:
                marks[nm] = "已打"
            elif cur == old:
                marks[nm] = "待打"
                already = False
            else:
                marks[nm] = "!!异常"
            d[fo:fo + len(new)] = new
        cur = bytes(d[P_PCTYPE[1]:P_PCTYPE[1] + P_PCTYPE[2]])
        if cur == pct_new:
            marks["_pctype"] = "已打"
        elif cur == pct_old:
            marks["_pctype"] = "待打"
            already = False
        else:
            marks["_pctype"] = "!!异常"
        d[P_PCTYPE[1]:P_PCTYPE[1] + P_PCTYPE[2]] = pct_new

        out = os.path.join(DST, f)
        ds = diffs(bytes(d), open(src, "rb").read())
        status = "已打(no-op)" if already else ("dry-run" if not apply_ else "已写入")
        if apply_ and not already:
            with open(out, "wb") as fh:
                fh.write(d)
            back = open(out, "rb").read()
            assert back == bytes(d), "回读校验失败"
            assert sha(out) != sha(src), "产物与源相同（异常）"
        if apply_:
            ok += 1
        print(f"{f:24s} {status:10s} {marks['iCharSet']:4s} {marks['_pctype']:4s} "
              f"{marks['__mbcodepage']:6s} {marks['date_LCID']:6s} {len(ds):<9d} "
              f"{os.path.relpath(out, WS) if apply_ else '-'}")

    print()
    print("=" * 92)
    print("校验：与参照成品的差异形态一致性")
    print("=" * 92)
    refdiff = diffs(refp, refo)
    print(f"  参照 PeG030（原版→成品）差异 {len(refdiff)} B，FO 段："
          f"{sorted(set((x // 16) * 16 for x in refdiff))[:12]} …")
    for f in exes[:1]:
        src = os.path.join(SRC, f)
        d = bytearray(open(src, "rb").read())
        for nm, fo, new, old in P_OTHER:
            d[fo:fo + len(new)] = new
        d[P_PCTYPE[1]:P_PCTYPE[1] + P_PCTYPE[2]] = pct_new
        dd = diffs(bytes(d), open(src, "rb").read())
        print(f"  本作 {f}：差异 {len(dd)} B；FO 区间 {dd[0]:#x}–{dd[-1]:#x}")
        print(f"    （参照同四段为 1+4+256+2 = 263 B；本作不含已作废的 ⑤ 与两条旧补丁）")

    if not apply_:
        print("\n[DRY-RUN] 未写任何文件。加 --apply 落盘。")
    else:
        print(f"\n[APPLIED] {ok} 个产物写入 {os.path.relpath(DST, WS)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
