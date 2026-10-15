# -*- coding: utf-8 -*-
r"""把 `gen_txt_zh.py --dry` 产出的 `txt-miss.tsv` 切成 N 块，交子代理按 TXT-POLICY 翻译。

用法: python make_txt_chunks.py [N]         # 默认 6
输出: work\clu\txt-chunks\chunk-NN.tsv（单列）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
MISS = os.path.join(HERE, "txt-miss.tsv")

n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 6
if not os.path.exists(MISS):
    raise SystemExit("先跑: python gen_txt_zh.py --dry（它会写 %s）" % MISS)
rows = []
for i, ln in enumerate(io.open(MISS, encoding="utf-8-sig", newline="").read()
                       .replace("\r\n", "\n").split("\n")):
    if i == 0 or not ln.strip():
        continue
    c = ln.split("\t")
    rows.append((c[0], int(c[1]) if len(c) > 1 and c[1].isdigit() else 0))
d = os.path.join(HERE, "txt-chunks")
os.makedirs(d, exist_ok=True)
for f in os.listdir(d):
    os.remove(os.path.join(d, f))
# 长散文优先排前（§三 套语多的先给人看），按出现次数降序再按长度
rows.sort(key=lambda x: (-x[1], -len(x[0])))
per = (len(rows) + n - 1) // n
for i in range(n):
    part = rows[i * per:(i + 1) * per]
    if not part:
        continue
    p = os.path.join(d, "chunk-%02d.tsv" % (i + 1))
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(k for k, _ in part) + "\n")
    print("  chunk-%02d: %d 行" % (i + 1, len(part)))
print("txt-miss 唯一 %d -> %d 块（%s）" % (len(rows), n, d))
