# -*- coding: utf-8 -*-
"""只读探针：名字行末尾是否带不可见控制字符（\x00 等）——它会让 EN 键与另一侧对不上。"""
import os, re, collections
WS = r"D:\DSH\军事游戏汉化"
SETS = [("pegww2_back", os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO"), "cp1252"),
        ("pegww2_game", r"D:\Program Files\PeG-WW2\SCENARIO", "gbk"),
        ("peg_back", os.path.join(WS, "peg", "testbed", "backup", "Scenario"), "cp1252"),
        ("peg_game", r"D:\Program Files\PeG\Scenario", "gbk")]
SENT = re.compile(r"[.!?。！？:：]$")
for label, d, enc in SETS:
    if not os.path.isdir(d):
        print(f"⛔ {label} 缺目录"); continue
    tail = collections.Counter(); samp = {}
    n = 0
    for fn in os.listdir(d):
        low = fn.lower()
        if low.endswith(".scn") or low.endswith("_u.txt") or low.endswith("_n.txt"):
            continue
        try:
            t = open(os.path.join(d, fn), "rb").read().decode(enc, "replace")
        except Exception:
            continue
        for ln in re.split(r"\r\n|\r|\n", t):
            s = ln.rstrip("\r\n")
            if not s or s != s.strip():
                continue
            if not any(ord(c) < 32 or ord(c) == 127 for c in s):
                continue
            n += 1
            bad = "".join(chr(ord(c)) for c in s if ord(c) < 32 or ord(c) == 127)
            key = " + ".join(f"\\x{ord(c):02x}" for c in bad)
            tail[key] += 1
            if key not in samp:
                base = s.rstrip()
                samp[key] = (fn, base[:40], bool(SENT.search(base)), base)
    print(f"=== {label}  含控制字符的行 {n}")
    for k, c in tail.most_common(8):
        fn, vis, sent, base = samp[k]
        print(f"   {k}  ×{c}   例: {fn} | {vis!r} | 去掉尾部控制字符后以句尾符结束={sent} | 键预览={base.lower()[:32]!r}")
