# 78 · OpenGeneral 汉化阶段 2：EFILE_GUS_Zx 全层收官执行报告

> 阶段目标（goal `goal-11421b2d-beb3-4783-81ae-52d856e812f0` objective）：
> 完成 OpenGeneral 汉化阶段 2 —— EFILE_GUS_Zx 全层收官：（1）76 个 `.xscn` 的 1,818 条唯一串全部定译并字节级回写；（2）118 个 `SCENARIO\*.txt`（63,052 字符）汉化覆盖（先备份）；（3）`.ply` 与 `.tmsg` 盘点处理；（4）三项校验 + `check_loop` 逐槽对拍异常 0；（5）出 docs/78 执行报告并交用户实机验收关键门 G2。
> 硬约束：**全程不动任何原文**；覆盖前必须独立命令备份。

---

## 一、结论速览

| 项 | 数量 | 状态 |
|---|---:|---|
| `.xscn` 字节级回写 | 76 文件 / 3,044 槽 / **2,306 槽改写** | ✅ 异常 0 |
| `.xscn` → `.txt` 硬桥 | 2,230 条中文串逐条比对 | ✅ 未命中 0 |
| 118 个 `SCENARIO\*.txt` 覆盖层 | 118 文件 / 63,231 字符 → **61,151 B（GBK）** | ✅ 119/119 行对齐 |
| `H02_Blitz14_i.PLY` | 1 文件 / 34 B → 28 B | ✅ 已译 |
| `.tmsg` | 15 文件 × 80 B，内容只有 `\r\n` | ✅ 无文本，无需处理 |
| `.front` | 30 文件 × 160 B，首字节 `01` 其余全 0 | ✅ 二进制无文本 |
| 三项校验 + `check_loop` | — | ✅ **异常 0** |
| G2 实机验收 | 地图标签 / 单位面板 / 场景简报 / 胜败文本 | ⏳ 待用户 |

**原文零改动**：`SCENARIO\` 下 118 个 `.txt` 与 30 个 `.front`、15 个 `.tmsg`、`H02_Blitz14_i.PLY` 的 mtime 全部保持出厂日期（仅 76 个 `.xscn` 于 2026-10-16 被写入，写入前已独立备份）。

---

## 二、勘察结论（决定了工作量的边界）

### 2.1 GUS_Zx 的数据层与 GUS 逐字节相同

`D:\OpenGeneral\EFILE_GUS_Zx` 共 **453 个文件**（GUS 为 7,173 个）。逐文件 md5 比对：

- `TEXT-ZH\` 5 个文件（`equip.txt` `names.txt` `NamesEx.txt` `nations.txt` `strings_efile.txt`）与 `EFILE_GUS\TEXT-ZH\` **全部全等**（`equip.txt` = `e9d80bbfbb64…`，正是阶段 1 回滚后记录的 md5）。
- 根目录 `equip.txt` `equip.txt2` `fronts.txt` `names.txt` `namesex.txt` `nations.txt` `strings_efile.txt` `terrainex.txt` 也全部全等。

⇒ **GUS_Zx 不含任何新的数据层文本**，阶段 2 的工作量全部落在 `SCENARIO\`。

### 2.2 场景目录盘点

| 类型 | 数量 | 判定 |
|---|---:|---|
| `.xscn` | 76（2,895,748 B） | 尾部串区含全部显示文本，**需回写** |
| `.txt` | 118（63,231 B） | 战役说明 / 场景简报 / 胜败文本 / 地图标签表，**需汉化** |
| `.scn` | 24（380,601 B） | 二进制，唯一可读串是 `MOKRA.MAP` 之类地图文件名 |
| `.front` | 30 | 各 160 B，首字节 `01` 其余全 `0x00` |
| `.tmsg` | 15 | 各 80 B，内容全是 `\r\n`（40 个空行） |
| `.PLY` | 1 | `H02_Blitz14_i.PLY` = 34 B（**有文本**，占位串） |
| `.xcam` / `.jpg` | 3 / 3 | 战役图与图片 |

### 2.3 覆盖层机制（语言后缀 = `zh`）

- `D:\OpenGeneral\Settings.cfg`：`EFolder=efile_gus\`、**`UI_Lang=strings-zh`**、`Font1=Font2=simhei.ttf`、`SzFont1=SzFont2=12`。
- `OpenGen.exe`（6,310,400 B）字符串区掘出四段相邻常量 **`"STRINGS-"` `"TEXT-"` `"TEXT-"` `"STRINGS-"`**，以及 `%sSCENARIO\%s.txt`、`%sSCENARIO\%s.tmsg`、`%sSCENARIO\%s.ply`、**`%s%s%s.ply`**、`%s%s%s.txt`。
- mod 里 `EFILE_GUS\TEXT-PL\SCENARIO\` 有 **2,286 个波兰语 `.txt`** 覆盖文件，而 `EFILE_GUS\SCENARIO\` 放英语基准（`B01_PW.txt` 英文 vs `TEXT-PL\SCENARIO\B01_PW.txt` 波兰语 `B01 PLAN WSCHÓD v.4.2`）。

⇒ 引擎按 `UI_Lang` 的语言后缀找 **`TEXT-<lang>\`** 覆盖层：efile 文本走 `TEXT-ZH\`，场景文本走 **`TEXT-ZH\SCENARIO\`**。本次即新建该目录落盘，**`SCENARIO\` 原文一字未动**。

---

## 三、`.xscn` 定译与字节级回写

### 3.1 结构

`work\xscn\xscn.py` 解析出的结构：`<场景数据> <N:####> 标题(u16 长度+字节) 组1(u16 计数)[u16 长度+字节]…`。

