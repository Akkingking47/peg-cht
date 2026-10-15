# -*- coding: utf-8 -*-
r"""KAISER `USERSCEN` 层 `.ply` / `.txt` 汉化生成器（落 `TEXT-ZH\USERSCEN\`）。

填译链：`userscen-zh.tsv` → `standard-glossary.tsv` → 口径保留 → 否则报错（绝不静默留西语）。

⚠️ 与 `SCENARIO\*.txt` 同型：简报是「西语段 ＋ 其英译段」双段 ⇒ **两段都译**（用户 10-08 裁定）。
输出：GBK(936) / 无 BOM / **换行沿用原文** / 逐行对齐。原文侧只读。
用法: python gen_userscen_text.py [--dry]
"""
import io
import os
import re
import sys
import unicodedata
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_KAISER"
SRC = os.path.join(EFILE, "USERSCEN")
ZH = os.path.join(EFILE, "TEXT-ZH", "USERSCEN")
MAP = os.path.join(HERE, "userscen-text-all.tsv")
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
MISS = os.path.join(HERE, "userscen-text-miss.tsv")

FALLBACK = {"\u00af": "\u2500", "\u00a1": "!", "\u00bf": "?", "\u00ba": "o", "\u00aa": "a"}
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}
KEEP_PAT = [
    re.compile(r"^\[[^a-z\u00e0-\u00ff]*\]?$"),
    re.compile(r"^[A-Z]{1,4}$"),
    re.compile(r"^\u00af+$"),
    re.compile(r"^\d+$"),
    re.compile(r"^[\W_]+$"),
]


def rd2(p):
    d = {}
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                d.setdefault(c[0], c[1])
    return d


def detect_nl(raw, fn):
    n_crlf, n_lf = raw.count(b"\r\n"), raw.count(b"\n")
    n_bare_lf = n_lf - n_crlf
    if raw.count(b"\r") - n_crlf:
        raise SystemExit("原文含裸 CR: %s" % fn)
    if n_lf == 0:
        return "\r\n"
    if n_crlf == 0:
        return "\n"
    if n_bare_lf == 0:
        return "\r\n"
    raise SystemExit("原文混合换行: %s" % fn)


def gbk_safe(s):
    try:
        s.encode("gbk"); return s
    except UnicodeEncodeError:
        pass
    for a, b in FALLBACK.items():
        s = s.replace(a, b)
    try:
        s.encode("gbk"); return s
    except UnicodeEncodeError:
        pass
    t = s
    for a, b in FOLD.items():
        t = t.replace(a, b)
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    try:
        t.encode("gbk"); return t
    except UnicodeEncodeError as e:
        raise SystemExit("GBK 无法编码: %r (%s)" % (s, e))


def register_fixup(s):
    r"""敬称/引号统一（同 `gen_txt_zh.py`）。本层来源全是散文与字段行，豁免逻辑不需要。"""
    s = re.sub("\u4f60(?!\u4eec)", "\u60a8", s)
    return s.replace("\u201c", "\u300c").replace("\u201d", "\u300d")


def main():
    dry = "--dry" in sys.argv
    mp = rd2(MAP)
    gloss = rd2(GLOSS)
    keepset = {k for k, v in mp.items() if k.strip() == v.strip()}
    print("userscen-zh %d | 译名库 %d | 口径保留 %d" % (len(mp), len(gloss), len(keepset)))

    files = sorted(f for f in os.listdir(SRC)
                   if f.lower().endswith((".ply", ".txt")))
    print("USERSCEN .ply/.txt %d 个%s" % (len(files), "  [DRY RUN]" if dry else ""))

    miss = []
    used = collections.Counter()
    plan = []
    tot = zhz = 0
    for fn in files:
        raw = open(os.path.join(SRC, fn), "rb").read().replace(b"\x00", b"")
        if raw[:3] == b"\xef\xbb\xbf":
            raise SystemExit("原文含 BOM: %s" % fn)
        nl = detect_nl(raw, fn)
        lines = raw.decode("cp1252").split(nl)
        out = []
        for l in lines:
            if not l.strip():
                out.append(l); continue
            key = l.strip()
            if key in mp:
                d = mp[key]; used["userscen-zh"] += 1
            elif key in gloss:
                d = gloss[key]; used["译名库"] += 1
            elif key in keepset or any(rx.match(key) for rx in KEEP_PAT):
                d = key; used["口径保留"] += 1
            else:
                miss.append((fn, l)); out.append(l); continue
            # 首尾空白沿用**原文**（有的字段行尾带空格，如 `Diseño Mapa: Santiago Fuertes `）
            lead = l[:len(l) - len(l.lstrip())]
            trail = l[len(l.rstrip()):]
            out.append(lead + register_fixup(d.strip()) + trail)
        plan.append((fn, lines, out, nl))
        tot += sum(1 for x in lines if x.strip())
        zhz += sum(1 for c in "".join(out) if "\u4e00" <= c <= "\u9fff")

    print("填译来源：%s" % dict(used))
    if miss:
        cnt = collections.Counter(m[1] for m in miss)
        print("!! 未覆盖 %d 处（唯一 %d）——未落盘:" % (len(miss), len(cnt)))
        for l, n in cnt.most_common(30):
            print("   x%-3d %r" % (n, l[:100]))
        with io.open(MISS, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("src\tn\n")
            for l, n in cnt.most_common():
                fh.write("%s\t%d\n" % (l, n))
        raise SystemExit(1)

    # 第 2 遍：GBK 安全化 + 字节（在 miss 闸门之后，避免未译行先炸在 ¡ 之类字符上）
    built = []
    for fn, lines, out, nl in plan:
        out = [gbk_safe(l) for l in out]
        blob = nl.join(out).encode("gbk")
        if blob.decode("gbk").split(nl) != out:
            raise SystemExit("编解码往返不一致: %s" % fn)
        if nl == "\r\n" and blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit("输出换行异常: %s" % fn)
        built.append((fn, lines, out, blob, nl))
    plan = built

    if dry:
        print("DRY RUN：%d 文件 / 非空行 %d / 输出汉字 %d" % (len(plan), tot, zhz))
        return

    if not os.path.isdir(ZH):
        os.makedirs(ZH)
    for fn, lines, out, blob, nl in plan:
        tgt = os.path.join(ZH, fn)
        with open(tgt, "wb") as f:
            f.write(blob)
        back = open(tgt, "rb").read()
        assert back == blob, "回读不一致 %s" % fn
        assert back[:3] != b"\xef\xbb\xbf", "含 BOM %s" % fn
        assert back.decode("gbk").split(nl) == out, "回读行不一致 %s" % fn
    print("---")
    print("写出 %d 个文件 | 非空行 %d | 输出汉字 %d" % (len(plan), tot, zhz))
    print("OK 全部行已覆盖，原文件未改动")


if __name__ == "__main__":
    main()
