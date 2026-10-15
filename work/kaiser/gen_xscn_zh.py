# -*- coding: utf-8 -*-
r"""KAISER `.xscn` 汉化生成器：把 `xscn-uniq.tsv` 的每条唯一串译成中文（或其口径保留）。

填译优先级（逐级可追溯）：
  1. `xscn-manual.tsv`   整串人工（file 无，列：src \t dst）
  2. `work\xscn\_xscn_dict.tsv`  跨 efile `.xscn` 词典（7 个已交付 efile 实证）
  3. `glossary\standard-glossary.tsv`  标准译名库
  4. **结构化翻译**：序数/罗马数字 + 编制词（规则引擎）＋ 词级替换（`root-words.tsv` ∪ `xscn-words.tsv`）
  5. 保留原文（口径）

产出：
  `xscn-zh.tsv`   src \t dst \t how（审计）
  `xscn-map.tsv`  src \t dst（供 `xscn.py apply` / `rawfix` 用）
  `_xscn_resid.tsv`  仍「保留原文」且含拉丁字母者（真残留清单）

用法:
    python gen_xscn_zh.py --dry      # 只看统计
    python gen_xscn_zh.py            # 落盘 map + 审计
"""
import collections
import io
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
W = r"D:\DSH\军事游戏汉化"
HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z\u00c0-\u024f]")


def rd2(p, col=1):
    d = {}
    if not os.path.exists(p):
        return d
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        f.readline()
        for ln in f:
            c = ln.rstrip("\r\n").split("\t")
            if len(c) >= col + 1 and c[0].strip() and c[col].strip():
                d.setdefault(c[0].strip(), c[col])
    return d


def gbk_safe(s):
    out = []
    for ch in s:
        try:
            ch.encode("gbk")
            out.append(ch)
        except UnicodeEncodeError:
            a = "".join(c for c in unicodedata.normalize("NFKD", ch) if ord(c) < 128)
            out.append(a if a else "?")
    return "".join(out)


ZH_GAP = re.compile(r"(?<=[\u4e00-\u9fff0-9]) +(?=[\u4e00-\u9fff])|(?<=[\u4e00-\u9fff]) +(?=[0-9])")


def zh_tight(s):
    return ZH_GAP.sub("", s)


# ── 资产 ───────────────────────────────────────────────────────────────
UNIQ = []
with io.open(os.path.join(HERE, "xscn-uniq.tsv"), encoding="utf-8-sig", newline="") as f:
    f.readline()
    for ln in f:
        c = ln.rstrip("\r\n").split("\t")
        if len(c) >= 2 and c[0]:
            UNIQ.append((c[0], int(c[1])))

MANUAL = rd2(os.path.join(HERE, "xscn-manual.tsv"))
PLACE = rd2(os.path.join(HERE, "xscn-place.tsv"))       # 地名/专名层（子代理产出）
PNAME = rd2(os.path.join(HERE, "xscn-names.tsv"))       # 人名/舰名层（子代理产出）
UNIT = rd2(os.path.join(HERE, "xscn-unit.tsv"))         # 编制番号层（子代理产出）
DICT = rd2(os.path.join(W, "work", "xscn", "_xscn_dict.tsv"))
GLOSS = rd2(os.path.join(W, "glossary", "standard-glossary.tsv"))
WORDS = {}
# 优先级：`xscn-words-extra.tsv`（xscn 专用覆盖）> `xscn-words.tsv` > 根级 `root-words.tsv`
for src in (os.path.join(HERE, "root-words.tsv"),
            os.path.join(HERE, "xscn-words.tsv"),
            os.path.join(HERE, "xscn-words-extra.tsv"),
            os.path.join(HERE, "xscn-words-extra2.tsv"),
            os.path.join(HERE, "xscn-words-extra3.tsv"),
            os.path.join(HERE, "xscn-words-extra4.tsv"),
            os.path.join(HERE, "xscn-words-extra5.tsv"),
            os.path.join(HERE, "xscn-words-extra6.tsv"),
            os.path.join(HERE, "xscn-words-extra7.tsv")):
    for k, v in rd2(src).items():
        WORDS[k] = v
print("资产：manual %d · dict %d · glossary %d · words %d" % (len(MANUAL), len(DICT), len(GLOSS), len(WORDS)))

# ── 规则引擎 ───────────────────────────────────────────────────────────
# 裸单字母歧义（`A` `K` 可能是代号）⇒ 从词表剔除
for _w in ("A", "A.", "K", "K.", "R", "R."):
    WORDS.pop(_w, None)

FORM = ["Div", "Brig", "Reg", "Bat", "Corps", "Korps", "Army", "Armee", "Armée", "Armiya",
        "Brigade", "Division", "Regiment", "Battalion", "Rgt", "Bn", "Bde", "Dyw", "Pulk",
        "Polk", "Bryg", "IDiv", "RI", "IR", "CA", "AK", "RK", "RD", "MG", "FA", "RIR",
        "ResIR", "GdDiv", "RDiv", "RIDiv"]
