# -*- coding: utf-8 -*-
r"""GCE 映射表**归一化**（2026-10-08 建立）。

作用对象：`gce-xscn-map.tsv`（= 词典档 948 ∪ 人工批次 727 的合成结果）。
本脚本只做**有据可查**的替换，每条规则都带命中数断言，任一为 0 即报警示；
原表已备份为 `_bak-gce-xscn-map.pre-20261008.tsv`，回滚＝把它拷回来。

规则来源（每条都有出处，不是"看着差不多"）：

  R1 · `[CEM]` → `[摩洛哥军]`（**证据**：CEM = Cuerpo de Ejército Marroquí，
       1937-11-11 组建、雅古埃指挥、隶属北方集团军、参战特鲁埃尔/阿拉贡/埃布罗/加泰罗尼亚。
       中文史料通行译「摩洛哥军」。原译「东方集团军群」无任何依据，且违反本 efile POLICY。）
  R2 · `[1Agrp.]` → `[第1集群]`（**POLICY 三**：`Agrupacion` → 集群。原译「集团军群」把
       兵团级抬成集团军群级，级别错。）
  R3 · 方括号内人名/地名**按 POLICY 六 译出**（donor 整批保留了拉丁原文，
       含 `[Col. A.Vega]` `[Ortiz]` `[Galicia]` `[S.Esteban]` `[Ebro]` `[Diaz Dunabeitia]` …）
  R4 · donor 的「(的)」硬插产物 `[Ejercito (的) Asturias]` → `[阿斯图里亚斯军团]`
  R5 · **罗马数字还原**：src 为 `[XVIII]` 而 dst 被写成 `[18]` ⇒ 还原（POLICY 三；13 条）
  R6 · **全角标点归半角**（`.xscn` 分层口径）

用法:
    python normalize_gce_map.py --check
    python normalize_gce_map.py --apply
"""
import argparse
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, "gce-xscn-map.tsv")
ROMAN = re.compile(r"^[IVXLCDM]+$")
RV = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
BR = re.compile(r"\[([^\]]*)\]")

# ⚠️ 顺序敏感：长键必须排在短键之前（`[东方集团军群 司令部]` 先于 `[东方集团军群]`）
BRACKET_MAP = [
    # R1 / R2 —— 证据与 POLICY 驱动的订正
    ("[东方集团军群 司令部]", "[摩洛哥军司令部]"),
    ("[东方集团军群]", "[摩洛哥军]"),
    ("[CEM HQ]", "[摩洛哥军司令部]"),
    ("[CEM]", "[摩洛哥军]"),
    ("[1Agrp.]", "[第1集群]"),
    # R3 —— 方括号人名/地名（POLICY 六 要求译出）
    ("[Col. Iglesias 司令部]", "[伊格莱西亚斯上校司令部]"),
    ("[Col. Iglesias]", "[伊格莱西亚斯上校]"),
    ("[Col. A.Vega]", "[阿隆索·维加上校]"),
    ("[A.Vega上校]", "[阿隆索·维加上校]"),
    ("[Alonso Vega 司令部]", "[阿隆索·维加司令部]"),
    ("[Diaz Dunabeitia纵队司令部]", "[迪亚斯·杜纳贝蒂亚纵队司令部]"),
    ("[Diaz Dunabeitia]", "[迪亚斯·杜纳贝蒂亚]"),
    ("[Beorlegui纵队司令部]", "[贝奥雷吉纵队司令部]"),
    ("[Los Arcos纵队司令部]", "[洛斯阿尔科斯纵队司令部]"),
    ("[Ortiz纵队司令部]", "[奥尔蒂斯纵队司令部]"),
    ("[Ortiz]", "[奥尔蒂斯]"),
    ("[Galicia]", "[加利西亚]"),
    ("[S.Esteban]", "[圣埃斯特班]"),
    ("[Fuentes de Ebro]", "[埃布罗河畔丰特斯]"),
    ("[Ebro]", "[埃布罗]"),
    ("[Moliner集群]", "[莫利内尔集群]"),
    ("[Com. 希洪]", "[希洪指挥部]"),
    ("[F. Exp. 阿斯图里亚斯]", "[阿斯图里亚斯远征军]"),
    ("[巴斯克第1军]", "[I军 巴斯克]"),
    ("[司令部 Agrupacion Solchaga]", "[索尔查加集群司令部]"),
    ("[司令部 Aranda]", "[阿兰达司令部]"),
    ("[CEA司令部 (Aranda)]", "[CEA司令部(阿兰达)]"),
    # R4 —— donor「(的)」硬插产物（长键在前）
    ("[司令部 Ejercito (的) Asturias]", "[阿斯图里亚斯军团司令部]"),
    ("[Ejercito (的) Asturias]", "[阿斯图里亚斯军团]"),
]

