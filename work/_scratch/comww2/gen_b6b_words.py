# -*- coding: utf-8 -*-
"""批次 6b-4（单词地名）：把「纯译文列表」按顺序配到 todo 的 src 上。

用法: python gen_b6b_words.py --dst _b6b4_dst.txt --from 1 --to 300 --out xscn-new-6b4.tsv
（from/to 为 1-based，闭区间；超出实际条数即报错）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))


def opt(name, dflt=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else dflt


def main():
    dst_f = os.path.join(HERE, opt("--dst"))
    out_f = os.path.join(HERE, opt("--out"))
    a = int(opt("--from", "1"))
    b = int(opt("--to", "0"))
    srcs = []
    for i, ln in enumerate(io.open(os.path.join(HERE, "_b6b_todo.tsv"), encoding="utf-8")):
        if i == 0:
            continue
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 3 and c[0] == "单词地名":
            srcs.append(c[1])
    dsts = [l.rstrip("\r\n") for l in io.open(dst_f, encoding="utf-8") if l.strip()]
    print("src 总 %d ；本批译文 %d（%d-%d）" % (len(srcs), len(dsts), a, b))
    if b == 0:
        b = a + len(dsts) - 1
    win = srcs[a - 1:b]
    if len(win) != len(dsts):
        raise SystemExit("!! 区间 %d-%d 有 %d 条 src，译文 %d 条 —— 不符" % (a, b, len(win), len(dsts)))
    # 校验 dst
    bad = []
    for s, d in zip(win, dsts):
        if not d.strip() or "\t" in d:
            bad.append((s, d, "空/含制表符"))
            continue
        try:
            d.encode("gbk")
        except UnicodeEncodeError:
            bad.append((s, d, "GBK 不可编码"))
    if bad:
        for s, d, w in bad:
            print("   !! %-26s -> %-20s (%s)" % (s, d, w))
        raise SystemExit(1)
    with io.open(out_f, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in zip(win, dsts):
            f.write("%s\t%s\n" % (s, d))
    bb = open(out_f, "rb").read()
    print("已写 %s（%d 条，BOM=%s）" % (os.path.basename(out_f), len(win), bb[:3] == b"\xef\xbb\xbf"))
    for n, (s, d) in enumerate(zip(win, dsts), 1):
        print("  %3d %-24s -> %s" % (n, s[:24], d))


if __name__ == "__main__":
    main()