FORM_ALT = "|".join(sorted(FORM, key=len, reverse=True))

ORD = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])(\d+)(?:st|nd|rd|th)(?![A-Za-z0-9\u00c0-\u024f])")
FRORD = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])(\d+)e(?![A-Za-z0-9\u00c0-\u024f])")
NUM_WORD = re.compile(
    r"(?<![A-Za-z0-9\u00c0-\u024f\u7b2c])(\d+)(?:st|nd|rd|th|e|er|ste)?\s*\.?\s*"
    r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)")
ROMAN_WORD = re.compile(
    r"(?<![A-Za-z0-9\u00c0-\u024f\u7b2c])([IVXLCDM]{1,7})(?:e|er|ste|me)?(?![A-Za-z\u00c0-\u024f])\s*\.?\s*"
    r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)")
# `Reg. Nr. 20` → `第20团`（语序反转）
REG_NR = re.compile(r"([A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*)\s*Nr\.?\s*(\d+)")
BRK_ARMY = re.compile(r"\[\s*(\d+)\s+A\.?\s*\]")


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
TOKEN = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*")
RV = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def r2i(s):
    s = s.upper()
    t = 0
    for i, ch in enumerate(s):
        t += RV[ch] * (1 if i + 1 >= len(s) or RV[ch] >= RV[s[i + 1]] else -1)
    return t


def _fzh(g):
    return WORDS.get(g) or WORDS.get(g + ".") or g


BRK_ARMY = re.compile(r"\[\s*(\d+)\s+A\.?\s*\]")


def structural(s):
    """规则引擎：序数/罗马数字 + 词表词 → 「第N<中文>」；其余交词级替换。返回 (结果, 是否有改动)。"""
    o = s
    o = BRK_ARMY.sub(lambda m: "[第%s集团军]" % m.group(1), o)
    o = REG_NR.sub(_regnr, o)
    o = ROMAN_WORD.sub(_romanform, o)
    o = NUM_WORD.sub(_numform, o)
    o = ORD.sub(lambda m: "第" + m.group(1), o)
    o = FRORD.sub(lambda m: "第" + m.group(1), o)
    # 逐 token 替换（未命中原样保留）
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


def translate(s):
    if s in MANUAL:
        return MANUAL[s], "人工"
    if s in PLACE:
        return PLACE[s], "地名"
    if s in PNAME:
        return PNAME[s], "人名"
    if s in UNIT:
        return UNIT[s], "编制"
    if s in DICT:
        return DICT[s], "dict"
    if s in GLOSS:
        return GLOSS[s], "glossary"
    r, ch = structural(s)
    if ch and HAN.search(r):
        return r, "结构"
    return s, "保留原文"


# ── 人工表键校验 ────────────────────────────────────────────────────────
_all = set(k for k, _ in UNIQ)
_un = [k for k in MANUAL if k not in _all]
if _un:
    print("!! 人工表未命中 %d 条：" % len(_un))
    for k in _un[:10]:
        print("   %r" % k)
    raise SystemExit(1)

rows = []
how_cnt = collections.Counter()
resid = []
for s, n in UNIQ:
    d, how = translate(s)
    how_cnt[how] += 1
    if d != s:
        rows.append((s, d, how))
    elif LAT.search(s):
        resid.append((s, n))

tot = len(UNIQ)
print("\n唯一串 %d" % tot)
for k, v in how_cnt.most_common():
    print("   %-10s %6d (%.1f%%)" % (k, v, 100.0 * v / tot))
print("   已有译文 %d (%.1f%%)" % (len(rows), 100.0 * len(rows) / tot))
print("   保留原文 %d（其中含拉丁字母 %d = 真残留）" % (how_cnt["保留原文"], len(resid)))

# 抽查样例
print("\n=== 结构翻译样例 40 ===")
k = 0
for s, d, how in rows:
    if how == "结构":
        print("   %-46s -> %s" % (s[:46], d[:46]))
        k += 1
        if k >= 40:
            break

with io.open(os.path.join(HERE, "xscn-zh.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("src\tdst\thow\n")
    for s, d, how in rows:
        f.write("%s\t%s\t%s\n" % (s, d, how))
if "--dry" in sys.argv:
    print("\n[DRY] 未写 map")
    raise SystemExit(0)
with io.open(os.path.join(HERE, "xscn-map.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("src\tdst\n")
    for s, d, _h in rows:
        f.write("%s\t%s\n" % (s, gbk_safe(d)))
with io.open(os.path.join(HERE, "_xscn_resid.tsv"), "w", encoding="utf-8", newline="\n") as f:
    f.write("src\tfreq\n")
    for s, n in sorted(resid, key=lambda x: -x[1]):
        f.write("%s\t%d\n" % (s, n))
print("\n已写 xscn-zh.tsv / xscn-map.tsv / _xscn_resid.tsv")
