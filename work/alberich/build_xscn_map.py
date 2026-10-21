# -*- coding: utf-8 -*-
"""构建 EFILE_ALBERICH `.xscn` 汉化映射（src<TAB>dst）。

来源优先级（后者覆盖前者）：
  1. 纯编号/符号（原文不含拉丁字母）  -> 原样保留
  2. work/xscn-all-map.tsv            （PG2 已实装口径）
  3. work/xscn/master-glossary.tsv     （主词典）
  4. work/xscn/_xscn_dict.tsv          （历史 xscn 词典）
  5. work/alberich/xscn_manual_data.py 的 MANUAL （本次人工定译，权威）
  6. 同文件的 KEEP                     （确认保留）

输出：work/alberich/xscn-map.tsv
"""
import importlib.util
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xscn_manual_data import MANUAL, KEEP  # noqa

spec = importlib.util.spec_from_file_location(
    "xscn", r"D:\DSH\军事游戏汉化\work\xscn\xscn.py")
X = importlib.util.module_from_spec(spec)
spec.loader.exec_module(X)

GAME = r"D:\OpenGeneral"
EFILE = "ALBERICH"
SCEN = os.path.join(GAME, "EFILE_" + EFILE, "SCENARIO")
ENC = "cp1250"
LAT = re.compile(r"[A-Za-z]")
HAN = re.compile(r"[\u4e00-\u9fff]")


def slots():
    out = []
    for fn in sorted(f for f in os.listdir(SCEN) if f.lower().endswith(".xscn")):
        d, it, m = X.parse(os.path.join(SCEN, fn))
        for gi, idx, off, L in X.slots_of(d, it, m):
            out.append((fn, gi, idx, X.raw_at(d, off, L).decode(ENC, "replace")))
        if m[0] is not None:
            out.append((fn, -1, 0, X.raw_at(d, m[0], m[1]).decode(ENC, "replace")))
    return out


def load(path, kc, vc):
    dd = collections.OrderedDict()
    with open(path, encoding="utf-8") as f:
        next(f)
        for ln in f:
            p = ln.rstrip("\n").split("\t")
            if len(p) > max(kc, vc):
                k, v = p[kc].strip(), p[vc].strip()
                if v and v != k:
                    dd.setdefault(k, v)
    return dd


def main():
    all_slots = slots()
    target = collections.OrderedDict()
    for fn, gi, idx, s in all_slots:
        target.setdefault(s.strip(), s)

    srcs = [
        ("all-map", r"D:\DSH\军事游戏汉化\work\xscn-all-map.tsv", 3, 4),
        ("glossary", r"D:\DSH\军事游戏汉化\work\xscn\master-glossary.tsv", 0, 1),
        ("xscn-dict", r"D:\DSH\军事游戏汉化\work\xscn\_xscn_dict.tsv", 0, 1),
    ]
    loaded = [(n, load(p, kc, vc)) for n, p, kc, vc in srcs]
    final = collections.OrderedDict()
    origin = collections.Counter()
    for k, orig in target.items():
        if not LAT.search(k):
            final[k] = k
            origin["keep-noletters"] += 1
        else:
            for name, d in loaded:
                if k in d:
                    final[k] = d[k]
                    origin[name] += 1
                    break

    for k, v in MANUAL.items():
        k2 = k.strip()
        if k2 in target:
            final[k2] = v.strip()
            origin["MANUAL"] += 1
    for k in KEEP:
        k2 = k.strip()
        if k2 in target:
            final[k2] = k2
            origin["KEEP"] += 1

    # ---- 校验 ----
    prob = []
    for k, v in final.items():
        if k == v:
            continue
        if not HAN.search(v):
            prob.append(("无汉字", k, v))
        for ch in "[]()":
            if k.count(ch) != v.count(ch):
                prob.append(("%s数不符" % ch, k, v))
        if k.count("/") != v.count("/"):
            prob.append(("/数不符", k, v))
    missing = [k for k in target if k not in final]

    out = []
    out.append("槽位 %d / 唯一 %d" % (len(all_slots), len(target)))
    for kk, vv in origin.most_common():
        out.append("  %s: %d" % (kk, vv))
    out.append("映射表 %d 条（其中保留原文 %d）"
               % (len(final), sum(1 for k, v in final.items() if k == v)))
    out.append("未覆盖 %d" % len(missing))
    for k in missing[:200]:
        out.append("   MISS %r" % k)
    out.append("结构可疑 %d" % len(prob))
    for t, k, v in prob[:200]:
        out.append("   %s %r -> %r" % (t, k, v))
    unmatched = [k for k in MANUAL if k.strip() not in target]
    out.append("MANUAL 中不在目标集里的键 %d" % len(unmatched))
    for k in sorted(unmatched):
        out.append("   EXTRA %r" % k)

    tsv = os.path.join(HERE, "xscn-map.tsv")
    n_w = 0
    with open(tsv, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")   # load_map() 跳过第 0 行，必须留表头
        for k, v in final.items():
            if v == k:
                continue
            f.write("%s\t%s\n" % (k, v))
            n_w += 1
    out.append("映射表实际写入 %d 条（已剔除 dst==src 的 %d 条保留项）"
               % (n_w, len(final) - n_w))
    with open(os.path.join(HERE, "_mapreport.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("\n".join(out[:8]))
    print("未覆盖 %d / 结构可疑 %d" % (len(missing), len(prob)))
    print("已写", tsv)


if __name__ == "__main__":
    main()
