# -*- coding: utf-8 -*-
"""独立 .xscn 解析/比对器（不依赖 xscn-patch.ps1 的任何代码路径）。

用法:
  python verify_xscn.py <a.xscn> [b.xscn]

输出: 标题、组数、每组条目数、总条目数、数据区终点、文件长度、尾部残留字节数。
给两个路径时额外做结构比对与文本差异统计。

⚠ 两参数模式必须按 <original> <written> 顺序传（例如 备份在前、现文件在后），
  否则「改写/残留」统计会整体反转，把译文当成漏译（曾误报过一次）。
"""
import sys
import os

ENC_IN = "cp1252"   # 原文单字节（西欧重音按 Latin-1/Win-1252 单字节）
ENC_OUT = "gbk"     # 中文回写编码


def parse(path):
    f = open(path, "rb").read()
    st = -1
    for i in range(len(f) - 2):
        if f[i] == 0x3C and f[i + 1] == 0x4E and f[i + 2] == 0x3A:  # "<N:"
            st = i
            break
    if st < 0:
        return None
    g = st
    while g < len(f) and f[g] != 0x3E:  # ">"
        g += 1
    data_end = g + 1
    off = data_end

    title = None
    title_raw = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title_raw = f[off + 2:off + 2 + L]
            title = title_raw.decode(ENC_IN, "replace")
            off += 2 + L

    groups = []
    items = []          # (group, idx, raw_bytes, decoded)
    gi = 0
    while off + 2 <= len(f):
        cnt = f[off] | (f[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        good = True
        for k in range(cnt):
            if off + 2 > len(f):
                good = False
                break
            L = f[off] | (f[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(f):
                good = False
                break
            raw = f[off + 2:off + 2 + L]
            items.append((gi, k, raw, raw.decode(ENC_IN, "replace")))
            off += 2 + L
        if not good:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break

    return dict(path=path, size=len(f), data_end=data_end, title=title,
                title_raw=title_raw, groups=groups, items=items,
                parsed_end=off, tail=len(f) - off)


def decode_smart(raw):
    """先按 GBK 试（有汉字），失败再按 cp1252。"""
    try:
        s = raw.decode("gbk")
        # GBK 解码成功但可能是巧合；要求含汉字才算
        if any("\u4e00" <= ch <= "\u9fff" for ch in s):
            return "gbk", s
    except Exception:
        pass
    return "cp1252", raw.decode(ENC_IN, "replace")


def han_count(s):
    return sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")


def describe(tag, x):
    print("=== %s ===" % tag)
    if x is None:
        print("  解析失败（找不到 <N: 标记）")
        return
    print("  路径     : %s" % os.path.basename(x["path"]))
    print("  文件大小 : %d B    数据区终点 : %d    尾部残留 : %d B" % (x["size"], x["data_end"], x["tail"]))
    tenc, ttxt = decode_smart(x["title_raw"])
    print("  标题     : %r  (%s)" % (ttxt, tenc))
    print("  组数     : %d   组条目数 : %s" % (len(x["groups"]), x["groups"]))
    print("  总条目   : %d" % len(x["items"]))
    han = 0
    for _, _, raw, _ in x["items"]:
        han += han_count(decode_smart(raw)[1])
    print("  汉字总数 : %d（GBK 解码后统计）" % han)


def compare(a, b):
    print("\n=== 结构比对（original vs written）===")
    if a is None or b is None:
        print("  有一侧解析失败，无法比对")
        return 1
    bad = 0
    for k in ("data_end", "groups", "size"):
        va, vb = a[k], b[k]
        if k == "size":
            print("  %-9s : %s -> %s  %s" % ("文件大小", va, vb, "(变化 %+d)" % (vb - va)))
            continue
        s = "OK" if va == vb else "DIFF"
        if va != vb:
            bad += 1
        print("  %-9s : %s  [%s]" % (k, va if k == "data_end" else "%s" % va, s))
    n = "OK" if len(a["items"]) == len(b["items"]) else "DIFF"
    if len(a["items"]) != len(b["items"]):
        bad += 1
    print("  条目数    : %d -> %d  [%s]" % (len(a["items"]), len(b["items"]), n))

    # 逐条对齐
    chg = same = 0
    chg_han = 0
    eng_left = []
    for (ga, ia, ra, ta), (gb, ib, rb, tb) in zip(a["items"], b["items"]):
        if ra == rb:
            same += 1
        else:
            chg += 1
            enc, s = decode_smart(rb)
            if han_count(s):
                chg_han += 1
            else:
                eng_left.append((ga, ia, ta, enc, s))
    print("  逐条：改写 %d 处 / 保留原字节 %d 处（共 %d）" % (chg, same, len(b["items"])))
    print("  改写中含汉字的：%d 处" % chg_han)
    if eng_left:
        print("  ⚠️ 改写后仍无汉字 %d 处（样例最多 10 条）:" % len(eng_left))
        for g, i, o, enc, s in eng_left[:10]:
            print("     g%d i%d  %r -> (%s) %r" % (g, i, o, enc, s))
    else:
        print("  ✅ 所有已改写条目均含汉字")

    # 残留英文扫描：写出后每条里仍是纯 ASCII 且长度>3 的
    ascii_left = []
    for (g, i, raw, old_t) in b["items"]:
        enc, s = decode_smart(raw)
        if enc == "cp1252" and len(s.strip()) > 3 and all(ord(c) < 128 for c in s):
            ascii_left.append((g, i, s))
    print("  仍未翻译的纯 ASCII 条目（长度>3）：%d 条" % len(ascii_left))
    for g, i, s in ascii_left[:12]:
        print("     g%d i%d  %r" % (g, i, s))

    print("\n结论：结构%s" % ("一致 ✅" if bad == 0 else "存在 %d 处偏差 ❌" % bad))
    return bad


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        return 1
    xs = [parse(p) for p in paths]
    for p, x in zip(paths, xs):
        describe(os.path.basename(p), x)
    if len(xs) == 2:
        return compare(xs[0], xs[1])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
