#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 **已部署终态**译文质量审核（只读；不改任何文件）。

为何另起脚本：
  · `lint_zh.py` 自己写明「整行未译不归它管 —— 已知规则空洞」（docstring-5），
    而「漏译」正是本次第一等大事 ⇒ 本脚本补洞，其余规则直接复用它的引擎。
  · `sweep_map_residue.py` 只扫**映射表层**；本脚本扫**游戏目录终态**（玩家真正看到的）。

判据类别：
  L1  整行未译（无汉字、残留拉丁）—— 已自动分流「口径保留」到 L1b
  L1b 口径保留（元数据 / 型号 / MOD 注释行）—— 仅计数，不算违规
  L2  半译：中文里残留拉丁（括注外、非专名）—— 复用 lint_zh latin 规则
  L3  空译：原文该行非空而译文空
  L4  结构对账：行数 / CR·LF 计数 / 转义序列计数 与原文备份不一致
  L5  编码：按 GBK 解码失败
  E1  非 GB2312 汉字（含行号）⇒ 游戏内缺字/方块风险（iCharSet=GB2312）
  E3  长数字丢失：英文里 ≥3 位、非千分位分组的数字串在译文里找不到
  Q1  禁用译法：lint_zh 的 banned/forbidden/regex/punct/paren/prefix 规则（带规则号）
  E2  型号代号丢失：**仅对 ww2-eqp.txt**（唯一有「型号保真」口径的表；其余层口径是
      「单位缩写要译出来」，用通用代号检查必全量误报）

排除清单（本作既有口径）：`DOCS\\` 手册 · `CINE\\`/`WAVS\\` 媒体 · `WW2gen.txt` · **任何 readme 类文件**。

用法：
    python audit_terminal.py              # 全量，写报告 TSV
    python audit_terminal.py --limit 50   # 冒烟
