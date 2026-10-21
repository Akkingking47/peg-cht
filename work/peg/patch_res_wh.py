# -*- coding: utf-8 -*-
"""按任意分辨率生成 PeG030 高分辨率产物（默认走 v5c 配方：只改"尺寸类"站点，不动控件记录位移）

前情：
  - 母本 = D:\\Program Files\\PeG\\PeG030.exe（中文版，md5 c462e897b3aa1c384870c857ce9e01df）
  - 站点表 = work\\peg\\out\\res_diff_v4.tsv（S1 从"母本 ↔ v4 产物"逐字节 diff 反推的 259 条，
    列：index/section/va/file_off/width/old/new/tag/note；va 是**立即数地址**不是指令地址）
  - 语义标签：w/w-1/w-4 → 新宽度；h/h-1/h-28/h-30 → 新高度；
    dx/dy → 旧值 + (新宽-800) / (新高-600)（控件记录的位移）
  - v5c 配方 = 母本 + 52 条 .text 尺寸站点 + 44 条非 dx 的 .data 尺寸站点 + 10 处代码侧尺寸
    实机结论：地图铺满新分辨率、界面元件形状/命中与原版一致，只是控件仍在 800x600 的老坐标上。
    若加 --keep-dx（= v4 配方），工具列会被横向拉伸（已实测），默认不做。

用法：
  python patch_res_wh.py --w 1920 --h 1080 --out out\\PeG030-1920x1080.exe            # 干跑
  python patch_res_wh.py --w 1920 --h 1080 --out out\\PeG030-1920x1080.exe --apply    # 写盘
纪律：母本 md5 必须匹配；逐站点内容断言（当前值必须等于记录旧值）；先改内存→回读校验→
      os.replace 落盘；落盘后复核中文补丁三处（charset / __mbcodepage / LCID）。
"""
import argparse
import hashlib
import os
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
TSV = os.path.join(OUT, "res_diff_v4.tsv")

SRC = os.path.join(GAME, "PeG030.exe")
SRC_MD5 = "c462e897b3aa1c384870c857ce9e01df"

# ---- 代码侧尺寸补丁（imm32 地址，已用 show_bytes.py 逐个核对过）----
# (imm32 VA, 旧值, 语义)
CODE_EDITS = [
    (0x41C4D7, 0x23B, "h-28", "面板矩形 bottom 571 -> h-28"),
    (0x41C4DE, 0x31F, "w-1", "面板矩形 right  799 -> w-1"),
    (0x44C5CD, 0x23A, "h-30", "屏幕边框 push 570 -> h-30"),
    (0x44C5D2, 0x31C, "w-4", "屏幕边框 push 796 -> w-4"),
    (0x44C731, 0x320, "w", "视口裁剪组1 mov eax, 800"),
    (0x44C778, 0x258, "h", "视口裁剪组1 mov edx, 600"),
    (0x44C86A, 0x320, "w", "视口裁剪组2 mov edx, 800"),
    (0x44C8B1, 0x258, "h", "视口裁剪组2 mov ecx, 600"),
    (0x44CC68, 0x320, "w", "视口裁剪组3 mov edx, 800"),
    (0x44CCAF, 0x258, "h", "视口裁剪组3 mov ecx, 600"),
]

CN_CHECKS = [
    (0x070CE3, bytes.fromhex("6a86"), "charset 0x86 GB2312"),
    (0x0A948C, bytes.fromhex("a803"), "__mbcodepage 936"),
    (0x07BE86, bytes.fromhex("b804080000"), "GetDateFormatA LCID 0x0804"),
]

SECS = [
    (".text", 0x401000, 0x400, 0x8A200),
    (".rdata", 0x48C000, 0x8A600, 0x1200),
    (".data", 0x48E000, 0x8B800, 0x21400),
    (".idata", 0x6AA000, 0xACC00, 0x5E00),
    (".rsrc", 0x6AC000, 0xAE200, 0x5600),
]

TAG_MEANING = {
    "w": "宽度", "w-1": "宽度-1", "w-4": "宽度-4",
    "h": "高度", "h-1": "高度-1", "h-28": "高度-28", "h-30": "高度-30",
    "dx": "控件横向位移", "dy": "控件纵向位移",
}


def va_to_fo(va):
    for _name, sva, raw, size in SECS:
        if sva <= va < sva + size:
            return raw + (va - sva)
    raise ValueError("VA %#x 不在任何已知节内" % va)


def rd(data, fo, width):
    return struct.unpack_from("<H" if width == 2 else "<I", data, fo)[0]


