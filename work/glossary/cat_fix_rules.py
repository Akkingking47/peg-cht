# -*- coding: utf-8 -*-
"""cat_fix_rules —— 词库 `cat` 误标纠正规则（`build_glossary.py` 与提案脚本共用）。

起因（用户裁定 m01713-①：需要治理）：
`build_glossary.py:83` 的 `cat_of_name()` **只看英文侧**、且默认落 `PLACE`，于是
  · 法语/意语番号 `1er Bon Sapeurs` / `110e RI` / `11e Cuirassiers`（序数不是 `1st`）
  · 小写缩写 `HG div`（正则要求 `Div` 大写）
  · 舰名 `Maxim Gorky II`、将军司令部 `Gen.Kdo. Gen. Hermann Geyer`
  · 中文侧明明是「营/团/师」的条目
全部被标成 `PLACE`。实测三层表 **752 条 / 7120 个 PLACE（10.6%）**。

⭐ 用户 m01642 的提醒是本模块的硬约束：**人名来源的地名仍然是地名**
（列宁格勒/斯大林格勒/基洛沃格勒/加里宁格勒…），一律豁免；同理豁免以部队后缀
结尾的**真实城市**（大连/东营/师宗/团风…）。

设计约束：`merge()` 按 `(en, scope)` 归并、**cat 不参与分组** ⇒ 本规则**只改 cat 列**，
en/zh/status/conf/zh_in 逐字节不变（重建后用 diff 证明）。
"""
import re

# 中文侧部队后缀（比英文侧可靠：中文化一定会写出「团/营/师」）
UNIT_TAIL_ZH = re.compile(
    r"(炮兵团|装甲掷弹兵团|掷弹兵团|步兵团|骑兵团|坦克团|炮兵团|工兵团|伞兵团|"
    r"团|旅|师|军|营|连|排|大队|中队|小队|联队|旅团|师团|支队|纵队|区队|兵团|"
    r"集团军|方面军|军团|司令部|警备队|卫队|舰队|航空队|分舰队|守备|卫戍|要塞|兵站|"
    r"摩托化|装甲|步兵|骑兵|炮兵|工兵|伞兵|近卫|党卫军)$")

# ⛔ 真实地名豁免：以部队后缀收尾的地名（用户 m01642 的陷阱）
CITY_GUARD = frozenset({
    "大连", "东营", "西营", "中营", "老营", "师宗", "团风", "军屯", "旅顺口",
    "营口", "连城", "连山", "军山", "团堡", "师寨",
})

# ⛔ 人名来源的地名豁免（仍是地名）
PERSON_PLACE = re.compile(
    r"(列宁|斯大林|基洛夫|伏罗希洛夫|加里宁|古比雪夫|莫洛托夫|高尔基|伏龙芝|"
    r"捷尔任斯基|日丹诺夫|恩格斯|布琼尼|伏罗希洛夫)(格勒|斯克|诺夫卡|诺|卡|市|州|区|堡|城|号)")

# 英文侧的编制缩写（大小写不敏感，补 `Div`/`Bn` 之类的漏网）
ABBR_EN = re.compile(
    r"(?i)(?:^|[^a-z])(rgt|regt|reg|bde|brig|div|bn|btn|bat|bon|gp|abt|bty|kdo|hq|"
    r"sqn|esc|coy|ca|ak|aok|korps|armee|army|corps|division|brigade|battalion|"
    r"regiment|flotilla|squadron|pz|pzgren|pzgr|stug|aufk|nachr)(?:[^a-z]|$)")

BRANCH_ZH = re.compile(r"(党卫军|近卫|掷弹兵|摩托化|装甲|步兵|骑兵|炮兵|工兵|伞兵|海军|"
                       r"山地|滑雪|轻装|重装|突击|要塞|守备|卫戍|警备)")
DIGIT = re.compile(r"\d")

# 舰名：`…号` 收尾且不含数字（`马克西姆·高尔基一号`/`努比亚号`），或英文带海军前缀
# ⚠️ 前缀必须**大写且后接大写开头舰名**——早期写成不区分大小写的 `orp?`，
#    会匹配散文里的裸词 `or`（实测误伤 `Efile: OLGWW2 … or higher` 两条）。
NAVAL_EN = re.compile(r"(?:^|[\s(（])(HMS|USS|IJN|KM|HMNZS|HMCS|HMAS|HMNoS|ORP|ARA|NRP|"
                      r"RMS|MN|RN|SM)\s+[A-Z(\"“]")
SHIP_TAIL_ZH = re.compile(r"号$")

# 源文件里成对包裹的引号/括号（`''Macau''` / `"Dora"` / `（-）营`）——判类前先剥掉
WRAP = re.compile(r'^[\s"\'“”‘’（）()\[\]【】]+|[\s"\'“”‘’（）()\[\]【】]+$')

# 少数无任何文本线索的**具名装备**（铁道炮/臼炮/巡洋舰），人工登记
NAMED_EQUIP = frozenset({
    "dora", "karl", "thor", "odin", "ziu", "loki",
    "maxim gorky i", "maxim gorky ii",
})

# 少数无任何文本线索的**部队条目**（母语原名，中文侧译名也没有「团/营/师」后缀），人工登记。
# ⚠️ 案例：`Tabor Mehal-la` → `梅哈利拉塔博尔`（摩洛哥塔博尔部队）。
#    它在第一轮定名里由 `塔博尔 梅哈利拉` 改成 `梅哈利拉塔博尔`，末字不再是部队词，
#    于是 cat 从 UNIT 掉回 PLACE（实测：重建后 UNIT-1/PLACE+1）⇒ 登记在此钉住。
UNIT_EN_EXACT = {
    "tabor mehal-la": "摩洛哥塔博尔部队（母语原名，无部队后缀）",
    "tabor ifni": "摩洛哥塔博尔部队（母语原名，无部队后缀）",
}


def unwrap(s):
    prev = None
    t = (s or "").strip()
    while t != prev:
        prev = t
        t = WRAP.sub("", t).strip()
    return t


def recat(en, zh):
    """给出建议 cat；返回 (新类别, 理由) 或 None（保持 PLACE）。"""
    e = unwrap(en)
    z = unwrap(zh)
    if not z or z in CITY_GUARD or PERSON_PLACE.search(z):
        return None
    if e.lower() in NAMED_EQUIP:
        return ("EQUIP", "具名装备（人工登记）")
    if e.lower() in UNIT_EN_EXACT:
        return ("UNIT", UNIT_EN_EXACT[e.lower()])
    # 舰名/装备：中文以「号」收尾（非「第N号」）或英文带海军前缀
    if SHIP_TAIL_ZH.search(z) and not DIGIT.search(z) and len(z) >= 3:
        return ("EQUIP", "中文以「号」收尾（舰名/装备）")
    if NAVAL_EN.search(e):
        return ("EQUIP", "英文海军前缀")
    m = UNIT_TAIL_ZH.search(z)
    if not m:
        return None
    corrob = []
    if DIGIT.search(z):
        corrob.append("中文含数字")
    if DIGIT.search(e):
        corrob.append("英文含数字")
    if ABBR_EN.search(e):
        corrob.append("英文编制缩写")
    if BRANCH_ZH.search(z):
        corrob.append("兵种词")
    if "司令部" in z or "集团军" in z or "方面军" in z or "卫队" in z or "警备队" in z:
        corrob.append("编制词")
    if not corrob:
        return None
    return ("UNIT", "中文后缀「%s」+%s" % (m.group(1), "、".join(corrob)))
