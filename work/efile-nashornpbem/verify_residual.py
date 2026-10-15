# -*- coding: utf-8 -*-
"""独立复核（最强）：重建比对。

取「备份版」→ 按 glossary 替换标题与条目 → 重新序列化
→ 必须与「现版」**逐字节相同**。
任何一处不符即说明写入过程动了不该动的字节。
"""
import os
import io
import sys

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
BAK = r"D:/DSH/军事游戏汉化/backup/olgww2-xscn-residual-before"
GLOSS = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/olgww2-glossary.tsv"
LIST = r"D:/DSH/军事游戏汉化/work/efile-nashornpbem/out/changed_all.txt"


def load_gloss():
    g = {}
    L = io.open(GLOSS, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(L):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 3:
            g[c[0]] = c[1]
    return g


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    tlf = f.index(b">", st) + 1          # title 长度字段起点
    prefix = f[:tlf]
    off = tlf
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    layout = []
    while off + 2 <= len(f):
        cnt = f[off] | (f[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        sav = off
        off += 2
        vals = []
        bad = False
        for k in range(cnt):
            if off + 2 > len(f):
                bad = True
                break
            L = f[off] | (f[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(f):
                bad = True
                break
            vals.append(f[off + 2:off + 2 + L])
            off += 2 + L
        if bad:
            off = sav
            break
        layout.append((cnt, vals))
        if len(layout) > 64:
            break
    return prefix, title, layout, f[off:]


def repl(raw, g):
    try:
        key = raw.decode("ascii").rstrip()
    except Exception:
        return raw
    dst = g.get(key)
    if dst:
        return dst.encode("gbk")
    return raw


def rebuild(prefix, title, layout, suffix, g):
    out = bytearray(prefix)
    t = repl(title, g) if title else title
    if title:
        out += len(t).to_bytes(2, "little") + t
    for cnt, vals in layout:
        out += cnt.to_bytes(2, "little")
        for v in vals:
            nv = repl(v, g)
            out += len(nv).to_bytes(2, "little") + nv
    out += suffix
    return bytes(out)


def main():
    g = load_gloss()
    files = [l.strip() for l in io.open(LIST, encoding="utf-8").read().split("\n") if l.strip()]
    ok = miss = 0
    bad = []
    for fn in files:
        pa, pb = os.path.join(BAK, fn), os.path.join(D, fn)
        prefix, title, layout, suffix = parse(pa)
        ra = open(pa, "rb").read()
        rb = open(pb, "rb").read()
        rec = rebuild(prefix, title, layout, suffix, g)
        if rec == rb:
            ok += 1
        elif rec == ra:
            miss += 1
            bad.append((fn, "重建==原文（译名表未命中）", "%d/%d" % (len(ra), len(rb))))
        else:
            # 找第一处不同
            n = min(len(rec), len(rb))
            pos = next((i for i in range(n) if rec[i] != rb[i]), n)
            bad.append((fn, "重建≠现版 @%d" % pos,
                        "%r | 重建 %r | 现版 %r" % (rb[max(0, pos - 10):pos + 14],
                                                    rec[max(0, pos - 10):pos + 14],
                                                    rb[max(0, pos - 10):pos + 14])))
    print("重建 = 现版（完全一致）: %d / %d" % (ok, len(files)))
    print("重建 = 原文（未命中）  : %d" % miss)
    print("不一致                 : %d" % len(bad))
    for fn, why, d in bad[:40]:
        print("  !!! %-22s %-30s %s" % (fn, why, d))
    return 0 if ok == len(files) else 1


sys.exit(main())
