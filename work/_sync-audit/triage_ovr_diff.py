# -*- coding: utf-8 -*-
"""triage_ovr_diff.py v3 — 差异词性质分类（定版）。只读。

用户 m01642 的纠正驱动本版：
  · `第1团/HG师` ↔ `第1团/赫尔曼·戈林师` = **缩写展开**（HG = Hermann Göring，**人名**），不是地名分叉
  · 列宁格勒/斯大林格勒这类**人名来源的地名仍然是地名** ⇒ 判据**对照真实地名**，不按「像不像人名」猜
  · 「番号内嵌地名」的括号里是**部队驻扎地**（`131 Ftr [Poznan]` = 驻波兹南）⇒ 属按势力/年代分叉

判据（按优先级）：
  H 场景标题行  `_m.txt` 第 0 行是场景标题，覆盖表加了「东线-03」之类的区段前缀
  I 简报散文行  `_m.txt` 里装的是整段简报（长句），两侧是不同译文 ⇒ 属简报统一，不属地名
  A 地名分叉    差异值中**至少一侧是词库 PLACE 条目的译法**，或英文键/括号内实体命中
                faction-places.tsv 或 cat==PLACE
  B 缩写/展开   一侧纯 ASCII，或两侧互为子串（HG師/赫尔曼·戈林师、RHA/2/第12皇家骑炮兵团/2）
  C 专名(非地名) 两侧中文指向同一英文实体，但该实体不是地名（人名/部队称号/装备/舰名）
  E 无法归类    其余

输出：work\\_sync-audit\\triage-ovr.tsv（全量）+ triage-place-fork.tsv（A 类，供逐条裁定）
"""
import io
import os
import re
from collections import defaultdict

W = r"D:\DSH\军事游戏汉化"
GL = os.path.join(W, "glossary")
EVID = os.path.join(GL, "evidence", "ingest-scn-ovr.tsv")
OUT = os.path.join(W, "work", "_sync-audit", "triage-ovr.tsv")
OUTP = os.path.join(W, "work", "_sync-audit", "triage-place-fork.tsv")
LAYERS = [os.path.join(GL, "layers", f) for f in
          ("common-glossary.tsv", "scope-glossary.tsv", "series-glossary.tsv")]

ASCII = re.compile(r"^[\x00-\x7f]+$")
TOKEN = re.compile(r"\[[^\]]*\]|\([^)]*\)|[^/\s\[\]()]+")
SENT = re.compile(r"[，。！？；：、]")
BRACKETED_EN = re.compile(r"\[([A-Za-z][A-Za-z'\.\- ]*)\]")
TITLE_MARK = re.compile(r"^\s*(东线|西线|北非|南线|二战|太平洋|意大利|欧洲)\s*[-–—]?\s*\d")
CJK = re.compile(r"[\u4e00-\u9fff]")
LATIN = re.compile(r"[A-Za-z]")
# 人名来源的地名（仍是地名，但要知道自己是这一类）
PERSON_PLACE = ("leningrad", "stalingrad", "kalinin", "kirov", "gorky", "kuibyshev",
                "molotov", "voroshilovgrad", "frunze", "dzerzhinsk", "zhdanov",
                "stalinogorsk", "budapest", "leninabad", "stalinabad")


def load_layers():
    z2e, e2z, cat, scopes = defaultdict(set), defaultdict(set), {}, defaultdict(set)

    def put(en, zh, ct, sc):
        z2e[zh].add(en)
        e2z[en].add(zh)
        old = cat.get(en)
        # PLACE 优先，避免被先读到的非 PLACE 行钉死
        if old is None or (old != "PLACE" and ct == "PLACE"):
            cat[en] = ct
        scopes[en].add(sc)

    for p in LAYERS:
        if not os.path.isfile(p):
            continue
        for i, l in enumerate(io.open(p, encoding="utf-8-sig")):
            if i < 2 or l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) < 4 or not c[0].strip() or not c[1].strip():
                continue
            put(c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip())
    return z2e, e2z, cat, scopes


