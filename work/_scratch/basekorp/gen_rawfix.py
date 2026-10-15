# -*- coding: utf-8 -*-
"""BASEKORP `.xscn` cp1252 残留修正表生成器。

背景：`.xscn` 槽位里 ä/ö/ü/ï/é 是 **cp1252 单字节**，而 `xscn.decode()` 先试 GBK
—— 高字节被解成 `鋑/鰎/黱` 这类**本身就是汉字码位**的假汉字，于是
`apply`（判 enc==ENC_OUT 跳过）和 `zhfix`（判 enc!=ENC_OUT 跳过）双双够不到。
`rawfix` 显式按 cp1252 读槽位、按原文 key 精确匹配，是唯一入口。

本表 key = **cp1252 原文**（含变音符），value = 中文。
12 条能从主表按「折写键」自动解析，96 条在此人工给出（口径见 RULES.md）。

产出 bk-xscn-rawfix.tsv（UTF-8 BOM / CRLF / src<TAB>dst）
"""
import io, os, re, sys, collections, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE))
MAP = os.path.join(HERE, 'bk-xscn-map.tsv')
OUT = os.path.join(HERE, 'bk-xscn-rawfix.tsv')

# ---------------------------------------------------------------- 人工译文
MANUAL = {
    # ---- 赫尔曼·戈林师族（HG 作为编制缩写保留，与先例 `II/HG1/…` 一致）
    'I/HG/Panzer-Division Hermann Göring': '第1/HG/赫尔曼·戈林装甲师',
    'II/HG/Panzer-Division Hermann Göring': '第2/HG/赫尔曼·戈林装甲师',
    'III/HG/Panzer-Division Hermann Göring': '第3/HG/赫尔曼·戈林装甲师',
    'IV/HG/Panzer-Division Hermann Göring': '第4/HG/赫尔曼·戈林装甲师',
    'HG/-/Panzer-Division Hermann Göring': 'HG/-/赫尔曼·戈林装甲师',
    'I/1HG/Panzer-Division Hermann Göring': '第1/1HG/赫尔曼·戈林装甲师',
    'II/1HG/Panzer-Division Hermann Göring': '第2/1HG/赫尔曼·戈林装甲师',
    'III/1HG/Panzer-Division Hermann Göring': '第3/1HG/赫尔曼·戈林装甲师',
    'I/2HG/Panzer-Division Hermann Göring': '第1/2HG/赫尔曼·戈林装甲师',
    'II/2HG/Panzer-Division Hermann Göring': '第2/2HG/赫尔曼·戈林装甲师',
    'III/2HG/Panzer-Division Hermann Göring': '第3/2HG/赫尔曼·戈林装甲师',
    'I/HG/Division Hermann Göring': '第1/HG/赫尔曼·戈林师',
    'II/HG/Division Hermann Göring': '第2/HG/赫尔曼·戈林师',
    'III/HG/Division Hermann Göring': '第3/HG/赫尔曼·戈林师',
    'HG/-/Division Hermann Göring': 'HG/-/赫尔曼·戈林师',
    'I/Jager-HG/Division Hermann Göring': '第1/猎兵-HG/赫尔曼·戈林师',
    'II/Jager-HG/Division Hermann Göring': '第2/猎兵-HG/赫尔曼·戈林师',
    'I/1 HG/Division Hermann Göring': '第1/第1 HG/赫尔曼·戈林师',
    'II/1 HG/Division Hermann Göring': '第2/第1 HG/赫尔曼·戈林师',
    'III/1 HG/Division Hermann Göring': '第3/第1 HG/赫尔曼·戈林师',

    # ---- 温舍战斗群（KG = Kampfgruppe → 战斗群，先例 [KG Waldmuller]）
    'I/12/Hitlerjugend [KG Wünsche]': '第1/第12/希特勒青年团 [温舍战斗群]',
    'III/12/Hitlerjugend [KG Wünsche]': '第3/第12/希特勒青年团 [温舍战斗群]',
    '12/-/Hitlerjugend [KG Wünsche]': '第12/-/希特勒青年团 [温舍战斗群]',
    'I/26/Hitlerjugend [KG Wünsche]': '第1/第26/希特勒青年团 [温舍战斗群]',
    'III/26/Hitlerjugend [KG Wünsche]': '第3/第26/希特勒青年团 [温舍战斗群]',
    'SS-Pz.Abt. [KG Wünsche]': '党卫军装甲营 [温舍战斗群]',
    's.SS-Pz.Abt. 101 [KG Wünsche]': '党卫军第101重型装甲营 [温舍战斗群]',
    'I/1/LSSAH [KG Wünsche]': '第1/第1/党卫军第1装甲师 [温舍战斗群]',

    # ---- 空降兵师（沿用批内已应用形式 `第N/第N/第N空降兵-师`）
    'I/6/6. Fallschirmjäger-Division': '第1/第6/第6空降兵-师',
    'II/6/6. Fallschirmjäger-Division': '第2/第6/第6空降兵-师',
    'III/6/6. Fallschirmjäger-Division': '第3/第6/第6空降兵-师',
    'I/19/7. Fallschirmjäger-Division': '第1/第19/第7空降兵-师',
    'II/19/7. Fallschirmjäger-Division': '第2/第19/第7空降兵-师',
    'III/19/7. Fallschirmjäger-Division': '第3/第19/第7空降兵-师',
    'I/22/8. Fallschirmjäger-Division': '第1/第22/第8空降兵-师',
    'II/22/8. Fallschirmjäger-Division': '第2/第22/第8空降兵-师',
    'III/22/8. Fallschirmjäger-Division': '第3/第22/第8空降兵-师',
    'I/24/8. Fallschirmjäger-Division': '第1/第24/第8空降兵-师',
    'II/24/8. Fallschirmjäger-Division': '第2/第24/第8空降兵-师',
    'III/24/8. Fallschirmjäger-Division': '第3/第24/第8空降兵-师',
    'I/32/8. Fallschirmjäger-Division': '第1/第32/第8空降兵-师',
    'II/32/8. Fallschirmjäger-Division': '第2/第32/第8空降兵-师',
    'III/32/8. Fallschirmjäger-Division': '第3/第32/第8空降兵-师',
    '8/-/8. Fallschirmjäger-Division': '第8/-/第8空降兵-师',

    # ---- 突尼斯 / 杰代达（Djedeïda）
    'Djedeïda Airfield': '杰代达机场',
    'The drive on Tunis - Battle for Djedeïda': '进军突尼斯 - 杰代达之战',
    'Elms. KG Djedeïda': '杰代达战斗群分队',
    'Elms. 501sPzAbt  KG Djedeïda': '第501重装甲营 杰代达战斗群分队',
    'Elms. 1./501sPzAbt  KG Lüder': '第1/第501重装甲营 吕德战斗群分队',
    'II/69/10PzDiv  KG Lüder': '第2/第69/第10装甲师 吕德战斗群',
    'Elms.3/7 Légion Garde': '第3/第7军团卫队分队',
    'Elms. 7 Légion Garde': '第7军团卫队分队',
    'Batterie de Mers el Kébir': '凯比尔港炮台',
    # ⚠️ 例外：奥兰/凯比尔港语境下 SS 是法国潜艇舰名前缀，不是党卫军。
    #    同文件 `SS Fresnel` 已被本批误译为「党卫军 弗雷内尔」，待一并改回。
    'SS Actéon': 'SS 阿克泰翁',

    # ---- 海军 / 巡洋舰（先例 `KM X`->`海军 X`；`CRG` 保留）
    'KM München': '海军 慕尼黑',
    'CRG München': 'CRG 慕尼黑',
    'KM Köln': '海军 科隆',
    'CRG Köln': 'CRG 科隆',
    ' 4. Zerstörer-Flottille': '第4驱逐舰分舰队',

    # ---- 匈牙利空军
    'Teile ung. JGr.101 / Jagdfliegerführer Ungarn':
        '残部 匈牙利第101战斗机大队 / 匈牙利战斗机航空兵指挥官',
    'II./JG51 Jagdfliegerführer Ungarn': '第2/第51战斗机联队 匈牙利战斗机航空兵指挥官',
    'II./JG52 Jagdfliegerführer Ungarn': '第2/第52战斗机联队 匈牙利战斗机航空兵指挥官',
    'I./JG53 Jagdfliegerführer Ungarn': '第1/第53战斗机联队 匈牙利战斗机航空兵指挥官',
    'I., IV./JG51 (Mölders)': '第1、第4/第51战斗机联队 (默尔德尔斯)',
    'SS-Brigadeführer August Zehender 22SS': '党卫军旅队长 奥古斯特·策亨德 第22党卫军',

    # ---- 地名
    'Zeebrügge': '泽布吕赫',
    'Königsberg': '柯尼斯堡',
    'Königsberger Haff': '柯尼斯堡潟湖',
    'Löwenhagen': '勒文哈根',
    'Pörschken': '珀施肯',
    'Mühlhausen': '米尔豪森',
    'Schönwalde': '舍恩瓦尔德',
    'Schönfeld': '舍恩费尔德',
    'Hohenfürst': '霍亨菲斯特',
    'Dörbeek': '德尔贝克',
    'Liebemühl': '利贝米尔',
    'Forst Liebemühl': '利贝米尔森林',
    'Bogunschöwen': '博贡舍文',
    'Löbau': '勒包',
    'Galánta': '加兰塔',
    'Déry': '德里',
    'Rácalmás': '拉卡尔马什',
    'Oberländischer Kanal': '奥伯兰运河',
    'Forst Födersdorf': '弗德斯多夫森林',
    'Staatsforst Födersdorf': '国有弗德斯多夫森林',
    'Kgl. Forst Födersdorf': '皇家弗德斯多夫森林',
    'Forst Coßwald': '科斯瓦尔德森林',
    '25/-/Pörschken Kp': '第25/-/珀施肯连',
    'Lake Mälar': '梅拉伦湖',
    'Lake Vänern': '维纳恩湖',
    'Lake Vättern': '韦特恩湖',
    'Ozero Beloïe': '别洛耶湖',
    'Rhône': '罗讷河',

    # ---- 其它
    'Unternehmen Wesserübung': '威悉演习行动',
    'Brückenkopf "Uncle Green"': '桥头堡 "绿色叔叔"',
    'Brückenkopf "Roger Green"': '桥头堡 "罗杰·格林"',
}


