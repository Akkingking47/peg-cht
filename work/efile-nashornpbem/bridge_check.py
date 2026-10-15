# -*- coding: utf-8 -*-
"""用 ORIGINAL-EFILE_OLGWW2 的原始英文 .txt/.xscn 做硬桥，零歧义地找出
   OLGWW2 .xscn 组0 里「已有中文但与权威清单不一致」的条目。

原理（不依赖任何位置对齐）：
  1. 原始英文 <n>.txt  <->  现中文 <n>.txt   逐行平行（同文件的两个语言版）
     ⇒ 得到 英文名 -> 中文名 字典
  2. orig.xscn 组0[i]  = 该条目的英文原名（索引天然对齐，同文件同结构）
     cur.xscn 组0[i]   = 现有中文
  3. cur[i] != dict[orig[i]]  ⇒ 不一致，且两边的对应关系由 i 直接锁定

用法: python bridge_check.py            # 只报告
      python bridge_check.py --parallel # 先验证 txt 是否逐行平行
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match_txt_names import parse_g0, dec, zh, is_unit_line

SCN = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
ORIG = r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))


def readlines(p, enc):
    try:
        return io.open(p, encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return None


def build_dict():
    """建 英文->中文 字典。
    返回 (global_dict, per_file_dict, (par_ok, par_bad), conflict)
    per_file_dict[name] = 该 .txt 自己的映射（优先），global 仅作兜底。"""
    names = sorted(x for x in os.listdir(ORIG) if x.lower().endswith(".txt"))
    D = {}
    per_file = {}
    conflict = []
    par_ok, par_bad = 0, []
    for n in names:
        a = readlines(os.path.join(ORIG, n), "cp1252")
        b = readlines(os.path.join(SCN, n), "gbk")
        if a is None or b is None:
            par_bad.append((n, "缺文件"))
            continue
        if len(a) != len(b):
            par_bad.append((n, "行数 %d vs %d" % (len(a), len(b))))
            continue
        par_ok += 1
        local = {}
        for ea, zb in zip(a, b):
            ea, zb = ea.strip(), zb.strip()
            if not ea:
                continue
            if ea in D and D[ea] != zb:
                conflict.append((ea, D[ea], zb, n))
            else:
                D.setdefault(ea, zb)
            local[ea] = zb
        per_file[n[:-4]] = local
    return D, per_file, (par_ok, par_bad), conflict


def main():
    D, per_file, (par_ok, par_bad), conflict = build_dict()
    print("=" * 96)
    print("1. .txt 双语版逐行平行性")
    print("=" * 96)
    tot = par_ok + len(par_bad)
    print("  逐行平行: %d/%d 个文件   ✅" % (par_ok, tot) if not par_bad
          else "  逐行平行: %d/%d 个文件" % (par_ok, tot))
    if par_bad:
        print("  ⇒ 不平行（不进字典）:")
        for n, why in par_bad[:20]:
            print("     %-22s %s" % (n, why))
    print("  英文名 -> 中文名 字典: %d 条" % len(D))
    if conflict:
        print("  !! 同英文名对应多个中文: %d 条" % len(conflict))
        for ea, z1, z2, n in conflict[:20]:
            print("     %-28s %s / %s   (%s)" % (ea[:28], z1, z2, n))

    print()
    print("=" * 96)
    print("2. 逐 .xscn 校验组0（英文原名 -> 应有中文 | 现有中文）")
    print("=" * 96)
    xs = sorted(x for x in os.listdir(SCN) if x.lower().endswith(".xscn"))
    bad, noorig, stats = [], [], {"ok": 0, "plain": 0, "notfound": 0}
    for n in xs:
        po = os.path.join(ORIG, n)
        pc = os.path.join(SCN, n)
        if not os.path.exists(po):
            noorig.append(n)
            continue
        o = parse_g0(po)
        c = parse_g0(pc)
        if o is None or c is None:
            noorig.append(n + " (解析失败)")
            continue
        if len(o) != len(c):
            noorig.append("%s (组0 条数 %d vs %d)" % (n, len(o), len(c)))
            continue
        local = per_file.get(n[:-5], {})
        for i, (ro, rc) in enumerate(zip(o, c)):
            se = dec(ro)
            sc = dec(rc)
            if not se.strip():
                continue
            if se in local:
                want = local[se]          # 优先同场景 .txt
            elif se in D:
                want = D[se]              # 兜底全局
            else:
                stats["notfound"] += 1
                continue
            if sc == want:
                stats["ok"] += 1
            elif not zh(sc):
                stats["plain"] += 1          # 仍是英文（另有既定流程处理）
            else:
                bad.append((n, i, se, sc, want))

    print("  组0 条目命中字典并要求一致: %d  ✅；仍是英文: %d（另行处理）；字典未收录: %d"
          % (stats["ok"], stats["plain"], stats["notfound"]))
    print("  !! 不一致: %d 处" % len(bad))
    print()
    print("%-18s %-4s %-30s %-22s %s" % ("file", "i", "orig英文", "现有中文", "权威中文"))
    print("-" * 110)
    for n, i, se, sc, want in bad:
        print("%-18s %-4d %-30s %-22s %s" % (n, i, se[:30], sc[:22], want))
    with io.open(os.path.join(HERE, "out", "bridge-mismatch.tsv"), "w",
                 encoding="utf-8", newline="\n") as f:
        for n, i, se, sc, want in bad:
            f.write("%s\t%d\t%s\t%s\t%s\n" % (n, i, se, sc, want))
    if noorig:
        print()
        print("  !! 无法校验: %s" % noorig[:20])


if __name__ == "__main__":
    main()
