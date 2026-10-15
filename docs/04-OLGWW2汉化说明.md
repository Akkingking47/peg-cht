# OLGWW2（EFILE_OLGWW2）efile 汉化说明

- 目标 efile：`D:\OpenPG2\EFILE_OLGWW2`（Open LGWW2 v2.26 / Apr.2013）
- 完成日期：本次会话
- 状态：**已部署并实测通过**

---

## 一、完成情况

| 文件 | 内容 | 体量 | 状态 |
|---|---|---|---|
| `TEXT-ZH\nations.txt` | 阵营 + 74 国国名 | 83 行 | ✅ |
| `TEXT-ZH\strings_efile.txt` | 覆盖 `[classes]` `[requisition]` `[terrain]` 三段 | 82 行 | ✅ |
| `TEXT-ZH\equip.txt` | 单位名称（型号保留、兵种/编制名译中文） | **1417 处** | ✅ |
| `TEXT-ZH\names.txt` | 将领姓名（72 组） | **2232 处** | ✅ |
| `TEXT-ZH\SCENARIO\*.txt` | 场景文本 | **807 个文件** | ✅ |

### 实测证据

| 界面 | 显示 |
|---|---|
| 战役标题 | `西班牙十字军：北方烽火` |
| 战役简介 | `在西班牙的冲突中，西班牙将是争夺焦点…` / `作者: Santiago Fuentes` |
| 国家名 | `西班牙国民军` |
| 场景列表标题 | `1940年5月` `博斯托尔十字军` `闪击波兰` `黄色方案` `大不列颠之战` `巴巴罗萨` `顿河` `台风` |
| UI | `EFile 文件夹:` `9 个场景` `检查地图（不下载）` `按文件名排序` |

---

## 二、为什么必须做 `TEXT-ZH\`

OLGWW2 的 `strings_efile.txt` **覆盖** UI 的 `[classes]`/`[requisition]`/`[terrain]`，其中含本 efile 特有的 `Mobile Air Defense`（→机动防空）、`Dense Underbrush`（→密灌丛）、`Tact. Bomber, Fighter-Bomber`（→战术轰炸机/战斗轰炸机）等。

注意：它**没有 `[results]` 段**，所以胜负等级直接用 UI 的 `strings-zh.txt`（决定性胜利/胜利/战术胜利/失败）。

---

## 三、题材特点与立场处理（重点）

OLGWW2 是**全球二战**题材，`nations.txt` 74 国覆盖欧洲、北非、苏德、太平洋、**中国战场**与满洲：

```
Nationalist China 国民政府    Communist China 中国共产党   Warlord China 军阀势力
Manchukuo 满洲国              Nanjing China 南京国民政府    Mengjiang 蒙疆
Fengtian clique 奉系          P.R. of China 中华人民共和国  Japan 日本
South Korea 韩国              North Korea 朝鲜             Free India 自由印度
```

所有译者统一执行：

1. **同一事件敌我称呼不同**（淮海/徐蚌 原则）：
   - 德军视角用德军代号（`Wacht am Rhein`→莱茵守望行动、`Zitadelle`→堡垒行动、`Fall Weiss`→白色方案）
   - 盟军视角用盟军代号（`Overlord`→霸王行动、`Cobra`→眼镜蛇行动）
   - 比利时/盟军文本用"德军/德国空军/第N装甲师"；DAK 轴心方文本用"我们/英军/最高统帅部"
   - 西班牙内战 gcn 系列按**国民军视角**：Nationalist→国民军、Republican→共和派
2. **禁止蔑称与旧称**：全库扫描 `支那`/`匪`/`鬼子`/`伪军` 等，**0 命中**
3. **中文人名还原汉字**：`names.txt` 中国/日本/朝鲜组的拼音与罗马字还原为汉字（如 `Chen`→陈、`Mao Zedong`→毛泽东）
4. **陆军/海军/空军编制名按所属方语言译中文**，装备型号与部队番号一律保留原文

---

## 四、装备名统一口径

