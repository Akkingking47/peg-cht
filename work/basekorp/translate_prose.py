# -*- coding: utf-8 -*-
"""BASEKORP 散文层机器翻译器（行级确定性替换）。

优先级：zh-r00 专用 > prose_dict 全局模板 > txt-precedent 先例 > 原文（保留）。
- 空行、装饰行（全 _*=.¯ 等）原样保留。
- 已译行用 gbk 写出；未译英文行保留原始 cp1252 字节（避免重编码丢字符）。
- 判定每个代表文件是否「完整翻译(full)」：所有非空非装饰行都有译文才标记。
- 产出：out/<rep>（字节文件）、deploy_manifest.tsv（full rep + 组内文件）、llm-todo.tsv（未译唯一行）。
"""
import os
import io
import re
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = r"D:\OpenPG2"
SC = os.path.join(GAME, "EFILE_BASEKORP", "SCENARIO")
OUT = os.path.join(HERE, "out_prose")
os.makedirs(OUT, exist_ok=True)


def gbk_safe(s):
    """gbk 编码；无法 gbk 编码的字符（¯/®/© 等装饰与符号）按 cp1252 字节原样保留——
    因为游戏渲染中文层时把这些单字节当作 cp1252 符号显示，
    与 DEC 原样保留的纯装饰行（0xAF→¯）一致，避免 encode('gbk','replace') 把它们写成 '?'。"""
    out = bytearray()
    for ch in s:
        try:
            out += ch.encode("gbk")
        except UnicodeEncodeError:
            try:
                out += ch.encode("cp1252")
            except UnicodeEncodeError:
                out += b"?"
    return bytes(out)


def load_map(path, ncols=2):
    d = {}
    if not os.path.exists(path):
        return d
    with io.open(path, encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            # 首字段(src)可能含 tab，故从右取 ncols-1 个 tab 作分隔
            p = ln.rstrip("\r\n").rsplit("\t", ncols - 1)
            if len(p) >= ncols:
                d[p[0].rstrip()] = p[1]
    return d


pre = load_map(os.path.join(HERE, "txt-precedent.tsv"), ncols=4)
pd = load_map(os.path.join(HERE, "prose_dict.tsv"), ncols=2)

# —— LLM 专项译文层（BASEKORP 本 efile 的逐块 LLM 译文，可信度高于跨 efile 先例）——
# 加载所有 zh-<block>.tsv（不含 zh-r00.tsv，后者为 per-file 专用）。
import glob
llm = {}
for _fp in glob.glob(os.path.join(HERE, "zh-*.tsv")):
    if os.path.basename(_fp) == "zh-r00.tsv":
        continue
    with io.open(_fp, encoding="utf-8") as _f:
        next(_f, None)
        for _ln in _f:
            _p = _ln.rstrip("\r\n").rsplit("\t", 1)
            if len(_p) >= 2:
                llm[_p[0].rstrip()] = _p[1]

r00 = collections.defaultdict(dict)
if os.path.exists(os.path.join(HERE, "zh-r00.tsv")):
    with io.open(os.path.join(HERE, "zh-r00.tsv"), encoding="utf-8") as f:
        next(f, None)
        for ln in f:
            p = ln.rstrip("\r\n").split("\t")
            if len(p) >= 3:
                r00[p[0]][p[1].rstrip()] = p[2]

DEC = re.compile(r"^[\s_*=.®¯Â\-]+$")

reps = []
with io.open(os.path.join(HERE, "rep-list.tsv"), encoding="utf-8") as f:
    next(f, None)
    for ln in f:
        p = ln.rstrip("\r\n").split("\t")
        if len(p) >= 7:
            reps.append((p[1], p[3], p[6]))  # rep, kind, files

tot_rep = tot_lines = tot_chars = 0
machine_lines = machine_chars = r00_lines = llm_lines = 0
unt = collections.Counter()
full_files = []
manifest = []
for rep, kind, files in reps:
    if kind != "prose":
        continue
    p = os.path.join(SC, rep)
    if not os.path.exists(p):
        continue
    raw = open(p, "rb").read()
    parts = raw.split(b"\r\n")
    out = []
    full = True
    for lb in parts:
        line = lb.decode("cp1252")
        key = line.rstrip()
        if not key.strip():
            out.append(lb)
            continue
        if DEC.match(key):
            out.append(lb)
            continue
        dst = None
        if rep in r00 and key in r00[rep]:
            dst = r00[rep][key]
            r00_lines += 1
        elif key in pd:
            dst = pd[key]
        elif key in llm:
            dst = llm[key]
            llm_lines += 1
        elif line in pre:
            dst = pre[line]
        if dst is not None:
            out.append(gbk_safe(dst))
            machine_lines += 1
            machine_chars += len(line)
        else:
            out.append(lb)
            unt[key] += 1
            full = False
    tot_rep += 1
    tot_lines += len(parts)
    tot_chars += sum(len(x) for x in parts)
    new = b"\r\n".join(out)
    if new != raw:
        with open(os.path.join(OUT, rep), "wb") as w:
            w.write(new)
        if full:
            full_files.append(rep)
            manifest.append((rep, files))

with io.open(os.path.join(HERE, "deploy_manifest.tsv"), "w",
             encoding="utf-8", newline="\r\n") as f:
    f.write("rep\tfiles\r\n")
    for r, fs in manifest:
        f.write("%s\t%s\r\n" % (r, fs))
with io.open(os.path.join(HERE, "llm-todo.tsv"), "w",
             encoding="utf-8", newline="\r\n") as f:
    f.write("src\tn\r\n")
    for k, v in sorted(unt.items(), key=lambda x: -x[1]):
        f.write("%s\t%d\r\n" % (k, v))

print("散文代表文件 %d / 行 %d / 字符 %d" % (tot_rep, tot_lines, tot_chars))
print("机器层命中行 %d / 字符 %d (%.1f%%)" % (
    machine_lines, machine_chars, 100.0 * machine_chars / tot_chars))
print("  r00 专用命中 %d 行 / llm 专项命中 %d 行" % (r00_lines, llm_lines))
print("未译唯一行 %d / 实例 %d / 字符 %d" % (
    len(unt), sum(unt.values()), sum(len(k) * v for k, v in unt.items())))
print("完整翻译(full)文件 %d -> deploy_manifest.tsv" % len(full_files))
for r in full_files:
    print("   ", r)
