# -*- coding: utf-8 -*-
"""验证：layer_gate.load_overrides() 里 faction 登记表的键(c[0]=地名ID) 能否命中层表的 en。只读。"""
import os, io, collections

WS = r"D:\DSH\军事游戏汉化"
LAY = os.path.join(WS, "glossary", "layers")

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return b.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', 'replace').splitlines()

# 1) 照 layer_gate.load_overrides() 的方式读 faction 表（键 = c[0]，值 = c[vcol]）
fac_keys_p, fac_keys_o = {}, {}
for fn, d in (("faction-places.tsv", fac_keys_p), ("faction-ops.tsv", fac_keys_o)):
    p = os.path.join(LAY, fn)
    for l in read(p):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) > 3 and c[0].strip():
            d.setdefault(c[0].strip(), set()).update(
                x for x in c[3].replace("|", "\t").split("\t") if x)
print("faction-places 登记键 %d 个（例：%s）" % (len(fac_keys_p), list(fac_keys_p)[:12]))
print("faction-ops    登记键 %d 个（例：%s）" % (len(fac_keys_o), list(fac_keys_o)[:12]))

# 2) 层表里的 en 键
by = collections.defaultdict(list)
for fn in ("common-glossary.tsv", "series-glossary.tsv", "scope-glossary.tsv"):
    p = os.path.join(LAY, fn)
    if not os.path.isfile(p):
        continue
    for l in read(p):
        if l.startswith("#") or l.startswith("en\t"):
            continue
        c = l.rstrip("\n").split("\t")
        if len(c) >= 9:
            by[c[0]].append((c[1], c[8], c[3]))
print("三层主库 en 键 %d 个" % len(by))

# 3) 命中率
hit_p = [k for k in fac_keys_p if k in by]
hit_o = [k for k in fac_keys_o if k in by]
print("\n=== 门的键命中率 ===")
print("  faction-places: %d/%d 命中（%.0f%%）" % (len(hit_p), len(fac_keys_p),
      100.0 * len(hit_p) / max(1, len(fac_keys_p))))
print("  faction-ops   : %d/%d 命中（%.0f%%）" % (len(hit_o), len(fac_keys_o),
      100.0 * len(hit_o) / max(1, len(fac_keys_o))))
if hit_p:
    print("  命中的键：", hit_p[:20])
if hit_o:
    print("  命中的键：", hit_o[:20])

# 4) 那些"真正出现在层表里"的地名，主库里是什么值？
print("\n=== 抽查：分支涉及的几个地名，主库里的实际 en 键 ===")
for probe in ("Amur", "Kuri", "Toro", "Chio", "Morotsu", "Lodz", "Danzig", "Viipuri", "Kishinev"):
    ks = [k for k in by if k.lower() == probe.lower() or k.lower().startswith(probe.lower() + " ")]
    print("  %-12s 主库 en：%s" % (probe, ks[:5] if ks else "（无）"))

# 5) 合并后的"允许集合"是否把所有阵营/年代名揉在一起
print("\n=== 门里得到的『允许集合』示例（阵营/年代被压平）===")
for k in ("Amur", "Lodz", "Viipuri", "Tannenberg"):
    if k in fac_keys_p:
        print("  %-12s -> %s" % (k, sorted(fac_keys_p[k])))
