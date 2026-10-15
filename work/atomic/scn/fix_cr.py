# -*- coding: utf-8 -*-
"""b11/b12 结构重建：以输入为骨架，段内行数/CR 完全跟随输入，行内容取译文。

分段依据：@@FILE 行。重建流程：
  - 取输入各段行数组（含 header 行）
  - 取输出各段行数组（按输出自己的 header 位置切）
  - 段数须相同、header 文本须相同
  - 输出段行数不足/过多 → 调整尾部空行
  - 输出行内容按 index 对位；多出的输出行丢弃、缺的补空
  - CR 标记一律取输入
"""
import os, sys

OUT = r"D:/DSH/军事游戏汉化/work/atomic/scn"

def read_lines(raw):
    has_trail = raw.endswith(b'\n')
    body = raw[:-1] if has_trail else raw
    lines = []
    for p in body.split(b'\n'):
        if p.endswith(b'\r'): lines.append((p[:-1], True))
        else: lines.append((p, False))
    return lines, has_trail

def segments(lines):
    """按 @@FILE 行切段，返回 [ (start, end) ]"""
    hs = [k for k, (c, _) in enumerate(lines) if c.startswith(b'@@FILE\t')]
    return [(hs[k], hs[k+1] if k+1 < len(hs) else len(lines)) for k in range(len(hs))]

def fix(i):
    iL, itr = read_lines(open(os.path.join(OUT, f"in-{i:02d}.txt"), 'rb').read())
    oL, otr = read_lines(open(os.path.join(OUT, f"out-{i:02d}.txt"), 'rb').read())
    iseg = segments(iL); oseg = segments(oL)
    assert len(iseg) == len(oseg), (i, len(iseg), len(oseg))
    new = []
    notes = []
    for (a, b), (c, d) in zip(iseg, oseg):
        ih = iL[a][0]; oh = oL[c][0]
        assert ih == oh, (i, ih[:40], oh[:40])
        irows = iL[a:b]          # 含 header
        orows = oL[c:d]          # 含 header
        name = ih.split(b'\t')[1].decode()
        if len(irows) != len(orows):
            # 调整：找输出内容行（非尾部空行）数量，与输入对齐
            def content_len(rows, base):
                k = len(rows)
                while k > base + 1 and rows[k-1][0].strip() == b'': k -= 1
                return k
            ci = content_len(irows, 0)
            co = content_len(orows, 0)
            # 以输入为骨架：保留 orows 前 co 行内容（header + 内容），补/删空行到 len(irows)
            orows = orows[:co] + [(b'', True)] * (len(irows) - co)
            notes.append(f"{name}: {len(irows)}<={len(orows)} (ci={ci},co={co})")
        # 重建：行内容取 orows（若短则空），CR 取 irows
        seg_out = []
        for k in range(len(irows)):
            icore, icr = irows[k]
            ocore = orows[k][0] if k < len(orows) else b''
            # header 行必须原样
            if icore.startswith(b'@@FILE\t'): ocore = icore
            seg_out.append((ocore, icr))
        new.extend(seg_out)
    # 写回
    res = bytearray()
    for k, (core, hc) in enumerate(new):
        res += core + (b'\r' if hc else b'')
        if k != len(new) - 1: res += b'\n'
    if itr: res += b'\n'
    open(os.path.join(OUT, f"out-{i:02d}.txt"), 'wb').write(bytes(res))
    return notes

for i in (11, 12):
    n = fix(i)
    print(f"batch {i:02d}: {len(n)} seg adjustments")
    for x in n[:5]: print("   ", x)
