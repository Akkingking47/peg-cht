#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批次 2 生成器：番号链/后缀同构串 —— 规则引擎 + 人工表

口径依据（先例全部取自既有交付件，抽样见 work/xscn/_xscn_dict.tsv 与 POLICY.md）：
  `I/104`→`第1/第104` · `1/10TB`→`第1/第10坦克旅` · `I/21L`→`第1/21L`（后缀未知⇒整 token 保留）
  `1340th Reg`→`第1340团`（去英文序数后缀） · `V Corps`→`第5军` · `10 Pz`→`第10装甲师`
  `70A`→`第70集团军` · `JG1`→`第1战斗机联队` · `I/StG1`→`第1/第1俯冲轰炸机联队` · `1/ HG`→赫尔曼·戈林
规则：纯数字/纯罗马(≥2位或 I/V) → `第N`；数字+已知后缀 → `第N+中文`；后缀未知 → 整 token 保留；
      纯字母 token → 查 TOKENS，否则**整 token 保留**（绝不把 `CA`/`L` 之类拆成罗马数字+后缀）。
⚠️ 凡是「整条一个 token 都判定不了」⇒ 不输出（保持原文）并列入跳过清单。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "xscn-new-2.tsv")

SUF = {
    "Pz": "装甲", "Pz.": "装甲", "Pz.Div.": "装甲师", "Pz. Div.": "装甲师", "Pz. Reg.": "装甲团",
    "Pz. Abt.": "装甲营", "JgdPz. Abt.": "反坦克营", "JgdPz.": "反坦克歼击",
    "TD": "坦克师", "TB": "坦克旅", "TC": "坦克军", "TA": "坦克集团军", "GTA": "近卫坦克集团军",
    "SS": "党卫军", "G": "近卫", "M": "摩托化", "A": "集团军", "AA": "防空", "R": "团",
    "Div": "师", "Div.": "师", "Rifle": "步兵", "Rifle Div.": "步兵师",
    "Guards": "近卫", "Guards Div.": "近卫师", "Guards Div": "近卫师",
    "Tank Bn.": "坦克营", "Tank Corps": "坦克军", "Mech. Corps": "机械化军",
    "Bn": "营", "Bn.": "营", "Corps": "军", "Armee": "集团军", "Brig.": "旅", "Reg.": "团",
    "Art. Reg.": "炮兵团", "FlaK Abt.": "高炮营", "StuG.Brig.": "突击炮旅",
    "Fallschirm.": "空降", "Luft. Field Div.": "空军野战师",
    "IAP": "歼击航空团", "JG": "战斗机联队", "JG-": "战斗机联队",
    "KG": "轰炸航空团", "StG": "俯冲轰炸机联队", "SchG": "强击航空联队", "HG": "赫尔曼·戈林",
    "Squadriglia": "中队", "Commandos": "突击队", "Mixed Air Div": "混成航空师",
    "Fortified Area": "筑垒地域",
}

# 纯字母 token 的表（含 L1/L2/L4 这类字母+数字的航空队代号）
TOKENS = {"L1": "第1航空队", "L2": "第2航空队", "L4": "第4航空队", "SPol": "党卫军警察"}

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
# ⚠️ 单个 L/C/D/M/X 一律**不认**（现实中多为缩写，不是罗马数字）
BARE_OK = {"I", "V"}

MAN = {
    "Labinski  Jewish Quarter": "拉宾斯基犹太区",
    "Destroyed Bridge": "被摧毁的桥梁",
    "Staging Area": "集结地域",
    "STEEP HILL": "陡峭丘陵",
    "Frozen Lake": "冰湖",
    "Forward Base": "前进基地",
    "Temp. Airfield": "临时机场",
    "Kroptin Tank Factories": "克罗普京坦克工厂",
    "Voltic Caves": "沃尔蒂克洞穴",
    "The Barrowlands": "巴罗兰兹",
    "Sperrgruppe Weidling": "魏德林封锁集群",
    "Flakuntergruppe Dieppe": "迪耶普高炮分队",
    "Queens Own Rfl./3": "女王皇家步枪团/第3",
    "Cameron Highlanders": "卡梅伦高地人",
    "Fort Garry/3": "加里堡/第3",
    "48th Commandos": "第48突击队",
    "360th Squadriglia": "第360中队",
    "43rd Div.": "第43师",
    "26th Guards": "第26近卫",
    "8th Fallschirm.": "第8空降",
    "8th AA": "第8防空",
    "16th Luft. Field Div.": "第16空军野战师",
    "116th Pz. Div.": "第116装甲师",
    "1st Tank Corps": "第1坦克军",
    "5th Mech. Corps": "第5机械化军",
    "1 Mixed Air Div": "第1混成航空师",
    "AD/23 Fortified Area": "AD/第23筑垒地域",
    "Finnisch/5SS": "芬兰/第5党卫军",
    "Reich/2nd SS": "帝国/第2党卫军",
    "Leibstandarte": "警卫旗队",
    "Force Z": "Z部队",
    "3SS/Tot": "第3党卫军/骷髅",
    "5SS/Vi": "第5党卫军/维克",
    "Germania/5SS": "日耳曼尼亚/第5党卫军",
    "Art. Reg./12th SS": "炮兵团/第12党卫军",
    "FlaK Abt./12th SS": "高炮营/第12党卫军",
    "Pz. Reg./12th SS": "装甲团/第12党卫军",
    "JgdPz. Abt./12th SS": "反坦克营/第12党卫军",
    "XXVI/12th SS": "第26/第12党卫军",
    "XXV/12th SS": "第25/第12党卫军",
    "II/1st SS": "第2/第1党卫军",
    "IV/4th SS Polizei": "第4/第4党卫军警察师",
    "XVI/JG-3": "第16/第3战斗机联队",
    "V/GTB": "第5/GTB",
    "XIII/G Kav": "第13/近卫骑兵",
    "LI/Luft. Nachrichten": "第51/空军通信",
    "XXI/109th Corps": "第21/第109军",
    "CXII/TF Rasanen": "第112/特遣队拉桑宁",
    "X/TF Rasanen": "第10/特遣队拉桑宁",
    "LXXV/31G": "第75/第31近卫",
    "LXXV/5G": "第75/第5近卫",
    "XIX/19th Pz.": "第19/第19装甲",
    "XXVII/17th Pz. Div.": "第27/第17装甲师",
    "XCII/20th Pz. Div.": "第92/第20装甲师",
    "CXII/20th Pz. Div.": "第112/第20装甲师",
    "1SB/4AF": "第1SB/4AF",
}


