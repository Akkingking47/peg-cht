# -*- coding: utf-8 -*-
"""
阶段 4 · 译稿结构修复器。

子代理常见违规：丢掉尾部圆括号标注（地形/高程/行政区）、把 `,` 改成 `/`、把 `//` 吞成 `/`。
本脚本按 POLICY.md「补充口径 2」机械修复，并报告**修不了的**行（交人工）。

用法：python repair_xscn_zh.py batch-03 [batch-04 ...]
"""
import os, re, sys

W = r"D:\DSH\军事游戏汉化\work\gus"
ZHDIR = os.path.join(W, "zh", "xscn")

MARK = {
    "FOREST": "森林", "HILL": "丘陵", "ROUGH": "起伏地", "SWAMP": "沼泽",
    "MOUNTAIN": "山地", "CLEAR": "开阔地", "VILLAGE": "村庄", "CITY": "城市",
    "PORT": "港口", "AIRFIELD": "机场", "BRIDGE": "桥", "HEDGEROW": "树篱",
    "FARM": "农庄", "LAKE": "湖", "RIVER": "河",
}
TAIL = re.compile(r"^(?P<core>.*?)(?P<tail>(?:\s*\([^()]*\))+)$")
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13}


def tr_inner(inner):
    s = inner.strip()
    m = re.fullmatch(r"(\d+)\s*m", s, re.I)
    if m:
        return m.group(1) + " 米"
    if s.upper() in MARK:
        return MARK[s.upper()]
    if s.upper().rstrip(".") in ROMAN:
        return "第%d区" % ROMAN[s.upper().rstrip(".")]
    return s


def rebuild_tail(tail):
    out = []
    for m in re.finditer(r"(\s*)\(([^()]*)\)", tail):
        out.append(m.group(1) + "(" + tr_inner(m.group(2)) + ")")
    return "".join(out)


def repair(src, dst):
    """返回 (新译文, 说明列表)"""
    notes = []
    # 0) 全角括号归一成半角（与阶段 2/3 交付口径一致）
    out = dst
    if "（" in out or "）" in out:
        out = out.replace("（", "(").replace("）", ")")
        notes.append("括号归一")

    # 1) 尾部圆括号标注丢失
    mt = TAIL.match(src)
    if mt:
        want = len(re.findall(r"\([^()]*\)", src))
        have = out.count("(") + out.count("（")
        if want > have:
            out = out.rstrip() + rebuild_tail(mt.group("tail"))
            notes.append("补尾部括号")

    # 2) `,` 被改成了 `/`
    if "," in src and src.count("/") < out.count("/"):
        # 把多出来的 `/` 还原成顿号：只处理「/」两侧都是中文词的情形
        while out.count("/") > src.count("/") and "、" not in out:
            out = out.replace("/", "、", 1)
            notes.append("逗号并列还原为顿号")

    # 3) 双斜杠/斜杠被吞（只补斜杠串本身，不动译文其余部分）
    if src.count("/") > out.count("/"):
        ms = re.findall(r"/+", src)
        md = re.findall(r"/+", out)
        if ms and md:
            want = max(ms, key=len)
            have = max(md, key=len)
            out = out.replace(have, want, 1)
            notes.append("补斜杠")
        # dst 里完全没有斜杠的情形留给人工（记进 hard 清单）
    return out, notes


def main(argv):
    names = argv[1:] or sorted(
        f[:-4] for f in os.listdir(ZHDIR) if re.fullmatch(r"batch-\d+\.tsv", f))
    for n in names:
        zp = os.path.join(ZHDIR, n + ".tsv")
        if not os.path.exists(zp):
            print("%s: 缺" % n); continue
        lines = open(zp, encoding="utf-8-sig", newline="").read().splitlines()
        out_lines = []
        fixed = 0
        hard = []
        for ln in lines:
            if not ln.strip():
                continue
            c = ln.rstrip("\r").split("\t")
            if c[0].strip().lower() == "src":
                continue
            s = c[0].strip()
            d = c[-1].strip()
            nd, notes = repair(s, d)
            if nd != d:
                fixed += 1
                c[-1] = nd
            # 修完仍不符的记下来
            bad = []
            if s.count("(") != nd.count("(") + nd.count("（"): bad.append("()")
            if s.count("/") != nd.count("/"): bad.append("/")
            if s.count("[") != nd.count("["): bad.append("[]")
            if bad:
                hard.append((s, nd, ",".join(bad)))
            out_lines.append("\t".join(c))
        with open(zp, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out_lines) + "\n")
        print("%s: 行 %d / 自动修复 %d / 修复后仍不符 %d" % (n, len(out_lines), fixed, len(hard)))
        for s, d, w in hard[:20]:
            print("    ! [%s] %-40s -> %s" % (w, s, d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
