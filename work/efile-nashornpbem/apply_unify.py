# -*- coding: utf-8 -*-
"""OLGWW2 .xscn 组0「全量统一」写入器（按 文件+索引 定点）。

读 out/unify-plan.tsv（file / idx / action / xscn_now / new_value / reason），
只改写 action=CHANGE 的条目：把该条目的「2 字节长度字段 + 内容」整体替换，
其余字节逐字节不动（长度变化会自然后移后续偏移，非破坏）。

安全检查：
  1. (file, idx) 处的现值必须等于计划里的 xscn_now，否则跳过并报警（防串位）；
  2. 写 .new → 回读 → 校验组数/条目数不变 且 目标索引已等于新值 → 才替换；
  3. 支持重入：若该处已等于新值，跳过。

用法: python apply_unify.py            # dry-run
      python apply_unify.py --apply    # 写入
      python apply_unify.py --files    # 只列将改文件
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apply_residual import parse  # noqa: E402

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(HERE, "out", "unify-plan.tsv")


def dec(raw):
    try:
        s = raw.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return s
    except Exception:
        pass
    return raw.decode("cp1252", "replace")


def load_plan():
    per = {}
    for ln in io.open(PLAN, encoding="utf-8").read().splitlines():
        if not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) < 5 or c[2] != "CHANGE":
            continue
        per.setdefault(c[0], []).append((int(c[1]), c[3], c[4]))
    return per


def main():
    apply = "--apply" in sys.argv
    per = load_plan()
    only_files = "--files" in sys.argv
    if only_files:
        for fn in sorted(per):
            print(fn)
        return

    print("计划待改: %d 处 / %d 文件" % (sum(len(v) for v in per.values()), len(per)))
    ok_files = skip_files = 0
    bad = []
    for fn in sorted(per):
        p = os.path.join(D, fn)
        if not os.path.exists(p):
            bad.append((fn, "文件不存在"))
            continue
        data, items, meta = parse(p)
        if items is None:
            bad.append((fn, "解析失败"))
            continue
        g0 = {idx: (off, L) for gi, idx, off, L in items if gi == 0}
        todo = []
        for idx, expect, new in per[fn]:
            if idx not in g0:
                bad.append((fn, "组0 无索引 %d" % idx))
                continue
            off, L = g0[idx]
            cur = dec(data[off + 2:off + 2 + L])
            if cur == new:
                continue                     # 已统一，重入安全
            if cur != expect:
                bad.append((fn, "索引 %d 现值不符: 期望 %r 实际 %r" % (idx, expect, cur)))
                continue
            todo.append((idx, off, L, cur, new.encode("gbk")))
        if not todo:
            skip_files += 1
            continue
        if not apply:
            print("  %-22s %2d 处  (例) %s -> %s" % (fn, len(todo), todo[0][3][:22], todo[0][4].decode("gbk")[:22]))
            continue
        d = bytearray(open(p, "rb").read())
        for idx, off, L, cur, nb in sorted(todo, key=lambda x: -x[1]):
            d[off:off + 2 + L] = len(nb).to_bytes(2, "little") + nb
        tmp = p + ".new"
        open(tmp, "wb").write(bytes(d))
        d2, items2, meta2 = parse(tmp)
        good = (items2 is not None and meta2[2] == meta[2] and len(items2) == len(items))
        if good:
            g0b = {idx: (off, L) for gi, idx, off, L in items2 if gi == 0}
            for idx, off, L, cur, nb in todo:
                o2, l2 = g0b[idx]
                if d2[o2 + 2:o2 + 2 + l2] != nb:
                    good = False
                    break
        if good and d2 == bytes(d):
            os.replace(tmp, p)
            ok_files += 1
            print("  OK  %-22s %2d 处  %d -> %d B" % (fn, len(todo), len(data), len(d2)))
        else:
            os.remove(tmp)
            bad.append((fn, "回读校验失败，已回滚"))

    if not apply:
        print("\n(dry-run，未写入)")
    else:
        print("\n写入完成: %d 个文件" % ok_files)
    if skip_files:
        print("跳过（已统一）: %d 个文件" % skip_files)
    if bad:
        print("\n!! 异常 %d 条:" % len(bad))
        for b in bad[:40]:
            print("   %s" % (b,))


if __name__ == "__main__":
    main()