GUS_Zx 实测：**76 文件 / 3,044 槽**，组号分布：

| 组 | 槽数 | 含义 | 唯一串 |
|---|---:|---|---:|
| −1 | 76 | 场景标题 | 75 |
| 0 | 741 | 地图地名 | 603 |
| 1 | 2,227 | 部队番号 | 1,218 |

**源编码 = cp1250**（波兰语），不是 cp1252。硬证据：`H02_Blitz02.xscn` 里 `Łowicz` 的字节为 `… 06 00 a3 6f 77 69 63 7a`，`0xA3` 在 cp1250 是 `Ł`（cp1252 是 `£`，且 U+00A3 不可 cp1250 编码）⇒ 必须 `--enc-in cp1250`。

### 3.2 覆盖口径

优先链（后者覆盖前者），产出 `work\gus_zx\xscn-map.tsv`（`src<TAB>dst`）：

1. **原文不含拉丁字母 → 原样保留**（`1`、`5/6`、`777/6`、`[XV]` 等纯编号/方括号代号不加「第」）
2. `work\xscn-all-map.tsv`（PG2 已实装，16,245 行 / 8,711 条）—— 命中 296
3. `work\xscn\master-glossary.tsv`（124,270 条）—— 命中 468
4. `work\xscn\_xscn_dict.tsv`（79,603 条）—— 补 4
5. `work\gus_zx\xscn_manual_data.py` 的 `MANUAL`（527 条人工定译）—— 命中 527
6. `KEEP`（47 条原样保留）

**登记表**：槽位 3,120 / 唯一 1,885；覆盖 1,883 条（其中保留原文 589）；来源分布 `keep-noletters 544 / MANUAL 527 / glossary 468 / all-map 296 / KEEP 47 / xscn-dict 4`；**未覆盖 0 / 结构可疑 0**。

口径权威文件：`work\xscn\POLICY.md`（序号「第+阿拉伯数字」、去英波序数后缀、罗马数字转阿拉伯、结构与分隔符 `/ [ ] ( )` 及空格逐字保留、地名有通行名用通行名否则音译+通名、**拿不准一律保留原文**）。

### 3.3 回写

```
python work\xscn\xscn.py --root D:/OpenGeneral --efile GUS_Zx --enc-in cp1250 \
       apply --map work/gus_zx/xscn-map.tsv --apply
```

**踩到的工具陷阱（两处，均已修）**：

1. `xscn.py:234 load_map()` 跳过文件第 0 行（为兼容带表头词典）⇒ 无表头的映射表会吃掉第一条。已在映射表加表头行解决。
2. 未加 `--src-first` 时，`decode()` 会先探测 GBK，把 cp1250 高字节吞成**假汉字**（`p³k. Gustlik` → `p砶. Gustlik`）⇒ 必须先 `set_src_first(True)`。加上之后又补写了 60 个槽，最终 **2,306 槽改写 / 738 槽保留**。

