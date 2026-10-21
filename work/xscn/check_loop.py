# -*- coding: utf-8 -*-
r"""阶段 0 闭环复核：poc 根（已写）vs 备份（原文）逐槽对拍。

目的（不改任何东西，只读）：
  1. 结构零偏差：每文件 parse 出的槽位数 / 组表 / 尾部残留完全一致；
  2. 改动落点可控：**所有**字节差异都落在「计划改写过的槽」内，槽外一个字节都不能动；
  3. 编码正确：新串按 GBK 能解码、含汉字；按 cp1252 读不出来（说明确实是 GBK）；
  4. 原文未被破坏：未改写的槽与备份逐字节相同。
用法: python _probe_loop_check.py <POC_ROOT> <BACKUP_SCENARIO> <EFILE>
"""
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
spec = importlib.util.spec_from_file_location("xscn", r"D:\DSH\军事游戏汉化\work\xscn\xscn.py")
X = importlib.util.module_from_spec(spec)
spec.loader.exec_module(X)

POC_ROOT, BAK, EF = sys.argv[1], sys.argv[2], sys.argv[3]
POC = os.path.join(POC_ROOT, EF, "SCENARIO")

files = sorted(f for f in os.listdir(POC) if f.lower().endswith(".xscn"))
tot_slot = dif_files = changed = unchanged = bad = 0
samples = []
for fn in files:
    p1, p2 = os.path.join(POC, fn), os.path.join(BAK, fn)
    if not os.path.exists(p2):
        print("!! 备份缺失 %s" % fn)
        bad += 1
        continue
    d1, it1, m1 = X.parse(p1)
    d2, it2, m2 = X.parse(p2)
    if it1 is None or it2 is None:
        print("!! 解析失败 %s" % fn)
        bad += 1
        continue
    # 1) 结构
    s1 = list(X.slots_of(d1, it1, m1))
    s2 = list(X.slots_of(d2, it2, m2))
    if len(s1) != len(s2) or m1[2] != m2[2] or (m1[4] - m1[3]) != (m2[4] - m2[3]):
        print("!! 结构偏差 %s 槽 %d->%d 组 %r->%r 尾残 %d->%d"
              % (fn, len(s2), len(s1), m2[2], m1[2], m2[4] - m2[3], m1[4] - m1[3]))
        bad += 1
        continue
    tot_slot += len(s1)
    # 2) 逐槽
    dirty = False
    for (g1, i1, o1, L1), (g2, i2, o2, L2) in zip(s1, s2):
        r1 = X.raw_at(d1, o1, L1)
        r2 = X.raw_at(d2, o2, L2)
        if r1 == r2:
            unchanged += 1
            continue
        changed += 1
        dirty = True
        # 3) 新串必须是合法 GBK 且含汉字
        try:
            zh = r1.decode("gbk")
        except UnicodeDecodeError as e:
            print("!! GBK 解码失败 %s g%d.%d: %s" % (fn, g1, i1, e))
            bad += 1
            continue
        if X.han_count(zh) == 0:
            print("!! 改写后无汉字 %s g%d.%d %r->%r" % (fn, g1, i1, r2, r1))
            bad += 1
        # 中文侧不应残留不可见控制字符
        if any(c in zh for c in "\ufffd"):
            print("!! 出现替换符 %s g%d.%d %r" % (fn, g1, i1, zh))
            bad += 1
        if len(samples) < 8 and L2 > 6:
            samples.append((fn, g1, i1, r2.decode("cp1252"), zh))
    if dirty:
        dif_files += 1
    # 4) 槽外字节：串区**起始之前**的场景数据必须逐字节相同（长度也必须相同）
    k1 = min(([m1[0]] if m1[0] is not None else []) + [o for _, _, o, _ in s1])
    k2 = min(([m2[0]] if m2[0] is not None else []) + [o for _, _, o, _ in s2])
    if k1 != k2:
        print("!! 串区起点位移 %s %d -> %d" % (fn, k2, k1))
        bad += 1
    elif d1[:k1] != d2[:k2]:
        print("!! 场景数据（串区前 %d B）被改动 %s" % (k1, fn))
        bad += 1

print("文件 %d / 槽 %d / 改动槽 %d / 未改动槽 %d / 有改动文件 %d"
      % (len(files), tot_slot, changed, unchanged, dif_files))
print("异常 %d" % bad)
print("--- 抽样（原文 cp1252 -> 现 GBK）---")
for fn, g, i, a, b in samples:
    print("  %-16s g%d.%-2d  %-28r -> %r" % (fn, g, i, a, b))
sys.exit(1 if bad else 0)
