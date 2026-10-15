# -*- coding: utf-8 -*-
"""直接读 .xscn 文件（不信映射表），审计「仍是纯 ASCII 的条目」。

分类：
  SHIP  : 船名前缀（HMS/USS/IJN/MV/SS/RMS/SMS 等）—— 按既定政策保留原文，不算漏译
  ACRO  : 全大写、或含数字、或极短 —— 缩写/型号，算合规
  ASCII : 其余纯 ASCII 条目 —— **疑似漏译候选**
"""
import os
import re
import sys
from collections import Counter

EFILES = {
    "EFILE_OLGWW2": r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO",
    "EFILE_OPENPG": r"D:/OpenPG2/EFILE_OPENPG/SCENARIO",
}
SHIP = re.compile(r"^(HMS|USS|IJN|RMS|SMS|MV|SS|USS|HMCS|HMAS|ORP|ARA|KM|RN)\b")
ACRO = re.compile(r"^[A-Z0-9][A-Z0-9 /\-\.',&\+\(\)]*$")


def parse(path):
    f = open(path, "rb").read()
    st = f.find(b"<N:")
    if st < 0:
        return None
    off = f.index(b">", st) + 1
    title = b""
    if off + 2 <= len(f):
        L = f[off] | (f[off + 1] << 8)
        if 0 < L and off + 2 + L <= len(f):
            title = f[off + 2:off + 2 + L]
            off += 2 + L
    groups, items = [], []
    gi = 0
    while off + 2 <= len(f):
        cnt = f[off] | (f[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        bad = False
        for k in range(cnt):
            if off + 2 > len(f):
                bad = True
                break
            L = f[off] | (f[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(f):
                bad = True
                break
            items.append((gi, k, f[off + 2:off + 2 + L]))
            off += 2 + L
        if bad:
            break
        groups.append(cnt)
        gi += 1
        if gi > 64:
            break
    return dict(title=title, groups=groups, items=items)


def is_cjk(raw):
    try:
        s = raw.decode("gbk")
    except Exception:
        return False
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def main():
    for ef, d in EFILES.items():
        if not os.path.isdir(d):
            continue
        files = sorted(f for f in os.listdir(d) if f.lower().endswith(".xscn"))
        cnt = Counter()
        ascii_items = []
        ship = []
        cjk_items = 0
        total = 0
        for fn in files:
            x = parse(os.path.join(d, fn))
            if x is None:
                cnt["unparsed"] += 1
                continue
            cnt["files"] += 1
            if is_cjk(x["title"]):
                cjk_items += 1
            else:
                ascii_items.append((fn, -1, 0, x["title"].decode("cp1252", "replace")))
            for g, i, raw in x["items"]:
                total += 1
                if is_cjk(raw):
                    cjk_items += 1
                    continue
                try:
                    s = raw.decode("ascii")
                except Exception:
                    cnt["non-ascii-non-cjk"] += 1
                    continue
                if len(s.strip()) < 3:
                    cnt["too-short"] += 1
                    continue
                if SHIP.match(s):
                    cnt["SHIP"] += 1
                    ship.append((fn, g, i, s))
                elif ACRO.match(s):
                    cnt["ACRO"] += 1
                else:
                    cnt["ASCII?"] += 1
                    ascii_items.append((fn, g, i, s))
        print("=" * 78)
        print("%s : %d 个 .xscn，%d 条目（含标题 %d）" % (ef, cnt["files"], total, cnt["files"]))
        print("  已含汉字         : %d" % cjk_items)
        print("  政策保留(船名)   : %d" % cnt["SHIP"])
        print("  合规(缩写/型号)  : %d" % cnt["ACRO"])
        print("  ⚠ 疑似漏译候选   : %d  (占条目 %.2f%%)" % (cnt["ASCII?"], 100.0 * cnt["ASCII?"] / max(total, 1)))
        print("  其它             : 过短 %d / 非ASCII非CJK %d / 解析失败 %d"
              % (cnt["too-short"], cnt["non-ascii-non-cjk"], cnt["unparsed"]))
        per = Counter(f for f, g, i, s in ascii_items)
        print("  涉及文件数       : %d ; 最严重的 10 个：" % len(per))
        for f, n in per.most_common(10):
            print("     %-26s %3d" % (f, n))
        print("  样例（最多 25）:")
        for f, g, i, s in ascii_items[:25]:
            print("     %-24s g%-3d i%-5d %r" % (f, g, i, s))


main()
