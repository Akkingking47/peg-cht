# -*- coding: utf-8 -*-
r"""GCE **通名 vs 专名** 判别器（09-30）。

背景：上游词典给 GCE 的命中里，**通名被当专名音译**（`Alambradas`＝铁丝网 → 「阿兰布拉达斯」），
与 COMWW2 轮 `donor 恒等保留` 吞普通名词**同型**。本脚本把词典档按「通名 / 存疑 / 专名」三分类，
只把**通名**交给覆盖表处理，专名（地名/人名）不动。

判别依据：
  1. **西语通名词根表**（本文件 `COMMON_ROOTS`）—— 命中即判「通名」；
  2. 其余一律判「专名」（地名/人名/番号，音译正确）。

用法: python classify_gce_dict.py
产出: `_gce_common_hits.tsv`（通名，需覆盖）· 终端打印全部命中
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# 西语军事/地形通名词根 → 中文（用于覆盖上游音译）
COMMON_ROOTS = [
    ("alambrada", "铁丝网"),
    ("blocao", "碉堡"),
    ("barricada", "街垒"),
    ("trinchera", "战壕"),
    ("pista", "跑道"),
    ("aerodromo", "机场"),
    ("aeropuerto", "机场"),
    ("puente", "桥"),
    ("estacion", "车站"),
    ("hospital", "医院"),
    ("fabrica", "工厂"),
    ("carretera", "公路"),
    ("camino", "道路"),
    ("cuartel", "兵营"),
    ("cementerio", "公墓"),
    ("convento", "修道院"),
    ("iglesia", "教堂"),
    ("pantano", "水库"),
    ("fortin", "碉堡"),
    ("vado", "渡口"),
    ("observatorio", "观察所"),
    ("deposito", "仓库"),
    ("almacen", "仓库"),
    ("bateria", "炮台"),
    ("polvorin", "弹药库"),
    ("refugio", "掩体"),
    ("trinchera", "战壕"),
]


def rd2(path):
    out = []
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                out.append((c[0], c[1]))
    return out


def main():
    cov = rd2(os.path.join(HERE, "_xscn_covered.tsv"))
    hits = []
    for s, d in cov:
        low = s.strip().lower()
        if not low or re.search(r"[\d/\[\]\(\)]", s):
            continue
        for root, zh in COMMON_ROOTS:
            if low.startswith(root) or low == root:
                hits.append((s, d, zh))
                break
    seen = set()
    print("词典档 %d 条；判为**通名**（上游音译需覆盖）%d 条：" % (len(cov), len(hits)))
    for s, d, zh in hits:
        if s in seen:
            continue
        seen.add(s)
        print("  %-26s 上游=%s  ⇒ 应为「%s」" % (s, d, zh))
    out = os.path.join(HERE, "_gce_common_hits.tsv")
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        f.write("src\tcur_dst\tshould\n")
        for s, d, zh in hits:
            f.write("%s\t%s\t%s\n" % (s, d, zh))
    print("→ %s" % out)


if __name__ == "__main__":
    main()
