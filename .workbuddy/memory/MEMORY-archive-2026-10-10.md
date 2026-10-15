# Open General（OpenPG）汉化工程 · 索引

> 游戏 `D:\OpenPG2`（OpenGen 26.3.30.0；SDL2+SDL2_ttf；PE32 ImageBase `0x400000`，exe 恒 6316032 B）。工作区 `D:\DSH\军事游戏汉化`。
> 必读：`MECHANICS.md`（各层机制与坑，86KB）· `docs\08`（排查方法论）· `docs\30`（推进方案）· `docs\24`（排期）· `glossary\README.md`。
> 译名真源：`glossary\standard-glossary.tsv`（23,200 条，UTF-8 BOM）。
> ⭐ **统一总词库（10-08 建）**：`work\xscn\master-glossary.tsv`（119,624 条整串，分 xscn/root/prose/glossary 四层）
>   ＋ `master-words.tsv`（1,849 词级通名）。由 `build_{dict,root_dict,prose_dict}.py`（原文↔部署件**全量配对**）＋ `build_master.py`（合并）产出；
>   `apply_master.py` 做「程序优先匹配」——**新 efile 开工先跑它，master 覆盖 ~93%，只剩 ~6% 交 LLM**（PzLIGA 实测 94.4%）。
>   ⭐ **冲突裁定（10-08）**：`resolve_master.py` + `master-overrides.tsv`（21 条人工订正）→ `master-resolve.tsv`（1,436 条 src→权威译法），
>   `build_master.py`/`apply_master.py` 已接线；重建后 master-glossary **0 多译法残留**。
>   每完成一个 efile 跑一遍四连：`build_dict && build_root_dict && build_prose_dict && build_master`，成果自动沉淀回总库。
> 进度真源＝本文件 §一；投影＝`docs\00` §三（`work\audit\progress.py` 实测，可复算）。
> 本文件只放**状态与决策**；「怎么运作／踩过什么坑」一律在 `MECHANICS.md`。

## 一、进度（21 efile，已收官 **11**；交付单位＝一个 efile）

**已收官**：`AG` · `AO` · `ATOMIC`（10-09） · `BASEKORP` · `COMWW2`（10-09） · `GCE`（10-08） · `KAISER`（10-08） · `NASHORNPBEM` · `OLGWW2` · `OPENPG` · `PzLIGA`（10-09）（判据＝`.xscn` 漏译≤0.5% 且 `.txt`>99% 且 `.ply` 全译）。
✅ **`COMWW2` / `ATOMIC` 的 cp1252 残槽已于 10-09 收口**（10-08 曾把 COMWW2 从「已收官」撤回）：
`.xscn` 漏译 `COMWW2` 432 → **3**（`KievFD`×2 · `32Para`）、`ATOMIC` 761 → **5**
（`12.AF/…/1°GAVCA`×2 · `Pz/IT-Superga` · `Gustlik2008` · 乱码串 `Ð#ð#P$à$`）—— **余项全为口径保留**。
根因＝`ó/ö/á/é/ü/ä/ø/å` 等 cp1252 高字节被 `decode('gbk')` 解成**假汉字** ⇒ `apply`/`zhfix` 双跳，
**只能走 `rawfix`**；工具链见 §六。落地：`atomic-xscn-rawfix.tsv`(402) / `comww2-xscn-rawfix.tsv`(302)，
改写 **763 ＋ 436 槽 / 68 ＋ 27 文件**，`verify` 结构偏差 0、尾部残留 0。

