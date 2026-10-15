# -*- coding: utf-8 -*-
r"""EFILE_Clu 场景 `.txt` 层汉化生成器（70 个文件；派生自 PzLIGA 版）。

填译链（**单一优先级，规则唯一**）：
  1. `clu-xscn-map.tsv`      ⭐ **跨层优先权威**：`.xscn` 组 0 就是场景 `.txt` 名单的镜像
                               （MECHANICS §19.2）⇒ 走这里即自动满足「跨层一致铁律」
  2. `txt-zh.tsv`            人工精译（散文/简报/战报，本层专有）
  3. `standard-glossary.tsv` 标准译名库（排除恒等与短条目）
  4. 地形名表                Clu 自有 `TEXT-ZH\strings_efile.txt` `[terrain]` ＋ 官方 UI 表
  5. **口径保留集**          `.xscn` 映射表里的 `src == dst` 条目 + `KEEP_PAT`
  6. 否则 **报错**（绝不静默留英文）

⚠️ Clu 的 `.txt` 是**三层混装**（实测）：`armclu-NN.txt` 是**标签清单**（`PzW 811`、
   `MG/PzW 761`，与 `.xscn` 组 0 同源）、`*-op.txt` 是**任务简报**、`*-all.txt` 是**战后战报**。
   故**不区分 label/prose**（沿 PzLIGA 口径），标签层交给 `.xscn` 表兜。

⚠️ 交叉守卫：`txt-zh.tsv` 与 `.xscn` 表**同键不同值 ⇒ 报错**（防止两层口径漂移）。

输出：`EFILE_Clu\TEXT-ZH\SCENARIO\<同名>`，GBK(936) / 无 BOM / **换行沿用原文** / 逐行对齐。
原文侧只读。用法: python gen_txt_zh.py [--dry]
"""
import io
import os
import re
import sys
import unicodedata
import collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_Clu"
SRC = os.path.join(EFILE, "SCENARIO")
ZH = os.path.join(EFILE, "TEXT-ZH", "SCENARIO")
MANUAL = os.path.join(HERE, "txt-zh.tsv")
XSCN_MAP = os.path.join(HERE, "clu-xscn-map.tsv")
XSCN_KEEP = os.path.join(HERE, "clu-xscn-keep.tsv")
GLOSS = r"D:\DSH\军事游戏汉化\glossary\standard-glossary.tsv"
UIZH = r"D:\OpenPG2\OPENGUI\strings-zh.txt"
EFILE_STRINGS = os.path.join(EFILE, "TEXT-ZH", "strings_efile.txt")
MISS = os.path.join(HERE, "txt-miss.tsv")

FALLBACK = {"\u00af": "\u2500",          # ¯ 无 GBK 编码 → ─
            "\u00a1": "!",               # ¡ 西语倒感叹号
            "\u00bf": "?",               # ¿ 西语倒问号
            "\u00ba": "o", "\u00aa": "a"}
FOLD = {"\u00df": "ss", "\u00e6": "ae", "\u00c6": "AE", "\u00f8": "o", "\u00d8": "O",
        "\u00e5": "a", "\u00c5": "A", "\u00fe": "th", "\u00de": "Th",
        "\u00f0": "d", "\u0142": "l", "\u0141": "L", "\u0111": "d", "\u0131": "i"}

KEEP_PAT = [
    # ⚠️ 2026-10-08 收紧：原 `^\[[^\]]*\]?$` 会把**方括号包裹的散文**也当代号保留
    #    （实测 `[Mensaje de Burgos]` `[Colonel Aranda comes to greet you...]` 被原样留下）。
    #    改为「括号内容**不含小写字母**才算代号」——`[V]` `[XVIII]` `[T.O.C.E.]` `[CNT]` 仍是代号；
    #    `[Mensaje de Burgos]` 这种会落到「未覆盖」被迫译出。方括号地名（`[Madrid]`）由
    #    `.xscn` 表在**更前面**兜住，不受影响。
    re.compile(r"^\[[^a-z\u00e0-\u00ff]*\]?$"),
    re.compile(r"^[A-Z]{1,4}$"),         # 纯大写缩写（FARE / CNT）
    re.compile(r"^\u00af+$"),            # ¯¯¯ 分隔线
    re.compile(r"^\d+$"),                # 纯数字
    re.compile(r"^[\W_]+$"),             # 纯符号/分隔符（含 -÷-÷- 与 ---------）
]

