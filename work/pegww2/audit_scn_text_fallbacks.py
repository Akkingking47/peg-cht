#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两块普查（**只读**）：

A · 单位名单(`_u.txt`)「整份拿错」普查 —— **最强证据＝主体与另一场景的 `_u` 主体逐条相同**（同一份文件被复制到别场），
    以及「行0 是别的场景的显示名」作次级线索（含同族 `-R` 冗余对，自动排除）。
B · `.SCN` 文本字段指向的文件在磁盘不存在（PeG 实证：引擎找不到就回退 ⇒ 实机「描述框」显示 `_m.txt` 的地名列表）。

产出：`pegww2/research/_单位名与简介普查-20261019.tsv`
用法: python audit_scn_text_fallbacks.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_单位名与简介普查-20261019.tsv")
PREFIX = re.compile(r"^[\u4e00-\u9fff]{2,4}\s*-\s*\d+\s+")
DROP = re.compile(r"(?i)peg\s*:\s*ww2|redux|重制版")
SKIP = re.compile(r"(?i)(_u|_i|_v|_l|_bv|_tv)\.txt$")

IDX = {}
for d in (os.path.join(G, "SCENARIO"), os.path.join(G, "USERSCEN")):
    if os.path.isdir(d):
        for n in os.listdir(d):
            if os.path.isfile(os.path.join(d, n)):
                IDX.setdefault(n.lower(), os.path.join(d, n))
BASES = {os.path.basename(p): os.path.basename(p) for p in IDX.values()}


def L(name):
    p = IDX.get(name.lower())
    if not p:
        return None
    return io.open(p, encoding="gbk", errors="replace").read().splitlines()


def norm(s):
    s = PREFIX.sub("", (s or "").strip())
    s = DROP.sub("", s)
    return re.sub(r"[\s:：·\-—()（）\[\]【】,，.。!！?？\"'’“”/\\]", "", s).lower()


