# -*- coding: utf-8 -*-
"""EFILE_AG `.xscn` 译名生成器：规则引擎 + 词典 -> ag-xscn-map.tsv

用法：
  python make_ag_xscn_map.py            # 生成 map，并输出未覆盖清单 ag-xscn-todo.tsv
  python make_ag_xscn_map.py --show N   # 预览前 N 条译文

设计：
  * 词典在 ag-xscn-dict.tsv（word<TAB>中文），与规则解耦，可批量追加
  * 规则负责罗马编制串（Legio X / Y / Z、Ala X / Y、纯数字层级）
  * 未命中一律进 todo，**不允许静默漏译**
"""
import io
import os
import re
import sys
import collections

WORK = r"D:/DSH/军事游戏汉化/work/glossary"
UNIQ = os.path.join(WORK, "ag-xscn-uniq.tsv")
DICT = os.path.join(WORK, "ag-xscn-dict.tsv")
MAP = os.path.join(WORK, "ag-xscn-map.tsv")
TODO = os.path.join(WORK, "ag-xscn-todo.tsv")

RN_VAL = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
RN_CHARS = set(RN_VAL)


NAMES = os.path.join(WORK, "ag-names-map.tsv")


def load_dict():
    # 先铺底：951 条古人音译表（人名/帝名/年号），再由专属词典覆盖
    d = {}
    if os.path.exists(NAMES):
        with io.open(NAMES, encoding="utf-8-sig", newline="") as f:
            txt = f.read()
        for ln in txt.replace("\r\n", "\n").split("\n")[1:]:
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1].strip():
                d[c[0]] = c[1].strip()
    if not os.path.exists(DICT):
        return d
    with io.open(DICT, encoding="utf-8-sig", newline="") as f:
        txt = f.read()
    for ln in txt.replace("\r\n", "\n").split("\n"):
        if not ln.strip() or ln.startswith("#"):
            continue
        c = ln.split("\t")
        # 允许空译文：虚词 the / ! / * 等需要映射成空串才能拼接
        if len(c) >= 2 and c[0]:
            d[c[0]] = c[1].strip()
    return d


def is_rn(s):
    return bool(s) and all(c in RN_CHARS for c in s)


def rn2int(s):
    total = 0
    prev = 0
    for c in reversed(s):
        v = RN_VAL[c]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


D = load_dict()


# ---------------------------------------------------------------- 段翻译
TOKEN_RE = re.compile(r'"[^"]*"|[A-Za-z][A-Za-z.\-]*|\'s|[0-9]+|\S')


def tokenize(seg):
    return TOKEN_RE.findall(seg)


