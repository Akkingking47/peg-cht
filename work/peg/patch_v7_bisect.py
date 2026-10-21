# -*- coding: utf-8 -*-
"""patch_v7_bisect.py —— 从 v5c（干净基线）出发，只位移指定的 dx 记录组，二分花屏责任。

背景：v5c（＝母本 + .text 52 + .data 44（除 dx）+ 代码 10 处）画面正确；
v4/v5a（＝v5c 再叠上 163 个 dx 站点 = 82 条右列记录的 x/right）花屏。
v5d 证明「组0」（0x490494 那 7 条 = 点击命中区）位移后画面不变。
剩下 11 组仍未归因，本脚本用来一组组地叠到 v5c 上。

dx 记录组（由 work\\peg\\out\\res_diff_v4.tsv 的 dx 站点聚类而来）：
    组0  0x490494 (14 站点)  已证＝命中区，不受影响
    组2  0x494220 (28)   组3  0x4949C8 (26)   组4  0x4A2068 (14)
    组5  0x4A21B0 (12)   组6  0x4A22F8 (26)   组10 0x4A8648 (30)
    组1  0x493B4C (2)    组7  0x4A24F4 (1)    组8  0x4A2560 (4)
    组9  0x4A6064 (4)    组11 0x4A9658 (2)

用法：
    python patch_v7_bisect.py --groups 6 --name v7a
    python patch_v7_bisect.py --groups 4,5 --name v7b --apply
"""
import csv
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


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
GAMEDIR = GAME_ALT
TSV = os.path.join(OUT, "res_diff_v4.tsv")
SRC = os.path.join(OUT, "v5c.exe")
SRC_MD5 = "4657e47d9170aebf586fc52730e0a1f8"

# 组号 -> 该组 dx 站点的文件偏移范围（由聚类结果换算：FO = VA - 0x48E000 + 0x8B800）
GROUP_RANGES = {
    0: (0x490494, 0x490574),
    1: (0x493B4C, 0x493B54),
    2: (0x494220, 0x4943FC),
    3: (0x4949C8, 0x494B80),
    4: (0x4A2068, 0x4A2148),
    5: (0x4A21B0, 0x4A2290),
    6: (0x4A22F8, 0x4A24B0),
    7: (0x4A24F4, 0x4A24F8),
    8: (0x4A2560, 0x4A258C),
    9: (0x4A6064, 0x4A6090),
    10: (0x4A8648, 0x4A8848),
    11: (0x4A9658, 0x4A9660),
}

CN_CHECKS = [
    ("charset", 0x070CE3, bytes.fromhex("6a86")),
    ("__mbcodepage", 0x0A948C, bytes.fromhex("a803")),
    ("LCID", 0x07BE86, bytes.fromhex("b804080000")),
]


def load_sites(groups):
    sites = []
    with open(TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["tag"] != "dx":
                continue
            va = int(row["va"], 16)
            for g in groups:
                lo, hi = GROUP_RANGES[g]
                if lo <= va <= hi:
                    sites.append((g, va, int(row["file_off"], 16), int(row["old"]), int(row["new"])))
                    break
    return sites


def main():
    args = sys.argv[1:]
    groups = [int(x) for x in args[args.index("--groups") + 1].split(",")]
    name = args[args.index("--name") + 1]
    apply = "--apply" in args
    sites = load_sites(groups)
    d = bytearray(open(SRC, "rb").read())
    got = hashlib.md5(bytes(d)).hexdigest()
    print("基点 v5c md5 %s（期望 %s）%s" % (got, SRC_MD5, "OK" if got == SRC_MD5 else "**不符**"))
    if got != SRC_MD5:
        return
    print("组 %s 共 %d 个站点" % (groups, len(sites)))
    bad = 0
    for g, va, fo, old, new in sites:
        cur = int.from_bytes(d[fo:fo + 2], "little")
        if cur == new:
            print("  组%-2d VA 0x%06X 已是 %d（幂等）" % (g, va, new))
            continue
        if cur != old:
            print("  组%-2d VA 0x%06X 期望 %d 实际 %d **不匹配**" % (g, va, old, cur))
            bad += 1
            continue
        print("  组%-2d VA 0x%06X FO 0x%06X %d -> %d" % (g, va, fo, old, new))
        if apply:
            d[fo:fo + 2] = new.to_bytes(2, "little")
    if bad or not apply:
        print("[%s] 未写文件（bad=%d apply=%s）" % (name, bad, apply))
        return
    for label, fo, want in CN_CHECKS:
        cur = bytes(d[fo:fo + len(want)])
        assert cur == want, "中文补丁被破坏 %s" % label
    assert len(d) == 734720
    dst = os.path.join(OUT, name + ".exe")
    with open(dst + ".tmp", "wb") as f:
        f.write(bytes(d))
    os.replace(dst + ".tmp", dst)
    print("写出 %s  md5 %s" % (dst, hashlib.md5(bytes(d)).hexdigest()))
    shutil.copy2(dst, os.path.join(GAMEDIR, "PeG030-%s.exe" % name))
    print("复制到 %s" % os.path.join(GAMEDIR, "PeG030-%s.exe" % name))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
