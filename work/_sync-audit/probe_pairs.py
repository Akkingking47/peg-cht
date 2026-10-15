# -*- coding: utf-8 -*-
"""只读侦察 2：英文备份 ↔ 中文成品 的成对文件，是否行行对应。"""
import os, re, sys

WS = r"D:\DSH\军事游戏汉化"
JOBS = [
    ("PeG",      r"D:\Program Files\PeG",      "Scenario",
     os.path.join(WS, "peg", "testbed", "backup", "Scenario"), "ALMATY1"),
    ("PeG-WW2",  r"D:\Program Files\PeG-WW2",  "SCENARIO",
     os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO"), "7Pzra7147"),
]


def lines(p, enc):
    if not os.path.isfile(p):
        return None
    t = open(p, "rb").read()
    return re.split(r"\r\n|\r|\n", t.decode(enc, "replace"))


def show(tag, bak_dir_en, game_dir_zh, en_names, zh_names, enc_en, enc_zh, limit=8):
    print("-" * 78)
    print(f"  ### {tag}")
    for en_n, zh_n in zip(en_names, zh_names):
        a = lines(os.path.join(bak_dir_en, en_n), enc_en)
        b = lines(os.path.join(game_dir_zh, zh_n), enc_zh)
        print(f"   [{en_n}] 英={ '(缺)' if a is None else len(a)} 行"
              f"  中={ '(缺)' if b is None else len(b)} 行")
        if a is None or b is None:
            continue
        n = max(len(a), len(b))
        for i in range(min(n, limit)):
            print("      EN | " + (a[i] if i < len(a) else "<无>")[:80])
            print("      ZH | " + (b[i] if i < len(b) else "<无>")[:80])


for tag, root, scndir, bak, stem in JOBS:
    print("=" * 78)
    print(f"### {tag}   备份目录 {bak}")
    if not os.path.isdir(bak):
        print("   ⛔ 备份目录不存在"); continue
    bf = os.listdir(bak)
    print(f"   备份文件 {len(bf)} 个；扩展名 "
          + str({e: sum(1 for x in bf if os.path.splitext(x)[1].lower() == e)
                 for e in sorted({os.path.splitext(x)[1].lower() for x in bf})}))
    S = os.path.join(root, scndir)
    gf = set(os.listdir(S))
    # 备份里对应的中文名（大小写可能不同）
    hits = sum(1 for x in bf if x in gf)
    print(f"   备份文件名**原样**出现在成品目录：{hits}/{len(bf)}")
    low = {x.lower(): x for x in gf}
    hits2 = sum(1 for x in bf if x.lower() in low)
    print(f"   忽略大小写后命中：{hits2}/{len(bf)}")
    # 成对样本
    if tag == "PeG":
        show(tag, bak, S,
             [stem + "_m.txt", stem.lower() + ".txt"],
             [stem + "_m.txt", stem.lower() + ".TXT"],
             "cp1252", "gbk")
    else:
        show(tag, bak, S,
             [stem + "_m.txt", stem + "_i.txt"],
             [stem + "_m.txt", stem + "_i.TXT"],
             "cp1252", "gbk")
    # 备份目录里 ASCII 原文样本
    print(f"   --- 备份里 {stem}* 的文件 ---")
    for x in sorted(bf):
        if x.lower().startswith(stem.lower()):
            print("      ", x, os.path.getsize(os.path.join(bak, x)))