def fam(st):
    s = st.lower()
    s = re.sub(r"[-_\s]*redux$", "", s)
    return re.sub(r"[-_\s]+r\d*$", "", s)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ufiles = sorted(os.path.basename(p) for p in IDX.values() if p.lower().endswith("_u.txt"))
    stems = {f: re.sub(r"(?i)_u\.txt$", "", f) for f in ufiles}
    body = {}
    for f in ufiles:
        ls = L(f) or []
        body[stems[f]] = "\x1f".join(x.strip() for x in ls[1:] if x.strip())
    # A1 主体相同（跨场景复制）；排除同族（X 与 X-R 等）
    bybody = {}
    for st, b in body.items():
        if b:
            bybody.setdefault(b, []).append(st)
    dupes = []
    for b, group in bybody.items():
        g = [st for st in group]
        for i, a in enumerate(g):
            for c in g[i + 1:]:
                if fam(a) != fam(c):
                    dupes.append((a, c, b))
    # 场地名索引（行0 用）
    allnames = {}
    for f in sorted(os.path.basename(p) for p in IDX.values() if p.lower().endswith("_m.txt")):
        ls = L(f)
        if ls and ls[0].strip():
            allnames.setdefault(norm(ls[0]), re.sub(r"(?i)_m\.txt$", "", f))
    campof = {}
    for p in sorted(IDX.values()):
        if p.lower().endswith(".cam"):
            b = io.open(p, "rb").read().decode("latin1").lower()
            for m in set(re.findall(r"[a-z0-9_\-]{3,}\.scn", b)):
                campof.setdefault(m[:-4], []).append(os.path.basename(p))

    rows = ["# A1 · `_u.txt` 主体与另一场景逐条相同（整份复制）",
            "场景\t同源场景\t行数\t行0\t_m行0\t所属战役\t行1-4"]
    a1 = {}
    for a, c, b in sorted(dupes):
        n = len([x for x in b.split("\x1f") if x])
        a1.setdefault(a, []).append(c)
        a1.setdefault(c, []).append(a)
    for a, c, b in sorted(dupes):
        ls = L(a + "_u.txt") or []
        m = L(a + "_m.txt") or []
        rows.append("%s\t%s\t%d\t%s\t%s\t%s\t%s" % (
            a, c, len([x for x in b.split("\x1f") if x]), ls[0].strip() if ls else "-",
            m[0].strip() if m else "-", ",".join(campof.get(a.lower(), [])) or "-",
            " | ".join([x for x in b.split("\x1f") if x][:4])))

    rows += ["", "# A2 · `_u.txt` 主体与同场 `.TXT` 主体**完全不相交**（疑整份拿错；可重建者标 ✔）",
             "场景\t_u条数\t.TXT条数\t交集\t_u行0\t同场.TXT行0\t单位段\t所属战役"]
    a2 = 0
    for st in sorted(stems.values()):
        ul = L(st + "_u.txt") or []
        tl = L(st + ".TXT") or L(st + ".txt")
        if not ul or not tl or len(tl) < 4:
            continue
        ub = {x.strip() for x in ul[1:] if x.strip()}
        tb = {x.strip() for x in tl[1:] if x.strip()}
        if not ub or not tb:
            continue
        inter = ub & tb
        if inter:
            continue
        ml = L(st + "_m.txt") or []
        place0 = ml[1].strip() if len(ml) > 1 else ""
        cut = None
        if place0:
            cut = next((k for k in range(1, len(tl)) if tl[k].strip() == place0), None)
        seg = [x.strip() for x in (tl[1:cut] if cut else []) if x.strip()]
        a2 += 1
        rows.append("%s\t%d\t%d\t%d\t%s\t%s\t%s\t%s" % (
            st, len(ub), len(tb), len(inter), ul[0].strip(), tl[0].strip(),
            ("✔ %d 条" % len(seg)) if len(seg) >= 3 else "✗(无单位段)",
            ",".join(campof.get(st.lower(), [])) or "-"))

    rows += ["", "# A3 · `_u.txt` 行0 是**别的场景**的显示名（弱线索，仅计数口径）",
             "场景\t_u行0\t＝哪个场景的名\t_m行0\t所属战役"]
    for st in sorted(stems.values()):
        ls = L(st + "_u.txt") or []
        if not ls or not ls[0].strip():
            continue
        own = {norm(st)}
        m = L(st + "_m.txt") or []
        if m:
            own.add(norm(m[0]))
        t = L(st + ".TXT") or L(st + ".txt") or []
        if t:
            own.add(norm(t[0]))
        o = allnames.get(norm(ls[0]))
        if o and o.lower() != st.lower() and norm(ls[0]) not in own and fam(o) != fam(st):
            rows.append("%s\t%s\t%s\t%s\t%s" % (st, ls[0].strip(), o, m[0].strip() if m else "-",
                                                ",".join(campof.get(st.lower(), [])) or "-"))

    rows += ["", "# B · `.SCN` 文本字段指向文件不存在（引擎回退 ⇒ 描述框可能显示 `_m.txt` 地名列表）",
             "场景\t@11210\t@11230\t@11250\t@11270\t@11290\t@11310\t@11329\t@11349\t缺失项"]
    mb = 0
    for p in sorted(IDX.values()):
        if not p.lower().endswith(".scn"):
            continue
        b = io.open(p, "rb").read()
        if len(b) < 11350:
            continue
        f = {o: b[o:o + 20].split(b"\x00")[0].decode("latin-1").strip()
             for o in (11210, 11230, 11250, 11270, 11290, 11310, 11329)}
        miss = []
        for o in (11210, 11230, 11250, 11270, 11290, 11310, 11329):
            v = f[o]
            if not v:
                continue
            if o == 11210:
                cands = [v if v.lower().endswith(".map") else v + ".map"]
            else:
                cands = [v if v.lower().endswith(".txt") else v + ".txt"]
            if not any(c.lower() in IDX for c in cands):
                miss.append("@%d=%s" % (o, v))
        if miss:
            mb += 1
            rows.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                os.path.basename(p)[:-4], f[11210], f[11230] or "-", f[11250] or "-",
                f[11270] or "-", f[11290] or "-", f[11310] or "-", f[11329] or "-",
                chr(b[11349]), ";".join(miss)))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rows) + "\n")
    print("A1 主体与别场相同：%d 对（涉及 %d 个场景）" % (len(dupes), len(a1)))
    for a, c, b in sorted(dupes)[:24]:
        print("   %-16s ≡ %-16s（%d 条）" % (a, c, len([x for x in b.split('\x1f') if x])))
    print("A2 行0＝别场景名：%d 个" % sum(1 for r in rows if r.startswith(("#",)) is False and r.count("\t") == 4))
    print("B 字段缺文件：%d 个" % mb)
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
