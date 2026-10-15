# -*- coding: utf-8 -*-
r"""KAISER `.xscn` 唯一串导出（**槽位一律按 cp1252 读**）。

⚠️ 为什么不用 `xscn.py export`：它走 `decode()`（先试 GBK），而 KAISER 原文里
   `Hortabágy`/`Ksttrich`/`Württ.` 这类**重音字母**在 GBK 下会解出汉字 ⇒ 被判「已汉化」跳过。
   实测有 **2516 条**会被漏掉（`Hortab\xe1gy River`→`Hortab醙y River`）。
   本脚本改为：能按 cp1252 解出即视为原文槽；cp1252 解不了（GBK 中文字节）才跳过。

用法:
    python export_xscn_uniq.py            # 导出 work\kaiser\xscn-uniq.tsv
    python export_xscn_uniq.py --full     # 另导 work\kaiser\xscn-full.tsv（逐槽）
"""
import collections
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "xscn", os.path.join(r"D:\DSH\军事游戏汉化\work\xscn", "xscn.py"))
xscn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xscn)

EFILE = "EFILE_KAISER"
GAME = os.path.join(r"D:\OpenPG2", EFILE, "SCENARIO")


def slots(fn):
    """产出 (data, meta, slots)；gi=-1 为标题槽。"""
    p = os.path.join(GAME, fn)
    data, items, meta = xscn.parse(p)
    if items is None:
        return None
    return data, meta, xscn.slots_of(data, items, meta)


def src_of(raw):
    """cp1252 能解 ⇒ 原文；解不了（0x81/0x8D/0x8F/0x90/0x9D 等）⇒ 已是 GBK 中文槽，返回 None。"""
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return None


def main():
    full = "--full" in sys.argv
    files = sorted(f for f in os.listdir(GAME) if f.lower().endswith(".xscn"))
    cnt = collections.Counter()
    groups_of = collections.defaultdict(set)
    where = collections.defaultdict(list)
    nin = nzh = nctl = 0
    ctl = []
    tails = collections.Counter()
    for fn in files:
        r = slots(fn)
        if r is None:
            print("!! 解析失败 %s" % fn)
            continue
        data, meta, sl = r
        tails[meta[4] - meta[3]] += 1
        for gi, idx, off, L in sl:
            raw = xscn.raw_at(data, off, L)
            s = src_of(raw)
            if s is None:
                nzh += 1
                continue
            nin += 1
            key = s.strip()
            if not key:
                continue
            if any(ord(ch) < 0x20 for ch in key):
                # 原文件自带的畸形记录（内嵌 TAB/统计字段）⇒ 不译、原样保留
                nctl += 1
                if len(ctl) < 8:
                    ctl.append((fn, gi, idx, key[:70]))
                continue
            cnt[key] += 1
            groups_of[key].add(gi)
            if len(where[key]) < 3:
                where[key].append(fn)
    print("%s: .xscn %d 文件  原文槽 %d  已中文化槽 %d  含控制字符槽 %d  唯一串 %d  尾部残留 %s" % (
        EFILE, len(files), nin, nzh, nctl, len(cnt), tails.most_common(3)))
    for c in ctl:
        print("   非文本槽 %-20s g%d#%d %r" % c)
    out = os.path.join(HERE, "xscn-uniq.tsv")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("src\tfreq\tgroups\texample\n")
        for k, n in cnt.most_common():
            f.write("%s\t%d\t%s\t%s\n" % (k, n, ",".join(str(x) for x in sorted(groups_of[k])), where[k][0]))
    print("已写 %s" % out)
    if full:
        fo2 = os.path.join(HERE, "xscn-full.tsv")
        with io.open(fo2, "w", encoding="utf-8", newline="\n") as f:
            f.write("file\tgroup\tidx\tsrc\n")
            for fn in files:
                r = slots(fn)
                if r is None:
                    continue
                data, meta, sl = r
                for gi, idx, off, L in sl:
                    s = src_of(xscn.raw_at(data, off, L))
                    f.write("%s\t%d\t%d\t%s\n" % (fn, gi, idx, "" if s is None else s.rstrip()))
        print("已写 %s" % fo2)


if __name__ == "__main__":
    main()
