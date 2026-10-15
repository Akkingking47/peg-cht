#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**战役 → 视角国别**对照表（用可靠锚点，不用关键词猜）。

方法（修正我前两版失败的做法）：
  1. 用 `.cam`（战役文件）解出 **战役 → 场景清单**（.cam 里含被引用的 `.scn` 文件名）
  2. 每个场景的文件（`_i.txt`/`_m.txt`/`_u.txt`/`<名>.txt`…）归到该战役
  3. 在**战役内部**统计称呼锚点：`Herr`（德语系）· `Comrade`（苏/共）· 其余
     ⇒ 这是本作**唯一可靠**的视角判据（口径 §一.2：关键词命中「提到某国」不可靠）
  4. 与 MOD 自带 `DOCS\` 战役说明目录名对照，给出**战役名 → 视角国别**的推定与依据
产出：`research/_scn-视角分桶.tsv`（战役 / 场景数 / Herr / Comrade / 判定 / 依据）
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_scn-视角分桶.tsv")
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

# MOD 自带 DOCS 战役目录名 → 视角国别（人工判定，见口径 §二）
DOCS_NATION = [
    ("1st SS Leibstandarte Division", "德国（武装党卫军）"),
    ("Band of Brothers", "美国"),
    ("Blitzkrieg Objective France", "德国"),
    ("Boot of Death", "待核"),
    ("British Campaign in Europe", "英国/加拿大"),
    ("Das Reich", "德国（武装党卫军）"),
    ("Deutsches Afrika Korps", "德国（非洲军）/意大利"),
    ("For Stalin and Motherland", "苏联"),
    ("Germany at War", "德国"),
    ("Mediterranean 46", "待核"),
    ("Operation Sealion", "德国"),
    ("Red Alert", "苏联"),
    ("Red Menace (German side)", "德国（视角反向）"),
    ("Red Menace", "苏联"),
    ("Red World Order", "苏联"),
    ("Reich Defence", "德国"),
    ("Road to Berlin", "苏联"),
    ("Romanian Struggle", "罗马尼亚"),
    ("SSI Campaigns", "官方战役集（多国）"),
    ("The 7 PzrArmee defends the Reich", "德国"),
    ("The Gallantry of the 7 PzrArmee", "德国"),
    ("Waffen SS", "德国（武装党卫军）"),
    ("WW2", "泛（多国）"),
    ("WW2½", "泛（多国）"),
]


def main():
    scn = os.path.join(GAME, "SCENARIO")
    # 1) 解 .cam → 场景清单
    camps = {}
    for f in sorted(os.listdir(scn)):
        if not f.lower().endswith(".cam"):
            continue
        with open(os.path.join(scn, f), "rb") as fh:
            raw = fh.read()
        refs = set()
        for m in re.finditer(rb"[\x20-\x7e]{4,60}", raw):
            s = m.group(0).decode("latin-1").strip()
            if s.lower().endswith(".scn"):
                refs.add(os.path.splitext(s)[0].lower())
        camps[os.path.splitext(f)[0]] = refs
    print(f"战役文件 .cam: {len(camps)} 个；引用场景合计 {len(set().union(*camps.values())) if camps else 0} 个")

    # 2) 场景文件按 stem 归类
    alltxt = [f for f in os.listdir(scn)
              if os.path.isfile(os.path.join(scn, f)) and re.search(r"(?i)\.(txt|tx|t|log)$", f)
              and not re.search(r"(?i)(^info\.txt$|read ?me|report)", f)]
    by_stem = defaultdict(list)
    for f in alltxt:
        stem = re.sub(r"(?i)(_i|_m|_u|_bv|_tv|_l|_v|_cb)?\.(txt|tx|t|log)$", "", f).lower()
        by_stem[stem].append(f)

    # 3) 逐战役统计称呼锚点
    rows = []
    claimed = set()
    for camp, refs in sorted(camps.items()):
        files = []
        for r in refs:
            files += by_stem.get(r, [])
            claimed.add(r)
        h = c = other = 0
        for f in files:
            with open(os.path.join(scn, f), "rb") as fh:
                t = fh.read().decode("latin-1")
            h += len(re.findall(r"\bHerr\b", t))
            c += len(re.findall(r"\bComrade\b|\bcomrade\b", t))
        if h and not c:
            verdict, why = "德语系", f"Herr={h} 且 Comrade=0"
        elif c and not h:
            verdict, why = "苏/共体系", f"Comrade={c} 且 Herr=0"
        elif h and c:
            verdict, why = "**混合（双方简报同捆）**", f"Herr={h} Comrade={c} ⇒ 需逐条判"
        else:
            verdict, why = "**无锚点**", "既无 Herr 也无 Comrade ⇒ 需人工判（多为战报/地图名）"
        rows.append((camp, len(refs), len(files), h, c, verdict, why))

    print()
    print("=" * 104)
    print(f"{'战役(.cam)':34s} {'场景':>4s} {'文本':>4s} {'Herr':>5s} {'Comd':>5s}  判定")
    print("=" * 104)
    for camp, ns, nf, h, c, verdict, why in rows:
        print(f"{camp:34s} {ns:>4d} {nf:>4d} {h:>5d} {c:>5d}  {verdict}  （{why}）")

    orphan = sorted(set(by_stem) - claimed)
    print()
    print(f"不属于任何 .cam 的场景 stem: {len(orphan)}（多为独立场景/USERSCEN）")
    for o in orphan[:25]:
        print(f"   {o}  → {by_stem[o][:4]}")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 战役→视角国别分桶（**锚点法**：Herr/Comrade 实测计数；关键词命中不作依据）\n")
        fh.write("# 依据：口径 §一.1（全库只有 Herr/Comrade 两个可靠锚点）\n")
        fh.write("战役(.cam)\t场景数\t文本文件数\tHerr\tComrade\t视角判定\t依据\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print(f"\n[out] {os.path.relpath(OUT, WS)}")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "scn-perspective.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
