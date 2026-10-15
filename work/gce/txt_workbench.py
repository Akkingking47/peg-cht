# -*- coding: utf-8 -*-
"""GCE 场景 `.txt` 层工作台：代表清单 + 分层量测 + 待译行导出。

由 `work/basekorp/txt_workbench.py` 参数化改造而来（规则与判据完全沿用）。

★ 与 BASEKORP 版的关键差异：**先例不用单独的 `txt-precedent.tsv`，而用本 efile 的
  `.xscn` 映射表 `comww2-xscn-map.tsv`（8,803 条）**。依据 `MECHANICS.md` §19.2：
  `.xscn` 尾部串区组 0 就是场景 `.txt` 名单的镜像 ⇒ 复用即自动满足跨层一致铁律，
  且覆盖率远高于跨 efile 借先例。

产出：
  work/comww2/rep-list.tsv        md5 \t 代表 \t 组内文件数 \t 层 \t 行数 \t 字符 \t 文件清单
  work/comww2/lines-label.tsv     标签层唯一行（src \t n \t hit \t precedent）
  work/comww2/lines-prose.tsv     散文层唯一行（src \t n）
  work/comww2/blocks.tsv          散文层按文件名前缀分块

用法: python txt_workbench.py
"""
import os
import io
import re
import hashlib
import collections

GAME = r"D:\OpenPG2"
HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = "EFILE_GCE"
SC = os.path.join(GAME, EFILE, "SCENARIO")
PRE = os.path.join(HERE, "gce-xscn-map.tsv")

SENT = re.compile(r"[.!?,;]")
HAN = re.compile(r"[\u4e00-\u9fff]")


def is_label_file(s):
    """同一判据（务必与 BASEKORP 版一致，否则跨 efile 分层口径会漂）。"""
    ls = [l for l in s.split("\r\n") if l.strip()]
    if not ls:
        return None
    lab = sum(1 for l in ls
              if len(l) <= 40 and not SENT.search(l) and len(l.split()) <= 5)
    return lab >= max(3, 0.7 * len(ls))


def load_precedent():
    pre = {}
    if not os.path.exists(PRE):
        print("!! 缺先例表 %s" % PRE)
        return pre
    with io.open(PRE, encoding="utf-8") as fh:
        next(fh, None)
        for ln in fh:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 2:
                pre[p[0]] = p[1]
    return pre


def block_of(fname):
    """按文件名前缀归族：取开头的字母串 + 紧随的数字（若有）。"""
    stem = fname[:-4]
    m = re.match(r"([A-Za-z]+)(\d*)", stem)
    if not m:
        return "misc"
    letters, digits = m.group(1), m.group(2)
    return letters.lower() + (digits[:2] if len(digits) > 2 else "")


def main():
    txts = sorted(f for f in os.listdir(SC) if f.lower().endswith(".txt"))
    groups = collections.OrderedDict()
    for f in txts:
        b = open(os.path.join(SC, f), "rb").read()
        groups.setdefault(hashlib.md5(b).hexdigest(), []).append(f)

    pre = load_precedent()
    reps = []
    for md5, fs in groups.items():
        rep = sorted(fs)[0]
        b = open(os.path.join(SC, rep), "rb").read()
        s = b.decode("cp1252")
        lines = [l for l in s.split("\r\n") if l.strip()]
        if not s.strip():
            kind = "empty"
        elif is_label_file(s):
            kind = "label"
        else:
            kind = "prose"
        reps.append((md5, rep, fs, kind, lines))

    with io.open(os.path.join(HERE, "rep-list.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("md5\trep\tgroup_n\tkind\tn_lines\tn_chars\tfiles\r\n")
        for md5, rep, fs, kind, lines in reps:
            fh.write("%s\t%s\t%d\t%s\t%d\t%d\t%s\r\n" % (
                md5, rep, len(fs), kind, len(lines),
                sum(len(l) for l in lines), ",".join(sorted(fs))))

    lab = collections.Counter()
    pro = collections.Counter()
    for md5, rep, fs, kind, lines in reps:
        tgt = lab if kind == "label" else (pro if kind == "prose" else None)
        if tgt is None:
            continue
        for l in lines:
            tgt[l] += 1

    with io.open(os.path.join(HERE, "lines-label.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("src\tn\thit\tprecedent\r\n")
        for k, v in sorted(lab.items(), key=lambda x: (-x[1], x[0])):
            fh.write("%s\t%d\t%d\t%s\r\n" % (k, v, 1 if k in pre else 0,
                                             pre.get(k, "")))
    with io.open(os.path.join(HERE, "lines-prose.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("src\tn\r\n")
        for k, v in sorted(pro.items(), key=lambda x: (-x[1], x[0])):
            fh.write("%s\t%d\r\n" % (k, v))

    blocks = collections.OrderedDict()
    for md5, rep, fs, kind, lines in reps:
        if kind != "prose":
            continue
        blocks.setdefault(block_of(rep), []).append((rep, sum(len(l) for l in lines)))
    with io.open(os.path.join(HERE, "blocks.tsv"), "w",
                 encoding="utf-8", newline="\r\n") as fh:
        fh.write("block\tn_reps\tn_chars\treps\r\n")
        for b, items in sorted(blocks.items(), key=lambda x: (-sum(c for _, c in x[1]))):
            fh.write("%s\t%d\t%d\t%s\r\n" % (
                b, len(items), sum(c for _, c in items),
                ",".join(sorted(r for r, _ in items))))

    n = collections.Counter(k for _, _, _, k, _ in reps)
    print("%s .txt：文件 %d → 代表 %d 个：%s" % (EFILE, len(txts), len(reps), dict(n)))
    nlab = sum(v for k, v in lab.items())
    npro = sum(v for k, v in pro.items())
    hit = sum(v for k, v in lab.items() if k in pre)
    print("标签层：唯一行 %d（实例 %d）｜命中 `.xscn` 先例 %d（%.1f%% 实例）"
          % (len(lab), nlab, hit, 100.0 * hit / max(1, nlab)))
    print("散文层：唯一行 %d（实例 %d，%d 字符）"
          % (len(pro), npro, sum(len(k) * v for k, v in pro.items())))
    print("散文块 %d 个 -> blocks.tsv" % len(blocks))
    print("先例表 %d 条" % len(pre))


if __name__ == "__main__":
    main()