| 层 | 状态 |
|---|---|
| L1 UI 主串 `OPENGUI\strings-zh.txt`（916 行） | ✅ 778 译 / 766 含汉字 |
| L2–L6 根级四件套 | ✅ **11 efile 全套**（+ **KAISER 10-08**）；欠账：ROI 仅 `names/nations`。⚠️ 文件名词形有两种：多数 efile 是 `names.txt`，**`ATOMIC`/`LXF`/`SON` 是 `NamesEx.txt`**（10-09 核实 ATOMIC 四件套齐全、行对齐） |
| 根级 `efile.txt`（机制 A，原文零改动） | 🟡 BASEKORP · COMWW2 已交付；余 ⬜ |
| ⭐ 装备名图标码反查 | ✅ `MECHANICS.md` §23；对余下 14 个 efile 的 `equip.txt`（4 万余行）同样适用 |
| L7 exe 硬编码 | ✅ 地图HUD 49 + 面板 48 + `Main`→主国 |
| L8 位图文字 | ✅ `hex_text`×9（8 重绘，`Clu` 象形跳过）／`mouse_*`×7 |
| L9 `.xscn` | ✅ **11 efile**（含 GCE · KAISER · PzLIGA · **ATOMIC/COMWW2 10-09 rawfix 收口**）；余 10 待 |
| `.ply` 简报（全库 63 有正文） | ✅ 全译毕 |
| `.tmsg` / `.xsch`（原地改，无覆盖层） | ✅ AO / ATOMIC / BASEKORP / **COMWW2（20 个：15 个有正文全译，5 个纯空行不译）**；余 ⬜ |
| ⭐ **`USERSCEN\`（用户场景层，09-30 新发现）** | ✅ **COMWW2** ＋ **GCE** ＋ **KAISER（10-08：31 `.xscn` 95.0% 含汉字 ＋ 31/31 标题 ＋ 22 `.ply` ＋ 9 `.txt` 100%）**；余 **PzLIGA 150** 个 `.xscn` ＋ 149 `.ply` ＋ 2 `.txt` ⬜（见 §七.13） |
| 场景 `.txt` 散文 | ✅ **10 efile 100%**（含 COMWW2 · GCE · **KAISER 2203/2203** · **PzLIGA 378/378**） |
| 译名库 A 类 | ✅ 280 行 |

**B5 COMWW2（主体已收官，余 .tmsg / 位图）**
- 根级四件套 ✅ **2,333 行**（equip 1,239 / names 990 / nations 34 / strings 70）；保留原文 2,869 行＝donor 证据 ＋ 型号/舰名/舰级 ＋ **待考 27**（`_todo_uncertain.txt`，词义未明但**类别已由图标反查定出**，分析 `TODO-UNCERTAIN.md`）＋ 注释 49
- `efile.txt` ✅（197 B，6 行，三重对拍，原文 md5 未变）
- `.xscn` ✅ **98.0%**（17,678/18,030 含汉字；唯一非中文 9,066→**282**，全为口径保留）；映射表 `comww2-xscn-map.tsv` **8,802 条**，配对 17,267 改动 **0 错位**
- `.txt` ✅ **1,032/1,032 = 100.0%**（09-30 收官）：label 227 rep ✅ ＋ **prose 671 rep ✅**（`prose-zh.tsv` 903 条 / 输出汉字 70,063）+ **同组 134 个重复文件按 md5 铺满**（`propagate_dup_txt.py`）＋ prose 内 12 处漏译番号行行级订正（`fix_scenario_lines.py`）
- **下一步**：① `.tmsg` ✅ 09-30 完成（15 个有正文）→ ② `L8` 位图 ✅ 已重绘（efile 自有 `hex_text.png` 3105 B，原件 1880 B；无自有 `mouse_*` ⇒ 走根级已汉化版）→ ③ `.front`(199，纯二进制 4 个非零字节无文本) / `.xcam`(10，场景文件名引用) / `.doc`(1，Word 版战役说明) → ④ **`USERSCEN\` 未纳入任何统计**：2 `.xscn` + 2 `.ply` + 2 readme `.txt` 全英文（见 §七.13）→ ⑤ label 保留集 **43 条明摆着的英文编制名**待一批清（详见 §七.12）
- ✅ **COMWW2 遗留（10-08 发现、10-09 修复）**：`.xscn` 内 **298 个唯一匈牙利地名的 cp1252 残槽**已全部补译
  （`Szigetszentmiklós`→西盖特圣米克洛什 等）⇒ 全库**首个全层收官 efile**（`.xscn`＋根级四件套＋`.txt`＋`.ply`＋`.tmsg`＋位图＋`efile.txt`＋`USERSCEN` 全部落地）。

**B6 GCE（10-08 全层收官：`.xscn` ＋ 根级四件套 ＋ 场景 `.txt` ＋ `USERSCEN` ＋ `efile.txt` ＋ 位图判性；细节见 `memory\2026-10-08.md`）**
- 题材＝**西班牙内战（1936–39）＋意大利 CTV**，原文西语；GCE = Guerra Civil Española。
- `.xscn` ✅ **3385/3834 = 88.3%**，**疑似漏译 0**，结构偏差 0，尾部残留 0，标题 34/34 中文；
  余 449 条（30 种）**全部口径保留**（`FARE`/`CNT/FAI`/`PNV` 等政治组织 ＋ 罗马数字方括号代号 ＋ `[T.O.C.E.]`/`L1`/`K/88`）。
- 映射表 `work\gce\gce-xscn-map.tsv` **1675 条**（词典档 948 ＋ 人工 727）；工具 `fix_gce_parts.py` `merge_gce_parts.py` `normalize_gce_map.py` `gce-xscn-rawfix.tsv`。
- ⚠️ 三类已修问题（各有出处）：
  1. **守卫规则互斥**：`merge_gce_parts.py` 原「方括号全 ASCII ⇒ 必须保留」与 POLICY 六「方括号地名/人名**要译**」互斥 ⇒ **6 份合格稿全被误杀、一条未合并**。已收窄为「**仅纯罗马数字**必须保留」＋「不得引入全角标点」。
  2. **`[CEM]` 译错**：donor（BASEKORP）作「东方集团军群」。**证据**＝CEM = `Cuerpo de Ejército Marroquí`（1937-11-11 组建、雅古埃指挥、隶北方集团军、参战特鲁埃尔/阿拉贡/埃布罗），中文通行译 **摩洛哥军**。已改 `[摩洛哥军]`/`[摩洛哥军司令部]`。⚠️ **BASEKORP 带同一错误，未动，待批**。
  3. donor 把罗马数字方括号改写为阿拉伯数字（`[XVIII]`→`[18]`，13 条）；`[1Agrp.]`→「集团军群」违 POLICY 三；`[Ejercito (的) Asturias]` 是 donor「(的)」硬插产物。全部归一。
- ⚠️ **09-30 那批 GCE 工作从未记入日志**（10:48–10:55 开了头即中断）；本次从备份重建 `.xscn` 而非信任旧写入。
- **根级四件套 ✅ 10-08 完成**：`TEXT-ZH\{equip,names,nations,strings_efile}.txt`
  - equip 5001 行（含汉字 **4715/5000**）· names 992（**992/992 = 100%**）· nations 41（32）· strings_efile 155（119）
  - 全部：无 BOM / CRLF / **行数与原文逐一对齐** / **原文 md5 4/4 未变**
  - 工具 `make_gce_root.py`（从 COMWW2 版派生 + **西语变音符折写** `gbk_safe()` + 人工表保空白）· `make_gce_root_manual.py` → `root-manual.tsv` **552 条**
  - ⚠️ 两个新坑已记：① **词级替换会误伤**（把 POLICY §五 明列必须保留的 `FlaK` 译成「高射炮」、把舰级 `Clase General Mola` 译成「Clase 将军 Mola」）⇒ 逐条钉死；② **donor「恒等保留」通道吞普通名词**（`Motoristas` `Ertzaintza` `Auto` `Bicicletta` `Carriaggi*` 被当口径继承）⇒ 已补译
- **场景 `.txt` ✅ 10-08 完成**：144 文件 / 941 非空行，含汉字 **932/941 = 99.0%**；行数全对齐、无 BOM、换行沿用原文、原文 mtime 仍 2018。
  - ⭐ **本层口径（用户裁定）**：GCE 简报是「西语段 + 其英译段」双段结构，**全库仅 GCE 有（110 个文件）**、8 个已交付 efile 均无先例 ⇒ **两段都译成中文**
  - 填译来源：`.xscn` 表 318 ＋ 人工 530 ＋ 译名库 92（**全部 941 行零遗漏**）；工具 `gen_txt_zh.py` `txt_workbench.py` `split_txt_miss.py` `merge_txt_parts.py` `normalize_txt_zh.py` `TXT-POLICY.md`
  - ⚠️ 三个新坑（详见当日日志）：① COMWW2 的 `is_label_file` 判据**不可照搬**（以 `[.!?,;]` 判句读，而西语番号 `Div.`/`Bda.` 自带句点 ⇒ 206 行标签清单被判成散文）⇒ 改为「一视同仁 ＋ `.xscn` 表承担标签层」；② `KEEP_PAT` 的 `^\[[^\]]*\]?$` **过宽**，把方括号包裹的散文当代号保留 ⇒ 收紧为「括号内容不含小写字母才算代号」；③ **敬称/引号跨源漂移**（译名库用「你」、子代理用「您」）⇒ `register_fixup` 统一，但**豁免 `.xscn` 表来源的行**（跨层一致优先：`[Your Army]`→`[你的军队]` 不能改）
- **USERSCEN ✅ 10-08 完成**：`.xscn` 1741 条 / 含汉字 **1636 = 94.0%**（余 105 处全为口径保留：`FARE` `PNV` `[XIV]` `L1` `J/88` `[N]` 与未知缩写 `Dest. Celere`）；标题 **14/14**；`.ply` 10 ＋ `.txt` 5 全部落 `TEXT-ZH\USERSCEN\`（276 非空行 / 99.3% 含汉字）。
  - 工具**增量扩展** `work\userscen\userscen_tool.py`：新增 `strings` 导出＋ `apply --strings-map`（原地回写串区）；标题比对改为 strip 比对并**沿用原文首尾空白**（`madrid_36` 标题尾带空格）。COMWW2 回归通过。
  - ⚠️ 新踩坑：**标题槽本就在 `slots_of` 里**，串区回写会顺手把标题一起译掉 ⇒ 原计划的标题表一半成了重复；另 3 个含 `á/í` 的标题又是 **cp1252 假汉字陷阱**（`decode` 判「已中文」跳过）⇒ 只能走标题机制补译。
- **位图 ✅ 判性**：`OPENGUI\{buttons18,buttons_dlgs,unitleader}.png` 均为**纯图标无文字**（军衔符号/按钮图标/将领徽章）⇒ 无需译。
- **`efile.txt` ✅ 交付**（机制 A）：根级只有 `efile.xml`（无 `.txt`），照 BASEKORP 先例写 `TEXT-ZH\efile.txt`（298 B / 9 行 / CRLF / 无 BOM）；`<title>`→`GCE 西班牙内战装备文件`，`<description>`→`涵盖 1936 至 1939 年期间的西班牙内战装备文件。`，`version`/`author`×3/`url` 原样。原文 0 改动。

⚠️ **排期**：按 `docs\24` 优先级（B4→B5→B6 GCE→B7 KAISER→…），**不被问题密度误导**；每批开工先**全 efile 量测**。
⚠️ **两种「假已改」不算进度**：① `EFILE_LXF` 426 安装戳、`BASEKORP` 8 官方自带；② 映射表 `src==dst` 恒等映射。⇒ **判进度必须直接读文件审计**。
⚠️ **cp1252 假汉字骗校验**：裸 `decode('gbk')` 把 cp1252 高字节解成假汉字。可靠判据＝GB2312 字节范围 ＋ 逐 efile 实证黑名单（`progress.py --dump-fake`）。

**B7 KAISER（10-08 全层收官 ⇒ 已达「完成」判据；细节见 `memory\2026-10-08.md`）**
- 题材＝**一战多国**（德/奥匈/俄/波/捷/匈/土/芬/爱沙尼亚/拉脱维亚/立陶宛/罗/塞/保/希/意/西/葡/法/英/日…），1850–1926。
- **全库最大单批**：`.xscn` **588 文件 / 唯一 31,117** · 场景 `.txt` **2203 个（含 **57 个 `.TXT`** 大写）/ 1.81M 字符**
  · `USERSCEN` 31＋22＋9 · `.tmsg` 38 / `.xsch` 13 / `.xcam` 36 / `.ply` 6。
- ✅ **备份** `backup\ORIGINAL-EFILE_KAISER\`（2956 文件 / md5 差异 0）。⚠️ Git Bash 通配**区分大小写**，`cp *.txt` 会漏 `.TXT`。
- ✅ **根级四件套**（`TEXT-ZH\{equip,names,nations,strings_efile}.txt`）：equip **2886/5286** · **names 2697/2697 = 100%**
  · nations 90/97 · strings_efile 119/155。无 BOM / 全 CRLF / 行对齐 / 节头 10/10 一致 / 原文 md5 未变。
- ⚠️ **`.ply`（1 个有正文）＋ 1 个场景 `.txt` 已于 09-24 完成**（`backup\ply-all-before\`、`backup\scenario-txt-zh-before\`），**不必重做**。
- ⚠️ 四条新坑（详见日志）：① tokenizer 须含重音字母（否则 `Portée`→`Port`→误译「港口」）；
  ② 型号标记行须**整行保留**（GCE 实证 115 行改动 0）；③ 含介词的单位名**整行进人工表**（半译比不译差）；
  ④ `zh_tight()` 收紧「汉字 空格 汉字」。
- **`.xscn` ✅ 88.4%（10-08 四批收官）**：588 文件 / 49,148 槽 → **43,449 = 88.40% 已中文化**，结构偏差 0、尾部残留 0；
  标题 587/588（余 1 为舰名 `Guerrero` 按口径保留）；**疑似漏译 204 = 0.42% ≤ 0.5% ⇒ 判据达标**。
  - 四批：① 规则引擎+词表（结构 18,272）→ ② **地名 6,139**（16 子代理）→ ③ **人名 184**（2 子代理）→
    ④ **编制番号 610**（4 子代理）。优先级 人工 > 地名 > 人名 > 编制 > dict > glossary > 结构。
  - 余 204 槽 / 132 种**全为舰名/型号/纯代号**（`CSS/SMS/S.M.` 舰名、`BP #N`、齐柏林 `LZ30+L37` 等）＝口径保留。
  - ⚠️ 两个坑：① `verify` 报「含汉字 2516」是 **cp1252 假汉字**（开工实为 **0%**）；
    ② `export`/`apply` 都走 `decode()`（先试 GBK）会漏掉那 2,516 条 ⇒ 自写 `export_xscn_uniq.py`（按 cp1252 读）＋ `apply`/`rawfix` 两步。
  - ⚠️ **人名要译**（我一度在 PLACE-POLICY 误写「保留」，与全库既有口径冲突——OLGWW2 `赫尔曼·盖尔将军`、GCE `佩德罗·鲁维奥营` 都译人名）。
