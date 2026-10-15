# -*- coding: utf-8 -*-
"""只读审计 ③：简报 vs 地图 地名对不上号。

方法（英文备份做对齐键）：
  1. 对每个成对文件（成品中文 ↔ 备份英文，同名）：
     - **地图侧** = `<stem>_m.txt`（地图名栏，纯译、不加原文括号）
     - **简报侧** = 其余 .txt/.TXT（说明/简报/单位资料标题…）
  2. 取**短行**（≤40 字符、无句末标点、含字母）作「名字对」：英文行 ↔ 中文行（行号一一对应）。
  3. 再从中文侧解析 `中文(English)` 括号对，补「简报侧」的名字对。
  4. 以规范化英文为键聚合 ⇒ 同一英文名在同一场景里出现 >1 种中文 = 对不上号。

产出：work/_sync-audit/brief-map-<proj>.tsv + 控制台摘要。
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
        enc_game="gbk", enc_back="cp1252",
    ),
    "pegww2": dict(
        label="PeG-WW2",
        game=r"D:\Program Files\PeG-WW2\SCENARIO",
        back=os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO"),
        enc_game="gbk", enc_back="cp1252",
    ),
    "pegww2u": dict(
        label="PeG-WW2 · USERSCEN",
        game=r"D:\Program Files\PeG-WW2\USERSCEN",
        back=os.path.join(WS, "pegww2", "testbed", "backup", "USERSCEN"),
        enc_game="gbk", enc_back="cp1252",
    ),
}

SENT_END = re.compile(r"[.!?。！？:：]$")
HAS_LETTER = re.compile(r"[A-Za-z]")
PAREN = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·\u3007]{0,15})\s*\(([A-Za-z][A-Za-z0-9 .'\-,]{1,34})\)")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")


def norm_en(s):
    s = s.strip().strip('"').strip()
    s = TAILTAG.sub("", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().strip(" .,-–—").lower()


def is_short_name(s):
    t = s.strip()
    if not (2 <= len(t) <= 40):
        return False
    if not HAS_LETTER.search(t):
        return False
    if SENT_END.search(t):
        return False
    if t.count(",") + t.count("，") >= 2:
        return False
    if t.count(".") >= 2:
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


def run(proj):
    cfg = PROJECTS[proj]
    G, B = cfg["game"], cfg["back"]
    if not os.path.isdir(G):
        print(f"⛔ {G} 不存在"); return
    if not os.path.isdir(B):
        print(f"⛔ 备份 {B} 不存在"); return
    gset = {x.lower(): x for x in os.listdir(G)}
    bset = {x.lower(): x for x in os.listdir(B)}
    common = sorted(set(gset) & set(bset))
    print("=" * 78)
    print(f"### {cfg['label']}")
    print(f"   成品 {len(gset)} 文件 · 备份 {len(bset)} · 同名配对 {len(common)}")
    only_g = len(set(gset) - set(bset)); only_b = len(set(bset) - set(gset))
    print(f"   仅成品 {only_g} · 仅备份 {only_b}")

    # (scenario, 英文) -> {中文: set(类别)}
    seen = collections.defaultdict(lambda: collections.defaultdict(set))
    # 全局：英文 -> {中文: 计数}
    glob = collections.defaultdict(collections.Counter)
    npair = 0
    lines_mismatch = []

    for fn in common:
        gname, bname = gset[fn], bset[fn]
        gp, bp = os.path.join(G, gname), os.path.join(B, bname)
        try:
            gt = open(gp, "rb").read().decode(cfg["enc_game"], "replace")
            bt = open(bp, "rb").read().decode(cfg["enc_back"], "replace")
        except Exception as e:
            lines_mismatch.append((gname, "decode-fail", str(e)))
            continue
        if gname.lower().endswith(".scn"):
            continue
        gl = re.split(r"\r\n|\r|\n", gt)
        bl = re.split(r"\r\n|\r|\n", bt)
        if len(gl) != len(bl):
            lines_mismatch.append((gname, f"{len(bl)}→{len(gl)}", "行数不平行"))
        stem = gname.split("_")[0].split(".")[0]
        cc = cls_of(gname)
        # a) 行对齐的短名对
        for i in range(min(len(gl), len(bl))):
            e, z = bl[i].strip(), gl[i].strip()
            if not e or not z:
                continue
            if is_short_name(e) and z and re.search(r"[\u4e00-\u9fff]", z):
                k = norm_en(e)
                if k:
                    seen[(stem, k)][z].add(cc)
                    glob[k][z] += 1
                    npair += 1
        # b) 中文侧括号对 `中文(English)`
        for m in PAREN.finditer(gt):
            z, e = m.group(1).strip(), m.group(2).strip()
            k = norm_en(e)
            if k:
                seen[(stem, k)][z].add(cc)
                glob[k][z] += 1
                npair += 1

    print(f"   收集名字对 {npair} 条（行对齐短名 + 括号对）")

    # 冲突 A：同场景同英文 → 多中文
    A = []
    for (stem, k), zs in seen.items():
        if len(zs) < 2:
            continue
        # 只保留跨越「地图侧」与「简报侧」的冲突
        mz = {z for z, cs in zs.items() if any(c.startswith("M") for c in cs)}
        bz = {z for z, cs in zs.items() if any(not c.startswith("M") for c in cs)}
        if mz and bz and not (mz & bz):
            A.append((stem, k, " ｜ ".join(f"{z}<{','.join(sorted(zs[z]))}>" for z in sorted(zs)), "跨地图/简报"))

    # 冲突 B：全局同英文 → 多中文（含地图侧与简报侧）
    Bc = []
    for k, zc in glob.items():
        if len(zc) < 2:
            continue
        Bc.append((k, " ｜ ".join(f"{z}×{n}" for z, n in zc.most_common()), len(zc)))
    Bc.sort(key=lambda x: -x[2])

    outp = os.path.join(WS, "work", "_sync-audit", f"brief-map-{proj}.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {cfg['label']} · 简报 vs 地图 地名一致性审计（只读）\n")
        f.write(f"# 成品 {G}\n# 备份 {B}\n")
        f.write(f"# 同名配对 {len(common)} · 名字对 {npair}\n\n")
        f.write("## A · 同场景内「地图侧 vs 简报侧」译名不一致（%d 条）\n" % len(A))
        f.write("场景\t英文(归一)\t各侧译名<来源类别>\t类型\n")
        for r in sorted(A):
            f.write("\t".join(r) + "\n")
        f.write("\n## B · 全局「同一英文名多个中文」（%d 条，含跨场景）\n" % len(Bc))
        f.write("英文(归一)\t译名分布\t译名数\n")
        for k, v, n in Bc:
            f.write("\t".join([k, v, str(n)]) + "\n")
        f.write("\n## C · 行数不平行/解码失败（%d 条）\n" % len(lines_mismatch))
        f.write("文件\t行数\t说明\n")
        for r in lines_mismatch[:400]:
            f.write("\t".join(str(x) for x in r) + "\n")

    print(f"   ⇒ A 同场景 地图↔简报 冲突：**{len(A)}** 条")
    for r in sorted(A)[:25]:
        print("      %-14s %-30s %s" % (r[0], r[1][:30], r[2][:70]))
    print(f"   ⇒ B 全局同英文多中文：**{len(Bc)}** 条（前 10）")
    for k, v, n in Bc[:10]:
        print("      %-28s %s" % (k[:28], v[:70]))
    print(f"   ⇒ C 行数不平行/解码失败：{len(lines_mismatch)} 条")
    print(f"   明细 → {outp}")


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PROJECTS)):
        run(p)
