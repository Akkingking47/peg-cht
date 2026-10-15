# -*- coding: utf-8 -*-
r"""PzLIGA USERSCEN 串区汉化器 —— 程序优先：master/主表精确 + 规则引擎 + 词级，剩残交 LLM。

复用 KAISER gen_xscn_zh.py 的规则引擎（structural）与词表资产（root-words/xscn-words/extra1-7），
叠加本 efile 的 root-words.tsv（WW2 德/英/意/法类型词）与 master-glossary、主 SCENARIO 的
pzliga-xscn-map.tsv（跨层权威）。

产出 work\efile_pzliga\：
  userscen-xscn-map.tsv   已定 src→dst（2 列，供 userscen_tool --strings-map 回写）
  userscen-xscn-resid.tsv 真残留 src→freq（含拉丁字母且未命中者，交 LLM）
"""
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
KAISER = r"D:\DSH\军事游戏汉化\work\kaiser"
XSCN = r"D:\DSH\军事游戏汉化\work\xscn"

MASTER = os.path.join(XSCN, "master-glossary.tsv")
WORDS_MASTER = os.path.join(XSCN, "master-words.tsv")
XSCNMAP = os.path.join(HERE, "pzliga-xscn-map.tsv")
UNIQ = r"D:\DSH\军事游戏汉化\work\userscen\pzliga-userscen-uniq.tsv"

HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")
TOKEN = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*")
NUM = re.compile(r"^[\d\.\-\/\s\[\],\(\)\'\"\+]+$")

ZH_GAP = re.compile(r"(?<=[\u4e00-\u9fff]) +(?=[\u4e00-\u9fff])")


def zh_tight(s):
    return ZH_GAP.sub("", s)


def rd2(p, col=1):
    d = {}
    if not os.path.exists(p):
        return d
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                d[c[0]] = c[col - 1] if col > 1 else c[1]
    return d


# ── 词表（KAISER 资产 + 本 efile root-words）───────────────────────────
WORDS = {}
for p in [os.path.join(KAISER, "root-words.tsv"),
          os.path.join(KAISER, "xscn-words.tsv")] + \
         [os.path.join(KAISER, "xscn-words-extra%d.tsv" % i) for i in range(1, 8)] + \
         [os.path.join(HERE, "root-words.tsv"),
          WORDS_MASTER,
          os.path.join(HERE, "userscen-words.tsv")]:
    for k, v in rd2(p).items():
        WORDS[k] = v
print("词表合计 %d 条" % len(WORDS))

# ⭐ 口径覆盖（PzLIGA WW2 语境；KAISER 词表里的多语歧义须钉死）：
#   Army/Armiya/Armata = 集团军（不是军/火炮）；Corps = 军（不是军团）
COVERRIDE = {
    "Army": "集团军", "Armiya": "集团军", "Armata": "集团军", "Armada": "舰队",
    "Corps": "军", "Korps": "军",
}
for _k, _v in COVERRIDE.items():
    WORDS[_k] = _v

# ── 规则引擎（沿用 KAISER structural）───────────────────────────────────
FORM = ["Div", "Brig", "Reg", "Bat", "Corps", "Korps", "Army", "Armee", "Armée", "Armiya",
        "Brigade", "Division", "Regiment", "Battalion", "Rgt", "Bn", "Bde", "Dyw", "Pulk",
        "Polk", "Bryg", "IDiv", "RI", "IR", "CA", "AK", "RK", "RD", "MG", "FA", "RIR",
        "ResIR", "GdDiv", "RDiv", "RIDiv", "PzDiv", "InfDiv", "MotDiv", "LtDiv", "MtnDiv"]
FORM_ALT = "|".join(sorted(FORM, key=len, reverse=True))

ORD = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])(\d+)(?:st|nd|rd|th)(?![A-Za-z0-9\u00c0-\u024f])")
FRORD = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])(\d+)e(?![A-Za-z0-9\u00c0-\u024f])")
NUM_WORD = re.compile(
    r"(?<![A-Za-z0-9\u00c0-\u024f\u7b2c])(\d+)(?:st|nd|rd|th|e|er|ste)?\s*\.?\s*"
    r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)")
