# -*- coding: utf-8 -*-
"""只读审计 ③ v3：简报 vs 地图 **地名** 对不上号（只留地图上真有的地名）。

v2 的错：`_u.txt`（单位资料）里成百上千条**番号**也被当名字对 ⇒ 满屏假冲突。
v3：① 只收 `_m.txt`（地图名栏）作「地图侧」；② 只收简报类文件（排除 `_m/_u/_n`）作「简报侧」；
    ③ **只报地图侧真出现过的英文键**；④ 冲突判据 = 两侧中文**互不包含**。
"""
import os
import re
import io
import sys
import collections

WS = r"D:\DSH\军事游戏汉化"
PROJECTS = {
    "peg": dict(label="PeG（前作）", game=r"D:\Program Files\PeG\Scenario",
                back=os.path.join(WS, "peg", "testbed", "backup", "Scenario")),
    "pegww2": dict(label="PeG-WW2", game=r"D:\Program Files\PeG-WW2\SCENARIO",
                   back=os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")),
    "pegww2u": dict(label="PeG-WW2 · USERSCEN", game=r"D:\Program Files\PeG-WW2\USERSCEN",
                    back=os.path.join(WS, "pegww2", "testbed", "backup", "USERSCEN")),
}
SKIP = ("_u.txt", "_n.txt")
SENT_END = re.compile(r"[.!?。！？:：]$")
HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
PAREN = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·\u3007]{0,15})\s*\(([A-Za-z][A-Za-z0-9 .'\-,]{1,34})\)")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")
LEADNUM = re.compile(r"^[\s\-–—]*\(?#?\d+\)?[\s、.．]*")
FEATURE = ("河", "山", "岛", "城", "港", "湾", "湖", "海", "铁路", "公路", "机场", "要塞", "半岛", "堡", "高地", "峡湾", "山脉")


def strip_deco(s):
    s = s.strip().strip('"“”「」')
    s = LEADNUM.sub("", s)
    s = TAILTAG.sub("", s)
    return s.strip().strip(" .,-–—、·")


def norm_en(s):
    return re.sub(r"\s+", " ", strip_deco(s)).strip(" .,-–—").lower()


def is_name_line(s):
    t = s.strip()
    return 2 <= len(t) <= 40 and bool(HAS_LETTER.search(t)) and not SENT_END.search(t) \
        and t.count(",") + t.count("，") < 2 and t.count(".") < 2


def cores(zs):
    cand = sorted({z for z in zs if HAS_CJK.search(z)}, key=len)
    return [z for z in cand if not any(z != o and z in o for o in cand)]


def feat_only(pair):
    """整组只差一个地貌/设施后缀？（取最短者为基，其余都=基+后缀）"""
    zs = sorted(set(pair), key=len)
    if len(zs) < 2:
        return False
    s = zs[0]
    return all(z != s and z.startswith(s) and z[len(s):] in FEATURE for z in zs[1:])


def run(proj):
    cfg = PROJECTS[proj]
    G, B = cfg["game"], cfg["back"]
    if not (os.path.isdir(G) and os.path.isdir(B)):
        print(f"⛔ 缺目录 {G} / {B}"); return
    gset = {x.lower(): x for x in os.listdir(G)}
    bset = {x.lower(): x for x in os.listdir(B)}
    common = sorted(set(gset) & set(bset))
    print("=" * 78)
    print(f"### {cfg['label']}   配对 {len(common)}（成品 {len(gset)} / 备份 {len(bset)}）")

    map_zh = collections.defaultdict(set)      # en -> {zh}
    side_zh = collections.defaultdict(lambda: collections.defaultdict(set))  # (stem,en) -> zh -> classes
    side_all = collections.defaultdict(lambda: collections.defaultdict(set))  # en -> zh -> classes
    n_map = n_side = 0
    for fn in common:
        gname, bname = gset[fn], bset[fn]
        low = gname.lower()
        if low.endswith(".scn") or low.endswith(SKIP):
            continue
        try:
            gt = open(os.path.join(G, gname), "rb").read().decode("gbk", "replace")
            bt = open(os.path.join(B, bname), "rb").read().decode("cp1252", "replace")
        except Exception:
            continue
        is_map = low.endswith("_m.txt")
        gl, bl = re.split(r"\r\n|\r|\n", gt), re.split(r"\r\n|\r|\n", bt)
        stem = re.split(r"[_.]", gname)[0]
        ccls = "M" if is_map else ("P" if low.endswith(".ply") else "B")
        for i in range(min(len(gl), len(bl))):
            e, z = bl[i].strip(), gl[i].strip()
            if not (e and z and is_name_line(e) and HAS_CJK.search(z)):
                continue
            k = norm_en(e)
            if not k:
                continue
            if is_map:
                map_zh[k].add(strip_deco(z)); n_map += 1
            else:
                side_zh[(stem, k)][strip_deco(z)].add(ccls)
                side_all[k][strip_deco(z)].add(ccls); n_side += 1
        if not is_map:  # 中文侧括号对（简报加原文括号的体例）
            for m in PAREN.finditer(gt):
                k = norm_en(m.group(2))
                z = strip_deco(m.group(1))
                if k and HAS_CJK.search(z):
                    side_zh[(stem, k)][z].add(ccls)
                    side_all[k][z].add(ccls); n_side += 1
    print(f"   地图侧名字对 {n_map} · 简报侧名字对 {n_side} · 地图上出现的不同地名 {len(map_zh)}")

    HI, LO = [], []
    for (stem, k), zs in sorted(side_zh.items()):
        if k not in map_zh:
            continue
        mz = map_zh[k]
        hit_hi, hit_lo = [], []
        for z in zs:
            for m in mz:
                if z == m:
                    continue
                if z in m or m in z:
                    hit_lo.append((m, z))
                else:
                    hit_hi.append((m, z))
        if hit_hi:
            HI.append((stem, k,
                       "地图: " + "｜".join(sorted(mz)) + "   ⇄   简报: " +
                       "｜".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in sorted(zs))))
        elif hit_lo:
            LO.append((stem, k, "地图: " + "｜".join(sorted(mz)) + "   ⇄   简报: " +
                       "｜".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in sorted(zs))))

    BHI, BLO = [], []
    for k, zs in sorted(side_all.items()):
        if k not in map_zh:
            continue
        allz = set(zs) | map_zh[k]
        cs = cores(allz)
        if len(cs) >= 2:
            src = " ｜ ".join(f"{z}<{','.join(sorted(zs.get(z, {'M'})))}>" for z in sorted(allz))
            BHI.append((k, src, len(cs)))
        elif len({strip_deco(z) for z in allz}) >= 2 and not feat_only(allz):
            src = " ｜ ".join(f"{z}" for z in sorted(allz))
            BLO.append((k, src, len(allz)))
    BHI.sort(key=lambda x: -x[2])

    outp = os.path.join(WS, "work", "_sync-audit", f"brief-map-{proj}.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {cfg['label']} · 简报 vs 地图【地名】一致性审计 v3（只读）\n")
        f.write(f"# 成品 {G}\n# 备份 {B}\n")
        f.write(f"# 地图侧名字对 {n_map} · 简报侧 {n_side} · 地图上不同地名 {len(map_zh)}\n\n")
        f.write("## A-HI · 同场景「地图名 ⇄ 简报名」互不包含 = 真对不上号（%d）\n" % len(HI))
        f.write("场景\t英文\t对照\n")
        for r in sorted(HI):
            f.write("\t".join(r) + "\n")
        f.write("\n## A-LO · 同场景内一方是另一方的子串（散文包裹/地貌后缀）（%d）\n" % len(LO))
        f.write("场景\t英文\t对照\n")
        for r in sorted(LO):
            f.write("\t".join(r) + "\n")
        f.write("\n## B-HI · 全局：地图上出现的英文名有多个互不包含的中文（%d）\n" % len(BHI))
        f.write("英文\t译名分布<来源M地图/B简报/P简报>\t核数\n")
        for k, v, n in BHI:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## B-LO · 全局：同核不同写法（%d）\n" % len(BLO))
        f.write("英文\t写法\t数\n")
        for k, v, n in BLO:
            f.write("\t".join([k, v, str(n)]) + "\n")

    print(f"   ⇒ A-HI **{len(HI)}** · A-LO {len(LO)} · B-HI **{len(BHI)}** · B-LO {len(BLO)}")
    print("   --- A-HI 全部 ---")
    for r in sorted(HI):
        print("      %-14s %-24s %s" % (r[0], r[1][:24], r[2][:88]))
    print("   --- B-HI 全部 ---")
    for k, v, n in BHI:
        print("      %-24s %s" % (k[:24], v[:88]))
    print(f"   明细 → {outp}")


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PROJECTS)):
        run(p)
