# -*- coding: utf-8 -*-
"""标准译名库校验器 —— 扫描 efile 里残留的原文，用库判定「漏译」还是「新词」。

只需中文侧文件即可运行（不依赖原始英文备份），因此对**尚未汉化的 efile**
同样有效：先扫出所有残留在界面上、本该是中文的原文串，再拿库查标准译名。

用法:
  python check_glossary.py EFILE_OLGWW2
  python check_glossary.py D:/OpenPG2/EFILE_OPENPG
  python check_glossary.py EFILE_OLGWW2 --all        # 含 ABBR 类（番号缩写）
  python check_glossary.py EFILE_OLGWW2 --out r.txt  # 同时落盘

输出三类:
  [未译] 库中有标准译名，文件里仍是原文  —— 直接可改
  [新词] 库中无，文件里是原文            —— 需人工定名后补进库
  [异译] 文件里是中文但与库标准译名不同   —— 需裁定
"""
import collections
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GL = os.path.normpath(os.path.join(HERE, "..", "..", "glossary", "standard-glossary.tsv"))
ROOT = r"D:/OpenPG2"
sys.path.insert(0, os.path.join(HERE, "..", "efile-nashornpbem"))

from apply_residual import parse  # noqa: E402

HEAD = ["en", "zh", "cat", "scope", "status", "src", "conf", "zh_in"]
SEP = re.compile(r"\s+/\s+|[|｜]")
CJK = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)
LAT = re.compile(r"[A-Za-z]")
NOISE = re.compile(r"^\s*(\*|//|;|#|\[)")
# 不算漏译的：纯符号/编号
SKIPVAL = re.compile(r"^[\s\-\u2013\u2014–—/\\.,:;!?'\"()\[\]{}<>*#@%&+=~^_]+$")
# 方括号编制标记（[XX] [DAF] [12A]）按口径保留原文，不算未译/新词
BRACKET_ONLY = re.compile(r"^[\[【][^\]】]*[\]】]$")
# 根文件 -> 层名
ROOT_LAYER = {"equip": "equip", "names": "names", "nations": "nations",
              "strings_efile": "strings", "tips1": "tips"}


def load_glossary():
    if not os.path.exists(GL):
        sys.exit("库不存在: %s（先跑 build_glossary.py）" % GL)
    idx, by_en = {}, collections.defaultdict(list)
    for ln in io.open(GL, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        while len(c) < len(HEAD):
            c.append("")
        r = c[:len(HEAD)]
        idx[(r[0], r[3])] = r
        by_en[r[0]].append(r)
    return idx, by_en


def lookup(by_en, en, scope, layer):
    """只在「该原文在同一层曾给出过中文」时才判 —— 层不同不判。

    equip.txt 保留装备型号、xscn 译地图标签，同一原文的合法处理本就不同。
    """
    cands = [x for x in by_en.get(en, [])
             if x[4] == "LOCKED" and layer in (x[7] or "").split("+")]
    if not cands:
        return None
    same = [x for x in cands if x[3] == scope]
    return same[0] if same else cands[0]


def scan(efile_dir, scope):
    """产出 (layer, src, loc, value)"""
    # 1) 根文件（TEXT-ZH 优先，其次原位）
    for d in (os.path.join(efile_dir, "TEXT-ZH"), efile_dir):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p) or not fn.lower().endswith(".txt"):
                continue
            layer = ROOT_LAYER.get(fn[:-4].lower())
            if layer is None:
                continue
            for i, ln in enumerate(io.open(p, encoding="gbk", errors="replace")
                                    .read().splitlines(), 1):
                if ln.strip() and not NOISE.match(ln):
                    yield (layer, fn, "%s:%d" % (fn, i), ln)
    # 2) 场景 .txt / .ply
    for sub in ("TEXT-ZH/SCENARIO", "SCENARIO"):
        d = os.path.join(efile_dir, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith((".txt", ".ply")):
                continue
            for i, ln in enumerate(io.open(os.path.join(d, fn), encoding="gbk",
                                           errors="replace").read().splitlines(), 1):
                if ln.strip() and not NOISE.match(ln):
                    yield ("txt", fn, "%s/%s:%d" % (sub, fn, i), ln)
    # 3) .xscn 组 0/1
    d = os.path.join(efile_dir, "SCENARIO")
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".xscn"):
                continue
            data, items, meta = parse(os.path.join(d, fn))
            if items is None:
                continue
            for gi, ki, off, ln in items:
                if gi > 1:
                    continue
                v = data[off + 2:off + 2 + ln].decode("gbk", "replace")
                if v.strip():
                    yield ("xscn", fn, "%s:g%d#%d" % (fn, gi, ki), v)


def atomize(v):
    """把 'A / B / C' 拆成单项，便于命中库"""
    if SEP.search(v):
        parts = [p.strip() for p in SEP.split(v)]
        if len(parts) >= 2:
            return [p for p in parts if p]
    return [v.strip()]


ABBR_LIKE = re.compile(r"^[A-Z0-9][A-Z0-9 .\-/&'\[\]()]{0,13}$")


