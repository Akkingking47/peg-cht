# -*- coding: utf-8 -*-
"""抽检 intro 覆盖结果：编码 / BOM / 行数 / 中文占比 / 前若干行内容。"""
import io, os, sys

GAME = r"D:\OpenPG2\EFILE_NASHORNPBEM"
WORK = r"D:\DSH\军事游戏汉化\work\efile-nashornpbem"
BAK = r"D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_NASHORNPBEM"

PAIRS = [
    ("SCENARIO\\utopianparadoxintro.txt", "游戏内(已覆盖)"),
    ("TEXT-ZH\\SCENARIO\\utopianparadoxintro.txt", "TEXT-ZH 存档"),
]


def sniff(path):
    with open(path, "rb") as f:
        raw = f.read()
    bom = "YES" if raw[:3] == b"\xef\xbb\xbf" else "no"
    utf16 = "YES" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "no"
    # 解码尝试
    dec = "?"
    text = None
    for enc in ("gbk", "utf-8"):
        try:
            text = raw.decode(enc)
            dec = enc
            break
        except Exception:
            continue
    crlf = raw.count(b"\r\n")
    lf_only = raw.count(b"\n") - crlf
    han = sum(1 for ch in (text or "") if "\u4e00" <= ch <= "\u9fff")
    # 判断是否含 U+FFFD
    fffd = (text or "").count("\ufffd")
    return dict(size=len(raw), bom=bom, utf16=utf16, enc=dec,
                crlf=crlf, lf_only=lf_only, han=han, fffd=fffd, text=text)


def main():
    for rel, tag in PAIRS:
        p = os.path.join(GAME, rel)
        if not os.path.exists(p):
            print("[缺] %s -> %s" % (tag, p))
            continue
        s = sniff(p)
        print("=== %s ===" % tag)
        print("  路径 : %s" % p)
        print("  大小 : %d B   BOM=%s   UTF16=%s   解码=%s" % (s["size"], s["bom"], s["utf16"], s["enc"]))
        print("  行尾 : CRLF=%d  LF-only=%d" % (s["crlf"], s["lf_only"]))
        print("  汉字 : %d 个   替换符U+FFFD=%d" % (s["han"], s["fffd"]))
        lines = (s["text"] or "").splitlines()
        print("  行数 : %d" % len(lines))
        print("  前 8 行:")
        for ln in lines[:8]:
            print("    | %s" % ln)
        print()

    # 与备份原文对比
    bak = os.path.join(BAK, "SCENARIO", "utopianparadoxintro.txt")
    cur = os.path.join(GAME, "SCENARIO", "utopianparadoxintro.txt")
    print("=== 原文 vs 覆盖后 行数对照 ===")
    for p, tag in ((bak, "原文(备份)"), (cur, "当前")):
        if os.path.exists(p):
            s = sniff(p)
            print("  %-10s %6d B  %3d 行  汉字 %d" % (tag, s["size"], len((s["text"] or "").splitlines()), s["han"]))


if __name__ == "__main__":
    main()
