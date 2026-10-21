# -*- coding: utf-8 -*-
"""番号残留待判收口 · 证据检索（只读）

输入：
  research/_番号展开-对照表-20261020.tsv   （处置=部分待判/待判/舰名待译 的行）
  research/_u-token-map-mined.tsv          （原版_u ↔ 已译_u 实测 token 映射）
  research/_u-line-map-mined.tsv           （原版_u ↔ 已译_u 实测 整行映射）
输出（stdout + research/_番号收口-证据表-20261020.tsv）：
  每条待判行的「未解 token」+ 实测证据（token 级 / 整行级）+ 建议处置
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RES = r"d:\DSH\军事游戏汉化\pegww2\research"
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改）
os.makedirs(DER, exist_ok=True)
CJK = re.compile(r"[\u4e00-\u9fff]")
SEP = re.compile(r"(\s+|/)")

# token 映射
tok = {}
for i, raw in enumerate(io.open(os.path.join(DER, "_u-token-map-mined.tsv"), encoding="utf-8")):
    if i == 0 or raw.startswith("#"):
        continue
    f = raw.rstrip("\r\n").split("\t")
    if len(f) >= 4:
        tok[f[0]] = (f[1], float(f[2]) if f[2].replace(".", "").isdigit() else 0.0,
                     f[3], f[4] if len(f) > 4 else "")

# 整行映射：原文行 -> 译法
line = {}
for i, raw in enumerate(io.open(os.path.join(DER, "_u-line-map-mined.tsv"), encoding="utf-8")):
    if i == 0 or raw.startswith("#"):
        continue
    f = raw.rstrip("\r\n").split("\t")
    if len(f) >= 2:
        line[f[0]] = f[1]

# 隧道：待判行为
rows = []
p = os.path.join(RES, "_番号展开-对照表-20261020.tsv")
for i, raw in enumerate(io.open(p, encoding="utf-8")):
    if i == 0 or raw.startswith("#"):
        continue
    f = raw.rstrip("\r\n").split("\t")
    if len(f) < 10:
        continue
    if f[8] in ("部分待判", "待判", "舰名待译"):
        rows.append(f)

# 收集未解 token（建议译法里仍是拉丁、且不在原行「已解」位置的那些）
def unresolved(orig, prop):
    """返回建议译法里未被中文化的拉丁 token（去重、保序）。"""
    o = [t for t in SEP.split(orig) if t and not SEP.fullmatch(t)]
    p2 = [t for t in SEP.split(prop) if t and not SEP.fullmatch(t)]
    out = []
    for t in p2:
        if CJK.search(t) or re.fullmatch(r"[-\[\]0-9]+", t):
            continue
        if t in o and t not in out:
            out.append(t)
    return out

agg = defaultdict(lambda: {"n": 0, "nat": Counter(), "scn": set(), "ex": []})
for f in rows:
    nat, era, fam, th, scn, orig, prop, why, disp, cf = f[:10]
    for t in unresolved(orig, prop):
        e = agg[t]
        e["n"] += 1
        e["nat"][nat] += 1
        e["scn"].add(scn)
        if len(e["ex"]) < 3:
            e["ex"].append((scn, orig, prop, disp))

print("== 未解 token 汇总（%d 个）==" % len(agg))
out = ["# 番号收口 · 未解 token 证据表（只读产出）",
       "token\t行数\t国别分布\t出现场景数\ttoken级实测\t整行级实测(含CJK)\t建议"]
for t in sorted(agg, key=lambda k: (-agg[k]["n"], k)):
    e = agg[t]
    tv = tok.get(t)
    if tv:
        cnt = tv[0]
        share = tv[1]
        hit = int(tv[2]) if tv[2].isdigit() else 0
        tinfo = "%s(share=%s, cnt=%d)" % (cnt, share, hit)
    else:
        tinfo = "—"
    # 整行证据：找包含该 token 的原行，且有中文译法的
    li = []
    for k, v in line.items():
        segs = [x for x in SEP.split(k) if x and not SEP.fullmatch(x)]
        if t in segs and CJK.search(v):
            li.append((k, v))
            if len(li) >= 4:
                break
    linfo = " ; ".join("%s→%s" % kv for kv in li) if li else "—"
    natd = "/".join("%s%d" % kv for kv in e["nat"].most_common(3))
    out.append("%s\t%d\t%s\t%d\t%s\t%s\t" % (t, e["n"], natd, len(e["scn"]), tinfo, linfo))
    print("%-8s n=%-4d nat=%-22s tok=%-28s line=%s" %
          (t, e["n"], natd, tinfo[:28], linfo[:100]))

with io.open(os.path.join(DER, "_番号收口-证据表-20261020.tsv"), "w",
             encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(out) + "\n")
print("[out]", os.path.join(DER, "_番号收口-证据表-20261020.tsv"))
