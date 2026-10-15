#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景列表「分组序号」执行器（用户批准：按地图分组出序号）。

做法：给每个进列表场景的 `_m.txt` **行0（显示名）** 加 `组名-NN ` 前缀，
      走 **per-file 覆盖表**（`_scn-file-overrides.tsv`）—— 理由：
        · 该表在 `gen_scn.py` 里**优先级高于整串键控**（第 132–134 行），能定点改这一行不改别处
        · 序号是"每文件一次"的改动，用整串键控会误伤同名正文（W17 教训）

分组判据：`.SCN@11210` 地图名 → 主战场（本作存在一图多用，冲突项由用户逐条裁决，本脚本只按地图初排）
组内序号：`_m.txt` 行0 的**英文原名**按 cp1252 字节序

纪律：幂等（已有同名前缀则跳过）；默认 dry-run；`--apply` 才写覆盖表；不碰游戏目录。
"""
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
S = os.path.join(G, "SCENARIO")
U = os.path.join(G, "USERSCEN")
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
RES = os.path.join(WS, "pegww2", "research")
OVF = os.path.join(RES, "_scn-file-overrides.tsv")
LOG = os.path.join(RES, "_场景序号前缀留痕.tsv")

PREFIX = {"西线/西北欧": "西线", "东线": "东线", "北非·地中海·意大利": "北非"}
MAPGROUP = {
    "西线/西北欧": ["CAEN", "STLO", "ARRACT", "SEDAN", "METZ", "WINDSOR", "DUNKIRK",
                    "NORDWIND", "REMAGEN", "MADRID", "EURORMY", "LILLEHAM", "OAKRIDGE"],
    "东线": ["KONRAD", "KANEV", "KISHINEV", "KLIN", "VIIPURI", "LENIN", "NOVGOROD",
             "PROKHORV", "SEELOW", "SOUMUSSA", "VOLOKOL", "DESSAU", "CIECHANO", "CHIR"],
    "北非·地中海·意大利": ["SALERNO", "MALTA", "GARAMLAH", "RATOBRUK", "PTOBRUK",
                            "GREECE", "SAVANNAH", "TOBRUK"],
}
SHELLS = {"ATM_scn29", "ATM_scn34"}   # 空壳，用户已决定从列表摸掉 ⇒ 不编号


def fld(b, o, n=20):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def firstline(p, enc):
    t = open(p, "rb").read()
    if p.lower().endswith(".ply"):
        t = t.split(b"\x00")[0]
    return re.split(r"\r\n|\r|\n", t.decode(enc, "replace"))[0]


def main():
    apply_ = "--apply" in sys.argv
    rows = []
    for d in (S, U):
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".scn"):
                continue
            b = open(os.path.join(d, fn), "rb").read()
            if len(b) < 11350 or b[0] != 0:
                continue
            stem = fn[:-4]
            if stem in SHELLS:
                continue
            # 英文原名（备份优先，备份缺失则用真源反查）
            en = None
            for c in (stem + "_m.txt", stem.upper() + "_m.txt"):
                pb = os.path.join(BK, c)
                if os.path.isfile(pb):
                    en = firstline(pb, "cp1252").strip()
                    break
            zh = None
            fn_real = None
            for c in (stem + "_m.txt", stem.upper() + "_m.txt"):
                pg = os.path.join(d, c)
                if os.path.isfile(pg):
                    zh = firstline(pg, "gbk").strip()
                    fn_real = c
                    break
            if zh is None:
                # 再按真实文件名（不区分大小写）找一次
                for x in os.listdir(d):
                    if x.lower() == stem.lower() + "_m.txt":
                        zh = firstline(os.path.join(d, x), "gbk").strip()
                        fn_real = x
                        break
            if zh is None:
                print(f"  ⚠️ {stem} 无 _m.txt ⇒ 无法加序号（跳过）")
                continue
            mp = fld(b, 11210).upper().replace(".MAP", "")
            g = next((k for k, v in MAPGROUP.items() if mp in v), None)
            if g is None:
                print(f"  ⚠️ {stem} 地图 {mp} 未归组 ⇒ 跳过")
                continue
            rows.append(dict(stem=stem, sub=os.path.basename(d), fn=fn_real, en=en or zh, zh=zh, mp=mp, g=g))

    # 分组内按英文原名排序编号
    plans = []
    for g in PREFIX:
        sub = sorted([r for r in rows if r["g"] == g], key=lambda r: r["en"].encode("cp1252", "replace"))
        for i, r in enumerate(sub, 1):
            pre = f"{PREFIX[g]}-{i:02d} "
            new = pre + r["zh"]
            already = r["zh"].startswith(f"{PREFIX[g]}-")
            plans.append(dict(r, pre=pre.strip(), new=new, no=i, already=already))

    print("=" * 110)
    print(f"场景列表分组序号  模式={'[APPLY]' if apply_ else '[DRY-RUN]'}  真源={os.path.relpath(OVF, WS)}")
    print("=" * 110)
    for g in PREFIX:
        grp = [p for p in plans if p["g"] == g]
        print(f"\n== {g}（{len(grp)} 条）==")
        for p in grp:
            tag = "（已有前缀，跳过）" if p["already"] else ""
            print("  %-8s %-16s %-30s ← %s  地图=%s %s" % (
                p["pre"], p["stem"], p["new"][:30], p["zh"][:22], p["mp"], tag))

    todo = [p for p in plans if not p["already"]]
    print(f"\n待写入 per-file 覆盖：{len(todo)} 条（已有前缀跳过 {len(plans) - len(todo)} 条）")
    if not apply_:
        print("  ⇒ dry-run，未写入。加 --apply 落盘。")
        return 0

    # 追加到覆盖表（gen_scn.py 按 key 取值，后写覆盖先写）
    # ⚠️⚠️ W21 事故护栏：文件名必须用**磁盘真实大小写**（曾经用 stem 小写拼名 ⇒ 56 条覆盖静默失效），
    #      且 `期望原文` 列必须是 **ASCII(Latin-1)** —— 生成器用它解码备份，非 ASCII 会抛异常。
    for p in todo:
        assert p["fn"] == [x for x in os.listdir(os.path.join(G, p["sub"])) if x.lower() == p["stem"].lower() + "_m.txt"][0], \
            f"文件名大小写不符: {p['fn']}"
        try:
            p["en"].encode("latin-1")
        except UnicodeEncodeError:
            raise SystemExit(f"⛔ {p['stem']}: 期望原文列含非 ASCII 字符，拒绝写入（会破坏 gen_scn 解码）: {p['en'][:40]!r}")
    if not os.path.isfile(OVF + ".pre-num"):
        shutil.copy2(OVF, OVF + ".pre-num")
        print(f"  备份 ⇒ {os.path.relpath(OVF + '.pre-num', WS)}")
    with open(OVF, "a", encoding="utf-8", newline="\n") as f:
        for p in todo:
            f.write(f"{p['sub']}\t{p['fn']}\t0\t{p['en']}\t{p['new']}\n")
    print(f"  已追加 {len(todo)} 行 ⇒ {os.path.relpath(OVF, WS)}")
    if not os.path.isfile(LOG):
        with open(LOG, "w", encoding="utf-8", newline="\n") as f:
            f.write("# 场景列表分组序号留痕\n组\t序号\tstem\t地图\t原显示名\t新显示名\n")
    with open(LOG, "a", encoding="utf-8", newline="\n") as f:
        for p in todo:
            f.write(f"{p['g']}\t{p['pre']}\t{p['stem']}\t{p['mp']}\t{p['zh']}\t{p['new']}\n")
    # 回读校验
    back = open(OVF, encoding="utf-8").read()
    miss = [p["stem"] for p in todo if f"{p['new']}" not in back]
    print(f"  回读校验 {'✅ 通过' if not miss else '❌ 缺 ' + str(miss[:5])}")
    return 0 if not miss else 1


if __name__ == "__main__":
    sys.exit(main())
