# -*- coding: utf-8 -*-
"""probe_keep62.py —— 只读：查清「词库值==英文原文」（keep 桶）那 62 类到底长什么样。

用户 m01214-② 「补齐」要的就是这批：`audit_shipped_vs_lib.py` 里 `kind_of(k)=="keep"`
的键（词库只登记了英文原文当中文），而成品其实已经译成中文。

本探针把每个键的**词库登记明细**（哪个 scope/层、conf、status）与**成品实际用词**并排打出，
用来判断该不该补、补到哪里（PEGWW2_EQP / PEGWW2_SCN / PEGWW2_UI …）。

用法：`python probe_keep62.py [--tsv 输出路径]`
只读，不写任何真源（TSV 落在 work\\_sync-audit\\ 下）。
"""
import io
import os
import re
import sys
from collections import defaultdict

W = r"D:\DSH\军事游戏汉化"
LIBFILES = (
    ("standard", os.path.join(W, r"glossary\standard-glossary.tsv")),
    ("common", os.path.join(W, r"glossary\layers\common-glossary.tsv")),
    ("scope", os.path.join(W, r"glossary\layers\scope-glossary.tsv")),
)
GAME = r"D:\Program Files\PeG-WW2"
BACK = os.path.join(W, r"pegww2\testbed\backup")
PREFIX = "PEG"

DECO = re.compile(r"\s*[\(（\[][^\)）\]]*[\)）\]]\s*")


def strip_deco(v):
    v = DECO.sub(" ", v).strip()
    return v


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def read_tsv(p):
    rows = []
    for ln in io.open(p, encoding="utf-8-sig"):
        ln = ln.rstrip("\r\n")
        if not ln or ln.startswith("#"):
            continue
        rows.append(ln.split("\t"))
    return rows


def load_lib():
    """LIB[en] = [(zh, scope, conf, status, layer)]；只留 PEG* scope。"""
    lib = defaultdict(list)
    for layer, path in LIBFILES:
        for c in read_tsv(path):
            if len(c) < 8:
                continue
            en, zh, scope, conf, status = c[0], c[1], c[3], c[6], c[4]
            if not scope.upper().startswith(PREFIX):
                continue
            lib[norm(en)].append((zh, scope, conf, status, layer))
    return lib


def read_shipped(path):
    """成品文件 → [(行号, 英文, 中文)]（英文取自备份）。"""
    out = []
    b = os.path.join(BACK, path)
    g = os.path.join(GAME, path)
    if not (os.path.isfile(b) and os.path.isfile(g)):
        return out
    en = io.open(b, "rb").read().decode("latin-1").split("\n")
    zh = io.open(g, "rb").read().decode("gbk", "replace").split("\n")
    for i, (a, z) in enumerate(zip(en, zh)):
        out.append((i, a.rstrip("\r"), z.rstrip("\r")))
    return out


def walk_exts():
    files = []
    for sub in ("SCENARIO", "USERSCEN"):
        root = os.path.join(BACK, sub.replace("SCENARIO", "SCENARIO"))
        if not os.path.isdir(root):
            continue
        for dp, _dn, fns in os.walk(root):
            for fn in fns:
                if fn.lower().endswith((".txt", ".tx", ".t", ".log")):
                    rel = os.path.relpath(os.path.join(dp, fn), BACK)
                    files.append(rel)
    return files


def main():
    lib = load_lib()
    # keep 桶：词库该键的**所有**译文 strip_deco 后都等于英文键本身
    keep = {}
    for k, vals in lib.items():
        if all(strip_deco(v[0]).lower() == k for v in vals):
            keep[k] = vals
    print(f"词库 PEG* 键 {len(lib)} 个 · 其中「词库值==英文」 {len(keep)} 个")

    # 成品侧：只认地图名栏 `_m.txt`（与候选审核口径一致）
    shipped = defaultdict(lambda: defaultdict(set))
    files_of = defaultdict(set)
    for rel in walk_exts():
        base = os.path.basename(rel)
        if not re.search(r"(?i)_m\.txt$", base):
            continue
        for _i, a, z in read_shipped(rel):
            s = a.strip()
            if not s or not re.search(r"[A-Za-z]", s):
                continue
            key = norm(s)
            if key in keep and z.strip():
                shipped[key][z.strip()].add(rel)
                files_of[key].add(rel)

    rows = []
    for k in sorted(shipped):
        vals = keep[k]
        zh_set = sorted(shipped[k])
        rows.append((k, vals, zh_set, sorted(files_of[k])))

    print(f"其中成品 `_m.txt` 里确实出现了 {len(rows)} 个\n")
    for k, vals, zs, fs in rows:
        meta = " · ".join(f"{sc}/{cf}/{st}" for _z, sc, cf, st, _l in vals)
        print(f"[{k}]")
        print(f"    词库值  : {' | '.join(z for z, *_ in vals)}   （{meta}）")
        print(f"    成品用词: {' | '.join(zs)}   ×{len(fs)} 文件  e.g. {fs[0]}")
    if "--tsv" in sys.argv:
        p = sys.argv[sys.argv.index("--tsv") + 1]
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("en\t词库值\tscope/conf/status\t成品用词\t文件数\t样例文件\n")
            for k, vals, zs, fs in rows:
                f.write("\t".join([
                    k,
                    " | ".join(z for z, *_ in vals),
                    " · ".join(f"{sc}/{cf}/{st}" for _z, sc, cf, st, _l in vals),
                    " | ".join(zs),
                    str(len(fs)),
                    fs[0],
                ]) + "\n")
        print(f"\n已写 {p}")


if __name__ == "__main__":
    main()
