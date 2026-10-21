# -*- coding: utf-8 -*-
"""破解 SSI .s16 RLE：以 ST030[0](压缩) vs ST030[1](未压缩) 为对照真值"""
import struct, os
from PIL import Image

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


DAT = os.path.join(GAME, "CWGEN.dat")
OUT = os.path.join(WS, "work", "peg", "s16")
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
                        (i,) + struct.unpack("<10I", f.read(40)))) for i in range(n)]
        base = f.tell()
    return idx, base

def blob(name, gi):
    idx, base = load(name)
    e = idx[gi]
    with open(DAT, "rb") as f:
        f.seek(base + e["starts"]); d = f.read(e["nbytes"])
    return e, d

# 真值
e1, d1 = blob("ST030.S16", 1)
truth = list(struct.unpack_from("<%dH" % (800 * 600), d1, 0))
e0, d0 = blob("ST030.S16", 0)
print("compressed bytes:", len(d0), " truth pixels:", len(truth))
print("first 64 bytes:", d0[:64].hex(" "))
print("as u16:", [hex(x) for x in struct.unpack_from("<32H", d0, 0)])

# 统计：真值的 run 结构
runs = []
cur = truth[0]; n = 1
for v in truth[1:]:
    if v == cur:
        n += 1
    else:
        runs.append((cur, n)); cur = v; n = 1
runs.append((cur, n))
print("true runs:", len(runs), " first 10:", [(hex(a), b) for a, b in runs[:10]])
print("distinct values:", len(set(truth)), "first row sample:", [hex(x) for x in truth[:10]])

# 候选方案：逐 u16 读，若 v & 0x8000 → 下一 u16 为重复次数(count)，颜色 = v & 0x7FFF
def dec_A(data, npix):
    out = []; i = 0; L = len(data)
    while i + 1 < L and len(out) < npix:
        v, = struct.unpack_from("<H", data, i); i += 2
        if v & 0x8000:
            if i + 1 >= L: break
            cnt2, = struct.unpack_from("<H", data, i); i += 2
            out.extend([v & 0x7FFF] * cnt2)
        else:
            out.append(v)
    return out

out = dec_A(d0, 800 * 600)
print("\nA: decoded", len(out), "/", len(truth))
k = min(len(out), len(truth))
mism = [i for i in range(k) if out[i] != truth[i]]
print("  mismatch count:", len(mism), "first few:", mism[:5])
if len(out) >= len(truth):
    print("  -> compare first mismatch idx:", mism[0] if mism else None)

# 候选 B：v & 0x8000 => count = (v & 0x7FFF) 为重复次数, 颜色 = 下一个 u16
def dec_B(data, npix):
    out = []; i = 0; L = len(data)
    while i + 1 < L and len(out) < npix:
        v, = struct.unpack_from("<H", data, i); i += 2
        if v & 0x8000:
            if i + 1 >= L: break
            c2, = struct.unpack_from("<H", data, i); i += 2
            out.extend([c2] * (v & 0x7FFF))
        else:
            out.append(v)
    return out

outB = dec_B(d0, 800 * 600)
kB = min(len(outB), len(truth))
mB = [i for i in range(kB) if outB[i] != truth[i]]
print("B: decoded", len(outB), "mismatch", len(mB))
