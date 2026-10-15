# -*- coding: utf-8 -*-
"""COMWW2 `label` 层（地图标签 .txt）汉化生成器。

由 `work/basekorp/gen_label_zh.py` 参数化改造（判据与守卫完全沿用）。

填译优先级：
  1. `label-zh.tsv`            —— 本层专用缺口表（人工逐条精译）
  2. `label-auto.tsv`          —— 番号链规则引擎对「未覆盖行」的产出（688 条）
                                 （`gen_xscn_batch.py --todo label-miss.tsv --out label-auto.tsv`）
  3. `comww2-xscn-map.tsv`     —— 本 efile `.xscn` 译文表（**同源镜像**，实测覆盖 84.3%）
  4. **口径保留集**（显式）     —— 本 efile `.xscn` 残留集 + 模式（方括号代号 / 纯大写 ≤4 / 标高 / 下划线）
  5. 否则 **报错**（绝不静默留英文）

★ 口径保留集为何用 `.xscn` 残留：`.xscn` 与场景 `.txt` 的 label 行是**同一批串**
  （组 0 镜像）。`.xscn` 收官后剩下的 282 条已被判定为「无法译、按口径保留」，
  同一判定理应在本层生效 ⇒ 跨层口径自动一致，无需重判。

输出：`<efile>\\TEXT-ZH\\SCENARIO\\<同名>.txt`，GBK(936) / 无 BOM / CRLF。
原文侧（`SCENARIO\\*.txt`）只读，绝不改写。
用法: python gen_label_zh.py [--dry]
"""
import io
import os
import re
import sys
import unicodedata
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_COMWW2"
SRC = os.path.join(EFILE, "SCENARIO")
ZH = os.path.join(EFILE, "TEXT-ZH", "SCENARIO")
MANUAL = os.path.join(HERE, "label-zh.tsv")
AUTO = os.path.join(HERE, "label-auto.tsv")
GLOSS = r"D://DSH//军事游戏汉化//glossary//standard-glossary.tsv"
XSCN_MAP = os.path.join(HERE, "comww2-xscn-map.tsv")
REPLIST = os.path.join(HERE, "rep-list.tsv")
KEEPSRC = os.path.join(HERE, "xscn-uniq-final3.tsv")
KEEPLIST = os.path.join(HERE, "label-keep.tsv")   # 人工判定的「未知缩写链 / 潜艇番号 / 标高」     # 本 efile `.xscn` 残留＝口径保留集

# U+00AF(¯) 在 GBK 无编码（正是「cp1252 假汉字」的陷阱），按视觉等价替换。
FALLBACK = {"\u00af": "\u2500"}
# 折写映射（NFKD 不分解这些字母，必须显式）
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}

KEEP_PAT = [
    re.compile(r"^\[[^\]]*\]?$"),        # 方括号代号 [55A] / [8A] / 54A]
    re.compile(r"^[A-Z]{1,4}$"),         # 纯大写作号 FC / NG / BC / FA / GM / RF
    re.compile(r"^H \d+\.\d+$"),         # 标高标记 H 125.6
    re.compile(r"^\u00af+$"),            # 纯下划线装饰行（经 ¯→─ 兜底）
    re.compile(r"^\d+$"),                # 纯数字（编号）
]


def read_tsv(path):
    """读 src/dst 两列（允许第三列 note）。

    ⚠️ 必须用完整 split("\\t")：用 split("\\t",1) 会把 note 并进译文，
       往标签行里塞进制表符（静默结构污染）。与 xscn.py::load_map 保持一致。
    """
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0]:
                d[c[0]] = c[1]
    return d


