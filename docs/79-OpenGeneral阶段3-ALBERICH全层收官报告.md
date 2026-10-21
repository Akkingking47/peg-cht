# 79 · OpenGeneral 汉化阶段 3：EFILE_ALBERICH 全层收官执行报告

> 阶段依据：`docs\73-OpenGeneral汉化阶段计划.md` §三 · 阶段 3（`133-141`）
> 前置：阶段 1（根级，`docs\77`）· 阶段 2（`EFILE_GUS_Zx`，`docs\78`，G2 已由用户实机通过）
> 完成日期：TASK AS OF THIS BLOCK
> 工作区：`D:\DSH\军事游戏汉化\work\alberich\`

---

## 一、结论速览

| 项 | 计划量 | 实测 | 状态 |
|---|---|---|---|
| 根级 `TEXT-ZH\` 5 件 | `equip` 9,436 行 / `names` 2,976 行 | 5 件行数**逐行对齐**、GBK 无 BOM | ✅ 阶段 1 已交付，本次复核通过 |
| `.xscn` | 8 个 / 320 唯一串 | 8 个 / **324 条** / 322 含汉字 / 2 条按口径保留原文 | ✅ 字节级回写完成 |
| `SCENARIO\*.txt` | 9 个 / 10,499 字符 | 9 个，**真波兰语散文**，从 cp1250 原译 | ✅ 落 `TEXT-ZH\SCENARIO\` |
| `SCENARIO\*.tmsg` | 计划未列（阶段 2 该目录为空遂未暴露） | **3 个 / 1,566 B 波兰语**，本次一并汉化 | ✅ |
| `.ply` | 0 | 0（确认该 efile 无 `.ply`） | ✅ |
| `.front` | 计划未列 | 0 | ✅ |
| 校验三项 | 全过 | 全过（异常 0） | ✅ |

**未动任何原文**：`EFILE_ALBERICH\SCENARIO\` 下 8 个 `.xscn` 是唯一被字节级改写的对象（本阶段工作的固有要求，已独立命令备份）；12 个 `.txt`/`.tmsg` 改写的是 `TEXT-ZH\SCENARIO\` 覆盖层，**原文 20 个文件 MD5 逐一比对无一变动**。

---

## 二、勘察结论

### 2.1 `EFILE_ALBERICH` 目录全貌

```
EFILE_ALBERICH\            17 个根文件
├─ MAP\                    0 个（空目录）
├─ OPENDAT\               10 个（dossier/inspect/flag/roundel/start_open 等位图）
├─ OPENGUI\               14 个 .png（全为位图，无文字型需处理）
├─ OPENLOG\               43 个（引擎日志 + AAR/ASR 存档，非游戏画面文本）
├─ SAVE\                  17 个 .xcsv（存档）
├─ SCENARIO\              31 个（见 2.2）
├─ TEXT-PL\                2 个（NATIONS.TXT / STRINGS_EFILE.TXT）
├─ TEXT-ZH\                5 个（阶段 1 交付）
└─ TEXT-ZH\SCENARIO\      12 个（本次交付）
```

根文件中的**玩家可见文本载体**与阶段 1 口径一致：`EQUIP.TXT` / `NAMES.TXT` / `NamesEx.txt` / `NATIONS.TXT` / `STRINGS_EFILE.TXT` 五件 → `TEXT-ZH\`。
`FRONTS.TXT` / `TERRAINEX.TXT` / `MISC.TXT` / `EQUIP.CFG` / `equip.txt2` 按 `docs\32:287` 与 `docs\73:107` 的既有裁定**不译**（配置数值 + 英文注释，非玩家可见）。`Strings-Leaders.PL` 是波兰语领袖名词表，ZH 侧无对应槽位，沿用原文。

### 2.2 `SCENARIO\` 31 个文件的分工

| 文件 | 数量 | 性质 | 处理 |
|---|---:|---|---|
| `LC.txt` | 1 | **战役简介（真波兰语散文，12 行）** | 汉化 → `TEXT-ZH\SCENARIO\` |
| `LC0Ni.TXT` | 8（`00`–`07`） | **场景简报（真波兰语散文）** | 汉化 → `TEXT-ZH\SCENARIO\` |
| `LC0N.tmsg` | 3（`00`–`02`） | **任务提示文本（真波兰语散文）** | 汉化 → `TEXT-ZH\SCENARIO\` |
| `LC0N.xscn` | 8 | 场景数据（尾部串区 = 地图标签 + 番号） | 字节级回写 |
| `LC.xcam` | 1 | 战役流程（63,747 B，含 42 个可读串） | **纯文件名引用**（`LC00i.TXT`、`LC00bv.TXT`…）⇒ 无显示文本，不译 |
| `LC.cfg` | 1 | 战役参数（`green=1` / `green_cost=65` …） | 纯配置 |
| `LC0N.jpg` | 9 | 场景海报位图 | 不处理 |

**关键发现（源编码）**：`.txt` / `.tmsg` 与 `.xscn` 一致，都是 **cp1250**（波兰语 `ę ł ń ó ś ź ż ć ą`）。
`LC.txt:3` 原文 `Niemcy. Po dwóch dekadach po katastrofie WELTKRIEGU…`，按 cp1252 解码会得到 `Niemcy. Po dwÃ³ch dekadach…`；按 gbk 硬解会造出假汉字（`docs\76` 的教训）。本次全程 `decode("cp1250")` 读取。

**关键发现（缺失的胜败文本）**：`LC.xcam` 引用了 `LC00bv.TXT` / `LC00v.TXT` / `LC00tv.TXT` / `LC00l.TXT`（每关 4 件），但 `SCENARIO\` 里**这些文件一个都不存在**（只有 `i.TXT` + `.tmsg`）。
⇒ 本战役的「战胜/战败」档位没有对应文本，引擎将取不到内容（既非英文也非波兰文）。**这不是本次汉化的遗漏，是原作者就没做**。

---

## 三、`.xscn` 定译与字节级回写

### 3.1 结构与口径

沿用 `work\xscn\xscn.py`（阶段 0 已参数化）与 `work\xscn\POLICY.md`（番号/地名汉化风格指南，本作与 PG2 交付件同口径）。
8 个文件解析出 **332 槽**（组 -1 = 场景标题 8 · 组 0 = 地图地名 + 组 1 = 番号 324）。

### 3.2 定译来源（优先级从低到高覆盖）

| 来源 | 条数 |
|---|---:|
| 纯编号/符号（不含拉丁字母）⇒ 原样保留 | 353 |
| `work\xscn-all-map.tsv`（PG2 已实装件） | — |
| `work\xscn\master-glossary.tsv` | — |
| 人工表 `work\alberich\xscn_manual_data.py` 的 `MANUAL` | 326 |
| 同上 `KEEP`（原样保留） | 2（`T-19`、`FARE`） |

构建脚本 `work\alberich\build_xscn_map.py`，产物 `work\alberich\xscn-map.tsv`。
内置 lint 只查三项（**刻意不做主观质量判断**）：改写项必含汉字、`[]()` 数量不变、`/` 数量不变 ⇒ **结构可疑 0**。

**示例译文**（`LC00.xscn`）：
`UNTERNEHMEN FEUERZAUBER`→`「魔火」行动` · `Ceutahelicopters`→`休达直升机基地` · `Eddalya`→`埃达利亚` · `Tangier`→`丹吉尔` · `Ksar es Seghir`→`塞吉尔堡` · `Malabata`→`马拉巴塔` · `Aeroport de Tanger`→`丹吉尔机场` · `Pedro Valiente`→`佩德罗·巴连特`

### 3.3 回写

```
python work\xscn\xscn.py --root D:/OpenGeneral --efile ALBERICH --enc-in cp1250 \
       apply --map work/alberich/xscn-map.tsv --apply
