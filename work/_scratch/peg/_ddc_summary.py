# -*- coding: utf-8 -*-
"""统计 DDrawCompat 逐次调用日志（DDrawCompat-PeG030.log，17.7MB / 15 万行）：
   - 各调用类型的次数
   - BltFast / Blt 的 dst、src 矩形与 flags 的「形状」直方图
   - CreateSurface 的描述符形状直方图
   - SetColorKey 的 (surface, flags, key) 形状直方图
用法:  python work\peg\_ddc_summary.py [每类前 N 种形状]
"""
import io, re, sys, collections

LOG = r"D:\Program Files\PeG\DDrawCompat-PeG030.log"
SHOW = int(sys.argv[1]) if len(sys.argv) > 1 else 12

RE_CALL = re.compile(r"^[0-9a-f]{4} \d\d:\d\d:\d\d\.\d{3} > ([A-Za-z0-9_:]+)\((.*)\)\s*$")

call_cnt = collections.Counter()
shapes = collections.defaultdict(collections.Counter)


def norm(fn, args):
    a = args.strip()
    if fn in ("Blt", "BltFast"):
        # 保留最后一个 *{...} 块与数值参数，替换指针
        a = re.sub(r"&[0-9A-Fa-f]{6,8}", "&P", a)
        a = re.sub(r"0x[0-9A-Fa-f]{6,8}(?=[,})])", "0xP", a)
        return a
    if fn == "CreateSurface":
        a = re.sub(r"&[0-9A-Fa-f]{6,8}", "&P", a)
        return a
    if fn == "SetColorKey":
        a = re.sub(r"&[0-9A-Fa-f]{6,8}", "&P", a)
        return a
    return None


with io.open(LOG, encoding="utf-8", errors="replace") as f:
    for line in f:
        m = RE_CALL.match(line.rstrip("\n"))
        if not m:
            continue
        fn = m.group(1).split("::")[-1]
        call_cnt[fn] += 1
        key = norm(fn, m.group(2))
        if key is not None:
            shapes[fn][key] += 1

print("===== 调用次数（前 25）=====")
for fn, c in call_cnt.most_common(25):
    print("%-22s %7d" % (fn, c))

for fn in ("BltFast", "Blt", "CreateSurface", "SetColorKey", "Flip", "SetDisplayMode"):
    if fn not in shapes:
        continue
    print("\n===== %s 形状（共 %d 种，前 %d）=====" % (fn, len(shapes[fn]), SHOW))
    for k, c in shapes[fn].most_common(SHOW):
        print("%7d× %s" % (c, k[:230]))
