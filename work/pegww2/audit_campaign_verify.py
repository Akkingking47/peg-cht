#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战役内「场景名 + 地图名」核准（**只读**）。

依据用户要求：以游戏内战役为序，用**战役内前后场**与**该场说明文件(_i.txt)**去核准每个场景的：
  ① 场景名（`_m.txt` 行0；列表/简报标题显示的就是它）
  ② 地图名（该场 `.SCN` 字节里**实际引用**的 `*.MAP`；附同图场景名做旁证）

说明文件(`_i.txt`)的**名字行**不在固定行：可能是
  · 行0「名 - 日期」   · 行0=日期 + 行2=名   · 行0=名 + 行2=日期   · 行0=正文
⇒ 本工具按「跳过纯日期行 / 跳过正文行；取首个像名字的行；再剥掉尾部日期」取「说明名」。

产出：`pegww2/research/_战役-场景与地图核准.tsv`
用法: python audit_campaign_verify.py
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2\SCENARIO"
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_战役-场景与地图核准.tsv")
LISTMD = os.path.join(RES, "_场景列表_最终序号.md")

PREFIX = re.compile(r"^[\u4e00-\u9fff]{2,4}\s*-\s*\d+\s+")
DROP = re.compile(r"(?i)peg\s*:\s*ww2|\buk\b")
DATE = re.compile(r"^[\s(（]*\d{1,4}\s*([/.\-年]\s*\d{1,4}\s*月?){0,2}\s*[日)）]?\s*$")


def index(root):
    return {n.lower(): n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n))}


IDX = index(GAME)


def rlines(name, enc="gbk"):
    real = IDX.get(name.lower())
    if not real:
        return None
    try:
        return io.open(os.path.join(GAME, real), encoding=enc, errors="replace").read().splitlines()
    except Exception:
        return None


def rd(name, k=0):
    ls = rlines(name)
    return ls[k].rstrip("\r\n") if ls and len(ls) > k else None


_MC = {}


def maptok(stem):
    k = stem.lower()
    if k in _MC:
        return _MC[k]
    real = IDX.get((stem + ".scn").lower())
    out = ""
    if real:
        try:
            b = io.open(os.path.join(GAME, real), "rb").read()
            ms = sorted({t.decode("latin1").upper() for t in re.findall(rb"[ -~]{4,}", b)
                         if t.lower().endswith(b".map")})
            out = ",".join(m[:-4] for m in ms[:3])
        except Exception:
            out = ""
    _MC[k] = out
    return out


def is_date(s):
    if not s:
        return False
    t = re.sub(r"[\s(（)）]", "", s)
    return bool(DATE.match(t))


HINT = re.compile(r"(操作提示|消息来自|玩家命令|祝你好运|祝好运|^选择[：:]?$|^注意|部署部队|^年\s*\d+\s*月|操作说明)")


def as_name(s):
    """剥组号前缀 + 剥尾部日期，判是不是「像名字的一行」；返回名字或 ''。"""
    if not s:
        return ""
    t = PREFIX.sub("", s.strip())
    if not t or is_date(t):
        return ""
    if t.endswith("：") or t.endswith(":"):
        return ""
    if re.search(r"(?i)^(dummy|loading scen|n/?a|message from)\b", t):
        return ""
    if re.search(r"(?i)^[=]{3,}", t):
        return ""
    if HINT.search(t):
        return ""
    if "。" in t or len(t) > 40:
        return ""
    if re.search(r"[！？,，]", t) and len(t) > 14:
        return ""
    t = re.sub(r"\s*[-—–]\s*\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\s*$", "", t)
    t = re.sub(r"\s*[-—–,，]\s*\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*$", "", t)
    t = re.sub(r"\s*[-—–,，]\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*$", "", t)
    t = t.strip(" -—–,，")
    if not t or not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", t):
        return ""
    return t


def i_name(name):
    """说明文件(`_i.txt`)里的「名字行」：L0 像名字就用 L0；L0 是纯日期则往后找；否则视为无名字行。"""
    ls = rlines(name)
    if ls is None:
        return None, ""
    if ls:
        v = as_name(ls[0])
        if v:
            return v, ls[0].strip()
        if is_date(ls[0]):
            for l in ls[1:6]:
                v = as_name(l)
                if v:
                    return v, l.strip()
    return "", (ls[0].strip() if ls else "")


def key(s):
    if not s:
        return ""
    s = PREFIX.sub("", s.strip())
    s = DROP.sub("", s)
    s = re.sub(r"[\s:：·\-—()（）\[\]【】,，.。!！?？\"'’“”/\\]", "", s)
    return s.lower()


