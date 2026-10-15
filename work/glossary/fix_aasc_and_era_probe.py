#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""① `AASC` 定稿为**澳军勤务部队**（用户 2026-10-12 决定）
   ② 量"场景年代可提取率"——决定**年代维度**值不值得做

用法: python fix_aasc_and_era_probe.py [--apply]
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
OVF = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
CBK = os.path.join(WS, "backup", "before-aasc-final")
SET = [("tobruk-R_u.txt", 29, "澳军勤务部队(AASC)"), ("RM_usvsruss19_i.txt", 36, "澳军勤务部队(AASC)")]
RANGE = os.path.join(WS, "pegww2", "research", "_scn-date-coverage.txt")


def fix(apply_):
    t = io.open(OVF, encoding="utf-8").read()
    out, done = [], set()
    for l in t.split("\n"):
        c = l.split("\t")
        if len(c) >= 2 and any(c[1] == fn and c[2] == str(i) for fn, i, _z in SET):
            en = io.open(os.path.join(BK, c[1]), encoding="cp1252", errors="replace").read().split("\n")[int(c[2])]
            l = "\t".join(("SCENARIO", c[1], c[2], en.rstrip("\r\n"),
                           [z for fn, i, z in SET if fn == c[1]][0], "澳军勤务部队（用户裁定 2026-10-12）"))
            done.add(c[1])
        out.append(l)
    add = []
    for fn, i, zh in SET:
        if fn in done:
            continue
        p = os.path.join(BK, fn)
        if os.path.isfile(p):
            en = io.open(p, encoding="cp1252", errors="replace").read().split("\n")[i]
            add.append("\t".join(("SCENARIO", fn, str(i), en.rstrip("\r\n"), zh, "澳军勤务部队（用户裁定）")))
    print("=== ① AASC 定稿：改 %d · 新增 %d ===" % (len(done), len(add)))
    for fn, i, zh in SET:
        print("   %-22s 行%-4d → %s" % (fn, i, zh))
    if not apply_:
        return
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    if add:
        if not out[-1].endswith("\n"):
            out[-1] += "\n"
        out += add
    io.open(OVF, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("✅ 已写 %s" % OVF)


def probe_dates():
    """统计：场景能否取出"年代/日期"（简报里的日期行）。"""
    pats = [re.compile(r"(19[3-5]\d)\s*年\s*(\d{1,2})?\s*月?"),
            re.compile(r"(?i)(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+(19[3-5]\d)"),
            re.compile(r"(?i)\b(19[3-5]\d)\b")]
    ok = no = 0
    years = {}
    for fn in sorted(os.listdir(GAME)):
        if not fn.lower().endswith(".txt") or re.search(r"(?i)(read ?me|report|info\.txt)", fn):
            continue
        try:
            t = io.open(os.path.join(GAME, fn), encoding="gbk", errors="replace").read()
        except Exception:
            continue
        if re.search(r"(?i)(_m\.txt$)", fn):
            continue                       # 地图标签文件通常无日期
        hit = None
        for p in pats:
            m = p.search(t)
            if m:
                g = [x for x in m.groups() if x and x.isdigit() and len(x) == 4]
                hit = g[0] if g else m.group(1)
                break
        if hit:
            ok += 1
            years[hit] = years.get(hit, 0) + 1
        else:
            no += 1
    print("\n=== ② 场景年代可提取率（文本类文件 %d 个）===" % (ok + no))
    print("   可提取 %d 个（%.0f%%）· 无法提取 %d 个" % (ok, 100.0 * ok / max(1, ok + no), no))
    print("   年份分布：%s" % dict(sorted(years.items())))
    with io.open(RANGE, "w", encoding="utf-8", newline="\n") as w:
        w.write("场景年代可提取：%d 个 / 共 %d（%.0f%%）\n" % (ok, ok + no, 100.0 * ok / max(1, ok + no)))
        w.write("年份分布：%s\n" % dict(sorted(years.items())))
    print("   → %s" % RANGE)


if __name__ == "__main__":
    fix("--apply" in sys.argv)
    probe_dates()
