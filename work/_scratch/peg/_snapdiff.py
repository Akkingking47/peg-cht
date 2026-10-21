import glob, os
d = r"D:\DSH\军事游戏汉化\work\peg\out"
fs = sorted(glob.glob(os.path.join(d, "snap_*.bin")))
base = 0x600000
prev = None
for f in fs:
    cur = open(f, "rb").read()
    if prev is not None and len(prev) == len(cur):
        pages = {}
        for i in range(len(cur)):
            if prev[i] != cur[i]:
                pages[(base + i) >> 12] = pages.get((base + i) >> 12, 0) + 1
        top = sorted(pages.items(), key=lambda kv: -kv[1])[:6]
        print(os.path.basename(f), "total=%d" % sum(pages.values()),
              " ".join("%X:n%d" % (p << 12, c) for p, c in top))
    prev = cur