def fold(s):
    """中文侧折写规则：ö->o / ä->a / ß->ss …（与既有 efile 一致）"""
    s = s.replace('ß', 'ss')
    return ''.join(ch for ch in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(ch))


def scan():
    """扫描现状 vs 备份，取「未改且含 cp1252 高字节」的槽位原文。"""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'xscn'))
    import xscn
    cur = 'D:/OpenPG2/EFILE_BASEKORP/SCENARIO'
    bak = os.path.join(os.path.dirname(HERE), os.pardir,
                       'backup', 'ORIGINAL-EFILE_BASEKORP', 'SCENARIO')
    bak = os.path.normpath(bak)
    cnt = collections.Counter()
    for fn in sorted(os.listdir(bak)):
        if not fn.endswith('.xscn'):
            continue
        d1, i1, m1 = xscn.parse(os.path.join(cur, fn))
        d2, i2, m2 = xscn.parse(os.path.join(bak, fn))
        if i1 is None or i2 is None:
            continue
        for (g, idx, o1, L1), (_, _, o2, L2) in zip(xscn.slots_of(d1, i1, m1),
                                                    xscn.slots_of(d2, i2, m2)):
            a = xscn.raw_at(d1, o1, L1)
            b = xscn.raw_at(d2, o2, L2)
            if a == b and any(x > 127 for x in a):
                cnt[a.decode('cp1252')] += 1
    return cnt