# 整条 dst 覆盖（键 = src 全串，值 = 最终 dst）
#  `R.R.`：09-30 part02 子代理猜成「预备队」—— 无依据。它是组 0 的**地图地名位**
#  （邻居是 Casa de Campo / Moncloa / Puente de Segovia；vgce4 里紧邻 `[R.R. Station]`）。
#  跨 efile 词典实证 `Antwerp [R.R. Station]` → `安特卫普 [火车站]`（4 个 efile）⇒ 取「铁路」。
EXACT_VALUE_OVERRIDES = {
    "R.R.": "铁路",
}

FW2HW = [("（", "("), ("）", ")"), ("［", "["), ("］", "]"),
         ("，", ","), ("、", ","), ("；", ";"), ("：", ":")]


def r2i(s):
    t = 0
    for i, c in enumerate(s):
        t += RV[c] * (1 if i + 1 >= len(s) or RV[c] >= RV[s[i + 1]] else -1)
    return t


def rd2(path):
    rows = []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                rows.append((c[0], c[1]))
    return rows


def norm_dst(s, d, hits):
    """返回归一化后的 dst；hits 记录每条规则命中次数。"""
    # R1–R4：方括号内容精确替换
    def sub(m):
        inner = m.group(1)
        for k, v in BRACKET_MAP:
            if k == "[" + inner + "]":
                hits[k] += 1
                return v
        return m.group(0)
    d = BR.sub(sub, d)
    # R5：罗马数字还原（src 的罗马数字在 dst 里被写成了阿拉伯数字）
    src_romans = [t for t in BR.findall(s) if ROMAN.match(t)]
    if src_romans:
        def sub2(m):
            inner = m.group(1)
            if ROMAN.match(inner):
                return m.group(0)                   # 已是罗马形，不管
            if re.fullmatch(r"\d+", inner):
                for t in src_romans:
                    if r2i(t) == int(inner) and ("[%s]" % t) not in d:
                        hits["R5 罗马数字还原"] += 1
                        return "[%s]" % t
            return m.group(0)
        d = BR.sub(sub2, d)
    # R5b/R5c：**罗马数字 + 文字** 的方括号（POLICY 三 的精神：罗马数字保留原形）
    #   `[V Reservas]` → `[第5预备队]`   ⇒ 该还原成 `[V预备队]`
    #   `[V Reservas]` → `[第V预备队]`   ⇒ 去掉冗余的「第」
    sb, db = BR.findall(s), BR.findall(d)
    if len(sb) == len(db):
        for a, b in zip(sb, db):
            m = re.match(r"^([IVXLCDM]+)\b(.*)$", a)
            if not m:
                continue
            r = m.group(1)
            m2 = re.match(r"^第(\d+)(.*)$", b)
            m3 = re.match(r"^第([IVXLCDM]+)(.*)$", b)
            if m2 and int(m2.group(1)) == r2i(r):
                hits["R5b 罗马+文字还原（第N→罗马）"] += 1
                d = d.replace("[" + b + "]", "[" + r + m2.group(2) + "]", 1)
            elif m3 and m3.group(1) == r:
                hits["R5c 去冗余「第」"] += 1
                d = d.replace("[" + b + "]", "[" + r + m3.group(2) + "]", 1)
    # R6：全角标点 → 半角
    for fw, hw in FW2HW:
        if fw in d and fw not in s:
            hits["R6 全角标点→半角"] += d.count(fw)
            d = d.replace(fw, hw)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rows = rd2(MAP)
    hits = __import__("collections").Counter()
    out = []
    changed = []
    for s, d in rows:
        n = norm_dst(s, d, hits)
        if s in EXACT_VALUE_OVERRIDES and n != EXACT_VALUE_OVERRIDES[s]:
            hits["R7 整条 dst 覆盖"] += 1
            n = EXACT_VALUE_OVERRIDES[s]
        out.append((s, n))
        if n != d:
            changed.append((s, d, n))

    print("映射表 %d 条；改动 %d 条" % (len(rows), len(changed)))
    print("\n规则命中：")
    for k, v in hits.items():
        print("   %-24s %d" % (k, v))
    for k, _ in BRACKET_MAP:
        if hits.get(k, 0) == 0:
            print("   ⚠ 规则未命中（请核）：%s" % k)
    print("\n改动样例（前 25）：")
    for s, d, n in changed[:25]:
        print("   %-40s\n       %s\n    -> %s" % (s[:40], d[:60], n[:60]))

    if a.apply:
        tmp = MAP + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write("src\tdst\n")
            for s, d in out:
                f.write("%s\t%s\n" % (s, d))
        back = rd2(tmp)
        assert back == out, "回读不一致"
        os.replace(tmp, MAP)
        print("\n已写 %s（%d 条）" % (os.path.basename(MAP), len(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
