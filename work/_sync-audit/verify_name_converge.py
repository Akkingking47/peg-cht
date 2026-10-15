#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""只读验证「裁定① 采用新名」是否贯穿三层：词库层表 → 两作成品目录。
单趟扫描（一次遍历同时统计所有关键词），避免 N 次全目录遍历。"""
import io
import os

WS = r"D:\DSH\军事游戏汉化"
LAY = os.path.join(WS, "glossary", "layers")

KEYS = [
    ("Acroma", "阿克罗马", "阿克罗玛"),
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
    ("Wolzskij", "沃尔日斯基", "伏尔加斯基"),
    ("Volzhshiy", "沃尔日斯基", "伏尔加斯基"),
]
EXTRA = ["库里纳河"]           # 易误伤：Kurina River（Kuri=库里 的子串）

TARGETS = [
    ("PeG 生成产物", os.path.join(WS, "peg", "testbed", "scn-zh")),
    ("PeG 游戏目录", r"D:\Program Files\PeG"),
    ("WW2 生成产物", os.path.join(WS, "pegww2", "testbed", "out")),
    ("WW2 游戏目录", r"D:\Program Files\PeG-WW2"),
]


def scan(root, needles):
    """一次遍历，返回 {needle: (次数, 文件数)}。"""
    cnt = {k: 0 for k in needles}
    fil = {k: 0 for k in needles}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                t = open(p, "rb").read().decode("gbk", errors="replace")
            except OSError:
                continue
            for k in needles:
                c = t.count(k)
                if c:
                    cnt[k] += c
                    fil[k] += 1
    return cnt, fil


print("=== A. 词库层表里的值（按 scope）")
rows = {}
for fn in ("common-glossary.tsv", "scope-glossary.tsv"):
    for line in io.open(os.path.join(LAY, fn), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) >= 4:
            rows.setdefault(c[0], set()).add((c[1], c[3]))
for en, old, new in KEYS:
    got = rows.get(en)
    if not got:
        print(f"  {en:24s} ⚠️ 层表无此键")
        continue
    marks = [f"{zh}({scope})" + ("✅新" if zh == new else ("·旧" if zh == old else "?"))
             for zh, scope in sorted(got)]
    print(f"  {en:24s} {' | '.join(marks)}")

needles = []
for _en, old, new in KEYS:
    needles += [old, new]
needles += EXTRA
needles = sorted(set(needles))

print("\n=== B/C. 成品目录（单趟扫描）")
for label, root in TARGETS:
    if not os.path.isdir(root):
        print(f"  ── {label}: ⚠️ 目录不存在")
        continue
    cnt, fil = scan(root, needles)
    print(f"  ── {label}")
    for en, old, new in KEYS:
        no, nn = cnt[old], cnt[new]
        flag = "✅" if (nn > 0 and no == 0) else ("⚠️旧名残留" if no else ("—无此键" if nn == 0 else "❓"))
        print(f"     {en:24s} 旧 {old}×{no:<5d} 新 {new}×{nn:<5d} {flag}")
    for e in EXTRA:
        print(f"     [易误伤] {e}×{cnt[e]}（{fil[e]} 个文件，应保持不变）")
