#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理 · **生成段级统一裁定表** `glossary\\layers\\seg-canon.tsv`。

只针对**真冲突**：同一段英文在映射表里由**两条以上都来自词库**的写法（`src=词库/POLICY`），
且经 `_seg_filecheck.py` 证实**同一成品文件内并列**（= 玩家可见的不一致）。
「槽位受限/人工确认」的写法不在本表内，不动。

裁定优先级：
  1. 本表 `OVR`（逐条人工裁定，附依据）——**最高**
  2. 词库裸段·本作层（`PEGWW2*`）
  3. 词库裸段·前作层（`EFILE_*` 等）
  4. 映射表内多数写法
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GL = os.path.join(WS, "glossary")
LAY = os.path.join(GL, "layers")
RES = os.path.join(WS, "pegww2", "research")
OUT2 = os.path.join(LAY, "seg-canon.tsv")
SKIP_SEG = re.compile(r"^\[?[0-9A-Za-z]{0,3}\]?$|^[-–—/]+$|^\[[IVXL]+\]$")
MINE = ("PEGWW2", "PEG-WW2")

# ── 逐条人工裁定（依据写在第 4 列）──────────────────────────────────────────────
OVR = {
    # A. 未译残留 → 补译
    "USAAF": ("美国陆军航空队", "词库·本作层 PEGWW2_SCN/UNIT"),
    "HG D": ("赫尔曼·戈林师", "词库·本作层 PEGWW2_SCN/UNIT"),
    "1 Br": ("第1旅", "词库 EFILE_OLGWW2/UNIT"),
    "9 Aust.": ("第9澳大利亚师", "本项目「第X师」体例；词库前作层作「9澳大利亚师」无「第」"),
    "90 LD": ("第90轻装师", "词库 EFILE_OLGWW2/UNIT"),
    "164 LD": ("第164轻装师", "词库 EFILE_OLGWW2/UNIT"),
    "17SS": ("党卫军第17师", "词库·本作层 PEGWW2_SCN/UNIT；场景层另作「第17党卫军」"),
    "1 SA": ("第1南非师", "词库 EFILE_OLGWW2/UNIT"),
    "8 FR": ("第8野战团", "FR=Field Regiment；本项目「第X团」体例（词库另有「野战炮兵团」写法）"),
    "LF2": ("第2航空队", "词库·本作层「Luftflotte 2 = 第2航空队」"),
    "GD [48]": ("大德意志 [48]", "GD=Grossdeutschland「大德意志」；词库 PLACE 层未译"),
    "Carpathian Rifle Brigade": ("喀尔巴阡步枪旅", "波兰第1独立喀尔巴阡步枪旅；词库前作层作「卡尔帕蒂亚」"),
    "Polish": ("波兰", "与同族行「喀尔巴阡步枪旅/ 波兰」一致"),
    "StG1": ("第1俯冲轰炸机联队", "StG=Sturzkampfgeschwader"),
    # B. 错译改正
    "1 African D": ("第1南非师", "South African=南非；词库作「第1非洲师」系错译（m01492：词库是约束不是事实源）"),
    "2 African D": ("第2南非师", "同上"),
    "4 Ind": ("第4印度师", "Indian=印度，非「独立」；词库前作层作「4印度师」无「第」"),
    "4 Ind D": ("第4印度师", "同上"),
    "4 Ind D.": ("第4印度师", "同上"),
    "4 Indian.": ("第4印度师", "同上"),
    "Imperiali D": ("因佩里亚利师", "意大利第3「因佩里亚利」师；原有一行误译「帝国师」"),
    "Raemcke Bde.": ("拉姆克旅", "词库 EFILE_OLGWW2/UNIT；场景层另有「雷姆克旅」「第拉姆克旅」"),
    "185 Folgore": ("第185“闪电”师", "意大利第185「闪电」伞兵师；本项目译意体例（Ariete→公羊）"),
    "- [A Corps]": ("- [军]", "Corps=军（词库 II Corps=第2军）；原「[ 军]」多出空格、「[A军]」残留字母"),
    # C. 语序/前缀/后缀/统一
    "Das Reich": ("帝国师", "词库·本作层 PEGWW2_SCN/UNIT；场景层多作「达斯帝国师」"),
    "VIII": ("第8集团军", "第8集团军（多数，57 处）"),
    "2 NZ": ("第2新西兰师", "词库 EFILE_OLGWW2/UNIT"),
    "[SS Pz]": ("[党卫军装甲]", "去空格"),
    "9 ID": ("第9步兵师", "补「第」"),
    "1 Arm": ("第1装甲师", "补「第」"),
    "4 Bde": ("第4旅", "补「第」"),
    "4 Br": ("第4旅", "补「第」；词库作「第4旅」"),
    "I Army": ("第1集团军", "罗马数字改阿拉伯；与同族 II Corps=第2军 一致"),
    "II Corps": ("第2军", "词库 EFILE_OLGWW2/UNIT"),
    "V Army": ("第5集团军", "罗马数字改阿拉伯"),
    "5 LD": ("第5轻装师", "多数"),
    "8 R": ("第8团", "补「第」"),
    "12 R": ("第12团", "补「第」"),
    "7 R": ("第7团", "补「第」"),
    "168 R": ("第168团", "补「第」"),
    "1 SA Div": ("第1南非师", "南非师；词库作「第1南非师」"),
    "2 SA Div": ("第2南非师", "同上"),
    "2 Indian ID": ("第2印度步兵师", "去空格、补「第」"),
    "7 Arm D": ("第7装甲师", "补「第」"),
    "2 155 R": ("2 第155团", "序号在前，与「2 第90团」同体例"),
    "2 90 R": ("2 第90团", "同上"),
    "7 Mot Bde": ("第7摩托化旅", "补「第」"),
    "102 Trento": ("第102特伦托师", "意大利师级补「师」"),
    "Trento D": ("第102特伦托师", "同上"),
    "132 Ariete": ("第132公羊师", "补「师」"),
    "101 Trieste": ("第101的里雅斯特师", "补「师」"),
    "101Trieste": ("第101的里雅斯特师", "补「师」（该键缺空格，与 101 Trieste 同物）"),
    "27 Brescia": ("第27布雷西亚师", "补「师」"),
    "55 Savona": ("第55萨沃纳师", "补「师」"),
    "Saharian Grouping": ("撒哈拉集群", "词库 EFILE_OLGWW2/PLACE"),
    "7 SG": ("第7支援群", "词库 EFILE_OLGWW2/UNIT（7th Support Group）"),
    "DR [2SS]": ("帝国师 [2SS]", "与 Das Reich 统一"),
    "LAH [2SS]": ("希特勒警卫旗队 [2SS]", "多数"),
    "Giov.Fasc D": ("法西斯青年师", "语序统一（意大利「青年法西斯」师）"),
    "JG26 [JFF2] LF2": ("第26战斗机联队 [JFF2] 第2航空队", "LF2=Luftflotte 2 译出"),
    "JG51 [II] LF2": ("第51战斗机联队 [II] 第2航空队", "语序 + LF2 译出"),
    "ZG1 [JFF2] LF2": ("第1驱逐机联队 [JFF2] 第2航空队", "LF2 译出"),
    "1 Army Free": ("第1自由集团军", "多数（12:10）；两种写法皆通行，取多数以减少改动"),
}


