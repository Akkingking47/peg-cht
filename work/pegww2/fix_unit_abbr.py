#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 部队编制缩写翻译器（用户裁定 2026-10-19）：把译文里残留的拉丁番号缩写改成中文。

设计要点（每条都是踩过的坑）：
 1. **真源是值模式**（`ww2-scn-map.tsv` 只有「原文串 → 译文」，没有文件维度）
    ⇒ 国别不能用「每行文件」判，必须用「**该原文串出现在哪些场景文件** → 那些场景的战役国别」
    （用户裁定②：按战役地图国别判定）。实现：扫 `testbed\\backup` 建 原文行 → 场景stem 索引，
    再查 `research\\_scn-国别.tsv` 取国别；国别冲突 ⇒ 登记待判，不硬改。
 2. **跨国歧义的缩写必须按国别分叉**：实测 `SA` 在苏军语境＝Shock Army（突击集团军，
    `36/10GCD [4GC] 5SA`），在英语系语境＝South African（`4 SA Arm. Car Rgt.`＝南非装甲车团）。
 3. **区间占用**（W20 血泪）：规则先长后短，已替换的区段不再被短规则二次命中 ——
    否则 `反坦克炮` 之后 `坦克炮` 会再咬一次。
 4. **括注不动**（`（原文）`/`(原文)`）：口径要求译名括注保留原文。
 5. **舰名前缀不动**（用户裁定③）：HMS/KMS/USS/ITS/VK 等。
 6. **无据代号不猜**：裸 2–3 字母的 MOD 内部代号（FC/BC/NG/BD/KK…）保留原文并登记。
 7. 幂等 · **默认 dry-run** · `--apply` 才写 · 写前备份 `.pre-unitabbr` · 全套回归断言。

用法：
    python fix_unit_abbr.py            # dry-run：出对照表 + 断言，不写任何文件
    python fix_unit_abbr.py --apply    # 写真源（备份后）