```

**独立命令备份（先于覆盖）**：`D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_ALBERICH\SCENARIO\`（20 个文件 = 8 `.xscn` + 9 `.txt` + 3 `.tmsg`），逐文件 MD5 校验 **20/20 一致**。

### 3.4 ⚠️ 工具陷阱（两次踩坑，务必记住）

1. **`--src-first` 必须显式传**。`xscn.py` 的 `decode()`（`189-202`）默认先试 GBK；带 cp1250 变音符的串（如 `Ksar es Seghir` 里含 `ñ` 的波兰/西班牙专名）用 GBK 能解出汉字，于是被当成「已汉化」而 `if enc == ENC_OUT: continue` **静默跳过**。阶段 2 因此漏写 60 条，本阶段同样必须先 `--src-first`。
2. **`load_map()` 会吃掉映射表第 0 行**（`xscn.py:234`：`if i == 0 or not ln.strip(): continue`，为兼容带表头的词典）。映射表第 0 行不能放数据，否则该条静默丢失。

---

## 四、9 个 `.txt` + 3 个 `.tmsg` 汉化

### 4.1 工作方式

**由我直接写定译**（不投放子代理）。原因：阶段 2 派出的 6 个译者子代理**全部空手交付**，`work\gus_zx\zh\` 一个文件未产出（`MEMORY.md` 硬纪律「inactive ≠ 干完」再次应验）。本阶段量小（11 个文件 / 约 3,500 字），直接手写更快更可控。

脚本 `D:\DSH\_s3_prose.py`：按**行下标**替换（不改动未列出的行），保持原行尾（`splitlines(keepends=True)`），写后 GBK 回读断言逐字节相等，最后打印「未译非空行」清单 —— 跑完必须为空。

### 4.2 译文要点（波兰语 → 中文，不是英译中）

- `LC.txt:3` 全段：`德国。在世界大战那场浩劫降临于皇帝陛下的帝国之后，在耻辱的《凡尔赛条约》被强加之后，二十年过去，德国武装力量——国防军——如凤凰自灰烬中重生……以下便是那些以志愿部队「秃鹰军团」之名出征、与马克思主义者作战的人们的故事。`
- `LC00i.TXT`：`柏林 / 欢迎您，少尉。 / 以下是来自地中海地区的最新情报：西班牙爆发了军事叛乱…… / 摩洛哥 / 共和国舰队拥有数艘驱逐舰、两艘巡洋舰和一艘战列舰……`
- 番号缩写按 `POLICY.md` 处理：`CC.NN.`（意大利黑衫军）保留、`KOLUMNA DURRUTIEGO`→`杜鲁蒂纵队`、`BRYGADY MIĘDZYNARODOWE`→`国际旅`、`Legión Espanola`→`西班牙军团`、`Sonder Sturmgruppe 800`→`第800特别突击群`。
- 德语称呼 `Herr Leutnant`→`少尉先生` / `Herr Oberleutnant`→`上尉先生`（与阶段 2 的 `Herr General`→`将军阁下` 同一口径）。
- 战役/场景标题：`CONDOR TRIFFT EIN`→`秃鹰降临` · `UNTERNEHMEN FEUERZAUBER`→`「魔火」行动` · `SCHLACHT VON MÁLAGA`→`马拉加战役` · `ANGRIFF AUF BILBAO`→`进攻毕尔巴鄂` · `EBRO, NO PASARÁN!`→`埃布罗河，他们想通过！`（纠正为通行译法 `他们休想通过！`）。
- `.tmsg` 3 件是全篇战时提示，逐段译；其格式特点：**40 个用 `\r\n\r\n\r\n…` 填充的高行数**（`LC02.tmsg` 后 39 行全空），替换时严格按行下标操作，不为「好看」重排。

### 4.3 落盘

`D:\OpenGeneral\EFILE_ALBERICH\TEXT-ZH\SCENARIO\` 12 个文件，全部 **GBK / 无 BOM**：

| 文件 | 源 | 译 | 行数 |
|---|---:|---:|---|
| `LC.txt` | 1,349 B | 760 B | 12 / 12 |
| `LC00i.TXT` | 1,855 B | 1,065 B | 12 / 12 |
| `LC01i.TXT` | 2,316 B | 1,236 B | 14 / 14 |
| `LC02i.TXT` | 2,311 B | 1,319 B | 16 / 16 |
| `LC03i.TXT` | 2,412 B | 1,307 B | 12 / 12 |
| `LC04i.TXT` | 60 B | 50 B | 3 / 3 |
| `LC05i.TXT` | 62 B | 54 B | 3 / 3 |
| `LC06i.TXT` | 58 B | 62 B | 3 / 3 |
| `LC07i.TXT` | 76 B | 69 B | 5 / 5 |
| `LC00.tmsg` | 814 B | 463 B | 40 / 40 |
| `LC01.tmsg` | 547 B | 328 B | 40 / 40 |
| `LC02.tmsg` | 307 B | 200 B | 40 / 40 |

合计 6,913 B。

---

## 五、`.ply` / `.front` 盘点

`EFILE_ALBERICH\SCENARIO\` 下 **`.ply` 0 个、`.front` 0 个** —— 与 `docs\73:139`（`.ply` 0）一致。

（对照：`EFILE_GUS_Zx\SCENARIO\H02_Blitz14_i.PLY` 34 B = `Intro for Berlin\r\n* Intro text *\r\n`，阶段 2 已译为 `柏林战役开场\r\n* 开场文本 *\r\n` 落在 `TEXT-ZH\SCENARIO\`。本 efile 无此文件。）

---

## 六、校验（三项 + 闭环对拍，全部异常 0）

### 6.1 出稿 GBK / 无 BOM / 行数逐行对齐

```
### 1) 根级 TEXT-ZH vs 原文
  equip.txt            源  9435 行  译  9435 行  OK  BOM=False  汉字=10370
  names.txt            源  2976 行  译  2976 行  OK  BOM=False  汉字=12330
  NamesEx.txt          源  3040 行  译  3040 行  OK  BOM=False  汉字=12330
  nations.txt          源   106 行  译   106 行  OK  BOM=False  汉字=316
  strings_efile.txt    源   120 行  译   120 行  OK  BOM=False  汉字=253

