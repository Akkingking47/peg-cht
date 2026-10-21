# -*- coding: utf-8 -*-
"""把 `work\\gus_zx\\zh` 的 118 个中文场景文本落盘为 GBK 覆盖层。

目标目录：`D:\\OpenGeneral\\EFILE_GUS_Zx\\TEXT-ZH\\SCENARIO\\`
（引擎按 `UI_Lang=strings-zh` 的 `zh` 后缀读 `TEXT-zh\\SCENARIO\\<name>.txt`）
**`SCENARIO\\` 原文目录不动**，因此无需备份。
写后逐文件 GBK 回读比对，必须与源 UTF-8 文本完全一致。
"""
import os
import sys

ZH = r"D:\DSH\军事游戏汉化\work\gus_zx\zh"
DST = r"D:\OpenGeneral\EFILE_GUS_Zx\TEXT-ZH\SCENARIO"


def main():
    os.makedirs(DST, exist_ok=True)
    ok = bad = 0
    total = 0
    for n in sorted(os.listdir(ZH)):
        t = open(os.path.join(ZH, n), encoding="utf-8", newline="").read()
        try:
            b = t.encode("gbk")
        except UnicodeEncodeError as e:
            print("[X] %-22s GBK 编码失败: %s" % (n, e))
            bad += 1
            continue
        p = os.path.join(DST, n)
        with open(p, "wb") as f:
            f.write(b)
        back = open(p, "rb").read().decode("gbk")
        if back != t:
            print("[X] %-22s 回读不一致" % n)
            bad += 1
        else:
            ok += 1
            total += len(b)
    print("\n落盘 %s" % DST)
    print("成功 %d 个 / 失败 %d 个，合计 %d 字节" % (ok, bad, total))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
