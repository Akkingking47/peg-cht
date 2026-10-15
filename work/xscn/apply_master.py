# -*- coding: utf-8 -*-
r"""程序优先匹配器 —— 新 efile 开工，先用 master 词库自动定译，只剩 miss 才交 LLM。

用法: python apply_master.py --efile PzLIGA [--with-words]

流程（对应「程序做翻译、LLM 只校验」）：
  1. 导出目标 efile 的 .xscn 唯一串（按 cp1252 读，避开假汉字陷阱）
  2. master-glossary.tsv 精确匹配（跨 efile 全层）
  3. master-words.tsv 词级组合（--with-words 时；token 全命中才整串替换）
  4. 输出：
       prematch-map.tsv    程序已定 src→dst（无需 LLM）
       prematch-miss.tsv   需 LLM 的 src（按频次降序）

产出文件落在 work\<efile-lower>\ 下。用法: python apply_master.py --efile PzLIGA
"""
import collections
import importlib.util
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "master-glossary.tsv")
WORDS = os.path.join(HERE, "master-words.tsv")
RESOLVE = os.path.join(HERE, "master-resolve.tsv")

spec = importlib.util.spec_from_file_location("xscn", os.path.join(HERE, "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(xscn)
except SystemExit:
    pass

TOK = re.compile(r"(?<![A-Za-z0-9\u00c0-\u024f])[A-Za-z\u00c0-\u024f][A-Za-z\u00c0-\u024f'\.\-]*")
NUM = re.compile(r"^[\d\.\-\/\s\[\],\(\)\'\"]+$")


def word_ok(s, toks):
    """词级拼接是否可用 —— ⚠️ 2026-10-09 修：旧版直接 `"".join(words[t])` 会**吞掉番号数字与分隔符**，
    把 `33 Army` 拼成「军」、`141 Mrt Rgt/8 Gds Army` 拼成「迫击炮团近卫军」（master 本身没这些条目，
    全是词级路径造出来的伪命中，Clu 一跑就暴露 24 条）。
    新判据（两条都要满足）：
      ① src **不含数字** —— 含番号的一律交 LLM（拼接无法补「第N」）；
      ② 拿掉全部命中 token 后**只剩分隔符/空白** —— 否则说明有未覆盖成分被丢掉。
    """
    if re.search(r"\d", s):
        return False
    rest = s
    for t in toks:
        rest = rest.replace(t, "", 1)
    return not rest.strip(" \t-/.,'()[]:")


def rd(path):
    d = {}
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1]:
                d.setdefault(c[0], c[1])
    return d


def main():
    a = sys.argv[sys.argv.index("--efile") + 1] if "--efile" in sys.argv else None
    if not a:
        raise SystemExit("用法: python apply_master.py --efile PzLIGA [--with-words]")
    ef = a.strip().upper()
    if not ef.startswith("EFILE_"):
        ef = "EFILE_" + ef
    with_words = "--with-words" in sys.argv
    outdir = os.path.join(os.path.dirname(os.path.dirname(HERE)), "work", ef.lower())
    os.makedirs(outdir, exist_ok=True)

    master = rd(MASTER)
    words = rd(WORDS) if with_words else {}
    # 冲突裁定表优先（resolve_master.py 产出，覆盖 master 里的多译法冲突）
    if os.path.exists(RESOLVE):
        resolve = rd(RESOLVE)
        master.update(resolve)

    D = os.path.join(ROOT, ef, "SCENARIO")
    uniq = collections.Counter()
    for f in sorted(os.listdir(D)):
        if not f.endswith(".xscn"):
            continue
        data, its, meta = xscn.parse(os.path.join(D, f))
        for gi, i, off, L in (its or []):
            s = xscn.raw_at(data, off, L).decode("cp1252", "replace").strip()
            if s:
                uniq[s] += 1

    mapped = {}
    miss = []
    wmiss = []
    for s in uniq:
        if s in master:
            mapped[s] = master[s]
        else:
            miss.append(s)
    if with_words:
        rest = miss
        miss = []
        for s in rest:
            toks = TOK.findall(s)
            if toks and all(t in words for t in toks) and word_ok(s, toks):
                mapped[s] = "".join(words[t] for t in toks)
                wmiss.append(s)
            else:
                miss.append(s)

    # 纯代号（编号）也算「程序已定＝保留原文」，不进 miss
    code = [s for s in miss if NUM.match(s) or not TOK.search(s)]
    miss = [s for s in miss if s not in code]
    miss.sort(key=lambda s: -uniq[s])

    with io.open(os.path.join(outdir, "prematch-map.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(mapped):
            f.write("%s\t%s\n" % (s, mapped[s]))
    with io.open(os.path.join(outdir, "prematch-miss.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tn\n")
        for s in miss:
            f.write("%s\t%d\n" % (s, uniq[s]))

    n = len(uniq)
    print("%s .xscn 唯一串 %d / 槽 %d" % (ef, n, sum(uniq.values())))
    print("master 精确命中  %5d (%.1f%%)" % (len(mapped) - len(wmiss), 100.0 * (len(mapped) - len(wmiss)) / n))
    if with_words:
        print("词级组合命中    %5d (%.1f%%)" % (len(wmiss), 100.0 * len(wmiss) / n))
    print("纯代号（保留）  %5d (%.1f%%)" % (len(code), 100.0 * len(code) / n))
    print("=> 程序覆盖 %.1f%%；需 LLM 的仅 %d 条 (%.1f%%)" %
          (100.0 * (len(mapped) + len(code)) / n, len(miss), 100.0 * len(miss) / n))
    print("已写 %s\\prematch-map.tsv / prematch-miss.tsv" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
