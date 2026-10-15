#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**阵营视角审计**：找"视角与用名不匹配"的地方（警告级）。

做法（数据驱动，不靠猜）：
  1. 读 `layers/faction-terms.tsv`：`en｜阵营｜译名｜备注`
  2. 逐场景文件读**英文原件**（`testbed/backup/SCENARIO/`）与**中文件**（游戏目录），
     用**译文里的视角标记**判定"这段文本是谁在说话"（见 `glossary/阵营视角-约定.md` §三）
  3. 若某行原文在对照表里**双方叫法不同**，而译文用了**对方阵营**的叫法 ⇒ 报出

用法:
  python faction_audit.py            # 全量审计
  python faction_audit.py --sample   # 只打前 20 条明细
"""
import collections
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
FAC = os.path.join(LAY, "faction-terms.tsv")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
EVID = os.path.join(GL, "evidence")

MARK = {                     # 阵营 → 视角标记（只收"说话人口吻/机构自称"，**不收单纯提到的国名**）
    "苏": ("将军同志", "最高统帅部", "斯大林同志", "同志们", "方面军", "红军", "法西斯入侵者"),
    "德": ("将军阁下", "元首", "党卫军", "帝国师", "警卫旗队", "国防军"),
    "盟": ("指挥官，", "盟军将", "艾森豪威尔", "蒙哥马利", "巴顿将军", "美国陆军"),
    "罗": ("罗马尼亚军队", "安东内斯库", "Conducator", "我们罗马尼亚"),
    "芬": ("芬兰军队", "曼纳海姆", "Mannerheim", "我们芬兰"),
    "波": ("家乡军", "华沙起义", "波兰流亡政府", "我们波兰"),
    "意": ("意大利军队", "墨索里尼", "意军指挥官"),
}
# ⚠️ **地图/部队名单文件**（`_m`/`_u`）里混着**双方**的名字，只有"名单"没有"口吻"
#    ⇒ 它们**只能接收**视角（从同场景的简报继承），**不能当视角来源**。
NO_VOICE = re.compile(r"(?i)(_m|_u)$")


def load_rules():
    """en → {阵营: 译名}；只保留**双方叫法不同**的条目。"""
    r = collections.defaultdict(dict)
    if not os.path.isfile(FAC):
        return r
    for l in io.open(FAC, encoding="utf-8"):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 3 and c[0].strip() and c[1].strip() and c[2].strip():
            r[c[0].strip()][c[1].strip()] = c[2].strip()
    return {en: d for en, d in r.items() if len(set(d.values())) > 1}


def perspective(text):
    """从译文判定视角；返回 (阵营, 命中标记) 或 (None, "")。"""
    sc = {f: sum(text.count(m) for m in ms) for f, ms in MARK.items()}
    best = max(sc, key=lambda f: sc[f])
    return (best, MARK[best][0]) if sc[best] > 0 else (None, "")


def family_of(fn):
    """**战役族**键（战役数据在 exe 内、`.cam` 不在磁盘 ⇒ 用文件名族作代理）。

    实测：`GE47I/GE48I/GE50V`→`GE`、`r701/r70x`→`r`、`DTR3L/DTR14BV`→`DTR`、`RTB31`→`RTB`、`BoB08TV`→`BoB`。
    同族多数票 = 该族的阵营（票数会记进证据）。
    """
    s = os.path.splitext(fn)[0]
    m = re.match(r"(?i)^([A-Za-z]{2,})", s)
    return m.group(1).lower() if m else ""


def stem_of(fn):
    """场景文件的 stem：去掉 `_i/_m/_u/_l/_bv/_tv/_v` 后缀与末尾 `e`（各文件共享同一 stem）。

    例：`G7Pzra715_i.txt` / `G7Pzra715_m.txt` / `G7Pzra715e.txt` ⇒ 同一 stem `G7Pzra715`。
    """
    s = os.path.splitext(fn)[0]
    s = re.sub(r"(?i)(_i|_m|_u|_l|_bv|_tv|_v)$", "", s)
    # ⚠️ 末位 `e` 只在前面是**数字或 v** 时才剥（`G7Pzra715e`→`G7Pzra715`、`7Pzra715ve`→`7Pzra715v`）；
    #    否则会误伤 `DAK_Choice`→`DAK_Choic`。
    return re.sub(r"(?i)(?<=[0-9v])e$", "", s)


def main():
    rules = load_rules()
    print("阵营对照表：%d 个原文有**双方不同**叫法" % len(rules))
    if not os.path.isdir(BK) or not os.path.isdir(GAME):
        print("  ⚠️ 缺备份或游戏目录，无法逐文件比对")
        return 0
    # ---- 读全部文件（英/中）----
    data = {}
    for fn in sorted(os.listdir(BK)):
        if not fn.lower().endswith(".txt"):
            continue
        gp = os.path.join(GAME, fn)
        if not os.path.isfile(gp):
            continue
        try:
            data[fn] = (io.open(os.path.join(BK, fn), encoding="cp1252", errors="replace").read(),
                        io.open(gp, encoding="gbk", errors="replace").read())
        except Exception:
            continue
    # ---- ① 逐文件判口吻；无口吻者按 **同 stem 的其它文件** 继承（留证据）----
    voice, vmark = {}, {}
    for fn, (_en, zh) in data.items():
        if NO_VOICE.search(os.path.splitext(fn)[0]):      # 名单类文件不当"视角来源"
            continue
        f, mark = perspective(zh)
        if f:
            voice[fn], vmark[fn] = f, mark
    by_stem = collections.defaultdict(collections.Counter)
    by_fam = collections.defaultdict(collections.Counter)
    for fn, f in voice.items():
        by_stem[stem_of(fn)][f] += 1
        fam = family_of(fn)
        if fam:
            by_fam[fam][f] += 1
    side, origin = dict(voice), {fn: "口吻标记「%s」" % vmark[fn] for fn in voice}
    for fn in data:
        if fn in side:
            continue
        c = by_stem.get(stem_of(fn))                      # ① 同场景文件（最强）
        if c:
            f, n = c.most_common(1)[0]
            side[fn] = f
            origin[fn] = "同场景文件（stem=%s，%d 票）" % (stem_of(fn), n)
            continue
        fam = family_of(fn)
        c = by_fam.get(fam)
        # 需 ≥3 票 **且** 首位占 ≥60%（族投票是启发式，别让微弱多数决定）
        if c and sum(c.values()) >= 3:
            f, n = c.most_common(1)[0]
            if n * 10 >= sum(c.values()) * 6:
                side[fn] = f
                origin[fn] = "战役族「%s」多数票（%d/%d）" % (fam, n, sum(c.values()))
    files, persp_stat = len(data), collections.Counter(side.values())
    cov = len(side)
    print("扫描场景文件 %d 个 · 判定视角 %d 个（覆盖率 %.0f%%：口吻 %d + 同场景继承 %d + 战役族继承 %d）"
          % (files, cov, 100.0 * cov / max(1, files), len(voice),
             sum(1 for f in side if origin[f].startswith("同场景")),
             sum(1 for f in side if origin[f].startswith("战役族"))))
    print("判定分布：%s" % dict(persp_stat))

    hits = []
    for fn, (en, zh) in data.items():
        f = side.get(fn)
        if not f:
            continue
        enl, zhl = en.split("\n"), zh.split("\n")
        for i, (a, b) in enumerate(zip(enl, zhl), 1):
            a, b = a.strip(), b.strip()
            if not a or not b:
                continue
            key = a if a in rules else next((k for k in rules if k in a), None)
            if not key:
                continue
            d = rules[key]
            found = sorted({v for v in d.values() if v in b}, key=len, reverse=True)
            if not found:
                continue
            used = found[0]
            ok = {k for k, v in d.items() if v == used}
            if f in ok or (f in ("苏", "俄") and ok & {"苏", "俄"}):
                continue
            want = d.get(f) or d.get("苏") or d.get("俄") or ""
            if used == want:
                continue
            hits.append((fn, i, a, used, f, "|".join(sorted(ok)), want, origin.get(fn, "")))
    print("⚠️ 视角与用名不匹配：%d 处" % len(hits))
    for fn, i, a, used, f, used_by, want, org in hits[:20]:
        print("   %-16s 行%-4d %-24s 用了「%s」(属%s方叫法) 视角=%s 应为「%s」"
              % (fn, i, a[:24], used[:12], used_by, f, want[:12]))
        print("        视角来源：%s" % org)
    # ---- 用名清单 ----
    inv = collections.defaultdict(collections.Counter)
    for fn, (_en, zh) in data.items():
        f = side.get(fn) or "?"
        for en, d in rules.items():
            for fac, name in d.items():
                if name and name in zh:
                    inv[(en, name)][f] += 1
    print("\n=== 用名清单（该译名出现在各视角文件的次数）===")
    for (en, name), c in sorted(inv.items()):
        if c:
            print("   %-16s 「%s」 ← %s" % (en[:16], name[:10], dict(c)))
    os.makedirs(EVID, exist_ok=True)
    with io.open(os.path.join(EVID, "faction-audit.txt"), "w", encoding="utf-8", newline="\n") as w:
        w.write("# 阵营视角审计：视角与用名不匹配（警告级）\n")
        w.write("文件\t行号\t原文\t现用译名\t判定视角\t该译名属\t本视角应用\n")
        for h in hits:
            w.write("\t".join(str(x) for x in h) + "\n")
    print("报告 → glossary/evidence/faction-audit.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
