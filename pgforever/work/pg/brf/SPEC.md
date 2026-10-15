# PG Forever 战役简报翻译规范（所有译者必读，口径必须一致）

## 任务
把 `batchN.json` 里每条 `en`（一个战役简报的 HTML 片段）译成简体中文，输出到 `batchN.zh.json`。

## 输入 / 输出格式
输入：`[{ "file": "0001.pgbrf", "scn": "波兰", "en": "<p>…</p>" }, …]`
输出：`[{ "file": "0001.pgbrf", "zh": "<p>…</p>" }, …]`（**file 必须原样保留、顺序一致、条数一致**）

## 绝对规则
1. **保留 HTML 结构**：`<p>` `</p>` `<br/>` `<b>` 等标签原样保留，只译标签之间的文字。
2. **保留所有数字与单位**：年份、日期、回合数、番号、口径（88mm）一律保留数字本身。
3. **日期格式统一为无空格中文**：`September 10, 1939` → `1939年9月10日`；`October 9, 1943` → `1943年10月9日`。
   `Nov 8, 1942` → `1942年11月8日`（英文缩写月份要还原成中文月份）。
4. **长度控制（重要）**：中文译文的**字符数不得超过原文的 70%**（引擎对长文本可能截断）。
   中文通常比英文短得多，一般自然达标；若某条过长，适当精简，不要删信息。
5. **立场原则**（淮海/徐蚌 同理）：按**扮演方视角**用词。
   - 德军视角的简报用德军自己的作战代号与编制名；提到敌方行动时用盟军代号。
   - 盟军视角的简报用盟军代号。
6. **禁用蔑称与旧称**：不得出现"支那""匪""鬼子""伪军"等。苏联称"苏军/苏联"，不称"俄国人"（除非原文明确指国家/地理）。
7. **不要翻译**：装备型号、军舰舰名与舰级、人名（除非有公认中文译名）。

## 术语表（必须遵守）

### 作战代号
| 英文 | 中文 | 阵营 |
|---|---|---|
| Fall Weiss | 白色方案行动 | 德 |
| Weserübung | 威悉演习行动 | 德 |
| Operation Sea Lion / Sealion | 海狮行动 | 德 |
| Barbarossa | 巴巴罗萨行动 | 德 |
| Unternehmen Zitadelle / Operation Citadel | 堡垒行动 | 德 |
| Wacht am Rhein | 莱茵守望行动 | 德 |
| Operation Overlord | 「霸王」行动 | 盟 |
| Operation Cobra | 「眼镜蛇」行动 | 盟 |
| Operation Torch | 「火炬」行动 | 盟 |
| Operation Husky | 「哈士奇」行动 | 盟 |
| Operation Anvil | 「铁砧」行动 | 盟 |
| Operation Market Garden | 「市场花园」行动 | 盟 |

### 地名（通行译名）
Poland 波兰｜Warsaw 华沙｜Lodz 罗兹｜Kutno 库特诺｜Norway 挪威｜Denmark 丹麦｜
Low Countries 低地国家｜Belgium 比利时｜Netherlands 荷兰｜Luxembourg 卢森堡｜
France 法国｜Paris 巴黎｜Dunkirk 敦刻尔克｜Maginot Line 马奇诺防线｜
England 英国｜London 伦敦｜Gibraltar 直布罗陀｜Egypt 埃及｜Suez 苏伊士｜
North Africa 北非｜Libya 利比亚｜Tobruk 托布鲁克｜Tripoli 的黎波里｜Benghazi 班加西｜
El Alamein 阿拉曼｜Persia 波斯｜Caucasus 高加索｜Baku 巴库｜Stalingrad 斯大林格勒｜
Kursk 库尔斯克｜Kharkov 哈尔科夫｜Kiev 基辅｜Moscow 莫斯科｜Leningrad 列宁格勒｜
Sevastopol 塞瓦斯托波尔｜Crimea 克里米亚｜Byelorussia 白俄罗斯｜Minsk 明斯克｜
Smolensk 斯摩棱斯克｜Budapest 布达佩斯｜Vienna 维也纳｜Berlin 柏林｜
Normandy 诺曼底｜Anzio 安齐奥｜Sicily 西西里｜Naples 那不勒斯｜Rome 罗马｜
Yugoslavia 南斯拉夫｜Greece 希腊｜Crete 克里特｜Balkans 巴尔干｜
Washington 华盛顿｜Rhine 莱茵河｜Gustav Line 古斯塔夫防线

### 军语与编制
Wehrmacht 国防军｜Luftwaffe 德国空军｜Afrika Korps 非洲军团｜Panzer 装甲（Panzers 装甲部队）｜
Panzergruppe 装甲集群｜Army Group Center 中央集团军群｜Army Group South 南方集团军群｜
blitzkrieg 闪电战｜beachhead 滩头阵地｜bridgehead 桥头堡｜pocket 包围圈（动词：合围）｜
encirclement 合围｜breakthrough 突破｜offensive 攻势｜counteroffensive 反攻｜
reinforcements 增援部队｜supply lines 补给线｜flanking 侧翼包抄｜
paratroopers 伞兵｜airborne 空降｜amphibious 两栖｜convoy 运输船队｜
prestige 声望｜core units 核心部队｜auxiliary 辅助部队｜turns 回合｜
victory hex 胜利格（VH）｜resistance 抵抗｜surrender 投降｜

### 军衔与人名（有通行中文译名时用中文，否则保留原文）
Rommel 隆美尔｜Guderian 古德里安｜Montgomery 蒙哥马利｜Chuikov 崔可夫｜Zhukov 朱可夫｜
Eisenhower 艾森豪威尔｜Patton 巴顿｜Manstein 曼施坦因｜Kleist 克莱斯特｜
学生（Student）、保卢斯（Paulus）等按通行译名。

## 语气
军事简报口吻：简洁、命令式、有紧迫感。避免翻译腔（不要"我们的部队的推进"这类）。
第二人称对玩家直接称呼（"你"／"你的部队"）。

## 完成标准
- 条数与 `en` 完全对应，`file` 一字不差
- 每条中文 ≤ 原文 70% 字符数
- `<p></p>` 标签保留
- 无残留英文句子（装备型号/舰名/人名除外）
- 无禁用词
