# OLGWW2 待考地名核对报告

> 日期：2026-09-24 ｜ 对象：`D:\OpenPG2\EFILE_OLGWW2\SCENARIO\*.xscn` 组0（地名）
> 起因：`docs\15` 留下「52 条拼写混乱的待考地名」，标注为「需核对原始战役地图拼写后再译」

---

## 一、结论

**45 条待考地名全部核定，并已写入 31 个场景文件。**

| 指标 | 前 | 后 |
|---|---|---|
| 组0 纯 ASCII 条目 | 55 | **5**（全是地图编号 362A/B/C、382、DG4，权威清单本即原样保留） |
| OLGWW2 含汉字条目 | 13,856 | **13,910（+54）** |
| 硬漏译候选 | 106 | **61**（54 舰名政策保留 + 7 条番号） |
| 重建复核 | — | **119 / 119 逐字节一致** |

> **+54 恰等于实际改动处数（45 条唯一原文，因重复共 54 处写入）⇒ 零副作用。**

---

## 二、方法（关键：找到权威对照源）

三个阶段，前两个都不够可靠，第三个才定案：

### ① 语境卡（判定地区）
`pending_context.py` 导出每个待考条目所在场景的标题与同组邻居，据此确定地区：
`MAO*`＝朝鲜战争/中国内战、`RSCHI*`＝华南与香港、`RSSOV*`＝满苏边境与南萨哈林、
`jh3*`＝希腊战役/诺夫哥罗德/色当、`n42s*`＝西西里/科林斯/阿尔萨斯/波兰。

### ② `.txt` 清单序列对齐（❌ 不可靠，已弃用）
`SCENARIO\<name>.txt` 是场景名称清单，与 `.xscn` 组0 部分同序。**但各场景情况不一**：
`MAO14_2` 对齐率 73%、`MAO11` 78%，而 `18days3` 仅 15%、`RSCHI07` 8%（顺序完全不同）。
`match_txt_names.py` 因此加了**质量门限**（<70% 的场景结论不采用）。
> 副产品：`strings-hu.txt` 式的"行号错位"教训 —— 跨文件按行号对照必须先验证对齐率。

### ③ ★ 原始英文清单 ↔ 中文清单 逐行对照（✅ 定案）
```
原文: backup/ORIGINAL-EFILE_OLGWW2/SCENARIO/<name>.txt   (cp1252)
中文: D:\OpenPG2\EFILE_OLGWW2\SCENARIO\<name>.txt          (gbk，已汉化覆盖)
```
两者是**同一份名单的两个语言版本**，行行对应（实测 164:164、174:174、171:171…），
直接建 `en → zh` 字典查表，**无任何对齐风险**。工具 `lookup_via_txt.py`。

---

## 三、45 条权威定名

### 朝鲜战争（MAO 系列）
| 原文 | 译名 | 场景 |
|---|---|---|
| Chongpyong | 定平 | MAO11、MAO13 |
| Hudong-ni | 厚洞里 | MAO12 长津湖 |
| Tongjoson mam | 东朝鲜湾 | MAO13 |
| Chon-ni | 村里 | MAO13_2 |
| Tondugch'on | 敦德川 | MAO14 |
| Chanji | 昌芝 | MAO14_2 |
| Samnagjnin | 三浪津 | MAO14_2 |
| Chingyong | 镇永 | MAO14_2 |
| Changan | 长安 | MAO14_2 |

> `Chongpyong`＝定平（咸镜南道，位于洪原—咸兴之间）与地名序列完全吻合；
> `Samnagjnin` 实为 `Samnangjin`（三浪津，密阳附近）的 n/r 转写讹误。

### 中国内地
| 原文 | 译名 | 场景 |
|---|---|---|
| Qingguang | 青光 | MAO17 天津 |
| Bayiashan | 八甲山 | MAO2 湖南 |
| Badu | 八都 | MAO3 江西 |
| Mao-Tsu-Fan | 毛嘴畈 | MAO6 湖北 |
| Qingyu | 清原 | MAO7/MAO8 东北 |
| VOLCANO LAKE | 火山湖 | MAO7/MAO8（长白山天池）|

### 华南 / 香港
| 原文 | 译名 | 说明 |
|---|---|---|
| Chang Cheng | 长城 | RSCHI02 海南 |
| Basou | 八所 | RSCHI02（东方市八所）|
| Jlesni | 甲子 | RSCHI05（陆丰甲子）|
| Hotel Eucliffe | 欧克立夫酒店 | RSCHI05 香港 |
| Ching Li ou | 清利口 | RSCHI07 常德 |
| Chiang Ching | 荆江 | RSCHI07 |

