#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""16 处简介污染：按用户裁定「撰写新简报」修复（20261020）。

纪律：
  · 每场的身份由「地图(@11210) + _m行0 + 地图字标 + 战役路径xls + 前后场序列」交叉锁定
  · 英文原件写入 backup（旧污染原件另存 .broken-orig），中文进 ww2-scn-map.tsv
  · 文风严格对齐同战役相邻场的既有格式（RTB 三行式 / RM 名-日期-散文 / SL 冒号式 …）
  · 不臆造游戏性数据（回合数/胜利条件/增援——未知则不写）
  · 行级整串进词表；与既有键冲突（异译）时报冲突且**不覆盖**
dry-run 默认；--apply 才写。
"""
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
BK = os.path.join(WS, "pegww2", "testbed", "backup", "SCENARIO")
MAP = os.path.join(WS, "pegww2", "research", "ww2-scn-map.tsv")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsv_esc import esc, unesc  # noqa: E402

TAG = "撰写-20261020"

# (目标stem, [(en, zh), ...])  —— ("","") 为空行
JOBS = [
    # ── RTB#31：里加（xls=Riga(24)/Dieppe图 + RM跨档同名佐证；_m行0「卡拉奇」疑借用，另报）
    ("RTB24_i", [
        ("Riga (RTB#24)", "里加 (RTB#24)"),
        ("September 14, 1944", "1944年9月14日"),
        ("The Red Army opens the Riga offensive, driving to cut Army Group North off from the Baltic coast.",
         "苏军发起里加(Riga)攻势，直插波罗的海(Baltic)沿岸，力图切断北方集团军群的陆上联系。"),
    ]),
    # ── RG#2：堵住缺口（_m行0+地图字标+xls「Plugging the gap」三方一致；RG2=1945-10-07 之前）
    ("RG_usvsruss1_i", [
        ("Plugging the Gap - September 16th, 1945", "堵住缺口 - 1945 年 9 月 16 日"),
        ("Commander, the Red Army has torn a gap in our line along the Moselle and is pouring armor toward Arracourt. You will seal the breach and destroy their spearheads before the whole front unravels. Good luck, Commander.",
         "指挥官，红军已在摩泽尔河(Moselle)一线撕开一道缺口，装甲集群正向阿拉库尔(Arracourt)涌来。你必须封住缺口、歼灭其矛头，否则整条战线都将瓦解。祝好运，指挥官。"),
    ]),
    # ── RG#14：波美拉尼亚壁垒（RG12=1946-06-30 / RG14=1946-08-05 之间）
    ("RG_usvsruss13_i", [
        ('Wal Pomorski - "Pommernstellung" - July 14th, 1946',
         "波美拉尼亚壁垒(Wal Pomorski) -「波美拉尼亚阵地」(Pommernstellung) - 1946 年 7 月 14 日"),
        ("Commander, the Red Army is massing for a decisive assault on the Pommernstellung position. You will hold the wall at all costs and bleed their tank armies white. One last thing: expect their air force to contest every mile of this battle.",
         "指挥官，红军正在集结兵力，准备对「波美拉尼亚阵地」发动决定性突击。你必须不惜一切代价守住壁垒，让他们的坦克集团军在此流尽鲜血。最后一件事：预计敌空军将在这场战斗中争夺每一英里的天空。"),
    ]),
    # ── RM#8：突击阿拉库尔（_i行0+洛林字标一致；RM 散文式）
    ("RM_usvsruss7_i", [
        ("Assault on Arracourt", "突击阿拉库尔(Arracourt)"),
        ("September 19, 1944", "1944年9月19日"),
        ("Herr General, Patton's Third Army has crossed the Moselle and its armor is probing toward the Saar. You will counterattack at once with the panzer reserves, smash the American spearheads around Arracourt and throw them back across the river.",
         "将军阁下，巴顿(Patton)的第3集团军已渡过摩泽尔河(Moselle)，其装甲矛头正向萨尔(Saar)方向推进。你须立即率装甲预备队发起反击，粉碎阿拉库尔(Arracourt)地域的美军矛头，把他们赶回到河对岸。"),
    ]),
    # ── RM#9：马耳他（_m行0=马耳他+马耳他字标；_i行0「施图登特」正合空降马耳他的策划者）
    ("RM_usvsruss8_i", [
        ("Malta", "马耳他"),
        ("July 13, 1942", "1942年7月13日"),
        ("Herr General, the time has come to eliminate the British fortress of Malta once and for all. General Student's paratroops will drop onto the northern airfields while the assault convoys close in from the sea. Take the island and open the sea lanes to Africa.",
         "将军阁下，彻底拔除马耳他(Malta)这座英国要塞的时机已经成熟。施图登特(Student)将军的空降兵将伞降夺取岛北各机场，突击船队同时从海上逼近。夺取该岛，打通通往非洲的海上航道。"),
    ]),
    # ── RM#10：普罗霍夫卡车站（_m行0+地图PROKHORV+字标三方一致；_i行0「乌兰乌德」系借用）
    ("RM_usvsruss9_i", [
        ("Prokhorovka Station", "普罗霍夫卡车站"),
        ("July 12, 1943", "1943年7月12日"),
        ("Herr General, the II SS Panzer Corps drives on Prokhorovka to rip open the southern face of the Kursk salient. The Soviet 5th Guards Tank Army is rushing to meet you head-on. Win this armored clash and the salient lies open.",
         "将军阁下，亲卫队第2装甲军正向普罗霍夫卡(Prokhorovka)突击，以期撕开库尔斯克(Kursk)突出部的南面。苏军近卫第5坦克集团军正迎面扑来。赢下这场装甲对决，突出部就将门户大开。"),
    ]),
    # ── RM#20：托布鲁克（_m行0+_i行0+北非字标一致）
    ("RM_usvsruss19_i", [
        ("Tobruk", "托布鲁克"),
        ("June 20, 1942", "1942年6月20日"),
        ("Herr General, after Gazala the remnants of the British Eighth Army have holed up inside the Tobruk perimeter. Panzerarmee Afrika attacks at dawn: breach the wire, seize the harbor and force the garrison to surrender before nightfall.",
         "将军阁下，加扎拉(Gazala)之战后，英国第8集团军残部龟缩进托布鲁克(Tobruk)环形阵地。非洲装甲集团军将于拂晓发起强攻：突破外围防线、夺取港口，迫使守军在天黑之前投降。"),
    ]),
    # ── SL#13：格洛斯特（_m行0+英格兰字标一致；SL03=布里斯托尔→SL05=进逼伦敦，本场次居中）
    ("SL_SLL04_i", [
        ("Gloucester:", "格洛斯特："),
        ("Herr General, Bristol has fallen and the Severn crossings are ours. Your kampfgruppe now drives north-east on Gloucester: take the city and its docks before the British can improvise a new defensive line along the Severn. Every day of delay lets them dig in deeper.",
         "将军阁下，布里斯托尔(Bristol)已经易手，塞文河(Severn)各渡口已在我们手中。你的战斗群现在向东北直取格洛斯特(Gloucester)：赶在英国人沿塞文河拼凑出新防线之前，夺取该城及其码头。每拖延一天，他们的工事就坚固一分。"),
    ]),
    # ── ZS#14：柏林最终突击（_m行0+Seelow图+奥得河字标一致；_i「温莎1943」系借用）
    ("ZS_berl_i", [
        ("Operacja Berlinska (ZS#14), 04/16/1945", "柏林行动(Operacja Berlinska) (ZS#14)，1945 年 4 月 16 日"),
        ("Comrade General, this is the final assault. Our fronts cross the Oder along the whole line: break through the Seelow Heights, crush the remnants of the Wehrmacht and raise the red banner over Berlin! For the Motherland!",
         "将军同志，这是最后的突击。我各方面军正沿全线强渡奥得河(Oder)：突破塞洛高地(Seelow Heights)，碾碎国防军残部，把红旗插上柏林(Berlin)城头！为了祖国！"),
    ]),
    # ── italy#12：哥特防线东部（_m行0+里米尼字标+xls 1944-08-25 一致）
    ("ita12_i", [
        ("Gothic Line East", "哥特防线东部"),
        ("In late August 1944 the British 8th Army opened Operation Olive along the Adriatic coast, aiming to rupture the eastern end of the Gothic Line, take Rimini and break out into the Po plain. Hold the ridge lines and the Conca crossings - the Line must not break here.",
         "1944 年 8 月下旬，英国第8集团军沿亚得里亚海(Adriatic)沿岸发起「橄榄枝」行动(Operation Olive)，企图撕裂哥特防线(Gothic Line)东端、夺取里米尼(Rimini)并突入波河(Po)平原。守住山脊线与孔卡河(Conca)各渡口——防线绝不能在这里被突破。"),
    ]),
    # ── R7#7：天王星行动窗口（r706=1942-09-07 格罗兹尼 / r708=1943-01-09 冬季风暴，本场次居中；DON图）
    ("r707_i", [
        ("Marching Orders (#7) - November 19, 1942", "行军命令 (#7) - 1942 年 11 月 19 日"),
        ("The Red Army has opened a massive offensive on the Don bend, smashing into the sectors held by our Romanian allies. General, the Leader demands that you hold the river line and cover the flanks of our Stalingrad armies. Counterattack at once and restore the front.",
         "红军在顿河(Don)弯道发起了大规模反攻，直冲罗马尼亚盟军据守的地段。将军，领袖要求你坚守沿河一线，掩护我斯大林格勒(Stalingrad)集团的两翼。立即反击，恢复战线。"),
    ]),
    # ── s00#11：杰拉（_m行0+西西里字标+PG2表 s0010=Gela 25/OCT/1945 一致；s0011=西西里 1945-11-15 紧邻）
    ("s0010_i", [
        ("Gela - October 25th, 1945", "杰拉(Gela) - 1945 年 10 月 25 日"),
        ("Comrade! The imperialists have landed at Gela on the southern coast of Sicily, trying to split our forces on the island in two. You are the nearest commander with available troops: seal off the beachhead and hurl them back into the sea before their armor comes ashore.",
         "同志！帝国主义者在西西里岛(Sicily)南岸的杰拉(Gela)地域登陆，企图把我在岛集团切成两段。你是就近唯一握有可用部队的指挥员：封锁滩头阵地，趁敌装甲兵力尚未上岸，把他们赶回大海。"),
    ]),
    # ── GAW#26：1944年冬（_m行0+DUBNO图+卢茨克/罗夫诺字标一致；GAW24=莫斯科43→GAW26=巴格拉季昂）
    ("GAW25_i", [
        ("Winter 1944 - February 1st, 1944", "1944年冬 - 1944 年 2 月 1 日"),
        ("Herr General,", "将军阁下，"),
        ("The Soviet winter offensive is rolling toward the Lutsk-Rovno sector and our front there is giving way. You will take over the sector, stop their rifle divisions and counterattack before the spring mud paralyzes all movement.",
         "苏军冬季攻势正扑向卢茨克(Lutsk)—罗夫诺(Rovno)方向，我军该地段正在动摇。你立即接管该地段，挡住敌步兵集团，并赶在春季泥泞瘫痪一切机动之前发起反击。"),
    ]),
    # ── G7#16：英格兰中部（xls=England:Midlands + 前场=海狮43成功 + 后场=圣乔治'45，故事链自洽；
    #    _m行0「冬季风暴行动 (#8)」疑借用 r708 名，另报名栏核准）
    ("G7pzra716_i", [
        ("English Midlands'43 - November 9th, 1943", "英格兰中部'43 - 1943 年 11 月 9 日"),
        ("Herr General, Sea Lion has succeeded beyond expectation: London is encircled and the British army is falling back in disorder. Your panzers now drive into the Midlands to seize Birmingham and the industrial heart of England before the enemy can form a new front.",
         "将军阁下，「海狮」的成功超乎预期：伦敦(London)已被合围，英军正溃不成军地后撤。你的装甲集群现在挺进中部地区，赶在敌人重组战线之前，夺取伯明翰(Birmingham)与英格兰的工业心脏。"),
    ]),
    # ── DR#32：郊区！（_m行0经覆盖表有意定为「郊区！」；xls=Vienna收官场；维也纳城郊 1945-04）
    ("drvien32_i", [
        ("Suburbs! - April 11th, 1945", "郊区！ - 1945 年 4 月 11 日"),
        ("Vienna is falling. Your division is ordered to fight a delaying action in the suburbs, holding the southern approaches while the remnants of the corps disengage to the west. Make the Russians pay for every street, Herr General - and then get your men out.",
         "维也纳(Vienna)即将陷落。你师奉命在城郊实施迟滞作战，扼守南面通道，掩护军残部向西脱离接触。让俄国人为每一条街道付出代价，将军阁下——然后把你的人带出来。"),
    ]),
    # ── konrad：Kd.TXT（konrad/konrad-R 共用；匈牙利维斯普雷姆字标+康拉德行动 1945-01-01）
    ("Kd", [
        ("Operation Konrad", "「康拉德」行动"),
        ("", ""),
        ("January 1, 1945", "1945年1月1日"),
        ("", ""),
        ("The IV SS Panzer Corps strikes from the Veszprem area to break the Soviet ring around Budapest and relieve the encircled garrison. The attack must succeed before the city falls.",
         "亲卫队第4装甲军自维斯普雷姆(Veszprem)地域发起突击，打破苏军对布达佩斯(Budapest)的合围圈，解救被围守军。必须在城市陷落之前达成突破。"),
    ]),
]


def find_ci(d, name):
    hit = [n for n in os.listdir(d) if n.lower() == name.lower()]
    return hit[0] if hit else None


def main():
    apply_ = "--apply" in sys.argv
    sys.stdout.reconfigure(encoding="utf-8")
    # 1) 载入既有词表键（unesc 后），查冲突
    existing = {}
    with io.open(MAP, encoding="utf-8-sig") as f:
        for ln in f:
            s = ln.rstrip("\r\n")
            if not s or s.startswith("#") or s.split("\t")[0].strip() == "原文":
                continue
            c = s.split("\t")
            if len(c) >= 3 and c[0].strip():
                existing[unesc(c[0])] = unesc(c[1])
    print(f"既有词表键 {len(existing)} 条")
    # 2) 逐目标：写 backup（.broken-orig 留存）+ 收集新增词
    new_entries, conflicts, done = [], [], []
    for stem, pairs in JOBS:
        fn = find_ci(BK, stem + ".txt")
        if not fn:
            print(f"❌ backup 未找到 {stem}.txt")
            continue
        p = os.path.join(BK, fn)
        raw = open(p, "rb").read()
        eol = b"\r\n" if b"\r\n" in raw else b"\n"
        if apply_:
            orig = p + ".broken-orig"
            if not os.path.isfile(orig):
                open(orig, "wb").write(raw)
            body = eol.join(x[0].encode("latin-1") for x in pairs)
            open(p, "wb").write(body)
        for en, zh in pairs:
            if not en:
                continue
            if en in existing:
                if existing[en] != zh:
                    conflicts.append((fn, en, existing[en], zh))
                continue
            new_entries.append((en, zh))
            existing[en] = zh
        done.append((fn, len(pairs)))
    print(f"目标 {len(done)} 个，新增词表行 {len(new_entries)}，冲突 {len(conflicts)}")
    for fn, en, old, new in conflicts:
        print(f"  ⚠️ 冲突 {fn}: {en[:50]!r} 既有={old[:30]!r} 新={new[:30]!r}")
    if conflicts:
        print("有冲突，未写任何文件" if not apply_ else "有冲突，词表未追加")
        return
    if apply_:
        with io.open(MAP, "a", encoding="utf-8") as f:
            f.write("# ── 简介撰写修复（20261020 · 16 场污染简报，用户裁定①逐场撰写）──\n")
            for en, zh in new_entries:
                f.write(f"{esc(en)}\t{esc(zh)}\t{TAG}\n")
        print("[APPLY] backup 与词表已写入")
    else:
        print("[DRY-RUN] 未写任何文件；--apply 执行")


if __name__ == "__main__":
    main()
