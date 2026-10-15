#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""番号链/后缀同构串 生成器（参数化）—— 规则引擎 + 人工表

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
OUT = os.path.join(HERE, "xscn-new-3.tsv")   # 默认输出；用 --out 覆盖

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

# ⭐ 2026-09-29 扩：**后缀逐词翻译**（要求每个词命中，否则整条保留）。
#    动机：残量里约 400 条是「数字 + 英文编制」型（`6th Bomber Grp.` / `92nd Infantry Brig.` /
#    `213th Sicherungs Div.` …），原先因后缀未整体收录而被跳过。逐词表可一次性覆盖。
WORD = {
    # ── 编制 ──
    "Batt.": "营", "Batt": "营", "Bat.": "营", "Abt.": "营", "Abt": "营",
    "Division": "师", "Brigade": "旅", "Brig": "旅", "Brg": "旅",
    "Regiment": "团", "Reg": "团", "Squadron": "中队", "Sqdr": "中队",
    "Grp.": "群", "Grp": "群", "Group": "群", "Army": "集团军",
    "Airforce": "航空队", "Commando": "突击队", "Comm.": "突击队", "Hussars": "骠骑兵团",
    # ── 兵种 / 类型 ──
    "Infantry": "步兵", "Inf.": "步兵", "Armored": "装甲", "Armoured": "装甲",
    "PzGren.": "装甲掷弹兵", "Moto.": "摩托化", "Mot.": "摩托化",
    "Cav.": "骑兵", "Cavalry": "骑兵", "Kav.": "骑兵", "Kavallerie": "骑兵",
    "Kavalerie": "骑兵", "Kavaleria": "骑兵",
    "Pioniere": "工兵", "Pion.": "工兵", "Saperni": "工兵", "Sap": "工兵", "Sapper": "工兵",
    "Pi": "工兵", "Eng.": "工兵", "Engineer": "工兵",
    "Art.": "炮兵", "Field": "野战", "Howitzer": "榴弹炮", "Mort.": "迫击炮",
    "FlaK": "高炮", "AT": "反坦克", "Anti-Tank": "反坦克", "MG": "机枪",
    "Recon": "侦察", "Rec": "侦察", "Rad": "自行车", "Bicycle": "自行车",
    "Para.": "伞兵", "Airborne": "空降", "Ski": "滑雪", "Sturm": "突击", "Assault": "突击",
    "JagdPz.": "反坦克歼击", "Schwere": "重型", "SPArt.": "自行火炮", "SP Art.": "自行火炮",
    "Ind.": "独立", "Ind": "独立",
    "Sicherungs": "警卫", "Sicherheit": "警卫", "Border": "边境", "Coastal": "海岸",
    "Bridging": "架桥", "Bruecken": "架桥", "NKVD": "内务人民委员部", "NKWD": "内务人民委员部",
    "Marine": "海军陆战", "Mar.": "海军陆战", "Naval": "海军", "Air": "航空",
    "Bomber": "轰炸机", "Fighter": "战斗机", "Tank": "坦克",
    "NSGr.": "夜间对地攻击联队", "NSGr": "夜间对地攻击联队",
    # ── 国别 / 地望 ──
    "Norge": "挪威", "Norwegian": "挪威", "Polish": "波兰", "French": "法国",
    "Free": "自由", "Indian": "印度", "Algerian": "阿尔及利亚", "Morrocan": "摩洛哥",
    "Moroccan": "摩洛哥", "British": "英国", "Scottish": "苏格兰", "Royal": "皇家",
    "Calgary": "卡尔加里", "Carpathian": "喀尔巴阡", "Kresowa": "克雷索瓦",
    "Special": "特别", "Service": "勤务", "Res": "预备", "Res.": "预备",
    "Moskauer": "莫斯科", "Mos": "莫斯科", "JgdFl.": "歼击航空", "SchlFl.": "对地攻击航空",
    "ArtReg": "炮兵团", "Schtz.Reg.": "步兵团", "SchtzReg": "步兵团", "Kav.Reg.": "骑兵团",
    "TkReg": "坦克团", "ATReg": "反坦克团", "JgFlgReg": "歼击航空团", "SchlFlgReg": "对地攻击航空团",
    "FlagReg": "旗队", "FlakReg": "高炮团", "NKWDReg": "内务人民委员部团",
    "MoskauerFlagReg": "莫斯科旗队", "MoskauerFlakReg": "莫斯科高炮团",
    "MosArbBrig": "莫斯科工人旅", "sArt": "重型炮兵", "Mar. Art": "海军陆战炮兵",
    "Pz Jgr": "反坦克歼击", "Pz": "装甲",
    # ── 补：批次 7 输出里暴露的缺口（2026-09-29）──
    "Geb": "山地", "Geb.": "山地", "Geb Div": "山地师", "GK": "山地军",
    "Norw": "挪威", "Norw.": "挪威", "Rif": "步兵", "Rif Div": "步兵师",
    "Rif Bde": "步兵旅", "Schtz.Div.": "步兵师", "Schtz.": "步兵",
    "Kav.Div.": "骑兵师", "Kav.Div": "骑兵师", "RD": "步兵师", "MD": "摩托化师",
    "LF5": "第5航空队", "Royal Scots": "皇家苏格兰团",
    "Scottish Borderers": "苏格兰边境团", "Shock": "突击", "Sicherung": "警卫",
    "'Krim-Front'": "'克里米亚方面军'", "GK Norw": "挪威山地军", "GK Norw.": "挪威山地军",
    # ── 补：末轮（2026-09-29）──
    "Ranger": "游骑兵", "Anti tank": "反坦克", "Antitank": "反坦克", "Assault Gun": "突击炮",
    "Tactical": "战术", "Lt.": "轻型", "Lt": "轻型", "Fuhrer-Begleit": "元首护卫",
    "StuG": "突击炮", "StuG.": "突击炮", "Jgdpz.": "反坦克歼击", "Jgdpz": "反坦克歼击",
    "ID": "步兵师", "CavD": "骑兵师", "CavB": "骑兵旅", "CvD": "骑兵师", "Cv": "骑兵", "Cav": "骑兵",
    "SS Liebstandarte": "党卫军警卫旗队", "SS Hitlerjugend": "党卫军希特勒青年团",
    "SS Totenkopf": "党卫军骷髅", "SS Wiking": "党卫军维京",
    "SS Das Reich": "党卫军帝国", "SS Hohenstaufen": "党卫军霍恩施陶芬",
    "Das Reich": "帝国", "Liebstandarte": "警卫旗队",
    "Anti": "反", "tank": "坦克", "Gun": "炮",
    # ── label 层补（2026-09-29）──
    "Arm": "装甲", "Brig": "旅", "Greek": "希腊", "air": "航空", "force": "队",
    "Fortifications": "要塞", "Fortification": "要塞", "Fortress": "要塞",
    "Beach": "海滩", "Town": "镇", "Pass": "隘口", "Airport": "机场",
    "infantry": "步兵", "SNOW": "雪地", "SAND": "沙地",
    "Sevastopol": "塞瓦斯托波尔", "Voroshilograd": "伏罗希洛夫格勒",
    "Littorio": "利托里奥", "Repulse": "反击", "HMS Repulse": "HMS 反击号",
    "Stalingrad": "斯大林格勒", "Alexandria": "亚历山大", "Moscow": "莫斯科",
    "Gold": "黄金", "Sword": "剑", "L5": "第5航空队",
}
SUF.update({k: v for k, v in WORD.items() if k not in SUF})

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


