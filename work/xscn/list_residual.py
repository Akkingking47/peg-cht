# -*- coding: utf-8 -*-
r"""清点某 efile `.xscn` 的「疑似漏译」残槽（判据与 `progress.py` 逐字一致）。

用法: python list_residual.py --efile ATOMIC [--title]

为什么需要它：
  `xscn.py export` 用 `decode()`（先试 GBK）判「是否已汉化」—— cp1252 高字节
  （`ä 0xE4` / `ó 0xF3` / `ñ 0xF1`）在 GBK 下解出**假汉字** ⇒ 这些残槽被 export 漏掉。
  本工具改用 `progress.py` 的 `zh_score(..., 逐 efile 假汉字黑名单) + kept_style()`
  双重判据，正是进度表里「疑似漏译」那一列的口径。

输出: work\<efile-lower>\residual.tsv      src(cp1252) freq gbk_read files master_hit
产出可直接作为 `xscn.py rawfix --map` 的键来源（键 = cp1252 读法 strip 后）。
"""
import collections
import glob
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
WORKROOT = os.path.dirname(os.path.dirname(HERE))          # D:\DSH\军事游戏汉化
GAME = r"D:\OpenPG2"

spec = importlib.util.spec_from_file_location(
    "prog", os.path.join(WORKROOT, "work", "audit", "progress.py"))
prog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prog)


def norm(arg):
    s = arg.strip().upper()
    return s if s.startswith("EFILE_") else "EFILE_" + s


def cp1252(b):
    try:
        return b.decode("cp1252")
    except UnicodeDecodeError:
        return None


def load_master():
    """master-glossary + master-resolve 合并（resolve 优先，与 apply_master.py 同序）。"""
    m = {}
    for p in (os.path.join(HERE, "master-glossary.tsv"),
              os.path.join(HERE, "master-resolve.tsv")):
        if not os.path.exists(p):
            continue
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
                if i == 0 or not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) >= 2 and c[0] and c[1]:
                    m[c[0]] = c[1]
    return m


def load_words():
    p = os.path.join(HERE, "master-words.tsv")
    d = {}
    if os.path.exists(p):
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
                if i == 0 or not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) >= 2 and c[0]:
                    d[c[0]] = c[1]
    return d


def main():
    if "--efile" not in sys.argv:
        print(__doc__)
        return 2
    EF = norm(sys.argv[sys.argv.index("--efile") + 1])
    with_title = "--title" in sys.argv
    d = next((x for x in os.listdir(GAME) if x.upper() == EF), None)
    if d is None:
        print("!! 目录不存在: EFILE_%s" % EF)
        return 2
    base = os.path.join(GAME, d)
    fake = prog.build_fake_han(d)
    master = load_master()
    words = load_words()

    cnt = collections.Counter()
    where = collections.defaultdict(list)
    gbk_read = {}
    nslots = nzh = nkeep = 0
    titles = []
    for f in sorted(glob.glob(os.path.join(base, "SCENARIO", "*.xscn"))):
        t, ent = prog.parse_xscn(open(f, "rb").read())
        if with_title and t:
            nslots += 1
            if prog.is_zh(t, fake):
                nzh += 1
            elif not prog.kept_style(t):
                s = cp1252(t)
                titles.append((os.path.basename(f), s, t.decode("gbk", "replace")))
        for e in ent:
            nslots += 1
            if not e.strip():
                continue
            if prog.is_zh(e, fake):
                nzh += 1
                continue
            if prog.kept_style(e):
                nkeep += 1
                continue
            s = cp1252(e)
            if s is None:
                s = "<cp1252 不可解: %s>" % e.hex()
            key = s.strip()
            cnt[key] += 1
            gbk_read.setdefault(key, e.decode("gbk", "replace"))
            if len(where[key]) < 3:
                where[key].append(os.path.basename(f))

    outdir = os.path.join(WORKROOT, "work", d.split("_", 1)[1].lower())
    os.makedirs(outdir, exist_ok=True)
    outp = os.path.join(outdir, "residual.tsv")
    hit = 0
    with io.open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tgbk_read\tfiles\tmaster_hit\n")
        for k, n in cnt.most_common():
            mh = master.get(k) or words.get(k) or ""
            if mh:
                hit += 1
            f.write("%s\t%d\t%s\t%s\t%s\n" % (
                k.replace("\t", "\\t"), n, gbk_read[k].replace("\t", "\\t"),
                ",".join(where[k]), mh))
    print("%s: 槽 %d  含汉字 %d  口径保留 %d  **疑似漏译 %d 条 / %d 唯一**"
          % (EF, nslots, nzh, nkeep, sum(cnt.values()), len(cnt)))
    print("   master/words 已能给译法的唯一串: %d" % hit)
    if titles:
        print("   ⚠️ 标题也需修 %d 个:" % len(titles))
        for fn, s, g in titles[:12]:
            print("      %-24s cp1252=%r  gbk=%r" % (fn, s, g))
    print("   --- 频次最高 30 ---")
    for k, n in cnt.most_common(30):
        print("   %5d  x%-3d  cp1252=%-42r gbk=%r" % (n, 0, k[:42], gbk_read[k][:30]))
    print("已写 %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
