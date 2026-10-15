#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 人名表**独立核验**（值模式）。

核验项：
  ① 唯一串集合与备份一致（含表末 DOS EOF 标记 \x1a）
  ② 空译文仅允许出现在 \x1a 占位行
  ③ 译文只含汉字（无拉丁字母/无标点混入）
  ④ 同串译法一致；⑤ 禁用译法；⑥ 行数
  ⑦ 列出 18 条「拿不准」项的当前值供人工裁定
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "text", "WW2NAME.TXT")
MAP = os.path.join(WS, "pegww2", "research", "WW2NAME-map.tsv")
BAN = os.path.join(WS, "pegww2", "research", "banned.tsv")
OUTD = os.path.join(WS, "pegww2", "research")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)

FLAGGED = ["Losch", "Obermann", "Oststein", "Pahner", "Fassbender", "Kepplers", "Inmann",
           "Thaler", "Theissen", "Maechich", "Vayaslava", "Breshkovsky", "Emirzyan",
           "Glushko", "Mikhoels", "Kvitinsky", "Orenkhova", "Rodos"]


def main():
    raw = open(BK, "rb").read()
    src = [x.decode("cp1252") for x in re.split(rb"\r\n|\r|\n", raw)]
    srcset = set(x for x in src if x.strip() != "" or x == "\x1a")
    rows = []
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            rows.append(s.split("\t"))
    banned = []
    with open(BAN, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s and not s.startswith("#"):
                banned.append(s.split("\t")[0].strip())

    print("=" * 92)
    print("① 唯一串集合 vs 备份")
    print("=" * 92)
    mapset = [f2[0] for f2 in rows]
    missing = sorted(x for x in srcset if x not in set(mapset))
    extra = sorted(x for x in mapset if x not in srcset)
    print(f"  map 数据行 {len(rows)} · 备份唯一串（含 \\x1a）{len(srcset)}")
    print(f"  备份中未进 map: {len(missing)} {'✅' if not missing else '❌ ' + repr(missing[:6])}")
    print(f"  map 中不在备份: {len(extra)} {'✅' if not extra else '❌ ' + repr(extra[:6])}")

    print()
    print("=" * 92)
    print("② 空译文 / ③ 译文字符集 / ④ 同串一致 / ⑤ 禁用译法 / ⑥ 行数")
    print("=" * 92)
    empty = [(i + 1, f2[0]) for i, f2 in enumerate(rows) if len(f2) < 2 or not f2[1].strip()]
    ok_empty = all(o == "\x1a" for _, o in empty)
    print(f"  ② 空译文 {len(empty)} 处 {'✅ 仅 \\x1a 占位行' if ok_empty else '❌ ' + repr(empty[:6])}")
    badchr = []
    for i, f2 in enumerate(rows):
        if len(f2) >= 2 and f2[1].strip():
            if not re.fullmatch(r"[\u4e00-\u9fff·]+", f2[1].strip()):
                badchr.append((i + 1, f2[0], f2[1]))
    print(f"  ③ 译文含非汉字字符: {len(badchr)} 处 {'✅' if not badchr else '❌'}")
    for i, o, z in badchr[:12]:
        print(f"      行{i} {o} ⇒ {z}")
    byval = defaultdict(set)
    for f2 in rows:
        if len(f2) >= 2:
            byval[f2[0]].add(f2[1])
    inc = {k: v for k, v in byval.items() if len(v) > 1}
    print(f"  ④ 同串译法不一致: {len(inc)} {'✅' if not inc else '❌ ' + repr(list(inc.items())[:4])}")
    hit = [(i + 1, f2[0], f2[1]) for i, f2 in enumerate(rows) if len(f2) >= 2 and f2[1].strip() in banned]
    print(f"  ⑤ 禁用译法: {len(hit)} {'✅' if not hit else '❌ ' + repr(hit[:5])}")
    print(f"  ⑥ map 行数 {len(rows) + 4}（含 4 行注释；原 404）")

    print()
    print("=" * 92)
    print("⑦ 「拿不准」18 项当前值（人工裁定用）")
    print("=" * 92)
    idx = {f2[0]: f2[1] for f2 in rows if len(f2) >= 2}
    for k in FLAGGED:
        print(f"    {k:16s} ⇒ {idx.get(k, '（不在表内）')}")
    print()
    print(f"  来源分布: {dict(Counter(f2[2] if len(f2) > 2 else '—' for f2 in rows))}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(OUTD, "evidence"), exist_ok=True)
    with open(os.path.join(OUTD, "evidence", "verify-name.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