"""
import argparse
import collections
import io
import os
import re
import sys

WS = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME = os.environ.get("PEG_GAME_WW2", r"D:\Program Files\PeG-WW2")
RES = os.path.join(WS, "pegww2", "research")
BK = os.path.join(WS, "pegww2", "testbed", "backup")
MAPFILE = os.path.join(RES, "unit-abbr-map.tsv")
NATION = os.path.join(RES, "_scn-国别.tsv")

# 待改真源（值模式表）
TARGETS = [
    ("scn", os.path.join(RES, "ww2-scn-map.tsv")),
    ("ovr", os.path.join(RES, "_scn-file-overrides.tsv")),
    ("gui", os.path.join(RES, "WW2Gui-map.tsv")),
    ("misc", os.path.join(RES, "WW2Misc-map.tsv")),
    ("tips", os.path.join(RES, "WW2Tips-map.tsv")),
    ("eqp", os.path.join(RES, "ww2-eqp-map.tsv")),
    ("name", os.path.join(RES, "WW2NAME-map.tsv")),
]

CJK = re.compile(r"[\u4e00-\u9fff]")
# 英文序数后缀：73rd → 第73（全局，安全）
ORD = re.compile(r"(?<![A-Za-z0-9])(\d+)(st|nd|rd|th)\b")
# 括注：`（原文）`/`(原文)`（含拉丁、空格、点号）
GLOSS = re.compile(r"[（(]\s*[A-Za-z0-9\u00c0-\u024f][A-Za-z0-9\u00c0-\u024f .,'’\-]*\s*[)）]")
SHIP = re.compile(r"\b(HMS|KMS|USS|ITS|VK|KM|RN)\b")
NATION_CLUE = [
    ("苏/共体系", re.compile(r"\b(GMech|GTA?|GCC?|GCD|Comrade)\b")),
    ("英语系", re.compile(r"\b(RTR|RHA|RAA|Recce|BEF|Abn)\b")),
    ("德语系", re.compile(r"\b(Pz|Aufkl|Funk|Leibstandarte|SS)\b")),
    ("意大利", re.compile(r"\b(Pavia|Littorio)\b")),
]


def load_map():
    """返回 rules: [(缩写, 国别, 译法, 依据, 条件正则, 行号)]，按缩写长度降序（长优先）。"""
    rules = []
    with io.open(MAPFILE, encoding="utf-8-sig") as fh:
        for ln, raw in enumerate(fh, 1):
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#") or s.startswith("缩写\t"):
                continue
            f = s.split("\t")
            if len(f) < 4:
                continue
            cond = f[4].strip() if len(f) > 4 else ""
            cond_rx = None if (not cond or cond == ".") else re.compile(cond)
            rules.append((f[0], f[1].strip(), f[2], f[3], cond_rx, ln))
    rules.sort(key=lambda r: -len(r[0]))
    return rules


def build_index():
    """扫原文备份：整行(去空白) → 场景 stem 集合。用于「按战役地图国别判定」。"""
    idx = collections.defaultdict(set)
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(BK, sub)
        if not os.path.isdir(d):
            continue
        for dp, _dn, fns in os.walk(d):
            for fn in fns:
                if not fn.lower().endswith((".txt", ".ply")):
                    continue
                stem = re.sub(r"(?i)(_i|_m|_u|_bv|_tv|_l|_v|_cb)?\.(txt|ply)$", "", fn).lower()
                try:
                    txt = io.open(os.path.join(dp, fn), encoding="gbk", errors="replace").read()
                except Exception:
                    continue
                for line in re.split(r"\r\n|\r|\n", txt):
                    k = line.strip()
                    if k:
                        idx[k].add(stem)
    return idx


def load_nations():
    out = {}
    if not os.path.isfile(NATION):
        return out
    with io.open(NATION, encoding="utf-8-sig") as fh:
        for raw in fh:
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#") or s.startswith("场景stem"):
                continue
            f = s.split("\t")
            if len(f) >= 3:
                out[f[0]] = f[2]
    return out


def row_nations(en, idx, nations):
    """该原文串出现在哪些场景 → 其战役国别集合"""
    stems = idx.get(en.strip(), set())
    got = collections.Counter()
    for st in stems:
        n = nations.get(st, "")
        if n and not n.startswith("("):
            got[n] += 1
    return got, len(stems)


def row_clue(en, zh):
    """行内容自证的国别线索（兜底，用于无索引命中时）"""
    got = collections.Counter()
    for nat, rx in NATION_CLUE:
        n = len(rx.findall(en)) + len(rx.findall(zh))
        if n:
            got[nat] += n
    return got


def gloss_spans(line):
    return [m.span() for m in GLOSS.finditer(line)]


def sub_outside_gloss(line, rx, repl):
    """只在**括注之外**做替换（括注必须保留原文 —— 口径要求；断言也会拦）。"""
    gl = gloss_spans(line)
    if not gl:
        return rx.sub(repl, line)
    parts, last = [], 0
    for a, b in gl:
        parts.append(rx.sub(repl, line[last:a]))
        parts.append(line[a:b])
        last = b
    parts.append(rx.sub(repl, line[last:]))
    return "".join(parts)


def rewrite_line(line, rules, ctx):
    """区间占用式替换；返回 (新行, 命中列表)。ctx＝该行上下文（原文+译文），用于条件化规则。"""
    occ, edits, hits = [], [], []
    ships = [m.span() for m in SHIP.finditer(line)]
    gl = gloss_spans(line)
    for abbr, _nat, zh, _src, cond_rx, _ln in rules:
        if cond_rx and not cond_rx.search(ctx):
            continue
        # 允许吃掉**已存在的「第」**前缀，避免「第2 RHA」→「第第2皇家骑炮兵团」
        pat = re.compile(r"(?<![A-Za-z])(?:第\s*)?(?:(\d+)\s?)?%s(?![A-Za-z])" % re.escape(abbr))
        for m in pat.finditer(line):
            s, e = m.span()
            if any(not (e <= a or s >= b) for a, b in occ + gl + ships):
                continue
            num = m.group(1)
            if "{n}" in zh:                       # 模板式：SS ⇒ 党卫军第{n}装甲师
                # 无编号时取模板里「第{n}」之前的部分（SS⇒党卫军），不臆造编号
                repl = zh.replace("{n}", num) if num else zh.split("第{n}")[0]
            else:
                repl = ("第%s%s" % (num, zh)) if num else zh
            edits.append((s, e, repl))
            occ.append((s, e))
            hits.append((abbr, line[s:e], repl))
    if not edits:
        out2 = sub_outside_gloss(line, ORD, r"第\1")
        return (out2, [("序数", "", "第N")]) if out2 != line else (line, [])
    edits.sort(key=lambda t: -t[0])
    out = line
    for s, e, r in edits:
        out = out[:s] + r + out[e:]
    out = sub_outside_gloss(out, ORD, r"第\1")
    # 纯番号行的**前导编号**：`2/2SS` ⇒ `第2/党卫军第2装甲师`
    # （只对「无汉字」的行做，避免在中文散文里误改编号）
    if not CJK.search(line):
        out = re.sub(r"^(\d+)\s*/", r"第\1/", out)
    out = re.sub(r"第(\d+)\s+(?=[\u4e00-\u9fff])", r"第\1", out)   # 「第73 中队」→「第73中队」
    return out, hits


META_LINE = re.compile(
    r"(?i)^(Dummy|Gameset|Equipment|PeGWW2|PG2|Loading|Note|.*E-File|.*conversion|http|"
    r"version|None|Empty|-+$)")


def is_meta_or_code(zh):
    """整行纯拉丁：属于元数据/占位/无据代号 ⇒ 不算「待判漏译」"""
    s = zh.strip()
    if not s or META_LINE.match(s):
        return True
    if re.match(r"^[A-Za-z]{1,4}$", s):        # 裸 2–4 字母代号：无展开依据
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rules = load_map()
    print("译法规则 %d 条（长优先）" % len(rules))
    idx = build_index()
    print("原文行索引：%d 个唯一行" % len(idx))
    nations = load_nations()
    print("场景国别表：%d 个场景" % len(nations))

    changes, pending, stats = [], [], collections.Counter()
    for tag, path in TARGETS:
        if not os.path.isfile(path):
            continue
        lines = io.open(path, encoding="utf-8-sig", newline="").read().split("\n")
        out = list(lines)
        n_hit = 0
        for i, raw in enumerate(lines):
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#"):
                continue
            f = s.split("\t")
            if len(f) < 2 or f[0] in ("原文",):
                continue
            en, zh = f[0], f[1]
            got, nstem = row_nations(en, idx, nations)
            nat = ""
            if len(got) == 1:
                nat = list(got)[0]
            elif len(got) > 1:
                nat = "**冲突**"
            else:
                cl = row_clue(en, zh)
                nat = list(cl)[0] if len(cl) == 1 else ("**冲突**" if cl else "")
            new, hits = rewrite_line(zh, rules, en + "\n" + zh)
            if new != zh:
                # 回归断言
                g_old = [m.group(0) for m in GLOSS.finditer(zh)]
                g_new = [m.group(0) for m in GLOSS.finditer(new)]
                assert g_old == g_new, "括注被改动：%s → %s" % (zh, new)
                for m in SHIP.finditer(zh):
                    assert m.group(0) in new, "舰名前缀丢失：%s" % m.group(0)
                assert len(CJK.findall(new)) >= len(CJK.findall(zh)), "汉字数减少：%s" % new
                assert "第 " not in new and "第（" not in new, "出现裸『第 』残段：%s" % new
                assert "第第" not in new, "双重编号前缀：%s" % new
                f2 = list(f)
                f2[1] = new
                out[i] = "\t".join(f2)
                n_hit += 1
                changes.append((tag, en, zh, new, nat, nstem, hits))
            elif not CJK.search(zh) and re.match(r"^[A-Za-z0-9 /\-\[\]().]+$", zh.strip()) \
                    and not is_meta_or_code(zh):
                cl = row_clue(en, zh)
                pending.append((tag, en, zh, "/".join("%s=%d" % kv for kv in cl.items()) or "无线索"))
        stats[tag] = n_hit
        if args.apply and n_hit:
            import shutil
            shutil.copy2(path, path + ".pre-unitabbr")
            io.open(path, "w", encoding="utf-8-sig", newline="").write("\n".join(out))

    print("\n=== 各表命中 ===")
    for k, v in stats.items():
        print("  %-6s %d" % (k, v))
    print("  合计 %d 行" % sum(stats.values()))

    cols = collections.Counter(i[0] for r in changes for i in r[6])
    print("\n=== 缩写命中分布（Top 20）===")
    for k, v in cols.most_common(20):
        print("  %-10s %d" % (k, v))
    natc = collections.Counter(r[4] for r in changes)
    print("\n=== 国别分布 ===")
    for k, v in natc.most_common():
        print("  %-16s %d" % (k or "(未定)", v))

    p1 = os.path.join(RES, "_番号-对照表.tsv")
    with io.open(p1, "w", encoding="utf-8", newline="") as fh:
        fh.write("# 番号缩写改写对照（fix_unit_abbr.py dry-run）\n")
        fh.write("表\t原文\t原译文\t新译文\t场景国别\t原文出现于几个场景\t命中缩写\n")
        for tag, en, zh, new, nat, ns, hits in changes:
            fh.write("%s\t%s\t%s\t%s\t%s\t%d\t%s\n" % (
                tag, en, zh, new, nat, ns, ",".join(h[0] for h in hits)))
    p2 = os.path.join(RES, "_番号-待判表.tsv")
    with io.open(p2, "w", encoding="utf-8", newline="") as fh:
        fh.write("# 整行纯拉丁、且无据可判的番号行（**保留原文，不臆造**）\n")
        fh.write("表\t原文\t现译文\t国别线索\n")
        for tag, en, zh, cl in pending:
            fh.write("%s\t%s\t%s\t%s\n" % (tag, en, zh, cl))
    print("\n[out] %s（%d 行）" % (os.path.relpath(p1, WS), len(changes)))
    print("[out] %s（%d 行）" % (os.path.relpath(p2, WS), len(pending)))
    if not args.apply:
        print("\n※ dry-run：真源未改动；各表旁的 *.dryrun 为试写产物（可删）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
