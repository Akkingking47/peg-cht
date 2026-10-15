# -*- coding: utf-8 -*-
r"""EFILE_Clu 的 `TEXT-ZH\efile.txt`（机制 A：引擎先读 .txt 后读 efile.xml）。

格式照 GCE / KAISER / COMWW2 先例：2 行注释 ＋ 与 `efile.xml` **同元素同顺序**的元素行
（`<tag>值`，无闭合标签）。出稿 GBK(936) / 无 BOM / CRLF。
`version` / `author` 照抄（人名与版本号不改），`url` 把 XML 实体 `&amp;` 还原成 `&`。

用法: python make_clu_efile_txt.py [--apply]
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
EFILE = r"D:\OpenPG2\EFILE_Clu"

LINES = [
    "* This is an Efile description file",
    "* Please don't change the number and order of the lines.",
    "<title>克卢二战装备文件",
    "<description>由 RSF 与阿德勒军团装备文件及其他特别构想汇编而成的二战装备文件。",
    "<version>03/11",
    "<author>Clu",
    "<url>http://www.panzercentral.com/forum/viewtopic.php?f=21&t=43562",
]


def main():
    apply = "--apply" in sys.argv
    blob = ("\r\n".join(LINES) + "\r\n").encode("gbk")
    print("行 %d / %d B" % (len(LINES), len(blob)))
    for l in blob.decode("gbk").split("\r\n")[:5]:
        print("   " + l)
    if not apply:
        print("(dry-run，加 --apply 落盘)")
        return 0
    d = os.path.join(EFILE, "TEXT-ZH")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "efile.txt")
    with open(p, "wb") as f:
        f.write(blob)
    back = open(p, "rb").read()
    assert back == blob and back[:3] != b"\xef\xbb\xbf", "回读不一致"
    assert back.count(b"\n") == back.count(b"\r\n"), "出现裸 LF"
    print("已写 %s（GBK / 无 BOM / CRLF，原文 efile.xml 未动）" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
