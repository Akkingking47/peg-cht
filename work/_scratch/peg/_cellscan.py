import glob, os
d = r"D:\DSH\军事游戏汉化\work\peg\out"
fs = sorted(glob.glob(os.path.join(d, "snap_*.bin")))[:10]
CELL, STRIDE, N = 0x6268A0, 65, 400
print("offset : nonzero-cell counts per snapshot (snap order)")
rows = {}
data = []
for f in fs:
    b = open(f, "rb").read()
    base = 0x600000
    off = CELL - base
    chunk = b[off:off + STRIDE * N]
    data.append((os.path.basename(f), chunk))
for k in range(STRIDE):
    counts = []
    for _, c in data:
        counts.append(sum(1 for g in range(N) if c[g * STRIDE + k]))
    rows[k] = counts
for k in range(STRIDE):
    c = rows[k]
    print("%02X: %s" % (k, " ".join("%3d" % v for v in c)))
