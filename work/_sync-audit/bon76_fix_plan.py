# -*- coding: utf-8 -*-
"""bon76 修复计划（**只读**，不写译文/词库/交付件）。

产出两件：
  ① work\\_sync-audit\\bon76-fix-table.tsv —— 44 槽：file/slot/en/zh_old/zh_new/tier
  ② 候选层文件的命中计数（每个文件出现多少条 zh_old 精确串）

zh_new 规则（候选①落地：一律改「营」）：
  - 「第76」是凭空注入的番号前缀，**只删它**；其余逐字符不变。
  - 若该键在 glossary\\standard-glossary.tsv 里已有不含「第76」的词库值 ⇒ 用词库值（19 键，逐键回填）。
用法：C:\\Python314\\python.exe work\\_sync-audit\\bon76_fix_plan.py
"""
import io
import os
import re
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\efile-nashornpbem")
from apply_residual import parse  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
ORIG = os.path.join(WS, "backup", "ORIGINAL-EFILE_OLGWW2", "SCENARIO")
CUR = r"D:\OpenPG2\EFILE_OLGWW2\SCENARIO"
OUT = os.path.join(WS, "work", "_sync-audit", "bon76-fix-table.tsv")
HAS76 = u"\u7b2c76"
CAND = re.compile(u"^(Bon\\.|Bon |Bn )")

LAYERS = [
    r"work\xscn\zh\part-01.tsv", r"work\xscn\zh\part-02.tsv", r"work\xscn\zh\part-04.tsv",
    r"work\xscn\zh\part-05.tsv", r"work\xscn\zh\part-07.tsv", r"work\xscn\zh\part-11.tsv",
    r"work\xscn\zh\part-13.tsv", r"work\xscn\zh\part-14.tsv", r"work\xscn\zh\part-17.tsv",
    r"work\xscn\zh\part-18.tsv",
    r"work\xscn\master-resolve.tsv", r"work\xscn\master-glossary.tsv",
    r"work\xscn\master-conflicts.tsv", r"work\xscn\_xscn_dict.tsv",
    r"work\xscn\_prose_dict.tsv", r"work\xscn-all-map.tsv",
    r"work\atomic\atomic-xscn-map.tsv", r"work\atomic\_xscn-crossmap.json",
    r"work\basekorp\_xscn-crossmap.json", r"work\basekorp\bk-xscn-map.tsv",
    r"work\gce\gce-xscn-map.tsv", r"work\gce\userscen-zh.tsv",
    r"work\efile_pzliga\userscen-prematch-map.tsv", r"work\userscen\gce-userscen-uniq.tsv",
    r"work\userscen\pzliga-userscen-uniq.tsv",
    r"glossary\standard-glossary.tsv", r"glossary\layers\common-glossary.tsv",
    r"glossary\glossary-occ.tsv", r"glossary\glossary-conflicts.tsv",
    r"glossary\xscn-division-trunc.tsv", r"glossary\evidence\regen-ww2-scn-map.tsv",
    r"glossary\glossary-residual.tsv", r"glossary\layers\common-drift.tsv",
    r"glossary\layers\scope-diff.tsv", r"glossary\layers\converge-list.tsv",
    r"pegww2\research\ww2-scn-map.tsv", r"pegww2\research\_scn-fill-prose-r13-01.tsv",
]


def pairs_of(path):
    """→ {(gi,idx): (en_bytes, zh_str)} ; 只读。"""
    data, items, meta = parse(path)
    out = {}
    if meta and meta[0] is not None:
        pass
    if items is None:
        return out
    for gi, idx, off, L in items:
        raw = data[off + 2:off + 2 + L]
        out[(gi, idx)] = raw
    return out


def main():
    std = {}
    for i, ln in enumerate(io.open(os.path.join(WS, "glossary", "standard-glossary.tsv"),
                                   encoding="utf-8-sig", errors="replace").read().replace(
            "\r\n", "\n").split("\n")):
        C = ln.split("\t")
        if i and len(C) >= 2 and C[0] not in std:
            std[C[0]] = C[1]
    files = sorted(fn for fn in os.listdir(CUR) if fn.lower().endswith(".xscn"))
    rows = []
    for fn in files:
        po, pc = os.path.join(ORIG, fn), os.path.join(CUR, fn)
        if not os.path.exists(po):
            print("!! ORIG 缺失: " + fn)
            continue
        oe, cz = pairs_of(po), pairs_of(pc)
        for k, zraw in cz.items():
            try:
                zh = zraw.decode("gbk")
            except Exception:
                continue
            if HAS76 not in zh:
                continue
            eraw = oe.get(k)
            if eraw is None:
                continue
            en_cp = eraw.decode("cp1252")
            if not CAND.match(en_cp) or re.search(r"\d", en_cp[:3]):
                continue
            g = std.get(en_cp, "")
            if g and HAS76 not in g:
                new, tier = g, "19-词库回填"
            else:
                new, tier = zh.replace(HAS76, ""), "21-删76"
            rows.append((fn, "g%d#%d" % (k[0], k[1]), en_cp, zh, new, tier))
    n1 = sum(1 for r in rows if r[5].startswith("19"))
    print("=== 44 槽确认: %d 槽 / %d 个不同键（19档 %d 槽，21档 %d 槽）===" % (
        len(rows), len({r[2] for r in rows}), n1, len(rows) - n1))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("file\tslot\ten\tzh_old\tzh_new\ttier\n")
        for r in sorted(rows):
            f.write("\t".join(r) + "\n")
    print("计划表 -> %s" % OUT)
    olds = sorted({r[3] for r in rows}, key=len, reverse=True)
    print("\n=== 不同 zh_old 串 %d 个；候选层文件命中计数 ===" % len(olds))
    for rel in LAYERS:
        fp = os.path.join(WS, rel)
        if not os.path.exists(fp):
            print("  %-52s MISSING" % rel)
            continue
        raw = open(fp, "rb").read().decode("utf-8-sig", "replace")
        n_tot = raw.count(HAS76)
        n_hit = sum(raw.count(o) for o in olds)
        if n_tot or n_hit:
            print("  %-52s 含第76=%-4d 精确命中zh_old=%-4d" % (rel, n_tot, n_hit))
    print("\n=== 21 档逐键 old => new ===")
    for r in sorted({(x[2], x[3], x[4]) for x in rows if x[5].startswith("21")}):
        print("  %-34s %-34s => %s" % (r[0][:34], r[1][:34], r[2]))


if __name__ == "__main__":
    main()
