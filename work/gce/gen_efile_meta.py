# -*- coding: utf-8 -*-
r"""交付 GCE 的 `efile.txt` 元数据层（**机制 A**：只写 `TEXT-ZH\efile.txt`，原文零改动）。

机制依据（`MECHANICS.md` §15.1）：
  exe `.text` FO `0x4F6480` 的 `%sefile.txt` 与 `strings_efile.txt` **同一模板**
  （`%s`＝文件路径前缀）⇒ `efile.txt` 走与 `strings_efile.txt` 相同的目录解析，
  可在 LangDir（`TEXT-ZH`）下覆盖；且查找顺序是 **先 `.txt` 后 `.xml`**。
  **失败模式仅为「不显示中文」，不影响运行。**

**GCE 的特殊性**：根级**没有** `efile.txt`，只有 `efile.xml`。
先例＝`EFILE_BASEKORP`（根级同样只有 `.xml`）——它交付的是**把 `.xml` 的字段
逐行镜像成 `.txt`** 的覆盖层（去 XML 标记与样式表 PI、`</tag>` 闭合符省略），
并在最前面加两行样板注释。本脚本照此办理。

⚠️ 硬约束：
  - 标签**种类与顺序**必须与 `efile.xml` 逐行一致；
  - `<version>` / `<author>` / `<url>` **保留原文**（`<version>` 与存档兼容判断相关；
    作者名按既有 efile 惯例不译）；
  - 输出 GBK / 无 BOM / CRLF；先写 `.new` → 回读校验 → 才替换。
用法: python gen_efile_meta.py [--apply]   （默认干跑）
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

EF = r"D:\OpenPG2\EFILE_GCE"
SRC = os.path.join(EF, "efile.xml")
OUT = os.path.join(EF, "TEXT-ZH", "efile.txt")

BOILER = [
    "* This is an Efile description file",
    "* Please don't change the number and order of the lines.",
]

# 只译 `<title>` 与 `<description>`，其余 `<tag>` 行取值照抄
TRANSLATED = {
    "title": "GCE 西班牙内战装备文件",
    "description": "涵盖 1936 至 1939 年期间的西班牙内战装备文件。",
}


def main():
    do = "--apply" in sys.argv
    raw = open(SRC, "rb").read()
    txt = raw.decode("utf-8", "replace")
    # ⚠️ 不能整段用 `<(\w+)>(.*?)</\1>`——外层 `<efile>…</efile>` 会把全部字段吞成一个。
    #    改为**逐行**解析（xml 的字段就是一行一个）。
    fields = []
    for ln in txt.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^\s*<(\w+)>(.*?)</\1>\s*$", ln)
        if m:
            fields.append((m.group(1), m.group(2).strip()))
    print("efile.xml：%d B，字段 %d 个（%s）" % (len(raw), len(fields),
                                              ", ".join(t for t, _ in fields)))
    lines = list(BOILER)
    for tag, val in fields:
        val = val.strip()
        if tag in TRANSLATED:
            lines.append("<%s>%s" % (tag, TRANSLATED[tag]))
        else:
            lines.append("<%s>%s" % (tag, val))
    print("将写 %d 行：" % len(lines))
    for l in lines:
        print("   " + l)

    blob = ("\r\n".join(lines) + "\r\n").encode("gbk")
    print("输出 %d B（GBK）" % len(blob))
    if not do:
        print("(dry-run，未写)")
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".new"
    with open(tmp, "wb") as f:
        f.write(blob)
    back = open(tmp, "rb").read()
    ok = (back == blob and back[:3] != b"\xef\xbb\xbf"
          and back.count(b"\n") == back.count(b"\r\n")
          and back.decode("gbk").split("\r\n")[:-1] == lines)
    if not ok:
        os.remove(tmp)
        print("!! 回读校验失败，已回滚")
        return 1
    os.replace(tmp, OUT)
    print("原文 efile.xml md5 未变: %s" % (open(SRC, "rb").read() == raw))
    print("✅ 已写 %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