def new_value(tag, old, w, h):
    if tag == "w":
        return w
    if tag == "w-1":
        return w - 1
    if tag == "w-4":
        return w - 4
    if tag == "h":
        return h
    if tag == "h-1":
        return h - 1
    if tag == "h-28":
        return h - 28
    if tag == "h-30":
        return h - 30
    if tag == "dx":
        return old + (w - 800)
    if tag == "dy":
        return old + (h - 600)
    raise ValueError("未知标签 %r" % tag)


def load_tsv():
    rows = []
    with open(TSV, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        for line in f:
            if not line.strip():
                continue
            rec = dict(zip(head, line.rstrip("\n").split("\t")))
            rows.append({
                "section": rec["section"],
                "va": int(rec["va"], 16),
                "fo": int(rec["file_off"], 16),
                "width": int(rec["width"]),
                "old": int(rec["old"]),
                "tag": rec["tag"],
                "note": rec["note"],
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, required=True)
    ap.add_argument("--h", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-dx", action="store_true",
                    help="同时做控件记录横向位移（v4 配方，已知会让工具列拉伸）")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    w, h = args.w, args.h
    if w < 800 or h < 600:
        print("拒绝：只有 w>=800 且 h>=600 才成立（右移/下拉假设），收到 %dx%d" % (w, h))
        return 2

    base = open(SRC, "rb").read()
    md5 = hashlib.md5(base).hexdigest()
    print("母本 %s\n  %d 字节  md5 %s" % (SRC, len(base), md5))
    if md5 != SRC_MD5:
        print("母本 md5 不符：期望 %s —— 中止，未做任何修改。" % SRC_MD5)
        return 2

    data = bytearray(base)
    plan = []          # (fo, width, old, new, label)
    skipped_dx = 0
    for r in load_tsv():
        if r["tag"] == "dx" and not args.keep_dx:
            skipped_dx += 1
            continue
        plan.append((r["fo"], r["width"], r["old"],
                     new_value(r["tag"], r["old"], w, h),
                     "%s %s %s" % (r["section"], r["tag"], r["note"][:44])))
    for va, old, tag, note in CODE_EDITS:
        plan.append((va_to_fo(va), 4, old, new_value(tag, old, w, h),
                     ".text 代码侧 %s  %s" % (tag, note)))
    print("目标 %dx%d：站点 %d 条（%s dx 位移 %d 条）"
          % (w, h, len(plan), "含" if args.keep_dx else "跳过", skipped_dx))

    # ---- 逐站点内容断言 ----
    bad = []
    for i, (fo, width, old, new, label) in enumerate(plan):
        cur = rd(data, fo, width)
        if cur != old:
            bad.append((i, fo, old, cur, label))
    if bad:
        print("\n---- 内容断言失败 %d 条（整体拒绝，未做任何修改）----" % len(bad))
        for i, fo, old, cur, label in bad[:20]:
            print("  [%3d] 0x%08X 期望 %d 实际 %d  %s" % (i, fo, old, cur, label))
        return 3
    print("内容断言：全部 %d 条通过" % len(plan))

    # ---- 改内存 ----
    for fo, width, old, new, label in plan:
        struct.pack_into("<H" if width == 2 else "<I", data, fo, new)

    # ---- 回读校验 ----
    for fo, width, old, new, label in plan:
        if rd(data, fo, width) != new:
            print("回读失败 @0x%08X" % fo)
            return 4
    print("回读校验：全部 %d 条已就位" % len(plan))

    # ---- 中文补丁复核 ----
    for fo, want, label in CN_CHECKS:
        got = bytes(data[fo:fo + len(want)])
        print("  中文补丁 %-26s %s %s" % (label, got.hex(" "), "OK" if got == want else "FAIL"))
        if got != want:
            return 5

    # ---- 规模与差异统计 ----
    diffs = [i for i in range(len(base)) if base[i] != data[i]]
    runs = 0
    prev = -9
    for i in diffs:
        if i != prev + 1:
            runs += 1
        prev = i
    tags = {}
    for fo, width, old, new, label in plan:
        key = label.split()[1]
        tags[key] = tags.get(key, 0) + 1
    print("与母本差异：%d 字节 / %d 段   站点标签分布：%s"
          % (len(diffs), runs, dict(sorted(tags.items()))))
    out_md5 = hashlib.md5(bytes(data)).hexdigest()
    print("输出 md5：%s" % out_md5)

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
        assert rd(chk, fo, width) == new, "落盘回读失败 @0x%08X" % fo
    os.replace(tmp, out)
    print("已写出：%s（%d 字节，md5 %s）" % (out, os.path.getsize(out), out_md5))
    return 0


if __name__ == "__main__":
    sys.exit(main())