_TERRAIN_ORDER = ["CLEAR", "CITY", "AIRFIELD", "FOREST", "HEDGE", "HILL", "MOUNTAIN",
                  "DESERT", "SWAMP", "OCEAN", "RIVER", "FORTIFICATION", "PORT", "STREAM",
                  "CLIFF", "IMPASSABLE RIVER", "ROUGH", "CUSTOM", "ROAD", "RAILROAD"]


def load_terrain():
    """地形名：官方 UI 表（L22-41，按引擎索引）＋**Clu 自有** `strings_efile.txt` 的 `[terrain]`。

    ⚠️ Clu 的 `[terrain]` 用自家词形（`TOWN`/`UNDERWOOD/FIELD`/`SNOW/SAND`/`FORD`/
       `ESCARPMENT`/`ROADS`/`RAILS`），与官方 UI 表**不同名** ⇒ 必须从 efile 自己的
       中文侧 `[terrain]` 段按索引取，否则这些行会落到「未覆盖」被误报。
    """
    d = {}
    if os.path.exists(UIZH):
        ls = open(UIZH, "rb").read().decode("gbk", "replace").replace("\r\n", "\n").split("\n")
        if len(ls) >= 41:
            for i, key in enumerate(_TERRAIN_ORDER):
                zh = ls[21 + i].strip()
                if zh and not zh.startswith("*"):
                    d[key] = zh
    d.setdefault("RAILWAY", d.get("RAILROAD", "铁路"))
    d.setdefault("MARSH", d.get("SWAMP", "沼泽"))
    d.setdefault("TOWN", d.get("CITY", "城市"))
    d.setdefault("HARBOUR", d.get("PORT", "港口"))
    d.setdefault("HARBOR", d.get("PORT", "港口"))
    # Clu 自有 [terrain]：与原文 efile 的段逐行对齐（值行 → 中文侧同行）
    try:
        a = open(os.path.join(EFILE, "strings_efile.txt"), "rb").read().decode("cp1252").splitlines()
        b = open(EFILE_STRINGS, "rb").read().decode("gbk").splitlines()
        if len(a) == len(b):
            sec = None
            for x, y in zip(a, b):
                t = x.strip()
                if t.startswith("[") and t.endswith("]"):
                    sec = t.lower()
                    continue
                if sec == "[terrain]" and t and not t.startswith("*"):
                    d.setdefault(t, y.strip())
    except OSError:
        pass
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
    """CRLF / LF / 无换行。判据＝`n_crlf == 0 且 n_lf > 0 ⇒ 纯 LF`（见 COMWW2 硬坑）。"""
    n_crlf, n_lf = raw.count(b"\r\n"), raw.count(b"\n")
    n_bare_lf = n_lf - n_crlf
    n_bare_cr = raw.count(b"\r") - n_crlf
    if n_bare_cr:
        raise SystemExit("原文含裸 CR（非 CRLF）: %s" % fn)
    if n_lf == 0:
        return "\r\n"
    if n_crlf == 0:
        return "\n"
    if n_bare_lf == 0:
        return "\r\n"
    # 混合换行（仅 KAISER kuk11cav15_i.txt 一例）⇒ 交由 main() 归一为 CRLF
    return "\r\n"


def txt_files():
    return sorted(f for f in os.listdir(SRC) if f.lower().endswith(".txt"))


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


def trans_seg(l, manual, xmap, gloss, terr, keepset, miss, used, fn):
    """返回 (译文, 来源标签)。来源标签用于**按来源决定要不要做敬称修正**。"""
    if not l.strip():
        return l, "空行"
    if l in xmap:
        return _ret(xmap[l], "xscn表", used, fn, l)
    if l in manual:
        return _ret(manual[l], "人工", used, fn, l)
    if l in gloss:
        return _ret(gloss[l], "译名库", used, fn, l)
    if l in terr:
        return _ret(terr[l], "地形表", used, fn, l)
    if l in keepset or any(rx.match(l.strip()) for rx in KEEP_PAT):
        return l, "口径保留"
    miss.append((fn, l))
    return l, "未覆盖"


def _ret(d, kind, used, fn, l):
    if d == "" and l.strip():
        raise SystemExit("空译文: %s :: %r" % (fn, l))
    used[kind] += 1
    return d, kind


