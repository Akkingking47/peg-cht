# -*- coding: utf-8 -*-
"""BASEKORP efile 元数据汉化（机制 A：`<efile>\\TEXT-ZH\\efile.txt`）。

依据（2026-09-29 取证）：
  · exe `.text` FO 0x4F6480 附近有 `%sefile.txt` / `%sefile.xml` 两条模板，
    紧邻 `"No efile.txt nor .xml found"`、`<author>`、`Version: `、`Efile：`（GBK）。
  · `MECHANICS.md` §15.1：`strings_efile.txt` 就是由 **同一条 `%sefile.txt` 模板** 拼出的
    （`%s` 是文件名前缀 `strings_`）⇒ `efile.txt` 与 `strings_efile.txt` **同函数、同目录**。
  · 既然 `TEXT-ZH\\strings_efile.txt` 是已验证生效的覆盖层（本工程 6 个 efile 均如此交付），
    `TEXT-ZH\\efile.txt` 走同一目录解析。

**安全边界（"不影响游戏运行"）**：
  · 根级 `efile.xml` **一字不动** ⇒ 即使引擎不读此覆盖层，也只是回落英文，游戏照常。
  · `<version>` 保持原文 —— `Settings.cfg` 有 `EVersion` 键，版本串可能与存档兼容性判断相关。
  · `<author>` / `<url>` 保持原文（人名 / URL）。
  · 行数与行序**严格照 `efile.txt` 规范**（文件自述「don't change the number and order」）。
  · 输出 GBK(936) / 无 BOM / CRLF；行数与原文侧 efile.txt 规范一致（7 行）。
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

EFILE = r"D:\OpenPG2\EFILE_BASEKORP"
DST = os.path.join(EFILE, "TEXT-ZH", "efile.txt")

ITEMS = [
    ("<title>", "Open BaseKorp 装备文件"),
    ("<description>",
     "Basekorps 二战装备文件的开放化版本。BKefile 与 AdlerKorp 大多兼容，"
     "但包含一些额外单位，并加入了本人的构想。"),
    ("<version>", "Aug 2019"),          # 保持原文（与 Settings.cfg EVersion 相关）
    ("<author>", "Brian Gosley"),
    ("<url>", "http://www.panzercentral.com/forum/viewtopic.php?f=132&amp;t=46498"),
]

lines = [
    "* This is an Efile description file",
    "* Please don't change the number and order of the lines.",
] + ["%s%s" % (t, v) for t, v in ITEMS]
text = "\r\n".join(lines) + "\r\n"

blob = text.encode("gbk")           # 顺带做 GBK 前置校验
assert blob[:3] != b"\xef\xbb\xbf"
assert blob.count(b"\n") == blob.count(b"\r\n") == 7

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "wb") as f:
    f.write(blob)

back = open(DST, "rb").read()
assert back == blob
print("wrote", DST)
print("  %d B | %d 行 | CRLF %d | BOM %s | 汉字 %d"
      % (len(back), back.count(b"\r\n"), back.count(b"\r\n"),
         back[:3] == b"\xef\xbb\xbf",
         sum(1 for c in back.decode("gbk") if "\u4e00" <= c <= "\u9fff")))
print("--- 回读 ---")
for i, l in enumerate(back.decode("gbk").split("\r\n"), 1):
    print("%2d|%s" % (i, l))
print()
# 根级原文侧自检：必须未改动
src = os.path.join(EFILE, "efile.xml")
b = open(src, "rb").read()
print("根级 efile.xml %d B | 非ASCII %d（应为 0，证明未改动）"
      % (len(b), sum(1 for c in b if c >= 0x80)))
