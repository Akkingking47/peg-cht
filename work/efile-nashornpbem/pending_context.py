# -*- coding: utf-8 -*-
"""为 olgww2-pending.tsv 里的待考地名生成语境卡。

输出每个待考条目所在场景的：场景标题 + 同一分组内全部条目（标注已译/待考），
便于据邻居地名判定地区与拼写。

用法: python pending_context.py [--group PLACE] > out/pending-context.txt
"""
import io
import os
import sys

SCN = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))


def decode_smart(raw):
    try:
        s = raw.decode("gbk")
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return "zh", s
    except Exception:
        pass
    return "en", raw.decode("cp1252", "replace")


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    g = st
    while g < len(f) and f[g] != 0x3E:
        g += 1
    off = g + 1
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    items = []
    gi = 0
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
            items.append((gi, i, f[off:off + L]))
            off += L
        if not good:
            break
        gi += 1
        if cnt == 0:
            break
    return dict(title=title, items=items)


def main():
    grp = "PLACE"
    if "--group" in sys.argv:
        grp = sys.argv[sys.argv.index("--group") + 1]

    pend = {}
    for ln in io.open(os.path.join(HERE, "olgww2-pending.tsv"), encoding="utf-8").read().splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 5 and p[3] == grp:
            pend.setdefault(p[0], []).append((int(p[1]), int(p[2]), p[4]))

    print("待考 %s 共 %d 条，涉 %d 个场景" % (grp, sum(len(v) for v in pend.values()), len(pend)))
    print("=" * 100)
    for fn in sorted(pend):
        path = os.path.join(SCN, fn)
        if not os.path.exists(path):
            print("\n### %s  —— 文件不存在！" % fn)
            continue
        x = parse(path)
        if x is None:
            print("\n### %s  —— 解析失败" % fn)
            continue
        tenc, ttxt = decode_smart(x["title"])
        print("\n### %s   【场景标题：%s】" % (fn, ttxt))
        want = {(g, i) for g, i, _ in pend[fn]}
        for gi, idx, raw in x["items"]:
            enc, s = decode_smart(raw)
            mark = " ★★待考★★" if (gi, idx) in want else ""
            print("    g%-2d i%-3d [%-2s] %s%s" % (gi, idx, enc, s, mark))


if __name__ == "__main__":
    main()
