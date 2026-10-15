#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全库扫描：哪些场景的「说明文件」不是标准简报（B 方案的施工清单）。

标准格式（本作 MOD 的既有体例，以 `Race.TXT` 为样本）：
    第0行 = 标题
    第1行 = 日期（如 `1941年4月8日`）
    第2行 = 描述
    …
    含一行 `N 名玩家`
    含一行 `M 回合`
判据（任一成立即列入清单）：
    ① 文件缺失（引擎会回退显示 `_m.txt` 地名清单）
    ② 第0行不像标题（过长 / 是句子而非名词短语）
    ③ 全文不含「N 名玩家」标记
产出：research/_desc-audit.tsv（场景 / 类别 / 说明文件 / 第0行 / 行数 / 有玩家行 / 病征）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
S = os.path.join(G, "SCENARIO")
U = os.path.join(G, "USERSCEN")
OUT = os.path.join(WS, "pegww2", "research", "_desc-audit.tsv")

PLAYER = re.compile(r"(\d+\s*名玩家|\d+\s*Players?|\d+\s*人玩)")
TURN = re.compile(r"(\d+\s*回合|\d+\s*Turns?)")


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def is_title(s):
    if not s or len(s) > 40:
        return False
    if re.search(r"[.!?。！？]\s*$", s) and len(s) > 18:
        return False
    if s.count("，") + s.count(", ") >= 2:
        return False
    return True


def prose_lines(lines):
    """散文句 = 长度 ≥15 且以句末标点收尾（数据文件里全是短 token：`5/5`、`1R/2`、地名）"""
    return [x for x in lines if len(x.strip()) >= 15 and re.search(r"[。！？.!?]$", x.strip())]


PLAYERS_ALT = re.compile(r"(\d+\s*(名)?玩家|\d+\s*Players?|\d+\s*人玩|\d+\s*P\b)")


def main():
    rows = []
    for fn in sorted(os.listdir(S)):
        if not fn.lower().endswith(".scn"):
            continue
        stem = fn[:-4]
        b = open(os.path.join(S, fn), "rb").read()
        if len(b) < 11350:
            rows.append((stem, "短文件", "", "", 0, 0, "scn 过短"))
            continue
        intro, flag = fld(b, 11329), b[11349]
        path = None
        for dd, ex in ((U, ".ply"), (S, ".TXT")) if flag else ((S, ".TXT"), (U, ".ply")):
            for nm in (intro + ex, intro + ex.lower()):
                p = os.path.join(dd, nm)
                if os.path.isfile(p):
                    path = p
                    break
            if path:
                break
        if not path:
            rows.append((stem, "①缺失", f"{'USERSCEN' if flag else 'SCENARIO'}/{intro}"
                         + (".ply" if flag else ".TXT"), "", 0, 0, "引擎将回退显示 _m.txt"))
            continue
        t = open(path, "rb").read().decode("gbk", "replace")
        lines = [x for x in re.split(r"\r\n|\r|\n", t)]
        ne = [x for x in lines if x.strip()]
        first = ne[0].strip() if ne else ""
        has_p = bool(PLAYER.search(t))
        has_t = bool(TURN.search(t))
        probs = []
        pl = prose_lines(ne)
        if not ne:
            probs.append("②空文件")
        elif not pl:
            probs.append("②无散文句(疑似数据文件)")
        elif not is_title(first) and not PLAYERS_ALT.search(t):
            probs.append("③第0行不像标题且无玩家行")
        if probs:
            rows.append((stem, "／".join(probs)[:2], os.path.relpath(path, G), first[:44],
                         len(ne), len(pl), "／".join(probs)))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 说明文件审计（B 方案施工清单）\n")
        f.write("场景\t病征\t说明文件\t第0行\t非空行数\t有玩家行\t问题\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    from collections import Counter
    c = Counter(r[6] for r in rows)
    print(f"扫描 .scn {len(os.listdir(S))} 项 · 列入清单 **{len(rows)}** 个 → {os.path.relpath(OUT, WS)}")
    print("病征分布：")
    for k, v in c.most_common():
        print(f"   {v:4d}  {k}")
    print()
    print("类别分布（①缺失 / ②标题 / ③无玩家行）：")
    c2 = Counter(r[1].split("／")[0] for r in rows)
    for k, v in c2.most_common():
        print(f"   {v:4d}  {k}")


if __name__ == "__main__":
    main()
