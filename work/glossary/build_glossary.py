# -*- coding: utf-8 -*-
"""标准译名库生成器 —— 从各 efile 的「原始英文 ↔ 当前中文」平行文件聚合。

用法:
  python build_glossary.py            # 生成库 + 报告 + 冲突 + 漏译清单
  python build_glossary.py --dry      # 只统计，不写文件

真源:  backup/ORIGINAL-<EFILE>/  与  OpenPG2/<EFILE>/TEXT-ZH/
       （同结构同行数，逐行平行 ⇒ en->zh 零对齐风险）

输出:
  glossary/standard-glossary.tsv     主库（唯一真源）
  glossary/glossary-conflicts.tsv    同名多译冲突
  glossary/glossary-residual.tsv     漏译：本库已有标准译名，该处仍用原文
  glossary/glossary-skip.tsv         未纳入的源（不平行等）
  out/glossary-build-report.txt      构建报告
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"D:/DSH/军事游戏汉化/work"
OUTD = r"D:/DSH/军事游戏汉化/glossary"
sys.path.insert(0, os.path.join(WORK, "efile-nashornpbem"))

from apply_residual import parse  # noqa: E402  复用 .xscn 解析器

sys.path.insert(0, HERE)
from cat_fix_rules import recat as _recat  # noqa: E402  cat 纠正规则（见 docs/50）

# cat 纠正留痕：[(en, zh, scope, 新cat, 理由), ...]，由 _recat() 判定
CAT_FIXED = []

# ---------------------------------------------------------------- 配置

EFILES = [
    ("EFILE_OLGWW2",      r"D:/OpenPG2/EFILE_OLGWW2",      r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_OLGWW2"),
    ("EFILE_OPENPG",      r"D:/OpenPG2/EFILE_OPENPG",      r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_OPENPG"),
    ("EFILE_NASHORNPBEM", r"D:/OpenPG2/EFILE_NASHORNPBEM", r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_NASHORNPBEM"),
]

ROOT_FILES = [
    ("names.txt",         "LEADER",  "names"),
    ("nations.txt",       "NATION",  "nations"),
    ("equip.txt",         "EQUIP",   "equip"),
    ("strings_efile.txt", "TERM",    "strings"),
    ("tips1.txt",         "TERM",    "tips"),
]

PRI = {"manual": 0, "glossary": 0, "txt": 1, "xscn": 2,
       "equip": 3, "strings": 4, "names": 5, "nations": 6, "tips": 7}

SKIP = re.compile(r"^\s*(\*|//|;|\[|#)")
CJK = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)
LAT = re.compile(r"[A-Za-z]")
# 部队行：以数字/罗马数字起头，或以编制词收尾
UNIT_HEAD = re.compile(r"^(\d+|\d+(st|nd|rd|th)|I{1,3}V?|IV|V|VI|VII|VIII|IX|X)\b")
UNIT_TAIL = re.compile(r"(团|旅|师|军|营|连|排|炮兵团|装甲|步兵|骑兵|工兵|伞兵|"
                       r"海军|航空|集团军|方面军|军团|支队|大队|中队|小队|联队|旅团|"
                       r"师团|旅团|机甲|摩步|机步|海岸|要塞|守备|卫戍|兵站|"
                       r"(Regt|Regiment|Bde|Brigade|Div|Division|Corps|Bn|Battalion|"
                       r"Company|Coy|Sqn|Squadron|Group|Army|Battery|Abteilung)\.?)$")
# 缩写+数字的番号形式：AOK 12 / KG 55 / IR 192
ALNUM_UNIT = re.compile(r"^[A-Z]{2,4}[\s\-]\d{1,3}[A-Za-z]?$")


def readlines(path, enc):
    if not os.path.exists(path):
        return None
    return io.open(path, encoding=enc, errors="replace").read().splitlines()


def is_noise(s):
    t = s.strip()
    if not t or SKIP.match(t):
        return True
    if not LAT.search(t) and not CJK(t):
        return True
    return False


def clean(s):
    return s.strip().replace("\t", " ")


def cat_of_name(s):
    t = s.strip()
    if len(t) > 40 or (t.count(" ") >= 7 and re.search(r"[.!?]", t)):
        return "TEXT"          # 叙述句（部分 .txt 混有场景文本，非名单项）
    if BRACKET.match(t):
        return "BRACKET"
    if UNIT_HEAD.match(t) or UNIT_TAIL.search(t) or ALNUM_UNIT.match(t):
        return "UNIT"
    return "PLACE"


# ---------------------------------------------------------------- 采集

def collect_root(efile, cur_dir, orig_dir, recs, stats):
    for fn, cat, src in ROOT_FILES:
        a = readlines(os.path.join(orig_dir, fn), "cp1252")
        cp = os.path.join(cur_dir, "TEXT-ZH", fn)
        if not os.path.exists(cp):
            cp = os.path.join(cur_dir, fn)
        b = readlines(cp, "gbk")
        if a is None or b is None:
            continue
        if len(a) != len(b):
            stats["skip"].append((efile, fn, "%d vs %d 行" % (len(a), len(b))))
            continue
        for i, (x, y) in enumerate(zip(a, b)):
            if is_noise(x):
                continue
            recs.append((clean(x), clean(y), cat, efile, src, "%s:%d" % (fn, i + 1)))


# 分隔符规范：原文侧「多名单项」用带空格的 " / "；番号内部（I./StG 1）不带空格。
SEP_O = re.compile(r"\s+/\s+")
ROMAN_DOT = re.compile(r"^[IVX]+\.?$")
BRACKET = re.compile(r"^[\[【].*[\]】]$")


def split_pair(x, y):
    """原文侧与中文侧都拆成「名单项」，段数一致才返回配对。

    务必以原文侧的分隔为依据：中文侧一律写无空格 `/`，
    直接拆会把德式番号 `I./StG 1` 拆成 `I.` + `StG 1`，凭空造条目。
    无空格拆分需通过罗马数字守卫（`I.`/`II.` 是番号层级，不是名单项）。
    """
    X = [p.strip() for p in SEP_O.split(x)]
    if len(X) < 2:
        X = [p.strip() for p in x.split("/")]
    if len(X) < 2 or not all(X) or any(ROMAN_DOT.match(p) for p in X):
        return None
    Y = [q.strip() for q in y.split("/")]
    if len(Y) != len(X) or not all(Y) or any(ROMAN_DOT.match(q) for q in Y):
        return None
    return list(zip(X, Y))


def collect_txt(efile, cur_dir, orig_dir, recs, stats):
    o_dir = os.path.join(orig_dir, "SCENARIO")
    c_dir = os.path.join(cur_dir, "SCENARIO")
    if not os.path.isdir(o_dir):
        return
    files = sorted(x for x in os.listdir(o_dir) if x.lower().endswith(".txt"))
    for fn in files:
        a = readlines(os.path.join(o_dir, fn), "cp1252")
        b = readlines(os.path.join(c_dir, fn), "gbk")
        if a is None or b is None:
            stats["skip"].append((efile, fn, "中文侧缺失" if b is None else "原文侧缺失"))
            continue
        if len(a) != len(b):
            stats["skip"].append((efile, fn, "行数 %d vs %d" % (len(a), len(b))))
            continue
        stats["txt_ok"] += 1
        for ln, (x, y) in enumerate(zip(a, b)):
            if is_noise(x):
                continue
            loc = "SCENARIO/%s:%d" % (fn, ln + 1)
            if ln == 0:
                recs.append((clean(x), clean(y), "TITLE", efile, "txt", loc))
                continue
            pr = split_pair(x, y)
            if pr:
                for p, q in pr:
                    if not is_noise(p):
                        recs.append((clean(p), clean(q), cat_of_name(p), efile, "txt", loc))
            else:
                recs.append((clean(x), clean(y), cat_of_name(x), efile, "txt", loc))


def getval(data, off, ln, enc="gbk"):
    """取 .xscn 字符串。

    注意：原文侧（ORIGINAL-*）是 cp1252 单字节，中文侧才是 GBK。
    一律按 GBK 读原文侧会把 `Bièvre` 变成 `Bi鑦re`（mojibake）。
    """
    if off + ln > len(data) or ln <= 0:
        return ""
    return data[off:off + ln].decode(enc, "replace")


def collect_xscn(efile, cur_dir, orig_dir, recs, stats):
    o_dir = os.path.join(orig_dir, "SCENARIO")
    c_dir = os.path.join(cur_dir, "SCENARIO")
    if not os.path.isdir(o_dir):
        return
    files = sorted(x for x in os.listdir(o_dir) if x.lower().endswith(".xscn"))
    for fn in files:
        op, cp = os.path.join(o_dir, fn), os.path.join(c_dir, fn)
        if not os.path.exists(cp):
            stats["skip"].append((efile, fn, "中文侧缺失"))
            continue
        da, ia, ma = parse(op)
        db, ib, mb = parse(cp)
        if ia is None or ib is None or len(ia) != len(ib):
            stats["skip"].append((efile, fn, "结构不一致 %s vs %s" %
                                  ("-" if ia is None else len(ia), "-" if ib is None else len(ib))))
            continue
        stats["xscn_ok"] += 1
        if ma and mb and ma[0] is not None and mb[0] is not None:
            ta, tb = getval(da, ma[0] + 2, ma[1], "cp1252"), getval(db, mb[0] + 2, mb[1])
            if ta and not is_noise(ta):
                recs.append((clean(ta), clean(tb), "TITLE", efile, "xscn",
                             "SCENARIO/%s:title" % fn))
        for (ga, ka, oa, la), (gb, kb, ob, lb) in zip(ia, ib):
            if ga != gb or ka != kb:
                continue
            va, vb = getval(da, oa + 2, la, "cp1252"), getval(db, ob + 2, lb)
            if not va or is_noise(va):
                continue
            cat = "PLACE" if ga == 0 else "UNIT"
            recs.append((clean(va), clean(vb), cat, efile, "xscn",
                         "SCENARIO/%s:g%d#%d" % (fn, ga, ka)))


def collect_old_glossary(recs):
    """并入既有 olgww2-glossary.tsv。

    KEEP 类的 dst == src，语义是「按口径保留原文」—— 这是权威政策登记，
    不能被别处的中文译名覆盖（否则舰名等会误报为漏译）。返回 KEEP 键集合。
    """
    p = os.path.join(WORK, "efile-nashornpbem", "olgww2-glossary.tsv")
    if not os.path.exists(p):
        return 0, set()
    n = 0
    keep = set()
    for ln in io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
        c = ln.split("\t")
        if len(c) < 3 or not c[0].strip() or not c[1].strip():
            continue
        src, dst, ct = clean(c[0]), clean(c[1]), c[2].strip()
        if src == "Name Error":
            continue
        if ct == "KEEP":
            keep.add(src)
            continue                      # 政策层单独处理，不进投票
        cat = {"PLACE": "PLACE", "UNIT": "UNIT", "TITLE": "TITLE",
               "ABBR": "ACRO"}.get(ct, "TERM")
        recs.append((src, dst, cat, "EFILE_OLGWW2", "glossary", "olgww2-glossary.tsv"))
        n += 1
    return n, keep


def collect_pegww2_glossary(recs):
    """并入本作（PeG / PeG-WW2）的人工术语表。

    ⭐ **新增 scope 与既有 efile 并列，互不覆盖**。总库是「按 scope 分列」的：
    同一英文在不同 scope 合法有不同译法 ——
      · `Air Transport`：OLGWW2＝**运输机**（飞机）／本作＝**空运**（动作，兵种名另作「空中运输」）
      · `Ranger`       ：OLGWW2＝**游骑兵**（美军）／本作＝**突击队**（英军编制）
      · `Ferdinand`    ：OLGWW2＝保留原文（POLICY）／本作＝**斐迪南**（与 Elefant 象式 区分）
    源文件由 `work/glossary/make_pegww2_glossary.py` 从三处真源生成，可重跑。
    """
    p = os.path.join(WORK, "glossary", "pegww2-glossary.tsv")
    if not os.path.exists(p):
        return 0
    n = 0
    for ln in io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
        c = ln.split("\t")
        if len(c) < 5 or not c[0].strip() or not c[1].strip():
            continue
        recs.append((clean(c[0]), clean(c[1]), c[2].strip(), c[3].strip(),
                     c[4].strip(), "pegww2-glossary.tsv"))
        n += 1
    return n


# ---------------------------------------------------------------- 合并 / 裁决

ZH_PUNC = re.compile(r"[（）()\[\]【】\s·・、]")


def norm_zh(s):
    """归一化后相同 ⇒ 只是表述差异（多/少「第」字等）"""
    return ZH_PUNC.sub("", re.sub(r"^第(?=[0-9])", "", s))


def is_abbr_key(en):
    """番号类原文键：含数字且数字密度高，或全大写短串。

    `32 R/132 Ariete/[XX]` 这种番号串同名在不同场景指不同部队，
    属上下文相关而非译名冲突。注意别把 `Canton` 这种首字母大写的
    普通词误判进来 —— 无数字时必须全大写且很短。
    """
    t = en.strip()
    if re.search(r"\d", t):
        d = len(re.findall(r"\d", t))
        return d * 6 >= len(t) or len(t) <= 8
    return len(t) <= 5 and t.upper() == t and bool(re.search(r"[A-Z]", t))


def conflict_kind(en, kept, other):
    if norm_zh(kept) == norm_zh(other):
        return "SAME"          # 仅表述差异（第32团 / 32团）
    if is_abbr_key(en):
        return "ABBR"          # 番号/缩写：上下文相关
    return "REAL"              # 实质不同，需裁定


def pick(dist, zh_items):
    """多数票；同票取来源优先级最高者。"""
    def prio(v):
        return min(PRI.get(s, 99) for z, c, s, _ in zh_items if z == v)
    return sorted(dist.items(), key=lambda kv: (-kv[1], prio(kv[0])))[0][0]


def merge(recs, keep_keys):
    """同 (en, scope) 归并；政策层（KEEP）优先，其次含中文值的多数票。"""
    grp = collections.defaultdict(list)
    for en, zh, cat, scope, src, loc in recs:
        grp[(en, scope)].append((zh, cat, src, loc))

    rows, conflicts, residual = [], [], []
    for (en, scope), lst in grp.items():
        srcs = sorted({t[2] for t in lst}, key=lambda x: PRI.get(x, 99))
        # ---- 政策层：KEEP 登记为「保留原文」，优先级最高，不参与投票
        if en in keep_keys:
            cat = next((c for z, c, s, _ in lst if z == en), lst[0][1])
            rows.append((en, en, cat, scope, "POLICY", "+".join(srcs), "POLICY", "POLICY"))
            continue

        zh_items = [t for t in lst if CJK(t[0])]
        conf = "ABBR" if is_abbr_key(en) else "HIGH"
        zh_in = ""
        if zh_items:
            # 标准译名 = 含中文值的多数票（同票取来源优先级高者）
            dist = collections.Counter(t[0] for t in zh_items)
            zh = pick(dist, zh_items)
            cat = next(c for z, c, s, _ in zh_items if z == zh)
            # 哪些「层」给出过中文 —— 校验时只跟同层比（equip 保留型号、
            # xscn 译地名，同一原文的合法处理本就可能不同）
            zh_in = "+".join(sorted({t[2] for t in zh_items}, key=lambda x: PRI.get(x, 99)))
            if len(dist) > 1:
                alt = " | ".join("%s×%d" % (k, v) for k, v in dist.most_common())
                other = dist.most_common(2)[1][0]
                kind = conflict_kind(en, zh, other)
                conflicts.append((en, scope, zh, alt, kind, cat, len(zh_items)))
                conf = {"SAME": "MID", "ABBR": "ABBR"}.get(kind, "LOW")
            # 其余位置若仍为原文 ⇒ 漏译
            for z, c, s, loc in lst:
                if z == en:
                    residual.append((en, zh, c, scope, s, loc,
                                     "ABBR" if is_abbr_key(en) else "PLAIN"))
        else:
            zh, cat = en, lst[0][1]
            conf = "POLICY"
        status = "LOCKED" if CJK(zh) and zh != en else "POLICY"
        rows.append((en, zh, cat, scope, status, "+".join(srcs), conf, zh_in))

    # ---- cat 纠正（后处理）：历史启发式把部队番号/舰名判成 PLACE
    # 只改 cat 列，不动 (en, scope) 主键、不动 zh ⇒ 对下游解析零影响。
    global CAT_FIXED
    CAT_FIXED = []
    for _i, _r in enumerate(rows):
        if _r[2] != "PLACE":
            continue
        _rr = _recat(_r[0], _r[1])
        if _rr:
            CAT_FIXED.append((_r[0], _r[1], _r[3], _rr[0], _rr[1]))
            rows[_i] = (_r[0], _r[1], _rr[0]) + tuple(_r[3:])

    rows.sort(key=lambda r: (r[0].lower(), r[3]))
    conflicts.sort(key=lambda c: (c[4] != "REAL", -c[6], c[0].lower()))
    residual.sort(key=lambda r: (r[6] != "PLAIN", r[3], r[5]))
    return rows, conflicts, residual


# ---------------------------------------------------------------- 主流程

def main():
    dry = "--dry" in sys.argv
    recs = []
    stats = collections.defaultdict(int)
    stats["skip"] = []

    for efile, cur, orig in EFILES:
        print("[采集] %s" % efile)
        collect_root(efile, cur, orig, recs, stats)
        collect_txt(efile, cur, orig, recs, stats)
        collect_xscn(efile, cur, orig, recs, stats)
    nold, keep_keys = collect_old_glossary(recs)
    npeg = collect_pegww2_glossary(recs)
    print("[并入] 本作 PeG/PeG-WW2 术语 %d 条" % npeg)

    rows, conflicts, residual = merge(recs, keep_keys)

    cnt_cat = collections.Counter(r[2] for r in rows)
    cnt_st = collections.Counter(r[4] for r in rows)
    cnt_cf = collections.Counter(r[6] for r in rows)
    cnt_ef = collections.Counter(r[3] for r in rows)
    res_by_src = collections.Counter(r[4] for r in residual)
    res_by_kind = collections.Counter(r[6] for r in residual)

    L = []
    L.append("标准译名库构建报告")
    L.append("=" * 76)
    L.append("输入记录 %d -> 去重后 %d 条（含政策保留 %d 条）"
             % (len(recs), len(rows), cnt_st.get("POLICY", 0)))
    L.append("")
    L.append("-- 按类别 --")
    for k, v in cnt_cat.most_common():
        L.append("   %-8s %6d" % (k, v))
    L.append("")
    L.append("-- 按状态 --")
    L.append("   LOCKED（有标准中文译名） %6d" % cnt_st.get("LOCKED", 0))
    L.append("   POLICY（按口径保留原文） %6d" % cnt_st.get("POLICY", 0))
    L.append("")
    L.append("-- 按可信度 --")
    for k in ("HIGH", "MID", "LOW", "ABBR", "POLICY"):
        if cnt_cf.get(k):
            L.append("   %-8s %6d" % (k, cnt_cf[k]))
    L.append("")
    L.append("-- 按 efile --")
    for k, v in cnt_ef.most_common():
        L.append("   %-20s %6d" % (k, v))
    L.append("")
    L.append("-- 源纳入情况 --")
    L.append("   场景 .txt 纳入 %d 个（行行平行）" % stats["txt_ok"])
    L.append("   .xscn   纳入 %d 个（结构一致）" % stats["xscn_ok"])
    L.append("   未纳入 %d 项：" % len(stats["skip"]))
    for e, f, why in stats["skip"][:20]:
        L.append("      %-20s %-24s %s" % (e, f, why))
    if len(stats["skip"]) > 20:
        L.append("      ... 余 %d 项见 glossary-skip.tsv" % (len(stats["skip"]) - 20))
    L.append("")
    L.append("-- ★ 冲突（同原文 + 同 efile 出现多个中文译法）: %d 条 --" % len(conflicts))
    kd = collections.Counter(c[4] for c in conflicts)
    L.append("   REAL=%d（实质不同，需裁） ABBR=%d（短缩写，上下文相关） SAME=%d（仅表述差异）"
             % (kd.get("REAL", 0), kd.get("ABBR", 0), kd.get("SAME", 0)))
    for en, sc, kept, alt, kind, cat, n in conflicts[:25]:
        L.append("   [%-4s] %-24s %-22s <= %s" % (kind, en[:24], kept[:22], alt[:44]))
    if len(conflicts) > 25:
        L.append("   ... 余 %d 条见 glossary-conflicts.tsv" % (len(conflicts) - 25))
    L.append("")
    L.append("-- ★ 漏译（本库已有标准译名，该位置仍为原文）: %d 处 --" % len(residual))
    L.append("   PLAIN=%d（整串/常规词，可直接改） ABBR=%d（番号缩写，需看语境）"
             % (res_by_kind.get("PLAIN", 0), res_by_kind.get("ABBR", 0)))
    for src, n in res_by_src.most_common():
        L.append("   %-10s %6d" % (src, n))
    for en, zh, cat, sc, s, loc, kind in residual[:24]:
        L.append("   [%-5s] %-26s 应为 %-20s @ %s" % (kind, en[:26], zh[:20], loc))
    if len(residual) > 24:
        L.append("   ... 余 %d 处见 glossary-residual.tsv" % (len(residual) - 24))
    if CAT_FIXED:
        L.append("")
        L.append("cat 纠正（PLACE 误标 → 部队/装备）: %d 条" % len(CAT_FIXED))
        for (nc, why), n in collections.Counter((f[3], f[4]) for f in CAT_FIXED).most_common():
            L.append("   %-6s %5d  %s" % (nc, n, why))
        for en, zh, sc, nc, why in CAT_FIXED[:20]:
            L.append("   %-30s %-24s → %-6s" % (en[:30], zh[:24], nc))
        if len(CAT_FIXED) > 20:
            L.append("   ... 余 %d 条见 work/out/glossary-cat-fix.tsv" % (len(CAT_FIXED) - 20))
    rep = "\n".join(L)
    print(rep)

    if dry:
        print("\n[dry] 未写文件")
        return

    os.makedirs(OUTD, exist_ok=True)

    def san(x):
        # 值内的制表符/换行会把裸 TSV 撕开（读取方一律 split('\t')）⇒ 写前消毒
        return str(x).replace("\t", " ").replace("\r", " ").replace("\n", " ")

    def dump(name, head, body):
        with io.open(os.path.join(OUTD, name), "w", encoding="utf-8-sig", newline="\r\n") as f:
            f.write("\t".join(head) + "\n")
            for r in body:
                f.write("\t".join(san(x) for x in r) + "\n")

    dump("standard-glossary.tsv",
         ["en", "zh", "cat", "scope", "status", "src", "conf", "zh_in"], rows)
    dump("glossary-conflicts.tsv",
         ["en", "scope", "kept", "rejected", "kind", "cat", "n"], conflicts)
    dump("glossary-residual.tsv",
         ["en", "should_be", "cat", "scope", "src", "loc", "kind"], residual)
    dump("glossary-skip.tsv", ["efile", "file", "reason"], stats["skip"])
    # 逐处出现表（含文件与位置）——供"按位置定点改写"使用
    dump("glossary-occ.tsv", ["en", "zh", "cat", "scope", "src", "loc"], recs)

    os.makedirs(os.path.join(WORK, "out"), exist_ok=True)
    with io.open(os.path.join(WORK, "out", "glossary-cat-fix.tsv"), "w",
                 encoding="utf-8-sig", newline="\r\n") as f:
        f.write("en\tzh\tscope\tnew_cat\treason\n")
        for en, zh, sc, nc, why in CAT_FIXED:
            f.write("\t".join(san(x) for x in (en, zh, sc, nc, why)) + "\n")

    os.makedirs(os.path.join(WORK, "out"), exist_ok=True)
    io.open(os.path.join(WORK, "out", "glossary-build-report.txt"), "w",
            encoding="utf-8", newline="\n").write(rep + "\n")

    print("\n已写出（glossary/）:")
    print("  standard-glossary.tsv   %6d 条" % len(rows))
    print("  glossary-conflicts.tsv  %6d 条" % len(conflicts))
    print("  glossary-residual.tsv   %6d 处" % len(residual))
    print("  glossary-skip.tsv       %6d 项" % len(stats["skip"]))


if __name__ == "__main__":
    main()