**写入前独立备份**：`backup\OpenGeneral-EFILE_GUS_Zx-SCENARIO-xscn.before-zh\`（路径记于 `work\gus_zx\_xscn-backup-path.txt`）；出厂原文另存于 `backup\ORIGINAL-EFILE_GUS_Zx\SCENARIO\`（76 个 `.xscn`，本次所有对拍的基准）。

聚合 md5（76 个 `.xscn` 按文件名序串接）：`af01aad124819e29f03a0c930abae920`。

---

## 四、118 个 `SCENARIO\*.txt` 汉化

### 4.1 后缀体系（与 `TEXT-PL\SCENARIO\` 对照后确认）

| 后缀 | 含义 | 例 |
|---|---|---|
| 无 | **地图标签表**（= `.xscn` 组 0/1 的逐行镜像，须与 `.xscn` 同步） | `G27_STA03.txt` 184 行 |
| `i` | 场景简报 | `G27_STA00i.TXT` 587 B |
| `bv` | 小胜 | `H02_Blitz00bv.txt` |
| `tv` | 决定性胜利 | `H02_Blitz00tv.txt` |
| `v` | 胜利 | `H02_Blitz13v.txt` |
| `l` | 失败横幅 | `H02_Blitz00l.txt` = `Dupa zbita.` |
| `__flow` | **引擎自己生成的**战役流程报表（非输入） | `G06__flow.txt` 7,732 字符 |

`__flow.txt` 由引擎写出（exe 字符串区 `# End_Scenario`、`Flow_`、`%-5s    %-45s   %s` 在写出上下文），但仍需汉化场景标题列并**保持列宽**（用「CJK 计 2 列」重算填充空格）。

### 4.2 落盘

- 源副本导出：`work\gus_zx\src\`（118 个 UTF-8 无 BOM，`manifest.tsv` 记 `file/bytes/crlf/lf_only/chars`）。
- 译稿：`work\gus_zx\zh\`（118 个）。标签表 (=`.xscn` 镜像) 复用 `xscn-map.tsv` 字典，**保证与 `.xscn` 中文完全一致**；散文（`i/bv/tv/v/l`）由 `_tr_prose.py` 定译；战役级与 `__flow` 由 `_tr_batch1.py` 定译。
- **换行符逐字节保留**：118 个文件里 **56 个完全无换行符**（多为单行 `i/bv/tv/l`），其余 CRLF ⇒ 一律 `newline=""` 处理。

**行对齐硬约束**：`_tr_prose.py` 对每个文件强制 `len(译行) == len(源行)`，不一致即断言失败。首轮 14 个文件（多段简报 / 带尾随空行的胜败文本）行数不符，已逐条修正（`G27_STA03i.TXT`、`H02_Blitz21i.txt` 为原文硬折行，按折行位置拆句；其余为补齐尾随空行）。

落盘脚本 `work\gus_zx\deploy_txt.py` → `D:\OpenGeneral\EFILE_GUS_Zx\TEXT-ZH\SCENARIO\`：

- `.txt` **118 个 / 61,151 B**（GBK 无 BOM），聚合 md5 `a508b5e66e38e6a94a8082deafe79910`
- `.PLY` **1 个 / 28 B**（`柏林战役开场\r\n* 开场文本 *\r\n`）
- 写后逐文件 GBK 回读比对：**118/118 一致**

---

## 五、`.ply` / `.tmsg` 盘点

- `H02_Blitz14_i.PLY`：原文 `Intro for Berlin\r\n* Intro text *\r\n`（34 B，占位文本，作者未填）⇒ 译为 `柏林战役开场\r\n* 开场文本 *\r\n`（28 B）。
- `.tmsg` 15 个：各 80 B，逐字节只有 `\r\n` ⇒ **无文本**，不需处理（引擎占位）。
- `.front` 30 个：各 160 B，首字节 `01`，其余全 `0x00` ⇒ 二进制阵型数据，无文本。

---

## 六、校验（三项 + 闭环对拍，全部异常 0）

`work\gus_zx\verify_all.py`：

```
[1] 覆盖层 GBK/无BOM/行对齐：通过 119 / 119
[2] 独立解析器：文件 76 / 条目 2968 / 改写槽 2230 / 非GBK 0 / 尾部残留文件 0
[3] .xscn↔.txt 硬桥：配对 30 / 校验中文串 2230 / 未命中 0 / 无标签表 46