| 类别 | 处理 | 例 |
|---|---|---|
| 装备型号/编号 | **保留原文** | `M4A1`、`Pz IVH`、`Type 97 Chi-Ha`、`SdKfz 251/1`、`Ki-84-Ia Hayate` |
| 军舰舰名/**舰级** | **保留原文** | `Yamato Class`、`Graf Zeppelin Class`、`Gearing Class`（共 316 处） |
| 舰级中的通用词 | 译 | `Saattaja Class`→护卫艇级 |
| 口径+类型混合名 | 保留数字+译类型 | `4.2inch Mortar`→4.2 英寸迫击炮、`12" Coastal Battery`→12 英寸岸防炮台 |
| 纯口径行 | 保留 | `37mm`、`88mm` |
| 缴获标记 | 保留 | `T-34/85 (Capt.)`、`(f)`/`(i)`/`(r)` |
| 通用军事缩写 | 保留 | `MG`、`HMG`、`NKVD`、`PSZ`、`KOP`、`LRDG`、`AAMG` |
| 有通行中文名的机构 | 译 | `RCMP`→加拿大皇家骑警 |
| 各语种兵种/编制/后勤名 | 译中文 | `Hohei`→步兵、`Rikusentai`→海军陆战队、`Teisintai`→挺身队、`Versorgung-LKW`→补给卡车 |

---

## 五、过程中解决的三个技术问题

1. **GBK 无法编码源文件的重音字符**
   `equip.txt` 含 `Göring`/`Muñoz` 等 CP1252 字符，整文件转 GBK 会失败。
   **解法**：改为**字节级替换**（`apply-maps-bytes.ps1`）——只有被翻译的行用 GBK 编码，其余行保留原始字节，未改动行与原文逐字节一致。

2. **`names.txt` 有 3 处纯 LF 行尾**（第 31、847、1110 行附近）
   按 CRLF 分割会少算 3 行导致行号越界。
   **解法**：按 LF 分割并统一输出 CRLF（官方规范本就要求 CRLF）。

3. **`names.txt` 的组顺序与 `nations.txt` 不一致**
   并行译者核对文件实际人名内容后发现对照错位（Mongolia 甚至出现两次）。
   **解法**：一律以**文件实际内容**判断国别，不依赖组号对照表。

---

## 六、协作与质量把关

- **16 个译者并行**（场景 8 + equip 5 + names 3），后因部分掉线中断，追加 **8 个补译**（只补缺口，不重做已完成）
- 生成 `work\olgww2\missing.txt` 逐段列出精确缺失文件名，重跑成本可控
- 多轮交叉审计：行数逐文件比对、UTF-8 无 BOM、无 U+FFFD、残留英文句扫描、禁用词扫描、繁简字审计
- 修正：`names-map-3` 的 93 条 `Leader` 占位符由「领袖」统一为**指挥官**（与 UI 一致）；`names-map-2` 的 `1147/1178` 姓名对应颠倒（`Hung`↔`Kuan-ying`）
- 日期格式全库归一化为无空格中文格式（`1941年5月14日`）

---

## 七、已知盲区（同 OPENPG，引擎硬编码）

- 程序级对话框（如退出确认框）
- 战役浏览器窗口的部分文字（`Welcome to Open General`、`Filter campaigns having` 等，模板 916 行中不存在）
- efile 名称/描述（`efile.xml`）、战役名单（`Campaigns.csv`）

---

## 八、工作目录

```
work\olgww2\
  ├─ nations.utf8.txt / strings_efile.utf8.txt   ← 小文件工作稿
  ├─ equip-map-1..5.tsv                          ← equip 翻译映射（1417 条）
  ├─ names-map-1..3.tsv                          ← names 翻译映射（2232 条）
  ├─ scenario\*.utf8.txt                         ← 807 个场景文本工作稿
  ├─ segments.txt / missing.txt                  ← 分段与缺口清单
  ├─ apply-maps-bytes.ps1                        ← 字节级映射套用（含 LF/CRLF 处理）
  └─ deploy-scenario.ps1                         ← 场景批量转 GBK 部署
```

回滚：删除 `EFILE_OLGWW2\TEXT-ZH\` 即恢复原状（原文件从未改动）。