def register_fixup(s):
    r"""敬称与引号统一（POLICY §五/§四）。

    ⚠️ **不作用于 `.xscn` 表来源的行**——那一层是跨层权威，改它就和已落进游戏
       `.xscn` 的内容打架（实例：`[Your Army]` 在 `.xscn` 里就是 `[你的军队]`）。
    `你` → `您`，但 `你们` 保留（复数不写「您们」）；`“”` → `「」`。
    """
    s = re.sub("\u4f60(?!\u4eec)", "\u60a8", s)
    return s.replace("\u201c", "\u300c").replace("\u201d", "\u300d")


def main():
    dry = "--dry" in sys.argv
    manual = read_tsv(MANUAL)
    xmap = read_tsv(XSCN_MAP)
    gloss = load_gloss()
    terr = load_terrain()
    keepset = {k for k, v in xmap.items() if k.strip() == v.strip()} | set(read_tsv(XSCN_KEEP))
    print("人工 %d | xscn表 %d | 译名库 %d | 地形 %d | 口径保留 %d"
          % (len(manual), len(xmap), len(gloss), len(terr), len(keepset)))

    # ⭐ 跨层守卫：人工表与 `.xscn` 表同键不同值 ⇒ 报错
    clash = [(k, manual[k], xmap[k]) for k in manual if k in xmap and manual[k] != xmap[k]]
    if clash:
        print("!! 人工表与 `.xscn` 表冲突 %d 条（两层口径漂移）:" % len(clash))
        for k, a, b in clash[:20]:
            print("   %r 人工=%r xscn=%r" % (k[:50], a[:30], b[:30]))
        raise SystemExit(1)

    files = txt_files()
    print("场景 .txt 文件 %d 个%s" % (len(files), "  [DRY RUN]" if dry else ""))

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
        nl = detect_nl(raw, fn)
        text = raw.decode("cp1252")
        if "\r\n" in text and re.search(r"(?<!\r)\n", text):
            # 混合换行（仅 KAISER kuk11cav15_i.txt 一例）：裸 LF 归一为 CRLF
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            lines = text.split("\n")
            nl = "\r\n"
        else:
            lines = text.split(nl)
        out = []
        for l in lines:
            if not l.strip():
                out.append(l)
                continue
            if "\t" in l:                      # 原文用制表符分栏 ⇒ 逐段译后拼回
                segs = [trans_seg(x, manual, xmap, gloss, terr, keepset, miss, used, fn)
                        for x in l.split("\t")]
                out.append("\t".join(d if k == "xscn表" else register_fixup(d)
                                     for d, k in segs))
                continue
            d, k = trans_seg(l, manual, xmap, gloss, terr, keepset, miss, used, fn)
            out.append(d if k == "xscn表" else register_fixup(d))

        for src_l, dst_l in zip(lines, out):
            if dst_l.strip() and ("\t" in dst_l and "\t" not in src_l):
                raise SystemExit("译文新引入制表符 @ %s: %r <- %r" % (fn, dst_l, src_l))

        plan.append((fn, lines, out, nl))
        tot_lines += sum(1 for x in lines if x.strip())
        tot_zh += sum(1 for c in "".join(out) if "\u4e00" <= c <= "\u9fff")
        src_bytes += len(raw)

    print("填译来源（第 1 遍）：%s" % dict(used))
    if miss:
        cnt = collections.Counter(m[1] for m in miss)
        print("!! 未覆盖 %d 处（唯一 %d）——**未落盘**:" % (len(miss), len(cnt)))
        for l, n in cnt.most_common(40):
            print("   x%-3d %r" % (n, l[:110]))
        with io.open(MISS, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("src\tn\n")
            for l, n in cnt.most_common():
                fh.write("%s\t%d\n" % (l, n))
        print("（已写 %s）" % os.path.basename(MISS))
        raise SystemExit(1)

    # 第 2 遍：GBK 安全化 + 字节构造（**在 miss 闸门之后**，否则未译的西语行会
    #   先炸在 `¡` 这类 GBK 编不了的字符上，把 miss 清单掩盖掉）
    built = []
    for fn, lines, out, nl in plan:
        out = [gbk_safe(l) for l in out]
        blob = nl.join(out).encode("gbk")
        if blob.decode("gbk").split(nl) != out:
            raise SystemExit("编解码往返不一致: %s" % fn)
        if nl == "\r\n" and blob.count(b"\n") != blob.count(b"\r\n"):
            raise SystemExit("输出换行异常: %s" % fn)
        built.append((fn, lines, out, blob, nl))
        tgt_bytes += len(blob)
    plan = built

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
