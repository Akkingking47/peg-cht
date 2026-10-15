#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨层地名一致性修复：把「简报里的叫法」与「地图格名的叫法」统一。

裁定原则（逐条人工判定，见下表）：
  · 默认 **以地图格名为准**（地图是玩家定位依据，且是键控权威译名）⇒ 改散文
  · 但地图名**本身译错**时，改地图（如 Serafimov⇒谢拉菲莫夫 应为 谢拉菲莫维奇）
产出：research/_scn-fill-nameconsist.tsv（并入真源）
"""
import os
import re

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
FILL = os.path.join(RES, "_scn-fill-nameconsist.tsv")

# orig(括号里的原文) : (权威中文, [散文里的变异写法...]) ；权威中文若与地图原值不同 ⇒ 连地图键一起改
CONSIST = {
    "Mareth Line":       ("马雷特防线", ["马雷斯防线"]),          # 地图错（标准即 马雷特）
    "Seelow":            ("塞洛", ["泽洛"]),
    "Seelow Heights":    ("塞洛高地", ["泽洛高地"]),
    "Agedabia":          ("阿杰达比亚", ["阿格达比亚", "艾季达比亚"]),
    "Maginot line":      ("马奇诺防线", ["马其诺防线"]),           # 地图错（中文惯用 马奇诺）
    "Unternehmen Marita": ("「玛丽塔」行动", ["「马里塔」行动", "马里塔行动"]),
    "Monte Cassino":     ("卡西诺山", ["蒙特卡西诺"]),
    "Serafimov":         ("谢拉菲莫维奇", ["谢拉菲莫夫"]),          # 地图错（城市名 Serafimovich）
    "Viipuri":           ("维堡", ["维普里"]),
    "Pouppeville":       ("普佩维尔", ["普皮维尔"]),
    "Grave":             ("赫拉弗", ["格拉弗"]),                  # 地图错（荷兰语 Grave）
    "Compogne":          ("孔波涅", ["孔波尼"]),                  # 地图错（法语 -ogne）
    "Nadrin":            ("纳德兰", ["纳德尔"]),
    "River Moder":       ("莫代尔河", ["莫德尔河"]),               # 地图错（阿尔萨斯法语区）
    "Halfaya Pass":      ("哈勒法亚隘口", ["哈勒法亚山口"]),
    "Sidi Azeiz":        ("西迪阿扎伊兹", ["西迪阿扎兹"]),
    "Das Reich":         ("帝国师", ["达斯帝国师"]),               # 地图错（Das Reich = 帝国师）；散文里的短写「帝国」保留（列表语境）
    # —— 第二轮（审计剩余的 39 处，逐条裁定）——
    "Sidi Azeiz":        ("西迪阿扎伊兹", ["西迪阿扎兹"]),
    "Bone":              ("博讷", ["博纳"]),                      # Bône(今安纳巴)
    "Belgorov":          ("别尔哥罗德", ["别尔戈罗夫"]),            # ⚠️地图错：城市 Belgorod=别尔哥罗德
    "Tolvajarvi":        ("托尔瓦湖", ["托尔瓦耶尔维"]),            # järvi=湖
    "Piotrkow":          ("彼得库夫", ["皮奥特库夫"]),              # ⚠️地图错：波兰城市 Piotrków=彼得库夫
    "Castelforte":       ("卡斯泰尔福尔特", ["卡斯泰尔福特"]),
    "Khabarovsk":        ("哈巴罗夫斯克", ["伯力"]),               # 原文用俄名 ⇒ 取俄名通行译法
    "Portsmouth":        ("朴茨茅斯", ["朴次茅斯"]),                # ⚠️地图改用惯用「朴茨茅斯」
    "Lympne":            ("林普尼", ["利姆"]),
    "Gillingham":        ("吉灵厄姆", ["吉林厄姆"]),                # ⚠️地图改用惯用「吉灵厄姆」
    "Bexteyhead":        ("贝克斯泰海德", ["贝克斯利希斯"]),
    "Operation Marita":  ("玛丽塔行动", ["马里塔行动"]),
    "Ponte Dirillo":     ("迪里洛桥", ["蓬特迪里洛"]),             # Ponte=桥
    "Ponte Olivo":       ("奥利沃桥", ["蓬特奥利沃"]),
    "Wieuroszov":        ("维耶乌罗舒夫", ["维乌罗苏夫"]),
    "Red Menace":        ("赤色威胁", ["红色威胁"]),
    "Panzer-Verbande Ostpreussen": ("东普鲁士装甲集群", ["东普鲁士装甲部队"]),
    "Deutsches Afrika-Korps": ("德意志非洲军", ["德国非洲军"]),
    # 标题/小标题类（同一串也出现在地图键里，一并统一）
    "Chokepoint":        ("咽喉要地", ["咽喉要道"]),
    "Reunion Tour":      ("重逢之旅", ["重聚之旅"]),
    "Marching orders":   ("行军命令", ["开拔令"]),
    "Spearhead":         ("先锋", ["矛头"]),
    "On the move":       ("行军中", ["行动中"]),
    "Mopping up":        ("清剿", ["扫荡"]),
    "Kicking in the door": ("破门而入", ["踹门"]),
    "Advanced Elements": ("先头部队", ["先遣部队"]),
    # —— 第三轮（修掉「一行只修第一个地名」的 bug 后，剩余的 11 处）——
    "Burzenin":          ("布热宁", ["布热尼", "布尔泽宁"]),        # ⚠️地图错：波兰 Burzenin≈布热宁
    "Moerdijk":          ("穆尔代克", ["莫尔代克"]),
    "Sio Canal":         ("西奥运河", ["希奥运河"]),              # ⚠️地图错：匈牙利 Sió=西奥
    "Korsun Pocket":     ("科尔松包围圈", ["科尔孙包围圈"]),
    "Epsom Defence":     ("埃普索姆防御战", ["埃普索姆防御"]),
    "Perekop":           ("佩列科普", ["彼列科普"]),
    "Bardia":            ("拜尔迪耶", ["巴尔迪亚"]),              # ⚠️地图错：利比亚 Bardia=拜尔迪耶
}
Q = "「」『』“”\"'"


def strip_q(s):
    return "".join(c for c in s if c not in Q)


def main():
    rows = []
    for i, l in enumerate(open(MAP, encoding="utf-8-sig")):
        if i < 4 or not l.strip():
            continue
        f = l.rstrip("\n").split("\t")
        if len(f) >= 3:
            rows.append(f)
    # 地图键是否要把某条权威译名写进去（当 CONSYST 的权威值 与 地图现值 的「去引号形式」不同时）
    mp = {r[0]: r[1] for r in rows if r[1].strip()}
    fixes, map_fixes, stat = [], [], {}
    for orig, (canon, variants) in CONSIST.items():
        cur = mp.get(orig, "")
        if cur and strip_q(cur) != strip_q(canon):
            map_fixes.append((orig, cur, canon))
    n_prose = 0
    for r in rows:
        zh = r[1]
        if not zh.strip() or ("(" not in zh and "（" not in zh):
            continue
        new = zh
        for orig, (canon, variants) in CONSIST.items():
            if f"({orig})" not in new and f"（{orig}）" not in new:
                continue
            for v in variants:
                if v in new and strip_q(canon) != strip_q(v):
                    new = new.replace(v, canon)
                    stat[v] = stat.get(v, 0) + 1
        # ⚠️ 不能 break：一行里可能引用**多个**地名（如 `…(Ponte Dirillo)与…(Ponte Olivo)`）
        if new != zh:
            fixes.append((r[0], new))
            n_prose += 1
    # 去重
    seen = {}
    for a, b in fixes:
        seen[a] = b
    with open(FILL, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# 跨层地名一致性修复（地图键 {len(map_fixes)} 条 + 散文 {len(seen)} 条）\n")
        f.write("原文\t译文\n")
        for o, cur, canon in map_fixes:
            f.write(f"{o}\t{canon}\n")
        for a, b in seen.items():
            f.write(f"{a}\t{b}\n")
    print(f"  地图键改名: {len(map_fixes)} 条")
    for o, cur, canon in map_fixes:
        print(f"     {o:22s} {cur[:20]} → {canon}")
    print(f"  散文句统一: {len(seen)} 行")
    for v, n in sorted(stat.items(), key=lambda x: -x[1]):
        print(f"     「{v}」被替换 {n} 次")
    print(f"  → {os.path.relpath(FILL, WS)}")


if __name__ == "__main__":
    main()
