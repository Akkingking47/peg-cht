# -*- coding: utf-8 -*-
"""COMWW2 prose 层「顺序配对」合并器 —— 杜绝手抄键错位。

用法:
    python merge_prose_block.py --block b01 --from 1 --to 45
    python merge_prose_block.py --check          # 校验现有 prose-zh.tsv 的键是否都在待译集内

机制:
    src  = `_prose_narrative_todo.txt` 第 N 行（**按行号取**，不手抄）
    dst  = `prose-dst-<block>.txt` 第 M 行（一一对应）
    ⇒ 行数必须严格相等，否则报错退出（不写盘）。

产出:
    `prose-zh-blocks/<block>.tsv`（src\tdst，UTF-8 **无 BOM**）
    （各块事后由 `build_prose_zh.py` 合成最终 `prose-zh.tsv`）

守卫:
    - dst 不得为空、不得含制表符/换行
    - dst 必须含汉字，或 src==dst（口径保留）
    - dst 必须可 GBK 编码（不可编码字符按 `gen_prose_zh.py` 同款折写表处理）
    - src 必须在待译集内（防越界配对）
"""
import io
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
TODO = os.path.join(HERE, "_prose_narrative_todo.txt")
# ⛔ 权威键集：**固化**在 `_prose_authority.txt`（715 条，唯一）。
#    ⚠️ 不可用 `prose-miss.tsv` 当基准——它每次干跑都会被**重写为剩余项**（会随进度缩水）。
AUTH = os.path.join(HERE, "_prose_authority.txt")
OUTDIR = os.path.join(HERE, "prose-zh-blocks")

# ⛔ 硬坑（09-29 踩过）：`_prose_narrative_todo.txt` 是**带行号前缀的清单**
#    （形如 `  1|Thanx for playing...`），不是裸原文行。直接拿它当键 ⇒ **0 命中**。
#    必须剥掉 `^\s*\d+\|`，并以 `prose-miss.tsv` 的键集逐条校验。
NUM_PREFIX = re.compile(r"^\s*\d+\|")

FALLBACK = {"\u00af": "\u2500"}
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}

HAN = re.compile(r"[\u4e00-\u9fff]")


def gbk_safe(s):
    try:
        s.encode("gbk")
        return s
    except UnicodeEncodeError:
        pass
    for a, b in FALLBACK.items():
        s = s.replace(a, b)
    try:
        s.encode("gbk")
        return s
    except UnicodeEncodeError:
        pass
    t = s
    for a, b in FOLD.items():
        t = t.replace(a, b)
    t = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
    try:
        t.encode("gbk")
        return t
    except UnicodeEncodeError as e:
        raise SystemExit("GBK 无法编码: %r (%s)" % (s, e))


def load_lines(path, keep_blank=False, strip_num=False):
    with io.open(path, encoding="utf-8", newline="") as f:
        raw = f.read()
    if raw.startswith("\ufeff"):
        raise SystemExit("文件含 BOM: %s" % path)
    ls = raw.replace("\r\n", "\n").split("\n")
    if ls and ls[-1] == "":
        ls.pop()
    if not keep_blank:
        ls = [x for x in ls if x.strip()]
    if strip_num:
        ls = [NUM_PREFIX.sub("", x) for x in ls]
    return ls


def load_authority():
    """权威键集 = 原始行真值（固化文件，不随进度缩水）。"""
    if not os.path.exists(AUTH):
        raise SystemExit("缺少固化权威键集 %s" % AUTH)
    out = set()
    for ln in io.open(AUTH, encoding="utf-8", newline="").read().split("\n"):
        if ln.strip():
            out.add(ln.rstrip("\n"))
    return out


