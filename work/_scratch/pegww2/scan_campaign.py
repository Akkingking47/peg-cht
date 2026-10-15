#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位：战役层（.cam）与仍残留的「名栏=段落」问题。

用户截图暴露两类新问题：
  ① 场景选择画面里**仍有**长段落当名字（我的 >120 字符阈值太高，漏了较短的段落）
  ② **战役选择画面**（另一个层）也有同样问题，且「达斯帝国师」还在（我的修复没碰到这层）
"""
import os
import re

G = r"D:\Program Files\PeG-WW2"
TARGETS = ["达斯帝国师", "这次失败绝不可容忍", "消息来自", "克列迪道山口", "帝国师"]

print("=" * 96)
print("① 目标串出现在哪些文件里（含行号）")
print("=" * 96)
for root, dirs, files in os.walk(G):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            b = open(p, "rb").read()
        except Exception:
            continue
        try:
            t = b.decode("gbk")
        except UnicodeDecodeError:
            t = b.decode("latin-1")
        hits = [s for s in TARGETS if s in t]
        if hits:
            rel = os.path.relpath(p, G)
            for i, line in enumerate(re.split(r"\r\n|\r|\n", t)):
                for s in hits:
                    if s in line:
                        print(f"  {rel:44s} 行{i:<4d} [{s}] {line.strip()[:66]}")
                        break

print()
print("=" * 96)
print("② 战役层文件清单（.cam / .CAM）与前几行")
print("=" * 96)
cams = []
for root, dirs, files in os.walk(G):
    for fn in files:
        if fn.lower().endswith(".cam"):
            cams.append(os.path.join(root, fn))
print(f"  共 {len(cams)} 个 .cam 文件")
for p in sorted(cams)[:6]:
    print(f"  --- {os.path.relpath(p, G)} ({os.path.getsize(p)} B)")
    b = open(p, "rb").read()
    try:
        t = b.decode("latin-1")
    except Exception:
        continue
    ls = [x for x in re.split(r"\r\n|\r|\n", t) if x.strip()][:6]
    for i, l in enumerate(ls):
        print(f"       行{i}: {l[:88]!r}")
