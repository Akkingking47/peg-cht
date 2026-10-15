#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 跨层地名一致性审计（简报「中文(原文)」对照 vs 地图格名 / 词库键）。

前作 PeG 的教训：简报里写「卡拉奇(Kalatsch)」，地图上那一格却成了别的译名 ⇒ 玩家对不上。

本脚本做三件事：
  A 括号对照 vs 地图键：散文译文里的 `X(Y)`，若真源中存在键 `Y`，则要求 X 与 `Y` 的译文一致
  B 同键多译：本层按原文串键控 ⇒ 结构上不可能 ⇒ 只做断言（列出违反者，应为 0）
  C 近似拼写分叉：归一化后同形（如 Kalatsch/Kalatch）却给出不同中文名 ⇒ 高风险
产出：research/_name-audit-A.tsv / _name-audit-C.tsv
"""
import os
import re
from collections import defaultdict

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
OUTA = os.path.join(RES, "_name-audit-A.tsv")
OUTC = os.path.join(RES, "_name-audit-C.tsv")

PAIR = re.compile(r"([\u4e00-\u9fff][\u4e00-\u9fff·・'’\-]{1,24})[（(]\s*([A-Za-z][A-Za-z0-9 .'’\-]{1,40}?)\s*[)）]")


def norm(s):
    return re.sub(r"[^0-9a-z]", "", s.lower())


def main():
    rows = []
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows.append((f[0], f[1], f[2] if len(f) > 2 else ""))
    by_src = {r[0]: r[1] for r in rows if r[1].strip()}
    mapname_keys = {r[0]: r[1] for r in rows if "m 地图格名" in r[2] and r[1].strip()}

    # A 括号对照 vs 地图键
    #   判据（稳）：散文行里的 `(原文)` ⇒ 查真源该键的**权威译名**（去掉它自带的 (原文) 部分）
    #              ⇒ 若该权威译名**没有出现在这句散文译文里** ⇒ 说明散文用了别的叫法 = 不一致
    #   （早期版本用「括号前的中文片段」比对，会把「即西西里」「正在马雷特防线」的前置普通词也算进名字 ⇒ 误报）
    def clean(s):
        return re.sub(r"[（(][^（()）]*[)）]", "", s).strip()

    # ⚠️ 比较前**去掉引号/书名号**：散文常写「堡垒」行动，地图写 堡垒行动 —— 同一名字，不算不一致
    QS = "「」『』“”\"'《》"

    def deq(s):
        return "".join(c for c in s if c not in QS)

    a_hits, a_ok, a_miss = [], 0, 0
    for src, zh, cls in rows:
        if not zh.strip() or ("(" not in zh and "（" not in zh):
            continue
        for m in PAIR.finditer(zh):
            orig = m.group(2).strip()
            want = mapname_keys.get(orig) or by_src.get(orig)
            if not want:
                a_miss += 1
                continue
            want_c = clean(want)
            if not want_c:
                a_miss += 1
                continue
            if deq(want_c) in deq(zh) or (len(deq(want_c)) >= 3 and deq(want_c)[:3] in deq(zh) and deq(want_c)[-2:] in deq(zh)):
                a_ok += 1
            else:
                # 展示括号前的中文片段（去噪声：取最后 14 字）
                before = zh[:m.start(1) + len(m.group(1))]
                a_hits.append((src[:46], before[-14:], orig, want))
    with open(OUTA, "w", encoding="utf-8", newline="\n") as f:
        f.write("# A：散文括号里的地名 vs 地图/词库同键译名 —— 不一致项\n")
        f.write("原文(散文行)\t括号里的译名\t括号里的原文\t真源中该键的译名\n")
        for r in a_hits:
            f.write("\t".join(r) + "\n")

    # B 同键多译（应为 0）
    seen = defaultdict(set)
    for src, zh, cls in rows:
        if zh.strip():
            seen[src].add(zh)
    b_bad = [(k, v) for k, v in seen.items() if len(v) > 1]

    # C 近似拼写分叉（只在**地图格名**类里查，避免把整句当名字）
    g = defaultdict(set)
    for src, zh, cls in rows:
        if "m 地图格名" not in cls or not zh.strip():
            continue
        k = src.strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9 .'’\-]{4,40}", k) and k.lower() not in ("dummy",):
            g[norm(k)].add((k, clean(zh)))
    c_hits = []
    for nk, items in g.items():
        zhs = {v for _, v in items if v}
        if len(items) > 1 and len(zhs) > 1:
            c_hits.append((sorted({k for k, _ in items}), sorted(zhs)))
    c_hits.sort(key=lambda x: -len(x[0]))
    with open(OUTC, "w", encoding="utf-8", newline="\n") as f:
        f.write("# C：近似拼写（归一化同形）却给出不同中文名 —— 可能是「同一地点两种叫法」\n")
        f.write("相关原文\t不同中文名\n")
        for ks, zs in c_hits:
            f.write("\t".join([" | ".join(ks), " / ".join(zs)]) + "\n")

    print("=" * 96)
    print("跨层地名一致性审计")
    print("=" * 96)
    print(f"  A 括号对照：一致 {a_ok} · **不一致 {len(a_hits)}** · 真源无此键（无法核对）{a_miss}")
    print(f"      → {os.path.relpath(OUTA, WS)}")
    print(f"  B 同一原文给出多种译名（结构上应为 0）：{len(b_bad)} {'✅' if not b_bad else '❌'}")
    for k, v in b_bad[:5]:
        print(f"      {k[:40]!r} → {sorted(v)[:3]}")
    print(f"  C 近似拼写分叉：{len(c_hits)} 组 → {os.path.relpath(OUTC, WS)}")
    print()
    print("  —— A 不一致 top 30 ——")
    for src, name, orig, want in a_hits[:30]:
        print(f"    散文「{name}」({orig})  但真源键 `{orig}` 的译名是「{want}」")
    print()
    print("  —— C 近似拼写分叉 top 20 ——")
    for ks, zs in c_hits[:20]:
        print(f"    {ks[:3]} ⇒ {zs}")


if __name__ == "__main__":
    main()
