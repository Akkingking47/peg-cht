# -*- coding: utf-8 -*-
"""ATOMIC 场景 .txt 译文批次合并 + 结构校验（不采信子代理自述）"""
import os, sys, json

OUT = r"D:/DSH/军事游戏汉化/work/atomic/scn"
SRC = r"D:/OpenPG2/EFILE_ATOMIC/SCENARIO"

def read_b(path):
    return open(path, 'rb').read()

def split_files(raw):
    """按 @@FILE 头切分；返回 [(head, body_bytes)]，head 不含 CR/LF"""
    parts = []
    idx = 0
    while True:
        j = raw.find(b'@@FILE\t', idx)
        if j < 0: break
        k = raw.find(b'\n', j)
        head = raw[j:k].rstrip(b'\r')
        nxt = raw.find(b'@@FILE\t', k)
        body = raw[k+1:] if nxt < 0 else raw[k+1:nxt]
        parts.append((head, body, j))
        if nxt < 0: break
        idx = nxt
    return parts

report = []
total_files = 0
mis = []
for i in range(1, 13):
    ip = os.path.join(OUT, f"in-{i:02d}.txt")
    op = os.path.join(OUT, f"out-{i:02d}.txt")
    if not os.path.exists(op):
        report.append(f"batch {i:02d}: MISSING out"); continue
    ib = open(ip,'rb').read()
    ob = open(op,'rb').read()
    if ob[:3] == b'\xef\xbb\xbf':
        mis.append(f"batch {i:02d}: BOM!")
    iparts = split_files(ib)
    oparts = split_files(ob)
    n_nl_i = ib.count(b'\n'); n_nl_o = ob.count(b'\n')
    if n_nl_i != n_nl_o:
        mis.append(f"batch {i:02d}: \\n count {n_nl_i} != {n_nl_o}")
    if len(iparts) != len(oparts):
        mis.append(f"batch {i:02d}: file count {len(iparts)} != {len(oparts)}")
    # head identical
    badh = 0
    for (ih, ibody, _), (oh, obody, _2) in zip(iparts, oparts):
        if ih != oh: badh += 1
    if badh: mis.append(f"batch {i:02d}: {badh} head mismatch")
    # CR structure per file: count \r\n in body
    badcr = 0; badlines = 0
    for (ih, ibody, _), (oh, obody, _2) in zip(iparts, oparts):
        if ibody.count(b'\r\n') != obody.count(b'\r\n'): badcr += 1
        if ibody.count(b'\n') != obody.count(b'\n'): badlines += 1
    if badcr: mis.append(f"batch {i:02d}: {badcr} files CRLF mismatch")
    if badlines: mis.append(f"batch {i:02d}: {badlines} files \\n-in-body mismatch")
    total_files += len(oparts)
    report.append(f"batch {i:02d}: {len(oparts)} files, \\n {n_nl_i}/{n_nl_o}, CRLF ok={badcr==0}, head ok={badh==0}")

print('\n'.join(report))
print("\nTOTAL FILES:", total_files)
print("\n### MISMATCHES ###")
if mis:
    for m in mis: print(" !", m)
else:
    print("  (none)")
