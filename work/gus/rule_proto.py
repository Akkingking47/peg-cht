# -*- coding: utf-8 -*-
"""
方案 D 原型：EFILE_GUS 的 .xscn 串「按 token + 形态」翻译的覆盖率实测。

目的：证明「不逐串翻、只建 token 字典 + 少量规则」能覆盖多少条唯一串。
输入：D:\\DSH\\_s4_gus_full.tsv（xscn.py export --full 的真实串表）
      D:\\DSH\\_s4_miss.txt（30,703 条待定译串）
"""
import re, json, collections, sys

TOK = {
 # ---- 序数后缀（规则：<N>th -> 第<N>，此处 token 本身译为空）----
 "th": "", "nd": "", "st": "", "rd": "", "TH": "",
 # ---- 罗马数字 ----
 "I": "第1", "II": "第2", "III": "第3", "IV": "第4", "V": "第5", "VI": "第6",
 "VII": "第7", "VIII": "第8", "IX": "第9", "X": "第10", "XI": "第11",
 "XII": "第12", "XIII": "第13", "XIV": "第14", "XVI": "第16", "XIX": "第19",
 "XX": "第20", "XXI": "第21", "XXIV": "第24", "XXVIII": "第28", "XLVI": "第46",
 # ---- 德军 ----
 "InfDiv": "步兵师", "Inf": "步兵", "Infantry": "步兵", "Inf.": "步兵",
 "InfReg": "步兵团", "InfRgt": "步兵团", "IR": "步兵团", "PzDiv": "装甲师",
 "PanzDiv": "装甲师", "Panzer": "装甲", "Pz": "装甲", "Pz.": "装甲",
 "PzGrenDiv": "装甲掷弹兵师", "PzGrenReg": "装甲掷弹兵团", "PzGrRgt": "装甲掷弹兵团",
 "PzReg": "装甲团", "PzJgAbt": "反坦克营", "PzJagAbt": "反坦克营",
 "VolksGrenDiv": "国民掷弹兵师", "GrenReg": "掷弹兵团", "StrDiv": "强击师",
 "Leichte": "轻装师", "FJDiv": "伞兵师", "ArtReg": "炮兵团", "ArtRgt": "炮兵团",
 "Artb": "炮兵营", "AR": "炮兵团", "AAb": "炮兵营", "PionAbt": "工兵营",
 "AufklAbt": "侦察营", "Recb": "侦察营", "Flak": "高炮", "FlakAbt": "高炮营",
 "StuGAbt": "突击炮营", "Abt.": "营", "Abt": "营", "HQ": "司令部",
 "Hauptquartier": "司令部", "Rem": "残部", "Res": "预备队", "elem": "分队",
 # ---- 德国空军 ----
 "JG": "战斗机联队", "KG": "轰炸机联队", "StG": "俯冲轰炸机联队", "ZG": "驱逐机联队",
 "LG": "教导联队", "Luftfl.": "航空队", "LF": "航空队", "Fliegerkorps": "航空军",
 # ---- 苏军 ----
 "SD": "步兵师", "RD": "步兵师", "A": "集团军", "TA": "坦克集团军",
 "Gvd": "近卫", "Gwd": "近卫", "Guards": "近卫", "GRD": "近卫师",
 "TB": "坦克旅", "Tk": "坦克", "Tank": "坦克", "TC": "坦克军", "MD": "摩托化师",
 "NKWD": "内务人民委员部", "ShAD": "强击航空兵师", "BAD": "轰炸航空兵师",
 "IAP": "战斗机航空团", "PLotn.": "飞行团", "Lotnicza": "航空", "Corps": "军",
 # ---- 波军 ----
 "DP": "步兵师", "DStrz": "步兵师", "DywStrz": "步兵师", "ZmotD": "摩托化师",
 "BPanc": "装甲旅", "DywPanc": "装甲师", "CArmDiv": "加拿大装甲师",
 "CInfDiv": "加拿大步兵师", "DKaw": "骑兵师", "PU": "枪骑兵团", "pp": "步兵团",
 "PP": "步兵团", "PAL": "轻炮兵团", "PArt": "野战炮兵团", "PStrz": "步兵团",
 "PSK": "乘骑步枪团", "BK": "骑兵旅", "DAK": "骑炮营", "bPlot": "高射炮营",
 "PLotn": "飞行团", "Brygada": "旅", "Brig": "旅", "Brigade": "旅",
 "kompania": "连", "Baza": "基地", "TP": "坦克团", "BZ": "装甲旅",
 # ---- 英美 ----
 "AD": "装甲师", "ArmDiv": "装甲师", "ArmReg": "装甲团", "Armb": "装甲营",
 "ArmBrig": "装甲旅", "TD": "坦克师", "CD": "骑兵师", "Cav": "骑兵",
 "ABD": "空降师", "AirDiv": "空降师", "Abn": "空降", "GB": "滑翔",
 "Airfield": "机场", "RAF": "皇家空军", "RA": "皇家炮兵", "Royal": "皇家",
 "Field": "野战", "Mech": "机械化", "Mot": "摩托化", "mot": "摩托化",
 "Marine": "海军陆战队", "MG": "机枪", "HMS": "皇家海军", "USS": "美国海军",
 "CRG": "巡洋舰", "BRG": "战列巡洋舰", "Army": "集团军", "GuardArmDiv": "近卫装甲师",
 "GMC": "机械化骑兵群", "Regiment": "团", "Reg": "团", "Reg.": "团", "Rgt": "团",
 "Div": "师", "Div.": "师", "Division": "师",
 # ---- 党卫军 / 专名 ----
 "SS": "党卫军", "LSSAH": "警卫旗队", "LAH": "警卫旗队", "Das": "Das", "Reich": "帝国",
 "HG": "赫尔曼·戈林", "GD": "大德意志",
 # ---- 地名通名 ----
 "River": "河", "river": "河", "Rzeka": "河", "Bay": "湾", "Lake": "湖",
 "See": "湖", "Jezioro": "湖", "jezioro": "湖", "Island": "岛", "Airport": "机场",
 "Station": "车站", "Port": "港", "Canal": "运河", "Fort": "要塞", "Fortifiactions": "工事",
 "Hill": "山", "HILL": "高地", "Gora": "山", "hegy": "山", "erdo": "森林",
 "FOREST": "森林", "sur": "畔", "OPERATION": "行动", "de": "德", "El": "埃勒",
 "el": "埃勒", "Al": "阿尔", "San": "圣", "Bir": "井", "Bir.": "井",
}

