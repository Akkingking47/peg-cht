#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐战役(.CAM)审计「简介/说明 地名回退」（只读，不写任何游戏文件）。

背景：战役层自身无独立文本；`.CAM` 是场景槽序列（锚=.scn 引用，步长 636B），
每槽引用 `.scn`（战斗）+ `<stem>_i.txt`（战役屏说明）+ 若干 v/bv/tv/l 视图文件。
玩家看到的文字全部来自场景侧文件：
  ① 任务简报面板 = .SCN @11329（20B NUL 串）→ SCENARIO\\<值>.TXT
     （@11349=1 时走 USERSCEN/.PLY 路径）
  ② 战役屏场景说明 = 槽内 `_i.txt`

本脚本对 34 个 .CAM 逐槽检查：
  A. 槽 .scn 是否存在
  B. @11329 目标：存在性 / 内容是否「清单式」（地名清单特征：
     非空行中 ≤16 字符占比 ≥60% 且无「回合/Turns」字样）
  C. 槽 _i.txt：存在性 / 是否清单式
产出：pegww2/research/_战役简介回退-按战役-20261019.tsv（逐槽）+ 控制台按战役汇总
"""
import io
import os
import re
import sys

WS = r"D:\DSH\军事游戏汉化"
G = r"D:\Program Files\PeG-WW2"
SCN = os.path.join(G, "SCENARIO")
USR = os.path.join(G, "USERSCEN")
RES = os.path.join(WS, "pegww2", "research")
OUT = os.path.join(RES, "_战役简介回退-按战役-20261019.tsv")

IDX = {}
for d in (SCN, USR):
    if os.path.isdir(d):
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                IDX.setdefault(n.lower(), p)

STR = re.compile(rb"[\x20-\x7e]{3,}")


def cam_slots(path):
    """解析 .CAM → [(scn引用, _i引用), ...]，槽锚 = .scn 引用偏移。"""
    raw = open(path, "rb").read()
    refs = []
    for m in STR.finditer(raw):
        s = m.group().decode("latin-1")
        if re.search(r"(?i)\.(scn|txt)$", s):
            refs.append((m.start(), s))
    anchors = [r for r in refs if r[1].lower().endswith(".scn")]
    slots = []
    for k, (off, scnf) in enumerate(anchors):
        end = anchors[k + 1][0] if k + 1 < len(anchors) else len(raw)
        i_file = ""
        for o, s in refs:
            if off < o < end and not s.lower().endswith(".scn") \
                    and re.search(r"(?i)_i\.txt$", s):
                i_file = s
                break
        slots.append((scnf, i_file))
    return slots


def scn_field(p, off, n=20):
    raw = open(p, "rb").read()
    if len(raw) < off + n:
        return None
    return raw[off:off + n].split(b"\x00")[0].decode("latin-1", "replace").strip()


DATE = re.compile(r"^\s*\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4}\s*$")
# 结构词：命中即视为正常文本（简报尾注/电台体/单位编制说明）
STRUCT = re.compile(r"(?i)回合|turn|玩家|player|消息来自|16个单位|营部|胜利格")


def classify_txt(rel):
    """返回 (存在, 非空行数, 清单式?, 行0, 前3条)。rel 为文件名（IDX 大小写不敏感查）。

    v2 判据（地名清单 = 地图字标/单位码清单，区别于三类正常形态）：
      非空行 ≥10 且 ≤16字符行占比 ≥60% 且 最长行 ≤40字符
      且 无日期行（日期+名+正文段是标准说明）且 无结构词（电台消息体正常）
    v1 只有「短行占比+无回合」，把 3 行小样本说明与电台体全部误报（125 个），已废弃。"""
    p = IDX.get((rel or "").lower())
    if rel and not p:
        # 尝试补 .TXT（CAM 引用常全小写）
        p = IDX.get(rel.lower() + ".txt")
    if not rel:
        return (None, 0, False, "", "")
    if not p:
        return (False, 0, False, "(文件缺失)", "")
    ls = io.open(p, encoding="gbk", errors="replace").read().splitlines()
    ne = [x.strip() for x in ls if x.strip()]
    if not ne:
        return (True, 0, False, "(空)", "")
    short = sum(1 for x in ne if len(x) <= 16)
    ratio = short / len(ne)
    maxlen = max(len(x) for x in ne)
    has_date = any(DATE.match(x) for x in ne)
    has_struct = any(STRUCT.search(x) for x in ne)
    listish = ratio >= 0.6 and maxlen <= 40 and not has_date and not has_struct \
        and len(ne) >= 10
    return (True, len(ne), listish, ne[0], " | ".join(ne[:3]))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    camps = sorted(n for n in os.listdir(SCN) if n.lower().endswith(".cam"))
    print(f"战役文件 {len(camps)} 个")
    for cam in camps:
        slots = cam_slots(os.path.join(SCN, cam))
        probs = []
        for si, (scnf, i_ref) in enumerate(slots, 1):
            scn_p = IDX.get(scnf.lower())
            tgt = flag = ""
            tgt_cls = (None, 0, False, "", "")
            if not scn_p:
                probs.append(f"#{si} 场景文件缺失:{scnf}")
            else:
                tgt = scn_field(scn_p, 11329) or ""
                b = scn_field(scn_p, 11349, 1)
                flag = b if b is not None else "?"
                tgt_cls = classify_txt(tgt + ".TXT" if tgt else "")
                if not tgt:
                    probs.append(f"#{si} {scnf}: @11329 为空")
                elif tgt_cls[0] is False:
                    probs.append(f"#{si} {scnf}: 简报文件缺失 {tgt}.TXT")
                elif tgt_cls[2]:
                    probs.append(f"#{si} {scnf}: 简报是清单式 {tgt}.TXT「{tgt_cls[3]}」")
            i_cls = classify_txt(i_ref)
            if i_ref and i_cls[0] is False:
                probs.append(f"#{si} {scnf}: 说明文件缺失 {i_ref}")
            elif i_ref and i_cls[2]:
                probs.append(f"#{si} {scnf}: 说明是清单式 {i_ref}「{i_cls[3]}」")
            # 交叉核对槽 .scn 与 _i 词干一致性（槽内 _i 应属本场）
            stem = re.sub(r"(?i)\.scn$", "", scnf)
            i_stem = re.sub(r"(?i)_i\.txt$", "", i_ref) if i_ref else ""
            rows.append((cam, si, scnf, stem, i_ref, tgt, flag,
                         tgt_cls[0], tgt_cls[1], "是" if tgt_cls[2] else "否",
                         tgt_cls[3], tgt_cls[4],
                         i_cls[0], i_cls[1], "是" if i_cls[2] else "否",
                         i_cls[3]))
        tag = "❌" if probs else "✅"
        print(f"{tag} {cam:<20} 槽 {len(slots):>3}  问题 {len(probs)}")
        for x in probs[:8]:
            print(f"      {x}")
        if len(probs) > 8:
            print(f"      …还有 {len(probs)-8} 条")
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("# 逐战役(.CAM)简介/说明回退审计 · 只读 · 逐槽\n")
        f.write("# 判据为启发式(v2)：已知污染清单以 _简介污染-普查-20261019.tsv 为准；\n"
                "# s0010_i（s00sov#11）因含日期行被漏报，人工已确认为单位码清单（已知待定）\n")
        f.write("战役\t槽#\t.scn引用\t词干\t_i引用\t@11329目标\t@11349\t"
                "简报存在\t简报行数\t简报清单式\t简报行0\t简报前3条\t"
                "_i存在\t_i行数\t_i清单式\t_i行0\n")
        for r in rows:
            f.write("\t".join("" if v is None else str(v) for v in r) + "\n")
    print(f"\n[out] {OUT}（{len(rows)} 槽）")


if __name__ == "__main__":
    main()