def suf_zh(suf):
    """后缀串 → 中文。优先整段命中；否则**逐词**（要求每词命中、且拼完不剩字母）。"""
    if suf in SUF:
        return SUF[suf]
    toks = re.findall(r"[A-Za-z][A-Za-z.'-]*|\d+", suf)
    if not toks:
        return None
    remain = suf
    for tk in toks:
        remain = remain.replace(tk, "", 1)
    if re.search(r"[A-Za-z]", remain):
        return None                       # 有词没被切出来 ⇒ 不冒险
    out = []
    for tk in toks:
        if tk in SUF:
            out.append(SUF[tk])
        else:
            return None
    return "".join(out)


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
    if n is None and len(t) >= 2 and t.endswith("."):
        n = r2i(t[:-1])          # `III.` / `II.` 带点罗马数字
    if n:
        return "第%d" % n
    # 整段 / 多词后缀直查（长度≥4 或多词，避免 `Div`/`G`/`M` 这类单词被独译）
    if " " in t or len(t) >= 4:
        z = suf_zh(t)
        if z:
            return z
    # 「缩写 + 空格 + 数字」型（如 `StuG.Brig. 303`）⇒ 第N + 中文
    m2 = re.fullmatch(r"([A-Za-z][A-Za-z. ]*?)\s+([0-9]+)", t)
    if m2 and m2.group(1).strip() in SUF:
        return "第%s%s" % (m2.group(2), SUF[m2.group(1).strip()])
    # 「数字 或 罗马数字」+ 英文序数后缀（可省）+ 后缀词
    m = re.fullmatch(r"([0-9]+|[IVXLCDM]+)(?:st|nd|rd|th)?\s*(.+)", t)
    if m:
        num, suf = m.group(1), m.group(2).strip()
        ni = int(num) if num.isdigit() else r2i(num)
        if ni is not None:
            z = suf_zh(suf)
            if z:
                return z if z.startswith("第") else "第%d%s" % (ni, z)
        return t                              # 后缀未知 / 前段不是合法数字 ⇒ 整 token 保留
    return t                                  # 纯字母 ⇒ 整 token 保留（绝不拆罗马）


