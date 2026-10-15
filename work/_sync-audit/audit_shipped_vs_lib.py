# -*- coding: utf-8 -*-
"""只读审计 ②：**成品用词 vs 新词库** —— PeG / PeG-WW2 的汉化还需不需要按新词库更新？

方法：把成品文件与英文备份按行配对（成品 GBK / 备份 cp1252），
  · 英文键归一后在**词库 PEG* scope** 里查得到，且成品中文**不包含**该键的任何词库译名 ⇒ 计入「冲突」；
  · 再对 docs/43 第三组 12 组「库仍旧名 / 分支新名」逐组数成品用量。
只读，不写游戏文件。
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
}
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
SENT_END = re.compile(r"[.!?。！？:：]$")
TAILTAG = re.compile(r"[\s\-–—,，]*\(?#?\d+\)?[\s]*$")
LEADNUM = re.compile(r"^[\s\-–—]*\(?#?\d+\)?[\s、.．]*")
# docs/43 §三 第三组：英文键 → (库里旧名, 分支新名)
THIRD = [
    ("Kuri", "库里", "九里"),
    ("Morotsu", "诸塚", "诸津"),
    ("Chio", "奇奥", "千绪"),
    ("Naikawa", "奈川", "内川"),
    ("Burnoshevo Russkoye", "俄罗斯科耶", "鲁斯科耶"),
    ("Toro", "土路", "塔路"),
    ("Chiwagai", "千早", "奇瓦盖"),
    ("Okutai-gawa River", "奥体川", "奥库泰河"),
    ("Chingyong", "镇永", "进永"),
    ("Chinyong", "镇永", "进永"),
    ("Hatsutai", "初代", "哈茨泰"),
    ("Acroma", "阿克罗马", "阿克罗玛"),
    ("Wolzskij", "沃尔日斯基", "伏尔加斯基"),
    ("Volzhshiy", "沃尔日斯基", "伏尔加斯基"),
]
AMUR = ("阿穆尔河", "黑龙江")
SKIP = ("_u.txt", "_n.txt")


def clean(s):
    return CTRL.sub("", s).strip()


def strip_deco(s):
    s = clean(s).strip('"“”「」')
    s = LEADNUM.sub("", s)
    s = TAILTAG.sub("", s)
    return s.strip().strip(" .,-–—、·")


def norm_en(s):
    return re.sub(r"\s+", " ", strip_deco(s)).strip(" .,-–—").lower()


def is_term_line(s):
    t = clean(s)
    return 2 <= len(t) <= 60 and bool(HAS_LETTER.search(t)) and not SENT_END.search(t) \
        and t.count(",") + t.count("，") < 3 and t.count(".") < 3


def load_lib():
    """PEG* scope 的词库条目：en_norm -> {zh}，并记 scope/来源文件。"""
    lib = collections.defaultdict(set)
    where = collections.defaultdict(set)
    conf_of = collections.defaultdict(set)
    files = [os.path.join(WS, "glossary", "standard-glossary.tsv"),
             os.path.join(WS, "glossary", "layers", "common-glossary.tsv"),
             os.path.join(WS, "glossary", "layers", "scope-glossary.tsv")]
    total = kept = 0
    for p in files:
        if not os.path.exists(p):
            continue
        base = os.path.basename(p)
        with io.open(p, encoding="utf-8-sig") as f:
            for ln in f:
                if not ln.strip() or ln.startswith("#"):
                    continue
                c = ln.rstrip("\r\n").split("\t")
                if len(c) < 4 or c[0] == "en":
                    continue
                total += 1
                scope = c[3].strip()
                if not scope.upper().startswith("PEG"):
                    continue
                en, zh = norm_en(c[0]), strip_deco(c[1])
                if not (en and zh):
                    continue
                lib[en].add(zh)
                where[en].add(f"{scope}@{base}")
                conf_of[en].add(c[6].strip().upper() if len(c) > 6 else "")
                kept += 1
    return lib, where, conf_of, total, kept


LIB, WHERE, CONF, TOT, KEPT = load_lib()


def kind_of(k):
    """冲突性质：keep=词库就是原样保留（zh==英文）；abbr=番号/政策类；real=真需裁定。"""
    vals = LIB[k]
    if all(strip_deco(v).lower() == k for v in vals):
        return "keep"
    if CONF[k] and CONF[k] <= {"ABBR", "POLICY", "LOW"}:
        return "abbr"
    return "real"


def scan(proj, want_third):
    cfg = PROJECTS[proj]
    G, B = cfg["game"], cfg["back"]
    gset = {x.lower(): x for x in os.listdir(G)}
    bset = {x.lower(): x for x in os.listdir(B)}
    common = sorted(set(gset) & set(bset))
    print("=" * 78)
    print(f"### {cfg['label']}   配对 {len(common)}")
    hits = collections.Counter()          # (en, shipped_zh) -> n
    files_of = collections.defaultdict(set)
    nline = 0
    third_cnt = collections.Counter()     # (en, variant) -> (n, files)
    third_files = collections.defaultdict(set)
    amur_cnt = collections.Counter()
    amur_files = collections.defaultdict(set)
    for fn in common:
        gname, bname = gset[fn], bset[fn]
        if gname.lower().endswith(".scn") or gname.lower().endswith(SKIP):
            continue
        try:
            gt = open(os.path.join(G, gname), "rb").read().decode("gbk", "replace")
            bt = open(os.path.join(B, bname), "rb").read().decode("cp1252", "replace")
        except Exception:
            continue
        gl, bl = re.split(r"\r\n|\r|\n", gt), re.split(r"\r\n|\r|\n", bt)
        for i in range(min(len(gl), len(bl))):
            e, z = clean(bl[i]), strip_deco(gl[i])
            if not (e and z and is_term_line(e) and HAS_CJK.search(z)):
                continue
            nline += 1
            k = norm_en(e)
            if not k:
                continue
            if want_third:
                for en_key, old, new in THIRD:
                    if k == norm_en(en_key):
                        for tag, v in (("旧", old), ("新", new)):
                            if v in z:
                                third_cnt[(en_key, tag, v)] += 1
                                third_files[(en_key, tag, v)].add(gname)
            if k in ("amur river", "amur"):
                for v in AMUR:
                    if v in z:
                        amur_cnt[v] += 1
                        amur_files[v].add(gname)
            if k in LIB:
                vals = LIB[k]
                if not any(v in z or z in v for v in vals):
                    hits[(k, z)] += 1
                    files_of[(k, z)].add(gname)
    print(f"   参与比对的术语行 {nline}（词库 PEG* 条目 {KEPT} / 全库 {TOT}）")
    if not hits:
        print("   ⇒ 成品与词库**无**冲突")
    else:
        agg = collections.defaultdict(lambda: collections.Counter())
        for (k, z), n in hits.items():
            agg[k][z] += n
        kinds = collections.Counter(kind_of(k) for k in agg)
        print(f"   ⇒ 成品用词与词库冲突：{len(agg)} 个英文键 / {len(hits)} 组（键×成品写法）"
              f" ⇒ 真需裁定 {kinds['real']} · 番号/政策 {kinds['abbr']} · 词库即原文 {kinds['keep']}")
        print("   --- 【真需裁定】---")
        for k in sorted(agg, key=lambda x: -sum(agg[x].values())):
            if kind_of(k) != "real":
                continue
            libs = "｜".join(sorted(LIB[k]))[:44]
            got = "｜".join(f"{z}×{n}" for z, n in agg[k].most_common(3))
            ex = ",".join(sorted(files_of[(k, list(agg[k])[0])])[:2])
            print(f"      {k[:26]:26s} 词库: {libs:46s} 成品: {got}   [{ex}]")
        print("   --- 【词库即原文 / 番号政策】（不是错，是政策差异）---")
        for k in sorted(agg, key=lambda x: -sum(agg[x].values())):
            kd = kind_of(k)
            if kd == "real":
                continue
            got = "｜".join(f"{z}×{n}" for z, n in agg[k].most_common(2))
            print(f"      [{kd:4s}] {k[:24]:24s} 词库: {'｜'.join(sorted(LIB[k]))[:30]:32s} 成品: {got[:44]}")
    if want_third:
        print("   --- docs/43 第三组 12 组：成品用量（旧名 vs 新名）---")
        for en_key, old, new in THIRD:
            o = sum(n for (k, t, v), n in third_cnt.items() if k == en_key and t == "旧")
            nw = sum(n for (k, t, v), n in third_cnt.items() if k == en_key and t == "新")
            if o or nw:
                fo = ",".join(sorted(third_files.get((en_key, "旧", old), set()))) or "-"
                print(f"      {en_key[:24]:24s} 旧「{old}」×{o}  新「{new}」×{nw}   例: {fo[:70]}")
            else:
                print(f"      {en_key[:24]:24s} 旧×0 新×0（成品无此键）")
    if amur_cnt:
        print("   --- Amur 阵营分叉实测（成品中文侧）---")
        for v in AMUR:
            print(f"      「{v}」×{amur_cnt[v]}  文件: {','.join(sorted(amur_files[v])[:6])}")
    return hits


if __name__ == "__main__":
    which = sys.argv[1:] or ["peg", "pegww2"]
    for p in which:
        scan(p, want_third=True)
