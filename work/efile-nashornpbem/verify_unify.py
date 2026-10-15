# -*- coding: utf-8 -*-
"""OLGWW2 .xscn 统一写入的独立复核（重建法）。

方法：取 backup/olgww2-unify-before/<f> 的原始字节 → 按 unify-plan.tsv 在
组0 指定索引做替换 → 重新序列化 → 与当前 D:/OpenPG2/... 下的文件**逐字节比对**。
另附结构审计：组数/条目数与备份一致、全库 187 个 .xscn 均可解析、尾部无残缺。

用法: python verify_unify.py [plan.tsv]   （默认 out/unify-plan.tsv）
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_residual import parse  # noqa: E402

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
BK = r"D:/DSH/军事游戏汉化/backup/olgww2-unify-before"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    global PLAN_PATH
    plan_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "unify-plan.tsv")
    PLAN_PATH = plan_path
    plan = {}
    for ln in io.open(plan_path, encoding="utf-8").read().splitlines():
        if not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 5 and c[2] == "CHANGE":
            plan.setdefault(c[0], []).append((int(c[1]), c[3], c[4]))
    print("计划: %s" % os.path.basename(plan_path))

    print("=" * 92)
    print("1. 重建比对（备份 + 计划 → 应等于现文件）")
    print("=" * 92)
    ok = bad = 0
    for fn in sorted(plan):
        p = os.path.join(D, fn)
        b = os.path.join(BK, fn)
        data, items, meta = parse(b)
        g0 = {idx: (off, L) for gi, idx, off, L in items if gi == 0}
        d = bytearray(data)
        for idx, expect, new in sorted(plan[fn], key=lambda x: -g0[x[0]][0]):
            off, L = g0[idx]
            nb = new.encode("gbk")
            d[off:off + 2 + L] = len(nb).to_bytes(2, "little") + nb
        cur = open(p, "rb").read()
        if bytes(d) == cur:
            ok += 1
        else:
            bad += 1
            print("  !! %-22s 重建不一致（%d vs %d B）" % (fn, len(d), len(cur)))
    print("  重建一致: %d/%d 个文件   %s" % (ok, len(plan), "✅" if bad == 0 else "✗"))

    print()
    print("=" * 92)
    print("2. 结构审计：全库 .xscn 可解析 + 组数与备份一致 + 尾部完整")
    print("=" * 92)
    files = sorted(f for f in os.listdir(D) if f.lower().endswith(".xscn"))
    bad2 = []
    n_changed = 0
    for fn in files:
        p = os.path.join(D, fn)
        data, items, meta = parse(p)
        if items is None:
            bad2.append((fn, "解析失败"))
            continue
        if fn in plan:
            _, _, metab = parse(os.path.join(BK, fn))
            if meta[2] != metab[2]:
                bad2.append((fn, "组数变化 %s -> %s" % (metab[2], meta[2])))
                continue
            if len(items) != len(parse(os.path.join(BK, fn))[1]):
                bad2.append((fn, "条目数变化"))
                continue
            n_changed += 1
    print("  全库 .xscn: %d 个；参与统一: %d 个" % (len(files), n_changed))
    print("  结构异常: %s" % ("无 ✅" if not bad2 else bad2[:20]))

    print()
    print("=" * 92)
    print("3. 目标条目落位抽检")
    print("=" * 92)


def dec(raw):
    try:
        s = raw.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return s
    except Exception:
        pass
    return raw.decode("cp1252", "replace")


def spot(plan_path):
    plan = {}
    for ln in io.open(plan_path, encoding="utf-8").read().splitlines():
        if not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 5 and c[2] == "CHANGE":
            plan.setdefault(c[0], []).append((int(c[1]), c[3], c[4]))
    tot = miss = 0
    for fn in sorted(plan):
        data, items, meta = parse(os.path.join(D, fn))
        g0 = {idx: (off, L) for gi, idx, off, L in items if gi == 0}
        for idx, expect, new in plan[fn]:
            tot += 1
            off, L = g0[idx]
            if dec(data[off + 2:off + 2 + L]) != new:
                miss += 1
                if miss <= 10:
                    print("  !! %s[%d] 未落位: %r" % (fn, idx, dec(data[off + 2:off + 2 + L])))
    print("  目标条目 %d 处，已落位 %d 处  %s" % (tot, tot - miss, "✅" if miss == 0 else "✗"))


if __name__ == "__main__":
    main()
    spot(PLAN_PATH)
