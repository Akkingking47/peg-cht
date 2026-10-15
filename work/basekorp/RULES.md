# BASEKORP `.xscn` 番号串汉化口径（子代理必读）

游戏：Open General / OpenPG（二战及古代题材回合制兵棋）。
本批是 `EFILE_BASEKORP\SCENARIO\*.xscn` 里的**单位标签串**（Order of Battle 条目、地名、设施名）。
这些串会在游戏地图上直接显示，**必须短、准、可读**，不要写成长句。

## 一、输入格式

`_llm-src.tsv` 四列：`src`（英文原文） / `draft`（确定性引擎已出的草稿） / `freq`（出现次数） / `resid`（草稿里仍未译的成分）。

- **草稿里已经译好的中文，一律沿用，不要另起译法**（保证与另外 6 个已交付 efile 一致）。
- 你只需要**补齐 / 修正 `resid` 里的残留成分**，并把整条串整理通顺。
- 如果草稿明显译错（例如把地名当编制），直接改正。

## 二、番号串结构（关键）

串用 `/` 分段，**顺序是「本单位 / 上级 / 再上级」**：

```
II/382/-/164Le KG Ziegler [DAK]
│   │   │  └── 师/旅级（战斗群）
│   │   └───── 空缺（用 - 表示）
│   └───────── 团级
└───────────── 营级（罗马数字）
```

规则：
1. **罗马数字 → 阿拉伯数字 + 「第」**：`II`→`第2`、`XXXIII`→第33、`XLIV`→第44。
2. **纯数字段 → 「第N」**：`382`→`第382`；`-` 原样保留。
3. **「数字+编制缩写」→ 「第N<中文编制>」**：
   `236D`→`第236师`、`99RD`→`第99步兵师`、`82ABD`→`第82空降师`、`13GRD`→`第13近卫步兵师`、`60ID`→`第60步兵师`。
4. **序数**：`236th Rifle`→`第236步兵`、`42nd`→`第42`、`3rd`→`第3`。
5. **方括号 `[...]`**：
   - 纯番号（罗马或阿拉伯）**原样保留**：`[XIII]` `[20]` `[51A]` `[-]`
   - 部队/军团代号**译中文**：`[DAK]`→`[非洲军]`、`[CTV]`→`[志愿军团]`、`[WDF]`→`[西部沙漠部队]`、`[IICdn]`→`[加拿大第2军]`、`[Cyrcom]`→`[昔兰尼加司令部]`、`[XVIIIAbn]`→`[第18空降军]`
6. **圆括号 `(...)`**：同段内规则；`(att)`→`(配属)`、`(mot)`→`(摩托化)`、`(L)`/`(H)` 等单字母标记**原样保留**。
7. **引号昵称 `'Xxx`**：部队绰号，**音译**即可，或保留原文（如 `'Pupp`、`'Ilse`）。`Rubik's Armor Gp` 这类把绰号放前面的，译作「鲁比克的装甲群」。
8. **链式组合**：`163/64R/44/13A` → `第163/第64团/第44/第13集团军`。

## 三、编制缩写对照（**强制使用，不得自创**）

