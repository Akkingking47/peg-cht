# -*- coding: utf-8 -*-
"""生成运行期内存扫描的探针清单。

对每个已部署的 TEXT-ZH 文件，按行号配对「原文(备份) ↔ 译文(已部署)」，
挑出「原文为纯 ASCII 且译文含汉字且长度≥4」的行作为探针。
输出：probes.tsv  —— 列 = 中文探针 <TAB> 英文原文 <TAB> 来源
"""
import io
import os

ROOT = r"D:\DSH\军事游戏汉化"
BAK = os.path.join(ROOT, r"backup\ORIGINAL-EFILE_NASHORNPBEM")
GAME = r"D:\OpenPG2\EFILE_NASHORNPBEM"

PAIRS = [
    (os.path.join(BAK, "equip.txt"), os.path.join(GAME, r"TEXT-ZH\equip.txt"), "equip.txt", 6),
    (os.path.join(BAK, "names.txt"), os.path.join(GAME, r"TEXT-ZH\names.txt"), "names.txt", 6),
    (os.path.join(BAK, "nations.txt"), os.path.join(GAME, r"TEXT-ZH\nations.txt"), "nations.txt", 4),
    (os.path.join(BAK, "strings_efile.txt"), os.path.join(GAME, r"TEXT-ZH\strings_efile.txt"), "strings_efile.txt", 4),
]


def lines(p):
    if not os.path.exists(p):
        return None
    return io.open(p, "rb").read().decode("gbk", "replace").splitlines()


def has_han(s):
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


out = []
for orig_p, zh_p, tag, want in PAIRS:
    o = lines(orig_p)
    z = lines(zh_p)
    if o is None or z is None:
        print("[缺] %s" % tag)
        continue
    print("%-18s 行数 原文=%d 译文=%d %s" % (tag, len(o), len(z), "OK" if len(o) == len(z) else "❌不等"))
    n = 0
    # 挑长度适中的（4..28 字符），从中间开始以免全是首行表头
    # 排除带 "(not used)" 的行：那是引擎解析用的标记，可能被剥离后再入库
    cand = []
    for i, (a, b) in enumerate(zip(o, z), 1):
        a, b = a.strip(), b.strip()
        if not a or not b:
            continue
        if not is_ascii(a) or not has_han(b):
            continue
        if len(b) < 4 or len(a) < 4:
            continue
        if "(not used)" in a.lower() or "not used" in b.lower():
            continue
        cand.append((i, a, b))
    cand.sort(key=lambda t: -len(t[2]))
    for i, a, b in cand:
        if n >= want:
            break
        out.append((b, a, "%s L%d" % (tag, i)))
        n += 1
    print("   取 %d 条探针" % n)

# .xscn 探针（地名 + 标题 + 番号组）
XS = [
    ("斯列夫明斯卡妓院", "Slevminska Brothels", "xscn g0.002"),
    ("乌托邦悖论", "UtopianParadox", "xscn 标题"),
    ("阿拉斯古代墓葬遗址", "Arras Ancient Burial Site", "xscn g0.228"),
    ("弗拉迪斯铁路补给站", "Vladis Train Depot", "xscn g0.007"),
    ("公路桥", "Road Bridge", "xscn g0.006"),
    ("魏特曼的第 101 装甲团", "Wittmann's 101st Pz Regiment", "xscn g1.016"),
    ("北部补给区", "Northern Supply Area", "xscn g0.000"),
]

p = os.path.join(ROOT, r"work\efile-nashornpbem\probes.tsv")
with io.open(p, "w", encoding="utf-8", newline="\n") as f:
    f.write("# zh\tenglish\tsource\n")
    for zh, en, src in out:
        f.write("%s\t%s\t%s\n" % (zh, en, src))
    for zh, en, src in XS:
        f.write("%s\t%s\t%s\n" % (zh, en, src))

print("\n写出 %d 条探针 -> %s" % (len(out) + len(XS), p))
for zh, en, src in out + XS:
    print("   %-22s | %-34s | %s" % (zh, en, src))
