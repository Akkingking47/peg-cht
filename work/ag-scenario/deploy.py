# -*- coding: utf-8 -*-
"""AG 场景散文层（`SCENARIO\\*.txt`）中文侧部署器。

输入：`zh.tsv`（UTF-8，无 BOM），列 = `rep<TAB>text`
  · `rep`  = 该内容组的**代表文件名**（组内按字母序最小者，见 `rep-list.tsv`）
  · `text` = 译文；用字面 `\\n` 表示换行（TSV 单元格内不能有真换行，也不能有 TAB）

行为：
  1. 扫 `EFILE_AG\\SCENARIO\\*.txt`，按内容 md5 分组；
  2. 用 `rep` 找到组 ⇒ 把译文写到 `EFILE_AG\\TEXT-ZH\\SCENARIO\\<组内每个名字>`；
  3. 出稿 **GBK(936) / 无 BOM / CRLF**；结尾 CRLF 跟随原文；
  4. 不动原文；已存在的中文侧直接覆盖（幂等）。

用法：
  python deploy.py            # 干跑：报告覆盖数与剩余
  python deploy.py --apply    # 写入
"""
import glob
import hashlib
import io
import os
import re
import sys

SRC = r"D:/OpenPG2/EFILE_AG/SCENARIO"
DST = r"D:/OpenPG2/EFILE_AG/TEXT-ZH/SCENARIO"
TSV = r"D:/DSH/军事游戏汉化/work/ag-scenario/zh.tsv"
TSV_GLOB = r"D:/DSH/军事游戏汉化/work/ag-scenario/zh*.tsv"


def groups():
    g = {}
    for f in sorted(glob.glob(os.path.join(SRC, "*.txt"))):
        b = open(f, "rb").read()
        g.setdefault(hashlib.md5(b).hexdigest(), [b, []])[1].append(os.path.basename(f))
    for b, names in g.values():
        names.sort()
    return g


def load_zh():
    """读 work/ag-scenario/zh*.tsv（可分多批追加）"""
    m = {}
    import glob as _g
    for path in sorted(_g.glob(TSV_GLOB)):
        with io.open(path, encoding="utf-8-sig", newline="") as f:
            for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
                if i == 0 or not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) >= 2 and c[0]:
                    m[c[0]] = c[1]
    return m


def render(text, src_bytes):
    """字面 \\n -> CRLF、\\t -> 制表；GBK 编码。

    ⚠️ 换行结构由译文**自己写全**（含结尾换行），此处不再补 —— 否则会多一行。
    """
    body = text.replace("\\n", "\n").replace("\\t", "\t")
    return body.replace("\n", "\r\n").encode("gbk")


def lines_of(src_bytes):
    """换行个数（两侧同口径比较）"""
    return src_bytes.decode("cp1252", "replace").replace("\r\n", "\n").count("\n")


def main():
    apply_ = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    g = groups()
    zh = load_zh()
    reps = {names[0] for names in (v[1] for v in g.values())}
    todo = sorted(reps - set(zh))
    bad_key = sorted(set(zh) - reps)
    if bad_key:
        print("!! zh.tsv 里有 %d 个 rep 不在源分组中（拼写错？）:" % len(bad_key))
        for k in bad_key[:10]:
            print("   " + k)
    if not os.path.isdir(DST):
        if apply_:
            os.makedirs(DST)
        else:
            print("(将创建 %s)" % DST)
    nfiles = 0
    errs = []
    for h, (srcb, names) in g.items():
        rep = names[0]
        if rep not in zh:
            continue
        if only and not rep.startswith(only):
            continue
        try:
            out = render(zh[rep], srcb)
        except UnicodeEncodeError as e:
            errs.append((rep, "GBK 装不下: %s" % e))
            continue
        srcn = lines_of(srcb)
        dstn = out.decode("gbk").replace("\r\n", "\n").count("\n")
        if abs(srcn - dstn) > 0:
            errs.append((rep, "行数 %d -> %d" % (srcn, dstn)))
        for n in names:
            p = os.path.join(DST, n)
            if apply_:
                tmp = p + ".new"
                with open(tmp, "wb") as f:
                    f.write(out)
                back = open(tmp, "rb").read()
                if back != out:
                    errs.append((n, "回读不一致"))
                    os.remove(tmp)
                    continue
                os.replace(tmp, p)
            nfiles += 1
    print("译好 %d / %d 个唯一内容；本次覆盖 %d 个文件" % (
        len(zh) - len(bad_key), len(reps), nfiles))
    if errs:
        print("!! 异常 %d 条:" % len(errs))
        for r, why in errs[:15]:
            print("   %-22s %s" % (r, why))
    if todo:
        print("剩余未译 %d 个（前 25）:" % len(todo))
        for t in todo[:25]:
            print("   " + t)
    if not apply_:
        print("(dry-run)")


if __name__ == "__main__":
    main()
