# -*- coding: utf-8 -*-
"""只读审计 ③ v2：简报 vs 地图 地名对不上号（去伪影版）。

v1 的错：简报行是**散文片段**（`夺取伊尔库茨克`），与地图的裸名（`伊尔库茨克`）被当成两个译名。
v2 修正：用**子串包含**判同一性 —— 先剥装饰（`(#2)`、序号、引号），
再取「最小核」（不被同组其它串包含者）；**核 ≥2 ⇒ 真冲突**；核 =1 但写法有别 ⇒ 低危（后缀/装饰差）。
"""
import os
import re
import io
import sys
import collections

WS = r"D:\DSH\军事游戏汉化"

PROJECTS = {
    "peg": dict(
        label="PeG（前作）",
        game=r"D:\Program Files\PeG\Scenario",
        back=os.path.join(WS, "peg", "testbed", "backup", "Scenario"),
    ),
    "pegww2": dict(
        label="PeG-WW2",
        game=r"D:\Program Files\PeG-WW2\SCENARIO",
        back=os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO"),
    ),
    "pegww2u": dict(
        label="PeG-WW2 · USERSCEN",
        game=r"D:\Program Files\PeG-WW2\USERSCEN",
        back=os.path.join(WS, "pegww2", "testbed", "backup", "USERSCEN"),
    ),
}

