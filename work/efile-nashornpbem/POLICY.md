# NASHORNPBEM 汉化口径

> 目标：`D:\OpenPG2\EFILE_NASHORNPBEM`（Nashorn PBEM efile v1.0a，WW2 1945 装备表，作者 Nashorn）
> 部署方式：译文放 `EFILE_NASHORNPBEM\TEXT-ZH\`（引擎官方语言覆盖目录，已由反汇编确证）
> 编码：**GBK(936)、无 BOM、CRLF**

---

## 一、装备名 `equip.txt`（最重要，520 条）

**判定顺序（从 1 到 4，命中即止）：**

### 1. 整行是「型号 + 编号」⇒ **原样保留**
```
Pz IVJ            Pz VIII Maus      Pz VA Panther     Pz IIIG
8.8 FlaK18        2 FlaK38          3.7 FlaK36        12.8 FlaK40
SdKfz 6/2 8.8 FlaK36                MG 34             MG 42
Cruiser I / II / III / IV           FlaKPz V Coelian  FlakPz IV Wirbelwind
Pz 38(t)A         Pz 735(f)         Pz 747(r)         Pz IIIM(F)
SS 7.92mm MG 34                     FlaK M31(r)
```
> 判据：整行由型号字母/数字/口径/括号国家码构成，无独立兵种名词。

### 2. 整行是「兵种 / 编制 / 后勤 词」⇒ **译中文**
```
Pioneeri→工兵          Recon→侦察            Artillery→炮兵       Engineer→工兵
Supply Base→补给基地    MG Position→机枪阵地   Artillery Bunker→炮兵掩体
Security Inf→保安步兵   Police Inf→警察步兵    Supply Depot→补给站
```

### 3. 「数字/口径 + 通用名词」⇒ **数字保留，名词译**
```
4.2inch Mortar→4.2inch 迫击击炮    81mm Mortar→81 毫米迫击炮
44 Engineer→44 工兵                  Pz IIIG Tauchfahig→Pz IIIG 潜渡型
```

### 4. 「修饰语 + 兵种」⇒ **修饰语译，型号部分保留**
```
SS Infanterie→党卫军步兵              SS Panzergrenadiere→党卫军装甲掷弹兵
SS Pioniere→党卫军工兵                SS Sturmpioniere→党卫军突击工兵
SS Gebirgsjager→党卫军山地猎兵         SS Kavallerie→党卫军骑兵
SS Grenadiere→党卫军掷弹兵             FJ Sturmpioniere→伞兵突击工兵
Para. Engineer→伞兵工兵               Mortar Para→伞兵迫击炮
USMC Engineer→美国海军陆战队工兵       Velo Recon→自行车侦察兵
AA Cruiser→防空巡洋舰                 Auxiliary Cruiser→辅助巡洋舰
MG 34 Div. Azul→MG 34 蓝色师          Artillery Bunker→炮兵掩体
Hvy. Artillery Bunker→重型炮兵碉堡
```

### 标准译名表（务必统一）
| 原文 | 中文 | 原文 | 中文 |
|---|---|---|---|
| Inf / Infanterie | 步兵 | PzGren / Panzergrenadiere | 装甲掷弹兵 |
| Grenadier(s) | 掷弹兵 | VolksGrenadier | 国民掷弹兵 |
| Pioneer / Pioniere | 工兵 | Sturmpionier | 突击工兵 |
| Gebirgsjager | 山地猎兵 | Kavallerie | 骑兵 |
| Recon | 侦察 | Artillery | 炮兵 |
| Mortar | 迫击炮 | Supply | 补给 |
| Depot | 补给站 | Bunker | 掩体 |
| Security | 保安 | Police | 警察 |
| Cossack / Kosaken | 哥萨克 | Para / FJ | 伞兵 |
| Halftruck / Halftrack | 半履带 | Cruiser | 巡洋舰 |
| Mobile | 自行 | Static | 固定 |
| HvGun | 重炮 | Wurfrahmen | 火箭发射器 |

### 保留不译
- **Pz / FlaK / Flak / MG / SdKfz / AT / AA / Hv / FJ（纯型号行内）**
- 括号国家码 `(f)` `(i)` `(r)` `(t)` `(j)` `(e)`
- 口径数字（`20mm` `88mm` `3.7`）
- `Error! VERSION ...` 首行（版本行，原样）

---

## 二、人名 `names.txt`（463 条需新译）

- 欧洲/美洲人名 → **音译中文**：`Smith`→史密斯、`Brown`→布朗、`Peterson`→彼得森
- 贵族介词保留并加间隔号：`von Hotzendorff`→冯·霍岑多夫、`van Habsburg`→范·哈布斯堡、`de Jong`→德容
- 斯拉夫/北欧人名 → 音译：`Konzev`→孔泽夫、`Albrektsson`→阿尔布雷克松
- **同一人名重复出现时译法必须完全一致**
- 无从考据的冷僻名 → 按读音音译，不臆造汉字名

---

## 三、国名 / 阵营 `nations.txt`（31 条）

```
Axis→阵营一        Allied→阵营二        （沿用 OLGWW2 既定口径）
Germans→德国       Yanks→美国           British→英国
Slovakians→斯洛伐克  Belgians→比利时      Bulgarians→保加利亚
Czechs→捷克斯洛伐克  Danish→丹麦          Finnish→芬兰
French→法国        Greeks→希腊          Hungarians→匈牙利
All Countries→所有国家
```
> 形容词/复数形式（-ians / -s / -ese）→ 一律译为**国名本身**。

---

## 四、界面段 `strings_efile.txt`

### `[targets]`
`Soft target`→软目标　`Hard target`→硬目标　`Air target`→空中目标　`Special target`→特殊目标

### `[terrain]`（**顺序不可变**，逐项对应地形 ID）
| # | 原文 | 中文 | # | 原文 | 中文 |
|---|---|---|---|---|---|
| 0 | CLEAR | 开阔地 | 10 | RIVER | 河流 |
| 1 | CITY | 城市 | 11 | FORTIFICATION | 要塞 |
| 2 | AIRFIELD | 机场 | 12 | PORT | 港口 |
| 3 | WOODED | 森林 | 13 | STREAM | 溪流 |
| 4 | BOCCAGE | 树篱地 | 14 | ESCARPMENT | 断崖 |
| 5 | HILL | 丘陵 | 15 | IMPASSABLE ROCKS | 不可通行岩地 |
| 6 | HEAVY | 山地 | 16 | ROUGH | 崎岖地 |
| 7 | SAND | 沙漠 | 17 | SHALLOW WATER | 浅水 |
| 8 | MARSH | 沼泽 | 18 | ROADS | 公路 |
| 9 | DEEP WATER | 深海 | 19 | RAILS | 铁路 |

### `[unitdata]`
```
Leader→领袖        Transport→运输      Country→国家        Experience→经验
Experience level→经验等级              Fuel→燃料           Ammo→弹药
Strength→兵力      Range→射程          Initiative→主动权   Spot→侦察
Mov.Method→移动方式  Hard Attack→硬目标攻击  Soft Attack→软目标攻击
Air Attack→空中攻击  Special Attack→特殊攻击  Ground defense→地面防御
Air defense→对空防御  Close defense→近距防御
Range defense modifier→射程防御修正     Class→类别          Cost→造价
```

---

## 五、不做 / 不改
| 文件 | 原因 |
|---|---|
| `TerrainEx.txt` | 纯数据表（`0=clear, 0, 99`，`clear` 是内部键） |
| `weather.txt` | 纯数据表（月份×4 参数） |
| `efile.xml` | efile 描述，引擎不读 `TEXT-XX`（已知盲区） |
| `SCENARIO\utopianparadox.cfg` | OpenSuite 生成的配置 |
| `OPENDAT\*.png` | 纯图形（旗帜/勋章/肖像），无烘焙文字 |
