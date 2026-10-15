#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 定点修：把载具括注按**英文原版的缩写量级**压缩（W20 · 方案 A）。

背景（用户实机 图3 发现）：英文 `w/251/1`（8 字符）被展开直译成 `（SdKfz 251 半履带车运载）`（15 字），
      使 `12.8cm PaK44 反坦克炮（SdKfz 251 半履带车运载）` 达 35 字，超出采购面板单行宽度。
方案（用户批准 A）：仅把该括注改成与英文同量级的 `（SdKfz 251/1）`；
      **型号代号与兵器名一字不动**（不违 W5）。

纪律：默认 dry-run；`--apply` 才写；写前备份 `.pre-w20`；写后回读校验；幂等（已改过的行不再匹配）。
"""
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-eqp-map.tsv")
BAK = MAP + ".pre-w20"
LOG = os.path.join(RES, "_eqp-carrier-shorten.tsv")

OLD = "（SdKfz 251 半履带车运载）"
NEW = "（SdKfz 251/1）"

_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def main():
    apply_ = "--apply" in sys.argv
    raw = open(MAP, encoding="utf-8-sig").read().split("\n")
    out, hits = [], []
    for i, l in enumerate(raw):
        if not l.strip() or l.startswith("#"):
            out.append(l)
            continue
        f = l.split("\t")
        if len(f) >= 3 and OLD in f[1]:
            old_zh = f[1]
            f[1] = f[1].replace(OLD, NEW)
            f[2] = (f[2] + "+W20载具缩写") if f[2].strip() else "W20载具缩写"
            hits.append((i + 1, f[0], old_zh, f[1]))
            out.append("\t".join(f))
        else:
            out.append(l)

    print("=" * 104)
    print(f"W20 载具括注缩写  真源={os.path.relpath(MAP, WS)}")
    print(f"  {OLD}  →  {NEW}    模式={'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print("=" * 104)
    print(f"  命中并改写 {len(hits)} 行")
    for no, src, oz, nz in hits:
        print(f"    行{no:<5d} {src[:34]:36s} {len(oz):2d}字 → {len(nz):2d}字  {nz}")
    if not hits:
        print("  （无命中：幂等，或已被改过）")
    # 全表残留检查
    still = [i + 1 for i, l in enumerate(out) if OLD in l]
    print(f"  改写后仍含旧括注的行: {len(still)} {'✅' if not still else '❌ ' + str(still[:8])}")

    if not apply_:
        print("\n  ⇒ dry-run，未写入。加 --apply 落盘。")
        return 0

    if not os.path.isfile(BAK):
        shutil.copy2(MAP, BAK)
        print(f"  备份 ⇒ {os.path.relpath(BAK, WS)}")
    else:
        print(f"  备份已存在（不覆盖）: {os.path.relpath(BAK, WS)}")
    with open(MAP, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    back = open(MAP, encoding="utf-8-sig").read()
    ok = (OLD not in back) and (back.count(NEW) >= len(hits))
    print(f"  回读校验 {'✅ 通过' if ok else '❌ 失败'}")
    if not os.path.isfile(LOG):
        with open(LOG, "w", encoding="utf-8", newline="\n") as f:
            f.write("# W20 载具括注缩写（方案 A）：仅压括注，型号代号与兵器名未动\n"
                    "真源行号\t英文原文\t原译文\t新译文\t原字数\t新字数\n")
    with open(LOG, "a", encoding="utf-8", newline="\n") as f:
        for no, src, oz, nz in hits:
            f.write(f"{no}\t{src}\t{oz}\t{nz}\t{len(oz)}\t{len(nz)}\n")
    print(f"  留痕 ⇒ {os.path.relpath(LOG, WS)}")
    return 0 if ok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "w20-eqp-carrier.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