# ── 上下文例外：同一 en 段在不同行里语义不同 ⇒ 这些行不套用该裁定 ─────────────────
# `VIII` 在 `.../XXX/VIII`（军/集团军层）＝第八集团军；在 `A/VIII/8th Division` 里＝师序号，
# 现行译法「第8」正确，不得改写。实测 61 行里只有这 2 行属于后者。
EXC = {"VIII": r"8th Division",
       # `17SS` 的（段级）规范形是「党卫军第17师」，但语料在 **`N/17SS` 复合番号**里一律
       # 用「第N/第17党卫军」（`17/17SS`、`I/37/17SS`、`KG GvB 17SS`…）⇒ 该段不做全局
       # 统一，改由下表 OUTLIERS 按行裁定（`37/17SS`、`38/17SS` 两行是英文残留，需补译）。
       "17SS": r"."}
# 目前无「只在某些行生效」的条目；留作机制
ONLY = {}

# ── 孤立异常行（同一段位、同类上下文里唯一不合群的写法）──────────────────────────
# 罗马数字段整体是**语境相关**的（`I/II/III` 可指营序号，也可指军/集团军；`V` 在
# `56 R/78 ID/V`＝第5军、在 `V/2-SS/...`＝第5），且有 1,700+ 段带 `人工确认` 标记，
# 无全局正解 ⇒ **不做全局统一**；只修下列「同一个军级段位、同类上下文占绝对多数」的孤例。
# （旁证：`.xscn` 定长槽截断只存在于 OLGWW2/PEG 侧——本作 PeG-WW2 的 SCENARIO 里
#  `.xscn` 数量为 **0**，故本作不存在「为了塞进槽位而故意缩短」的情形。）
# 列：en行(精确) | 段en | 现行段zh | 应为段zh | 依据
OUTLIERS = [
    ("126 R/51 ID/XXX/VIII", "XXX", "第30", "第30军",
     "同段位 38/39 作「第30军」；本报是唯一漏「军」的"),
    # 注：`126 R/51 ID/XXX/VIII` 与 `6 eB/2 NZ/XXX/VIII` 的 `VIII` 无需在此列出——
    # 段级规则 `VIII→第8集团军`（排除含 `8th Division` 的行）已覆盖这两行。
    ("/1 Arm/[XXX]", "[XXX]", "[第30军]", "[XXX]",
     "方括号军级标记本作惯例保留拉丁，同段位 107/108 作「[XXX]」"),
    ("62 R/Trento D/XXI", "XXI", "[第21军]", "第21军",
     "同段位 16/22 作「第21军」；方括号写法仅此 2 处"),
    ("46 R/Trento D/XXI", "XXI", "[第21军]", "第21军", "同上"),
    ("19 R/Brescia D/X", "X", "[第10军]", "第10军",
     "同段位 9/16 作「第10军」；方括号写法仅此 3 处"),
    ("20 R/Brescia D/X", "X", "[第10军]", "第10军", "同上"),
    ("1 R/Brescia D/X", "X", "[第10军]", "第10军", "同上"),
    # ── 注：复合番号里的缺陷（`1/1 SA` 作「南非第1师」、`2/LAH [2SS]` 作省称、
    # `2/8 FR/...` 的 `8 FR` 英文残留）已由**段级规则**（守卫拆除后全局生效）覆盖，无需在此列出。──
    ("37/17SS", "37", "37", "第37",
     "整行英文残留；依同族 `17/17SS` → `第17/第17党卫军`、`I/37/17SS` → `第1/第37/...`"),
    ("37/17SS", "17SS", "17SS", "第17党卫军",
     "同上；本族统一用「第17党卫军」，不套独立段规范形「党卫军第17师」以免族内混用"),
    ("38/17SS", "38", "38", "第38", "整行英文残留；同族写法一致"),
    ("38/17SS", "17SS", "17SS", "第17党卫军", "同上"),
]
OUT = os.path.join(LAY, "seg-canon-outliers.tsv")