def cam_blocks(path):
    b = io.open(path, "rb").read()
    toks, cur = [], []
    for x in b:
        if 32 <= x < 127:
            cur.append(chr(x))
        else:
            if len(cur) >= 4:
                toks.append("".join(cur))
            cur = []
    if len(cur) >= 4:
        toks.append("".join(cur))
    out, blk = [], None
    for t in toks:
        tl = t.lower()
        if tl.endswith(".scn"):
            blk = (t, [])
            out.append(blk)
        elif tl.endswith(".txt") and blk is not None:
            blk[1].append(t)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    listed = {}
    if os.path.isfile(LISTMD):
        for l in io.open(LISTMD, encoding="utf-8"):
            m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|", l)
            if m:
                listed[m.group(3).strip().lower()] = (m.group(2).strip(), m.group(4).strip())

    stems = {}
    for fn in sorted(n for n in IDX if n.lower().endswith("_m.txt")):
        stems[re.sub(r"(?i)_m\.txt$", "", IDX[fn]).lower()] = re.sub(r"(?i)_m\.txt$", "", IDX[fn])
    bymap = {}
    for k, st in stems.items():
        for one in maptok(st).split(","):
            if one:
                bymap.setdefault(one, []).append(st)
    selfname = {k: (rd(st + "_m.txt", 0) or "") for k, st in stems.items()}

    cams = sorted(n for n in IDX if re.search(r"(?i)\.cam$", n))
    rows = []
    for cn in cams:
        camp_name = rd(re.sub(r"(?i)\.cam$", "", cn) + ".txt", 0) or ""
        seq = []
        for scn, txts in cam_blocks(os.path.join(GAME, IDX[cn.lower()])):
            stem = re.sub(r"(?i)\.scn$", "", scn)
            itxt = next((t for t in txts if re.search(r"(?i)_i\.txt$", t)), "")
            seq.append((stem, itxt))
        for i, (stem, itxt) in enumerate(seq):
            M = selfname.get(stem.lower(), rd(stem + "_m.txt", 0)) or ""
            IN, Iraw = i_name(itxt) if itxt else i_name(stem + "_i.txt")
            if IN is None:
                IN, Iraw = i_name(stem + "_i.txt")
            mp = maptok(stem)
            prev_n = seq[i - 1][0] if i > 0 else ""
            next_n = seq[i + 1][0] if i + 1 < len(seq) else ""
            lname, lmap = listed.get(stem.lower(), ("", ""))
            peers = [s for one in mp.split(",") for s in bymap.get(one, [])] if mp else []
            peers = [p for p in peers if p.lower() != stem.lower()]
            flags = []
            if not M:
                flags.append("无名栏")
            elif not as_name(M):
                flags.append("名栏非名字")
            if IN is None:
                flags.append("无说明文件")
            elif IN == "":
                flags.append("说明无名字行")
            elif as_name(M) and key(IN) != key(M):
                flags.append("名栏≠说明名")
            if itxt and re.sub(r"(?i)_i\.txt$", "", itxt).lower() != stem.lower():
                flags.append("说明文件异名")
            if lname and as_name(M) and key(M) != key(PREFIX.sub("", lname)):
                flags.append("名栏≠列表名")
            if lmap and mp and lmap.strip().lower() != mp.split(",")[0].strip().lower():
                flags.append("列表地图≠实际地图")
            rows.append([
                camp_name, cn, i + 1, stem, M or "-", IN or "-", (Iraw or "-")[:90],
                itxt or "(无)", mp or "-",
                "|".join(selfname.get(s.lower(), "") or s for s in peers[:6]),
                lname or "-", lmap or "-",
                prev_n + "→" + stem + "→" + next_n,
                ";".join(flags),
            ])

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 战役内「场景名 + 地图名」核准（只读；读游戏目录成品 GBK）\n")
        f.write("# 依据：.cam 场次顺序（战役进程）· 该场 _i.txt（战役说明，名字行未必行0）· .SCN 引用的 *.MAP\n")
        f.write("战役\t战役文件\t场次\t场景\t名栏(_m行0)\t说明名(_i)\t说明名原文行\t说明文件\t地图(.MAP)\t同图场景名\t列表名\t列表地图\t前后场\t标记\n")
        for r in rows:
            f.write("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    from collections import Counter
    c = Counter()
    for r in rows:
        for fl in r[-1].split(";"):
            if fl:
                c[fl] += 1
    print("战役 %d 个 · 场次行 %d" % (len(cams), len(rows)))
    for k, v in c.most_common():
        print("   %-16s %d" % (k, v))
    print("→ %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
