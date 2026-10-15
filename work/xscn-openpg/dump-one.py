import pathlib
import sys


def parse(p):
    b = p.read_bytes()
    st = b.find(b"<N:")
    g = b.find(b">", st)
    off = g + 1
    L = b[off] | (b[off + 1] << 8)
    title = b[off + 2:off + 2 + L].decode("gbk")
    off += 2 + L
    out, gi = [], 0
    while off + 2 <= len(b):
        cnt = b[off] | (b[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        row = []
        for k in range(cnt):
            L = b[off] | (b[off + 1] << 8)
            row.append(b[off + 2:off + 2 + L].decode("gbk"))
            off += 2 + L
        out.append(row)
        gi += 1
    return title, out


for name in sys.argv[1:]:
    p = pathlib.Path(r"D:\OpenPG2\EFILE_OPENPG\SCENARIO") / name
    title, groups = parse(p)
    print("== %s  标题: %s ==" % (name, title))
    for i, row in enumerate(groups):
        print("  组%d (%d 条): %s" % (i, len(row), " / ".join(row)))
    print()
