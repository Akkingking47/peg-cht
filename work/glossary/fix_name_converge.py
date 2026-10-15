#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""落实 m01055 裁定①「采用新名」：把 docs/43 第三组 12 个键在两作**真源表**里改成新名。

真源（`ingest_layers.py` 实测）：
  · PeG  地图/场景真源 = peg\\research\\scenario-map.tsv      → PEGWW2… 不是；PeG 侧经 gen_scn_zh.py 生成
  · PeG-WW2 场景真源   = pegww2\\research\\ww2-scn-map.tsv    → 层 PEGWW2_SCN（ingest_layers.py:187）
两张表都是 `原文<TAB>译文`，**按英文键整行替换第 1 列**（绝不做全局文本替换：
`Kurina River`→库里纳河 与 `Kuri` 共用子串，文本替换会误伤）。

铁律三：备份与覆盖分两条命令。本脚本默认**干跑**，`--apply` 才写，写完立即回读校验。

用法：
    python fix_name_converge.py            # 干跑（打印逐键命中与新旧值）
    python fix_name_converge.py --apply    # 备份 + 写入 + 回读
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
BACKUP_DIR = os.path.join(WS, "backup", "before-name-converge")

# 新名（m01055 裁定①：采用 docs/43 第三组新名）
NEW = {
    "kuri": "九里",
    "morotsu": "诸津",
    "chio": "千绪",
    "naikawa": "内川",
    "burnoshevo ruskoye": "布尔诺舍沃-鲁斯科耶",
    "burnoshevo russkoye": "布尔诺舍沃-鲁斯科耶",
    "burnoshevo russokoye": "布尔诺舍沃-鲁斯科耶",
    "toro": "塔路",
    "chiwagai": "奇瓦盖",
    "okutai-gawa river": "奥库泰河",
    "okutai-gawa": "奥库泰河",
    "chingyong": "进永",
    "chinyong": "进永",
    "hatsutai": "哈茨泰",
    "acroma": "阿克罗玛",
    "volzhshiy": "伏尔加斯基",
    "wolzskij": "伏尔加斯基",
}

FILES = [
    os.path.join(WS, "peg", "research", "scenario-map.tsv"),
    os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv"),
]


def run(apply_):
    grand = 0
    for p in FILES:
        if not os.path.exists(p):
            print(f"❌ 缺失 {p}")
            continue
        print(f"\n==== {p}")
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            lines = f.readlines()
        hits = []
        out = []
        for i, raw in enumerate(lines, 1):
            body = raw.rstrip("\r\n")
            eol = raw[len(body):]
            if body.startswith("#") or "\t" not in body:
                out.append(raw)
                continue
            c = body.split("\t")
            k = c[0].strip().lower()
            if k in NEW and NEW[k] != c[1]:
                hits.append((i, c[0], c[1], NEW[k]))
                c[1] = NEW[k]
                out.append("\t".join(c) + eol)
            else:
                out.append(raw)
        for i, en, old, new in hits:
            print(f"   L{i:<6d} {en!r:28s} {old!r:26s} → {new!r}")
        print(f"   ⇒ 命中 {len(hits)} 行")
        grand += len(hits)
        if not hits:
            continue
        if not apply_:
            print("   （干跑，未写入）")
            continue
        os.makedirs(BACKUP_DIR, exist_ok=True)
        tgt = os.path.join(BACKUP_DIR, os.path.basename(p))
        if not os.path.exists(tgt):
            shutil.copy2(p, tgt)
            print(f"   已备份 → {tgt}")
        else:
            print(f"   备份已存在（保留首次）→ {tgt}")
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.writelines(out)
        # 回读校验
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            back = f.readlines()
        ok = len(back) == len(lines)
        bad = []
        for (i, en, old, new) in hits:
            c = back[i - 1].rstrip("\r\n").split("\t")
            if c[1] != new:
                bad.append((i, en, c[1]))
        print(f"   回读：行数 {len(back)}/{len(lines)} {'✅' if ok else '❌'}；"
              f"逐条校验 {'✅ 全部生效' if not bad else '❌ ' + str(bad)}")
    print(f"\n合计命中 {grand} 行")


if __name__ == "__main__":
    run("--apply" in sys.argv)
