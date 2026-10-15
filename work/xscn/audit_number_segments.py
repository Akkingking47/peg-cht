# -*- coding: utf-8 -*-
"""番号段校验：map 表里「纯数字段 → 非『第N』」的错位体检（全 efile）。

典型病例：BASEKORP `100 → 连`（纯数字 100 被当成罗马数字 C＝Company＝连），
连带 `100/25 → 连/第25`、`397/100 → 第397/连`、`I/100/50th Tk → 第1/连/第50坦克`。

判据：把 src / dst 按 `/` 分段，段数相同且同位置 src 段为纯数字 N 时，
      dst 段必须匹配 `第N…`（或本身就是 N，未译）。否则记为错位。
用法: python audit_number_segments.py [--fix]
"""
import io
import os
import re
import sys
import glob
import collections

sys.stdout.reconfigure(encoding="utf-8")
WORK = r"D:\DSH\军事游戏汉化\work"
MAPS = sorted(set(
    glob.glob(os.path.join(WORK, "*", "*xscn-map.tsv")) +
    glob.glob(os.path.join(WORK, "*", "*-map.tsv"))
))
MAPS = [p for p in MAPS if os.path.basename(p) != "comww2-xscn-map.tsv"]

NUM = re.compile(r"^\d+$")


def read_rows(p):
    rows = []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                rows.append(c)
    return rows


def bad_segments(s, d):
    """返回 [(seg_idx, num, got), ...]"""
    if "/" not in s:
        return []
    ps, pd = s.split("/"), d.split("/")
    if len(ps) != len(pd):
        return []
    out = []
    for i, (a, b) in enumerate(zip(ps, pd)):
        a = a.strip()
        if not NUM.match(a):
            continue
        b = b.strip()
        if b == a:                      # 未译（原样保留）
            continue
        if re.match(r"^第" + a + r"(?![0-9])", b):
            continue
        out.append((i, a, b))
    return out


def main():
    do_fix = "--fix" in sys.argv
    total = 0
    allbad = collections.defaultdict(list)
    for p in MAPS:
        if not p.endswith(".tsv"):
            continue
        try:
            rows = read_rows(p)
        except Exception:
            continue
        for c in rows:
            s, d = c[0], c[1]
            for i, num, got in bad_segments(s, d):
                allbad[os.path.relpath(p, WORK)].append((s, d, num, got))
                total += 1
    print("=== 番号段错位（数字段→非第N）：%d 处，涉及 %d 个表 ===" % (total, len(allbad)))
    for f, arr in sorted(allbad.items(), key=lambda x: -len(x[1])):
        print("\n-- %s : %d 处" % (f, len(arr)))
        for s, d, num, got in arr[:40]:
            print("   %-34s -> %-30s  (段 %r 应为 第%s)" % (s[:34], d[:30], num, num))
    if do_fix:
        print("\n[FIX] 未实现原地修（需人工确认每条后按表写回）")


if __name__ == "__main__":
    main()
