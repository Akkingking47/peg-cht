# -*- coding: utf-8 -*-
r"""审计 GCE 词典档里的**通名陷阱**（音译代替意译）。

起因（09-30）：`Alambradas`（西语＝铁丝网，通名）被上游词典音译成「阿兰布拉达斯」——
即 COMWW2 轮 `donor 恒等保留` 吞普通名词的**同型错误**，只是这次是「音译通名」。

判据（启发式，**人工复核**，不自动改）：
  1. 原文是**单个西语普通名词**（无大写、无数字、无斜杠、长度 ≥5）；
  2. 译文是**纯音译**（≥4 个汉字、不含任何「通名汉字」：山/河/桥/路/城/村/营/师/旅/团/军/队/厂/站/线/门/塔/堡/仓/库/沟/壕/林/园/场）；
  3. 它在 `POLICY.md` 的通名表里，或与表中词同根。
命中即登记到 `_gce_override.tsv`（人工填 dst），供 `build_xscn_map.py` **优先覆盖**词典。

用法: python audit_gce_dict.py
"""
import collections
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HAN = re.compile(r"[\u4e00-\u9fff]")
GEN = "山河桥路城村营师旅团军队厂站线门塔堡仓库沟壕林园场岛屿洲湾港街巷院宫堡"

# 已知的 GCE 通名（西语 → 中文），与 POLICY.md 一致
COMMON = {
    "Alambradas": "铁丝网",
    "Barricada": "街垒",
    "Barricadas": "街垒",
    "Trincheras": "战壕",
    "Trinchera": "战壕",
    "Puente": "桥",
    "Estacion": "车站",
    "Hospital": "医院",
    "Fabrica": "工厂",
    "Camino": "道路",
    "Carretera": "公路",
    "Cota": "高地",
    "Fortin": "碉堡",
    "Vado": "渡口",
    "Pista": "跑道",
    "Aerodromo": "机场",
    "Cuartel": "兵营",
    "Cementerio": "公墓",
    "Convento": "修道院",
    "Iglesia": "教堂",
    "Pantano": "水库",
}


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
    sus = []
    for s, d in cov:
        st = s.strip()
        if not st or " " in st or st != st[0].upper() + st[1:]:
            continue
        if re.search(r"[\d/\[\]\(\)\.]", st):
            continue
        if st in COMMON:
            sus.append((s, d, COMMON[st]))
            continue
        # 纯音译特征：译文 ≥4 汉字且无通名汉字
        if len(st) >= 5 and len(d) >= 4 and HAN.search(d) and not any(ch in d for ch in GEN):
            sus.append((s, d, ""))
    print("词典档 %d 条；可疑（通名被音译/无通名字）%d 条：" % (len(cov), len(sus)))
    for s, d, sug in sus:
        print("  %-22s -> %-14s %s" % (s, d, ("建议：" + sug) if sug else ""))
    out = os.path.join(HERE, "_gce_override_candidates.tsv")
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        f.write("src\tcur_dst\tsuggested\n")
        for s, d, sug in sus:
            f.write("%s\t%s\t%s\n" % (s, d, sug))
    print("→ %s（人工复核后再进 _gce_override.tsv）" % out)


if __name__ == "__main__":
    main()
