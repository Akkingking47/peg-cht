#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 阶段1/3 准备：生成「译法真源」工作表（前作可复用部分预填）。

产出（译法与逻辑分离：**这些 tsv 就是译法真源**）：
  pegww2/research/WW2Gui-map.tsv     行号模式  行号 原文 译文 来源
  pegww2/research/WW2Misc-map.tsv    行号模式
  pegww2/research/WW2Tips-map.tsv    行号模式
  pegww2/research/ww2-eqp-map.tsv    原文串模式  原文 译文 来源
  pegww2/research/WW2NAME-map.tsv    原文串模式

规则：前作 PeG 命中 ⇒ 预填译文 + 来源=PeG（**不改**）；未命中 ⇒ 译文留空 + 来源=新译（待填）。
已存在的 map **不覆盖**（幂等；保护人工已填内容）。
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "text")
PEGR = os.path.join(WS, "peg", "research")
OUTD = os.path.join(WS, "pegww2", "research")
os.makedirs(OUTD, exist_ok=True)
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


def lines_of(p):
    with open(p, "rb") as f:
        b = f.read()
    return re.split(rb"\r\n|\r|\n", b)


def load_line_map(name):
    """支持 2 列（行号/译文）与 3 列（行号/原文/译文）两种前作格式。"""
    m = {}
    p = os.path.join(PEGR, name)
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if len(f2) >= 2 and re.fullmatch(r"\d+", f2[0].strip()):
                m[int(f2[0])] = (f2[1].strip(), f2[2].strip()) if len(f2) >= 3 else ("", f2[1].strip())
    return m


def load_value_map(name):
    m = {}
    p = os.path.join(PEGR, name)
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            f2 = line.rstrip("\r\n").split("\t")
            if len(f2) >= 2 and not re.fullmatch(r"\d+", f2[0].strip()):
                m[f2[0].strip()] = f2[1].strip()
    return m


def write_line_map(outname, srcfile, pegmaps, title):
    out = os.path.join(OUTD, outname)
    if os.path.isfile(out):
        print(f"  {outname}: 已存在，跳过（保护人工已填）")
        return
    lm = {}
    for nm in pegmaps:
        for k, v in load_line_map(nm).items():
            lm.setdefault(k, v)
    ls = lines_of(os.path.join(BK, srcfile))
    reused = new = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n")
        f.write(f"# 来源：{srcfile}（行号模式；引擎按行号取字，**行数必须与原版严格一致**）\n")
        f.write("# 来源列：PeG=前作已验证译文（勿改）/ 新译=待填 / 保留=原样不动\n")
        f.write("行号\t原文\t译文\t来源\n")
        for i, raw in enumerate(ls):
            t = raw.decode("cp1252").rstrip()
            if not t:
                continue
            ent = lm.get(i + 1)
            if ent and (not ent[0] or ent[0] == t):
                f.write(f"{i + 1}\t{t}\t{ent[1]}\tPeG\n")
                reused += 1
            else:
                f.write(f"{i + 1}\t{t}\t\t新译\n")
                new += 1
    print(f"  {outname}: 共 {reused + new} 行（PeG 预填 {reused} / **待填 {new}**）")


def write_value_map(outname, srcfile, pegmaps, title):
    out = os.path.join(OUTD, outname)
    if os.path.isfile(out):
        print(f"  {outname}: 已存在，跳过")
        return
    vm = {}
    for nm in pegmaps:
        for k, v in load_value_map(nm).items():
            vm.setdefault(k, v)
    ls = lines_of(os.path.join(BK, srcfile))
    seen = []
    for raw in ls:
        t = raw.decode("cp1252").rstrip()
        if t and t not in seen:
            seen.append(t)
    reused = new = kept = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n")
        f.write(f"# 来源：{srcfile}（原文串模式；未列出的条目 ⇒ 生成器**原样保留**）\n")
        f.write("# 来源列：PeG=前作已验证译文 / 新译=待填 / 保留=按型号规范原样保留\n")
        f.write("原文\t译文\t来源\n")
        for t in seen:
            if t in vm and vm[t] != t:
                f.write(f"{t}\t{vm[t]}\tPeG\n")
                reused += 1
            elif t in vm:
                f.write(f"{t}\t{t}\t保留\n")
                kept += 1
            else:
                f.write(f"{t}\t\t新译\n")
                new += 1
    print(f"  {outname}: 共 {reused + kept + new} 唯一串（PeG 预填 {reused} / 原样保留 {kept} / **待填 {new}**）")


def main():
    print("=" * 92)
    print("生成译法真源工作表（前作可复用部分预填）")
    print("=" * 92)

    write_line_map("WW2Gui-map.tsv", "WW2Gui.txt", ["gui030-zh.tsv"], "WW2Gui.txt 行级译法（界面/菜单/面板/悬浮标签）")
    write_line_map("WW2Misc-map.tsv", "WW2Misc.txt", ["misc030-map.tsv"], "WW2Misc.txt 行级译法（地形/战斗标签）")
    write_line_map("WW2Tips-map.tsv", "WW2Tips.TXT", ["tips030-map.tsv"], "WW2Tips.TXT 行级译法（玩法提示）")
    write_value_map("ww2-eqp-map.tsv", "ww2-eqp.txt", ["Equip30-map.tsv"], "ww2-eqp.txt 装备名译法（型号保留 + 绰号意译）")

    # 姓名表：前作「原文 × 成品」还原
    out = os.path.join(OUTD, "WW2NAME-map.tsv")
    if os.path.isfile(out):
        print("  WW2NAME-map.tsv: 已存在，跳过")
    else:
        o = lines_of(os.path.join(WS, "peg", "testbed", "backup", "name030.txt"))
        d = lines_of(os.path.join(r"D:\Program Files\PeG", "Name030.txt"))
        vm = {}
        for i in range(min(len(o), len(d))):
            a = o[i].decode("cp1252").strip()
            b = d[i].decode("cp1252").strip()
            if a and b and a != b:
                vm.setdefault(a, b)
        seen = []
        for raw in lines_of(os.path.join(BK, "WW2NAME.TXT")):
            t = raw.decode("cp1252").rstrip()
            if t and t not in seen:
                seen.append(t)
        reused = new = 0
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("# WW2NAME.TXT 姓名译法（原文串模式；未列出 ⇒ 原样保留）\n")
            f.write("# 口径：能还原汉字的还原；德/意/日/苏等按**标准音译**（见 ui-glossary.tsv「人名」节）\n")
            f.write("原文\t译文\t来源\n")
            for t in seen:
                if t in vm:
                    f.write(f"{t}\t{vm[t]}\tPeG\n")
                    reused += 1
                else:
                    f.write(f"{t}\t\t新译\n")
                    new += 1
        print(f"  WW2NAME-map.tsv: 共 {reused + new} 唯一串（PeG 预填 {reused} / **待填 {new}**）")


if __name__ == "__main__":
    main()
    with open(os.path.join(OUTD, "..", "research", "evidence", "worksheets.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
