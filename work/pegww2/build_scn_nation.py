#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**场景 stem → 战役 → 国别**对照表（只读）。

用途：番号（部队编制缩写）译法要**按战役国别判定**（用户裁定 2026-10-19），
      本脚本把「这一行属于哪个战役、该战役是哪国视角」固化成可复算的表，
      供 `fix_unit_abbr.py` 逐行带出国别证据，并用于**跨国别冲突**检查。

方法与 `build_perspective.py` 一致（同一套 .cam 解析，不另立一套）：
  ① 解 `.cam`（战役文件内含被引用的 `.scn` 文件名）⇒ 战役 → 场景 stem
  ② 读 `research/_scn-视角分桶.tsv` 的**锚点法判定**（Herr/Comrade 实测）⇒ 战役 → 视角国别
  ③ 对不属于任何 .cam 的孤立场景（多为 USERSCEN/独立场景）标 `(无战役)`

产出：`research/_scn-国别.tsv`
   场景stem \t 战役 \t 视角国别 \t 依据
用法：python build_scn_nation.py
"""
import io
import os
import re
import sys
from collections import defaultdict

WS = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME = os.environ.get("PEG_GAME_WW2", r"D:\Program Files\PeG-WW2")
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_scn-国别.tsv")
BUCKET = os.path.join(RES, "_scn-视角分桶.tsv")
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


def load_bucket():
    """战役 → (视角判定, 依据)"""
    out = {}
    if not os.path.isfile(BUCKET):
        return out
    with io.open(BUCKET, encoding="utf-8-sig") as fh:
        for raw in fh:
            s = raw.rstrip("\r\n")
            if not s or s.startswith("#"):
                continue
            f = s.split("\t")
            if len(f) >= 7 and f[0] != "战役(.cam)":
                out[f[0]] = (f[5], f[6])
    return out


# 战役名的**别名**（实测：MOD 的场景文件名前缀与 .cam 名不完全一致）
# 只放「实测见过」的别名，不臆测；最长优先匹配在 match_camp() 里保证
ALIAS = {
    "lah_it": "LSSAH-IT", "lah-it": "LSSAH-IT", "lssah": "LSSAH-IT",
    "usvsussr": "Usvsussr", "usvsurss": "Usvsussr",
    "s0": "s00sov", "s00": "s00sov",
    "wd": "wdbrit1", "wdcass": "wdbrit1", "wdbrit": "wdbrit1",
    "zs_": "ZS_Za_Stalina", "zs": "ZS_Za_Stalina",
    "fi": "fi", "ita": "italy", "italy": "italy",
    "rm_": "RM", "rg_": "RG", "sl_": "SL", "rtb": "RTB", "gaw": "GAW",
    "dak_": "DAK", "b7": "B7", "b7low": "B7low", "bob": "BOB",
    "atm": "ATM", "camp": "CAMP1", "ra_": "RA_redalert", "ss_": "ss_campaign",
    "7pzr": "7PzrCamp7dr", "g7pzr": "G7PzrCamp7d",
    "lh_ger46med": "LH_ger46med", "r7": "R7", "dr": "DR",
}


def nation_tells(text):
    """从文件内容本身推断国别归属（番号 token 自带国别）—— 作为第三种判据。
    只认**有确凿国别归属**的编制缩写，避免「提到某国」式猜测（那是本作明令禁止的）。"""
    tells = {"苏/共体系": 0, "英语系": 0, "德语系": 0, "意大利": 0}
    rules = [("苏/共体系", r"\b(GMech|GTA?|GCC?|GC)\b|\bComrade\b"),
             ("英语系", r"\b(RTR|RHA|RAA|Recce|BEF|Abn)\b"),
             ("德语系", r"\b(Pz|Aufkl|Funkschl|Leibstandarte|SS)\b"),
             ("意大利", r"\b(Pavia|Littorio|Mare Nostrum)\b")]
    for k, pat in rules:
        tells[k] = len(re.findall(pat, text))
    tot = sum(tells.values())
    if not tot:
        return "", ""
    best = max(tells, key=lambda k: tells[k])
    if tells[best] * 1.0 / tot < 0.6:
        return "**混合**", " ".join("%s=%d" % kv for kv in tells.items() if kv[1])
    return best, "%s=%d（占 %.0f%%）" % (best, tells[best], 100.0 * tells[best] / tot)


def match_camp(stem, names):
    """最长前缀匹配（先别名，再战役名本身）"""
    low = stem.lower()
    cands = []
    for a, c in ALIAS.items():
        if low.startswith(a):
            cands.append((len(a) + 1, c))          # 别名给一点加权（更具体）
    for n in names:
        if low.startswith(n.lower()):
            cands.append((len(n), n))
    if not cands:
        return ""
    return max(cands)[1]


def main():
    scn = os.path.join(GAME, "SCENARIO")
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
    print("战役 .cam: %d 个；引用场景合计 %d 个"
          % (len(camps), len(set().union(*camps.values())) if camps else 0))

    bucket = load_bucket()
    print("视角分桶表读到 %d 个战役判定" % len(bucket))

    stem2camp = {}
    for camp, refs in camps.items():
        for r in refs:
            stem2camp.setdefault(r, camp)     # 一个 stem 只归首个战役（不重复归属）

    alltxt = [f for f in os.listdir(scn)
              if os.path.isfile(os.path.join(scn, f))
              and re.search(r"(?i)\.(txt|tx|t|log)$", f)
              and not re.search(r"(?i)(^info\.txt$|read ?me|report)", f)]
    by_stem = defaultdict(list)
    for f in alltxt:
        stem = re.sub(r"(?i)(_i|_m|_u|_bv|_tv|_l|_v|_cb)?\.(txt|tx|t|log)$", "", f).lower()
        by_stem[stem].append(f)
    print("文本文件 %d 个 → %d 个场景 stem" % (len(alltxt), len(by_stem)))

    rows = []
    for stem in sorted(by_stem):
        camp = stem2camp.get(stem, "")
        how = "① .cam 归属"
        if not camp:
            camp = match_camp(stem, list(camps))
            how = "② 前缀法"
        if camp:
            verdict, why = bucket.get(camp, ("**桶表缺失**", "视角分桶表无此战役"))
            src = how
            note = why
        else:
            # ③ 内容自证（番号 token 自带国别）——最后兜底
            txt = ""
            for f in by_stem[stem][:6]:
                try:
                    txt += io.open(os.path.join(scn, f), encoding="gbk").read()
                except Exception:
                    pass
            verdict, note = nation_tells(txt)
            camp = "(无战役)"
            src = "③ 内容自证" if verdict else "—"
        rows.append((stem, camp, verdict or "**未定**", src, note))

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 场景 stem → 战役 → 视角国别（锚点法；供番号译法逐行带出国别证据）\n")
        fh.write("# 生成：build_scn_nation.py · 判据优先级：① .cam 归属 > ② 前缀法 > ③ 内容自证\n")
        fh.write("场景stem\t战役\t视角国别\t判据\t说明\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")

    from collections import Counter
    c = Counter(r[2] for r in rows)
    print("\n国别分布（按场景 stem 计）：")
    for k, v in c.most_common():
        print("  %-26s %d" % (k, v))
    cn = Counter(r[3] for r in rows)
    print("\n判据分布：")
    for k, v in cn.most_common():
        print("  %-14s %d" % (k, v))
    print("\n[out] %s（%d 行）" % (os.path.relpath(OUT, WS), len(rows)))
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with io.open(os.path.join(RES, "evidence", "scn-nation.txt"), "w",
                 encoding="utf-8", newline="\n") as fh:
        fh.write(_sink.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())