def load_gloss():
    """标准译名库（23,200 条），带两条守卫：
      ① 排除恒等映射（`FC→FC` 是对「口径保留」的确认，不是译文）；
      ② **排除短条目**（单/双字母缩写上下文相关，`FA`＝巴斯克自治区空军、
         `RM`＝意海军 在本 efile 未必成立）——只收 len>=4 或含空格者。
    """
    d = {}
    if not os.path.exists(GLOSS):
        return d
    with io.open(GLOSS, encoding="utf-8-sig", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and c[0] and c[1].strip():
                k = c[0].strip()
                if k == c[1].strip():
                    continue
                if len(k) >= 4 or " " in k:
                    d.setdefault(k, c[1].strip())
    return d


def read_first_col(path):
    out = set()
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if c and c[0]:
                out.add(c[0])
    return out


def label_files():
    out = []
    with io.open(REPLIST, encoding="utf-8") as f:
        f.readline()
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 7 and p[3] == "label":
                out.append(p[1])
    return sorted(out)


def gbk_safe(s):
    """三级兜底：① 直接编 ② 视觉等价替换（¯→─）③ **折写去变音符**
    （BASEKORP 既有口径：`Brześć Litewski`→`Brzesc`）。
    COMWW2 实测 6 种不可编码字符：¯(2703) / ä / ß / ï / ô / É。
    """
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
    # 折写：先做显式字母映射（NFKD 不分解 ß/l/ø…），再去组合记号
    t = s
    for a, b in FOLD.items():
        t = t.replace(a, b)
    t = "".join(c for c in unicodedata.normalize("NFKD", t)
                if not unicodedata.combining(c))
    try:
        t.encode("gbk")
        return t
    except UnicodeEncodeError as e:
        raise SystemExit("GBK 无法编码: %r (%s)" % (s, e))


def main():
    dry = "--dry" in sys.argv
    manual = read_tsv(MANUAL)
    auto = read_tsv(AUTO)
    xmap = read_tsv(XSCN_MAP)
    gloss = load_gloss()
    keepset = read_first_col(KEEPSRC) | read_first_col(KEEPLIST)
    print("缺口表 %d | 规则引擎 %d | xscn 映射 %d | 口径保留集 %d"
          % (len(manual), len(auto), len(xmap), len(keepset)))

    files = label_files()
    print("label 文件 %d 个%s" % (len(files), "  [DRY RUN]" if dry else ""))

    miss = []
    used = collections.Counter()
    plan = []
    tot_lines = tot_zh = 0
    src_bytes = tgt_bytes = 0

    for fn in files:
        sp = os.path.join(SRC, fn)
        raw = open(sp, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            raise SystemExit("原文含 BOM: %s" % fn)
        # ⚠️ 换行必须**沿用原文**：COMWW2 的 .txt 有 516 个纯 CRLF + **52 个纯 LF**
        #    （464 个无换行的空壳）。强行统一 CRLF 会改变文件结构。
        n_crlf, n_lf = raw.count(b"\r\n"), raw.count(b"\n")
        if n_crlf == 0 and n_lf == 0:
            nl = "\r\n"
        elif n_crlf == n_lf:
            nl = "\r\n"
        elif n_crlf == 0:
            nl = "\n"
        else:
            raise SystemExit("原文混合换行（CRLF %d / LF %d）: %s" % (n_crlf, n_lf, fn))

        text = raw.decode("cp1252")
        lines = text.split(nl)
        out = []
        for l in lines:
            if not l.strip():
                out.append(l)
                continue
            if l in manual:
                d = manual[l]; used["缺口表"] += 1
            elif l in auto:
                d = auto[l]; used["规则引擎"] += 1
            elif l in xmap:
                d = xmap[l]; used["xscn映射"] += 1
            elif l in gloss:
                d = gloss[l]; used["译名库"] += 1
            elif l in keepset or any(rx.match(l.strip()) for rx in KEEP_PAT):
                d = l; used["口径保留"] += 1
            else:
                miss.append((fn, l))
                d = None
            if d == "" and l.strip():
                raise SystemExit("空译文: %s :: %r" % (fn, l))
            out.append(d if d is not None else l)

        # 守卫：只禁「译文**新引入**」的控制符。
        #       ⚠️ 原文自带制表符要照留（`huncam.txt` 的 `\t- Blow / build / repair is allowed`
        #          是缩进条目；与 §19.4 的 `strings_efile.txt` 同型）。
        for src_l, dst_l in zip(lines, out):
            if dst_l.strip() and ("\t" in dst_l and "\t" not in src_l):
                raise SystemExit("译文新引入制表符 @ %s: %r <- %r" % (fn, dst_l, src_l))
        out = [gbk_safe(l) for l in out]          # 含 ¯→─ 兜底
        blob = nl.join(out).encode("gbk")
        if blob.decode("gbk").split(nl) != out:
            raise SystemExit("编解码往返不一致: %s" % fn)
        if nl == "\r\n" and blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit("输出换行异常: %s" % fn)

        plan.append((fn, lines, out, blob))
        tot_lines += sum(1 for x in lines if x.strip())
        tot_zh += sum(1 for c in "".join(out) if "\u4e00" <= c <= "\u9fff")
        src_bytes += len(raw)
        tgt_bytes += len(blob)

    print("填译来源：%s" % dict(used))
    if miss:
        cnt = collections.Counter(m[1] for m in miss)
        print("!! 未覆盖 %d 处（唯一 %d）——**未落盘**:" % (len(miss), len(cnt)))
        for l, n in cnt.most_common(80):
            print("   x%-3d %r" % (n, l))
        with io.open(os.path.join(HERE, "label-miss.tsv"), "w",
                     encoding="utf-8", newline="") as fh:
            fh.write("src\tn\n")
            for l, n in cnt.most_common():
                fh.write("%s\t%d\n" % (l, n))
        print("（已写 label-miss.tsv）")
        raise SystemExit(1)

    if dry:
        print("DRY RUN：%d 文件 / 非空行 %d / 输出汉字 %d / 字节 %d -> %d"
              % (len(plan), tot_lines, tot_zh, src_bytes, tgt_bytes))
        return

    if not os.path.isdir(ZH):
        os.makedirs(ZH)
    for fn, lines, out, blob in plan:
        tgt = os.path.join(ZH, fn)
        with open(tgt, "wb") as f:
            f.write(blob)
        back = open(tgt, "rb").read()
        if back != blob:
            raise SystemExit("回读不一致: %s" % fn)
        if back[:3] == b"\xef\xbb\xbf":
            raise SystemExit("输出含 BOM: %s" % fn)
        if back.decode("gbk").split(nl) != out:
            raise SystemExit("回读行不一致: %s" % fn)
        if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
            raise SystemExit("输出含裸 LF: %s" % fn)

    print("---")
    print("写出 %d 个文件 | 非空行 %d | 输出汉字 %d" % (len(plan), tot_lines, tot_zh))
    print("字节 %d -> %d" % (src_bytes, tgt_bytes))
    print("OK 全部行已覆盖，原文件未改动")


if __name__ == "__main__":
    main()