def main():
    cnt = scan()
    print('cp1252 残留 唯一 %d / 实例 %d' % (len(cnt), sum(cnt.values())))
    main_map = {}
    for ln in io.open(MAP, encoding='utf-8-sig', newline='').read().split('\r\n')[1:]:
        if not ln.strip():
            continue
        c = ln.split('\t')
        if len(c) >= 2:
            main_map[c[0]] = c[1]

    # rawfix 用 raw.decode('cp1252').strip() 作 key，故两侧统一 strip
    manual = dict((k.strip(), v) for k, v in MANUAL.items())
    out, miss = {}, []
    for s in cnt:
        if s.strip() in manual:
            out[s.strip()] = manual[s.strip()]
            continue
        f = fold(s)
        if f.strip() in main_map and any('\u4e00' <= ch <= '\u9fff'
                                         for ch in main_map[f.strip()]):
            out[s.strip()] = main_map[f.strip()]
        else:
            miss.append((s, f))
    if miss:
        print('!! 未覆盖 %d 条：' % len(miss))
        for s, f in miss:
            print('   %-50r 折写=%r' % (s, f))
        raise SystemExit(1)

    bad = [(s, d) for s, d in out.items()
           if not any('\u4e00' <= ch <= '\u9fff' for ch in d)]
    if bad:
        print('!! 译文无汉字：')
        for s, d in bad:
            print('   %r -> %r' % (s, d))
        raise SystemExit(1)

    with io.open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('src\tdst\r\n')
        for s in sorted(out):
            f.write('%s\t%s\r\n' % (s, out[s]))
    print('修正表 %d 条 -> %s' % (len(out), OUT))
    print('  人工 %d / 主表解析 %d' % (sum(1 for s in out if s in manual),
                                       sum(1 for s in out if s not in manual)))


if __name__ == '__main__':
    main()