ROMAN_WORD = re.compile(
    r"(?<![A-Za-z0-9\u00c0-\u024f\u7b2c])([IVXLCDM]{1,7})(?:e|er|ste|me)?(?![A-Za-z\u00c0-\u024f])\s*\.?\s*"
    r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)")
REG_NR = re.compile(r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)\s*Nr\.?\s*(\d+)")
BRK_ARMY = re.compile(r"\[\s*(\d+)\s*A\.?\s*\]")
RV = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def r2i(s):
    s = s.upper()
    t = 0
    for i, ch in enumerate(s):
        t += RV[ch] * (1 if i + 1 >= len(s) or RV[ch] >= RV[s[i + 1]] else -1)
    return t


def _wzh(w):
    return WORDS.get(w) or WORDS.get(w.rstrip("."))


def _numform(m):
    zh = _wzh(m.group(2))
    return m.group(0) if zh is None else "第%s%s" % (m.group(1), zh)


def _romanform(m):
    zh = _wzh(m.group(2))
    return m.group(0) if zh is None else "第%d%s" % (r2i(m.group(1)), zh)


def _regnr(m):
    base, num = m.group(1), m.group(2)
    zh = _wzh(base)
    if zh is None or base.rstrip(".").lower() not in ("reg", "bat", "div", "brig", "rgt", "bn", "ir", "ri"):
        return m.group(0)
    return "第%s%s" % (num, zh)


def structural(s):
    o = s
    o = BRK_ARMY.sub(lambda m: "[第%s集团军]" % m.group(1), o)
    o = REG_NR.sub(_regnr, o)
    o = ROMAN_WORD.sub(_romanform, o)
    o = NUM_WORD.sub(_numform, o)
    o = ORD.sub(lambda m: "第" + m.group(1), o)
    o = FRORD.sub(lambda m: "第" + m.group(1), o)
    last = 0
    out = []
    for m in TOKEN.finditer(o):
        w = m.group(0)
        zh = WORDS.get(w)
        if zh is None and w.endswith("."):
            zh = WORDS.get(w[:-1])
        if zh is None:
            continue
        out.append(o[last:m.start()])
        out.append(zh)
        last = m.end()
    if not out:
        return o, o != s
    out.append(o[last:])
    return zh_tight("".join(out)), True


def main():
    master = rd2(MASTER)
    master.update(rd2(XSCNMAP))     # 跨层权威优先
    uniq = {}
    with io.open(UNIQ, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2:
                uniq[c[0]] = int(c[1])

    mapped = {}
    resid = []
    how = collections.Counter()
    for s in uniq:
        if s in master:
            mapped[s] = master[s]; how["精确"] += 1; continue
        if NUM.match(s) or not TOKEN.search(s):
            how["纯代号"] += 1; continue
        r, ch = structural(s)
        if ch and HAN.search(r):
            mapped[s] = r; how["结构"] += 1; continue
        resid.append((s, uniq[s])); how["残留"] += 1

    resid.sort(key=lambda x: -x[1])
    tot = len(uniq)
    print("唯一串 %d" % tot)
    for k, v in how.most_common():
        print("   %-6s %6d (%.1f%%)" % (k, v, 100.0 * v / tot))
    with io.open(os.path.join(HERE, "userscen-xscn-map.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(mapped):
            f.write("%s\t%s\n" % (s, mapped[s]))
    with io.open(os.path.join(HERE, "userscen-xscn-resid.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tn\n")
        for s, n in resid:
            f.write("%s\t%d\n" % (s, n))
    print("已写 userscen-xscn-map.tsv（%d）/ userscen-xscn-resid.tsv（%d）" % (len(mapped), len(resid)))
    # 结构翻译样例
    print("=== 结构样例 25 ===")
    k = 0
    for s in sorted(mapped):
        if not LAT.search(s) or NUM.match(s):
            continue
        if mapped[s] and HAN.search(mapped[s]) and not any(t in s for t in ("[", "]", "(", ")")):
            print("   %-40s -> %s" % (s[:40], mapped[s][:40]))
            k += 1
            if k >= 25:
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
