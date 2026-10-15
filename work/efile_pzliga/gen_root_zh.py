# -*- coding: utf-8 -*-
"""PzLIGA 根级三件套汉化生成器（equip / names / nations / strings_efile）。

填译优先级（全部**证据驱动**，逐级可追溯）：
  1. donor 精确译文  —— 同名文件在已交付 efile 里「原文行 → 译文行」（行对齐，MECHANICS §16）
  2. donor 恒等保留  —— 同名原文行在 donor 的 TEXT-ZH 里**与原文完全相同**
                        ⇒ 既有口径就是「保留原文」（炮口径/型号/舰名）
  3. 词级映射        —— 从 donor 对齐对里自动学出的「拉丁词 → 中文」表 + 人工补表
                        （保留数字前缀：`43 Strelkovy` → `43 步兵`，同 BASEKORP 先例）
  4. 保留原文        —— 仍无依据者**保持原文**（口径：装备型号/舰名/编号保留）

输出：`<efile>\\TEXT-ZH\\<同名>`，GBK(936) / 无 BOM / CRLF / **逐行对齐**。
原文侧只读。
"""
import io
import os
import re
import sys
import json
import collections

sys.stdout.reconfigure(encoding="utf-8")

GAME = r"D:\OpenPG2"
TGT = "EFILE_PzLIGA"
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["equip.txt", "names.txt", "nations.txt"]
LAT = re.compile(r"[A-Za-z]")
import unicodedata


def gbk_safe(s):
    """GBK 装不下的字符 → NFKD ASCII 折写（ñ→n / é→e / ü→u）。汉字不动。"""
    out = []
    for ch in s:
        try:
            ch.encode("gbk")
            out.append(ch)
        except UnicodeEncodeError:
            a = "".join(c for c in unicodedata.normalize("NFKD", ch) if ord(c) < 128)
            out.append(a if a else "?")
    return "".join(out)
HAN = re.compile(r"[\u4e00-\u9fff]")
NORM = lambda x: re.sub(r"\s+", " ", x.strip()).lower()


ZH_GAP = re.compile(r"(?<=[\u4e00-\u9fff]) +(?=[\u4e00-\u9fff])")


def zh_tight(s):
    """收紧「汉字 空格 汉字」——词级替换留下的复合词空隙（`轻型 巡洋舰`→`轻型巡洋舰`）。"""
    return ZH_GAP.sub("", s)


def sp_cp(b):
    return b.decode("cp1252", "replace").replace("\r\n", "\n").split("\n")


def sp_zh(b):
    try:
        return b.decode("gbk").replace("\r\n", "\n").split("\n")
    except UnicodeDecodeError:
        return b.decode("gbk", "replace").replace("\r\n", "\n").split("\n")


# ---------------------------------------------------------------- donor 收集
exact = {fn: {} for fn in FILES}     # src -> dst（有译文）
kept = {fn: set() for fn in FILES}   # src（恒等保留）
pairs = {fn: [] for fn in FILES}     # (src, dst) 供学词
donor_files = collections.Counter()

for d in sorted(os.listdir(GAME)):
    if not d.upper().startswith("EFILE_") or d == TGT:
        continue
    z = os.path.join(GAME, d, "TEXT-ZH")
    if not os.path.isdir(z):
        continue
    fake = None
    for fn in FILES:
        a, b = os.path.join(GAME, d, fn), os.path.join(z, fn)
        if not (os.path.exists(a) and os.path.exists(b)):
            continue
        s, t = sp_cp(open(a, "rb").read()), sp_zh(open(b, "rb").read())
        if len(s) != len(t):
            print("  !! 行数不等，跳过 %s/%s (%d vs %d)" % (d, fn, len(s), len(t)))
            continue
        donor_files[fn] += 1
        for x, y in zip(s, t):
            if not x.strip():
                continue
            if x == y:
                kept[fn].add(x)
            elif y.strip():
                exact[fn].setdefault(x, y)
            pairs[fn].append((x, y))