def r2i(s):
    """罗马数字 → int；含非法字符 / 单字母 L C D M X / 超范围 → None。"""
    if not re.fullmatch(r"[IVXLCDM]+", s):
        return None
    if len(s) == 1 and s not in BARE_OK:
        return None
    v, prev = 0, 0
    for ch in reversed(s):
        n = ROMAN[ch]
        v += -n if n < prev else n
        prev = max(prev, n)
    return v if 0 < v <= 2000 else None


def tok(t):
    t = t.strip()
    if not t:
        return t
    if t in ("-",):
        return t
    if t in TOKENS:
        return TOKENS[t]
    if re.fullmatch(r"[0-9]+", t):
        return "第" + t
    n = r2i(t)
    if n:
        return "第%d" % n
    # 「缩写 + 空格 + 数字」型（如 `StuG.Brig. 303`）⇒ 第N + 中文
    m2 = re.fullmatch(r"([A-Za-z][A-Za-z. ]*?)\s+([0-9]+)", t)
    if m2 and m2.group(1).strip() in SUF:
        return "第%s%s" % (m2.group(2), SUF[m2.group(1).strip()])
    # 「数字 或 罗马数字」+ 英文序数后缀（可省）+ 后缀词
    m = re.fullmatch(r"([0-9]+|[IVXLCDM]+)(?:st|nd|rd|th)?\s*(.+)", t)
    if m:
        num, suf = m.group(1), m.group(2).strip()
        ni = int(num) if num.isdigit() else r2i(num)
        if ni is not None and suf in SUF:
            return "第%d%s" % (ni, SUF[suf])
        return t                              # 后缀未知 / 前段不是合法数字 ⇒ 整 token 保留
    return t                                  # 纯字母 ⇒ 整 token 保留（绝不拆罗马）


def tr(s):
    if s in MAN:
        return MAN[s]
    parts = s.split("/")
    if len(parts) == 1:
        return tok(s)
    out = []
    for p in parts:
        if p == "":
            return None
        d = tok(p)
        if d is None:
            return None
        out.append(d)
    return "/".join(out)


def main():
    todo = []
    with io.open(os.path.join(HERE, "_xscn_todo2.tsv"), encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and int(c[1]) >= 5:
                todo.append(c[0])

    rows, skipped = [], []
    for s in todo:
        d = tr(s)
        # 守卫：输出里不得出现「第 + 数字 + 纯大写字母(≥2)」这种把未知后缀当已知的痕迹
        if d and re.search(r"第[0-9]+[A-Z]{2,}", d):
            skipped.append((s, "守卫: " + d))
            continue
        if d is None or d == s:
            skipped.append((s, d))
            continue
        try:
            d.encode("gbk")
        except UnicodeEncodeError:
            skipped.append((s, "GBK 不可编码"))
            continue
        if "\t" in d:
            skipped.append((s, "含制表符"))
            continue
        rows.append((s, d))

    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in rows:
            f.write("%s\t%s\n" % (s, d))
    print("批次 2: 输出 %d 条 / 跳过 %d 条（跳过＝保持原文）" % (len(rows), len(skipped)))
    print()
    print("=== 输出（供复核）===")
    for s, d in rows:
        print("   %-30s -> %s" % (s, d))
    print()
    print("=== 跳过（保持原文）共 %d ===" % len(skipped))
    for s, d in skipped:
        print("   %-30s %s" % (s, d if d else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
