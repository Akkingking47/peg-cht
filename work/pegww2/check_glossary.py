#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**跨层术语一致性校验器**（治本件）：同一英文 ⇒ 只允许一种译法。

逻辑：
  1. 读规范表 `_统一术语表.tsv` ⇒ `en → zh`（规范值）
  2. 读例外表 `_统一术语表-例外.tsv` ⇒ `en → {允许译法}`（分工/待裁定/前作未同步）
  3. 逐层逐条比对：`zh` 既不等于规范值、又不在例外里 ⇒ **违规**
  4. 撞名检查：术语类（非装备名/人名/场景名）里「不同英文 → 同一中文」⇒ 报警（需人工分类，
     因为多语言兵种名（意/法/波/俄语同一兵种）本就该同名）
  5. 任有违规 ⇒ 退出码 1；报告写 `research/evidence/glossary-check.txt`

用法:
  python check_glossary.py             # 全层校验
  python check_glossary.py --with-scn  # 连场景/地名层一起（较慢）
"""
import collections
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
PRES = os.path.join(WS, "peg", "research")
UNI = os.path.join(RES, "_统一术语表.tsv")
EXC = os.path.join(RES, "_统一术语表-例外.tsv")
DOCS_TERM = os.path.join(WS, "pegww2", "docs-zh", "_翻译须知与术语.md")
REP = os.path.join(RES, "evidence", "glossary-check.txt")

# (层名, 文件, 原文列, 译文列)
LAYERS = [
    ("UI", os.path.join(RES, "WW2Gui-map.tsv"), 1, 2),
    ("UI", os.path.join(RES, "WW2Misc-map.tsv"), 1, 2),
    ("UI", os.path.join(RES, "WW2Tips-map.tsv"), 1, 2),
    ("EQ", os.path.join(RES, "ww2-eqp-map.tsv"), 0, 1),
    ("EQ", os.path.join(RES, "WW2NAME-map.tsv"), 0, 1),
    ("PeG-UI", os.path.join(PRES, "gui030-zh.tsv"), 1, 2),
    ("基准", os.path.join(PRES, "ui-glossary.tsv"), 0, 1),
]

MD_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$")


def norm_key(en):
    """键归一化：只去掉**含中文的尾部夹注**（那是译者注），压空白。

    ⚠️ 两个坑：
      ① 不归一化会**假绿**：文档层写 `River Assault（原 Bridging）`，
         会被当成独立键，于是与界面层的 `River Assault` 对不上也报不出来。
      ② 归一化过头会**假红**：`DECREASE DIFFICULTY (+ Player Prestige %)`、
         `Spitfire II (Sqn 315 City of Deblin)` 的括号是**字符串本体**，
         剥掉就会让同名的不同串互相打架 ⇒ **只剥含中文的夹注**。
    """
    s = en.strip()
    m = re.search(r"[（(]([^）)]*)[）)]\s*$", s)
    if m and re.search(r"[\u4e00-\u9fff]", m.group(1)):
        s = s[: m.start()]
    return re.sub(r"\s+", " ", s).strip()


def load_docs_pairs(path):
    out = []
    if not os.path.isfile(path):
        return out
    for l in open(path, encoding="utf-8"):
        m = MD_ROW.match(l)
        if not m or m.group(1) in ("英文", "---") or set(m.group(1).strip()) <= {"-"}:
            continue
        en, zh = m.group(1).strip(), m.group(2).strip()
        if en and zh and not en.startswith("-") and not zh.startswith("-"):
            out.append((en, zh))
    return out


def docs_forms(zh):
    """把文档术语表里的**多形登记**拆成「允许形」。

    例：`空运 / 空中运输` ⇒ {空运, 空中运输} · `对空防御（部队数值）/ 防空（兵种·战报）`
    ⇒ {对空防御, 防空}（括号里是译者注，不算形的一部分）。
    """
    out = set()
    for part in re.split(r"[/｜|、]", zh):
        part = re.sub(r"[（(][^）)]*[）)]", "", part).strip()
        if part:
            out.add(part)
    return out


def load_layer_variants():
    """层文件 ⇒ `en → [(zh, scope)]`。文档层规则要用「**别的项目**的译法」作反例。"""
    out = collections.defaultdict(list)
    for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv"):
        p = os.path.join(WS, "glossary", "layers", fn)
        if not os.path.isfile(p):
            continue
        for l in open(p, encoding="utf-8"):
            if l.startswith("#") or l.startswith("en\t"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 9 and c[0].strip():
                out[c[0]].append((c[1].strip(), c[3].strip()))
    return out


def scan_docs(rules):
    """扫描 **DOCS 成品正文**里出现的「非规范译法」（警告级）。

    ⚠️ 光比"术语表"不够：真正的跨层差异常常只在**成品正文**里（如手册写「地面占领者」，
    而界面写「攻坚专家」）。所以这一层必须扫成品，不能只扫术语表。
    """
    hits = []
    root = os.path.join(WS, "pegww2", "docs-zh")
    if not os.path.isdir(root):
        return hits
    sys.path.insert(0, os.path.join(WS, "work", "pegww2"))
    try:
        import dump_text
    except Exception:
        dump_text = None
    for dp, _, fs in os.walk(root):
        if any(x in dp for x in ("_src", "_fill", "_staging", "_recovered")):
            continue
        for f in fs:
            p = os.path.join(dp, f)
            lines = []
            if f.endswith(".rtf") and dump_text:
                try:
                    lines = dump_text.display_lines(p)
                except Exception:
                    continue
            elif f.endswith(".txt"):
                try:
                    lines = open(p, encoding="utf-8-sig").read().split("\n")
                except Exception:
                    continue
            else:
                continue
            for ln in lines:
                for en, bad, _c in rules:
                    if bad in ln:
                        hits.append((p, 0, en, bad))
                        break
    return hits


def main():
    sink = []
    canon, cat, ncanon = {}, {}, {}
    for l in open(UNI, encoding="utf-8"):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 4:
            canon[c[0]] = c[1]
            cat[c[0]] = c[3]
            k = norm_key(c[0])
            # 归一化索引：**优先非 DOCS 层**（DOCS 的键常带夹注）
            if k not in ncanon or c[2] != "DOCS":
                ncanon.setdefault(k, c[1])
                if c[2] != "DOCS":
                    ncanon[k] = c[1]
    allow = {}
    if os.path.isfile(EXC):
        for l in open(EXC, encoding="utf-8"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 3 and c[0].strip():
                allow[c[0].strip()] = set(c[1].split("|"))
                allow[norm_key(c[0])] = set(c[1].split("|"))

    viol, unchecked, stats = [], [], {}
    for layer, path, ec, zc in LAYERS:
        if not os.path.isfile(path):
            continue
        n = v = 0
        for i, l in enumerate(open(path, encoding="utf-8-sig"), 1):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) <= max(ec, zc):
                continue
            en, zh = c[ec].strip(), c[zc].strip()
            if not en or not zh or en in ("行号", "原文", "en") or re.fullmatch(r"\d+", en):
                continue
            n += 1
            k = norm_key(en)
            if zh in allow.get(en, ()) or zh in allow.get(k, ()):
                continue
            # ⚠️ 键带夹注（如 `River Assault（原 Bridging）`）时**必须走归一化索引**：
            #    否则它在规范表里自成一条，`canon[en]` 会自证 → 假绿。
            exp = ncanon.get(k) if k != en else (canon.get(en) or ncanon.get(k))
            if exp is None:
                unchecked.append((layer, os.path.basename(path), i, en, zh))
            elif exp != zh:
                v += 1
                viol.append((layer, os.path.basename(path), i, en, zh, exp))
        pn, pv = stats.get(layer, (0, 0))
        stats[layer] = (pn + n, pv + v)      # ⚠️ 同层多文件要**累加**，不能覆盖

    # 文档层（markdown 表格）
    dn = dv = 0
    for en, zh in load_docs_pairs(DOCS_TERM):
        dn += 1
        k = norm_key(en)
        if zh in allow.get(en, ()) or zh in allow.get(k, ()):
            continue
        exp = ncanon.get(k) if k != en else (canon.get(en) or ncanon.get(k))
        if exp is None:
            unchecked.append(("DOCS", os.path.basename(DOCS_TERM), 0, en, zh))
        elif exp != zh:
            dv += 1
            viol.append(("DOCS", os.path.basename(DOCS_TERM), 0, en, zh, exp))
    if dn:
        pn, pv = stats.get("DOCS", (0, 0))
        stats["DOCS"] = (pn + dn, pv + dv)

    # 撞名（仅术语类）
    rev = {}
    for en, zh in canon.items():
        if cat.get(en) in ("装备", "人名", "场景"):
            continue
        if not re.search(r"[\u4e00-\u9fff]", zh):
            continue
        rev.setdefault(zh, set()).add(en)
    coll = {z: es for z, es in rev.items() if len(es) > 1
            and not any(e in allow for e in es)}

    out = []
    out.append("跨层术语一致性校验 · %s" % "见下")
    out.append("=" * 88)
    out.append("规范条目 %d · 例外 %d · 逐层（词条数/违规数）：" % (len(canon), len(allow)))
    tot = 0
    for k, (n, v) in stats.items():
        tot += n
        out.append("   %-8s 词条 %-5d 违规 %d" % (k, n, v))
    out.append("   合计校验 %d 条（未在规范表内 %d 条，不计违规）" % (tot, len(unchecked)))
    out.append("")
    if viol:
        out.append("❌ 违规 %d 条（同英文出现非规范译法，且不在例外表内）：" % len(viol))
        for layer, fn, i, en, zh, exp in viol[:40]:
            out.append("   [%s] %s 行%-4d %-28s got=%s  应为=%s" % (layer, fn, i, en, zh, exp))
    else:
        out.append("✅ 无违规：所有层的术语与规范表一致（例外表已登记 %d 条分工/待裁定/前作未同步）" % len(allow))
    out.append("")
    if coll:
        out.append("⚠️ 撞名候选 %d 组（不同英文→同一中文，需人工分类；多语言兵种同名属正常）：" % len(coll))
        for z, es in sorted(coll.items())[:20]:
            out.append("   %-14s ← %s" % (z, " ｜ ".join(sorted(es)[:5])))

    # ---- 文档成品层扫描（**警告**，不是硬违规）：规则三源 ----
    # ⚠️ 不能把所有异译都当问题：`AT→反坦克`、`Air Defense→对空防御` 是**已裁定的正当分工**，
    #    两处都合法；只有"待裁定"的层间差异才值得在正文里点名。
    # ⚠️ 覆盖缺口（本轮补）：以前这里**只读「待裁定」**，而该状态当时 0 条 ⇒ 文档层
    #    实际一条规则都没有。现补三源：
    #      ① 例外表「待裁定」（既有）
    #      ② `banned.tsv` 禁用译法黑名单（文档成品同样适用；整串精确匹配 ⇒ 零误伤）
    #      ③ **文档自身术语表的多形登记**：文档表里 `空运 / 空中运输` 是**允许形**；
    #         层文件里该 en 的「别的项目」译法（EFILE_*/PEG_UI/PEG_BASE）若不在此列
    #         ⇒ 就是"文档用了别人家的词"，成规则。基准取自**文档自己的表**，不是外来的。
    pend = []
    if os.path.isfile(EXC):
        for l in open(EXC, encoding="utf-8"):
            if l.startswith("#"):
                continue
            c = l.rstrip("\n").split("\t")
            if len(c) >= 4 and c[2].strip() == "待裁定":
                k = norm_key(c[0])
                cur = canon.get(c[0]) or ncanon.get(k)
                if cur:
                    for bad in c[1].split("|"):
                        if bad.strip() and bad.strip() != cur:
                            pend.append((c[0], bad.strip(), cur))
    n_ban = 0
    p_ban = os.path.join(RES, "banned.tsv")
    if os.path.isfile(p_ban):
        for l in open(p_ban, encoding="utf-8"):
            if l.startswith("#") or not l.strip():
                continue
            bad = l.split("\t")[0].strip()
            if bad:
                pend.append(("(禁用词)", bad, "—"))
                n_ban += 1
    n_tab = 0
    lv = load_layer_variants()
    for en, zh in load_docs_pairs(DOCS_TERM):
        allow = docs_forms(zh)
        if len(allow) < 2:
            continue
        for z, sc in lv.get(en, ()):
            if z in allow or not re.search(r"[\u4e00-\u9fff]", z):
                continue
            if sc.startswith(("EFILE_", "PEG_UI", "PEG_BASE")):
                pend.append((en, z, " / ".join(sorted(allow))))
                n_tab += 1
    cur_of = {(en, bad): cur for en, bad, cur in pend}
    hits = scan_docs(pend) if pend else []
    out.append("")
    out.append("📄 文档成品正文 · 非规范译法扫描（%d 条规则 = 例外表待裁定 %d + 禁用词 %d + 文档表多形 %d；警告级）："
               % (len(pend), len(pend) - n_ban - n_tab, n_ban, n_tab))
    if hits:
        seen = set()
        for f, _ln, en, bad in hits:
            key = (os.path.basename(os.path.dirname(f)) or "docs-zh", en, bad)
            if key in seen:
                continue
            seen.add(key)
            cur = cur_of.get((en, bad)) or canon.get(en) or ncanon.get(norm_key(en))
            out.append("   %-38s 用了「%s」，应为「%s」" % (key[0][:38], bad, cur))
    else:
        out.append("   未发现")
    txt = "\n".join(out)
    print(txt)
    os.makedirs(os.path.dirname(REP), exist_ok=True)
    open(REP, "w", encoding="utf-8").write(txt + "\n")
    return 1 if viol else 0


if __name__ == "__main__":
    sys.exit(main())