NEXACT = {fn: {} for fn in FILES}
NKEPT = {fn: set() for fn in FILES}
for fn in FILES:
    for x, y in pairs[fn]:
        if not x.strip():
            continue
        n = NORM(x)
        if x == y:
            NKEPT[fn].add(n)
        elif y.strip():
            NEXACT[fn].setdefault(n, y)

print("donor 覆盖：" + " · ".join("%s %d 个" % (fn, donor_files[fn]) for fn in FILES))

# ---------------------------------------------------------------- 学词表
def learn_words(pairs):
    """从 donor 对齐对里学「拉丁词 → 中文」映射。

    ⚠️ **只收「军事编制/装备类别」型**（中文含 兵/军/师/团/旅/营/连/队/炮/卫队/预备/迫击…）。
    否则会把专名一并学进来（donor 里 `Alaska`→阿拉斯加、`Elephant`→战象），
    用在 COMWW2 的**舰名/机型行**上就是误译 —— 那些行按口径必须保留原文。
    """
    MIL = ("兵", "军", "师", "团", "旅", "营", "连", "队", "炮", "卫", "预备", "迫击", "登陆")

    def ok(zh):
        return HAN.search(zh) and not LAT.search(zh) and any(k in zh for k in MIL)

    m = collections.Counter()
    for x, y in pairs:
        xs, ys = x.strip(), y.strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z\-'.]*", xs) and ok(ys):
            m[(xs, ys)] += 1
        mx = re.fullmatch(r"(\d+\s+)([A-Za-z][A-Za-z\-'.]*)", xs)
        my = re.fullmatch(r"(\d+\s+)(.+)", ys)
        if mx and my and mx.group(1) == my.group(1) and ok(my.group(2)):
            m[(mx.group(2), my.group(2))] += 1
    return {k: v for k, v in m.items() if v >= 1}


WORDS = {}
for fn in FILES:
    for (a, b), n in learn_words(pairs[fn]).items():
        WORDS.setdefault(a, collections.Counter())[b] += n
WORDS = {k: c.most_common(1)[0][0] for k, c in WORDS.items()}
print("学得词表 %d 条（例：%s）" % (len(WORDS), ", ".join("%s→%s" % kv for kv in list(WORDS.items())[:6])))

MANUAL_WORDS = {
    "Sapper": "工兵", "Sappers": "工兵", "Pioneeri": "工兵", "Pioneer": "工兵",
    "Piechota": "步兵", "Strelkovy": "步兵", "Infanterie": "步兵", "Infantry": "步兵",
    "Ratsuvaki": "骑兵", "Cavalerie": "骑兵", "Sissi": "游击队",
    "Kriegsmarine": "海军", "Gvardia": "近卫军", "Garda": "近卫军",
    "Scottish": "苏格兰", "FallschirmJaeger": "伞兵", "Fallschirmjager": "伞兵",
    "Mortar": "迫击炮", "Battery": "炮台", "Tienraivaaja": "筑路兵",
    "Entr.": "预备", "Honved": "国防军", "Hohei": "步兵", "Eihei": "卫兵",
    "Banzai": "万岁", "Danuvia": "达努维亚",
    "GebH": "山地榴弹炮", "Rail Mortar": "铁道迫击炮",
}
for k, v in MANUAL_WORDS.items():
    WORDS.setdefault(k, v)

# ⚠️ 剔除与 donor 主流口径相悖的学得词：
#    `X Class` 在 OLGWW2/AO 里主流是**保留原文**（`Akagi Class`/`Bismarck Class`），
#    少数译成 `Barracuda Class`→梭鱼级 ⇒ 学得 `Class`→级 会造成少口径不一致。
for _w in ("Class",):
    WORDS.pop(_w, None)

