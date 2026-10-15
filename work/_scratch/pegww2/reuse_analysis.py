#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段1 准备：前作资产复用率实测。

复用来源（前作 PeG，已交付锁定）：
  peg/research/gui030-zh.tsv      行号模式（行号/原文/译文/备注）
  peg/research/misc030-map.tsv    行号模式（行号/译文）
  peg/research/tips030-map.tsv    行号模式（行号/译文）
  peg/research/Equip30-map.tsv    原文串模式（原文/译文）
  peg/research/scenario-map.tsv   原文串模式（原文/译文，含分节注释）
  peg/research/scenario-long-zh.tsv  ?
  peg/research/ui-glossary.tsv    术语表 en/zh/类别/依据/备注
  glossary/standard-glossary.tsv  23,200
  work/xscn/master-glossary.tsv   119,624 四层

判据：
  · 行号模式（引擎按行号取字的文件）→ 必须「同一行号 + 英文原文一致」才算命中
  · 原文串模式（按整串查表的文件）→ 英文整串一致即命中
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
PEG = os.path.join(WS, "peg", "research")
OUT = os.path.join(WS, "pegww2", "research")
os.makedirs(OUT, exist_ok=True)
_REPORT = os.path.join(OUT, "reuse-analysis.txt")
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

HEADERS = {"行号", "en", "原文", "src", "key"}


def rows_of(path):
    out = []
    if not os.path.isfile(path):
        return out
    for enc in ("utf-8-sig", "gbk", "cp1252"):
        try:
            with open(path, encoding=enc) as fh:
                for line in fh:
                    s = line.rstrip("\r\n")
                    if not s or s.startswith("#"):
                        continue
                    f = s.split("\t")
                    if f[0].strip() in HEADERS:
                        continue
                    out.append([x.strip() for x in f])
            return out
        except UnicodeDecodeError:
            out = []
            continue
    return out


def build_maps(path):
    """返回 (line_map, value_map)。line_map: int -> zh（3 列时另有 en）; value_map: en -> zh"""
    lm, vm = {}, {}
    for f in rows_of(path):
        if len(f) < 2:
            continue
        if re.fullmatch(r"\d+", f[0]):
            k = int(f[0])
            if len(f) >= 3:
                lm[k] = (f[1], f[2])
            else:
                lm[k] = ("", f[1])
        else:
            vm[f[0]] = f[1]
    return lm, vm


def lines_of(path):
    with open(path, "rb") as f:
        b = f.read()
    return [x.decode("cp1252", "replace") for x in re.split(rb"\r\n|\r|\n", b)]