def load_faction():
    """返回 (id -> {阵营:中文}, 英文写法小写 -> id)"""
    p = os.path.join(GL, "layers", "faction-places.tsv")
    byid, en2id = defaultdict(dict), {}
    if not os.path.isfile(p):
        return byid, en2id
    for l in io.open(p, encoding="utf-8-sig"):
        if l.startswith("#"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 5:
            continue
        pid, side, zh = c[0].strip(), c[1].strip(), c[3].strip()
        byid[pid][side] = zh
        en2id[pid.lower()] = pid
        for alt in re.split(r"[|;]", c[4]):
            a = alt.strip()
            if a:
                en2id[a.lower()] = pid
    return byid, en2id


def toks(s):
    return [t for t in TOKEN.findall(s) if t.strip()]


def bare(t):
    return t.strip().strip("[]()（）【】").strip()


def main():
    z2e, e2z, cat, scopes = load_layers()
    byid, en2id = load_faction()
    place_zh = {zh for zh, ens in z2e.items() if any(cat.get(e) == "PLACE" for e in ens)}
    fac_zh = {zh for m in byid.values() for zh in m.values()}

    rows = []
    for i, l in enumerate(io.open(EVID, encoding="utf-8")):
        if i < 4:
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 4:
            continue
        rows.append((c[0].strip(), c[1].strip(), c[2].strip(), c[3].strip()))

    detail = []
    for en, ozh, f, why in rows:
        mzh = why.split(":", 1)[1].strip() if why.startswith("映射表另有中文") else ""
        tag = f
        if why == "同键多译":
            detail.append(("F 同键多译", en, "", "", "", tag, ozh))
            continue
        # 先判散文（标题锚定只认行首，否则长散文会被误判成标题行）
        if len(mzh) > 26 or len(ozh) > 26 or SENT.search(mzh) or SENT.search(ozh):
            detail.append(("I 简报散文行", en, "%s ⇄ %s" % (mzh[:34], ozh[:34]), "", "", tag, ""))
            continue
        if TITLE_MARK.match(ozh) or TITLE_MARK.match(mzh):
            detail.append(("H 场景标题行", en, "%s ⇄ %s" % (mzh, ozh), "", "", tag, ""))
            continue

        ba = [bare(x) for x in toks(mzh)]
        bb = [bare(x) for x in toks(ozh)]
        pairs = list(zip(ba, bb)) if len(ba) == len(bb) and ba else [(mzh, ozh)]
        seen = set()
        for a, b in pairs:
            if a == b or (a, b) in seen:
                continue
            seen.add((a, b))
            common = z2e.get(a, set()) & z2e.get(b, set())
            ent = sorted(common)[0] if common else ""
            ct = cat.get(ent, "") if ent else ""
            # 英文键中的地名候选
            key_cands = [m.group(1).strip() for m in BRACKETED_EN.finditer(en)]
            k = en.strip()
            if len(k.split()) <= 2:
                key_cands.append(k)
            fac_hit = ""
            for cand in key_cands:
                if cand.lower() in en2id:
                    fac_hit = en2id[cand.lower()]
                    break
            is_place = (ct == "PLACE" or a in place_zh or b in place_zh
                        or a in fac_zh or b in fac_zh or bool(fac_hit))
            pwhy = []
            if ct == "PLACE":
                pwhy.append("cat=PLACE")
            if a in place_zh:
                pwhy.append("映射值∈PLACE译法")
            if b in place_zh:
                pwhy.append("覆盖值∈PLACE译法")
            if a in fac_zh:
                pwhy.append("映射值∈势力表")
            if b in fac_zh:
                pwhy.append("覆盖值∈势力表")
            if fac_hit:
                pwhy.append("键命中势力表:" + fac_hit)
            if is_place:
                cls, e2 = "A 地名分叉", (fac_hit or ent or (key_cands[0] if key_cands else ""))
            elif ASCII.match(a) or ASCII.match(b) or a in b or b in a or (LATIN.search(a) != LATIN.search(b) and CJK.search(a) and CJK.search(b)):
                cls, e2 = "B 缩写/展开", ent
            elif ent:
                cls, e2 = "C 专名(非地名)", ent
            else:
                cls, e2 = "E 无法归类", ""
            note = "%s ｜ %s ｜ 判据=%s" % (mzh, ozh, "+".join(pwhy) or "无")
            if e2 in byid:
                note += " ｜ 势力表 " + e2 + " => " + "/".join(
                    "%s:%s" % (s, z) for s, z in sorted(byid[e2].items()))
            detail.append((cls, en, "%s ⇄ %s" % (a, b), e2, ct, tag, note))

    with io.open(OUT, "w", encoding="utf-8") as fp:
        fp.write("类别\ten\t差异词(映射侧 ⇄ 覆盖侧)\t英文实体\tcat\t文件\t备注\n")
        for d in sorted(detail):
            fp.write("\t".join(d) + "\n")
    with io.open(OUTP, "w", encoding="utf-8") as fp:
        fp.write("英文实体\ten\t差异词\tcat\t文件\t备注\n")
        for d in sorted(d for d in detail if d[0] == "A 地名分叉"):
            fp.write("\t".join((d[3], d[1], d[2], d[4], d[5], d[6])) + "\n")

    cnt = defaultdict(int)
    for d in detail:
        cnt[d[0]] += 1
    print("=== 差异点分类（证据 %d 行 · 差异点 %d） ===" % (len(rows), len(detail)))
    for k in sorted(cnt):
        print("  %-16s %d" % (k, cnt[k]))
    print()
    a = [d for d in detail if d[0] == "A 地名分叉"]
    byent = defaultdict(set)
    for d in a:
        byent[d[3]].add(d[2])
    print("-- A 地名分叉（%d 点 / %d 个英文实体）--" % (len(a), len(byent)))
    for e in sorted(byent):
        print("   %-22s %s" % (e[:22], " ; ".join(sorted(byent[e])[:3])))
        for d in [x for x in a if x[3] == e][:1]:
            print("      %-30s %s" % (d[5][:30], d[6][:110]))
    print()

    # 人名来源的地名（用户 m01642 提醒）：这类**仍然是地名**，但要知道自己在哪一类
    print("-- 人名来源的地名检查（leningrad/stalingrad/kalinin/kuibyshev/gorky/molotov…）--")
    universe = set(byent) | set(en2id)
    hits = sorted({e for e in universe if any(p in e.lower() for p in PERSON_PLACE)})
    for e in hits:
        src = []
        if e in byent:
            src.append("差异证据表 A 类")
        if e.lower() in en2id:
            src.append("faction-places.tsv:" + en2id[e.lower()])
        print("   %-24s %s" % (e[:24], "、".join(src)))
    if not hits:
        print("   无（本次差异证据与 faction-places.tsv 内均无该类型键）")
    print()
    for want in ("C 专名(非地名)", "E 无法归类", "H 场景标题行"):
        it = [d for d in detail if d[0] == want]
        print("-- %s（%d）--" % (want, len(it)))
        for d in it[:12]:
            print("   %-30s %-28s ent=%s" % (d[1][:30], d[2][:28], d[3][:14]))
        if len(it) > 12:
            print("   ... 另 %d 条见 %s" % (len(it) - 12, OUT))
        print()


if __name__ == "__main__":
    main()