### 2) TEXT-ZH\SCENARIO vs SCENARIO   —— 12/12 行数一致，BOM=False
异常: 0
```

### 6.2 `.xscn` 独立解析器复核

```
EFILE_ALBERICH: 备份条目 324 / 现状条目 324
   现状含汉字 322 / 无汉字 2
   尾部残留分布: [(0, 8)]
   --- 无汉字条目样例 ---
     LC00.xscn   g1.7   'T-19'
     LC00.xscn   g1.14  'FARE'
   结构偏差文件: 0
```

2 条无汉字是 `KEEP` 口径的**有意保留**（苏制坦克型号 `T-19`、西班牙无政府主义民兵缩写 `FARE`），非漏译。

### 6.3 逐槽闭环对拍（`work\xscn\check_loop.py`）

```
python check_loop.py D:/OpenGeneral \
   "D:/DSH/军事游戏汉化/backup/ORIGINAL-EFILE_ALBERICH/SCENARIO" EFILE_ALBERICH

文件 8 / 槽 332 / 改动槽 330 / 未改动槽 2 / 有改动文件 8
异常 0
```

判据含义：结构零偏差 + 槽外字节未动 + 新串均为合法 GBK 且含汉字。

### 6.4 `.xscn` ↔ `.txt` 硬桥校验

**不适用**。本 efile **没有**地图标签 `.txt`（`SCENARIO\` 里不带后缀的 `<name>.txt` 只有战役简介 `LC.txt`，无 `LC0N.txt`）⇒ `.xscn` 组 0/1 与 `.txt` 无镜像关系，硬桥为空集（0 个待比对象，**零新增**成立）。

---

## 七、产出物清单

**交付（游戏内生效）**

- `D:\OpenGeneral\EFILE_ALBERICH\TEXT-ZH\{equip,names,NamesEx,nations,strings_efile}.txt`（阶段 1，本次复核）
- `D:\OpenGeneral\EFILE_ALBERICH\TEXT-ZH\SCENARIO\` 12 个文件（本次）
- `D:\OpenGeneral\EFILE_ALBERICH\SCENARIO\{LC00…LC07}.xscn` 8 个（字节级回写）

**备份（可完整还原）**

- `D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_ALBERICH\SCENARIO\` —— 20 个文件，MD5 校验 20/20
  - 8 个 `.xscn`：已被改写（回滚用）
  - 9 个 `.txt` + 3 个 `.tmsg`：**原文未动**，MD5 与现行一致

**工具与中间产物（`work\alberich\`）**

- `xscn_manual_data.py` —— `MANUAL` 326 条 + `KEEP` 2 条
- `build_xscn_map.py` / `xscn-map.tsv` —— 映射表（含 lint）
- `D:\DSH\_s3_prose.py` —— 12 个散文文件的定译与落盘脚本（行下标替换 + 回读断言）
- `D:\DSH\_s3_verify.py` —— 根级 + 场景级编码/行数校验
- `D:\DSH\_s3_bakchk.py` —— 备份完整性核对

---

## 八、G3 实机验收清单（待用户确认）

请切到 `EFILE_ALBERICH`，进 `LC` 战役（`CONDOR TRIFFT EIN` / 「秃鹰降临」），逐项确认：

| # | 位置 | 应显示 |
|---|---|---|
| 1 | 战役选择页 → LC 战役说明 | 「秃鹰降临 / 欧洲 1936 / 德国。在世界大战那场浩劫……」全文中文 |
| 2 | 场景 0 简报（`LC00i.TXT`） | 「柏林 / 欢迎您，少尉。/ 以下是来自地中海地区的最新情报……」 |
| 3 | 场景 0 地图标签（`.xscn` 组 0） | 地名中文：`休达直升机基地`、`埃达利亚`、`丹吉尔`、`塞吉尔堡`、`马拉巴塔`、`丹吉尔机场` |
| 4 | 场景 0 部队番号（`.xscn` 组 1） | 番号链中文；`T-19`、`FARE` **原样保留**（有意） |
| 5 | 场景内任务提示（`LC00.tmsg`） | 「大部分运输力量已拨归胡安·亚圭上校指挥……西班牙万岁！」 |
| 6 | 装备浏览器 / 国家名（根级，阶段 1） | 中文 |

**特别关注 #5**：`.tmsg` 是本次第一次处理（阶段 2 的 `GUS_Zx` 里 `.tmsg` 全为空文件，未暴露）。若 #5 仍显示波兰语，则说明 `.tmsg` 不走 `TEXT-ZH\SCENARIO\` 覆盖层，需改为**备份后直接覆盖** `SCENARIO\LC0N.tmsg`（备份已就绪，一条命令即可）。

**若 #2 / #3 出现波兰语或英文**：说明覆盖层对该 efile 不生效，同样改为覆盖 `SCENARIO\` 原文（20 个文件已在备份中）。

---

## 九、遗留与待确认

1. ~~`docs\73:197` 的断言与阶段 2 实证矛盾~~ —— **已用反汇编定案，且定案结果支持本阶段做法**。
   `docs\06:14` / `docs\08:19` / `docs\73:197` 三处都写「`TEXT-ZH\SCENARIO\` 引擎根本不查这个路径」，但 `docs\14-实机三图复核与四层新发现.md:55-74` 的逐站点反汇编已把这三处**证伪**（原文即写着「旧结论『引擎根本不查 `TEXT-ZH\SCENARIO\`』是错的」）：

   | 模板 | 站点 | 目录来源 | 结论 |
   |---|---|---|---|
   | `%sSCENARIO\%s.xscn` | `0x725BC3` | `mov ecx,[0x11951AC]` = **EfileRoot** | 数据类**只认** `SCENARIO\` |
   | `%sSCENARIO\%s.xscn` | `0x6DAC6A` | `mov ecx,[0x11951AC]` = **EfileRoot** | 同上（全库仅此两处） |
   | `%sSCENARIO\%s.ply` | `0x7321B1` | `mov ecx,[0x11951B0]` = **LangDir** | 文本类 **LangDir 优先** |
   | `%sSCENARIO\%s.txt` | `0x757011` | `mov edx,[0x11951B0]` = **LangDir** | 文本类 **LangDir 优先** |
   | `%sSCENARIO\%s`（通用） | `0x7E8C7A` | `mov ecx,[0x11951B0]` = **LangDir** | 首选，打不开则回退 EfileRoot（`0x7E8CF1`） |

   ⇒ **判据：数据类（`.xscn`）只认 `<efile>\SCENARIO\`；文本类（`.txt` / `.ply` / `.tmsg`）`TEXT-ZH\SCENARIO\` 优先、可回退 efile 根。**
   这正是本阶段（以及阶段 2）的做法：`.xscn` 就地字节级回写，`.txt`/`.tmsg` 落覆盖层。
   **仍建议修订 `docs\73:197` 那一行**，以免后续阶段（4/5/6）再按错误口径去覆盖原文。
2. **`.tmsg` 未在 `docs\14` 的站点表里单列**，故其是否走 LangDir 属**推断而非实证**（依据：同族的通用模板 `0x7E8C7A` 是 LangDir 优先）。见 §八 #5 的实机确认项；若不生效，改覆盖原文即可（备份已就绪）。
3. **`SCENARIO\LC.xcam` 引用的 `LC0N{bv,v,tv,l}.TXT` 全部缺失** —— 原作者未制作胜败文本，非本次遗漏。若用户希望在胜败时看到中文，需要**新增**这 32 个文件（`LC00`–`LC07` × 4），属超出「汉化」范围的新增内容，需用户决定。
4. **`OPENLOG\` 的 AAR/ASR 日志**是玩家存档的战后报告（英文/波兰语混杂），属运行时生成物，不属汉化对象。
5. **阶段 7 待盘点项**：`MAPFILES\*.mapx`（1,242 个）的地名归属仍未裁定（`docs\73:73`）。

---

## 十、下一步

阶段 3 出口 = **G3**：`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译（`docs\73:236`）。
本阶段实测：`.xscn` 322/324 = **99.4% 含汉字**（2 条为有意保留）· `.txt` **100%**（12/12 全译，含 `.tmsg`）· `.ply` **0 个** ⇒ **数据侧已达标**。

