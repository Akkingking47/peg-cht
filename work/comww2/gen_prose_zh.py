# -*- coding: utf-8 -*-
"""COMWW2 `prose` 层（战役说明 / 简报头等 .txt）汉化生成器。

与 `gen_label_zh.py` 同一套填译链（规则唯一），只是**多了地形表**一档：

  1. `prose-zh.tsv`            人工精译（跨层最高优先）
  2. `label-zh.tsv`            label 层的人工表（UI 套话在两层都出现，直接复用）
  3. `prose-auto.tsv`          番号链规则引擎对「未覆盖行」的产出
  4. `comww2-xscn-map.tsv`     本 efile `.xscn` 译文表（同源镜像）
  5. `standard-glossary.tsv`   标准译名库（排除恒等与短条目）
  6. **官方地形名表**          `OPENGUI\\strings-zh.txt` L22-41（`CLEAR/FOREST/HILL/ROUGH`…）
                               ⚠️ 放在 `.xscn` 之后：`.xscn` 主流用「空地」而官方用「开阔地」，
                               依 §24.3 的「沿上游」原则，`.xscn` 已覆盖者不回退到官方口径。
  7. **口径保留集**            本 efile `.xscn` 残留 + label-keep + 模式
  8. 否则 **报错**（绝不静默留英文）

⚠️ 换行/编码：`¯`(U+00AF) 无 GBK 编码 → `─`(U+2500)；变音符（ä/ß/ï/ô/É）→ 折写。
输出 GBK(936) / 无 BOM / CRLF；原文侧只读。
用法: python gen_prose_zh.py [--dry]
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
MANUAL = os.path.join(HERE, "prose-zh.tsv")
LABELMAN = os.path.join(HERE, "label-zh.tsv")
AUTO = os.path.join(HERE, "prose-auto.tsv")
XSCN_MAP = os.path.join(HERE, "comww2-xscn-map.tsv")
REPLIST = os.path.join(HERE, "rep-list.tsv")
KEEPSRC = os.path.join(HERE, "xscn-uniq-final3.tsv")
KEEPLIST = os.path.join(HERE, "label-keep.tsv")
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
UIZH = r"D:\OpenPG2\OPENGUI\strings-zh.txt"

FALLBACK = {"\u00af": "\u2500"}
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}

KEEP_PAT = [
    re.compile(r"^\[[^\]]*\]?$"),
    re.compile(r"^[A-Z]{1,4}$"),
    re.compile(r"^H \d+\.\d+$"),
    re.compile(r"^\u00af+$"),
    re.compile(r"^\d+$"),
]

# 官方地形名（`OPENGUI\strings-zh.txt` L22-41，按行序）
_TERRAIN_ORDER = ["CLEAR", "CITY", "AIRFIELD", "FOREST", "HEDGE", "HILL", "MOUNTAIN",
                  "DESERT", "SWAMP", "OCEAN", "RIVER", "FORTIFICATION", "PORT", "STREAM",
                  "CLIFF", "IMPASSABLE RIVER", "ROUGH", "CUSTOM", "ROAD", "RAILROAD"]


def load_terrain():
    """读官方中文地形名（L22-41），与 `_TERRAIN_ORDER` 逐行对应。"""
    d = {}
    if not os.path.exists(UIZH):
        return d
    ls = open(UIZH, "rb").read().decode("gbk", "replace").replace("\r\n", "\n").split("\n")
    if len(ls) < 41:
        return d
    for i, key in enumerate(_TERRAIN_ORDER):
        zh = ls[21 + i].strip()
        if zh and not zh.startswith("*"):
            d[key] = zh
    # 常见同义写法
    d.setdefault("RAILWAY", d.get("RAILROAD", "铁路"))
    d.setdefault("MARSH", d.get("SWAMP", "沼泽"))
    d.setdefault("TOWN", d.get("CITY", "城市"))
    d.setdefault("HARBOUR", d.get("PORT", "港口"))
    d.setdefault("HARBOR", d.get("PORT", "港口"))
    return d


def read_tsv(path):
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


def load_gloss():
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


def detect_nl(raw, fn):
    """判定原文换行类型：CRLF / LF / 无换行（默认 CRLF）。

    ⚠️ 硬坑（2026-09-30 实做踩到）：一度写成 `elif n_crlf == n_lf: nl = "\\r\\n"`，
    对「**只有 1 个裸 LF、0 个 CRLF**」的 52 个 LF 文件命中该分支 ⇒ 输出被写成 CRLF，
    而回读校验按 CRLF 切分「全部换成 CRLF 的整块」⇒ 回读只剩 1 行、**部署中断在 hun01_b.txt**。
    正确判据：`n_crlf == 0 且 n_lf > 0` ⇒ 纯 LF。
    """
    n_crlf, n_lf = raw.count(b"\r\n"), raw.count(b"\n")
    n_bare_lf = n_lf - n_crlf
    n_bare_cr = raw.count(b"\r") - n_crlf
    if n_bare_cr:
        raise SystemExit("原文含裸 CR（非 CRLF）: %s" % fn)
    if n_lf == 0:
        return "\r\n"          # 无换行（单行/空壳）
    if n_crlf == 0:
        return "\n"            # 纯 LF
    if n_bare_lf == 0:
        return "\r\n"          # 纯 CRLF
    raise SystemExit("原文混合换行（CRLF %d / LF %d）: %s" % (n_crlf, n_bare_lf, fn))


def prose_files():
    out = []
    with io.open(REPLIST, encoding="utf-8") as f:
        f.readline()
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 7 and p[3] == "prose":
                out.append(p[1])
    return sorted(out)


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


def trans_seg(l, manual, labman, auto, xmap, gloss, terr, keepset, miss, used, fn):
    """翻译单个「制表符分段」；未命中则记 miss 并返回原文。"""
    if not l.strip():
        return l
    if l in manual:
        d = manual[l]; used["人工"] += 1
    elif l in labman:
        d = labman[l]; used["label人工"] += 1
    elif l in auto:
        d = auto[l]; used["规则引擎"] += 1
    elif l in xmap:
        d = xmap[l]; used["xscn"] += 1
    elif l in gloss:
        d = gloss[l]; used["译名库"] += 1
    elif l in terr:
        d = terr[l]; used["地形表"] += 1
    elif l in keepset or any(rx.match(l.strip()) for rx in KEEP_PAT):
        d = l; used["口径保留"] += 1
    else:
        miss.append((fn, l))
        d = None
    if d == "" and l.strip():
        raise SystemExit("空译文: %s :: %r" % (fn, l))
    return d if d is not None else l


def main():
    dry = "--dry" in sys.argv
    manual = read_tsv(MANUAL)
    labman = read_tsv(LABELMAN)
    auto = read_tsv(AUTO)
    xmap = read_tsv(XSCN_MAP)
    gloss = load_gloss()
    terr = load_terrain()
    keepset = read_first_col(KEEPSRC) | read_first_col(KEEPLIST)
    print("人工 %d | label人工 %d | 规则引擎 %d | xscn %d | 译名库 %d | 地形 %d | 保留 %d"
          % (len(manual), len(labman), len(auto), len(xmap), len(gloss), len(terr), len(keepset)))

    files = prose_files()
    print("prose 代表文件 %d 个%s" % (len(files), "  [DRY RUN]" if dry else ""))

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
        nl = detect_nl(raw, fn)

        lines = raw.decode("cp1252").split(nl)
        out = []
        for l in lines:
            if not l.strip():
                out.append(l)
                continue
            # ⚠️ 原文用制表符作**列分隔**（`huncam.txt` 的 `\t- Blow / build / repair is allowed`）
            #    ⇒ 按段翻译后以制表符拼回，不破坏缩进/分栏结构。
            if "\t" in l:
                parts = [trans_seg(x, manual, labman, auto, xmap, gloss, terr, keepset, miss, used, fn)
                         for x in l.split("\t")]
                out.append("\t".join(parts))
                continue
            out.append(trans_seg(l, manual, labman, auto, xmap, gloss, terr, keepset, miss, used, fn))

        # 守卫：只禁「译文**新引入**」的控制符。
        #       ⚠️ 原文自带制表符要照留（`huncam.txt` 的 `\t- Blow / build / repair is allowed`
        #          是缩进条目；与 §19.4 的 `strings_efile.txt` 同型）。
        for src_l, dst_l in zip(lines, out):
            if dst_l.strip() and ("\t" in dst_l and "\t" not in src_l):
                raise SystemExit("译文新引入制表符 @ %s: %r <- %r" % (fn, dst_l, src_l))
        out = [gbk_safe(l) for l in out]
        blob = nl.join(out).encode("gbk")
        if blob.decode("gbk").split(nl) != out:
            raise SystemExit("编解码往返不一致: %s" % fn)
        if nl == "\r\n" and blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit("输出换行异常: %s" % fn)

        plan.append((fn, lines, out, blob, nl))
        tot_lines += sum(1 for x in lines if x.strip())
        tot_zh += sum(1 for c in "".join(out) if "\u4e00" <= c <= "\u9fff")
        src_bytes += len(raw)
        tgt_bytes += len(blob)

    print("填译来源：%s" % dict(used))
    if miss:
        cnt = collections.Counter(m[1] for m in miss)
        print("!! 未覆盖 %d 处（唯一 %d）——**未落盘**:" % (len(miss), len(cnt)))
        for l, n in cnt.most_common(60):
            print("   x%-3d %r" % (n, l[:110]))
        with io.open(os.path.join(HERE, "prose-miss.tsv"), "w",
                     encoding="utf-8", newline="") as fh:
            fh.write("src\tn\n")
            for l, n in cnt.most_common():
                fh.write("%s\t%d\n" % (l, n))
        print("（已写 prose-miss.tsv）")
        raise SystemExit(1)

    if dry:
        print("DRY RUN：%d 文件 / 非空行 %d / 输出汉字 %d / 字节 %d -> %d"
              % (len(plan), tot_lines, tot_zh, src_bytes, tgt_bytes))
        return

    if not os.path.isdir(ZH):
        os.makedirs(ZH)
    for fn, lines, out, blob, nl in plan:
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
        # ⚠️ 硬坑（2026-09-30）：此处一度误用**循环外泄漏的 `nl`**（= 构建阶段最后一个文件的换行），
        #    导致 LF 文件被按 CRLF 校验 ⇒ 部署中断在 `hun01_b.txt`。
        #    修法：`plan` 元组带上每个文件自己的 `nl`（见构建循环），校验只用它。
        if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
            raise SystemExit("输出含裸 LF: %s" % fn)
        if nl == "\n" and back.count(b"\r\n"):
            raise SystemExit("输出混入 CRLF: %s" % fn)

    print("---")
    print("写出 %d 个文件 | 非空行 %d | 输出汉字 %d" % (len(plan), tot_lines, tot_zh))
    print("字节 %d -> %d" % (src_bytes, tgt_bytes))
    print("OK 全部行已覆盖，原文件未改动")


if __name__ == "__main__":
    main()
