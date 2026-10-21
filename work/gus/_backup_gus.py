# -*- coding: utf-8 -*-
"""
阶段 4 写前独立备份：EFILE_GUS 的 SCENARIO\*.xscn 与 SCENARIO\*.txt。

硬约束（docs\\73 / goal）：覆盖任何原文之前，必须用独立命令完成备份并验 MD5。
本次只备份将被改动的两类文件；TEXT-ZH\\ 与根级 5 件阶段 1 已完成，不在本次改动范围。
"""
import os, shutil, hashlib, sys, io

SRC = r"D:\OpenGeneral\EFILE_GUS\SCENARIO"
DST = r"D:\DSH\军事游戏汉化\backup\OpenGeneral-EFILE_GUS-SCENARIO.before-zh"


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(DST, exist_ok=True)
    groups = {".xscn": "xscn", ".txt": "txt"}
    total = 0; bad = 0; lines = []
    for ext, sub in groups.items():
        out = os.path.join(DST, sub)
        os.makedirs(out, exist_ok=True)
        names = sorted(f for f in os.listdir(SRC)
                       if f.lower().endswith(ext))
        for f in names:
            s = os.path.join(SRC, f); d = os.path.join(out, f)
            shutil.copy2(s, d)
            a, b = md5(s), md5(d)
            ok = (a == b)
            if not ok:
                print("  [MD5 不一致] %s" % f); bad += 1
            lines.append("%s\t%d\t%s\t%s" % (sub + "/" + f, os.path.getsize(s), a, "ok" if ok else "BAD"))
            total += 1
        print("  %s: 备份 %d 个 -> %s" % (ext, len(names), out))
    with open(os.path.join(DST, "_manifest.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tsize\tmd5\tverify\n")
        f.write("\n".join(lines) + "\n")
    print("\n合计备份 %d 个文件，MD5 不一致 %d 个" % (total, bad))
    print("备份目录: %s" % DST)
    print("清单: %s" % os.path.join(DST, "_manifest.tsv"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