SENT_END = re.compile(r"[.!?。！？:：]$")
HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
PAREN = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·\u3007]{0,15})\s*\(([A-Za-z][A-Za-z0-9 .'\-,]{1,34})\)")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")
LEADNUM = re.compile(r"^[\s\-–—]*\(?#?\d+\)?[\s、.．]*")
FEATURE = ("河", "山", "岛", "城", "港", "湾", "湖", "海", "铁路", "公路", "机场", "要塞", "半岛", "堡")


def strip_deco(s):
    s = s.strip().strip('"“”「」')
    s = LEADNUM.sub("", s)
    s = TAILTAG.sub("", s)
    return s.strip().strip(" .,-–—、·")


def norm_en(s):
    s = strip_deco(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,-–—").lower()


def is_short_name(s):
    t = s.strip()
    if not (2 <= len(t) <= 40):
        return False
    if not HAS_LETTER.search(t):
        return False
    if SENT_END.search(t):
        return False
    if t.count(",") + t.count("，") >= 2 or t.count(".") >= 2:
        return False
    return True


def cls_of(fn):
    low = fn.lower()
    if low.endswith("_m.txt"):
        return "M地图"
    if low.endswith("_u.txt"):
        return "U单位"
    if low.endswith("_i.txt"):
        return "I说明"
    if low.endswith("_n.txt"):
        return "N名栏"
    if low.endswith(".ply"):
        return "PLY简报"
    return "简报" + os.path.splitext(fn)[1].upper().lstrip(".")


def cores(zs):
    """最小核：不被同组其它串包含者（含 CJK 才算候选）。"""
    cand = sorted({z for z in zs if HAS_CJK.search(z)}, key=len)
    out = []
    for z in cand:
        if not any(z != o and z in o for o in cand):
            out.append(z)
    return out


def is_feature_only(a, b):
    """只差一个地貌/设施后缀？"""
    s, l = (a, b) if len(a) <= len(b) else (b, a)
    if not l.startswith(s):
        return False
    return l[len(s):] in FEATURE


def run(proj):
    cfg = PROJECTS[proj]
    G, B = cfg["game"], cfg["back"]
    if not (os.path.isdir(G) and os.path.isdir(B)):
        print(f"⛔ 缺目录：{G} / {B}"); return
    gset = {x.lower(): x for x in os.listdir(G)}
    bset = {x.lower(): x for x in os.listdir(B)}
    common = sorted(set(gset) & set(bset))
    print("=" * 78)
    print(f"### {cfg['label']}")
    print(f"   成品 {len(gset)} · 备份 {len(bset)} · 配对 {len(common)}"
          f" · 仅成品 {len(set(gset)-set(bset))} · 仅备份 {len(set(bset)-set(gset))}")

    seen = collections.defaultdict(lambda: collections.defaultdict(set))
    glob = collections.defaultdict(collections.Counter)
    npair = 0
    bad = []
    for fn in common:
        gname, bname = gset[fn], bset[fn]
        if gname.lower().endswith(".scn"):
            continue
        try:
            gt = open(os.path.join(G, gname), "rb").read().decode("gbk", "replace")
            bt = open(os.path.join(B, bname), "rb").read().decode("cp1252", "replace")
        except Exception as e:
            bad.append((gname, "decode", str(e))); continue
        gl, bl = re.split(r"\r\n|\r|\n", gt), re.split(r"\r\n|\r|\n", bt)
        if len(gl) != len(bl):
            bad.append((gname, f"{len(bl)}→{len(gl)}", "行数不平行"))
        stem = re.split(r"[_.]", gname)[0]
        cc = cls_of(gname)
        for i in range(min(len(gl), len(bl))):
            e, z = bl[i].strip(), gl[i].strip()
            if e and z and is_short_name(e) and HAS_CJK.search(z):
                k = norm_en(e)
                if k:
                    seen[(stem, k)][z].add(cc); glob[k][z] += 1; npair += 1
        for m in PAREN.finditer(gt):
            k = norm_en(m.group(2))
            if k:
                seen[(stem, k)][m.group(1).strip()].add(cc)
                glob[k][m.group(1).strip()] += 1; npair += 1
    print(f"   名字对 {npair} 条")

    A_hi, A_lo = [], []
    for (stem, k), zs in seen.items():
        cs = cores(set(zs))
        if len(cs) >= 2:
            A_hi.append((stem, k, " ｜ ".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in cs)))
        elif len(zs) >= 2:
            ks = [z for z in zs if strip_deco(z) in cs] or list(zs)
            if len({strip_deco(z) for z in zs}) >= 2:
                pair = sorted({strip_deco(z) for z in zs}, key=len)
                tag = "地貌后缀" if is_feature_only(pair[0], pair[-1]) else "装饰差异"
                A_lo.append((stem, k, " ｜ ".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in zs), tag))

    B_hi, B_lo = [], []
    for k, zc in glob.items():
        cs = cores(set(zc))
        if len(cs) >= 2:
            B_hi.append((k, " ｜ ".join(f"{z}×{zc[z]}" for z in cs), len(cs)))
        elif len({strip_deco(z) for z in zc}) >= 2:
            B_lo.append((k, " ｜ ".join(f"{z}×{n}" for z, n in zc.most_common()), len(zc)))
    B_hi.sort(key=lambda x: -x[2]); B_lo.sort(key=lambda x: -x[2])

    outp = os.path.join(WS, "work", "_sync-audit", f"brief-map-{proj}.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {cfg['label']} · 简报 vs 地图 地名一致性审计 v2（只读）\n")
        f.write(f"# 成品 {G}\n# 备份 {B}\n# 配对 {len(common)} · 名字对 {npair}\n\n")
        f.write("## A-HI · 同场景内译名互不包含 = 真冲突（%d）\n" % len(A_hi))
        f.write("场景\t英文\t最小核<来源>\n")
        for r in sorted(A_hi):
            f.write("\t".join(r) + "\n")
        f.write("\n## A-LO · 同场景内同核不同写法 = 低危（%d）\n" % len(A_lo))
        f.write("场景\t英文\t写法<来源>\t类型\n")
        for r in sorted(A_lo):
            f.write("\t".join(r) + "\n")
        f.write("\n## B-HI · 全局同英文多核（%d）\n" % len(B_hi))
        f.write("英文\t最小核分布\t核数\n")
        for k, v, n in B_hi:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## B-LO · 全局同核不同写法（%d）\n" % len(B_lo))
        f.write("英文\t写法分布\t写法数\n")
        for k, v, n in B_lo:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## C · 行数不平行/解码失败（%d）\n" % len(bad))
        f.write("文件\t行数\t说明\n")
        for r in bad[:400]:
            f.write("\t".join(str(x) for x in r) + "\n")

    print(f"   ⇒ A-HI 真冲突 **{len(A_hi)}** · A-LO 低危 {len(A_lo)}"
          f" · B-HI 全局多核 **{len(B_hi)}** · B-LO {len(B_lo)} · C 异常 {len(bad)}")
    print("   --- A-HI 全部 ---")
    for r in sorted(A_hi):
        print("      %-14s %-26s %s" % (r[0], r[1][:26], r[2][:72]))
    print("   --- B-HI 前 22 ---")
    for k, v, n in B_hi[:22]:
        print("      %-26s %s" % (k[:26], v[:74]))
    print(f"   明细 → {outp}")


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PROJECTS)):
        run(p)
