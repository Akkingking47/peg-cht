# -*- coding: utf-8 -*-
"""s16 渲染 + RLE 破解尝试"""
import struct, os
from PIL import Image

DAT = r"D:\Program Files\PeG\CWGEN.dat"
OUT = r"D:\DSH\军事游戏汉化\work\peg\s16"
os.makedirs(OUT, exist_ok=True)

cnt, _ = struct.unpack("<II", open(DAT, "rb").read(8))
with open(DAT, "rb") as f:
    f.seek(8)
    ENT = {}
    for _ in range(cnt):
        r = f.read(17)
        ENT[r[:13].split(b"\x00")[0].decode("latin-1").upper()] = struct.unpack("<I", r[13:17])[0]

def load(name):
    with open(DAT, "rb") as f:
        f.seek(ENT[name])
        n, = struct.unpack("<I", f.read(4))
        idx = [dict(zip("i w h sx sy fw fh starts nbytes comp load".split(),
                        (i,) + struct.unpack("<10I", f.read(40))))
               for i in range(n)]
        base = f.tell()
        return idx, base

def rgb565(v):
    return ((v >> 11) << 3, ((v >> 5) & 0x3F) << 2, (v & 0x1F) << 3)

def write_png(px, W, H, tag, scale=1):
    img = Image.new("RGB", (W, H))
    img.putdata([rgb565(v) for v in px])
    if scale != 1:
        img = img.resize((W * scale, H * scale), Image.NEAREST)
    fn = os.path.join(OUT, tag + ".png")
    img.save(fn)
    return fn

def decode_rle(data, npix):
    """尝试多种 RLE 方案"""
    out = []
    i = 0
    L = len(data)
    while i + 1 < L and len(out) < npix:
        v, = struct.unpack_from("<H", data, i); i += 2
        out.append(v)
        c = 1
        # 方案A: 高位置1 => 下一 u16 是重复次数
        if v & 0x8000 and i + 1 < L:
            n, = struct.unpack_from("<H", data, i); i += 2
            out.extend([v & 0x7FFF] * (n - 1))
    return out

def raw(data, npix):
    return list(struct.unpack_from("<%dH" % npix, data, 0))

print("=== ST030[1] 未压缩 800x600 ===")
idx, base = load("ST030.S16")
e = idx[1]
with open(DAT, "rb") as f:
    f.seek(base + e["starts"]); data = f.read(e["nbytes"])
fig = raw(data, 800 * 600)
print("   wrote", write_png(fig, 800, 600, "ST030_g1_full", 1))

print("=== 尝试 RLE ===")
for nm, gi in [("BUTTN30.S16", 0), ("MAINBAR.S16", 0), ("MAINBAR.S16", 7), ("STRNGM.S16", 0)]:
    idx, base = load(nm)
    e = idx[gi]
    with open(DAT, "rb") as f:
        f.seek(base + e["starts"]); data = f.read(e["nbytes"])
    W, H = e["fw"], e["fh"]
    px = decode_rle(data, W * H)
    print(f"  {nm}[{gi}] {W}x{H} nbytes={e['nbytes']} -> decoded {len(px)} px")
    if len(px) >= W * H:
        write_png(px[:W * H], W, H, f"{nm}_{gi}_rle", 3)
    else:
        write_png(px + [0] * (W * H - len(px)), W, H, f"{nm}_{gi}_rle_partial", 3)
print("done")
