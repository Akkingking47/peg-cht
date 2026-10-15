#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""装备名「图标码反查」—— 见 MECHANICS.md §23

链路：equip.txt 行 N → equip.xeqp 记录 N-1 → 图标槽(相对 +72/80/88/96)
      → 假码 → OpenIcons.keep(假码;真码) → OpenIcons.csv 的 Description/IconClass/Nation

用途：efile 的 equip.txt 出现罗马字外语名/生造名而全库无文档可查时，
      把条目**至少归到确定的功能类别**，少数情况可直接读出词义。

⚠️ 图标是「最接近可用」而非精确对应 ⇒ 只能给**类别**，不能当词义。

用法：
    python probe_equip_icons.py COMWW2                 # 抽样 30 条
    python probe_equip_icons.py COMWW2 --lines 640-670  # 指定行段
    python probe_equip_icons.py COMWW2 --grep Keishu    # 按名搜
    python probe_equip_icons.py COMWW2 --todo _todo_uncertain.txt
"""
import io
import os
import struct
import sys

GAME = r"D:\OpenPG2"
REC_LEN = 120          # 记录长度（COMWW2 实测：4B 头 + 4054×120B）
SLOT_OFF = 72          # 记录内图标槽起始相对偏移
SLOT_N = 4             # 槽数


def load_icons(path_csv, path_keep):
    """真码表 + 假码→真码 回落表。"""
    real = {}
    with io.open(path_csv, encoding="cp1252", errors="replace") as f:
        for ln in f:
            if ln.lstrip().startswith("*") or ";" not in ln:
                continue
            c = ln.rstrip("\r\n").split(";")
            if len(c) >= 5 and c[0].strip():
                real[c[0].strip()] = (c[1].strip(), c[3].strip(), c[4].strip())
    keep = {}
    if os.path.exists(path_keep):
        with io.open(path_keep, encoding="cp1252", errors="replace") as f:
            for ln in f:
                if ln.lstrip().startswith("*") or ";" not in ln:
                    continue
                c = ln.rstrip("\r\n").split(";")
                if len(c) >= 2 and c[0].strip() and c[1].strip():
                    keep[c[0].strip()] = c[1].strip()
    return real, keep


def parse_xeqp(path):
    """返回 [ [槽0码, 槽1码, 槽2码, 槽3码], ... ]；记录数由头部 u16[1] 给出。"""
    b = open(path, "rb").read()
    n = struct.unpack("<H", b[2:4])[0]
    rec_len = (len(b) - 4) // n
    out = []
    for i in range(n):
        o = 4 + i * rec_len
        s = b[o + SLOT_OFF: o + SLOT_OFF + 8 * SLOT_N].decode("latin1")
        out.append([s[8 * k: 8 * k + 8].rstrip("\x00") for k in range(SLOT_N)])
    return out, sorted(set([rec_len, REC_LEN]))[0]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    ef = sys.argv[1]
    root = os.path.join(GAME, "EFILE_" + ef if not ef.upper().startswith("EFILE_") else ef)
    if not os.path.isdir(root):
        raise SystemExit("找不到 efile 目录: %s" % root)
    src_p = os.path.join(root, "equip.txt")
    xeqp_p = os.path.join(root, "equip.xeqp")
    for p in (src_p, xeqp_p):
        if not os.path.exists(p):
            raise SystemExit("缺文件: %s" % p)

    src = io.open(src_p, encoding="cp1252", errors="replace").read().replace("\r\n", "\n").split("\n")
    recs, rec_len = parse_xeqp(xeqp_p)
    real, keep = load_icons(os.path.join(GAME, "OpenIcons.csv"),
                            os.path.join(GAME, "OpenIcons.keep"))
    print("# efile=%s  equip.txt %d 行 | xeqp %d 记录 × %dB | 图标表 %d | keep %d"
          % (ef, len(src), len(recs), rec_len, len(real), len(keep)))
    print("# ⚠️ 图标=最接近可用 ⇒ 只能给类别，不能当词义")

    # 选择要看的行
    sel = []
    args = sys.argv[2:]
    if "--grep" in args:
        k = args[args.index("--grep") + 1]
        sel = [i + 1 for i, l in enumerate(src) if k.lower() in l.lower()]
    elif "--lines" in args:
        a, b = args[args.index("--lines") + 1].split("-")
        sel = list(range(int(a), int(b) + 1))
    elif "--todo" in args:
        p = args[args.index("--todo") + 1]
        names = set()
        with io.open(p, encoding="utf-8") as f:
            for ln in f:
                s = ln.rstrip("\r\n")
                if s and not s.startswith("#"):
                    names.add(s.split("\t")[0].strip())
        sel = [i + 1 for i, l in enumerate(src) if l.strip() in names]
    else:
        sel = [i + 1 for i, l in enumerate(src) if l.strip() and i % max(1, len(src) // 30) == 0]

    print("%-6s %-24s %-7s %-7s %-46s %-22s %s" % ("行", "原文", "假码", "真码", "描述", "图标类", "国籍"))
    print("-" * 140)
    miss = 0
    for L in sel:
        i = L - 1
        if i < 0 or i >= len(recs):
            continue
        c = recs[i][0]
        rc = keep.get(c, c)
        d = real.get(rc)
        if d:
            print("%-6d %-24s %-7s %-7s %-46s %-22s %s"
                  % (L, src[i].strip()[:24], c, rc, d[0][:46], d[1][:22], d[2][:26]))
        else:
            miss += 1
            print("%-6d %-24s %-7s %-7s %-46s %-22s %s"
                  % (L, src[i].strip()[:24], c, rc, "(真码也不在表)", "", ""))
    print("-" * 140)
    print("# 共 %d 行；无解 %d 行" % (len(sel), miss))
    return 0


if __name__ == "__main__":
    sys.exit(main())
