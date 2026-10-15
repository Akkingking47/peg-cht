# -*- coding: utf-8 -*-
"""
B4 EFILE_BASEKORP 根级四件套生成器
产出：D:/OpenPG2/EFILE_BASEKORP/TEXT-ZH/{equip,names,nations,strings_efile}.txt
编码 GBK / 无 BOM / 与原文逐行对齐。
"""
import os, re, json, sys

GAME = "D:/OpenPG2/EFILE_BASEKORP"
OUT = os.path.join(GAME, "TEXT-ZH")
WORK = "work/basekorp"

def read_cp1252(p):
    return open(p, "rb").read().decode("cp1252")

def write_gbk(p, text):
    data = text.encode("gbk")   # 变音符会抛异常 => 暴露问题
    tmp = p + ".new"
    with open(tmp, "wb") as f:
        f.write(data)
    # 回读校验
    assert open(tmp, "rb").read() == data
    os.replace(tmp, p)

def split_keep(text):
    """按 \n 切，保留行尾 \r；返回 [(core, cr)]"""
    parts = text.split("\n")
    out = []
    for i, p in enumerate(parts):
        cr = p.endswith("\r")
        out.append((p[:-1] if cr else p, cr))
    return out

def join_keep(rows):
    return "\n".join(core + ("\r" if cr else "") for core, cr in rows)

# ---------- nations ----------
def gen_nations():
    src = split_keep(read_cp1252(f"{GAME}/nations.txt"))
    # 复用映射（来自已交付 efile nations.txt 的英文->中文）
    REUSE = {
        "Axis":"轴心国","Allied":"盟军","All Countries":"所有国家",
        "Slovakia":"斯洛伐克","Belgium":"比利时","Bulgaria":"保加利亚",
        "Czechoslovakia":"捷克斯洛伐克","Denmark":"丹麦","Finland":"芬兰",
        "France":"法国","Germany":"德国","Greece":"希腊","USA":"美国",
        "Hungary":"匈牙利","Turkey":"土耳其","Italy":"意大利",
        "Netherlands":"荷兰","Norway":"挪威","Poland":"波兰",
        "Portugal":"葡萄牙","Romania":"罗马尼亚","Croatia":"克罗地亚",
        "Sweden":"瑞典","United Kingdom":"英国","Yugoslavia":"南斯拉夫",
        "Nationalist Spain":"西班牙国民军","Republican Spain":"西班牙共和国",
        "Australia":"澳大利亚","Canada":"加拿大","Ethiopia":"埃塞俄比亚",
        "New Zealand":"新西兰","South Africa":"南非",
        "Free French Forces":"自由法国部队","Japan":"日本",
        "Euzko Gudarostea":"巴斯克义勇军","Estonia":"爱沙尼亚",
        # 4 个新增（按 WWII 语境与既有口径）
        "Russia":"苏联","Allied Yugoslavia":"盟国南斯拉夫",
        "SS":"武装党卫军","Japanese Navy":"日本海军",
    }
    rows = []
    for core, cr in src:
        s = core.strip()
        if s in REUSE:
            rows.append((REUSE[s], cr))
        else:
            rows.append((core, cr))
    write_gbk(f"{OUT}/nations.txt", join_keep(rows))
    n = sum(1 for r in rows if any(0x4e00 <= ord(c) <= 0x9fff for c in r[0]))
    print(f"nations.txt: {len(rows)} 行, {n} 行含汉字")

