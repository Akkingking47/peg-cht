"""独立验证 EFILE_OPENPG 的 .xscn 写入结果。

不依赖 xscn-patch.ps1 的自我校验，另用一份独立解析器对比：
  1. 每个文件的条目数 / 分组数 == 官方原始备份
  2. 尾部剩余字节与原始一致
  3. 标题与内容确为中文（GBK）
"""
import pathlib
import re

NEW = pathlib.Path(r"D:\OpenPG2\EFILE_OPENPG\SCENARIO")
ORIG = pathlib.Path(r"D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OPENPG\SCENARIO")


def parse(p):
    b = p.read_bytes()
    st = b.find(b"<N:")
    if st < 0:
        return None
    g = b.find(b">", st)
    off = g + 1
    L = b[off] | (b[off + 1] << 8)
    tbytes = b[off + 2:off + 2 + L]
    off += 2 + L
    items, groups, gi = [], [], 0
    while off + 2 <= len(b):
        cnt = b[off] | (b[off + 1] << 8)
        if cnt <= 0 or cnt > 4000:
            break
        off += 2
        ok = True
        for k in range(cnt):
            if off + 2 > len(b):
                ok = False
                break
            L = b[off] | (b[off + 1] << 8)
            if L <= 0 or off + 2 + L > len(b):
                ok = False
                break
            items.append(b[off + 2:off + 2 + L])
            off += 2 + L
        if not ok:
            break
        groups.append(cnt)
        gi += 1
    return dict(size=len(b), title=tbytes, items=items, groups=groups,
                parsedEnd=off, nchars=len(b) - st)


class L1:
    @staticmethod
    def dec(b):
        return b.decode("cp1252")


class GBK:
    @staticmethod
    def dec(b):
        try:
            return b.decode("gbk")
        except UnicodeDecodeError:
            return b.decode("cp1252")


files = sorted(NEW.glob("*.xscn"))
print("待验证文件：", len(files))

bad_count, bad_tail, missing_orig = [], [], []
total_items = 0
zh_items = 0
sample_titles = []
for p in files:
    o = ORIG / p.name
    if not o.exists():
        missing_orig.append(p.name)
        continue
    n, r = parse(p), parse(o)
    total_items += len(n["items"])
    if len(n["items"]) != len(r["items"]):
        bad_count.append((p.name, len(r["items"]), len(n["items"])))
    if n["groups"] != r["groups"]:
        bad_count.append((p.name + " (groups)", r["groups"], n["groups"]))
    if (n["size"] - n["parsedEnd"]) != (r["size"] - r["parsedEnd"]):
        bad_tail.append((p.name, r["size"] - r["parsedEnd"], n["size"] - n["parsedEnd"]))
    # 统计已中文化的条目
    for it in n["items"]:
        if re.search(rb"[\x81-\xfe][\x40-\xfe]", it):
            zh_items += 1
    if len(sample_titles) < 12:
        sample_titles.append((p.name, GBK.dec(n["title"]), L1.dec(r["title"])))

print("原始备份缺失     :", len(missing_orig))
print("条目数/分组数不符:", len(bad_count))
for b in bad_count[:15]:
    print("    ", b)
print("尾部剩余不一致   :", len(bad_tail))
for b in bad_tail[:15]:
    print("    ", b)
print()
print("条目总数         :", total_items)
print("含 GBK 双字节的条目:", zh_items, "(%.1f%%)" % (100.0 * zh_items / max(1, total_items)))
print()
print("标题抽样（原文 -> 译文）:")
for fn, t, o in sample_titles:
    print("    %-22s %-26s -> %s" % (fn, o, t))