| 缩写 | 中文 | 缩写 | 中文 | 缩写 | 中文 |
|---|---|---|---|---|---|
| D / Div / Div. / dv | 师 | RD | 步兵师 | GRD | 近卫步兵师 |
| ID | 步兵师 | MRD | 摩托化步兵师 | MD | 摩托化师 |
| TD | 坦克师 | TC | 坦克军 | TB / TBr | 坦克旅 |
| CD | 骑兵师 | AD | 装甲师 | ABD | 空降师 |
| PD | 伞兵师 | LD | 轻装师 | VGD | 国民掷弹兵师 |
| GD | 近卫师 | Gds / Gd / Gv | 近卫 | G | 近卫 |
| GA | 近卫集团军 | GTA | 近卫坦克集团军 | GT | 近卫坦克 |
| A / Arm / Army / Armee | 集团军 | CA / AK / K / Korps | 军 | F | 方面军 |
| Bde / Br / Brigade | 旅 | B / Bn / Btl / Btn / Bat | 营 | C | 连 |
| R / RR / IR / RI / Rgt | 团 | Gp / Group | 群 | KG | 战斗群 |
| Pz / PZ | 装甲 | PzD / PzDiv | 装甲师 | PzA | 装甲集团军 |
| PzGren / PzGrenDiv | 装甲掷弹兵(师) | Panzer-Division | 装甲师 | Infanterie-Division | 步兵师 |
| Inf / Inf. / Infantry / Rifle / Rif | 步兵 | Cav / Kav / RC | 骑兵 | Tk / Tank | 坦克 |
| Mech / Mot / mot | 机械化 / 摩托化 | Art / Aty / AR / RA | 炮兵（皇家炮兵） | AT / ATk | 反坦克 |
| FlaK / Flak / AA / aa | 高射炮 / 防空 | mor / m | 迫击炮 | mg / MG | 机枪 |
| batt | 炮兵连 | Sqn / Sqdr / Sq | 中队 | Wing | 大队 |
| JG | 战斗机联队 | ZG | 驱逐机联队 | StG | 俯冲轰炸机联队 |
| IAP | 歼击航空团 | IAD | 歼击航空师 | BAD | 轰炸航空师 |
| ShAD | 强击航空师 | VA | 航空集团军 | AF / LW | 空军 |
| RAF | 皇家空军 | USAAF | 美国陆军航空队 | SAF / SAAF | 南非空军 |
| VVS | 苏联空军 | WDAF / WDF | 西部沙漠空军（部队） | BEF | 英国远征军 |
| HMS | 英国皇家海军 | USS | 美国海军 | KM | 海军 |
| USMC / Marine | 海军陆战队 | NKVD | 内务人民委员部 | SS | 党卫军 |
| HQ | 司令部 | Front | 方面军 | Garrison | 卫戍部队 |
| Aus | 澳大利亚 | NZ / NZEF | 新西兰（远征军） | Ind / Indian | 印度 |
| Cdn | 加拿大 | Polish | 波兰 | MVSN | 黑衫军 |
| Bunker | 地堡 | Fort | 堡垒 | Tower | 塔楼 |
| Line | 防线 | position | 阵地 | River | 河（…河） |
| Sea / See | 海 / 湖 | Gulf | 湾 | Hill | 高地 |
| Airfield / Airstrip | 机场 | Port | 港口 | Station | 车站 |
| Redoubt | 棱堡 | Trench | 战壕 | Ditch | 壕沟 |
| Str | 步兵 | att | 配属 | Rem | 补充兵 |
| supt / Supply | 补给 | support | 支援 | Production | 生产 |
| posting | 驻防 | Recce | 侦察 | Coastal | 海岸 |
| Border | 边境 | Defence / Defences | 防御 | Shock | 突击 |
| Guards | 近卫 | Hvy / Heavy | 重型 | Lt / Le / Light | 轻型 |
| Mtn / Mountain / Gebirgs | 山地 | Abn / Airborne | 空降 | Fallschirm / FschJgr | 空降兵 |

单字母标记吃不准时（`H` `T` `E` `L` `U` `S`）**原样保留**，不要硬译。

## 四、地名 / 专名

- **二战欧洲地名用通行中译名**：`Leningrad`→列宁格勒、`Stalingrad`→斯大林格勒、`Moscow`/`Moskva`→莫斯科、`Volga`→伏尔加河、`Volkhov`→沃尔霍夫、`Orel`→奥廖尔、`Warta`→瓦尔塔河、`Mlawa`→姆瓦瓦、`Pillau`→皮劳、`Vervins`→韦尔万、`Lodz`→罗兹。
- **苏联/东欧小地名**：按俄语/波兰语/塞尔维亚语**音译**（`Kalanin`→卡列宁、`Michajlovskoje`→米哈伊洛夫斯科耶、`Sremska`→斯雷姆斯卡、`Dunavska`→多瑙河、`Banatiski`→巴纳特）。
- **军舰舰名/舰级保留原文**：`HMS Hermes`→`英国皇家海军 赫尔墨斯`；`USS Iowa`→`美国海军 衣阿华`。
- **人名**：知名将领用通行译名，其余音译（`Kempf`→肯普夫、`Weber`→韦伯）。

## 五、硬纪律

1. **装备型号保留原文**（M4A1、Bf-109G2、Pz IVH）。
2. **大写机制缩写保留**：`AT` `FlaK` `ZOC` `LOS` `VH` `pp`。（但编制缩写按上表译）
3. **不要加解释、不要加空格排版、不要加标点**。输出就是游戏里显示的标签。
4. **一条原文 = 一条译文**，不得合并或拆分行；行数必须与输入一致。
5. 输出 **UTF-8、无 BOM、CRLF**，`src<TAB>dst` 两列，一行一条。

## 六、示例

| src | draft | 你应输出 |
|---|---|---|
| `SAF Fgt Gp 20` | `南非空军 战斗机 群 第20` | `南非空军战斗机群 第20` |
| `1/504/82ABD` | `第1/第504空降师`… | `第1/第504/第82空降师` |
| `Warta Line` | `Warta 防线` | `瓦尔塔河防线` |
| `1 Ukr F` | `第1 Ukr 方面军` | `第1乌克兰方面军` |
| `9th Infantry 'Pleven' Div.` | `第9步兵 'Pleven' 师` | `第9步兵师“普列文”` |
| `Maginot SF Altkirch [XLIV]` | 原样 | `马奇诺要塞区 阿尔特基什 [XLIV]` |
| `II/382/-/164Le KG Ziegler [DAK]` | — | `第2/第382/-/第164Le 齐格勒战斗群 [非洲军]` |
| `Kalanin dv 64` | — | `卡列宁 第64师` |
| `Tank Gp 21` | `坦克 群 第21` | `坦克群 第21` |
| `236th Rifle Division` | — | `第236步兵师` |
| `HMS Havock` | — | `英国皇家海军 哈沃克` |
| `Guard Tower` | — | `警戒塔` |