=== 异常 0 ===
```

`work\xscn\check_loop.py D:\OpenGeneral <备份> EFILE_GUS_Zx`：

```
文件 76 / 槽 3044 / 改动槽 2306 / 未改动槽 738 / 有改动文件 76
异常 0
```

`check_loop` 逐项复核：结构零偏差（槽位数 / 组表 / 尾部残留）、改动落点可控（串区起始之前的场景数据逐字节相同）、编码正确（新串合法 GBK 且含汉字）、原文未受损（未改写槽与备份逐字节相同）。

**判据陷阱（本次踩到并修正）**：未改写的槽里可能残留 cp1250 高位字节（如 `ń` = `0xF1`），用 GBK 解码会造出**假汉字**（`SBS Podhalańskich` → `SBS Podhala駍kich`），据此统计「含汉字」会误报、据此做硬桥会误判未命中。**正确判据是「与备份字节不同」**，`verify_all.py` 已改为以备份对拍为准。`G06_01…G06_46` 共 46 个场景在原包里**本来就没有同名标签表**，不计异常。

---

## 七、产出物清单

| 路径 | 说明 |
|---|---|
| `D:\OpenGeneral\EFILE_GUS_Zx\TEXT-ZH\SCENARIO\` | **交付物**：118 个 `.txt` + 1 个 `.PLY`（GBK 无 BOM） |
| `D:\OpenGeneral\EFILE_GUS_Zx\SCENARIO\*.xscn` | **交付物**：76 个已字节级回写（2,306 槽） |
| `work\gus_zx\xscn-map.tsv` | 1,883 条 `src<TAB>dst` 映射表（唯一串全覆盖） |
| `work\gus_zx\xscn_manual_data.py` | 527 条人工定译 `MANUAL` + 47 条 `KEEP` |
| `work\gus_zx\build_xscn_map.py` | 映射表构建 + lint（含汉字 / `[]()` 数量不变 / `/` 数量不变） |
| `work\gus_zx\_tr_prose.py` / `_tr_batch1.py` / `_tr_labels.py` | 散文 / 战役级 / 标签表定译 |
| `work\gus_zx\deploy_txt.py` | 覆盖层 GBK 落盘 + 回读比对 |
| `work\gus_zx\verify_all.py` | 三项校验 + 硬桥 |
| `work\gus_zx\src\`、`zh\`、`manifest.tsv` | 源副本 / 译稿 / 清单 |
| `work\xscn\POLICY.md` | 番号/地名汉化风格指南（权威口径） |
| `backup\OpenGeneral-EFILE_GUS_Zx-SCENARIO-xscn.before-zh\` | 写 `.xscn` 前的独立备份 |
| `backup\ORIGINAL-EFILE_GUS_Zx\SCENARIO\` | 出厂 76 个 `.xscn` 原文 |

---

## 八、G2 实机验收清单（待用户确认）

请进入 **H02「为了第三帝国」** 或 **G27 斯大林格勒** 战役，确认以下四处**均无英文/波兰文**：

1. **地图标签**——地图上的地名与部队番号（如 `莫克拉`、`第1装甲师/第4侦察营`、`马马耶夫岗`）。
2. **单位面板**——点选部队后右上角面板里的单位名。
3. **场景简报**——开局前的任务说明（如 `莫克拉，1939年9月1日约10:00。赖因哈特将军第4装甲师的第36装甲团…`）。
4. **胜败文本**——战斗结束后的结局简报与失败横幅（横幅应为「一败涂地。」）。

**若地图标签仍显示波兰语**：说明引擎不读 `TEXT-ZH\SCENARIO\`，此时需改为直接覆盖 `SCENARIO\*.txt`（**落盘前必须先备份该目录 118 个 `.txt`**）——这是本报告唯一尚未被实机证实的假设，请务必回一个结论。

---

## 九、遗留

1. **G2 验收**（上文第八节）——覆盖层路径假设待实机确认。
2. `TEXT-ZH\SCENARIO\` 目前只有 GUS_Zx 这一个 efile 的场景覆盖；其余 efile 的场景文本仍为原文（不在阶段 2 范围）。
3. `G06` 战役的 46 个场景在原包里没有标签表，其地名/番号只存在于 `.xscn`（已译），无 `.txt` 可同步。