# 纯规则：<数字>th/nd/st/rd -> 第<数字>
ORD = re.compile(r"(\d+)\s*(?:th|nd|st|rd)\b")
TOKEN = re.compile(r"[A-Za-z][A-Za-z.&']*")


def translate(s):
    """返回 (译文, 未覆盖 token 列表)"""
    body = ORD.sub(lambda m: "第" + m.group(1), s)
    miss = []

    def rep(m):
        t = m.group(0)
        if t in TOK:
            return TOK[t]
        if t in ("Das", "Reich"):
            return t
        miss.append(t)
        return t

    out = TOKEN.sub(rep, body)
    # 收尾清理：去掉 token 删除后产生的多余空格
    out = re.sub(r"\s+", " ", out).strip()
    return out, miss


def main():
    miss_set = set(x for x in open(r"D:\DSH\_s4_miss.txt", encoding="utf-8").read().split("\n") if x)
    rows = [l.rstrip("\n").split("\t") for l in open(r"D:\DSH\_s4_gus_full.tsv", encoding="utf-8") if l.strip()][1:]
    freq = {}
    for r in rows:
        if len(r) >= 2 and r[0].strip():
            try: freq[r[0].strip()] = int(r[1])
            except: freq[r[0].strip()] = 0

    print("token 字典 %d 条" % len(TOK))
    total = len(miss_set)
    full = 0; partial = 0
    uncovered_tok = collections.Counter()
    partial_ex = []; full_ex = []
    for s in sorted(miss_set):
        out, m = translate(s)
        if not m:
            full += 1
            if len(full_ex) < 12: full_ex.append((s, out))
        else:
            partial += 1
            for t in m: uncovered_tok[t] += 1
            if len(partial_ex) < 12: partial_ex.append((s, out, m))
    print("\n输入待译串 %d" % total)
    print("  完全覆盖 %d (%.1f%%)" % (full, 100*full/total))
    print("  仍有未覆盖 %d (%.1f%%)" % (partial, 100*partial/total))

    # 按频次加权
    wf = sum(freq.get(s, 1) for s in miss_set if not translate(s)[1])
    wt = sum(freq.get(s, 1) for s in miss_set)
    print("  按出现频次加权覆盖 %.1f%% (%d/%d)" % (100*wf/wt, wf, wt))

    print("\n=== 完全覆盖示例 ===")
    for s, o in full_ex: print("  %-34s -> %s" % (s[:34], o[:44]))
    print("\n=== 未覆盖示例 ===")
    for s, o, m in partial_ex: print("  %-34s -> %-30s  缺 %s" % (s[:34], o[:30], m[:4]))
    print("\n=== 未覆盖 token Top 40（下一步补字典的清单）===")
    for t, c in uncovered_tok.most_common(40):
        print("  %-14s %5d" % (t, c))
    print("\n未覆盖 token 种类 %d" % len(uncovered_tok))
    json.dump({"tok_dict": len(TOK), "total": total, "full": full,
               "uncovered": uncovered_tok.most_common()},
              open(r"D:\DSH\_proto_d.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("-> D:\\DSH\\_proto_d.json")


if __name__ == "__main__":
    main()
