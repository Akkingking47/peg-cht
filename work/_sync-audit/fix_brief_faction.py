#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""落实用户裁定 ③「简报测按阵营方描述来统一」：
在**真源** `peg\\research\\scenario-long-zh.tsv` 上做定行替换（不碰产出文件，产出由生成器重建）。

两处改动（依据见 docs/49）：
1. `Suchan` —— 地图名栏（`scenario-map.tsv:156`）与词库（`standard-glossary.tsv:20844`）都作
   **苏昌**，而简报侧 7 处作 **苏城** ⇒ 统一为 **苏昌**（无按势力分叉，纯统一）。
2. `Amur River` —— `Khabarovsk3mp`（「强袭哈巴罗夫斯克（3 人）」）里越河的是
   **俄罗斯与美国**，该场景玩家即西方/俄方 ⇒ 按俄方名作 **阿穆尔河**（原为黑龙江）。
   ※ `Khabarovsk4`（玩家=中华人民共和国）与 `Khabarovsk3`/`Khabarovskrri`（玩家=俄）分别正确，不动。

默认干跑；`--apply` 先备份再写、写完回读校验。
"""
import collections
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
LT = os.path.join(WS, r"peg\research\scenario-long-zh.tsv")
BAK = os.path.join(WS, r"backup\before-brief-faction")
APPLY = "--apply" in sys.argv

SUCHAN_OLD, SUCHAN_NEW = "苏城", "苏昌"
AMUR_ANCHOR = "With the People's Republic of China assembling troops in Khabaro"
AMUR_OLD, AMUR_NEW = "黑龙江", "阿穆尔河"

with io.open(LT, encoding="utf-8-sig") as f:
    raw = f.read()
lines = raw.split("\n")

hits = collections.Counter()
out = []
for i, ln in enumerate(lines, 1):
    parts = ln.split("\t")
    if len(parts) >= 2 and parts[0] != "原文":
        n = parts[1].count(SUCHAN_OLD)
        if n:
            parts[1] = parts[1].replace(SUCHAN_OLD, SUCHAN_NEW)
            hits["苏城→苏昌"] += n
            print(f"  L{i:<5} 苏城→苏昌 ×{n}")
        if parts[0].startswith(AMUR_ANCHOR):
            n2 = parts[1].count(AMUR_OLD)
            if n2:
                parts[1] = parts[1].replace(AMUR_OLD, AMUR_NEW)
                hits["黑龙江→阿穆尔河"] += n2
                print(f"  L{i:<5} 黑龙江→阿穆尔河 ×{n2}（Khabarovsk3mp）")
        ln = "\t".join(parts)
    out.append(ln)

print(f"\n合计：{dict(hits)}  行数 {len(lines)}")
if not APPLY:
    print("（干跑，未写盘；加 --apply 生效）")
    raise SystemExit(0)

os.makedirs(BAK, exist_ok=True)
shutil.copy2(LT, os.path.join(BAK, "scenario-long-zh.tsv"))
with io.open(LT, "w", encoding="utf-8-sig", newline="") as f:
    f.write("\n".join(out))
with io.open(LT, encoding="utf-8-sig") as f:
    back = f.read()
assert back == "\n".join(out), "⛔ 回读不一致"
print(f"✅ 已写 {LT}（备份 {BAK}）· 回读一致 · 行数 {len(back.split(chr(10)))}")
