#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**阵营/年代维度 · 接线**（第一步：只报不判，不改任何判定结果）。

解决的问题（详见 `docs/44-地名三维规则纳入词库方案.md` §三）：
  缺口 1 · `layer_gate.load_overrides()` 用 **地名ID**（如 `Amur`）当键，
           而层表/正文的键是 **英文写法**（如 `Amur River`）⇒ 登记大量落空。
  缺口 2 · 即使键命中，`ov[en]` 是**同 ID 下所有阵营、所有年代名的并集**
           ⇒ 用错阵营/错年代也判"已登记"。
  缺口 3 · 三维判定只在 `faction_place_audit.py` 里，**门不调用它**。

本模块做四件事（**全部只读 + 只写自己的证据文件**）：
  ① **键对齐**：地名ID → 层表 en 键（精确 + 前缀），**按 `cat` 排除装备/人名等误命中**，
     报覆盖率、未解析项与**一键多 ID 冲突**。
  ② **压平清单**：对已对齐的键，列出「层表现值 ← 哪些阵营接受它」：
     唯一阵营 / 多阵营（压平）/ 简称（全称与简称不一致）/ 复合标题（应走别的判法）。
  ③ **影响预测**：若把 `load_overrides()` 换成对齐后的键，会有多少条偏离
     从「未登记」变「已登记」——**只预测，不实施**。
  ④ **未判定计数**：读 `faction_place_audit.py` 写的摘要。

⚠️ 本步骤**不修改任何判定**：`layer_gate` 的 ok/bad/退出码一律不受影响。

用法:
  python faction_wire.py            # 报告（stdout + evidence/faction-wire.txt）
  python faction_wire.py --json     # 只输出摘要 JSON（供上层门调用）
