# -*- coding: utf-8 -*-
r"""
EFILE_AG（Antique General 3.4 Britannia，古代战争 mod）根级文件汉化生成器。

纪律：
  * 只写 <efile>\TEXT-ZH\，**绝不动原文**
  * 出稿 GBK(936) / 无 BOM / CRLF
  * 逐行对齐：注释行(*)与空行原样保留，未命中词必须报错（不许静默漏译）
用法：
  python make_ag_root.py            # dry-run，只报未命中
  python make_ag_root.py --apply    # 写盘（先备份到 backup/ag-root-before）
"""
import os, io, sys, shutil

GAME = r'D:\OpenPG2'
EF = 'EFILE_AG'
SRC = os.path.join(GAME, EF)
DST = os.path.join(SRC, 'TEXT-ZH')
BK = r'D:\DSH\军事游戏汉化\backup\ag-root-before'

# ---------------------------------------------------------------- nations
NAT = {
    'Side 1': '阵营一',
    'Side 2': '阵营二',
    'All Countries': '所有国家',
    'Romans': '罗马',
    'Celts': '凯尔特',
    'Huns': '匈奴',
    'rebellious Slaves': '起义奴隶',
    'Cilician Pirates': '奇里乞亚海盗',
    'Germans': '日耳曼',
    'Carthages': '迦太基',
    'Trojans': '特洛伊',
    'Achaians': '亚该亚',
    'Egyptians': '埃及',
    'Hittites': '赫梯',
    'Assyrians': '亚述',
    'Babylonians': '巴比伦',
    'Spartans': '斯巴达',
    'Athenian Confederacy': '雅典同盟',
    'Macedonians': '马其顿',
    'Persians': '波斯',
    'Indian Lords': '印度王公',
    'Numidians': '努米底亚',
    'Armenians': '亚美尼亚',
    'Parthians': '帕提亚',
    'Skythians': '斯基泰',
    'Etruscans': '伊特鲁里亚',
    'Chinese Empire': '中华帝国',
    'Natives': '土著',
    'Majas': '玛雅',
    'Polynesians': '波利尼西亚',
    'Saxony': '萨克森',
    'Franconians': '法兰克尼亚',
    'Roman Rebels': '罗马叛军',
    'Nubians': '努比亚',
    'Goths': '哥特',
    'Jews': '犹太',
    'Thrakians': '色雷斯',
    'Illyrians': '伊利里亚',
    'Britons': '不列颠',
    'Picts': '皮克特',
    'celtish Opponents': '凯尔特对手',
    'germanic Opponents': '日耳曼对手',
    'Western Roman Empire': '西罗马帝国',
    'Byzantine Empire': '拜占庭帝国',
    'Sarmatians': '萨尔马提亚',
    'Scoti': '斯科特人',
    'Thebes': '底比斯',
    # 占位标记：数据槽位标记，不是显示文本 ⇒ 保留原文
    '(empty)': '(empty)',
}

