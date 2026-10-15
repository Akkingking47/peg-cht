# -*- coding: utf-8 -*-
r"""把 Clu 的 equip97.txt 粗分为「型号类（按口径保留）」与「纯词类（待译）」。

判据（保守，宁多译不漏译——最后仍由 `gen_root_zh.py` 的守卫兜）：
  · 去掉尾部 `[XX]` 标记与 `'39` 年份后，若**仍含数字**且形如型号（含 `-` `/` 或 字母+数字）
    ⇒ 型号类，保留原文（装备型号保留是 POLICY 硬规则）
  · 否则若以字母开头且无数字 ⇒ 纯词类，待译
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
P = r"D:\OpenPG2\EFILE_Clu\equip97.txt"
FLAG = re.compile(r"\s*\[[^\]]*\]\s*$")
# ⚠️ 年份剥离只对「空格 + 'NN」生效：旧版 `\s*'?\d{2}` 会把 `AB-41` 的 41 当成年份剥掉，
#    于是 `AB-41` 变成 `AB-` 被误判为「纯词类」。修：必须前面有空白，或带撇号。
YEAR = re.compile(r"(?:\s+'?\d{2}|\s*\(\d{2}\))\s*(\(.*\))?$")

lines = open(P, "rb").read().decode("cp1252").replace("\r\n", "\n").split("\n")
keep, word, other = [], [], []
for i, l in enumerate(lines, 1):
    s = l.strip()
    if not s or s.startswith("*"):
        continue
    core = YEAR.sub("", FLAG.sub("", s)).strip()
    if re.search(r"\d", core) and ("-" in core or "/" in core or re.match(r"^[A-Za-z]{1,5}\s?\d", core)):
        keep.append(s)
    elif re.match(r"^[A-Za-z\u00c0-\u024f]", core) and not re.search(r"\d", core):
        word.append(s)
    else:
        other.append(s)

print("总非空 %d | 型号类(保留) %d | 纯词类(待译) %d | 其他 %d"
      % (len(keep) + len(word) + len(other), len(keep), len(word), len(other)))
u = sorted(set(word))
print("纯词类唯一 %d" % len(u))
print("纯词类样例:", u[:14])
print("其他样例:", other[:14])
print("型号类样例:", keep[:8])
io.open(os.path.join(HERE, "equip-words.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(u) + "\n")
io.open(os.path.join(HERE, "equip-other.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(sorted(set(other))) + "\n")
print("已写 equip-words.txt / equip-other.txt")