"""
import collections
import io
import json
import os
import re
import sys
import time

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
EVID = os.path.join(GL, "evidence")
LAYER_TABLES = ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv")

# 登记表：(文件名, 键列, 阵营列, 中文列, 其它写法列, 时期列)
REGISTRIES = (("faction-places.tsv", 0, 1, 3, 4, 5),
              ("faction-ops.tsv", 0, 1, 3, 4, 5))

# 前缀对齐可接受的后缀分隔符（`Amur River` / `Danzig (PORT)` / `Lodz-2`）
SEP = (" ", "-", "_", "(", "[", "'")
# 这些 cat 明显不是地名/作战名 ⇒ 前缀命中一律排除（实测 `Crusader AA/I` 是坦克却撞「十字军行动」）
CAT_DENY = {"EQUIP", "LEADER", "NATION"}
# ⭐ 层表键准入（2026-10-13）：地名表只认 `PLACE`，作战表另认 `TITLE`/`TERM`。
#    **不能放开**：实测不加准入门会命中 63 个 `UNIT`（坦克/飞机型号）与整句简报文。
CAT_ALLOW_PLACE = {"PLACE"}
CAT_ALLOW_OPS = {"PLACE", "TITLE", "TERM"}
# 「全称/简称」差异允许的通用尾巴；差出别的内容即为**复合标题**
GENERIC_TAIL = ("行动", "河", "城", "战役", "会战", "村", "镇", "地区", "山", "湖", "岛",
                "海湾", "海峡", "半岛", "港", "机场", "市", "郡", "县")

# ── 复合标题判法（2026-10-13 · 用户口径 ③：「先剥限定后缀、只对地名部分判阵营」）──
# 实测 63 条「复合标题」全部出自下列五类装饰，剥掉后地名部分即可判阵营。
QUAL_RESULT = ("辉煌胜利", "战术胜利", "决定性胜利", "重大胜利", "胜利", "失败")
QUAL_ACT = ("反击战", "反击", "突围", "解放", "事件", "取消", "中止", "攻势", "防御", "撤退",
            "登陆", "空降")
QUAL_FEATURE = ("铁路", "公路", "道路", "河流", "运河", "机场", "森林", "车站", "港口", "阵地",
                "防线")
# 括号注记（**不含**「」『』——那里面包的常是地名本身，如「台风」中止）
_BRACKET = re.compile(r"[（(【\[][^）)】\]]*[）)】\]]")
# 连接路名：`维堡—列宁格勒公路` ⇒ 取地名段 `维堡`
_JOINED = re.compile(r"^(.+?)\s*[—–\-]+\s*.+?(铁路|公路|道路|河流|运河)$")
# 尾部编号/日期/来源标注：`(#16v) 43 #5 - 1943年7月4日 PeG:WW2 ZS#05`
_TAILNUM = re.compile(r"[\s\-—–,，、·]*#?\d+([\s]*年([\s]*\d+[\s]*月([\s]*\d+[\s]*日)?)?)?[\s]*$")
_TAILTAG = re.compile(r"[\s]*(PeG:?WW2|RTB#?\d*|ZS#?\d*|#\d+[a-zA-Z]?)[\s]*$", re.I)
_QUOTES = re.compile(r"[「」『』]")
_STRIPCHARS = " -—–、·,，"


def strip_quals(z):
    """先剥限定后缀/注记，返回剩下的**地名部分**（用户口径 ③）。

    剥除顺序（反复剥到不动）：① 引号 → ② 括号注记 → ③ 连接路名取地名段
    → ④ 结果/动作/设施尾词 → ⑤ 尾部编号、日期、来源标注。剥不动或剥空即原样返回。
    """
    s = z
    for _ in range(8):
        t = _QUOTES.sub("", s)
        t = _BRACKET.sub("", t)
        m = _JOINED.match(t)
        if m:
            t = m.group(1)
        for q in sorted(QUAL_RESULT + QUAL_ACT + QUAL_FEATURE, key=len, reverse=True):
            if t.endswith(q) and len(t) > len(q):
                t = t[:-len(q)]
                break
        t = _TAILTAG.sub("", t)
        t = _TAILNUM.sub("", t)
        t = t.strip(_STRIPCHARS)
        if t == s or not t:
            return s
        s = t
    return s


def alias_kind(z, regnames):
    """层表值 z 与某阵营登记名的关系：same / 简称 / 复合。

    ⭐ 2026-10-13（用户口径 ③）：**先剥限定后缀、只对地名部分判阵营** ——
    实测 `维堡—列宁格勒公路` / `哈尔科夫反击战 (#3)` / `「台风」中止 1941年12月 胜利`
    这类复合标题，剥装饰后地名部分就是已登记名，应算「简称」而非「复合」。
    """
    stripped = strip_quals(z)
    for cand in ([stripped, z] if stripped != z else [z]):
        for r in regnames:
            if not r:
                continue
            if cand == r:
                return "same"
            if cand in r:
                tail = r.replace(cand, "", 1)
                return "简称" if tail in GENERIC_TAIL else "复合"
            if r in cand:
                tail = cand.replace(r, "", 1)
                return "简称" if tail in GENERIC_TAIL else "复合"
    return "复合"


def _read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return b.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', 'replace').splitlines()


def load_layer_keys():
    """层表：{en: [(zh, layer, scope, cat), …]}。"""
    by = collections.defaultdict(list)
    for fn in LAYER_TABLES:
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for ln in _read(p):
            if ln.startswith("#") or ln.startswith("en\t"):
                continue
            c = ln.split("\t")
            if len(c) >= 9:
                by[c[0]].append((c[1], c[8], c[3], c[2]))
    return by


def load_registries():
    """登记表 → [{fn,id,阵营,中文集合,其它写法集合,时期,依据}]。"""
    rows = []
    for fn, idc, facc, zhc, altc, erac in REGISTRIES:
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for ln in _read(p):
            if ln.startswith("#") or ln.startswith("en\t"):
                continue
            c = ln.split("\t")
            if len(c) < 4 or not c[idc].strip():
                continue
            zh = [x.strip() for x in c[zhc].split("|") if x.strip() and x.strip() != "—"]
            alt = set()
            if len(c) > altc and c[altc].strip() and c[altc].strip() != "—":
                for tok in re.split(r"[,，]", c[altc]):
                    if tok.strip():
                        alt.add(tok.strip())
            alt.add(c[idc].strip())
            rows.append(dict(fn=fn, id=c[idc].strip(), fac=c[facc].strip(), zh=zh, alt=alt,
                             era=(c[erac].strip() if len(c) > erac else ""),
                             note=(c[6].strip() if len(c) > 6 else "")))
    return rows


def id_matches_key(pid, key):
    """地名ID 能否覆盖层表键：精确，或 ID + 分隔符/数字 开头。"""
    a, b = pid.lower(), key.lower()
    if a == b:
        return "精确"
    for s in SEP:
        if b.startswith(a + s):
            return "前缀"
    if b.startswith(a) and len(b) > len(a) and b[len(a)].isdigit():
        return "前缀"
    return None


def build_align(rows, by):
    keys = list(by.keys())
    per_id, key2ids = collections.defaultdict(dict), collections.defaultdict(set)
    # ⭐ 别名也参与对齐：登记 ID 常与层表键拼写不同（`Chisinau↔Kishinev`、
    #    `Citadel_ND↔Nordwind`、`Shingle↔Operation Shingle`）。只用 ID 对齐 ⇒
    #    这些明明能解析的也会被报成"未解析、门里完全不生效"。
    #    （`aligned_authorized()` 早就用了别名列，报数用的 `build_align()` 却漏了 ⇒ 报数与实况不符）
    alts = collections.defaultdict(set)
    for r in rows:
        alts[r["id"]] |= set(r["alt"]) | {r["id"]}
    for pid in {r["id"] for r in rows}:
        for seed in alts[pid]:
            for k in keys:
                how = id_matches_key(seed, k)
                if how:
                    per_id[pid][k] = how
                    key2ids[k].add(pid)
    return per_id, key2ids


def acceptance(rows):
    per = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in rows:
        for z in r["zh"]:
            per[r["id"]][r["fac"]].add(z)
    return per


def aligned_authorized(rows, by):
    """用「ID + 其它写法」当种子对齐层表键，返回 {层表键: 该 ID 各阵营已登记名}。

    ⭐ 缺口 1 的真因（2026-10-13 实测）：`build_align()` **只拿 ID 对齐**，
    而登记表的**「其它写法」列（第 4 列）根本没参与** —— 正是它才能救回
    `Tarnopol → Ternopol'`、`Warschau → Warsaw`、`Seelöwe → Sealion`、`Krakau` 等。
    另需按 `cat` 准入（否则前缀会撞上 63 个 `UNIT`：`Crusader II CS` 是坦克、
    `Typhoon IB` 是飞机）并排除整句（`Wacht am Rhein is our best chance…`）。
    """
    keys = list(by.keys())
    out = collections.defaultdict(set)
    for r in rows:
        allow = CAT_ALLOW_PLACE if r["fn"].startswith("faction-places") else CAT_ALLOW_OPS
        for seed in r["alt"]:
            for k in keys:
                if not id_matches_key(seed, k):
                    continue
                if not ({c for _z, _l, _s, c in by[k]} & allow):
                    continue
                if "." in k or len(k) > 60:
                    continue
                out[k].update(r["zh"])
    return out


def predict_effect(rows, by):
    """③ 影响预测：**调用真实的门**，而不是本模块的简化模型。

    ⚠️ 踩过（2026-10-13）：本模块原用「只含 faction 两表、按 ID 建键」的 `cur` 作对照，
    报出「修键后放宽 1 条（`Amur River`）」；把对齐键真的喂给 `layer_gate.compute()` 后，
    **偏离 288 → 288、分类变化 0 条** —— 简化模型漏算了 `override.tsv` /
    `scope-diff.tsv` / `faction-terms.tsv` 与三层词库本身也参与「已登记」判定，
    故预测**系统性偏乐观**。现在一律以真实门为准，并保留简化值供对照。
    """
    try:
        import layer_gate as LG                      # 延迟导入：避免与 layer_gate 循环
    except Exception:
        return None
    if not hasattr(LG, "compute"):
        return None
    gby = LG.load_glossary()
    ov0 = LG.load_overrides()
    ov1 = {k: set(v) for k, v in ov0.items()}
    for k, zs in aligned_authorized(rows, by).items():
        ov1.setdefault(k, set()).update(zs)
    def cls(div):
        return {(d["cls"], d["en"]) + tuple(d["zh"]) for d in div}
    d0 = cls(LG.compute(gby, ov0)[1])
    d1 = cls(LG.compute(gby, ov1)[1])
    return dict(keys=len(ov1) - len(ov0),
                total0=len(d0), total1=len(d1),
                loosened=len(d1 - d0), tightened=len(d0 - d1))


def analyze():
    by = load_layer_keys()
    rows = load_registries()
    per_id, key2ids = build_align(rows, by)
    acc = acceptance(rows)
    ids = sorted({r["id"] for r in rows})
    resolved = [i for i in ids if per_id.get(i)]
    unresolved = [i for i in ids if not per_id.get(i)]
    conflicts = {k: sorted(v) for k, v in key2ids.items() if len(v) > 1}

    verdicts, blocked, only1, many, short, compound = [], 0, 0, 0, 0, 0
    for pid in resolved:
        facs_here = acc.get(pid, {})
        regnames = {z for zs in facs_here.values() for z in zs}
        for k in sorted(per_id[pid]):
            cats = {cat for _z, _la, _sc, cat in by[k]}
            if cats and cats <= CAT_DENY:          # 装备/人名等误命中 ⇒ 排除
                blocked += 1
                continue
            for z in sorted({z for z, _la, _sc, _cat in by[k]}):
                # ⭐ 用户口径 ③：**只对地名部分判阵营** —— 先用剥掉装饰后的地名段匹配登记名
                zp = strip_quals(z)
                owners = sorted(f for f, zs in facs_here.items() if z in zs or zp in zs)
                if len(owners) == 1:
                    kind, only1 = "唯一阵营", only1 + 1
                elif len(owners) >= 2:
                    kind, many = "多阵营（压平）", many + 1
                else:
                    ak = alias_kind(z, regnames)
                    if ak in ("简称", "same"):
                        kind, short = "简称（缺别名登记）", short + 1
                    else:
                        kind, compound = "复合标题（应走别的判法）", compound + 1
                verdicts.append(dict(id=pid, en=k, zh=z, owners=owners, kind=kind,
                                     cats=sorted(cats),
                                     all_fac={f: sorted(zs) for f, zs in facs_here.items()}))

    # ③ 影响预测
    aov = collections.defaultdict(set)
    for pid in resolved:
        for k in per_id[pid]:
            for zs in acc.get(pid, {}).values():
                aov[k].update(zs)
    cur = collections.defaultdict(set)
    for fn, idc, _f, zhc, _a, _e in REGISTRIES:
        p = os.path.join(LAY, fn)
        if not os.path.isfile(p):
            continue
        for ln in _read(p):
            if ln.startswith("#") or ln.startswith("en\t"):
                continue
            c = ln.split("\t")
            if len(c) > zhc and c[idc].strip():
                cur[c[idc].strip()].update(x for x in c[zhc].replace("|", "\t").split("\t") if x)
    flip_unreg, flip_reg = [], []
    for en, lst in by.items():
        zs = sorted({z for z, _la, _sc, _cat in lst})
        if len(zs) < 2:
            continue
        was = en in cur and set(zs) <= cur[en]
        now = en in aov and set(zs) <= aov[en]
        if now and not was:
            flip_unreg.append(en)
        elif was and not now:
            flip_reg.append(en)

    und = {}
    sp = os.path.join(EVID, "faction-audit-summary.txt")
    if os.path.isfile(sp):
        for ln in _read(sp):
            if "=" in ln:
                k, v = ln.split("=", 1)
                und[k.strip()] = v.strip()

    return dict(layers=(len(by), sum(len(v) for v in by.values())), rows=rows, ids=ids,
                resolved=resolved, unresolved=unresolved, conflicts=conflicts,
                verdicts=verdicts, blocked=blocked,
                only1=only1, many=many, short=short, compound=compound,
                flip_unreg=flip_unreg, flip_reg=flip_reg,
                effect=predict_effect(rows, by),
                cur_keys=len(cur), aligned_keys=len(aov), und=und)


def summary():
    """给 `layer_gate.quick_check()` 用的轻量摘要（不写文件、不打印）。"""
    a = analyze()
    return dict(ids=len(a["ids"]), resolved=len(a["resolved"]), unresolved=len(a["unresolved"]),
                only1=a["only1"], many=a["many"], short=a["short"], compound=a["compound"],
                blocked=a["blocked"], conflicts=len(a["conflicts"]),
                flip_unreg=len(a["flip_unreg"]), flip_reg=len(a["flip_reg"]),
                effect=a.get("effect"), und=a["und"])


def report(a):
    L = ["阵营/年代维度 · 接线报告（只报不判）  " + time.strftime("%Y-%m-%d %H:%M:%S"), "=" * 64,
         "层表：%d 个 en 键 / %d 条取值" % a["layers"], "",
         "① 键对齐（缺口 1）",
         "   登记 ID %d 个 ⇒ 解析到层表键 %d 个（未解析 %d 个）"
         % (len(a["ids"]), len(a["resolved"]), len(a["unresolved"])),
         "   现口径登记键 %d 个 ⇒ 对齐后 %d 个" % (a["cur_keys"], a["aligned_keys"])]
    if a["unresolved"]:
        L.append("   ⚠️ 未对齐到层表 en 键（**不参与门侧 allow-list**；阵营审计器按"
                 "「该方称法/其它写法」在文本里匹配，不受影响）：%s" % " · ".join(a["unresolved"]))
        L.append("      （实测分类：9 个在本作文本里出现 ⇒ 审计器仍生效；14 个本作不存在 ⇒ 仅备查。"
                 "见 glossary/阵营视角-约定.md §十一）")
    L.append("   （另有 %d 个前缀命中被 `cat` 排除：装备/人名等，不是地名）" % a["blocked"])
    if a["conflicts"]:
        L.append("   ⚠️ 一键多 ID（对齐歧义，需人工裁定）%d 个：" % len(a["conflicts"]))
        for k, v in list(a["conflicts"].items())[:12]:
            L.append("        %-26s ← %s" % (k, " / ".join(v)))

    L += ["", "② 阵营压平清单（缺口 2）",
          "   ✅ 唯一阵营接受（将来可升 error）：%d" % a["only1"],
          "   ⚠️ 多阵营接受（门里判不出谁对）：%d" % a["many"],
          "   🟡 简称（全称/简称不一致，缺别名登记）：%d" % a["short"],
          "   🟠 复合标题（含地名但不止地名，应走别的判法）：%d" % a["compound"]]
    for want, title, cap in (("多阵营（压平）", "⚠️ 多阵营", 15),
                             ("简称（缺别名登记）", "🟡 简称", 20),
                             ("复合标题（应走别的判法）", "🟠 复合标题", 12),
                             ("唯一阵营", "✅ 唯一阵营", 12)):
        sel = [v for v in a["verdicts"] if v["kind"] == want]
        L.append("")
        L.append("   ── %s（%d 条，列前 %d）──" % (title, len(sel), cap))
        for v in sel[:cap]:
            L.append("      %-14s %-24s 现值「%s」 %s  全部登记=%s"
                     % (v["id"], v["en"][:24], v["zh"], "/".join(v["owners"]) or "—",
                        " · ".join("%s:%s" % (f, "|".join(zs)) for f, zs in v["all_fac"].items())))

    eff = a.get("effect")
    L += ["", "③ 影响预测（缺口 1 修好之后会松多少）—— 只预测，未实施",
          "   本模块简化口径：未登记→已登记 %d · 已登记→未登记 %d"
          % (len(a["flip_unreg"]), len(a["flip_reg"]))]
    for en in a["flip_unreg"][:20]:
        L.append("        %s" % en)
    for en in a["flip_reg"][:10]:
        L.append("        (收紧) %s" % en)
    if eff is None:
        L.append("   ⚠️ 真实门不可用（import layer_gate 失败）⇒ 以上仅为简化口径，**偏乐观**")
    else:
        L.append("   ⭐ 真实门 `layer_gate.compute()` 口径（**以此为准**）：")
        L.append("        新增对齐键 %d 个 · 偏离 %d → %d 条 · 放宽 %d 条 · 收紧 %d 条"
                 % (eff["keys"], eff["total0"], eff["total1"], eff["loosened"], eff["tightened"]))
        if eff["loosened"] == 0 and len(a["flip_unreg"]):
            L.append("        ⚠️ 简化口径报 %d 条、真实门 0 条 —— 简化模型漏算了 override.tsv /"
                     % len(a["flip_unreg"]))
            L.append("           scope-diff.tsv / faction-terms.tsv 与三层词库本身也参与「已登记」判定。")

    L += ["", "④ 未判定计数（缺口 3 的上游）"]
    if a["und"]:
        for k, v in a["und"].items():
            L.append("   %-24s %s" % (k, v))
    else:
        L.append("   （尚无 evidence/faction-audit-summary.txt —— 由 faction_place_audit.py 产出）")
    L += ["", "⚠️ 本报告**不影响任何判定**：layer_gate 的 ok/bad/退出码不变。"]
    return "\n".join(L) + "\n"


def main():
    a = analyze()
    if "--json" in sys.argv:
        print(json.dumps(summary(), ensure_ascii=False))
        return 0
    txt = report(a)
    print(txt)
    os.makedirs(EVID, exist_ok=True)
    io.open(os.path.join(EVID, "faction-wire.txt"), "w", encoding="utf-8", newline="\n").write(txt)
    print("报告 → glossary/evidence/faction-wire.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