def load_bank():
    d = defaultdict(list)
    for p in (os.path.join(GL, "standard-glossary.tsv"),
              os.path.join(LAY, "common-glossary.tsv"),
              os.path.join(LAY, "series-glossary.tsv"),
              os.path.join(LAY, "scope-glossary.tsv")):
        if not os.path.isfile(p):
            continue
        for l in io.open(p, encoding="utf-8-sig"):
            c = l.rstrip("\r\n").split("\t")
            if len(c) >= 4 and c[0].strip() and c[0].strip() != "en":
                d[c[0].strip()].append((c[1].strip(), c[3] if len(c) > 3 else ""))
    return d


def main():
    seg = defaultdict(Counter)
    src = defaultdict(Counter)          # (en,zh) → Counter(src)
    for l in io.open(os.path.join(RES, "ww2-scn-map.tsv"), encoding="utf-8-sig"):
        s = l.rstrip("\r\n")
        if not s or s.startswith("#"):
            continue
        c = s.split("\t")
        if len(c) < 3 or "/" not in c[0] or "/" not in c[1]:
            continue
        es, zs = [x.strip() for x in c[0].split("/")], [x.strip() for x in c[1].split("/")]
        if len(es) != len(zs):
            continue
        for a, b in zip(es, zs):
            if a and b and not SKIP_SEG.match(a):
                seg[a][b] += 1
                src[(a, b)][c[2].strip()] += 1
    real = {a: c for a, c in seg.items()
            if len(c) >= 2 and sum(1 for v in c if src[(a, v)].get("词库") or src[(a, v)].get("POLICY")) >= 2}
    bank = load_bank()
    rows = []
    for a, c in sorted(real.items(), key=lambda x: (-sum(x[1].values()), x[0])):
        top = c.most_common(1)[0][0]
        if a in OVR:
            canon, why = OVR[a]
            if canon not in c:
                why += "（新增写法）"
        else:
            hits = bank.get(a, [])
            mine = [h for h in hits if any(h[1].upper().startswith(m) for m in MINE)]
            if mine:
                canon, why = mine[0][0], "词库·本作层"
            elif hits:
                canon, why = hits[0][0], "词库·前作层"
            else:
                canon, why = top, "映射表多数"
        rows.append((a, canon, why, " ｜ ".join("%s×%d" % (v, n) for v, n in c.most_common())))
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 段级孤立异常行（精确匹配 en 行；`fix_map_segments.py` 读本表）\n")
        f.write("# 列：en行 \\t 段en \\t 现行段zh \\t 应为段zh \\t 依据\n")
        for r in OUTLIERS:
            f.write("\t".join(r) + "\n")
    with io.open(OUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 段级统一裁定表（真冲突专用；`fix_map_segments.py` 读本表）\n")
        f.write("# 列：en_seg \\t 规范译名 \\t 依据 \\t 映射表原分布 \\t 仅当(en行正则) \\t 排除(en行正则)\n")
        for r in rows:
            f.write("\t".join(r + (ONLY.get(r[0], ""), EXC.get(r[0], ""))) + "\n")
    print("真冲突段 %d 组 → %s" % (len(rows), OUT2))
    print("孤立异常行 %d 条 → %s" % (len(OUTLIERS), OUT))
    for r in rows:
        print("  %-30s → %-26s [%s]" % (r[0][:30], r[1][:26], r[2][:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
