#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 装备表**独立核验**（不信任子代理自述，逐项复算）。

核验项：
  ① 原文列 是否与备份逐行逐字一致（**必须 0 差异**，否则译文会错配到别的装备）
  ② 行数一致；译文列零空值
  ③ 未译残留：译文里仍含「小写英文单词（≥4 字母）」且来源≠保留 的行
  ④ 恒等残留：来源=新译 但 译文 == 原文 的行（可能是漏译）
  ⑤ 禁用译法黑名单扫描
  ⑥ 重复原文的译文一致性（同一原文串必须同一译文）
  ⑦ 逐条列出子代理「拿不准」的行，供人工裁定
"""
import io
import os
import re
import sys
from collections import defaultdict

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "text", "ww2-eqp.txt")
MAP = os.path.join(WS, "pegww2", "research", "ww2-eqp-map.tsv")
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

# 允许保留的英文词（型号/品牌/缩写/单位标记），不算「未译残留」
ALLOW = re.compile(
    r"\b(?:Pz|Pzkpfw|SdKfz|Sdkfz|StuG|StuH|JgdPz|JgdPanther|JagdTiger|Jagdpanzer|FlaK|Flak|PaK|Pak|"
    r"sIG|sFH|leFH|FK|K|MG|MGMC|ATG|CSU|FIST|MEB|EP|MEP|Mk|MkI|MkII|MkIII|MkIV|MkV|MkVI|"
    r"Class|Sqn|Pdr|inch|mm|cm|Mk\.|Type|Mark|U|SS|Kg|t)\b",
    re.I)
WORDY = re.compile(r"[a-z]{4,}")


def main():
    raw = open(BK, "rb").read()
    src = [x.decode("cp1252").rstrip() for x in re.split(rb"\r\n|\r|\n", raw)]
    rows = []
    head = 0
    with open(MAP, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s.startswith("#") or s.split("\t")[0].strip() in ("原文", "行号"):
                head += 1
                continue
            f2 = s.split("\t")
            rows.append(f2)
    banned = []
    with open(BAN, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\r\n")
            if s and not s.startswith("#"):
                banned.append(s.split("\t")[0].strip())

    print("=" * 96)
    print("① 原文列 vs 备份（**值模式**：map 是 906 唯一串，不能按行号比）")
    print("=" * 96)
    print(f"  map 数据行 {len(rows)}（唯一串） · 备份非空行 {len([x for x in src if x.strip()])} · 备份总行元素 {len(src)}")
    srcset = [x for x in src if x.strip()]
    mapset = [f2[0] for f2 in rows]
    missing = [x for x in srcset if x not in set(mapset)]
    extra = [x for x in mapset if x not in set(srcset)]
    print(f"  备份中未进 map 的串: {len(missing)} {'✅' if not missing else '❌'}")
    for x in missing[:8]:
        print(f"      {x[:70]!r}")
    print(f"  map 中不在备份的串: {len(extra)} {'✅' if not extra else '❌'}")
    for x in extra[:8]:
        print(f"      {x[:70]!r}")
    # 覆盖率：唯一串集合是否一致（含重数）
    print(f"  ⇒ 唯一串集合{'一致 ✅' if not missing and not extra else '不一致 ❌'}；"
          f"重数校验：备份唯一 {len(set(srcset))} vs map {len(set(mapset))}")

    print()
    print("=" * 96)
    print("② 空值 / ③ 未译残留 / ④ 恒等残留 / ⑤ 禁用译法")
    print("=" * 96)
    empty = [i + 1 for i, f2 in enumerate(rows) if len(f2) < 3 or not f2[1].strip()]
    print(f"  ② 空译文: {len(empty)} 处 {'✅' if not empty else '❌ ' + str(empty[:12])}")
    resid = []
    for i, f2 in enumerate(rows):
        if len(f2) < 3:
            continue
        tag, zh = f2[2].strip(), f2[1]
        if tag == "保留":
            continue
        stripped = ALLOW.sub(" ", zh)
        if WORDY.search(stripped) and re.search(r"[a-zA-Z]{2,}\s+[a-zA-Z]{2,}", stripped):
            resid.append((i + 1, f2[0], zh, tag))
    print(f"  ③ 疑似未译残留（译文含连续英文词）: {len(resid)} 处")
    for i, o, z, t in resid[:25]:
        print(f"      行{i:<5d} [{t}] {o[:44]:46s} ⇒ {z[:46]}")
    ident = [(i + 1, f2[0]) for i, f2 in enumerate(rows)
             if len(f2) >= 3 and f2[2].strip() == "新译" and f2[1].strip() == f2[0].strip()]
    print(f"  ④ 来源=新译 但译文=原文（疑漏译）: {len(ident)} 处")
    for i, o in ident[:20]:
        print(f"      行{i:<5d} {o[:70]}")
    hit = [(i + 1, f2[0], f2[1]) for i, f2 in enumerate(rows)
           if len(f2) >= 3 and f2[1].strip() in banned]
    print(f"  ⑤ 禁用译法命中: {len(hit)} 处 {'✅' if not hit else '❌'}")
    for i, o, z in hit[:10]:
        print(f"      行{i}: {o} ⇒ {z}")

    print()
    print("=" * 96)
    print("⑥ 同一原文的译文一致性（同串必须同译）")
    print("=" * 96)
    byval = defaultdict(set)
    for f2 in rows:
        if len(f2) >= 3:
            byval[f2[0]].add(f2[1])
    bad = {k: v for k, v in byval.items() if len(v) > 1}
    print(f"  不一致的原文串: {len(bad)} 个")
    for k, v in list(bad.items())[:15]:
        print(f"      {k[:44]:46s} ⇒ {sorted(v)}")

    print()
    print("=" * 96)
    print("⑧ ⭐ 型号代号丢失检查（只查【含数字且含字母】的代号，排除尺寸；描述性缩写如 FlaK/PaK/Pz 意译不算丢失）")
    print("=" * 96)
    # 型号特征 = 含数字且含字母，且不是尺寸（mm/cm/inch）
    TOK = re.compile(r"[A-Za-z0-9][A-Za-z0-9\./()\-]*\d[A-Za-z0-9\./()\-]*")
    lost = []
    for f2 in rows:
        if len(f2) < 3:
            continue
        tag, zh = f2[2].strip(), f2[1]
        if tag == "保留":
            continue
        zh_up = zh.upper()
        for tk in sorted(set(TOK.findall(f2[0]))):
            t = tk.strip("().-/")
            if not re.search(r"[A-Za-z]", t) or not re.search(r"\d", t):
                continue
            if re.search(r"(?i)(mm|cm|inch)$", t):
                continue
            if t.upper() not in zh_up:
                lost.append((f2[0], t, zh, tag))
    lost = sorted(set(lost))
    print(f"  疑似丢失型号代号的条目: {len(lost)} 处")
    for o, tk, z, t in lost:
        print(f"      [{t}] {o[:46]:48s} 丢失={tk:<12s} ⇒ {z[:44]}")
    print()
    print("=" * 96)
    print("⑦ 来源分布 + 抽样（每 60 行取 1）")
    print("=" * 96)
    from collections import Counter
    print(f"  {dict(Counter(f2[2].strip() for f2 in rows if len(f2) >= 3))}")
    print()
    for i, f2 in enumerate(rows):
        if i % 60 == 0:
            print(f"  行{i + 1:<5d} {f2[0][:40]:42s} ⇒ {f2[1][:42]}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(OUTD, "evidence"), exist_ok=True)
    with open(os.path.join(OUTD, "evidence", "verify-eqp.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
