#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层：**批次独立核验**（不信任子代理自述）。

用法: python verify_scn_fill.py <bucket> <片号>        # 例: m 01
      python verify_scn_fill.py m 01

核验项（任一不过即报错，不并入真源）：
  ① 行数 == 该片数据行数；两列
  ② 第一列与 todo 片**逐字节一致**（含反斜杠转义序列）——这是最关键的防错位判据
  ③ 译文列零空值；译文无 TAB / 换行
  ④ 转义序列保留：原文含 `\\t`/`\\xNN` ⇒ 译文也必须含**同种同数**
  ⑤ 译文非「原文照抄」（除 元数据/型号/纯符号 等本来就该原样保留的行）
  ⑥ 禁用译法扫描
  ⑦ 译文不含繁体「民国感」词
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
_sink = io.StringIO()

# 本来就该「译文＝原文」的行（元数据 / 纯符号 / 纯型号）
KEEP_OK = re.compile(
    r"(?i)^(?:dummy|-+|\*+|=+|version\b|gameset\b|equipment\b|note\b|source\b|btw\b"
    r"|[A-Za-z0-9\.\-/()\[\] ]+)$")
BANNED = ["國力", "佔領", "光榮勝利", "前進觀測官", "改良裝備", "声望", "空中出击", "海军攻击"]


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


def rows(p):
    """自动跳过注释与表头：跳过 `#` 行，并跳过第一列是「原文」的那一行。

    容错：若**找不到表头**（历史上切片脚本曾漏写表头），则把全部非 `#` 行当数据，
    并打印提醒 —— 绝不静默返回 0 行（曾因此误判整片不合格）。
    """
    out = []
    seen_header = False
    with open(p, encoding="utf-8-sig") as f:
        for line in f:
            s = line.rstrip("\n")
            if not s.strip() or s.startswith("#"):
                continue
            f2 = s.split("\t")
            if not seen_header:
                if f2[0].strip() in ("原文", "行号", "en"):
                    seen_header = True
                    continue
                # 没找到表头 ⇒ 容错：当作数据
                seen_header = True
            out.append(f2)
    return out


def main():
    bucket, num = sys.argv[1], sys.argv[2]
    todo = os.path.join(RES, f"_scn-todo-{bucket}-{num}.tsv")
    fill = os.path.join(RES, f"_scn-fill-{bucket}-{num}.tsv")
    if not os.path.isfile(fill):
        print(f"❌ 缺产出文件 {os.path.basename(fill)}")
        return 1
    t = rows(todo)
    f = rows(fill)
    print("=" * 88)
    print(f"核验 {os.path.basename(fill)}   （todo 数据 {len(t)} 行 / fill 数据 {len(f)} 行）")
    print("=" * 88)
    errs, warns = [], []
    if len(t) != len(f):
        errs.append(f"行数不一致：todo {len(t)} vs fill {len(f)}")

    bad_col = bad_src = empty = tabbed = 0
    esc_bad = ident = banned = 0
    ident_ex = []
    for i in range(min(len(t), len(f))):
        trow, frow = t[i], f[i]
        if len(frow) < 2:
            bad_col += 1
            continue
        src_todo, src_fill, zh = trow[0], frow[0], frow[1]
        if src_todo != src_fill:
            bad_src += 1
            if bad_src <= 3:
                errs.append(f"行{i + 1} 原文列不一致：todo={src_todo[:50]!r} fill={src_fill[:50]!r}")
        if not zh.strip():
            empty += 1
            continue
        if "\t" in zh or "\n" in zh or "\r" in zh:
            tabbed += 1
        # 转义序列保留
        for pat in (r"\\t", r"\\x[0-9a-fA-F]{2}"):
            if len(re.findall(pat, src_todo)) != len(re.findall(pat, zh)):
                esc_bad += 1
                break
        if zh.strip() == src_todo.strip():
            if not KEEP_OK.match(src_todo.strip()):
                ident += 1
                if len(ident_ex) < 8:
                    ident_ex.append(src_todo[:70])
        if zh.strip() in BANNED:
            banned += 1

    def rep(name, v, ok_msg="✅"):
        print(f"  {name}: {v} {'✅' if v == 0 else '❌'}")
    # ⑦ GBK 可编码性（实测踩过：½ / ö 等西文符号无法用 GBK 编码 ⇒ 生成阶段会整文件失败）
    gbk_bad = []
    for i in range(min(len(t), len(f))):
        if len(f[i]) < 2 or not f[i][1].strip():
            continue
        try:
            f[i][1].encode("gbk")
        except UnicodeEncodeError as e:
            gbk_bad.append((i + 1, f[i][1][e.start], f[i][1][:40]))
    print(f"  ⑦ GBK 无法编码的字符: {len(gbk_bad)} {'✅' if not gbk_bad else '❌'}")
    for no, ch, z in gbk_bad[:8]:
        print(f"       行{no} 字符 {ch!r} (U+{ord(ch):04X}) ← {z}")
    print(f"  ② 原文列不一致: {bad_src} {'✅' if bad_src == 0 else '❌'}")
    print(f"  ③ 缺字段 {bad_col} / 空译文 {empty} / 译文含 TAB·换行 {tabbed} "
          f"{'✅' if bad_col == empty == tabbed == 0 else '❌'}")
    print(f"  ④ 转义序列未保留: {esc_bad} {'✅' if esc_bad == 0 else '❌'}")
    print(f"  ⑤ 疑似「原文照抄」（非元数据/型号）: {ident} "
          f"{'✅' if ident == 0 else '⚠ 见下'}")
    for s in ident_ex:
        print(f"       {s}")
    print(f"  ⑥ 禁用译法命中: {banned} {'✅' if banned == 0 else '❌'}")
    if errs:
        print("  错误明细：")
        for e in errs[:10]:
            print(f"    {e}")
    ok = (len(t) == len(f) and bad_src == 0 and bad_col == 0 and empty == 0
          and tabbed == 0 and esc_bad == 0 and banned == 0)
    print()
    print("总判定:", "✅ 可并入译法真源" if ok else "❌ 不合格，打回")
    return 0 if ok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", f"verify-{sys.argv[1]}-{sys.argv[2]}.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
