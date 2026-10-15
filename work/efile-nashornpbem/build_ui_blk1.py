# -*- coding: utf-8 -*-
"""按 POLICY 第三节/第四节生成 ui-blk1.zh.tsv（GBK / CRLF / 无 BOM）。"""
import io, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "ui-blk1.tsv")
DST = os.path.join(BASE, "out", "ui-blk1.zh.tsv")

ZH = {
    # --- 三、国名 / 阵营 ---
    "Slovakians": "斯洛伐克",
    "Belgians": "比利时",
    "Bulgarians": "保加利亚",
    "Czechs": "捷克斯洛伐克",
    "Danish": "丹麦",
    "Finnish": "芬兰",
    "French": "法国",
    "Germans": "德国",
    "Greeks": "希腊",
    "Yanks": "美国",
    "Hungarians": "匈牙利",
    "Turks": "土耳其",
    "Italians": "意大利",
    "Dutch": "荷兰",
    "Norwegians": "挪威",
    "Poles": "波兰",
    "Portuguese": "葡萄牙",
    "Romanians": "罗马尼亚",
    "Croats": "克罗地亚",
    "Russians": "俄罗斯",
    "Swedes": "瑞典",
    "Communist Slavs": "共产主义斯拉夫人",
    "Brits": "英国",
    "Yugoslavs": "南斯拉夫",
    "Spanish Nationalists": "西班牙国民军",
    "Spanish Republicans": "西班牙共和军",
    "Australians": "澳大利亚",
    "Canadians": "加拿大",
    "Ethiopians": "埃塞俄比亚",
    "New Zealanders": "新西兰",
    "South Africans": "南非",
    # --- 四、[targets] ---
    "Soft target": "软目标",
    "Hard target": "硬目标",
    "Air target": "空中目标",
    "Special target": "特殊目标",
    # --- 四、[terrain]（顺序即地形 ID，逐项对应，不可变） ---
    "CLEAR": "开阔地",
    "CITY": "城市",
    "AIRFIELD": "机场",
    "WOODED": "森林",
    "BOCCAGE": "树篱地",
    "HILL": "丘陵",
    "HEAVY": "山地",
    "SAND": "沙漠",
    "MARSH": "沼泽",
    "DEEP WATER": "深海",
    "RIVER": "河流",
    "FORTIFICATION": "要塞",
    "PORT": "港口",
    "STREAM": "溪流",
    "ESCARPMENT": "断崖",
    "IMPASSABLE ROCKS": "不可通行岩地",
    "ROUGH": "崎岖地",
    "SHALLOW WATER": "浅水",
    "ROADS": "公路",
    "RAILS": "铁路",
    # --- 四、[unitdata] ---
    "Leader": "领袖",
    "Transport": "运输",
    "Country": "国家",
    "Experience": "经验",
    "Experience level": "经验等级",
    "Fuel": "燃料",
    "Ammo": "弹药",
    "Strength": "兵力",
    "Range": "射程",
    "Initiative": "主动权",
    "Spot": "侦察",
    "Mov.Method": "移动方式",
    "Hard Attack": "硬目标攻击",
    "Soft Attack": "软目标攻击",
    "Air Attack": "空中攻击",
    "Special Attack": "特殊攻击",
    "Ground defense": "地面防御",
    "Air defense": "对空防御",
    "Close defense": "近距防御",
    "Range defense modifier": "射程防御修正",
    "Class": "类别",
    "Cost": "造价",
}

with io.open(SRC, "r", encoding="utf-8") as f:
    raw = f.read()

lines = [ln for ln in raw.replace("\r\n", "\n").split("\n") if ln != ""]
out_lines = []
missing = []
for ln in lines:
    parts = ln.split("\t")
    assert len(parts) == 2, "列数异常: %r" % ln
    key, src = parts[0], parts[1].strip()
    if src not in ZH:
        missing.append((key, src))
        continue
    zh = ZH[src]
    assert "\t" not in zh and "\n" not in zh and "\r" not in zh
    out_lines.append("%s\t%s" % (key, zh))

if missing:
    sys.stderr.write("MISSING: %r\n" % (missing,))
    sys.exit(1)

data = "\r\n".join(out_lines) + "\r\n"
with io.open(DST, "wb") as f:
    f.write(data.encode("gbk"))

n_n = sum(1 for l in out_lines if l.startswith("N"))
n_s = sum(1 for l in out_lines if l.startswith("S"))
print("input=%d output=%d  N=%d S=%d" % (len(lines), len(out_lines), n_n, n_s))