def main():
    a = sys.argv
    if "--check" in a:
        todo = set(load_lines(TODO, strip_num=True))
        auth = load_authority()
        bad = 0
        for fn in sorted(os.listdir(OUTDIR)):
            if not fn.endswith(".tsv"):
                continue
            p = os.path.join(OUTDIR, fn)
            with io.open(p, encoding="utf-8-sig", newline="") as f:
                f.readline()
                for ln in f:
                    c = ln.rstrip("\n").split("\t")
                    if len(c) >= 2 and c[0] and c[0] not in todo:
                        print("  !! 键不在待译集 %s :: %r" % (fn, c[0][:80]))
                        bad += 1
                    elif len(c) >= 2 and c[0] and c[0] not in auth:
                        print("  !! 键不在权威键集 %s :: %r" % (fn, c[0][:80]))
                        bad += 1
        print("check: 异常键 %d / 块内键命中权威集 OK" % bad)
        return

    if "--purge" in a:
        """剔除 `prose-zh.tsv` 里带行号前缀的坏键（09-29 前缀事故回滚）。"""
        p = os.path.join(HERE, "prose-zh.tsv")
        rows = []
        with io.open(p, encoding="utf-8-sig", newline="") as f:
            head = f.readline()
            for ln in f.read().replace("\r\n", "\n").split("\n"):
                if not ln.strip():
                    continue
                c = ln.split("\t")
                if len(c) >= 2 and c[0]:
                    rows.append((c[0], c[1]))
        bad = [r for r in rows if NUM_PREFIX.match(r[0])]
        good = [r for r in rows if not NUM_PREFIX.match(r[0])]
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write("src\tdst\n")
            for k, v in good:
                f.write("%s\t%s\n" % (k, v))
        print("purge: 剔除带前缀坏键 %d 条，保留 %d 条" % (len(bad), len(good)))
        return

    def opt(k):
        return a[a.index(k) + 1] if k in a else None

    block = opt("--block")
    i0 = int(opt("--from"))
    i1 = int(opt("--to"))
    if not block or i0 < 1 or i1 < i0:
        raise SystemExit("用法: --block b01 --from 1 --to 45")

    todo = load_lines(TODO, strip_num=True)   # ⛔ 剥行号前缀
    auth = load_authority()
    bad = [x for x in todo if x not in auth]
    if bad:
        raise SystemExit("待译清单有 %d 条不在权威键集（前缀未剥净？），例: %r"
                         % (len(bad), bad[0][:80]))
    dp = os.path.join(HERE, "prose-dst-%s.txt" % block)
    dst = load_lines(dp, keep_blank=True)   # ⚠️ 保留空行位（译文不会空，只防行数错位）

    n = i1 - i0 + 1
    if len(dst) != n:
        raise SystemExit("行数不符: 待译区间 %d 行 / 译文 %d 行  （%s）" % (n, len(dst), dp))
    if i1 > len(todo):
        raise SystemExit("区间越界: 待译总共 %d 行，请求到 %d" % (len(todo), i1))

    rows = []
    for k, (s, d) in enumerate(zip(todo[i0 - 1:i1], dst)):
        if not d.strip():
            raise SystemExit("空译文 @ 第 %d 行: %r" % (i0 + k, s[:80]))
        if "\t" in d or "\n" in d or "\r" in d:
            raise SystemExit("译文含制表符/换行 @ 第 %d 行: %r" % (i0 + k, s[:80]))
        if d != s and not HAN.search(d):
            print("  ~ 提示：第 %d 行译文无汉字（将视为口径保留）: %r -> %r" % (i0 + k, s[:60], d[:60]))
        rows.append((s, gbk_safe(d)))

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    out = os.path.join(OUTDIR, "%s.tsv" % block)
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in rows:
            f.write("%s\t%s\n" % (s, d))
    # 回读校验
    with io.open(out, encoding="utf-8", newline="") as f:
        got = [x.rstrip("\n").split("\t") for x in f.read().split("\n")[1:] if x.strip()]
    if len(got) != len(rows) or any(g[0] != r[0] or g[1] != r[1] for g, r in zip(got, rows)):
        raise SystemExit("回读不一致: %s" % out)
    print("OK %s: %d 条 -> %s   (待译区间 %d-%d)" % (block, len(rows), out, i0, i1))


if __name__ == "__main__":
    main()
