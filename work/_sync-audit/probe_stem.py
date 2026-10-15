# -*- coding: utf-8 -*-
import os,re,io,collections
G=r"D:\Program Files\PeG-WW2\SCENARIO"; B=r"D:\DSH\军事游戏汉化\pegww2\testbed\backup\SCENARIO"
g={x.lower():x for x in os.listdir(G)}
for stem in ("112","BoB14TV","lah","DES","B709V","fi01","MALTA","RM"):
    hits=[g[k] for k in g if k.startswith(stem.lower())]
    maps=[h for h in hits if h.lower().endswith("_m.txt")]
    print(f"--- stem {stem}: {len(hits)} 文件, _m.txt: {maps}")
    for h in sorted(hits)[:14]:
        print("     ", h)
    for h in maps:
        raw=open(os.path.join(G,h),"rb").read().decode("gbk","replace")
        print(f"     >> {h} ({len(raw)}B): {raw[:120]!r}")
