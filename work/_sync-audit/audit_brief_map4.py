# -*- coding: utf-8 -*-
"""只读审计 ③ v4：简报 vs 地图 **地名** 对不上号（修 v3 的两个真 bug + 地名筛选）。

v3 的两个真 bug（probe_null.py 实测发现）：
  ① 两侧文件的行尾带 `\\x00`（PeG-WW2 的 `_i.txt`/`_m.txt` 大量如此）⇒ 键变成 `message from:\\x00`，
     既绕过「UI 标签（以冒号结尾）」过滤，又让同名的 EN 键彼此**对不上**（漏报 + 假报）。
  ② 没有区分「地名」与「番号/UI 串」⇒ `ss`/`rha/`/`pt` 之类淹没真问题。

v4：先清洗控制字符，再用 `glossary\\standard-glossary.tsv` 的 cat 把键分三桶：
  place（cat 含 PLACE，真地名，出全部四张表）· other（入库但非地名，只计数）· unk（未入库，单列候选）。
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
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")  # 保留 \t(\x09) \n(\x0a) \r(\x0d)
SENT_END = re.compile(r"[.!?。！？:：]$")
HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
PAREN = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·\u3007]{0,15})\s*\(([A-Za-z][A-Za-z0-9 .'\-,]{1,34})\)")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")
LEADNUM = re.compile(r"^[\s\-–—]*\(?#?\d+\)?[\s、.．]*")
FEATURE = ("河", "山", "岛", "城", "港", "湾", "湖", "海", "铁路", "公路", "机场", "要塞", "半岛", "堡", "高地", "峡湾", "山脉")


def clean(s):
    """去掉控制字符（含行尾 NUL）后再 strip —— 这是 v3 漏掉的一步。"""
    return CTRL.sub("", s).strip()


def strip_deco(s):
    s = clean(s).strip('"“”「」')
    s = LEADNUM.sub("", s)
    s = TAILTAG.sub("", s)
    return s.strip().strip(" .,-–—、·")


def norm_en(s):
    return re.sub(r"\s+", " ", strip_deco(s)).strip(" .,-–—").lower()


def is_name_line(s):
    t = clean(s)
    return 2 <= len(t) <= 40 and bool(HAS_LETTER.search(t)) and not SENT_END.search(t) \
        and t.count(",") + t.count("，") < 2 and t.count(".") < 2


def cores(zs):
    """互不包含的**最小**核：`釜山` 是 `你在釜山` 的子串 ⇒ 只留 `釜山`；`苏昌` 与 `苏城` 互不包含 ⇒ 两个都留。"""
    cand = sorted({z for z in zs if HAS_CJK.search(z)}, key=len)
    return [z for z in cand if not any(o != z and z in o for o in cand)]


def common_suffix(zs):
    """整组中文的共同后缀（≥2 个汉字）= 简报那边的「名字」——中文语序里名字多在句尾。"""
    zs = [z for z in zs if z]
    if not zs:
        return ""
    s = min(zs, key=len)
    k = 0
    for i in range(1, len(s) + 1):
        if all(z[-i:] == s[-i:] for z in zs if len(z) >= i):
            k = i
        else:
            break
    out = s[-k:] if k else ""
    return out if (len(out) >= 2 and HAS_CJK.search(out)) else ""


def feat_only(pair):
    zs = sorted(set(pair), key=len)
    if len(zs) < 2:
        return False
    s = zs[0]
    return all(z != s and z.startswith(s) and z[len(s):] in FEATURE for z in zs[1:])


def load_cats():
    """glossary 主库 en -> {cat}（跨 scope 取并集）。"""
    p = os.path.join(WS, "glossary", "standard-glossary.tsv")
    cats = collections.defaultdict(set)
    hdr = None
    with io.open(p, encoding="utf-8-sig") as f:
        for ln in f:
            if ln.startswith("#") or not ln.strip():
                continue
            c = ln.rstrip("\r\n").split("\t")
            if hdr is None:
                hdr = c
                try:
                    ie, ic = c.index("en"), c.index("cat")
                except ValueError:
                    ie, ic = 0, 2
                continue
            if len(c) > max(ie, ic):
                cats[norm_en(c[ie])].add(c[ic].strip().upper())
    return cats, hdr


CATS, HDR = load_cats()


BADCAT = {"UNIT", "EQUIP", "LEADER", "NATION"}


def bucket(k):
    """place = 可信地名。⚠️ 主库里 `ss`/`pt`/`longest path:` 这类 **UI 标签与番号**也被错标成 PLACE
    （`ss`=PLACE+UNIT、`longest path:`=PLACE）⇒ 再加三道「不像地名」的护栏，把它们降到 other。"""
    c = CATS.get(k)
    if not c:
        return "unk"
    if "PLACE" not in c:
        return "other"
    if len(k) < 3 or k.endswith(":") or k.endswith("/") or k.startswith("/") or (c & BADCAT):
        return "other"
    return "place"


def run(proj):
    cfg = PROJECTS[proj]
    G, B = cfg["game"], cfg["back"]
    if not (os.path.isdir(G) and os.path.isdir(B)):
        print(f"⛔ 缺目录 {G} / {B}")
        return
    gset = {x.lower(): x for x in os.listdir(G)}
    bset = {x.lower(): x for x in os.listdir(B)}
    common = sorted(set(gset) & set(bset))
    print("=" * 78)
    print(f"### {cfg['label']}   配对 {len(common)}（成品 {len(gset)} / 备份 {len(bset)}）")

    map_zh = collections.defaultdict(set)
    side_zh = collections.defaultdict(lambda: collections.defaultdict(set))
    side_all = collections.defaultdict(lambda: collections.defaultdict(set))
    n_map = n_side = n_trim = 0
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
            e, z = bl[i], gl[i]
            if CTRL.search(e) or CTRL.search(z):
                n_trim += 1
            if not (clean(e) and clean(z) and is_name_line(e) and HAS_CJK.search(z)):
                continue
            k = norm_en(e)
            if not k:
                continue
            if is_map:
                map_zh[k].add(strip_deco(z)); n_map += 1
            else:
                side_zh[(stem, k)][strip_deco(z)].add(ccls)
                side_all[k][strip_deco(z)].add(ccls); n_side += 1
        if not is_map:
            for m in PAREN.finditer(gt):
                k = norm_en(m.group(2))
                z = strip_deco(m.group(1))
                if k and HAS_CJK.search(z):
                    side_zh[(stem, k)][z].add(ccls)
                    side_all[k][z].add(ccls); n_side += 1
    buckets = collections.Counter(bucket(k) for k in map_zh)
    print(f"   地图侧名字对 {n_map} · 简报侧名字对 {n_side} · 行内被清洗过控制字符 {n_trim}")
    print(f"   地图上出现的不同地名 {len(map_zh)} ⇒ 桶: place {buckets['place']} · other {buckets['other']} · unk {buckets['unk']}")

    HI, LO, NOISE, UNK = [], [], [], []
    for (stem, k), zs in sorted(side_zh.items()):
        if k not in map_zh:
            continue
        mz = map_zh[k]
        hit_hi, hit_lo = [], []
        for z in zs:
            for m in mz:
                if z == m:
                    continue
                (hit_lo if (z in m or m in z) else hit_hi).append((m, z))
        if not (hit_hi or hit_lo):
            continue
        txt = "地图: " + "｜".join(sorted(mz)) + "   ⇄   简报: " + \
              "｜".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in sorted(zs))
        b = bucket(k)
        if b == "place":
            (HI if hit_hi else LO).append((stem, k, txt))
        elif b == "unk":
            UNK.append((k, txt, len(cores(set(zs) | mz))))
        else:
            NOISE.append((k, txt))

    BHI, BLO = [], []
    for k, zs in sorted(side_all.items()):
        if k not in map_zh or bucket(k) != "place":
            continue
        mz = map_zh[k]
        suf = common_suffix(list(zs))
        uniq = {strip_deco(z) for z in set(zs) | mz}
        if suf:
            if any(suf in m or m in suf for m in mz):
                continue                      # 简报的名字与地图名兼容 ⇒ 正常
            src = f"地图: {'｜'.join(sorted(mz))}   ⇄   简报: {suf}"
            BHI.append((k, src, 2))
        else:
            cs = cores(set(zs) | mz)
            if len(cs) >= 2:
                src = " ｜ ".join(f"{z}<{','.join(sorted(zs.get(z, {'M'})))}>" for z in sorted(set(zs) | mz))
                BHI.append((k, src, len(cs)))
            elif len(uniq) >= 2 and not feat_only(set(zs) | mz):
                BLO.append((k, " ｜ ".join(sorted(uniq)), len(uniq)))
    BHI.sort(key=lambda x: -x[2])

    outp = os.path.join(WS, "work", "_sync-audit", f"brief-map-{proj}.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {cfg['label']} · 简报 vs 地图【地名】一致性审计 v4（只读）\n")
        f.write(f"# 成品 {G}\n# 备份 {B}\n")
        f.write(f"# 地图侧名字对 {n_map} · 简报侧 {n_side} · 地图上不同地名 {len(map_zh)}\n")
        f.write(f"# 桶: place {buckets['place']} · other（入库非地名）{buckets['other']} · unk（未入库）{buckets['unk']}\n\n")
        f.write("## A-HI · 同场景「地图名 ⇄ 简报名」互不包含 = 真对不上号（%d）\n" % len(HI))
        f.write("场景\t英文\t对照\n")
        for r in sorted(HI):
            f.write("\t".join(r) + "\n")
        f.write("\n## A-LO · 同场景内一方是另一方的子串（散文包裹/地貌后缀）（%d）\n" % len(LO))
        f.write("场景\t英文\t对照\n")
        for r in sorted(LO):
            f.write("\t".join(r) + "\n")
        f.write("\n## B-HI · 全局：地图上出现的地名有多个互不包含的中文（%d）\n" % len(BHI))
        f.write("英文\t译名分布<来源M地图/B简报/P简报>\t核数\n")
        for k, v, n in BHI:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## B-LO · 全局：同核不同写法（%d）\n" % len(BLO))
        f.write("英文\t写法\t数\n")
        for k, v, n in BLO:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## U · 未入库英文（不在 glossary 主库）候选（%d）\n" % len(UNK))
        f.write("英文\t对照\t核数\n")
        for k, v, n in sorted(UNK, key=lambda x: -x[2]):
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## N · 入库但非地名（番号/UI/装备）· 仅留档（%d）\n" % len(NOISE))
        f.write("英文\t对照\n")
        for k, v in NOISE:
            f.write("\t".join([k, v]) + "\n")

    print(f"   ⇒ A-HI **{len(HI)}** · A-LO {len(LO)} · B-HI **{len(BHI)}** · B-LO {len(BLO)} · U-未入库 {len(UNK)} · N-非地名 {len(NOISE)}")
    print("   --- A-HI 全部 ---")
    for r in sorted(HI):
        print("      %-14s %-24s %s" % (r[0], r[1][:24], r[2][:110]))
    print("   --- B-HI 全部 ---")
    for k, v, n in BHI:
        print("      %-24s %s" % (k[:24], v[:110]))
    print(f"   明细 → {outp}")


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PROJECTS)):
        run(p)