G3 通过后进入 **阶段 4 · `EFILE_GUS` 全层收官**（`docs\73:145-151`）：`.xscn` 978 个 / 61,975 槽位 / **27,367 唯一串**（程序覆盖仅 46.8%，需人工 14,548 条）· `SCENARIO\*.txt` 2,463 个 / **1,146,106 字符** · `.ply` 31 个。这是全计划**最大的一块**（8–15 人·日，与阶段 6 合计约占总量 50%），开工前需先定「散文是否走 MT 初稿 + 精修」的路线。

---

## 十一、文本面全覆盖审计（本轮补充：回答「还有没有漏掉的可见文本」）

阶段 3 收尾时对 `EFILE_ALBERICH` 做了**穷尽式**文本面清点（`D:\DSH\_probe_alb_txt.py` + 四条 exe 反查），结论如下。

### 11.1 逐个候选文件裁定

| 文件 | 大小 | 裁定 | 依据 |
|---|---:|---|---|
| `MISC.TXT` | 257 B | **死文件，不处理** | exe 内**不存在** `MISC` 文件名字符串（大小写不敏感搜 16 处命中全是 COM 注册表噪声，无一带 `.txt`）⇒ 引擎从不读取。另：`EFILE_GUS` / `EFILE_GUS_Zx` **根本没有这个文件**，而 GUS_Zx 已被用户验收为「无英文」⇒ 反向印证其不可见。内容只是 PG2 时代的遗留（17 个地形名 + `Close Assault` / `Attk:` / `Dfnd:` / `Remove this Line:` 等） |
| `Strings-Leaders.PL` | 2,326 B | **死文件，不处理** | 全盘 exe 里 `Strings-Leaders` 只出现 **1 次**，位于窗口 486 B 的**文件对话框**串里：`%s%s\` … `Nations.txt` `Nations.txt` `PL` `Strings-Leaders.pl` `rt` `*.txt` `TXT Files \|*.txt\|` `Antique.ini` —— 与 `gui97.txt` / `Select GUI97 or Nations txt file` 同处一段，是**编辑器「打开文件」对话框的默认名与过滤器列表**，不是运行时加载路径 |
| `FRONTS.TXT` / `TERRAINEX.TXT` | 4.9 KB / 11.2 KB | 无玩家可见文本 | 与 `docs\32:287` 裁定一致；且有 `TEXT-ZH\` 覆盖层机制可用而未被原作者使用 |
| `NATIONS.TXT` / `equip.txt2` / `EquipIcons.csv` / `efile.xml` / `Debug1.log` | — | 无显示文本 | 数据/图标/元数据 |
| `OPENLOG\*.log` · `OPENLOG\AAR_*.txt` · `OPENLOG\ASR_*.txt` | — | **运行时生成物** | 战后报告与 AI 日志（已汉化/未汉化混杂，因是玩家实际游玩时写出的）。不属汉化对象 |
| `SCENARIO\*.txt` / `*.tmsg` | 12 个 | **已全部汉化** | 见 §四；落 `TEXT-ZH\SCENARIO\` |

### 11.2 领袖技能串：34/41 已汉化，7 条为引擎硬编码（**不可由数据修复**）

`OPENGUI\strings-zh.txt`（15,291 B / **916 行，与 `OPENTXT\strings-en-template.txt` 逐行同构**）已把 UI 全部汉化，其中第 **879–913 行**是领袖技能串，实测 **34 条全部已译**：

```
en[879] Tenacious Defense : +4 to Defense   → zh: 顽强防御 : 防御 +4
en[886] Skilled Assault : Inmune to …        → zh: 突击专家 : 免疫背阳突袭与 AA 拦截
en[893] Fire Discipline : Uses ammo at half rate → zh: 射击纪律 : 弹药消耗减半
…（34/34 命中）
```

**未覆盖的 7 条**是海军技能，它们在**英文模板里根本不存在**：`Expert Sea Wolf` · `Deep Sea Hunter` · `Expert Sea Whale` · `Expert Sea Base` · `Expert Sea Bear` · `Blockade Vessel` · `Screening Vessel`。

反查 exe（偏移 `0x5B36A0` 附近）证实：这些串以**定长 `\0` 填充表**的形式**硬编码在 exe 内**，且同时存在英文与波兰文两份：

```
'…Shock Tactics : Inflicts suppression lasting the entire turn\x00…'
'…Flak Support : Close Support Fire and Multiple intercept\x00…'
'…Expert Sea Wolf : ignores ZOC and + 1 to Defense\x00…'
'…Deep Sea Hunter : ignores Evasion Skill and +1 naval attack\x00…'
（另有波兰文副本 'Expert Sea Wolf : Ignoruje wrogie strefy kontroli, +1 do obrony'）
```

而 efile 级 `STRINGS_EFILE.TXT` 只支持 `[terrain] [movement] [movement2] [classes] [requisition]` 五个节，**没有 `[leaders]`**；`Strings-XX.txt` 模板又标注「**Do not remove neither insert lines**」，行数固定 916。

⇒ **这 7 条海军领袖技能没有本地化挂钩，数据层无法修**。影响面极小（只在悬停海军领袖的海军技能时出现英文），且 `EFILE_GUS` / `EFILE_GUS_Zx` / `EFILE_ALBERICH` 三个 efile **完全同等**——已验收的 GUS_Zx 也一样。**不作为缺陷，仅作记录**。

### 11.3 审计结论

**`EFILE_ALBERICH` 不存在被遗漏的、可由数据文件修复的可见文本。** 剩余英文只有两类，且都不是本 efile 的问题：
1. exe 硬编码串（上述 7 条海军技能、`Attacker : %s` / `Forever: Attacker:%d` 等调试串）；
2. `OPENLOG\` 的玩家运行时日志。
