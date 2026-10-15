# -*- coding: utf-8 -*-
"""只读审计 ③ v5（终版）：简报 vs 地图 **地名** 对不上号。

v3/v4 的判据缺陷（实测逐个修掉）：
  ① 行尾 `\\x00` 未清洗 ⇒ 键成 `message from:\\x00`，绕过 UI 标签过滤（v4 修）。
  ② A-HI 用「地图侧全局值」做笛卡尔比对 ⇒ 同场景 `德绍` 撞另一场景 `西线-09 德绍` 假报；
     地图与简报同集合（三个殖民地旅）也假报（v5 修）。
  ③ 归属用 `re.split(r"[_.]", name)[0]` ⇒ 既过度合并（`lah` 吞 141 个文件）又漏配
     （`BoB14TV`/`B709V` 找不到自己的 `_m.txt`）（v5 改为**对真实 `_m.txt` 词干做最长前缀匹配**）。
  ④ `cores()` 取极大串 ⇒ `你在釜山` 压过 `釜山`（v5 用「互相包含测试」取代）。

v5 判据统一为一条：**某中文值与地图名（互相包含测试）完全不相容**。
  A-HI = 同一场景内出现不相容值；B-HI = 全局同一英文名有 ≥2 个不相容值。
另出 M-多值：同一英文名在**地图侧**就有多个译名（含按年代/阵营合法分叉的，需人工裁定）。
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
MAPSUF = re.compile(r"(?i)_m\.txt$")
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")   # 保留 \t \n \r
SENT_END = re.compile(r"[.!?。！？:：]$")
HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
PAREN = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·\u3007]{0,15})\s*\(([A-Za-z][A-Za-z0-9 .'\-,]{1,34})\)")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")
LEADNUM = re.compile(r"^[\s\-–—]*\(?#?\d+\)?[\s、.．]*")
FEATURE = ("河", "山", "岛", "城", "港", "湾", "湖", "海", "铁路", "公路", "机场", "要塞", "半岛", "堡", "高地", "峡湾", "山脉")
BADCAT = {"UNIT", "EQUIP", "LEADER", "NATION"}


def clean(s):
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


def incompat(z, mz):
    """该中文值与地图名完全不相容（既不包含任一个地图名，也不被它们包含）。"""
    return not any(z in m or m in z for m in mz)


def feat_only(zs):
    zs = sorted(set(zs), key=len)
    if len(zs) < 2:
        return False
    s = zs[0]
    return all(z != s and z.startswith(s) and z[len(s):] in FEATURE for z in zs[1:])


def load_cats():
    p = os.path.join(WS, "glossary", "standard-glossary.tsv")
    cats = collections.defaultdict(set)
    hdr, ie, ic = None, 0, 2
    with io.open(p, encoding="utf-8-sig") as f:
        for ln in f:
            if ln.startswith("#") or not ln.strip():
                continue
            c = ln.rstrip("\r\n").split("\t")
            if hdr is None:
                hdr = c
                if "en" in c and "cat" in c:
                    ie, ic = c.index("en"), c.index("cat")
                continue
            if len(c) > max(ie, ic):
                cats[norm_en(c[ie])].add(c[ic].strip().upper())
    return cats, hdr


CATS, HDR = load_cats()


def bucket(k):
    """place = 可信地名。⚠️ 主库把 `ss`(PLACE+UNIT)/`pt`/`longest path:` 这类番号与 UI 标签也标成 PLACE
    ⇒ 再加三道「不像地名」护栏，降到 other。"""
    c = CATS.get(k)
    if not c:
        return "unk"
    if "PLACE" not in c:
        return "other"
    if len(k) < 3 or k.endswith(":") or k.endswith("/") or k.startswith("/") or (c & BADCAT):
        return "other"
    return "place"


def fmt(mz, zs, bad, cap=180):
    s = "地图: " + "｜".join(sorted(mz)) + "   ⇄   简报: "
    if isinstance(zs, dict):
        s += "｜".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in sorted(zs))
    else:
        s += "｜".join(sorted(zs))
    if bad:
        s += "   ⚠️不相容: " + "｜".join(sorted(bad))
    return s[:cap]


def skip_title(gl, bl):
    """首行（非空）通常是场景标题（`_m.txt` 第 0 行＝标题，简报第 0 行＝标题、第 1 行＝日期）。
    文件只剩 1 个非空行时不跳（可能整文件就是一个地名）。返回 None 表示不跳。"""
    n = sum(1 for x in gl if x.strip())
    if n < 2:
        return None
    for i in range(min(len(gl), len(bl))):
        if gl[i].strip() or bl[i].strip():
            return i
    return None


def read_pair(gpath, bpath):
    gt = open(gpath, "rb").read().decode("gbk", "replace")
    bt = open(bpath, "rb").read().decode("cp1252", "replace")
    return gt, bt


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

    pairs = []
    for fn in common:
        gname, bname = gset[fn], bset[fn]
        low = gname.lower()
        if low.endswith(".scn") or low.endswith(SKIP):
            continue
        pairs.append((gname, bname, low))

    # 第一遍：地图侧（真实 `_m.txt`），词干 = 去掉 `_m.txt`；并登记词干清单
    map_zh = collections.defaultdict(set)                 # en -> {zh}
    map_seq = collections.defaultdict(set)                # (pid,en) -> {zh}
    seqs, n_map, n_trim = set(), 0, 0
    for gname, bname, low in pairs:
        if not MAPSUF.search(gname):
            continue
        gt, bt = read_pair(os.path.join(G, gname), os.path.join(B, bname))
        n_trim += len([1 for s in (gt, bt) if CTRL.search(s)])
        pid = MAPSUF.sub("", gname)
        seqs.add(pid)
        gl, bl = re.split(r"\r\n|\r|\n", gt), re.split(r"\r\n|\r|\n", bt)
        skip = skip_title(gl, bl)                        # ⭐ `_m.txt` 第 0 行通常是场景标题
        for i, (e, z) in enumerate(zip(bl, gl)):
            if i == skip:
                continue
            if not (clean(e) and clean(z) and is_name_line(e) and HAS_CJK.search(z)):
                continue
            k = norm_en(e)
            if k:
                map_zh[k].add(strip_deco(z))
                map_seq[(pid, k)].add(strip_deco(z))
                n_map += 1
    seqs = sorted(seqs, key=len, reverse=True)            # 最长前缀优先

    def pid_of(base):
        for s in seqs:
            if base.lower().startswith(s.lower()):
                return s
        return None

    # 第二遍：简报侧，按最长前缀归属到场景
    side_seq = collections.defaultdict(lambda: collections.defaultdict(set))   # (pid,en) -> zh -> cls
    side_all = collections.defaultdict(lambda: collections.defaultdict(set))   # en -> zh -> cls
    n_side = n_orphan = 0
    for gname, bname, low in pairs:
        if MAPSUF.search(gname):
            continue
        gt, bt = read_pair(os.path.join(G, gname), os.path.join(B, bname))
        pid = pid_of(gname)
        if pid is None:
            n_orphan += 1
        ccls = "P" if low.endswith(".ply") else "B"
        gl, bl = re.split(r"\r\n|\r|\n", gt), re.split(r"\r\n|\r|\n", bt)
        skip = skip_title(gl, bl)
        for i in range(min(len(gl), len(bl))):
            if i == skip:
                continue
            e, z = bl[i], gl[i]
            if not (clean(e) and clean(z) and is_name_line(e) and HAS_CJK.search(z)):
                continue
            k = norm_en(e)
            if not k:
                continue
            z = strip_deco(z)
            side_seq[(pid, k)][z].add(ccls)
            side_all[k][z].add(ccls)
            n_side += 1
        for m in PAREN.finditer(gt):
            k, z = norm_en(m.group(2)), strip_deco(m.group(1))
            if k and HAS_CJK.search(z):
                side_seq[(pid, k)][z].add(ccls)
                side_all[k][z].add(ccls)
                n_side += 1

    buckets = collections.Counter(bucket(k) for k in map_zh)
    print(f"   地图文件 {len(seqs)} 个场景词干 · 地图侧名字对 {n_map} · 简报侧名字对 {n_side}")
    print(f"   含控制字符被清洗的文件 {n_trim} · 无对应地图词干的简报文件 {n_orphan}")
    print(f"   地图上出现的不同英文名 {len(map_zh)} ⇒ 桶: place {buckets['place']} · other {buckets['other']} · unk {buckets['unk']}")

    HI, LO, NOISE, UNK = [], [], [], []
    for (pid, k), zs in sorted(side_seq.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
        if k not in map_zh:
            continue
        b = bucket(k)
        if b == "other":
            NOISE.append((k, fmt(map_seq.get((pid, k), map_zh[k]), zs, [])))
            continue
        mz = map_seq.get((pid, k)) or map_zh[k]           # ⭐ 该场景自己的地图名，取不到才回退全局
        bad = [z for z in zs if incompat(z, mz)]
        if bad:
            (HI if b == "place" else UNK).append((pid or "(无)", k, fmt(mz, zs, bad)))
        elif len({z for z in set(zs) | mz}) >= 2 and not feat_only(set(zs) | mz):
            LO.append((pid or "(无)", k, fmt(mz, zs, [])))

    BHI, BLO = [], []
    for k, zs in sorted(side_all.items()):
        if k not in map_zh or bucket(k) != "place":
            continue
        bad = [z for z in zs if incompat(z, map_zh[k])]
        if len(bad) >= 2:
            BHI.append((k, fmt(map_zh[k], zs, bad), len(bad)))
        elif len({z for z in set(zs) | map_zh[k]}) >= 2 and not feat_only(set(zs) | map_zh[k]):
            BLO.append((k, " ｜ ".join(sorted(set(zs) | map_zh[k])), len(set(zs) | map_zh[k])))
    BHI.sort(key=lambda x: -x[2])

    MDUP = []                                              # 地图侧自身多值
    for k, zs in sorted(map_zh.items()):
        if len(zs) >= 2:
            who = collections.defaultdict(list)
            for (pid, kk), vs in map_seq.items():
                if kk == k:
                    who[pid] = sorted(vs)
            MDUP.append((k, "｜".join(sorted(zs)), len(who), bucket(k)))

    outp = os.path.join(WS, "work", "_sync-audit", f"brief-map-{proj}.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {cfg['label']} · 简报 vs 地图【地名】一致性审计 v5（只读）\n")
        f.write(f"# 成品 {G}\n# 备份 {B}\n")
        f.write(f"# 地图文件（场景词干）{len(seqs)} · 地图侧名字对 {n_map} · 简报侧 {n_side} · 无对应地图词干的简报文件 {n_orphan}\n")
        f.write(f"# 地图上不同英文名 {len(map_zh)} · 桶 place {buckets['place']} / other {buckets['other']} / unk {buckets['unk']}\n")
        f.write("# 判据：某中文值与**该场景自己的**地图名互相都不包含 = 对不上号\n\n")
        f.write("## A-HI · 同场景真对不上号（入库地名）（%d）\n场景\t英文\t对照\n" % len(HI))
        for r in sorted(HI):
            f.write("\t".join(r) + "\n")
        f.write("\n## B-HI · 全局：同一英文名有 ≥2 个不相容译名（%d）\n英文\t对照\t不相容数\n" % len(BHI))
        for k, v, n in BHI:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## M-DUP · 地图侧自身就有多译名（%d；含按年代/阵营合法分叉，需人工裁定）\n英文\t地图译名\t涉及场景数\t桶\n" % len(MDUP))
        for k, v, n, b in MDUP:
            f.write("\t".join([k, v, str(n), b]) + "\n")
        f.write("\n## U-HI · 同场景真对不上号（**未入库**，需人工判是否地名）（%d）\n场景\t英文\t对照\n" % len(UNK))
        for r in sorted(UNK):
            f.write("\t".join(r) + "\n")
        f.write("\n## A-LO · 同场景一侧是另一侧的子串（散文包裹/地貌后缀/括号体例）（%d）\n场景\t英文\t对照\n" % len(LO))
        for r in sorted(LO):
            f.write("\t".join(r) + "\n")
        f.write("\n## B-LO · 全局同核不同写法（%d）\n英文\t写法\t数\n" % len(BLO))
        for k, v, n in BLO:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## N · 入库但非地名（番号/UI/装备）· 仅留档（%d）\n英文\t对照\n" % len(NOISE))
        for k, v in NOISE:
            f.write("\t".join([k, v]) + "\n")

    print(f"   ⇒ A-HI **{len(HI)}** · B-HI **{len(BHI)}** · M-DUP {len(MDUP)} · U-HI {len(UNK)} · A-LO {len(LO)} · B-LO {len(BLO)} · N {len(NOISE)}")
    print("   --- A-HI 全部 ---")
    for r in sorted(HI):
        print("      %-16s %-20s %s" % (r[0][:16], r[1][:20], r[2][:132]))
    print("   --- B-HI 全部 ---")
    for k, v, n in BHI:
        print("      %-20s %s" % (k[:20], v[:134]))
    print(f"   --- M-DUP 前 40 / 共 {len(MDUP)} ---")
    for k, v, n, b in MDUP[:40]:
        print("      %-22s %-34s 场景%2d  %s" % (k[:22], v[:34], n, b))
    print(f"   明细 → {outp}")


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PROJECTS)):
        run(p)