# ⭐ PzLIGA：载入德语 WW2 词表（德/俄/波/捷/匈/土/芬/…）
_wp = os.path.join(HERE, "root-words.tsv")
if os.path.exists(_wp):
    with io.open(_wp, encoding="utf-8-sig") as _f:
        _f.readline()
        for _ln in _f:
            _ln = _ln.rstrip("\r\n")
            if not _ln:
                continue
            _c = _ln.split("\t")
            if len(_c) >= 2 and _c[0].strip() and _c[1].strip():
                WORDS[_c[0].strip()] = _c[1].strip()
    print("KAISER 词表合计 %d 条" % len(WORDS))

def load_manual():
    """外部人工译表 root-manual.tsv（file \t src \t dst）。"""
    m = {}
    fp = os.path.join(HERE, "root-manual.tsv")
    if not os.path.exists(fp):
        return m
    with io.open(fp, encoding="utf-8-sig") as f:
        f.readline()
        for ln in f:
            ln = ln.rstrip("\r\n")
            if not ln:
                continue
            c = ln.split("\t")
            if len(c) >= 3 and c[1]:
                m.setdefault(c[0], {})[c[1].strip()] = c[2]
    return m


MANUAL_FILE = {}

MANUAL = {}

MANUAL_FILE = load_manual()
for _f, _d in MANUAL_FILE.items():
    MANUAL.setdefault(_f, {}).update({k: v for k, v in _d.items() if k not in MANUAL.get(_f, {})})

# ---------------------------------------------------------------- 逐文件翻译
MARK = re.compile(
    r"(?i)\b(obr|wz|vz|zr|md|mle|mod|mk|typ|cal|nom)\.?\s*[\dIA]"
    r"|\bM\.?\s*\d|\by\.\s*\d{2,4}|\bL/\d|\bC/\d|\b\d{2}/\d{2}\b")

PART = re.compile(
    r"(?<![A-Za-z\u00c0-\u024f])(de|da|di|du|des|del|\u00e0|au|zu|zum|zur|w|na|van|der|von|of|the|et|a)"
    r"(?![A-Za-z\u00c0-\u024f])")


TOKEN = re.compile(r"[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f\-'.]*")


def translate_line(fn, s):
    if not s.strip():
        return s, "空行"
    if fn in MANUAL and s.strip() in MANUAL[fn]:
        _lead = s[:len(s) - len(s.lstrip())]
        _trail = s[len(s.rstrip()):]
        return _lead + MANUAL[fn][s.strip()] + _trail, "人工"
    if not LAT.search(s):
        return s, "纯数字/符号"
    if s in exact[fn]:
        return exact[fn][s], "donor译文"
    # ⚠️「donor 恒等保留」只对 **装备/结构型** 文件算证据：
    #    equip.txt 里 `13 Pdr` / `2 FlaK38` 保留原文是口径；
    #    但 names.txt 是**人名表**，口径是「音译 / 通行译名」，donor 里的恒等行
    #    更可能是 donor 的**漏译**，不能当口径继承（否则缺口被静默传染）。
    if fn in ("equip.txt", "strings_efile.txt") and s in kept[fn]:
        return s, "donor保留"
    # 归一化后来一击（专治大小写/空白差异，09-29 实测多捞回 15 条）
    n = NORM(s)
    if n in NEXACT[fn]:
        return NEXACT[fn][n], "donor译文·归一"
    if fn in ("equip.txt", "strings_efile.txt") and n in NKEPT[fn]:
        return s, "donor保留·归一"
    # 词级替换：按 token 查表（O(1)/token），未命中的 token 原样保留
    toks = [m for m in TOKEN.finditer(s)]
    if not toks:
        return s, "保留原文"
    out = []
    last = 0
    changed = False
    for m in toks:
        w = m.group(0)
        zh = WORDS.get(w)
        if zh is None and w.endswith("'s"):
            zh = WORDS.get(w[:-2])
        if zh is None:
            continue
        out.append(s[last:m.start()])
        out.append(zh)
        last = m.end()
        changed = True
    if not changed:
        return s, "保留原文"
    if fn == "equip.txt":
        _res = "".join(out) + s[last:]
        if MARK.search(s):
            return s, "型号保留"
        if PART.search(s) and HAN.search(_res) and LAT.search(_res):
            return s, "虚词回退"
    out.append(s[last:])
    return "".join(out), "词级"


