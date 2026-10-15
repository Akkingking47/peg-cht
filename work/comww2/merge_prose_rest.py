# -*- coding: utf-8 -*-
"""校验并合并子代理产出的 `_prose_rest_dst_partNN.txt`。

用法:
    python merge_prose_rest.py --check            # 只校验/统计
    python merge_prose_rest.py --apply             # 校验通过才写 prose-zh-blocks/rest-NN.tsv

校验（任一不过 => 不写盘、退出 1）:
  1. 行数 == 对应 `_prose_rest_partNN.txt` 行数
  2. `NNN|` 序号逐行一致
  3. 译文非空、无 TAB、无 CR/LF
  4. ` ⟦T⟧ ` 个数与原文一致（原文制表符分栏）
  5. 译文可 GBK 编码（不可则按折写表处理，并打印）
  6. GBK 往返（写盘前）
另外打印「真源覆盖缺口」= 715 条里仍无译文的条目数。
"""
import io
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
AUTH = os.path.join(HERE, "_prose_authority.txt")
ZH = os.path.join(HERE, "prose-zh.tsv")
OUTDIR = os.path.join(HERE, "prose-zh-blocks")
TABMARK = " \u27e6T\u27e7 "

FALLBACK = {"\u00af": "\u2500"}
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}
HAN = re.compile(r"[\u4e00-\u9fff]")


def gbk_safe(s):
    try:
        s.encode("gbk")
        return s, False
    except UnicodeEncodeError:
        pass
    t = s
    for a, b in FALLBACK.items():
        t = t.replace(a, b)
    t2 = t
    for a, b in FOLD.items():
        t2 = t2.replace(a, b)
    t2 = "".join(c for c in unicodedata.normalize("NFKD", t2) if not unicodedata.combining(c))
    try:
        t2.encode("gbk")
        return t2, True
    except UnicodeEncodeError:
        return t, True


def load_part(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    out = []
    for ln in raw.replace("\r\n", "\n").split("\n"):
        if not ln.strip():
            continue
        no, sep, txt = ln.partition("|")
        out.append((no.strip(), txt))
    return out


def read_first_col(path):
    s = set()
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c and c[0]:
                s.add(c[0])
    return s


def main():
    apply = "--apply" in sys.argv
    auth = [x for x in io.open(AUTH, encoding="utf-8", newline="").read()
            .replace("\r\n", "\n").split("\n") if x.strip()]
    byno = {}
    for i, s in enumerate(auth):
        byno[i + 1] = s

    parts = sorted(fn for fn in os.listdir(HERE)
                   if re.match(r"^_prose_rest_part\d+\.txt$", fn))
    errors = []
    all_rows = []
    for pf in parts:
        tag = re.search(r"part(\d+)", pf).group(1)
        df = "_prose_rest_dst_part%s.txt" % tag
        dp = os.path.join(HERE, df)
        src = load_part(os.path.join(HERE, pf))
        if not os.path.exists(dp):
            errors.append("缺译文文件 %s（%d 条待译）" % (df, len(src)))
            continue
        dst = load_part(dp)
        if len(src) != len(dst):
            errors.append("行数不符 %s: 待译 %d / 译文 %d" % (df, len(src), len(dst)))
            continue
        rows = []
        for (ns, ss), (nd, dd) in zip(src, dst):
            if ns != nd:
                errors.append("序号错位 %s: %s vs %s" % (df, ns, nd))
                break
            no = int(ns)
            if no not in byno:
                errors.append("序号越界 %s: %d" % (df, no))
                break
            s_true = byno[no]
            d = dd.replace(TABMARK, "\t").strip()
            if not d:
                errors.append("空译文 %s N=%d" % (df, no))
                continue
            if "\t" in d and TABMARK not in dd:
                errors.append("译文含真制表符 %s N=%d" % (df, no))
                continue
            if s_true.count("\t") != d.count("\t"):
                errors.append("制表符数不符 %s N=%d（原文 %d / 译文 %d）"
                              % (df, no, s_true.count("\t"), d.count("\t")))
                continue
            if d != s_true and not HAN.search(d):
                print("  ~ 无汉字（视为口径保留）N=%d %r -> %r" % (no, s_true[:50], d[:50]))
            g, folded = gbk_safe(d)
            if folded:
                print("  ~ 折写 N=%d: %r -> %r" % (no, d[:50], g[:50]))
            rows.append((s_true, g, no, tag))
        all_rows.extend(rows)

    print("可合并条目 %d" % len(all_rows))
    if errors:
        print("!! 校验失败 %d 项：" % len(errors))
        for e in errors[:40]:
            print("   - %s" % e)
        if not apply:
            return
        raise SystemExit(1)

    if not apply:
        return

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    per = {}
    for s, d, no, tag in all_rows:
        per.setdefault(tag, []).append((s, d))
    for tag, rows in sorted(per.items()):
        out = os.path.join(OUTDIR, "rest-%s.tsv" % tag)
        with io.open(out, "w", encoding="utf-8", newline="") as f:
            f.write("src\tdst\n")
            for s, d in rows:
                f.write("%s\t%s\n" % (s, d))
        with io.open(out, encoding="utf-8", newline="") as f:
            got = [x.rstrip("\n").split("\t") for x in f.read().split("\n")[1:] if x.strip()]
        if len(got) != len(rows) or any(g[0] != r[0] or g[1] != r[1] for g, r in zip(got, rows)):
            raise SystemExit("回读不一致: %s" % out)
        print("OK %s: %d 条" % (os.path.basename(out), len(rows)))

    done = read_first_col(ZH) | set(s for s, _, _, _ in all_rows)
    gap = [i for i, s in enumerate(auth, 1) if s not in done]
    print("真源覆盖：%d / %d 条已译，剩余 %d 条" % (len(auth) - len(gap), len(auth), len(gap)))
    if gap:
        print("  剩余序号: %s" % (",".join(str(x) for x in gap[:60]) + ("..." if len(gap) > 60 else "")))


if __name__ == "__main__":
    main()
