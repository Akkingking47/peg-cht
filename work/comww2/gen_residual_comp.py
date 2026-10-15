#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批次 4 合成档：`专名 + 通名` → 词典译名 + 中文通名

依据 **POLICY.md 规则 5**：「地名：有通行中文名的用通行名；否则音译 + 通名后缀
（River→河，Sea→海，Canal→运河，Airfield→机场，Station→站，Lake→湖，Bay→湾）」
⇒ 只要**专名本身**在词典里有既有译法，`专名+通名` 即可按政策合成，**不是猜**。

安全约束（防 B 档那种"丢名字"事故）：
  1. 通名必须来自白名单，且必须是整词（词边界）；
  2. 专名部分必须**整体**有词典译法（精确或归一化），不得只匹配其中一段；
  3. 合成结果里必须**包含专名的全部译名字符**（防 `Lake Velencei`→「湖泊」这类只剩通名）。
产出：xscn-new-4-comp.tsv（src \t dst），并打印抽样供复核。
用法: python gen_residual_comp.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv"
SNAP = os.path.join(HERE, "xscn-uniq-after3.tsv")
OUT = os.path.join(HERE, "xscn-new-4-comp.tsv")

# 通名白名单 → 中文（POLICY 规则 5 及同类）
TYPE = {
    "river": "河", "airfield": "机场", "lake": "湖", "bay": "湾", "canal": "运河",
    "sea": "海", "station": "站", "harbour": "港", "harbor": "港", "port": "港",
    "island": "岛", "ridge": "岭", "mountain": "山", "hill": "丘陵", "valley": "谷",
    "bridge": "桥", "docks": "码头", "dock": "码头", "depot": "库", "factory": "工厂",
    "factories": "工厂", "village": "村", "town": "镇", "city": "城",
    "airbase": "机场", "railway": "铁路", "station ": "站",
}
NORM = lambda x: re.sub(r"\s+", " ", x.strip().rstrip(".").lower())


def main():
    dic = {}
    dicN = {}
    with io.open(DICT, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 3 and c[1].strip():
                dic.setdefault(c[0], c[1])
                dicN.setdefault(NORM(c[0]), c[1])

    used = set()
    with io.open(os.path.join(HERE, "comww2-xscn-map.tsv"), encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i and ln.strip():
                used.add(ln.split("\t")[0])

    res = []
    with io.open(SNAP, encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c[0] and c[0] not in used:
                res.append(c[0])

    rows, skipped = [], []
    for s in res:
        m = re.fullmatch(r"(.+?)\s+([A-Za-z]+)", s.strip())
        if not m:
            skipped.append(s)
            continue
        head, tail = m.group(1).strip(), m.group(2).strip()
        if tail.lower() not in TYPE:
            skipped.append(s)
            continue
        zh = dic.get(head) or dicN.get(NORM(head))
        if not zh:
            skipped.append(s)
            continue
        # 守卫：合成结果必须包含专名译名的全部字符
        core = re.sub(r"[\s（）()]", "", zh)
        tz = TYPE[tail.lower()]
        # 守卫：词典译名已含该通名（如 `Rhein`→莱茵河）⇒ 不重复追加
        out = zh.rstrip() if zh.rstrip().endswith(tz) else "%s%s" % (zh.rstrip(), tz)
        if not core or core not in re.sub(r"[\s（）()]", "", out):
            skipped.append(s)
            continue
        try:
            out.encode("gbk")
        except UnicodeEncodeError:
            skipped.append(s)
            continue
        rows.append((s, out))

    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in rows:
            f.write("%s\t%s\n" % (s, d))
    print("合成档: 输出 %d 条 / 跳过 %d 条" % (len(rows), len(skipped)))
    for s, d in rows[:60]:
        print("   %-34s -> %s" % (s[:34], d))
    print("   ...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
