# -*- coding: utf-8 -*-
"""对 COMWW2 已生效映射表做译文体检（模式筛查，不猜语义）。

检查项：
  1. 空译文 / 纯空白
  2. 译文含控制符（\\t \\r \\n）
  3. 译文含 GBK 不可编码字符
  4. 中文里混入孤立拉丁 token（原文是纯英文词时尤可疑）— 排除「按口径保留」白名单
  5. 连续重复汉字/词（河河、机场机场、师师）
  6. 译文长度异常（比原文长 >2.5 倍 且 原文 <=8 字符）
  7. 译文含残留英文标点异常（连续两个空格、尾随空格）
  8. 恒等映射（src == dst）—— 非错，但单独列出以便确认是否属口径保留
用法：python audit_map_quality.py
"""
import io
import os
import re
import sys
import collections

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(HERE, "comww2-xscn-map.tsv")

HAN = re.compile(r"[\u4e00-\u9fff]")
LAT = re.compile(r"[A-Za-z]")
# 允许保留的拉丁内容（装备型号/番号后缀/口径保留缩写）
KEEP_OK = re.compile(
    r"^(?:[A-Z]{1,4}|[A-Z]{1,4}\d+[A-Za-z0-9\-]*|\d+[A-Za-z]{1,4}|"
    r"[A-Z][A-Za-z]*\d+[A-Za-z0-9\-/]*|"
    r"[A-Za-z]{1,4}\d*[/\-][A-Za-z0-9/\-]*)$"
)
DUP2 = re.compile(r"([\u4e00-\u9fff]{1,2})\1")


def read_tsv(p):
    rows = []
    with io.open(p, encoding="utf-8-sig", newline="") as f:
        data = f.read().replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(data):
        if i == 0 or not ln.strip():
            continue
        c = ln.split("\t")
        if len(c) >= 2:
            rows.append((c[0], c[1], c[2] if len(c) > 2 else ""))
    return rows


def main():
    rows = read_tsv(MAP)
    print("映射表 %d 条" % len(rows))
    issues = collections.defaultdict(list)
    ident = []

    for s, d, note in rows:
        if not d.strip():
            issues["空译文"].append((s, d, note))
            continue
        if any(ch in d for ch in "\t\r\n"):
            issues["含控制符"].append((s, d, note))
        try:
            d.encode("gbk")
        except UnicodeEncodeError as e:
            issues["GBK 不可编码"].append((s, d + "  <%s>" % e, note))
        # 中英混排：译文含汉字，同时含一个"看起来是完整英文词"的 token 且不在白名单
        if HAN.search(d) and LAT.search(d):
            toks = [t for t in re.findall(r"[A-Za-z][A-Za-z\-'.]*", d)]
            bad = [t for t in toks if not KEEP_OK.match(t)]
            if bad and len("".join(bad)) >= 6:      # 只报"成词"的量级，避免型号噪音
                issues["中英混排(成词)"].append((s, d, note))
        m = DUP2.search(d)
        if m:
            issues["连续重复字"].append((s, d + "  <<%s>>" % m.group(0), note))
        if s.strip() == d.strip():
            ident.append((s, d, note))
        if len(s) <= 8 and len(d) > len(s) * 2.5 + 6:
            issues["长度异常"].append((s, d, note))
        if "  " in d.strip() or d != d.rstrip():
            issues["空白异常"].append((s, repr(d), note))

    for k in sorted(issues, key=lambda x: -len(issues[x])):
        arr = issues[k]
        print("\n=== %s : %d 条 ===" % (k, len(arr)))
        for s, d, note in arr[:60]:
            print("   %-34s -> %-34s [%s]" % (s[:34], d[:34], note))
        if len(arr) > 60:
            print("   ... 余 %d 条" % (len(arr) - 60))

    print("\n=== 恒等映射（src==dst，非错，待确认是否属口径保留）: %d 条 ===" % len(ident))
    for s, d, n in ident[:80]:
        print("   %-30s [%s]" % (s[:30], n))


if __name__ == "__main__":
    main()
