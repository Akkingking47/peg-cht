#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段3 装备层：词法分析（用**词级规则**取代 845 条逐串翻译）。

判据：
  · 型号型 token（含数字，或在型号前缀白名单内）⇒ 原样保留
  · 词型 token（有实义的英文/法文/德文/芬兰词）⇒ 需一条词级译法
产出：词频表（供人工写 ww2-eqp-words.tsv），以及「纯型号串」清单（可自动保留）。
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

WS = r"D:\DSH\军事游戏汉化"
SRC = os.path.join(WS, "pegww2", "testbed", "backup", "text", "ww2-eqp.txt")
OUTD = os.path.join(WS, "pegww2", "research")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)

# 型号/番号类 token 的白名单前缀（大小写不敏感；含数字的一律视为型号）
MODEL_PREFIX = {
    "pz", "pzkpfw", "sdKfz", "stug", "jgpz", "jgdpz", "jgpanther", "jagdtiger", "jagdpanzer",
    "marder", "hetzer", "ferdinand", "wespe", "hummel", "nashorn", "mobelwagen", "ostwind",
    "wirbelwind", "coelian", "kugelblitz", "brummbar", "sturmtiger", "elefant",
    "me", "bf", "fw", "ju", "he", "do", "ar", "hs", "sm", "cr", "ms", "d", "mb", "leO", "potez",
    "flak", "pak", "fg", "kwk", "mg", "mG", "atg", "how", "fg", "sIG", "k", "m", "h", "g",
    "mk", "mki", "mkii", "mkiii", "mkiv", "mkv", "mkvi", "spitfire", "hurricane", "typhoon",
    "lancaster", "wellington", "halifax", "mosquito", "tempest", "beaufighter",
    "m4", "m5", "m7", "m8", "m10", "m18", "m36", "m16", "m3", "m2", "m1", "m6",
    "c", "t", "kv", "is", "su", "bt", "ba", "tac", "t34", "t35", "t60", "t70",
    "r", "h", "s", "b", "amr", "amc", "fcm", "arL", "lorraine", "panhard", "somua", "renault",
    "hotchkiss", "char", "conus", "ckm", "wz", "tp", "7tp", "tks", "pzinz",
}
# 明确的「词」（有实义，需译）
STOP_WORDS = set()


def tokens(s):
    return [t for t in re.split(r"[\s]+", s) if t]


def main():
    raw = open(SRC, "rb").read()
    lines = [x.decode("cp1252").rstrip() for x in re.split(rb"\r\n|\r|\n", raw)]
    entries = [x for x in lines if x.strip()]
    print(f"装备条目（非空行）: {len(entries)}  唯一: {len(set(entries))}")

    wordfreq = Counter()
    modelish = 0
    need = []
    for e in entries:
        ts = tokens(e)
        has_word = False
        for t in ts:
            core = t.strip("(),.-/&'\"")
            if not core:
                continue
            low = core.lower()
            if re.search(r"\d", core):          # 含数字 ⇒ 型号
                continue
            if low in MODEL_PREFIX:
                continue
            if re.fullmatch(r"[A-Z]{1,4}", core):   # 全大写缩写 ⇒ 保留
                continue
            if re.fullmatch(r"[A-Za-z]+", core):
                wordfreq[core] += 1
                has_word = True
            else:
                wordfreq[core] += 1
                has_word = True
        if has_word:
            need.append(e)
        else:
            modelish += 1

    print(f"\n纯型号/番号串（可自动保留）: {modelish}")
    print(f"含实义词的串（需处理）: {len(need)}")
    print(f"\n=== 实义词频表（{len(wordfreq)} 个不同词）===")
    for w, c in wordfreq.most_common():
        print(f"  {c:>4d}  {w}")

    print("\n=== 含实义词的串：全部列出（供人工定词法规则后复算）===")
    for e in need:
        print(f"  {e}")

    with open(os.path.join(OUTD, "_eqp-vocab.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("词\t频次\n")
        for w, c in wordfreq.most_common():
            f.write(f"{w}\t{c}\n")
    with open(os.path.join(OUTD, "_eqp-need.txt"), "w", encoding="utf-8", newline="\n") as f:
        for e in need:
            f.write(e + "\n")
    print(f"\n[out] {os.path.relpath(os.path.join(OUTD, '_eqp-vocab.tsv'), WS)}")
    print(f"[out] {os.path.relpath(os.path.join(OUTD, '_eqp-need.txt'), WS)}")


if __name__ == "__main__":
    main()
    with open(os.path.join(OUTD, "evidence", "eqp-vocab-report.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