BRACKET_TAIL = re.compile(r"^(.+?)\s+(\[[^\]]*\]?)$")


def tr(s):
    # 尾部方括号（`3/3 [48]` / `417/168 [3]`）：译番号链，**方括号代号原样保留**
    mt = BRACKET_TAIL.match(s)
    if mt:
        head, tail = mt.group(1).strip(), mt.group(2)
        dh = tr(head)
        if dh and dh != head:
            return dh + " " + tail
        return s
    if s in MAN:
        return MAN[s]
    # 守卫：`MM/YYYY` 是**日期**不是番号链（`05/2012` 曾被译成「第05/第2012」）
    if re.fullmatch(r"\d{1,2}/\d{4}", s.strip()):
        return s
    parts = s.split("/")
    if len(parts) == 1:
        d = tok(s)
        # ⚠️ 同 §27.1：tok() 会 strip。单 token 路径原先直接返回 strip 结果，
        #    于是 `Sevastopol `（尾随空格）被当成"译文"输出成 `Sevastopol`（丢空白）。
        #    现：① 要求**实质改动**（去空白后不同）才算翻译；② **保留首尾空白**。
        if d.strip() == s.strip():
            return s
        lead = s[:len(s) - len(s.lstrip())]
        trail = s[len(s.rstrip()):]
        return lead + d.strip() + trail
    out = []
    changed = False
    for p in parts:
        if p == "":
            return None
        d = tok(p)
        if d is None:
            return None
        # ⚠️ 2026-09-29 修：tok() 会 strip 段落前后空格，若直接 join 就会产出
        #    「I.R. 136/ 46. I.D. → I.R. 136/46. I.D.」这类**只去空格、并无翻译**的
        #    伪译文（13 条逃过 d==s 判定并混入批次表）。现要求至少一段真被改动。
        if d.strip() != p.strip():
            changed = True
        out.append(d)
    if not changed:
        return s                      # 无任何段落被翻译 ⇒ 原样返回（主逻辑将跳过）
    return "/".join(out)


def main():
    argv = sys.argv[1:]
    def opt(name, dflt):
        return argv[argv.index(name) + 1] if name in argv else dflt
    todo_f = os.path.join(HERE, opt("--todo", "_xscn_todo3.tsv"))
    out_f = os.path.join(HERE, opt("--out", os.path.basename(OUT)))
    minf = int(opt("--minfreq", "1"))
    todo = []
    with io.open(todo_f, encoding="utf-8", newline="") as f:
        for i, ln in enumerate(f.read().replace("\r\n", "\n").split("\n")):
            if i == 0 or not ln.strip():
                continue
            c = ln.split("\t")
            if len(c) >= 2 and int(c[1]) >= minf:
                todo.append(c[0])

    rows, skipped = [], []
    for s in todo:
        # 守卫：**散文句**一律整条保留 —— 曾把 `Hold 8 VHs ... TV/MV` 的 `MV` 当罗马数字
        #       译成「第1005」。链条只在「不含逗号 且 词数<=3」时才允许规则处理。
        if "," in s or len(s.split()) >= 4:
            skipped.append((s, "散文句 ⇒ 整条保留"))
            continue
        # 守卫：**畸形**方括号一律口径保留 —— `54A]` 曾被译成「第54集团军」而丢掉 `]`。
        #       ⚠️ 但 `3/3 [48]` 这类「番号链 + 空格 + 平衡方括号」**应放行**（BRACKET_TAIL 处理）。
        if ("[" in s or "]" in s) and not BRACKET_TAIL.match(s):
            skipped.append((s, "畸形方括号 ⇒ 口径保留"))
            continue
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

    with io.open(out_f, "w", encoding="utf-8", newline="") as f:
        f.write("src\tdst\n")
        for s, d in rows:
            f.write("%s\t%s\n" % (s, d))
    print("%s: 输出 %d 条 / 跳过 %d 条（minfreq=%d；跳过＝保持原文）"
          % (os.path.basename(out_f), len(rows), len(skipped), minf))
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