def trans_seg(seg, level, kind):
    """翻译单个 '/' 段。level=0 军团级, 1 大队级, 2 百人队级。
    kind: 'legio' | 'ala' | 'plain'"""
    seg = seg.strip()
    if seg in D:
        return D[seg]
    q = seg.strip('"').strip()
    if q != seg and q in D:      # "Alaudae" -> 云雀
        return D[q]
    if q != seg and " " in q:    # "Octavian Caesar" -> 屋大维·凯撒
        inner = tokenize(q)
        v = lookup_name(inner, "·")
        if v is not None:
            return v
    if is_rn(seg):
        n = rn2int(seg)
        if kind == "ala":
            return ["第%d骑兵翼" % n, "第%d骑兵中队" % n, "第%d小队" % n][min(level, 2)]
        if kind == "cohors":
            return ["第%d大队" % n, "第%d百人队" % n, "第%d小队" % n][min(level, 2)]
        return ["第%d军团" % n, "第%d大队" % n, "第%d百人队" % n][min(level, 2)]
    toks = tokenize(seg)
    if not toks:
        return None
    toks = [t.strip('"').strip() if t.startswith('"') else t for t in toks]
    if len(toks) > 1:
        toks = [t for t in toks if t.lower() != "the"]
    # "Sagitarii I" -> 弓箭手1
    if len(toks) == 2 and is_rn(toks[1]) and toks[0] in D:
        return "%s%d" % (D[toks[0]], rn2int(toks[1]))
    if len(toks) == 2 and is_rn(toks[0]) and toks[1] in D:
        return "%s%d" % (D[toks[1]], rn2int(toks[0]))
    # X('s|') Y -> X 的 Y（"'" 可出现在任意位置：Army' Scorpion）
    k = next((j for j, t in enumerate(toks) if t in ("'s", "'")), None)
    if k is not None and 0 < k < len(toks) - 1:
        lv = lookup_name(toks[:k], "·")
        rv = trans_seg(" ".join(toks[k + 1:]), level, kind)
        if lv and rv:
            return "%s的%s" % (lv, rv)
    # X of [the] Y -> Y 的 X
    low = [t.lower() for t in toks]
    if "of" in low:
        k = low.index("of")
        left = [t for t in toks[:k] if t.lower() != "the"]
        right = [t for t in toks[k + 1:] if t.lower() != "the"]
        lv = lookup_name(left)
        rv = lookup_name(right)
        if lv is None or rv is None:
            return None
        return "%s的%s" % (rv, lv)
    # 中置编制词：Cilicia Ala I / Rhine Patrol II / Pompey's Fleet Army VII
    if len(toks) >= 3 and is_rn(toks[-1].rstrip(".")):
        body = toks[:-1]
        n = rn2int(toks[-1].rstrip("."))
        if body[-1] in ("Ala", "Cohors", "Turma", "Legio") and len(body) >= 2:
            pre = lookup_name(body[:-1])
            if pre is not None:
                return "%s第%d%s" % (pre, n, D.get(body[-1], "部队"))
        pre = lookup_name(body)
        if pre is not None:
            return "%s%d" % (pre, n)
    # 全词命中 -> 顺次拼接
    if all(t in D for t in toks):
        return "".join(D[t] for t in toks)
    return None


def lookup_name(toks, sep=""):
    """把若干 token 译成人名/称号；全命中才返回。sep 默认直接连写。"""
    if not toks:
        return None
    joined = " ".join(t.strip('"').strip() for t in toks)
    if joined in D:
        return D[joined]
    if len(toks) == 1:
        return D.get(toks[0].strip('"').strip())
    if all(t.strip('"').strip() in D for t in toks):
        return sep.join(D[t.strip('"').strip()] for t in toks)
    return None


def trans_legio(seg):
    """Legio [Name|"Epithet"] [RN] [TYPE [RN2]] -> 中文；失败 None

    例：Legio I / Legio Crassus I / Legio V. "Alandae" /
        Legio Marius AR II / praetoriani Legio I / Legio "Cilicia"
    返回 (主名, [附加段]) 或 None
    """
    toks = tokenize(seg)
    if not toks:
        return None
    i = 0
    pre = False
    if toks[0].lower().startswith("praetorian"):
        # Praetoriani / Praetorianii 自身成军，不一定带 Legio
        base = D.get(toks[0], "禁卫军")
        if len(toks) == 1:
            return (base, [])
        if toks[1].lower() in ("legio", "legion", "legionen"):
            pre = True
            i = 1
        else:
            rest = trans_seg(" ".join(toks[1:]), 1, "legio")
            if rest is None:
                return None
            return (base, [rest])
    if i >= len(toks) or toks[i].lower() not in ("legio", "legion", "legionen"):
        return None
    i += 1
    rest = [t for t in toks[i:] if t not in ("-",)]
    idx = next((k for k, t in enumerate(rest) if is_rn(t.rstrip("."))), None)
    extra = []
    if idx is None:
        nm = lookup_name(rest)
        if nm is None:
            return None
        return (("禁卫" if pre else "") + nm + "军团", extra)
    rn = rn2int(rest[idx].rstrip("."))
    before, after = rest[:idx], rest[idx + 1:]
    out = "第%d军团" % rn
    if before:
        nm = lookup_name(before, "·")
        if nm is None:
            return None
        # 引号称号放番号后："第5云雀军团"；人名放番号前："克拉苏斯第1军团"
        if any(b.startswith('"') for b in before):
            out = "第%d%s军团" % (rn, nm)
        else:
            out = "%s第%d军团" % (nm, rn)
    if after:
        t = trans_seg(" ".join(after), 1, "legio")
        if t is None:
            return None
        extra.append(t)
    if pre:
        out = "禁卫" + out
    return (out, extra)