def main():
    print("=" * 96)
    print("A. 载入前作资产")
    print("=" * 96)
    assets = {}
    for nm in ["gui030-zh.tsv", "misc030-map.tsv", "tips030-map.tsv",
               "Equip30-map.tsv", "scenario-map.tsv", "scenario-long-zh.tsv"]:
        p = os.path.join(PEG, nm)
        lm, vm = build_maps(p)
        assets[nm] = (lm, vm)
        print(f"  {nm:26s} 行号模式 {len(lm):<6d} 原文串模式 {len(vm):<6d} {'（缺）' if not os.path.isfile(p) else ''}")

    # 术语总库（值模式）
    gloss = {}
    for p in [os.path.join(PEG, "ui-glossary.tsv"),
              os.path.join(WS, "glossary", "standard-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-glossary.tsv"),
              os.path.join(WS, "work", "xscn", "master-words.tsv")]:
        _, vm = build_maps(p)
        for k, v in vm.items():
            gloss.setdefault(k, v)
        # ui-glossary 是多列表：en/zh/类别/依据/备注
        for f in rows_of(p):
            if len(f) >= 2 and f[0] not in HEADERS:
                gloss.setdefault(f[0], f[1])
    print(f"  {'术语总库(合并)':26s} {len(gloss):,} 条")

    print()
    print("=" * 96)
    print("B. 根级 5 文件：复用率（行号模式严格判据）")
    print("=" * 96)
    plan = [
        ("WW2Gui.txt", "gui030-zh.tsv", "line", None),
        ("WW2Misc.txt", "misc030-map.tsv", "line", None),
        ("WW2Tips.TXT", "tips030-map.tsv", "line", None),
        ("ww2-eqp.txt", "Equip30-map.tsv", "value", None),
        ("WW2NAME.TXT", None, "value", "name"),
    ]
    total_need = 0
    for fn, asset, mode, special in plan:
        p = os.path.join(GAME, fn)
        ls = lines_of(p)
        n = len([x for x in ls if x.strip()])
        need = []
        reuse = 0
        if asset:
            lm, vm = assets[asset]
        else:
            lm, vm = {}, {}
        if special == "name":
            # 从「前作原文 × 已部署成品」还原姓名表
            o = lines_of(os.path.join(WS, "peg", "testbed", "backup", "name030.txt"))
            d = lines_of(os.path.join(r"D:\Program Files\PeG", "Name030.txt"))
            m = min(len(o), len(d))
            vm = {}
            for i in range(m):
                a, b = o[i].strip(), d[i].strip()
                if a and b and a != b:
                    vm.setdefault(a, b)
            print(f"  （name 表由前作原文×成品还原：{len(vm)} 条）")
        for idx, s in enumerate(ls):
            t = s.strip()
            if not t:
                continue
            hit = None
            if mode == "line":
                ent = lm.get(idx + 1)          # 引擎 1-based
                if ent:
                    en, zh = ent
                    if not en or en == t:      # 英文一致（或映射表未记原文）
                        hit = zh
            else:
                hit = vm.get(t)
            if hit:
                reuse += 1
            else:
                need.append((idx + 1, t))
        total_need += len(need)
        print(f"\n  {fn}: 非空 {n}  复用 {reuse} ({reuse / max(1, n) * 100:.1f}%)  **需新译 {len(need)}**")
        for k, t in need[:12]:
            print(f"      行{k:<5d} {t[:86]}")
        if len(need) > 12:
            print(f"      … 其余 {len(need) - 12} 条")
    print(f"\n  ⇒ 根级合计需新译：{total_need} 条")

    print()
    print("=" * 96)
    print("C. 场景层：复用率（原文串模式：前作 scenario-map + long + 术语总库）")
    print("=" * 96)
    smap = dict(assets["scenario-map.tsv"][1])
    lmap = dict(assets["scenario-long-zh.tsv"][1])
    for k, v in lmap.items():
        smap.setdefault(k, v)
    print(f"  前作场景译文（串模式合并）: {len(smap):,} 条")
    # ⚠️ 大小写不敏感的术语总库**只建一次**（曾因在生成器内重复构建 6 万条集合而卡死）
    gloss_lc = {}
    for kk, vv in gloss.items():
        gloss_lc.setdefault(kk.lower(), vv)

    def classify(name):
        n = name.lower()
        for suf, tag in (("_m.txt", "m"), ("_u.txt", "u"), ("_i.txt", "i"), ("_bv.txt", "bv"),
                         ("_tv.txt", "tv"), ("_l.txt", "l"), ("_v.txt", "v")):
            if n.endswith(suf):
                return tag
        if n.endswith(".log"):
            return "log"
        if n.endswith(".tx"):
            return "tx"
        if n.endswith(".txt"):
            return "txt"
        return "其他"

    for tag, d in (("SCENARIO", os.path.join(GAME, "SCENARIO")),
                   ("USERSCEN", os.path.join(GAME, "USERSCEN"))):
        uniq = defaultdict(set)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if not os.path.isfile(p) or not re.search(r"(?i)\.(txt|ply|tx|t|log)$", f):
                continue
            k = f"{tag}/{classify(f)}"
            for s in lines_of(p):
                t = s.strip()
                if t and re.search(r"[A-Za-z]", t):
                    uniq[k].add(t)
        for k in sorted(uniq):
            u = uniq[k]
            hit_s = sum(1 for x in u if x in smap)
            hit_g = sum(1 for x in u if x.lower() in gloss_lc)
            print(f"  {k:22s} 可译唯一={len(u):<7d} 前作场景命中={hit_s:<6d} 术语总库命中={hit_g:<6d} "
                  f"⇒ 需新译≈{len(u) - max(hit_s, hit_g)}")


if __name__ == "__main__":
    main()
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    print(f"\n[report] {_REPORT}")