# 人工表键命中校验（防手抄错位/多余条目）
_src_all = {fn: set() for fn in FILES}
for fn in FILES:
    for l in sp_cp(open(os.path.join(GAME, TGT, fn), "rb").read()):
        _src_all[fn].add(l.strip())
_unused = [(f, k) for f in MANUAL for k in MANUAL[f] if k not in _src_all.get(f, set())]
if _unused:
    print("!! 人工表未命中 %d 条（应删除或修正）:" % len(_unused))
    for f, k in _unused:
        print("   %-18s %r" % (f, k))
    raise SystemExit(1)
print("人工表键全部命中原文 ✓")

summary = collections.Counter()
plans = {}
for fn in FILES:
    src_path = os.path.join(GAME, TGT, fn)
    raw = open(src_path, "rb").read()
    lines = sp_cp(raw)
    if raw.count(b"\n") != raw.count(b"\r\n"):
        raise SystemExit("原文含裸 LF: " + fn)
    out = []
    hows = []
    for s in lines:
        d, how = translate_line(fn, s)
        d = gbk_safe(d)
        d = zh_tight(d)
        summary[(fn, how)] += 1
        hows.append(how)
        if d != s and "\t" in d:
            raise SystemExit("改动行含制表符 %s: %r" % (fn, d))
        out.append(d)
    for d in out:
        if d.strip():
            try:
                d.encode("gbk")
            except UnicodeEncodeError as e:
                raise SystemExit("GBK 无法编码 %s: %r (%s)" % (fn, d, e))
    plans[fn] = (raw, lines, out, hows)

print()
for fn in FILES:
    _, lines, out, _h = plans[fn]
    nb = sum(1 for l in lines if l.strip())
    print("%-18s 行 %-5d 非空 %-5d | %s" % (
        fn, len(lines), nb,
        " · ".join("%s %d" % (h, n) for (f, h), n in sorted(summary.items()) if f == fn)))

if "--dry" in sys.argv:
    print("\n[DRY] 未落盘")
else:
    only = None
    for a in sys.argv:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
    todo_files = [f for f in FILES if only is None or f in only]
    z = os.path.join(GAME, TGT, "TEXT-ZH")
    os.makedirs(z, exist_ok=True)
    for fn in todo_files:
        _, lines, out, _h = plans[fn]
        blob = "\r\n".join(out).encode("gbk")
        assert blob.count(b"\n") == blob.count(b"\r\n")
        p = os.path.join(z, fn)
        with open(p, "wb") as f:
            f.write(blob)
        back = open(p, "rb").read()
        assert back == blob and back[:3] != b"\xef\xbb\xbf"
        assert back.decode("gbk").split("\r\n") == out
    print("\n已写 %d 个文件到 %s（%s）" % (len(todo_files), z, ", ".join(todo_files)))

# 落盘待审：逐行 diff（原→译）
with io.open(os.path.join(HERE, "_root_diff.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    for fn in FILES:
        _, lines, out, _h = plans[fn]
        for i, (a, b) in enumerate(zip(lines, out), 1):
            if a != b:
                fh.write("%s\t%d\t%s\t%s\n" % (fn, i, a, b))
print("差异明细 -> _root_diff.tsv")

# 待办清单：判为「保留原文」但含拉丁字母者（真残留）
for fn in FILES:
    _, lines, out, hows = plans[fn]
    pend = sorted({a for a, h in zip(lines, hows) if h == "保留原文" and LAT.search(a)})
    with io.open(os.path.join(HERE, "_pending_" + fn.replace(".txt", "") + ".txt"),
                 "w", encoding="utf-8", newline="\n") as fh:
        for x in pend:
            fh.write(x + "\n")
    print("待办 %-18s %d 条 -> _pending_%s.txt" % (fn, len(pend), fn.replace(".txt", "")))