SEP_RE = re.compile(r"\s+/\s+|\s+-\s+|/")


def trans(s):
    """整串翻译；失败返回 None"""
    s0 = s.strip()
    if not s0:
        return ""
    if s0 in D:
        return D[s0]
    segs = [x.strip() for x in SEP_RE.split(s0) if x.strip()]
    head = segs[0]
    hl = head.lower()
    extra = []
    if (hl.startswith("legio") or hl.startswith("legion")
            or (hl.startswith("praetoriani") and "legio" in hl)):
        kind = "legio"
        r = trans_legio(head)
        if r is None:
            return None
        h, extra = r
    elif hl.startswith("praetoriani"):
        kind = "legio"
        r = trans_legio(head)
        if r is None:
            return None
        h, extra = r
    elif hl.startswith("ala"):
        kind = "ala"
        m = re.match(r'^Ala\s+(?P<rn>[IVXL]+)$', head, re.I)
        h = ("第%d骑兵翼" % rn2int(m.group("rn"))) if m else None
        if h is None:
            h = trans_seg(head, 0, "ala")
    else:
        kind = "plain"
        h = trans_seg(head, 0, "plain")
    if h is None:
        return None
    out = [h] + extra
    for i, seg in enumerate(segs[1:], start=1 + len(extra)):
        t = trans_seg(seg, i, kind)
        if t is None:
            return None
        out.append(t)
    return "/".join(out)


def main():
    show = "--show" in sys.argv
    n = 40
    if "--show" in sys.argv:
        i = sys.argv.index("--show")
        if i + 1 < len(sys.argv):
            n = int(sys.argv[i + 1])
    rows = []
    with io.open(UNIQ, encoding="utf-8") as f:
        txt = f.read()
    for ln in txt.replace("\r\n", "\n").split("\n")[1:]:
        if not ln.strip():
            continue
        c = ln.split("\t")
        rows.append((c[0], int(c[1]), c[2], c[3] if len(c) > 3 else ""))

    ok = {}
    todo = []
    for src, freq, groups, ex in rows:
        s = src.strip()
        if not s:
            ok[src] = ""
            continue
        t = trans(s)
        if t is None:
            todo.append((src, freq, groups, ex))
        else:
            ok[src] = t
    tot = sum(r[1] for r in rows)
    cov = sum(r[1] for r in rows if r[0].strip() == "" or r[0] in ok)
    print("唯一串 %d / 出现 %d" % (len(rows), tot))
    print("已覆盖 %d 唯一（出现 %d 次，%.1f%%）" % (
        len(rows) - len(todo), cov, 100.0 * cov / tot))
    print("未覆盖 %d 唯一（出现 %d 次）" % (
        len(todo), sum(r[1] for r in todo)))
    if show:
        for src, freq, groups, ex in rows[:n]:
            s = src.strip()
            print("  %-42s -> %s" % (s, ok.get(src) or "❌"))
        return
    with io.open(TODO, "w", encoding="utf-8", newline="") as f:
        f.write("src\tfreq\tgroups\texample\n")
        for src, freq, groups, ex in todo:
            f.write("%s\t%d\t%s\t%s\n" % (src, freq, groups, ex))
    print("todo -> %s" % TODO)
    if os.path.exists(MAP) and "--keep" in sys.argv:
        print("(保留既有 map)")
        return
    with io.open(MAP, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for k, v in ok.items():
            f.write("%s\t%s\n" % (k, v))
    print("map -> %s" % MAP)


if __name__ == "__main__":
    main()
