# -*- coding: utf-8 -*-
"""用场景自带 <name>.txt（汉化地名清单）反查 .xscn 组0 的译名。

要点（避免上一版漂移）：
  1. .txt 里混有「部队行」（含 `/`，如 `第17团/第7步兵师/第10军`）→ 先过滤，只留地名行；
  2. 用 difflib 对 (.xscn组0, .txt地名行) 做**全局序列对齐**，等长 replace 块也视为对应；
  3. 仍无法确定的（不等长空隙）用左右锚点线性插值，并标注 ? 供人工复核。

用法: python match_txt_names.py
"""
import difflib
import io
import os
import re

SCN = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))
SHIP = re.compile(r"^(HMS|USS|IJN|RMS|SMS|MV|SS|HMCS|HMAS|ORP|ARA|KM|RN|HMNZS|HMNoS)\b")


def parse_g0(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    g = st
    while g < len(f) and f[g] != 0x3E:
        g += 1
    off = g + 1
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            off += 2 + L
    items, gi = [], 0
    while off + 2 <= len(f) and gi <= 64:
        cnt = f[off] | (f[off + 1] << 8)
        off += 2
        good = True
        for i in range(cnt):
            if off + 2 > len(f):
                good = False
                break
            L = f[off] | (f[off + 1] << 8)
            off += 2
            if off + L > len(f):
                good = False
                break
            if gi == 0:
                items.append(f[off:off + L])
            off += L
        if not good or cnt == 0:
            break
        gi += 1
    return items


def dec(raw):
    try:
        s = raw.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return s
    except Exception:
        pass
    return raw.decode("cp1252", "replace")


def zh(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def load_txt(fn):
    for c in (fn[:-5] + ".txt", fn[:-5].lower() + ".txt"):
        p = os.path.join(SCN, c)
        if os.path.exists(p):
            L = io.open(p, encoding="gbk", errors="replace").read().splitlines()
            return [t.strip() for t in L if t.strip()]
    return None


def is_unit_line(s):
    """部队行判据：含 '/'（编制层级分隔），或整行形如 [XXX]。"""
    return ("/" in s) or re.match(r"^\[[^\]]+\]$", s) is not None


def align(X, T):
    """返回 xscn 组0 索引 -> txt 索引 的映射。"""
    sm = difflib.SequenceMatcher(None, X, T, autojunk=False)
    pairs = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1):
                pairs[i1 + k] = j1 + k
    return pairs


def lookup(pairs, X, T, i):
    if i in pairs:
        return T[pairs[i]]
    left = [j for j in pairs if j < i]
    right = [j for j in pairs if j > i]
    if left:
        jl = max(left)
        e = pairs[jl] + (i - jl)
        if 0 <= e < len(T):
            return T[e]
    if right:
        jr = min(right)
        e = pairs[jr] - (jr - i)
        if 0 <= e < len(T):
            return T[e]
    return "?"


def main():
    pend = {}
    for ln in io.open(os.path.join(HERE, "olgww2-pending.tsv"), encoding="utf-8").read().splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 5 and p[3] == "PLACE":
            pend.setdefault(p[0], []).append(int(p[2]))

    todo, mism, nodata = [], [], []
    quality = {}
    for fn in sorted(pend):
        cur = parse_g0(os.path.join(SCN, fn))
        if cur is None:
            nodata.append((fn, "解析失败"))
            continue
        cur = [dec(r) for r in cur]
        raw_txt = load_txt(fn)
        if raw_txt is None:
            nodata.append((fn, "无同名 .txt"))
            continue
        T = [t for t in raw_txt if not is_unit_line(t)]
        X = [s if zh(s) else "\x00" for s in cur]
        pairs = align(X, T)

        # 该场景的对齐质量 = 已译条目里与 .txt 对上号的比例
        zh_idx = [i for i, s in enumerate(cur) if zh(s)]
        hit = sum(1 for i in zh_idx if lookup(pairs, X, T, i) == cur[i])
        q = hit / float(len(zh_idx)) if zh_idx else 0.0
        quality[fn] = (q, hit, len(zh_idx))

        for i in pend[fn]:
            if i >= len(cur) or zh(cur[i]):
                continue
            todo.append((fn, i, cur[i], lookup(pairs, X, T, i), q))

        for i, s in enumerate(cur):
            if not zh(s):
                continue
            g = lookup(pairs, X, T, i)
            if g not in ("?", s):
                mism.append((fn, i, s, g, q))

    print("=" * 96)
    print("0. 各场景对齐质量（已译条目与 .txt 对上号的比例；<50% 的场景结论不可信）")
    print("=" * 96)
    for fn in sorted(quality, key=lambda k: -quality[k][0]):
        q, hit, tot = quality[fn]
        bar = "★可信" if q >= 0.7 else ("~参考" if q >= 0.5 else "✗不可信")
        print("  %-18s %5.1f%%  (%d/%d)  %s" % (fn, q * 100, hit, tot, bar))

    print()
    print("=" * 96)
    print("A. 待考条目 -> .txt 权威译名（%d 条；★=场景对齐可信，✗=场景不可信仅供参考）" % len(todo))
    print("=" * 96)
    print("%-18s %-4s %-28s %-22s %s" % ("file", "i", "src", "txt译名", "对齐"))
    for fn, i, s, h, q in todo:
        mark = "★" if q >= 0.7 else ("~" if q >= 0.5 else "✗")
        print("%-18s %-4d %-28s %-22s %s %.0f%%" % (fn, i, s, h, mark, q * 100))

    print()
    print("=" * 96)
    print("B. .xscn 已有中文 与 .txt 不一致（仅列对齐可信场景，需人工判断）")
    print("=" * 96)
    n = 0
    for fn, i, a, b, q in mism:
        if q < 0.7:
            continue
        n += 1
        print("%-18s %-4d %-26s | %s" % (fn, i, a, b))
    print("  （可信场景内共 %d 处；不可信场景的 %d 处已略去）" %
          (n, len(mism) - n))

    if nodata:
        print()
        print("!! 缺数据: %s" % nodata)


if __name__ == "__main__":
    main()