def is_abbr_like(s):
    """全大写/数字的短串 ⇒ 番号、缩写、编号（多半按口径保留原文）"""
    t = s.strip()
    return len(t) <= 14 and bool(ABBR_LIKE.match(t))


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    flags = {x for x in sys.argv[1:] if x.startswith("--")}
    if not a:
        print(__doc__)
        return
    name = a[0]
    efile_dir = name if os.path.isdir(name) else os.path.join(ROOT, name)
    if not os.path.isdir(efile_dir):
        sys.exit("目录不存在: %s" % efile_dir)
    scope = os.path.basename(os.path.normpath(efile_dir))
    show_abbr = "--all" in flags
    # 默认只看场景层：.txt 清单 与 .xscn 标签才是「会跨文件出现、必须一致」的部分。
    # equip/names 是装备表与人名册，保留型号/音译人名本就是既定口径。
    want_layers = {"txt", "xscn"}
    for f in flags:
        if f.startswith("--layers="):
            want_layers = set(f.split("=", 1)[1].split(","))
    if "--all-layers" in flags:
        want_layers = None

    idx, by_en = load_glossary()

    miss, neww, okcnt = [], [], 0
    for layer, fname, loc, val in scan(efile_dir, scope):
        if want_layers is not None and layer not in want_layers:
            continue
        for atom in atomize(val):
            if not atom or SKIPVAL.match(atom) or BRACKET_ONLY.match(atom):
                continue
            has_zh, has_lat = CJK(atom), bool(LAT.search(atom))
            if not has_lat:
                if has_zh:
                    okcnt += 1
                continue
            if has_zh:
                continue                       # 中英混排（型号保留等），不判
            r = lookup(by_en, atom, scope, layer)
            if r is None:
                neww.append((layer, loc, atom))
            elif r[4] == "LOCKED" and r[1] != atom:
                kind = "ABBR" if r[6] == "ABBR" else "PLAIN"
                if kind == "PLAIN" or show_abbr:
                    miss.append((kind, layer, loc, atom, r[1], r[2], r[6]))

    print("=" * 100)
    print("标准译名库校验: %s   （库 %d 条）" % (scope, len({r[0] for v in by_en.values() for r in v})))
    print("检查层: %s" % ("全部" if want_layers is None else ",".join(sorted(want_layers))))
    print("=" * 100)
    print("合规中文条目 %d 条 ｜ 待核对 %d 处 ｜ 库外新词 %d 条\n"
          % (okcnt, len(miss), len({n[2] for n in neww})))

    lm = collections.Counter(m[1] for m in miss)
    ln_ = collections.Counter(n[0] for n in neww)
    print("-- 分布 --")
    print("   未译: " + "  ".join("%s=%d" % (k, v) for k, v in lm.most_common()))
    print("   新词: " + "  ".join("%s=%d" % (k, v) for k, v in ln_.most_common()))
    print()

    print("## [未译] 库中有标准译名，文件里仍是原文: %d 处" % len(miss))
    bykind = collections.Counter(m[0] for m in miss)
    print("   PLAIN=%d（可直接改）  ABBR=%d（番号缩写，需看语境；--all 全列）"
          % (bykind.get("PLAIN", 0), bykind.get("ABBR", 0)))
    shown = collections.Counter()
    for kind, layer, loc, atom, zh, cat, conf in miss:
        if shown[layer] >= 15:
            continue
        shown[layer] += 1
        print("   [%-11s] %-26s -> %-22s @ %s" % (layer + "/" + kind, atom[:26], zh[:22], loc))
    print()

    neww_abbr = [n for n in neww if is_abbr_like(n[2])]
    neww_word = [n for n in neww if not is_abbr_like(n[2])]
    print("## [新词] 库中无 —— 普通词 %d 条（很可能是漏译）" % len({n[2] for n in neww_word}))
    for atom, n in collections.Counter(n[2] for n in neww_word).most_common(25):
        loc = next(x[1] for x in neww_word if x[2] == atom)
        print("   %-34s ×%-3d e.g. %s" % (atom[:34], n, loc))
    print()
    print("## [新词] 库中无 —— 缩写/编号 %d 条（多半按口径保留，留意即可）"
          % len({n[2] for n in neww_abbr}))
    for atom, n in collections.Counter(n[2] for n in neww_abbr).most_common(25):
        loc = next(x[1] for x in neww_abbr if x[2] == atom)
        print("   %-20s ×%-3d e.g. %s" % (atom[:20], n, loc))

    if "--out" in flags:
        i = sys.argv.index("--out")
        out = sys.argv[i + 1] if i + 1 < len(sys.argv) else "glossary-check.txt"
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("# 未译\tkind\tlayer\ten\tzh\tcat\tconf\tloc\n")
            for kind, layer, loc, atom, zh, cat, conf in miss:
                f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n"
                        % (kind, layer, atom, zh, cat, conf, loc))
            f.write("# 新词\ten\tloc\n")
            for layer, loc, atom in sorted(neww, key=lambda x: x[2]):
                f.write("%s\t%s\t%s\n" % (layer, atom, loc))
        print("\n明细已写入 %s" % out)


if __name__ == "__main__":
    main()
