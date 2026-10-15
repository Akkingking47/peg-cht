# -*- coding: utf-8 -*-
"""交付 COMWW2 的 `efile.txt` 元数据层（**机制 A**：只写 `TEXT-ZH\\efile.txt`，零改动原文）。

机制依据（`MECHANICS.md` §15.1 / BASEKORP 先例）：
  exe `.text` FO `0x4F6480` 的 `%sefile.txt` 与 `strings_efile.txt` **同一模板**
  （`%s`＝文件路径前缀）⇒ `efile.txt` 走与 `strings_efile.txt` 相同的目录解析，
  可在 LangDir（`TEXT-ZH`）下覆盖。**失败模式仅为「不显示中文」，不影响运行。**

⚠️ 硬约束：
  - 行数与行序必须与根级 `efile.txt` **完全一致**（文件首行明写 "don't change the number
    and order of the lines"）⇒ COMWW2 是 6 行（无 `<url>`），BASEKORP 是 7 行。
  - `<version>` 保留原文（`Settings.cfg` 有 `EVersion` 键，可能与存档兼容判断相关）。
  - `<author>` 保留原文（标准译名库 `MG43→MG43` 恒等，且既有 5 个 efile 惯例）。
  - 输出 GBK / 无 BOM / CRLF；先写 .new → 回读校验 → 才替换正式文件。
用法: python gen_efile_meta.py [--apply]   （默认干跑）
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
EF = r"D:\OpenPG2\EFILE_COMWW2"
SRC = os.path.join(EF, "efile.txt")
OUT = os.path.join(EF, "TEXT-ZH", "efile.txt")

# 与根级 efile.txt 逐行对应（注释行照抄；只有 title / description 译）
LINES = [
    "* This is an Efile description file",
    "* Please don't change the number and order of the lines.",
    "<title>OpenComposite 综合装备文件",
    "<description>为 Open General 改编的综合装备文件。",
    "<version>1.02F",
    "<author>MG43",
]


def main():
    do = "--apply" in sys.argv
    raw = open(SRC, "rb").read()
    src_all = raw.decode("cp1252", "replace").split("\r\n")
    # 末尾的 CRLF 会切出一个空段 ⇒ 只取内容行
    src_txt = src_all[:-1] if src_all and src_all[-1] == "" else src_all
    has_trail = raw.endswith(b"\r\n")
    print("根级 %s：%d B，内容行 %d，尾部 CRLF=%s" % (SRC, len(raw), len(src_txt), has_trail))
    print("根级内容行 %d | 待写内容行 %d" % (len(src_txt), len(LINES)))
    if len(src_txt) != len(LINES):
        print("!! 行数不符（根级 %d vs 待写 %d）—— 禁止写入" % (len(src_txt), len(LINES)))
        return 1
    # 结构对拍：非注释行（`<tag>...`）的标签必须逐行一致
    def tag(l):
        return l.split(">")[0] + ">" if l.startswith("<") else None
    st = [tag(l) for l in src_txt if tag(l)]
    ot = [tag(l) for l in LINES if tag(l)]
    if st != ot:
        print("!! 标签序列不符: %s vs %s" % (st, ot))
        return 1
    print("标签序列一致 ✓  %s" % ot)
    # 注释行必须逐字照抄（引擎可能按行识别）
    for i, (a, b) in enumerate(zip(src_txt, LINES)):
        if a.startswith("*") or b.startswith("*"):
            if a != b:
                print("!! 第 %d 行注释不一致：%r vs %r" % (i + 1, a, b))
                return 1
    print("注释行逐字一致 ✓")

    blob = ("\r\n".join(LINES) + "\r\n").encode("gbk")
    print("输出 %d B（GBK）" % len(blob))
    if not do:
        print("--- 内容 ---")
        for l in LINES:
            print("   " + l)
        print("(dry-run，未写)")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".new"
    with open(tmp, "wb") as f:
        f.write(blob)
    back = open(tmp, "rb").read()
    ok = (back == blob and back[:3] != b"\xef\xbb\xbf"
          and back.count(b"\n") == back.count(b"\r\n")
          and back.decode("gbk").split("\r\n")[:-1] == LINES)
    if not ok:
        os.remove(tmp)
        print("!! 回读校验失败，已回滚")
        return 1
    os.replace(tmp, OUT)
    # 终检：原文未被改动
    after = open(SRC, "rb").read()
    print("原文 md5 未变: %s" % (after == raw))
    print("✅ 已写 %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
