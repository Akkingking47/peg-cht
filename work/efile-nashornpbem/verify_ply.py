# -*- coding: utf-8 -*-
"""独立验证 58 个 .ply 中文版：编码/换行/BOM/汉字数/两处一致性/星号行保留"""
import os, sys, hashlib

ROOT = r"D:/OpenPG2"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mk_ply_all as m

bad = []
ok = 0
rows = []
for (ef, fn) in sorted(m.DOCS):
    blobs = {}
    for path, tag in m.targets(ef, fn):
        if not os.path.exists(path):
            bad.append("%s/%s [%s] 文件不存在" % (ef, fn, tag)); continue
        d = open(path, "rb").read()
        blobs[tag] = (d, path)
    if len(blobs) != 2:
        continue
    for tag, (d, path) in blobs.items():
        if d[:3] == b"\xEF\xBB\xBF":
            bad.append("%s/%s [%s] 含 BOM" % (ef, fn, tag))
        lone = d.count(b"\n") - d.count(b"\r\n")
        if lone:
            bad.append("%s/%s [%s] 孤立 LF %d" % (ef, fn, tag, lone))
        try:
            s = d.decode("gbk")
        except Exception as e:
            bad.append("%s/%s [%s] GBK 解码失败 %s" % (ef, fn, tag, e)); continue
        han = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        if han == 0:
            bad.append("%s/%s [%s] 无汉字" % (ef, fn, tag))
    # 两处一致
    a = blobs["SCENARIO"][0]; b = blobs["TEXT-ZH"][0]
    same = (hashlib.md5(a).hexdigest() == hashlib.md5(b).hexdigest())
    if not same:
        bad.append("%s/%s 两处不一致" % (ef, fn))
    # 星号行
    s = a.decode("gbk")
    stars = [l for l in s.replace("\r\n", "\n").split("\n") if l.strip() and set(l.strip()) == {"*"}]
    # 与备份对比星号行
    bp = os.path.join(r"D:/DSH/军事游戏汉化/backup/ply-all-before", ef, "SCENARIO", fn)
    nstar_o = 0
    if os.path.exists(bp):
        so = open(bp, "rb").read().decode("latin-1")
        nstar_o = len([l for l in so.replace("\r\n", "\n").split("\n") if l.strip() and set(l.strip()) == {"*"}])
    if nstar_o != len(stars):
        bad.append("%s/%s 星号行数变化 %d -> %d" % (ef, fn, nstar_o, len(stars)))
    han = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
    rows.append((ef, fn, len(a), han, len(stars), same))
    ok += 1

print("验证文件数:", ok)
print("%-18s %-26s %7s %6s %5s %5s" % ("efile", "file", "bytes", "汉字", "星号", "两处同"))
for ef, fn, n, han, st, same in rows:
    print("%-18s %-26s %7d %6d %5d %5s" % (ef, fn, n, han, st, "Y" if same else "N"))
print()
if bad:
    print("!! 问题 %d 条：" % len(bad))
    for x in bad:
        print("   ", x)
else:
    print("=== 全部通过 ===")
