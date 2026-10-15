# -*- coding: utf-8 -*-
"""
源数据损坏名称（单字节重音字符）的还原译名。

背景：原作者的 mapnames.str 里有 12 条名称的重音字符被压成单字节：
    é / é → \xa4  或  \xef       ñ → \xf1
    ç     → \x87                 ü → \xfc
这不是 UTF-8，也不是 GBK，是**原始录入损坏**，无法用任何编码直接解出。
必须按词形语义还原，否则该条永远不会被匹配到。

还原对照：
    Alca\xa4ices      → 阿尔卡伊塞斯      (Alcaices, 实际 Alcañices → 阿尔卡尼塞斯)
    Alca\xf1iz       → 阿尔卡尼斯        (Alcañiz, 西班牙特鲁埃尔省)
    Almu\xa4ecar     → 阿尔穆内卡尔      (Almuñécar)
    Besan\x87on      → 贝桑松            (Besançon)
    Fuentidue\xa4a   → 丰蒂杜埃尼亚      (Fuentidueña)
    Logro\xa4o       → 洛格罗尼奥        (Logroño)
    Mora d\xb4Ebre   → 埃布罗河畔莫拉    (Mora d'Ebre)
    Pe\xa4arroya     → 佩尼亚罗亚        (Peñarroya)
    Pe\xf1alver      → 佩尼亚尔韦尔      (Peñalver)
    Razdol\xefnoie   → 拉兹多利诺耶       (Razdolnoie)
    Santo\xa4a       → 桑托尼亚          (Santoña)
    Sig\xfcenza      → 锡古恩萨          (Sigüenza)

用法：patch_place_names.py 在收集名称时，对无法 UTF-8 解码的记录
按【原始字节】查本表，而不是按字符串查。
"""

# 键 = 原始字节（bytes），值 = 中文译名
MOJIBAKE = {
    b'Alca\xa4ices':    '阿尔卡尼塞斯',
    b'Alca\xf1iz':      '阿尔卡尼斯',
    b'Almu\xa4ecar':    '阿尔穆内卡尔',
    b'Besan\x87on':     '贝桑松',
    b'Fuentidue\xa4a':  '丰蒂杜埃尼亚',
    b'Logro\xa4o':      '洛格罗尼奥',
    b'Mora d\xb4Ebre':  '莫拉德埃布罗',  # 去介词改紧凑音译，19B 上限内
    b'Pe\xa4arroya':    '佩尼亚罗亚',
    b'Pe\xf1alver':     '佩尼亚尔韦尔',
    b'Razdol\xefnoie':  '拉兹多利诺耶',
    b'Santo\xa4a':      '桑托尼亚',
    b'Sig\xfcenza':     '锡古恩萨',
}
