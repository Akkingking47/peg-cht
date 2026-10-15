# -*- coding: utf-8 -*-
r"""把 Clu 的 equip97.txt **整体**均分成 N 块（交子代理逐行判断：型号照抄、通用名译出）。

为什么整表交出去而不预分「型号/词类」：型号与词的边界靠启发式判不准
（`AB-41` 就被旧启发式误判成词类），**逐行判断交给人（子代理）更稳**；
POLICY 明确「整条是型号 ⇒ 照抄」，子代理有能力按行判。

用法: python make_equip_chunks.py [N]      # 默认 6
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
P = r"D:\OpenPG2\EFILE_Clu\equip97.txt"

n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 6
raw = open(P, "rb").read()
nl = "\r\n" if raw.count(b"\r\n") else "\n"
lines = raw.decode("cp1252").split(nl)
body = [l for l in lines if l.strip()]
d = os.path.join(HERE, "equip-chunks")
os.makedirs(d, exist_ok=True)
for f in os.listdir(d):
    os.remove(os.path.join(d, f))
per = (len(body) + n - 1) // n
for i in range(n):
    part = body[i * per:(i + 1) * per]
    if not part:
        continue
    p = os.path.join(d, "chunk-%02d.tsv" % (i + 1))
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(part) + "\n")
    print("  chunk-%02d: %d 行" % (i + 1, len(part)))
print("equip97.txt 非空行 %d -> %d 块（%s）" % (len(body), n, d))