# ---------------------------------------------------------- strings_efile
# [terrain] 段 20 项与 OLGWW2 中文侧逐条一致（顺序相同），直接沿用既有译法。
SEF = {
    # [sides]
    'Side I': '阵营 I', 'Side II': '阵营 II',
    # [classes] —— 古代兵种，与二战 efile 不同，独立定名
    'None': '无', 'Infantry': '步兵', 'Cavalry': '骑兵', 'Scout': '侦察兵',
    'Spearmen': '长矛兵', 'Fortification': '要塞', 'Ground Transport': '地面运输',
    'Rail Transport ????': '铁路运输 ????', 'Archers': '弓箭手',
    'Spyprotection': '反间谍', 'Spy': '间谍',
    'Spy Transport': '间谍运输', 'Helo Transport ???': '直升机运输 ???',
    'Boat': '小船', 'Ship': '船舰', 'Naval-Transport': '海上运输',
    # [targets]
    'Soft': '软目标', 'Hard': '硬目标', 'Naval': '海军',
    # [spaces]
    'Ground': '地面',
    # [movement]
    'on horseback': '骑乘', 'light carriage': '轻型马车', 'heavy carriage': '重型马车',
    'Leg': '步行', 'Towed': '牵引', 'Incognito': '隐蔽',
    'on the high Seas': '远洋', 'Coastal': '沿海', 'All Terrain': '全地形',
    'Amphibious': '两栖', 'Mountain (Leg)': '山地（步行）',
    '--- Train ???': '--- 列车 ???', '--- Helicopter ???': '--- 直升机 ???',
    # [transports]
    'Cannot be transported': '无法运输', 'Airmobile': '空中机动', 'Airborne': '空降',
    '--- Zug ???': '--- 列车 ???',
    # [requisition]
    'Switch Ground/Spy/Naval menu': '切换地面/间谍/海军菜单',
    'Select Spyprotection': '选择反间谍', 'Select Fortification': '选择要塞',
    'Select Spearmen': '选择长矛兵', 'Select Archers': '选择弓箭手',
    'Select Infantry': '选择步兵', 'Select Scout': '选择侦察兵',
    'Select Cavalry': '选择骑兵', 'Select Spy': '选择间谍',
    'Select Boat': '选择小船', 'Select Ship': '选择船舰',
    'Name unit': '命名单位', 'Reassign Unit': '重新分配单位', 'Exit': '退出',
    # [terrain] —— 沿用 OLGWW2 既有定名
    'CLEAR': '开阔地', 'TOWN': '城镇', 'AIRFIELD': '机场', 'WOODED': '林地',
    'DENSE UNDERBRUSH': '密灌丛', 'HILL': '丘陵', 'MOUNTAIN': '山地',
    'SAND': '沙漠', 'SWAMP': '沼泽', 'OCEAN': '海洋', 'RIVER': '河流',
    'FORTIFICATION': '要塞', 'PORT': '港口', 'STREAM': '溪流',
    'ESCARPMENT': '断崖', 'IMPASSABLE RIVER': '不可通行河流', 'ROUGH': '崎岖地',
    'CUSTOM': '自定义', 'ROADS': '公路', 'RAILS': '铁路',
    # [unitdata]
    'Leader': '指挥官', 'Transport': '运输', 'Country': '国家',
    'Experience': '经验', 'Experience level': '经验等级', 'Stamina': '耐力',
    'Strength': '兵力', 'Range': '射程', 'Initiative': '主动性',
    'Spot': '侦察', 'Mov. Method': '移动方式', 'Hard Attack': '硬攻击',
    'Soft Attack': '软攻击', 'Spy Attack': '间谍攻击', 'Naval Attack': '海军攻击',
    'Ground defense': '地面防御', 'Spy defense': '间谍防御',
    'Close defense': '近战防御', 'Range defense': '远程防御',
    'Class': '类别', 'Cost': '费用',
    # 结构性占位（作者占位符，非显示文本）⇒ 保留
    '---': '---', '--': '--',
}

FILES = [('nations.txt', NAT), ('strings_efile.txt', SEF)]


def rd(p):
    raw = open(p, 'rb').read()
    return raw.decode('cp1252').replace('\r\n', '\n').split('\n')


def build(fn, table):
    src = os.path.join(SRC, fn)
    lines = rd(src)
    out, miss = [], []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith('*') or s.startswith('['):
            out.append(ln)          # 空行 / 注释 / 段头 ⇒ 原样保留
            continue
        if s in table:
            out.append(ln.replace(s, table[s]))
        else:
            out.append(ln)
            miss.append((i + 1, s))
    return out, miss


def main():
    apply = '--apply' in sys.argv
    ok = True
    plans = []
    for fn, table in FILES:
        out, miss = build(fn, table)
        plans.append((fn, out))
        print('%-20s %d 行  未命中 %d' % (fn, len(out), len(miss)))
        for ln, s in miss[:30]:
            print('    L%-4d %s' % (ln, s))
        if miss:
            ok = False
    if not ok:
        print('\n★ 存在未命中，未写盘（补进映射表后再跑）')
        return
    if not apply:
        print('\n（dry-run，未写盘）')
        return

    os.makedirs(BK, exist_ok=True)
    os.makedirs(DST, exist_ok=True)
    for fn, out in plans:
        text = '\r\n'.join(out)
        data = text.encode('gbk')
        tmp = os.path.join(DST, fn + '.new')
        open(tmp, 'wb').write(data)
        assert open(tmp, 'rb').read() == data, '回读不一致 ' + fn
        dst = os.path.join(DST, fn)
        if os.path.exists(dst) and not os.path.exists(os.path.join(BK, fn)):
            shutil.copy2(dst, os.path.join(BK, fn))
        os.replace(tmp, dst)
        print('已写出 %-20s %6d B  CRLF=%d' % (fn, len(data), data.count(b'\r\n')))


if __name__ == '__main__':
    main()
