# -*- coding: utf-8 -*-
"""把 OLGWW2 的 754 条疑似漏译按「组」拆开（-1=标题 / 0=地名 / 1+=番号），
并把「缩写风格番号」与「真·地名/标题」分开 —— 后者才是硬漏译。
"""
import os
import re
from collections import Counter

D = r"D:/OpenPG2/EFILE_OLGWW2/SCENARIO"
SHIP = re.compile(r"^(HMS|USS|IJN|RMS|SMS|HMCS|HMAS|ORP|ARA|KM|RN)\b")
ACRO = re.compile(r"^[A-Z0-9][A-Z0-9 /\-\.',&\+\(\)]*$")
# 「缩写风格」番号特征：含斜杠 + 大量单字母词，或含 (H)/(P) 之类
ABBRSTYLE = re.compile(r"(^|\s)[A-Z]{1,3}\.\s*/|/\s*[A-Z][a-z]*\s*[0-9]|\([A-Z]\)|^[0-9]+\.[A-Z]?\.?\(?[A-Za-z]?\)?/")
HASDIGIT = re.compile(r"[0-9]")


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


def cjk(raw):
    try:
        s = raw.decode("gbk")
    except Exception:
        return False
    return any("\u4e00" <= c <= "\u9fff" for c in s)


hard_title, hard_place, hard_unit, abbr_unit = [], [], [], []
for fn in sorted(f for f in os.listdir(D) if f.lower().endswith(".xscn")):
    x = parse(os.path.join(D, fn))
    if x is None:
        continue
    if not cjk(x["title"]):
        t = x["title"].decode("cp1252", "replace")
        if t.strip() and not SHIP.match(t) and not ACRO.match(t):
            hard_title.append((fn, t))
    for g, i, raw in x["items"]:
        if cjk(raw):
            continue
        try:
            s = raw.decode("ascii")
        except Exception:
            continue
        if len(s.strip()) < 3 or SHIP.match(s) or ACRO.match(s):
            continue
        if g == 0:
            hard_place.append((fn, i, s))
        else:
            if ABBRSTYLE.search(s) or (HASDIGIT.search(s) and "/" in s):
                abbr_unit.append((fn, i, s))
            else:
                hard_unit.append((fn, i, s))

print("=== 疑似漏译 754 条的结构分类 ===")
print("  ① 场景标题（组 -1）未译   : %d" % len(hard_title))
print("  ② 地图地名（组 0）未译     : %d" % len(hard_place))
print("  ③ 部队番号（组 1+）非缩写式 : %d" % len(hard_unit))
print("  ④ 部队番号（组 1+）缩写式   : %d  ← 政策/口径待定" % len(abbr_unit))
print("  合计 %d" % (len(hard_title) + len(hard_place) + len(hard_unit) + len(abbr_unit)))
print()
print("--- ① 未译标题全部 ---")
for f, t in hard_title:
    print("   %-22s %r" % (f, t))
print()
print("--- ② 未译地名（前 40）---")
for f, i, s in hard_place[:40]:
    print("   %-22s i%-5d %r" % (f, i, s))
print("   ... 共 %d 条，涉及 %d 个文件" % (len(hard_place), len(set(f for f, _, _ in hard_place))))
print()
print("--- ③ 非缩写式未译番号（前 20）---")
for f, i, s in hard_unit[:20]:
    print("   %-22s i%-5d %r" % (f, i, s))
print()
print("--- ④ 缩写式番号（前 12，口径待定）---")
for f, i, s in abbr_unit[:12]:
    print("   %-22s i%-5d %r" % (f, i, s))
