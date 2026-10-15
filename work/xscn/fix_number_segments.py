# -*- coding: utf-8 -*-
"""修复「纯数字段 → 连」错位（BASEKORP 历史误译：数字 100 被当罗马数字 C＝Company＝连）。

两种目标：
  --target map    修 `work/basekorp/bk-xscn-map.tsv`（真源表）
  --target files  修 `D:\\OpenPG2\\EFILE_BASEKORP\\SCENARIO\\*.xscn`（已写入的成品，
                  以 backup/ORIGINAL-EFILE_BASEKORP 的原文为对照，按位置精确改写）

规则：src/dst 按 `/` 分段，段数相同且 src 段为纯数字 N 时，dst 段应为 `第N…`；
      若 dst 段是 `连` ⇒ 改为 `第N`。**只改这一种模式，不动其它任何内容。**
默认干跑，加 --apply 才写。
用法:
  python fix_number_segments.py --target map   [--apply]
  python fix_number_segments.py --target files [--apply]
"""
import io
import os
import re
import sys
import importlib.util

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MAP = r"D:\DSH\军事游戏汉化\work\basekorp\bk-xscn-map.tsv"
BK = r"D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_BASEKORP\SCENARIO"
CUR = r"D:\OpenPG2\EFILE_BASEKORP\SCENARIO"
NUM = re.compile(r"^\d+$")

_x = importlib.util.module_from_spec(importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py")))
try:
    importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py")).loader.exec_module(_x)
except SystemExit:
    pass


def fix_line(s, d):
    """把 dst 里对应到「src 纯数字段」却译成 `连` 的段，改成 `第N`。返回新 dst 或 None。
    ⚠️ 含**单段**情形（src 就是纯数字，如 `100 → 连`）—— 首版漏掉，导致 map 表里
       裸 `100 → 连` 存活并继续经词典传播。"""
    s, d = s.strip(), d.strip()
    if NUM.match(s) and d == "连":
        return "第" + s
    if "/" not in s:
        return None
    ps, pd = s.split("/"), d.split("/")
    if len(ps) != len(pd):
        return None
    changed = False
    for i, (a, b) in enumerate(zip(ps, pd)):
        a, b = a.strip(), b.strip()
        if NUM.match(a) and b == "连":
            pd[i] = "第" + a
            changed = True
    return "/".join(pd) if changed else None


def do_map(apply_):
    rows, n = [], 0
    with io.open(MAP, encoding="utf-8-sig", newline="") as f:
        head = f.readline()
        for ln in f.read().replace("\r\n", "\n").split("\n"):
            if not ln.strip():
                continue
            c = ln.rstrip("\n").split("\t")
            if len(c) >= 2:
                nd = fix_line(c[0], c[1])
                if nd and nd != c[1]:
                    print("   %-34s : %-28s -> %s" % (c[0][:34], c[1][:28], nd[:28]))
                    c[1] = nd
                    n += 1
            rows.append("\t".join(c))
    print("map 表待修 %d 条" % n)
    if apply_ and n:
        bak = MAP + ".before-numfix"
        if not os.path.exists(bak):
            io.open(bak, "w", encoding="utf-8", newline="").write(
                io.open(MAP, encoding="utf-8-sig", newline="").read())
        with io.open(MAP, "w", encoding="utf-8", newline="") as f:
            f.write(head if head.endswith("\n") else head + "\n")
            for r in rows:
                f.write(r + "\n")
        print("已写回 %s（备份 %s）" % (MAP, bak))
    elif not apply_:
        print("(dry-run，未写)")


def do_files(apply_):
    fs = sorted(f for f in os.listdir(BK) if f.lower().endswith(".xscn"))
    tot = 0
    nfile = 0
    for fn in fs:
        pb, pc = os.path.join(BK, fn), os.path.join(CUR, fn)
        data_b, items_b, meta_b = _x.parse(pb)
        data_c, items_c, meta_c = _x.parse(pc)
        if items_b is None or items_c is None or len(items_b) != len(items_c):
            continue
        slots_b = _x.slots_of(data_b, items_b, meta_b)
        slots_c = _x.slots_of(data_c, items_c, meta_c)
        plan = []
        for (gb, ib, ob, lb), (gc, ic, oc, lc) in zip(slots_b, slots_c):
            rawb = _x.raw_at(data_b, ob, lb)
            rawc = _x.raw_at(data_c, oc, lc)
            _, s = _x.decode(rawb)
            _, d = _x.decode(rawc)
            nd = fix_line(s.strip(), d.strip())
            if nd and nd != d.strip():
                lead = rawc[:len(rawc) - len(rawc.lstrip())]
                trail = rawc[len(rawc.rstrip()):]
                new = lead + nd.encode(_x.ENC_OUT) + trail
                plan.append((oc, lc, rawc, new))
        if not plan:
            continue
        nfile += 1
        tot += len(plan)
        print("  %-22s %d 处" % (fn, len(plan)))
        for oc, lc, rawc, new in plan[:3]:
            print("       %r -> %r" % (_x.decode(rawc)[1], _x.decode(new)[1]))
        if apply_:
            data = bytearray(open(pc, "rb").read())
            before = _x.parse(pc)
            for oc, lc, rawc, new in sorted(plan, key=lambda x: -x[0]):
                data[oc:oc + 2 + lc] = len(new).to_bytes(2, "little") + new
            if _x.write_checked(pc, data, before):
                pass
            else:
                print("  !! %s 校验失败已回滚" % fn)
    print("文件待修 %d 处 / %d 个文件%s" % (tot, nfile, "" if apply_ else "  (dry-run，未写)"))


if __name__ == "__main__":
    a = "--apply" in sys.argv
    t = sys.argv[sys.argv.index("--target") + 1] if "--target" in sys.argv else "map"
    if t == "map":
        do_map(a)
    else:
        do_files(a)
