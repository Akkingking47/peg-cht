#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战役(CAM) ↔ 场景(SCN) 错配审计（**只读**，不改任何文件）。

背景：`saturn` 场景在「向柏林前进」苏联战役里，简报标题却显示别的场景名
（MOD 当年把 Windsor 场景的 `_m.txt` 复制过来未改行0）。本审计在**全库**找同类残留。

★ 读的是**已部署成品**（游戏目录，GBK）：备份/真源里已被改好的不算问题，
  报出来的才是玩家当前在实机上看到的东西。

三类：
  A 战役断链    CAM 里写的 SCN / 文本 / 语音在游戏目录不存在
  B 名栏残留   场景名栏（`_m.txt` 行0，剥掉组号前缀后）与自有材料
               （`<stem>.TXT` / `<stem>_u.txt` 行0）不一致，或本身不是名字
  C 名栏借用   名栏串与**另一个场景**的自有名相同（saturn 同类：整份文件拿错）
附加：D 战役入场文本里找不到该场景任何自有地名（启发式，待人工）

用法: python audit_camp_scn.py [--out FILE]
"""
import collections
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
SCNG = os.path.join(GAME, "SCENARIO")
OUTDEF = os.path.join(WS, "pegww2", "research", "_战役场景错配-审计.tsv")

PREFIX = re.compile(r"^[\u4e00-\u9fff]{2,4}\s*-\s*\d+\s+")     # 组号：东线-29 / 西线-10 / 北非-17
DROP = re.compile(r"(?i)peg\s*:\s*ww2|\buk\b")


def index(root):
    m = {}
    if os.path.isdir(root):
        for n in os.listdir(root):
            if os.path.isfile(os.path.join(root, n)):
                m[n.lower()] = n
    return m


IDX = index(SCNG)


def rd(name, k=0):
    """部署文件第 k 行（GBK）；不存在返回 None。"""
    real = IDX.get(name.lower())
    if not real:
        return None
    p = os.path.join(SCNG, real)
    try:
        with io.open(p, encoding="gbk", errors="replace") as f:
            for i, l in enumerate(f):
                if i == k:
                    return l.rstrip("\r\n")
    except Exception:
        return None
    return None


def rds(name):
    real = IDX.get(name.lower())
    if not real:
        return None
    try:
        return io.open(os.path.join(SCNG, real), encoding="gbk", errors="replace").read()
    except Exception:
        return None


_MAPC = {}


def maptok(stem):
    """该场景 `.SCN` 内引用的地图名（结构性强证据：场景**确实**用这张图）。"""
    k = stem.lower()
    if k in _MAPC:
        return _MAPC[k]
    real = IDX.get((stem + ".scn").lower())
    out = "-"
    if real:
        try:
            b = io.open(os.path.join(SCNG, real), "rb").read()
            ms = sorted({t.decode("latin1").upper() for t in re.findall(rb"[ -~]{4,}", b)
                         if t.lower().endswith(b".map")})
            out = ",".join(m[:-4] for m in ms[:3]) or "-"
        except Exception:
            out = "-"
    _MAPC[k] = out
    return out


def key(s):
    """名栏/自有名的归一化：剥组号前缀 + 去 PeG:WW2/UK + 去空白标点。"""
    if not s:
        return ""
    s = PREFIX.sub("", s.strip())
    s = DROP.sub("", s)
    s = re.sub(r"[\s:：·\-—()（）\[\]【】,，.。!！?？\"'’“”/\\]", "", s)
    return s.lower()


def is_name(s):
    if not s:
        return False
    t = PREFIX.sub("", s.strip())
    if not t:
        return False
    if re.search(r"(?i)^(dummy|loading scen|n/a)\b", t):
        return False
    if re.search(r"[。！？，,;]", t):
        return False
    if len(t) > 24:
        return False
    if not re.search(r"[\u4e00-\u9fffA-Za-z0-9]", t):
        return False
    return True


def message_tier(s):
    """名栏是不是「简报正文/调试串」而不是场景名。返回 '' 表示像名字。

    分两级（避免把『地名 - 日期』这种正常名误判）：
      B1 = 铁证（含句号 / 超 60 字 / 调试串 / Dummy / 全等号）
      B2 = 疑似（>12 字且含 ！？，）
    """
    if not s or not s.strip():
        return "B1 名栏=正文"
    t = PREFIX.sub("", s.strip())
    if ("Loading Scen" in s or "not found" in s or t.strip().lower() == "dummy"
            or (t.strip() and set(t.strip()) <= {"=", " ", "-"})):
        return "B1 名栏=正文"
    if "。" in t or len(t) > 60:
        return "B1 名栏=正文"
    if len(t) > 12 and re.search(r"[！？，]", t):
        return "B2 名栏疑似正文"
    return ""


def cam_strings(path):
    b = io.open(path, "rb").read()
    out, cur = [], []
    for x in b:
        if 32 <= x < 127:
            cur.append(chr(x))
        else:
            if len(cur) >= 4:
                out.append("".join(cur))
            cur = []
    if len(cur) >= 4:
        out.append("".join(cur))
    return out


def fam(stem):
    s = stem.lower()
    s = re.sub(r"[-_\s]*redux$", "", s)
    s = re.sub(r"[-_\s]+r\d*$", "", s)
    s = re.sub(r"[-_\s]*\d+$", "", s)
    return s


def main():
    out = OUTDEF
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]

    rows = []
    stems = {}
    mfiles = sorted(n for n in IDX if n.endswith("_m.txt"))
    ownname = {}          # key(自有名) -> [stem:来源]
    for fn in mfiles:
        stem = re.sub(r"(?i)_m\.txt$", "", IDX[fn])
        M = rd(stem + "_m.txt", 0)
        T = rd(stem + ".TXT", 0) or rd(stem + ".txt", 0)
        U = rd(stem + "_u.txt", 0) or rd(stem + "_U.TXT", 0)
        stems[stem.lower()] = {"stem": stem, "M": M, "T": T, "U": U}
        for tag, v in (("T", T), ("U", U)):
            if v and is_name(v):
                ownname.setdefault(key(v), []).append(stem + ":" + tag)

    for k in sorted(stems):
        s = stems[k]
        stem, M, T, U = s["stem"], s["M"], s["T"], s["U"]
        if M is None:
            rows.append(["B1 名栏=正文", stem, "(无 _m.txt)", "", "", "该场景在列表里无显示名文件"])
            continue
        msg = message_tier(M)
        if msg:
            rows.append([msg, stem, M, "T=" + (T or "-"), "", "名栏是简报正文/调试串，不是场景名"])
            continue
        strong = T and U and is_name(T) and is_name(U) and key(T) == key(U) and key(M) != key(T)
        weak = (not strong) and T and is_name(T) and key(M) != key(T)
        if strong:
            rows.append(["B3 名栏≠自有材料", stem, M, "T/U=" + T, "自有材料两票否决名栏", "saturn 同类"])
        elif weak:
            rows.append(["B3 名栏≠自有材料?", stem, M, "T=" + T + " / U=" + (U or "-"), "", "仅 .TXT 一票，待核"])

    for k in sorted(stems):
        s = stems[k]
        M = s["M"]
        if not is_name(M):
            continue
        others = [o for o in ownname.get(key(M), [])
                  if not o.lower().startswith(s["stem"].lower() + ":") and fam(o.split(":")[0]) != fam(s["stem"])]
        if others:
            rows.append(["C 名栏借用", s["stem"], M, "亦为 " + ",".join(others[:4]) + " 的自有名", "", "疑似整份文件拿错"])

    cams = sorted(n for n in IDX if n.endswith(".cam"))
    for cn in cams:
        toks = cam_strings(os.path.join(SCNG, IDX[cn]))
        items, cur = [], None
        for t in toks:
            tl = t.lower()
            if tl.endswith(".scn"):
                cur = {"scn": t, "txt": []}
                items.append(cur)
            elif tl.endswith(".txt") and cur is not None:
                cur["txt"].append(t)
        for it in items:
            scn = it["scn"]
            miss = []
            if scn.lower() not in IDX:
                miss.append("SCN缺失")
            for f in it["txt"]:
                if f.lower() not in IDX:
                    miss.append("文本缺失:" + f)
            if miss:
                rows.append(["A 战役断链", cn, scn, ";".join(miss[:3]), "", "CAM 引用的文件在游戏目录找不到"])
            stem = re.sub(r"(?i)\.scn$", "", scn)
            s = stems.get(stem.lower())
            if not s or not it["txt"]:
                continue
            blob = "".join(x for x in (rds(f) for f in it["txt"]) if x)
            labels = []
            for kk in ("_m.txt", ".TXT", "_u.txt"):
                xx = rds(stem + kk)
                if xx:
                    labels += [l.strip() for l in xx.splitlines()[1:40]]
            labels = [l for l in labels if l and len(l) <= 12]
            if labels and blob and not any(l in blob for l in labels):
                rows.append(["D 战役内可疑", cn, scn, s["M"] or "-",
                             "入场文本未出现任何自有地名(%d项)" % len(labels), "待人工核对"])

    # ---------- E 实机可见性：78 列表 ∪ 任何 CAM 引用的 .SCN ----------
    LISTMD = os.path.join(WS, "pegww2", "research", "_场景列表_最终序号.md")
    listed = set()
    if os.path.isfile(LISTMD):
        for l in io.open(LISTMD, encoding="utf-8"):
            m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`", l)
            if m:
                listed.add(m.group(3).strip().lower())
    camref = set()
    for cn in cams:
        for t in cam_strings(os.path.join(SCNG, IDX[cn])):
            if t.lower().endswith(".scn"):
                camref.add(re.sub(r"(?i)\.scn$", "", t).strip().lower())
    for r in rows:
        if r[0].startswith(("B", "C")) and r[2].lower() not in listed and r[2].lower() not in camref:
            r[0] = "E 不可见·不修"

    # ---------- F 反向污染复核：既有 override 里「原文行0 像名字却被替换」 ----------
    OVFP = os.path.join(WS, "pegww2", "research", "_scn-file-overrides.tsv")
    if os.path.isfile(OVFP):
        for l in io.open(OVFP, encoding="utf-8-sig"):
            c = l.rstrip("\n").split("\t")
            if len(c) < 5 or not c[2].strip().isdigit() or int(c[2]) != 0:
                continue
            en, fn = c[3].strip(), c[1].strip()
            if not en or fn in ("文件", "期望原文"):
                continue
            if (re.search(r"[.!?]\s*$", en) and len(en.split()) > 2) or len(en.split()) > 8:
                continue                        # 原文本身是句子/长句 ⇒ 替换是对的
            stem = re.sub(r"(?i)_m\.txt$", "", fn)
            cur = rd(fn, 0) or "-"
            waved = ",".join(ownname.get(key(cur), [])[:2]) or "-"
            rows.append(["F 反向污染?", "", stem, cur,
                         "原文行0=%s｜地图=%s｜该名亦属=%s" % (en, maptok(stem), waved),
                         "原文行0 像名字却被覆盖 ⇒ 复核是否改错（ZS_kanw 同类）"])

    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# 战役↔场景 错配审计（读**已部署成品**；只读产出）\n")
        f.write("# A 战役断链 / B 名栏残留 / C 名栏借用 / D 战役内可疑\n")
        f.write("类别\t战役\t场景\t现名栏或缺失项\t反证/来源\t说明\n")
        for r in rows:
            f.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    print("扫描：已部署 _m.txt %d 个 · CAM %d 个" % (len(mfiles), len(cams)))
    cnt = collections.Counter(r[0] for r in rows)
    for k2 in ("A 战役断链", "B1 名栏=正文", "B2 名栏疑似正文", "B3 名栏≠自有材料",
               "B3 名栏≠自有材料?", "C 名栏借用", "D 战役内可疑",
               "E 不可见·不修", "F 反向污染?"):
        print("  %-12s %d" % (k2, cnt.get(k2, 0)))
    print("报告 -> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
