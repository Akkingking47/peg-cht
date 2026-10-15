# -*- coding: utf-8 -*-
"""OLGWW2 待考地名权威定名：用「原始英文清单 ↔ 中文清单」逐行对照查表。

数据源：
  原文: backup/ORIGINAL-EFILE_OLGWW2/SCENARIO/<name>.txt   (cp1252)
  中文: D:/OpenPG2/EFILE_OLGWW2/SCENARIO/<name>.txt          (gbk，已被汉化覆盖)
两者是同一份名单的两个语言版本，行行对应 —— 直接建 en->zh 字典，无对齐风险。

用法: python lookup_via_txt.py
"""
import io
import os

SCN = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
ORIG = r"D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_OLGWW2/SCENARIO"
HERE = os.path.dirname(os.path.abspath(__file__))


def load(fn_dir, fn, enc):
    for c in (fn[:-5] + ".txt", fn[:-5].lower() + ".txt", fn[:-5].upper() + ".txt"):
        p = os.path.join(fn_dir, c)
        if os.path.exists(p):
            try:
                return io.open(p, encoding=enc, errors="replace").read().splitlines()
            except Exception:
                return None
    return None


def main():
    pend = {}
    for ln in io.open(os.path.join(HERE, "olgww2-pending.tsv"), encoding="utf-8").read().splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 5 and p[3] == "PLACE":
            pend.setdefault(p[0], []).append(int(p[2]))

    ok, miss, nofile = [], [], []
    for fn in sorted(pend):
        o = load(ORIG, fn, "cp1252")
        z = load(SCN, fn, "gbk")
        if o is None or z is None:
            for i in pend[fn]:
                nofile.append((fn, i))
            continue
        m = {}
        for a, b in zip(o, z):
            a, b = a.strip(), b.strip()
            if a and b and a not in m:
                m[a] = b
        # 已汉化版本可能加空格，做一次去空格键
        m2 = {k.replace(" ", ""): v for k, v in m.items()}

        # 读 .xscn 组0 拿原文
        import struct  # noqa
        path = os.path.join(SCN, fn)
        f = open(path, "rb").read()
        st = f.find(b"<N:")
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

        for i in pend[fn]:
            if i >= len(items):
                miss.append((fn, i, "?", "索引越界"))
                continue
            s = items[i].decode("cp1252", "replace").strip()
            v = m.get(s) or m2.get(s.replace(" ", ""))
            if v:
                ok.append((fn, i, s, v))
            else:
                miss.append((fn, i, s, "未在清单中找到"))

    print("=" * 90)
    print("A. 权威对照命中（%d 条）—— 原文清单↔中文清单逐行查表" % len(ok))
    print("=" * 90)
    print("%-18s %-4s %-30s %s" % ("file", "i", "src", "权威译名"))
    for fn, i, s, v in ok:
        print("%-18s %-4d %-30s %s" % (fn, i, s, v))

    print()
    print("=" * 90)
    print("B. 未命中（%d 条）—— 需另行判定" % len(miss))
    print("=" * 90)
    for fn, i, s, why in miss:
        print("%-18s %-4d %-30s %s" % (fn, i, s, why))
    if nofile:
        print("\n!! 缺清单文件: %s" % sorted({f for f, _ in nofile}))


if __name__ == "__main__":
    main()
