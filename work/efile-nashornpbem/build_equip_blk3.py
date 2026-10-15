# -*- coding: utf-8 -*-
"""生成 equip-blk3.zh.tsv（GBK / CRLF / 无 BOM）。
严格按 POLICY.md 四步判定：型号+编号 原样保留；兵种/编制/后勤词译中文；
数字/口径+通用名词 数字保留名词译；修饰语+兵种 修饰语译型号保留。
括号注记 (not used) / (PBEM) 等原样保留。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "equip-blk3.tsv")
OUT = os.path.join(HERE, "out", "equip-blk3.zh.tsv")

# 行号 -> 译文（仅需译出的行；未列出者按规则1原样保留）
TR = {
370: "掩体 (not used)",
372: "摩托车 (not used)",
373: "7,5 反坦克炮 早期型 40 (not used)",
375: "固定重型火箭发射器(B) (not used)",
378: "山地步兵 40 (not used)",
379: "步兵 35 7,5 轻炮 (not used)",
380: "步兵迫击炮 40 (not used)",
382: "重型岸防炮台 (not used)",
383: "浮桥 (not used)",
385: "伞兵轻型迫击炮 (not used)",
387: "75 野战反坦克炮 (not used)",
388: "中型榴弹炮 (not used)",
389: "装甲侦察(f) (not used)",
390: "Pz 侦察 (not used)",
391: "Pz II 两栖 (not used)",
392: "Pz II 喷火 (not used)",
404: "Me-262A 后期型 (not used)",
405: "He-115 水上飞机 (not used)",
406: "Hs-123 双翼机 (not used)",
407: "Hs-129C 夜间战斗轰炸机 (not used)",
408: "Hs-129 侦察 (not used)",
414: "党卫军黑衫军 38 骑兵 (not used)",
415: "反坦克障碍 (not used)",
416: "路障 (not used)",
417: "工厂 (not used)",
420: "登陆艇 (not used)",
422: "37mm 防空 (not used)",
423: "超重型岸防炮台 (not used)",
424: "土质机场 (not used)",
425: "马车 (not used)",
426: "半履带牵引车 (not used)",
427: "轻型卡车 (not used)",
428: "野战炮 (r) (not used)",
429: "105 野战反坦克炮 (not used)",
431: "雷达 CL (not used)",
432: "黑衫军民兵 (not used)",
433: "HQ 盖世太保",
434: "党卫军 10.5cm 野战炮 (not used)",
437: "战斗轰炸水上飞机 (not used)",
440: "发电站 (not used)",
441: "铁路桥 (not used)",
442: "党卫军轻型迫击炮 (not used)",
443: "阿尔卑斯架桥步兵 (not used)",
444: "警察步兵",
445: "BA-6 装甲车",
446: "7.6cm 反坦克炮",
447: "5.5cm 反坦克炮",
449: "运输车",
450: "马车",
452: "铁路运输",
453: "铁路运输",
454: "西伯利亚重型迫击炮",
455: "A-19 重炮",
458: "卡车 MGx2",
470: "运输机",
471: "伞兵运输机",
472: "伞兵滑翔机",
474: "突击艇",
475: "半履带车 (not used)",
478: "突击部队 (not used)",
488: "P39 战斗轰炸机 (not used)",
490: "Katyuska 火箭炮 (not used)",
491: "105 野战反坦克炮 (not used)",
492: "轻型 Katyuska 卡车 (not used)",
493: "BT-7 轻型 CS 坦克 (not used)",
494: "BT-7 CS 坦克 (not used)",
495: "BT-7 侦察坦克 (not used)",
497: "100mm 炮台 (not used)",
498: "重型 76mm 反坦克炮 (not used)",
499: "水上运输机 (not used)",
500: "P63 战斗轰炸机 (not used)",
501: "土质机场 (not used)",
502: "大型轰炸机 (not used)",
503: "重型岸防炮台 (not used)",
504: "Pe-2 轰炸机 (not used)",
505: "T-28 两栖坦克 (not used)",
506: "舰炮 (not used)",
507: "轻型自行反坦克炮 (not used)",
508: "反坦克炮运输车 (not used)",
509: "D-10 野战炮 (not used)",
510: "75 野战反坦克炮 (not used)",
511: "122mm 远程炮台 (not used)",
512: "火箭 CS 坦克 (not used)",
513: "重型机枪支援 (not used)",
516: "轻型喷火坦克 (not used)",
517: "T-35 突击型 (not used)",
518: "I-16 运输车 (not used)",
519: "Pe-3 运输车 (not used)",
520: "Ar-2 轰炸机 (not used)",
521: "Tb 轰炸机 (not used)",
522: "轰炸机 (not used)",
526: "狙击小组 (not used)",
527: "近卫军+T34/85 (not used)",
528: "快速卡车 (not used)",
529: "两栖卡车 (not used)",
530: "重型马车 (not used)",
531: "轻型空中机动炮兵 (not used)",
532: "早期自行反坦克炮 (not used)",
533: "自行火炮 (not used)",
534: "弹坑 (not used)",
536: "指挥车",
537: "M16 MG(4) 防空 (not used)",
}

def main():
    src = open(SRC, "rb").read().decode("utf-8")
    rows = []
    for ln in src.splitlines():
        if not ln.strip():
            continue
        num, txt = ln.split("\t", 1)
        rows.append((num.strip(), txt))

    out_lines = []
    kept = 0
    for num, txt in rows:
        n = int(num)
        if n in TR:
            zh = TR[n]
        else:
            zh = txt.strip()
            kept += 1
        assert "\t" not in zh and "\n" not in zh and "\r" not in zh, num
        out_lines.append("%s\t%s" % (num, zh))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    data = ("\r\n".join(out_lines) + "\r\n").encode("gbk")
    open(OUT, "wb").write(data)
    print("rows=%d translate=%d keep=%d" % (len(rows), len(TR), kept))

if __name__ == "__main__":
    main()
