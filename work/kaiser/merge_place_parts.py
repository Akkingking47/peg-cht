# -*- coding: utf-8 -*-
"""合并 KAISER .xscn 地名/专名层 16 份译文 -> xscn-place.tsv，并做硬校验。"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
HAN = re.compile(r"[\u4e00-\u9fff]")


FOLD = {
    "\u00e0": "a", "\u00e1": "a", "\u00e2": "a", "\u00e3": "a", "\u00e4": "a", "\u00e5": "a",
    "\u00c0": "A", "\u00c1": "A", "\u00c2": "A", "\u00c3": "A", "\u00c4": "A", "\u00c5": "A",
    "\u00e6": "ae", "\u00c6": "AE",
    "\u00e7": "c", "\u00c7": "C",
    "\u00e8": "e", "\u00e9": "e", "\u00ea": "e", "\u00eb": "e",
    "\u00c8": "E", "\u00c9": "E", "\u00ca": "E", "\u00cb": "E",
    "\u00ec": "i", "\u00ed": "i", "\u00ee": "i", "\u00ef": "i",
    "\u00cc": "I", "\u00cd": "I", "\u00ce": "I", "\u00cf": "I",
    "\u00f1": "n", "\u00d1": "N",
    "\u00f2": "o", "\u00f3": "o", "\u00f4": "o", "\u00f5": "o", "\u00f6": "o", "\u00f8": "o",
    "\u00d2": "O", "\u00d3": "O", "\u00d4": "O", "\u00d5": "O", "\u00d6": "O", "\u00d8": "O",
    "\u00f9": "u", "\u00fa": "u", "\u00fb": "u", "\u00fc": "u",
    "\u00d9": "U", "\u00da": "U", "\u00db": "U", "\u00dc": "U",
    "\u00fd": "y", "\u00ff": "y", "\u00dd": "Y",
    "\u00df": "ss",
    "\u0153": "oe", "\u0152": "OE",
    "\u0161": "s", "\u0160": "S", "\u017e": "z", "\u017d": "Z",
    "\u015f": "s", "\u015e": "S", "\u0131": "i", "\u0130": "I",
    "\u011f": "g", "\u011e": "G", "\u010d": "c", "\u010c": "C",
    "\u00b3": "3", "\u00b2": "2", "\u00b9": "1",
}


def gbk_safe(s):
    """折写 GBK 装不下的变音符（与根级 gen_root_zh.gbk_safe 同口径）。"""
    for k, v in FOLD.items():
        if k in s:
            s = s.replace(k, v)
    return s


def rdlines(p):
    if not os.path.exists(p):
        raise SystemExit("缺文件 " + p)
    return [l for l in io.open(p, encoding="utf-8", newline="").read()
            .replace("\r\n", "\n").split("\n")]


def main():
    do = "--apply" in sys.argv
    rows = []
    errs = []
    stats = {"kept": 0, "zh": 0, "rows": 0, "kept_mod": 0}
    for i in range(1, 17):
        tag = "%02d" % i
        src = rdlines(os.path.join(HERE, "_pl_todo_part%s.txt" % tag))
        dst = rdlines(os.path.join(HERE, "_pl_dst_part%s.txt" % tag))
        src = [l for l in src if l.strip()]
        dst = [l for l in dst if l.strip()]
        if len(src) != len(dst):
            errs.append("part%s 行数不符 源%d/译%d" % (tag, len(src), len(dst)))
            continue
        for s, d in zip(src, dst):
            s = s.rstrip("\n")
            d = d.rstrip("\n")
            if "\t" in d:
                errs.append("part%s 含 TAB: %r" % (tag, d[:40]))
                continue
            if d != d.strip():
                errs.append("part%s 首尾空白: %r" % (tag, d[:40]))
                continue
            if not d:
                errs.append("part%s 空译文 (源 %r)" % (tag, s[:40]))
                continue
            has_han = bool(HAN.search(d))
            stats["rows"] += 1
            if not has_han:
                # 无汉字 ⇒ 视为「照抄/代号保留」：不入表（不写即保持原文）
                stats["kept"] += 1
                if d.strip() != s.strip():
                    stats["kept_mod"] += 1
                    if len(stats.setdefault("kept_ex", [])) < 12:
                        stats["kept_ex"].append((tag, s[:40], d[:44]))
                continue
            d = gbk_safe(d)
            if s.count("[") != d.count("[") or s.count("]") != d.count("]"):
                errs.append("part%s 方括号数变: %r -> %r" % (tag, s[:34], d[:34]))
                continue
            try:
                d.encode("gbk")
            except UnicodeEncodeError:
                errs.append("part%s GBK 编不了: %r" % (tag, d[:40]))
                continue
            stats["zh"] += 1
            rows.append((s, d))
    print("合并 %d 行；含汉字 %d；照抄保留 %d（其中与原文有差异但无汉字者 %d，已忽略）"
          % (stats["rows"], stats["zh"], stats["kept"], stats["kept_mod"]))
    for tag, s, d in stats.get("kept_ex", []):
        print("   ~ part%s %r -> %r" % (tag, s, d))
    print("错误 %d" % len(errs))
    for e in errs[:30]:
        print("   !! " + e)
    if errs:
        raise SystemExit(1)

    # 去重（同 src 不同 dst 报冲突）
    m = {}
    dup = []
    for s, d in rows:
        if s in m and m[s] != d:
            dup.append((s, m[s], d))
        m.setdefault(s, d)
    if dup:
        print("!! src 冲突 %d" % len(dup))
        for s, a, b in dup[:10]:
            print("   %r: %s / %s" % (s[:34], a[:24], b[:24]))
    print("唯一 src %d" % len(m))

    if not do:
        print("(dry-run)")
        return
    with io.open(os.path.join(HERE, "xscn-place.tsv"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write("src\tdst\n")
        for s in sorted(m):
            f.write("%s\t%s\n" % (s, m[s]))
    print("已写 xscn-place.tsv（%d 条）" % len(m))


if __name__ == "__main__":
    main()