"""
import argparse
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import lint_zh  # noqa: E402

WS = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME = os.environ.get("PEG_GAME_WW2", r"D:\Program Files\PeG-WW2")
BK = os.path.join(WS, "pegww2", "testbed", "backup")
OUTDIR = os.path.join(WS, "pegww2", "research")
RULES = os.path.join(WORK, "lint_rules.tsv")
TAG = "审核-终态-20261019"

CJK = re.compile(r"[\u4e00-\u9fff]")
LAT3 = re.compile(r"[A-Za-z]{3,}")
ESC = re.compile(r"\\x[0-9A-Fa-f]{2}|\\[tn]")
# ≥3 位数字，且不属于千分位/小数分组（修掉「100,000」被切成「100」的误报）
NUM3 = re.compile(r"(?<![\d.,])\d{3,}(?![\d.,])")

# 「口径保留样式」：擦掉后才判定是否漏译
KEEP = [
    re.compile(r"https?://\S+|www\.\S+"),
    re.compile(r"\S+\.(?:exe|txt|ply|scn|ini|int|dat|rtf|xls|xlsx|dll|mov|wav)", re.I),
    re.compile(r"\b[vV]ersion\s*\d[\w.]*", re.I),
    re.compile(r"[A-Z]{2,5}(?![a-z])"),                     # 全大写缩写：HMS/KMS/DAK
    re.compile(r"[IVXLCDM]{2,}"),                           # 罗马数字：XXXVIII
    re.compile(r"\b[A-Za-z][A-Za-z0-9]*\d[A-Za-z0-9/.\-()]*\b"),   # 含数字型号：Pz 35(t)
    re.compile(r"\b\d[\d.,/:\-]*\b"),                       # 数字/日期/比例
    re.compile(r"\bw/\S+"),
]

# MOD 元数据 / 注释词（实测词频反推，见报告 §白名单来源）
META = set("""Dummy dummy File Files Gameset Equipment European conversion PeG PeGWW2 unused
lines Line not this the modified Redball CreationTime Version version Scen Scen:
loading Loading Map map Date date total maximum GUI GUIWW2 Great Britain
Germany East West USA USSR Italy Japan France Poland Russia
Robert Mary Nowak Gabitto Fuertes Savage Deuce Kirby Guzman Chlanda Rick Scott
hi Hi Says says Readme readme Scenario scenario by and or with Hugo""".split())

# 二战兵器/飞机型号词干（保留原文是既有口径 W20-A′）
STEMS = set("""StuG StuH SdKfz Sdkfz Pz PaK sFH FlaK MG MP StG K98 Sem YaK MiG
Panhard Tatra Fokker Lorraine Renault Somua Hotchkiss Char Crusader Valentine Matilda
Churchill Cromwell Sherman Stuart Grant Lee Ju Bf He Fw Me Do Hs Ar Bf Wurfrahmen
DXXI Daimler Benz Krupp Skoda Bofors Vickers""".split())

SKIP_FILE = re.compile(r"readme", re.I)
# 「非 GB2312 字形 · 有意保留」真源（人工裁定；在册字符不计违规，降级 E1b）
KEEPFILE = os.path.join(OUTDIR, "policy-keep-non-gb2312.tsv")


def load_keep_non_gb():
    out = set()
    if os.path.isfile(KEEPFILE):
        with open(KEEPFILE, "r", encoding="utf-8-sig") as fh:
            for raw in fh:
                s = raw.rstrip("\r\n")
                if not s or s.startswith("#") or s.split("\t")[0].strip() == "字":
                    continue
                f = s.split("\t")
                if f[0].strip():
                    out.add(f[0].strip())
    return out


KEEP_NONGB = load_keep_non_gb()


def read_gbk(path):
    raw = open(path, "rb").read()
    try:
        return raw.decode("gbk"), None, raw
    except UnicodeDecodeError as e:
        return raw.decode("gbk", errors="replace"), str(e), raw


def is_binary(raw):
    """扩展名 .TXT 也可能是二进制（实测 SCENARIO\\GE52I.TXT = 头 01 00 00 00 80 02…）。
    判据：头部 64 字节含 NUL，或解码失败且含 NUL ⇒ 按二进制排除，不当译文审。"""
    if b"\x00" in raw[:64]:
        return True
    try:
        raw.decode("gbk")
        return False
    except UnicodeDecodeError:
        return b"\x00" in raw


def split_lines(text):
    """三态拆行（裸 CR 也算）—— 不能用 str.splitlines()，它把 \\x0b/\\x0c 也当换行。"""
    return re.split(r"\r\n|\r|\n", text)


def residue_words(s):
    """擦掉保留样式后剩下的拉丁词。"""
    t = s
    for rx in KEEP:
        t = rx.sub(" ", t)
    return LAT3.findall(t)


def is_kept_line(words, en):
    """残留词全部属于 元数据 / 型号 词表 ⇒ 口径保留（不是漏译）。"""
    if not words:
        return True
    pool = set(words)
    return all((w in META or w in STEMS) for w in pool)


def scan_file(rel, rules, allows):
    out = []
    gp = os.path.join(GAME, rel)
    bp = os.path.join(BK, rel)
    if not os.path.isfile(bp) and os.sep not in rel:      # 根级文本的备份在 backup\text\
        bp = os.path.join(BK, "text", rel)
    raw = open(gp, "rb").read()
    if is_binary(raw):
        return [("BIN", 0, "头部 %s" % raw[:8].hex(" "), "扩展名为文本但内容是二进制 ⇒ 排除，不当译文审",
                 "info", rel)], {"lines": 0, "bytes": len(raw)}
    text, enc_err, raw = read_gbk(gp)
    ori = None
    if os.path.isfile(bp):
        ori, _, oraw = read_gbk(bp)

    tlines = split_lines(text)
    olines = split_lines(ori) if ori is not None else []
    if ori is None:
        out.append(("N0", 0, "testbed\\backup 无此文件", "从未进入汉化管线（未纳备份链）⇒ 内容为 MOD 原样",
                    "mid", rel))

    # ---- L4 结构对账 ----
    if ori is not None:
        if len(tlines) != len(olines):
            out.append(("L4", 0, "行数 译文 %d / 原文 %d" % (len(tlines), len(olines)),
                        "行数不一致", "high", rel))
        for name, rx in (("CR", rb"(?<!\r)\r(?!\n)"), ("LF", rb"(?<!\r)\n"), ("CRLF", rb"\r\n")):
            a, b = len(re.findall(rx, oraw)), len(re.findall(rx, raw))
            if a != b:
                out.append(("L4", 0, "%s 计数 原文 %d / 译文 %d" % (name, a, b),
                            "换行三态不一致", "mid", rel))
        a, b = len(ESC.findall(ori)), len(ESC.findall(text))
        if a != b:
            out.append(("L4", 0, "转义序列 原文 %d / 译文 %d" % (a, b),
                        "转义序列计数不一致", "high", rel))

    # ---- L5 编码 ----
    if enc_err:
        out.append(("L5", 0, enc_err[:120], "GBK 解码失败", "mid", rel))

    # ---- 逐行 ----
    for i, ln in enumerate(tlines, 1):
        zh = ln.strip()
        en = olines[i - 1] if i <= len(olines) else ""

        # E1 非 GB2312（带行号）——先于空行判断，空白行也可能夹字
        bad = [c for c in set(ln) if CJK.match(c) and not _gb2312_ok(c)]
        for c in sorted(bad):
            keep = c in KEEP_NONGB
            out.append(("E1b" if keep else "E1", i,
                        "「%s」（U+%04X，查 GBK 编码 = %s）" % (c, ord(c), _hex(ln, c)),
                        "有意保留（见 policy-keep-non-gb2312.tsv）" if keep else
                        "字形不在 GB2312 ⇒ 游戏内可能缺字/方块；若为繁体字则属错字",
                        "info" if keep else "high", rel))

        if not zh:
            if en.strip():
                out.append(("L3", i, "原文非空而译文为空：「%s」" % _visible(en.strip()[:60]),
                            "空译", "high", rel))
            continue

        # L1 整行未译（自动分流 L1b 保留）
        if not CJK.search(zh):
            words = residue_words(zh)
            if words:
                cls = "L1b" if is_kept_line(words, en) else "L1"
                out.append((cls, i, "%s  ⇐残留「%s」" % (zh[:80], " ".join(sorted(set(words)))[:50]),
                            "口径保留（元数据/型号/注释）" if cls == "L1b" else "疑似漏译",
                            "info" if cls == "L1b" else "high", rel))

        # L2 / Q1 复用 lint_zh 规则引擎
        ctx = {"file": rel, "line": i, "skipped": 0}
        for h in lint_zh.check(zh, en, rules, allows, ctx):
            if h["type"] == "latin":
                continue                       # L2 单独判（下面按词表分流）
            out.append(("Q1", i, "%s  [%s] %s" % (h["text"][:70], h["rule"], h["message"][:90]),
                        h["evidence"], h["severity"], rel))
        if CJK.search(zh):
            bare = lint_zh.GLOSS.sub("", zh)
            for a in allows:
                bare = a.rx.sub("", bare)
            m = LAT3.search(bare)
            if m:
                w = LAT3.findall(bare)
                cls = "L2b" if is_kept_line(w, en) else "L2"
                out.append((cls, i, "%s  [残留「%s」]" % (zh[:70], m.group(0)),
                            "口径保留（专名/署名/括注）" if cls == "L2b" else "半译：中文里残留拉丁",
                            "info" if cls == "L2b" else "mid", rel))

        # E3 长数字丢失
        if en.strip() and zh != en.strip():
            for num in sorted(set(NUM3.findall(en))):
                if num not in zh and not re.search(r"\b%s\s*(?:mm|cm|kg|km|mi)\b" % num, en, re.I):
                    out.append(("E3", i, "原文数字「%s」→ 译文「%s」" % (num, zh[:70]),
                                "长数字未出现（阿拉伯↔汉字量词互换属正常，需人工判）", "low", rel))
        # E2 型号代号丢失 —— 仅装备表
        if rel.lower() == "ww2-eqp.txt" and en.strip() and zh != en.strip():
            for tok in sorted(set(CODE_STEMS.findall(en))):
                if tok.lower() not in zh.lower() and tok.lower() not in en.lower().replace(tok, ""):
                    out.append(("E2", i, "原文「%s」→ 译文「%s」" % (tok, zh[:70]),
                                "型号代号未在译文出现", "high", rel))
    return out, {"lines": len(tlines), "bytes": len(raw)}


CODE_STEMS = re.compile(r"\b(?:StuG|StuH|SdKfz|Sdkfz|PaK|sFH|FlaK|MG\s?\d|Ju\s?\d|Bf\s?\d|"
                        r"He\s?\d|Fw\s?\d|Me\s?\d|T-3[45]|KV-?\d|IS-?\d)\b")
_GB = {}


def _gb2312_ok(ch):
    if ch not in _GB:
        try:
            ch.encode("gb2312")
            _GB[ch] = True
        except UnicodeEncodeError:
            _GB[ch] = False
    return _GB[ch]


def _hex(line, ch):
    for enc in ("gb2312", "gbk"):
        try:
            return ch.encode(enc).hex().upper()
        except UnicodeEncodeError:
            continue
    return "—"


def _visible(s):
    return "".join(c if c.isprintable() else "<%02X>" % ord(c) for c in s)


def enumerate_files():
    exts = (".txt", ".TXT", ".ply", ".PLY")
    rels, skipped = [], []
    for fn in sorted(os.listdir(GAME)):
        if fn.endswith(exts):
            (skipped if (fn.lower() == "ww2gen.txt" or SKIP_FILE.search(fn)) else rels).append(fn)
    for sub in ("SCENARIO", "USERSCEN"):
        d = os.path.join(GAME, sub)
        if not os.path.isdir(d):
            continue
        for dp, _dns, fns in os.walk(d):
            for fn in fns:
                if fn.endswith(exts):
                    rel = os.path.relpath(os.path.join(dp, fn), GAME)
                    (skipped if SKIP_FILE.search(fn) else rels).append(rel)
    return sorted(rels), skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rules, stats, _, _ = lint_zh.load_rules(RULES)
    allows = [r for r in rules if r.type == "allow"]
    print("规则表 %s：%d 条（%s）" % (os.path.basename(RULES), len(rules),
                                 " ".join("%s=%d" % kv for kv in sorted(stats.items()))))

    rels, skipped = enumerate_files()
    print("待扫 %d 个文件；按口径排除 %d 个（readme/WW2gen：%s）"
          % (len(rels), len(skipped), " ".join(skipped[:6]) + (" …" if len(skipped) > 6 else "")))
    if args.limit:
        rels = rels[:args.limit]

    allf, tot_lines, tot_bytes = [], 0, 0
    for n, rel in enumerate(rels, 1):
        f, st = scan_file(rel, rules, allows)
        tot_lines += st["lines"]
        tot_bytes += st["bytes"]
        allf += f
        if n % 500 == 0:
            print("  ... %d/%d" % (n, len(rels)))

    by = collections.Counter(c for c, *_ in allf)
    print("\n=== 命中汇总（%d 文件 / %d 行 / %.1f KB）===" % (len(rels), tot_lines, tot_bytes / 1024))
    for c, n in sorted(by.items()):
        print("  %-5s %6d" % (c, n))

    grouped = collections.defaultdict(list)
    for c, i, t, why, sev, r in allf:
        grouped[c].append((r, i, t, why, sev))
    for c, rows in grouped.items():
        p = os.path.join(OUTDIR, "_%s-%s.tsv" % (TAG, c))
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write("文件\t行号\t严重度\t证据\t判据\n")
            for r, i, t, why, sev in rows:
                fh.write("%s\t%d\t%s\t%s\t%s\n" % (r, i, sev, t.replace("\t", " "), why))
        print("  写出 %s (%d 行)" % (os.path.basename(p), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