# ---------- strings_efile ----------
def gen_strings_efile():
    src = split_keep(read_cp1252(f"{GAME}/strings_efile.txt"))
    # 来自 ATOMIC/AO/OLGWW2/AG 的内容键映射（英文->中文）
    M = {
        "Axis":"轴心国","Allied":"盟军",
        "Brilliant Victory":"辉煌胜利","Victory":"胜利","Tactical Victory":"战术胜利","Loss":"失败",
        "Soft target":"软目标","Hard target":"硬目标","Air target":"空中目标","Naval target":"海上目标",
        "Ground":"地面","Air":"空中",
        "Tracked":"履带","Half Tracked":"半履带","Wheeled":"轮式","Leg":"徒步","Towed":"牵引",
        "Deep Naval":"远洋","Coastal":"近海","4wd":"四驱","Amphibious":"两栖","Naval":"海军",
        "Ranger":"游骑兵","Train":"列车","Helicopter":"直升机",
        "Road Train":"公路列车",
        "Cannot be transported":"无法运输","Airmobile":"空中机动","Airborne":"空降",
        "None":"无","Infantry":"步兵","Tank":"坦克","Recon":"侦察","Anti-Tank":"反坦克",
        "Flak":"高射炮","Fortification":"要塞","Ground Transport":"地面运输",
        "Rail Transport":"铁路运输","Artillery":"炮兵","Air-Defence":"防空",
        "Fighter":"战斗机","Dive Bomber":"俯冲轰炸机","Level Bomber":"重型轰炸机",
        "Air Transport":"运输机","Helo Transport":"直升机运输","Submarine":"潜艇",
        "Destroyer":"驱逐舰","Capitol Ship":"主力舰","Carrier":"航空母舰",
        "Naval Transport":"海上运输",
        # classes 尾部 3 条（BASEKORP 特有）
        "Spare Empty":"备用空格","Installations":"设施","Special Units":"特种部队",
        "Switch Ground+Air / Naval units menu":"切换 陆空/海军 单位菜单",
        "Select Anti-Aircraft":"选择防空","Select Support Weapons":"选择支援武器",
        "Select Fortification":"选择要塞","Select Anti-Tank":"选择反坦克",
        "Select Artillery":"选择炮兵","Select Infantry":"选择步兵","Select Recon":"选择侦察",
        "Select Tanks":"选择坦克","Select Fighters":"选择战斗机",
        "Select Dive Bombers":"选择俯冲轰炸机","Select Level Bombers":"选择重型轰炸机",
        "Select Submarine":"选择潜艇","Select Destroyer":"选择驱逐舰",
        "Select Capitol Ship":"选择主力舰","Select Carrier":"选择航空母舰",
        "Select Spare Empty":"选择备用空格","Select Installation":"选择设施",
        "Select Special Units":"选择特种部队",
        "Name unit":"命名部队","Reassign Unit":"重新指派","Exit":"退出",
        "CLEAR":"开阔地","TOWN":"城镇","AIRFIELD":"机场","Forest":"森林","Bocage":"树篱地",
        "HILL":"丘陵","MOUNTAIN":"山地","SAND":"沙漠","SWAMP":"沼泽","OCEAN":"海洋",
        "RIVER":"河流","FORTIFICATION":"要塞","PORT":"港口","STREAM":"溪流",
        "ESCARPMENT":"断崖","Major River":"大河","ROUGH":"崎岖地","Rubble":"瓦砾",
        "ROADS":"公路","RAILS":"铁路",
    }
    rows = []
    for core, cr in src:
        s = core.strip()
        if s in M:
            rows.append((M[s], cr))
        else:
            rows.append((core, cr))     # 保留 * 注释头、段头、空行
    write_gbk(f"{OUT}/strings_efile.txt", join_keep(rows))
    n = sum(1 for r in rows if any(0x4e00 <= ord(c) <= 0x9fff for c in r[0]))
    print(f"strings_efile.txt: {len(rows)} 行, {n} 行含汉字")

# ---------- names ----------
def gen_names():
    import json
    src = split_keep(read_cp1252(f"{GAME}/names.txt"))
    cm = {}
    for mp in ['work/atomic/_names-crossmap.json', 'work/ao/_names-crossmap.json']:
        cm.update(json.load(open(mp, encoding="utf-8")))
    # 占位模板串 'crap-dik-XXX'（等间距 31 行，各国姓后缀）与 'von Krap' 同源 ⇒ 保留原文
    # 编号条目 'NNN - Portugal' ⇒ 译国名，编号保留
    EXTRA = {
        "von Egerdorff": "冯·埃格尔多夫",
        "Puma": "普马",
        "555 - Portugal": "555 - 葡萄牙",
        "556 - Portugal": "556 - 葡萄牙",
        "557 - Portugal": "557 - 葡萄牙",
    }
    rows = []
    for core, cr in src:
        s = core.strip()
        if not s:
            rows.append((core, cr)); continue
        if s in cm:
            rows.append((cm[s], cr))
        elif s in EXTRA:
            rows.append((EXTRA[s], cr))
        elif "crap-dik" in s or s == "von Krap":
            rows.append((core, cr))      # 占位模板 ⇒ 保留
        else:
            rows.append((core, cr))      # 兜底：保留
    write_gbk(f"{OUT}/names.txt", join_keep(rows))
    n = sum(1 for r in rows if any(0x4e00 <= ord(c) <= 0x9fff for c in r[0]))
    print(f"names.txt: {len(rows)} 行, {n} 行含汉字")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    gen_nations()
    gen_strings_efile()
    gen_names()