### 蒙古 / 日本 / 苏联
| 原文 | 译名 | 说明 |
|---|---|---|
| Chang-Chung-Miao | 张忠庙 | RSGOL 诺门罕 |
| Aohima | 青滨 | RSJAP03 埼玉 |
| Amatsu | 天津 | RSJAP03（千叶县天津町）|
| Chokchidon | 乔克奇东 | RSSOV01 张鼓峰 |
| Homuku | 霍穆库 | RSSOV01 |
| Chynsandon | 钦桑东 | RSSOV01 |
| Ruydun-Gova-khe River | 鲁伊敦-戈瓦赫河 | RSSOV03 |
| Tumuhop | 图穆霍普 | RSSOV05 满苏边境 |
| Chihsi | 奇西 | RSSOV05 |
| Sangchihtung | 三池洞 | RSSOV05 |
| Chingkulingmiao | 清河岭庙 | RSSOV05 |
| Lishan | 梨山 | RSSOV05 |
| Chiwagai | 千轮街 | RSSOV06 南萨哈林 |
| Hatsutai | 初代 | RSSOV06 |
| Chio | 千绪 | RSSOV06 |

### 欧洲
| 原文 | 译名 | 说明 |
|---|---|---|
| Harzy | 阿尔济 | 18days3 阿登 |
| HEES | 海斯 | 18days2、CanalAlbert |
| Vzvatl | 弗兹瓦德 | jh3nov43 / jh3novg（俄 Vzvad，伊尔门湖）|
| Belebzika | 别列布济卡 | jh3novg |
| Renvez | 朗韦 | jh3seda 色当（法 Renwez）|
| Rehrbaon | 雷尔邦 | n42s12a 北风行动 |
| Sarreinsberg | 萨兰斯贝格 | n42s12a |

### 其他
| 原文 | 译名 | 说明 |
|---|---|---|
| VOLCANIC SOIL | 火山土 | RSJAP01 地形 |
| `[DAF]` | `[沙漠航空队]` | SP3 / DAK2；**由 KEEP 改为实译**（同 `[JAAF]`→`[日本陆军航空队]` 口径）|

---

## 四、顺带发现（待用户定夺）

### ⚠️ `.xscn` 既有译名与场景清单 `.txt` 不一致
在对齐可信的场景内检出若干处（`.xscn` ≠ `.txt`），例如：

| 文件 | 索引 | `.xscn` 现译 | `.txt` 清单译名 |
|---|---|---|---|
| MAO14_2 | i2 | 蔚松 | **蔚城** |
| MAO14_2 | i20 | 南仓 | **南昌** |
| MAO14_2 | i21 | 穆南 | **武安** |
| MAO14_2 | i26 | 基姜 | **机张** |
| MAO11 | i2 | 大青 | **泰川** |
| MAO11 | i3 | 惠冲 | **熙川** |

- `.txt` 侧明显是韩国/朝鲜**标准译名**（盈德、金泉、机张均为真实地名），
  说明 `.xscn` 侧（部分来自 PGForever 复用表）存在**早期误译**。
- **本次未动**（超出"核待考地名"范围，且波及面较大）⇒ 建议列为下一批统一订正任务。
- 完整比对见 `work\efile-nashornpbem\out\place-txt-match.txt` 的 B 节
  （含**质量门限**：仅列对齐率 ≥70% 的场景）。

### 📌 `olgww2-pending.tsv` 是过期快照
其中 12 条（jh3ther 7、n42s04 1、n42s07 2、n42s14 2）**早已译成中文**，
却仍被登记为待考，导致待考量虚高（57 实际剩 45）。
**⇒ 纪律重申：判进度必须直接读文件，登记表会滞后。**

---

## 五、产出与回滚

| 类别 | 路径 |
|---|---|
| 备份 | `backup\olgww2-place-before\`（**31 个**，md5 抽样校验通过）|
| 译名真源 | `work\efile-nashornpbem\olgww2-glossary.tsv`（+45 条，并清理 60 条空占位行）|
| 工具 | `lookup_via_txt.py`（权威查表）·`list_place_ascii.py`（残留地面审计）·`pending_context.py`（语境卡）·`match_txt_names.py`（序列对齐+质量门限）|
| 输出 | `out\place-authoritative.txt`（45 条命中）·`out\place-ascii-after.txt`（残留 5 条）·`out\place-txt-match.txt`（对齐质量+B节）|
| 回滚 | 从 `backup\olgww2-place-before\` 覆盖回 `EFILE_OLGWW2\SCENARIO\` 即可 |

### 写入纪律执行记录
1. 备份与覆盖**分两条独立命令**；dry-run 先跑（54 处 / 31 文件）再 `--apply`；
2. 写入器为**字节级定点替换**（只改 2 字节长度字段 + 内容，其余字节不动，天然可重入）；
3. 复核用**重建比对**（备份 + 译名表重新序列化，要求与现文件逐字节相同）⇒ **119/119 一致**。