- **场景 `.txt` ✅ 10-08 完成**：2,203 文件（含 57 个大写 `.TXT`）/ 12,338 非空行，含汉字 **98.62%**；
  唯一行 7,549 → 人工 6,426（16 子代理散文 + 1 子代理编制代号 293）＋ `.xscn` 表 1,331 ＋ 译名库 60；
  **2203/2203 = 100.0% 文件判据达标**。工具 `gen_txt_zh.py`（GCE 版派生）＋ `txt-zh.tsv`(6,426) ＋ `TXT-POLICY.md`。
- **USERSCEN ✅ 10-08 完成**：`.xscn` 4,083 条 / 含汉字 **95.0%**（余 191 种全为代号/舰名）；标题 **31/31**；
  `.ply` 22 ＋ `.txt` 9 全落 `TEXT-ZH\USERSCEN\`（221 非空行 / **100%** 含汉字）。
  工具 `userscen-all.tsv`(28,451) ＋ `gen_userscen_text.py`（GCE 版派生，改 strip 查键保空白）＋ `userscen-zh.tsv`(1,285) ＋ `userscen-text.tsv`(163)。
- **`.tmsg` ✅ 38（2 空文件跳过）/ `.xsch` ✅ 13 文件 56 处 / `.xcam` ✅ 36 判性（纯文件名引用无文本）**。
  工具 `work\tmsg\tmsg.py` / `work\xsch\xsch.py` ＋ `kaiser-tmsg-map.tsv`(36) ＋ `kaiser-xsch-map.tsv`(56) ＋ `tmsg-xsch-zh.tsv`(142)。
- **位图 ✅ 判性**：efile 自有 `OPENGUI\{hex_text,mouse_build}.png` 已于 09-22/23 重绘为中文（其余 menu_*/dlg_*/hex_layers* 为引擎标准图无文字）。
- **`efile.txt` ✅ 交付**（机制 A）：`TEXT-ZH\efile.txt` 290 B / 7 行 CRLF / 无 BOM；`<title>`→`凯撒将军 II`，
  `<description>`→`涵盖 1850 至 1926 年期间的第一次世界大战装备文件。`，version/author/license 原样。原文 0 改动。
- 工具：`work\kaiser\{make_kaiser_root,make_kaiser_root_manual,gen_root_zh,export_xscn_uniq,measure_xscn_cov,gen_xscn_zh,merge_place_parts}.py`
  ＋ `xscn-place.tsv`(6,139) / `xscn-names.tsv`(184) / `xscn-unit.tsv`(610) / `xscn-map.tsv`(27,166) / `root-words.tsv`(1156) / `root-manual.tsv`(2355)。

**B8 PzLIGA（10-08/09 达「完成」判据 ⇒ 第 9 个已收官 efile；题材＝德占挪威 1940＋太平洋/中国战场；细节见 `memory\2026-10-08/09.md`）**
- **`.xscn` ✅ 98.6%**（3863/3916 含汉字；**疑似漏译 0**；结构偏差 0；尾部残留 0；标题 58/58 中文）。
  余 53 槽 = 26 种**全部口径保留**（`[12A]`/`[USAEF]`/`[NMD]`/`Pol I-V`/`NKVD`/`K-10`/`362A-C` 等方括号代号与编号）。
- ⭐ **新流程验证**：`apply_master` 程序覆盖 **94.4%**（master 精确 93.2% ＋ 词级 0.5% ＋ 纯代号 0.7%）⇒ **只需 LLM 145 条(5.6%)**，
  且几乎全是舰名/人名/地名（Schlachtschiff/Zerstoerer/Kreuzer…），我直接译 131 ＋ 保留 14 ＋ 补 5 番号。
- **根级三件套 ✅ 10-08 完成**（PzLIGA 无 `strings_efile.txt`）：equip **1869/4639 = 40.3%**（余全为型号口径保留）·
  **names 1271/1271 = 100%**（524 条音译＝3 子代理西文 + 我 131 条日/华/菲/泰/俄）· nations 62/68。
  工具 `work\efile_pzliga\gen_root_zh.py`（KAISER 版派生）+ `root-words.tsv`(~1400) + `root-manual.tsv`(~700)。
- **场景 `.txt` ✅ 10-09 完成**：378 文件 / 8986 非空行 / 唯一 3076，**100.0% 含汉字**（填译＝xscn表 7589 + 人工 618 + 译名库 705，0 miss）。
  人工 303 条＝散文 99（2 子代理）＋ 短串 204（我译）。工具 `work\efile_pzliga\gen_txt_zh.py` + `txt-zh.tsv`(303)。
  ⚠️ 坑：txt-zh.tsv 合并须用**完整 src（含尾空格）**去重，否则尾空格行 miss。
- ⚠️ **新坑：派生生成器 TGT 必须与 `os.listdir` 实际目录名逐字一致**（`EFILE_PzLIGA` 混大小写 vs 写全大写 ⇒ self 被当 donor 自引用）。
- 工具 `work\efile_pzliga\{translate_miss,gen_titles,make_pzliga_root,make_pzliga_txt,translate_short}.py` ＋ `pzliga-xscn-map.tsv`(2545) ＋ `txt-zh.tsv`(303)。
- **余项（附加层）**：`USERSCEN`（150 `.xscn` + 149 `.ply` + 2 `.txt`）→ `.tmsg`/`.xsch`/`.xcam` → 位图 → `efile.txt`。

**B9 ATOMIC ＋ COMWW2 的 cp1252 残槽收口（10-09 ⇒ 全库第 10、11 个已收官 efile；细节见 `memory\2026-10-09.md`）**
- 量测：`work\xscn\list_residual.py`（判据与 `progress.py` 逐字一致，**避开 `export` 的假汉字陷阱**）
  ⇒ `ATOMIC` **761 槽 / 401 唯一**、`COMWW2` **432 槽 / 298 唯一**；另各 **7 个标题**也是 cp1252 原文（旧统计不含标题）。
- 题材：ATOMIC 多国（丹麦/瑞典/挪威/冰岛/德意志/波兰/法兰西/西班牙/土耳其/匈牙利/爱沙尼亚/阿塞拜疆）；
  COMWW2 匈牙利（布达佩斯周边、阿拉德、巴拉顿湖）＋少量瑞典/俄湖泊 ＋ **45 条英文编制名**。
- 既有译法复用 **36 条**（其中 **25 条来自 `work\comww2\label-keep-zh.tsv`** —— 09-30 清了 `.txt` label 层与保留集，
  **但没回填 `.xscn`**，正是 §七.12 提醒过的那一步）；余 **565 条**跨两 efile 合并去重成 **601 条联合表**，
  1 区 38 条部队/杂项**本会话亲译**（POLICY §编制表），527 条地名交 **6 个子代理**（`RESIDUAL-PLACE-POLICY.md`）。
- 严校验 `work\xscn\build_rawfix.py`：行数/TAB/原文列逐行对拍、拉丁只许出自原文、GBK 可编码、`/ [ ] ( )` 结构对拍
  （例外显式登记）、**`dst==src` 的口径保留行必须丢出映射表**（否则 `rawfix` 在乱码串上 `encode('gbk')` 崩批）。
- 复核订正 1 条：`Nektarios`（子代理判为专名照抄 ⇒ 查上下文知其在 `blitz8`/`legion9` 的 g0 地图标签内、四周皆希腊地名，改译「内克塔里奥斯」），
  机制＝`residual-overrides.tsv`（可审计覆盖）。
- 落地后 `progress.py`：`ATOMIC 98.4% / 漏译 5`、`COMWW2 97.2% / 漏译 3` ⇒ **双双达标**；全库 `.xscn` 含汉字 **156,427/298,430 = 52.4%**。
- 🔁 **四连沉淀已跑**：`_xscn_dict` 79,603 · `_root_dict` 13,987 · `_prose_dict` 43,458 · `master-glossary` **124,072 条（src 全唯一，多译法残留 0）**。
  同时修两处工具缺口：`build_{dict,root_dict,prose_dict}.py` 的 `EFS` **补 `EFILE_PzLIGA`**（此前 PzLIGA 成果未沉淀）；
  `build_root_dict.py` 的 `FILES` **补 `NamesEx.txt`**（否则 ATOMIC/LXF/SON 的 4,925 条人名对全丢）。
- ⚠️ 旧记「ATOMIC 缺 `names.txt`」**是误记**：ATOMIC 的人名文件本名 `NamesEx.txt`，`TEXT-ZH\` 四件套齐全且行对齐。

## 二、显示机制（目录矩阵见 `MECHANICS.md`）

1 `STRINGS-XX` 前缀（**按行索引**，22–41 地形名）→ `OPENGUI\strings-zh.txt`
1b `strings_efile.txt` 覆盖层（per-efile，覆盖 exe `[sides]`/`[classes]`）→ `<efile>\TEXT-ZH\`
2/3/4 `TEXT-XX\` ／ `TEXT-XX\SCENARIO\`（**仅 `.txt`/`.ply`**）／ `<efile>\SCENARIO\`（`.xscn`/`.tmsg`/`.xsch` **原地**）
5 PNG atlas `OPENGUI\hex_text.png` / `mouse_*.png`
6 `.xscn` 尾部字符串区（二进制回写）
7 `.ply` 简报正文 → `<efile>\TEXT-ZH\SCENARIO\`
8/9 `.tmsg`（首尾 `\r\n` 定位）／`.xsch`（24B 头＋记录：12B 参数＋104B 槽A＋u16 tail＋槽B）

**`.xscn` 串区**：`cnt==0` 是合法空组，不是结束信号。**判据只能是「解析位置 == 文件长度」**；组内可能有二进制项（占 `u16 len + L` 槽）：跳过登记但**仍推进 off**。

## 三、排查决策树（改了几处都没反应）

1. 全 exe 搜原文 ASCII → 看位置 2. 查 `strings-zh.txt` **行号** 3. 查 efile 目录（**先按目录矩阵确认走哪个目录**）
4. ★ **内存扫描**：命中 ⇒ 内存文本；**0 命中 ⇒ 不是文本，是图形！** 5. exe grep 图形名 → `OPENGUI\*.png`

## 四、关键地址

| FO | VA | 内容 |
|---|---|---|
| `0x5842A0` | `0x9858A0` | 内置 `[terrain]`（21×0x100）✅ |
| `0x5857A0` | `0x986DA0` | 内置 `[sides]` ❌ 英文 |
| `0x5859A0` | `0x986FA0` | 内置 `[classes]`（24）❌ 英文 |
| `0x511180` | `0x911F80` | 地图 HUD 串块 49 ✅（`docs\29`）|
| `0x5139BC` | `0x9147BC` | 单位面板/升级 48 ✅（`docs\28`）|
| `0x513A38` | `0x914838` | `Main`→**主国**（switch @`0x81A5E3`，OTP @`0x914804`）|
| `0x4B1A9A`/`0x4B1C86`/`0x4ECB39` | `0x8B2A9A`/`0x8B2A86`/`0x8ED939` | 三个合法空洞 |
| ⛔ `0x51CB31` | `0x91D931` | **废弃**：落在 PE `LoadConfig` ⇒ ntdll 崩 `0xC0000005` |

段布局：`.text` `0x401000`/`0x400` · `.rdata` `0x878000`/`0x477200` · `.data` `0x971000`/`0x56FA00` · `.rsrc` `0x12AB000`/`0x5BEC00`。
⚠️ **VA↔FO**：`.rdata` `VA=FO+0x400E00`、`.data` `VA=FO+0x401600`。明细 `work\exe\ledger.md`。

## 五、翻译口径

- 装备**型号保留原文**（M4A1、Bf-109G2）；著名装备用通行译名；**军舰舰名/舰级保留原文**。
- 各国原语言兵种/编制/后勤名译中文。**大写缩写保留**：`AT` `FlaK` `BB` `ZOC` `LOS` `LOF` `VH` `AAR` `BV` `U:%d` `pp`。
- **方括号/花括号标记**（`[XIII]` `[DAF]` `{Sab}`）视为符号保留。**括号别名**：有独立通行中文名≠主名 ⇒ 译；否则保留原语言；**严禁**译成与主名相同的重复串。
- **立场原则**：按扮演方视角用其代号与编制名。禁蔑称旧称。日期 `1941年5月14日`；知名将领用通行译名。
- **单位级别**：纯「数字+兵种缩写」位于父位＝**师级**（`N Pz`→第N装甲师）；后接 `R/Bde/Rgt/Bn`＝团/旅级。判据＝番号串顺序 `本单位/上级/再上级`。
- **`.txt` 按阵营用词**：日军 `第N师团`、国军 `国民党军第N师`、苏军 `第N师`；`.xscn` g1 一律 `第N师`（**待统一**）。
- **括号全/半角是分层约定**：场景 `.txt` 用**全角**；`equip.txt`/`.xscn` 用**半角**。
- **场景标题**：`Battle of/at/in X`→`X之战`；`YYYY Battle of X`→`YYYY年X之战`；`Operation X`→`X行动`；`X Tank Battle`→`X坦克战`；名词性 `Manchurian Operation`→`满洲战役`（散文内 `Battle of X` 仍译「战役」）。
- ⚠️ **改专名前必须先查同一 efile 既有对译**（AG 的 `praetor` 既有译法「法官」）。

## 六、脚本（要点）

- ⭐ `work\audit\progress.py`：全库进度实测 → `docs\00` §三（`--dump-fake` 查黑名单）。
- ⭐ **cp1252 残槽批次四件套（10-09 建）**：`list_residual.py`（列残槽，判据同 `progress.py`）→
  `lookup_residual.py`（先查既有译法）→ `union_residual.py`（多 efile 去重分块）→ `build_rawfix.py`
  （严校验 + 按 efile 出 `rawfix --map` 表）；口径 `RESIDUAL-PLACE-POLICY.md`，复核订正 `residual-overrides.tsv`。
  ⚠️ `xscn.py export` **看不到**这类残槽（它走 `decode()`，被假汉字骗过），必须用 `list_residual.py`。
- 辅助：`find_slot.py --efile X --sub 串`（看某串在 `.xscn` 里的同组上下文，判性质用）。
- ⭐ `work\xscn\xscn.py`：`--efile <EF> verify|export|apply --map F|zhfix --sub A B|rawfix`（后四者默认**干跑**，需 `--apply`）。⚠️ `rawfix` 是修「保留原文」cp1252 残留的**唯一**入口。
- ⭐⭐ `work\xscn\build_dict.py`：**跨 efile `.xscn` 词典**（`backup/ORIGINAL-<EF>/SCENARIO/*.xscn` ↔ 交付件，按 (文件,gi,idx) 配对）→ `_xscn_dict.tsv` / `_xscn_conflicts.tsv`。7 efile / 98,053 对 / 唯一 src 47,731 / 冲突 50。§24。
- ⭐ `work\comww2\probe_equip_icons.py <EFILE>`：装备名图标码反查（`--lines A-B`／`--grep 串`／`--todo 文件`）。`equip.xeqp` → 槽 +72/80/88/96 → `OpenIcons.keep` → `OpenIcons.csv`。§23。
- ⭐ `work\basekorp\gen_label_zh.py`（label 层原型）→ `work\comww2\gen_label_zh.py` / `gen_prose_zh.py`（COMWW2 两层生成器，**有任一未覆盖行即拒绝落盘**）。
- ⛔ `work\comww2\audit_map_quality.py` · `audit_pollution.py` · `verify_pollution_hits.py`（§25 污染源）· `work\xscn\audit_number_segments.py` · `fix_number_segments.py`（§26）。
- `work\comww2\`：量测 `measure_comww2.py`/`txt_workbench.py`、覆盖 `measure_xscn_cov.py`、重建 `rebuild_todo.py`、规则引擎 `gen_xscn_batch.py`、复用扫描 `probe_residual_reuse.py`（**B 档必须弃用**）、合成 `gen_residual_comp.py`/`build_xscn_map.py`、根级 `gen_root_zh.py`、元数据 `gen_efile_meta.py`。
- `work\exe\`：补丁脚本（幂等）＋ `exe_zhfix.py`（已汉化串二次修正唯一入口）；台账 `ledger.md`+`holes.tsv`。
- 其他：`work\glossary\` · `work\efile-poc\` · `work\ag-verify\`（PIL 离屏，**不启动游戏**）· `tools\*.ps1` · `work\build-zh.ps1 -Deploy`。

## 七、未解 / 待批

0. **旧账（OLGWW2/OPENPG，均未动）**：E 类标点 126 · `.xscn` g1 师团轴 292 段（是否跟随 `.txt` 阵营用词**待批**）· 真漏译 1,380（`glossary-residual.tsv`）· 实质冲突 1,043 · 112 双语不平行 `.txt` · `.txt` 同源问题（`砥平里→稷洞里` 等）· A 类 160 · ⚠️ **译名库 4,179 条恒等映射须单独一批清理**。
1. 实机核验 ✅ 已过（09-28），无崩溃。清单 `docs\31`；回滚档 `backup\OpenGen.exe.before-*`。
2. OLGWW2 闪屏根因 ✅ 定位（旧空洞占 `LoadConfig`），已迁 `0x4B1A9A`，**待实机确认**。
3. B 类原文 4,433 行（真待办 3,737）：cp1252，游戏内正常、编辑器显假汉字。按 `docs\24` 优先级推进，不从 KAISER 开刀。
4. `EFILE_ROI`：已建 `TEXT-ZH\{names,nations}.txt`+6 场景；`equip.txt`/`strings_efile.txt`/36 场景未汉化。
5. ⚠️ AG 待实机复核：单字母兵种缩写 A→辅助队/C→大队/S→射手/B→弩炮/R→骑兵/P→散兵/SP→斥候/AR→弓箭手/RC→骑兵。
6. `efile.xml` efile 名与描述：机制已定位（exe FO `0x4F6480` 附近，**先 `.txt` 后 `.xml`**），BASEKORP/COMWW2 已用机制 A 交付；余 efile 待批。`.xcam` 战役标题 186 个。
7. ⚠️ `progress.py` `.txt` 判据漏计短标签文件（`zh_score>=3`），已加「`>=2` 且无残留拉丁字母」分支；`kept_style()` 不认 `'Xxx` 昵称前缀与 `U-\d+` 潜艇号。
8. OLGWW2 15 个场景仍用带空格日期（`dak*int` 等）需归一化。
9. 退出确认框改了但引擎没调用；P1–P4 UI 微调**已译未应用**（`work\exe\todo-p*.txt`）。
10. OLGWW2 法军航空编制译法待批：`Aé` 译「第N航空队」还是折写 `Ae`。
11. ✅ 面板「能力 XXX」＝特殊能力代号（`能力`/`无能力`=行 835/836，836–877 是 41 项能力名；`*` 开头行是模板注释、引擎不读）。
12. ⚠️ **COMWW2 label 保留集里 43 条明摆着的英文编制名未译**（09-30 新发现，未修）：
    `label-keep.tsv` ＋ `xscn-uniq-final3.tsv` 的唯一保留集共 **306 条**，其中 **43 条**
    是普通英文编制名／番号（`216th Battery` `2nd Jaeger Batt.` `4th Anti-tank Brig.`
    `19th Aufklarungs Abt.` `244th Sturm.` `13th SP Art. Brig.` `10th Sapernii Brig.`
    `[GK Norw.]` 批 `214 Pi Bn` / `244 (Res) Flk Bn`…），**游戏内仍显示英文**。
    根因＝保留集由「`.xscn` 残留」整批继承，而 `.xscn` 残留混进了**普通英文词**（同 `donor 恒等保留`
    吞普通名词的老毛病）。**建议单列一批清理**（须先查同 efile 既有对译，再回填 `.xscn` 映射表与两张保留集）。
13. ⭐ **`USERSCEN\` 目录从未纳入任何统计（09-30 发现并已量测）**：`progress.py` 只扫
    `SCENARIO\`／`TEXT-ZH\SCENARIO\` ⇒ 各 efile 的用户场景目录全在报表之外。实测（`work\audit\measure_userscen.py`）：

    | efile | `.xscn` | 含拉丁条目 | `.ply` 正文 | `.txt` |
    |---|---:|---:|---:|---:|
    | COMWW2 | 2（**仅标题**） | 0 | 2 / 2,640 字符 | 2 / 239 |
    | GCE | 14 | 1,740 | 10 / 8,304 | 5 / 6,124 |
    | KAISER | 31 | 3,955 | 22 / 24,134 | 9 / 8,326 |
    | PzLIGA | 150 | 19,564 | 149 / 111,244 | 2 / 200 |
    | **合计** | **197** | **25,259** | **183 / 146,322 字符** | **18 / 14,889** |

    ✅ **COMWW2 已清**（09-30，全库首个）：2 个标题（原地改，`write_checked` 对拍只动标题槽）＋
    2 `.ply` ＋ 2 `readme` → `TEXT-ZH\USERSCEN\`。工具 **`work\userscen\userscen_tool.py`**
    （`titles|verify|apply --map`，与 `xscn.py` 同解析器）＋ `deploy_cmww2_userscen.py`。
    ⚠️ 余下 3 个 efile 的 USERSCEN 是**真正的大体量**（PzLIGA 一家 19,564 条 `.xscn` 串 + 111K 字符简报），
    **须单列排期**，不能混进各 efile 的「收官」判据里。
14. `readme.doc`（COMWW2 `SCENARIO\`，45KB OLE2 Word）＝ 战役说明文档，**玩家可见但非引擎渲染**；
    已抽取可读文本（Barbarossa v1.1 / 作者 / 地图清单 / 链接），**待批是否译**。
15. ✅ **COMWW2 label 保留集 44 条英文编制名已清**（09-30，见 §七.12 原条目）：整行精确替换
    （15 文件 / 34 行）＋ `xscn-uniq-final3.tsv` 剔除 44 键；对照表 `work\comww2\label-keep-zh.tsv`；
    剩余英文整行 69 行/28 种**全是纯代号**（`SSPol` `SSLAH` `4GDNO` `KievFD` `LLv.24` `FNAF`…）＝ 口径保留。

## 八、硬纪律（详情 `MECHANICS.md`）

1. **出稿 GBK(936)、无 BOM**；**换行沿用原文**（COMWW2 有 516 纯 CRLF ＋ **52 纯 LF** ＋ 464 空壳）。`UI_Lang` 必须 `strings-zh`（写 `zh` 静默回退英文）。
2. ⭐ **字体必须 `simhei.ttf`，禁用 `deng.ttf`**：DengXian 12px 拉丁字形溢出 advance ⇒ 重叠（`Main`→`Nlain`）。见 `docs\27`。
3. **绝不覆盖改原文**；**备份与覆盖分两条独立命令**；**先重建到临时 → 回读校验 → 才写正式**。
4. **含中文的脚本/数据文件必须显式确认 BOM**；`.ps1` 存 BOM 或纯 ASCII，数据文件一律**无 BOM**（BOM 会吞掉 TSV 首条）。
5. **需要截图时必须停下**，明确告知看哪一屏，由用户手动截取；**严禁自行启动/点击游戏**。
6. **优先级铁律**：词典（已交付件实证）> 归一化 > 人工批次（只填空缺，不得覆盖既有）。
