# 待考清单（COMWW2 `equip.txt`）— 2026-09-29 第三轮：**图标证据**

> 判据演进：① **邻域上下文** → ② **音系特征** → ③ ⭐ **图标码反查**（本轮新增，见下）。
> 原则不变：**能确证才落笔；不能确证就登记**，绝不猜测原词。
> 机读名单：同目录 `_todo_uncertain.txt`。

## 一、⭐ 本轮新增的判据：图标码反查（可机械化）

链路：`equip.txt` 行号 → `equip.xeqp` 记录 → 图标码 → **`OpenIcons.keep`（假码→真码）** → `OpenIcons.csv` 描述。

| 环节 | 事实 |
|---|---|
| `equip.xeqp` | 4 字节头（`u16[0]=2`、`u16[1]=记录数 4054`）+ **4054 × 120 字节**记录 |
| 记录内图标槽 | 相对偏移 **72/80/88/96**，各为「5 字符码 + NUL 填充」的 8 字节槽（4 槽多为同值） |
| 行↔记录 | `equip.txt` **L1 ＝ 版本头**（`VERSIONOpen Composite v1.02F`，非装备）、末行空 ⇒ 行 N ↔ 记录 N−1 |
| `OpenIcons.csv` | 17,908 条，列 `IconID;Description;Color;IconClass;Nation;Chassis;IconStyle` |
| `OpenIcons.keep` | 2,723 条 **`假码;真码` 回落表**（表头 `*Fake;Real`）⇒ 本 efile 大量引用「假码」，须先经它还原 |

⚠️ 两个坑：
1. **图标是「最接近可用」而非精确对应** ⇒ 图标只能给**类别**，给不出词义；
2. **必须先过 `OpenIcons.keep`**，否则一半码在 `OpenIcons.csv` 里查不到（会误判成「悬空引用」）。

### 本轮据此**确证并译出** 3 条

| 原文 | 行 | 证据 | 译 |
|---|---|---|---|
| `Shin Hoto` | L652 | 图标 `FZ150` = **Type 97-Kai Shinhoto Chi-Ha**；同文件另有独立 `T97 Chi-Ha`（`FZ149`）⇒ 即「新砲塔型」 | **新炮塔** |
| `Hara Kamei` | L3186/3393 | KAISER 自带对照表 `README\_UNIT_NAME_TRANSLATIONS.txt` L226 明写 **`Hara Kamei: Field Command`**；图标 `JK331` = Sanbo Honbu (HQ Command Infantry x3)；同簇为多语「指挥部」（`Feld Befehl`/`Polevoye Upravlenie`/`Ordine del Campo`…） | **战地指挥部** |
| `Jiaotache` | L2437 | 图标 `JKS93` = **Jiaotache (Bicycle x3)**、Nation = WW2 China Nationalist ⇒ 脚踏车 | **自行车** |

## 二、仍待考 27 条 —— 词义未明，但**类别已定**（本轮新增）

| 原文 | 行 | 假码→真码 | 真实图标 · 类别 |
|---|---|---|---|
| `Awai Bahitsu` | L2165 / L2972 | H14→H14 | Povozka (Horse x2) · **畜力运输车** |
| `Bao Mai` | L2124 | H14 | 同上 · **畜力运输车** |
| `Guang Chema` | L2439 | H14 | 同上 · **畜力运输车** |
| `Biao Chema` | L775 | H11 | Tachanka · **马拉机枪车** |
| `Kabu Bahitsu` | L1714 / L2970 | H11 | Tachanka · **马拉机枪车** |
| `Saai pan Mai` | L747 | H11 | Tachanka · **马拉机枪车** |
| `Gao Chema` | L2436 | KKT1→JCN64 | 3.3in QF 18pdr Horse Artillery · **马拉炮兵** |
| `Maak ho Mai` | L2122 | KKT1→JCN64 | 同上 · **马拉炮兵** |
| `Soukou Bahitsu` | L2971 | KKT1→JCN64 | 同上 · **马拉炮兵** |
| `Tahun` | L3016 | AU13 | 105 mm Berittene Artillerie · **马拉炮兵** |
| `Mai` | L2450 | TD82→LV485 | Kihei (Horse Transport / Light Cavalry x2) · **骑兵／马匹运输** |
| `Raba` | L937 | JK337 | Mule Pack (x1) · **驮骡** |
| `Jijun` | L940 | TDF28→BN145 | Cavalleggeri (Light Cavalry x2) · **轻骑兵** |
| `Kuaiban` | L1833 | TDF29→LV468 | Esploratore a Cavallo (Scout Cavalry x1) · **侦察骑兵** |
| `Keishu` | L1684 | WDF77→JKT18 | Hohei 1931 (Infantry x3) jungle · **日军步兵** |
| `Shiro Rokoku` | L1683 | H41P→JKT18 | 同上 · **日军步兵** |
| `Ko-on Pon` | L1685 | SBC22→JKS95 | Zong Canmou Bu 1945 (HQ Command Infantry) · **指挥部步兵** |
| `Pak Naa-wik` | L2646 | JK86 | Naval Infantry (x3) · **海军陆战队** |
| `Raat Jot-mat` | L2645 | SKR18→JCI90 | Grenadery 1916 (Elite Infantry) · **精锐步兵** |
| `Ozzowiachimzen` | L3488 | JK460→JCP51 | Strelkovy 1943 (Infantry) · **步兵** |
| `T-Truppen` | L2214 | H33→JCO41 | Feld Infanterie 1942 (Infantry) · **步兵** |
| `Paan Pon` | L2476 | JK44→JCI52 | Saperno-mostovoi (Bridging Infantry) · **架桥工兵** |
| `Ossa` | L2561 | WD63 | Motorcyclists (x3) · **摩托车兵** |
| `Dowa` | L1315 / L1690 | MM65B | Crossley IGA1 AC / Type 87 Armored Car · **装甲车** |
| `Ko-Hi` | L2925 | TDZ45 | Praga T-9 · **履带牵引车** |
| `Voro` | L2106 | TDZ44 | Praga T-9 · **履带牵引车** |
| `Shi-Ke` | L2924 | PA316 | SdKfz 6 Zugkraftwagen 5t · **半履带牵引车** |

## 三、为什么仍不落笔

类别 ≠ 词义。按「**错译比保留原文更有害**」（`Ta-haan` 教训：曾误译「登陆」，实为 ทหาร＝士兵）：
`Keishu`／`Shiro Rokoku`／`Ko-on Pon`／`Dowa` 等**词义无原文可反查**，据类别硬译会把
「某具体单位名」压成「泛类别词」（如把 `Keishu` 写成「步兵」），等于**制造原文里没有的信息** ⇒ 登记不填。

### 三条待验证的**假说**（有旁证，但未达落笔标准）

| 假说 | 旁证 | 反证/弱点 |
|---|---|---|
| `Ko-on Pon` ＝ 泰语 **กองพล**(kong phon)＝师/兵团 | 本 efile 有 Thailand ＋成体系的泰语转写（`Pon Maa`=พลม้า 骑兵、`Ta-haan`=ทหาร 士兵、`Dtam-ruat`=ตำรวจ 警察、`Sa-mak`=สมัคร 志愿、`Jakrayaan`=จักรยาน 自行车、`Reua`=เรือ 舰艇、`Pak Naa-wik`=นาวิก 海军）；本词 `Ko-on`↔กอง、`Pon`↔พล 拆分整齐 | 图标为 **HQ 指挥部步兵**（`JKS95`），与「师」不合 |
| `Shiro Rokoku` ＝ 日语「白露国」→ 白俄（白系ロシア人）部队 | `露国`＝俄罗斯（日语）；20 世纪 30–40 年代满洲国／关东军确有白俄部队 | 图标仅给「日军步兵」泛类；`白露` 无日文常用先例 |
| `Mai` ＝ 马（与 `Maa` 同为 ม้า 的另一种转写） | 邻域 L2446–2463 全为各国「马」词（`Chevaux`/`Pferde`/`Caballos`/`Konie`/`Hevonen`/`Paarden`…）；图标 `LV485` 明写 "Horse Transport" | 本 efile 已用 `Maa` 表示 ม้า，`Mai` 可能另有其词 |

## 四、⚠️ 已确认**不是**日式古国名 / 舰级名（本轮结论）

用户假说「这批会不会是日本古国名或日本海军舰级名」——**逐条证否**：

1. **本文件的舰级段是独立的一簇**：L1931–1946 `Kagero`/`Nagara`/`Mutuski`/`Yugumo`/`Akagi`/`Unryu`/`Zuiho`/`Taiyo`/`Shokaku`/**`Ise Class`**/`Furutaka`/`Tone`/`Mogami`/**`Nagato`**/`Kongo`/**`Fuso`**。
   ⇒ 古国名**确实**存在（`Ise`=伊勢、`Nagato`=長門、`Fuso`=扶桑 皆为令制国名，是IJN战列舰命名法），但**只出现在这一簇**，且均形如 `X Class` 或单名。
2. 六个目标里**只有 `Mutuski` 落在该簇**（L1933，紧邻 `Kagero`/`Nagara`）⇒ 它是 **IJN 驱逐舰「睦月」**（罗马字应为 Mutsuki，缺 `s`）。
   驱逐舰用**月名**而非国名 ⇒ 属**舰名**，按「军舰舰名／舰级保留原文」口径**保留原文**（当前处理正确）。
3. 其余五条全在**陆上单位批**（L1676–1691：`Afghan`/`Moroccan`/`Egyptian`/`Kouhei`（工兵）/`Sento Kouhei`（战斗工兵）/`Keisatsu`（警察）/`Kihei`（骑兵）/`Sukauto`（侦察）/`Osaka`/`Brazilian EF`/`T97 Chi-Ha`…），
   图标类别分别为**日军步兵／指挥部步兵／装甲车／畜力车／马拉炮兵／坦克** ⇒ **不是舰级名**。
4. 附带确证：`Osaka` 亦非地名泛称，而是 **Type 92 HoKoKu-Go 装甲车**（图标 `WDG06`）；`SNLF` → `WDG05 Type 93 Sumida`（上海海军特别陆战队确用过九三式装甲车，图标分配合理）。

## 五、已移出/已定案的条目（累计）

- **口径保留**：`Mutuski`（睦月，舰名）· `Ratnakosindra`（泰舰名）
- **已译出**：`Bahitsu`→马匹 · `Dtam-ruat`→警察 · `Jakrayaan`→自行车 · `Reua`→舰艇 · `Pon Maa`→骑兵 ·
  `Sa-mak`→志愿兵 · `Hadimernok`→军事工程师 · `Oszver`→骡 · `Viuchny`→驮畜 · `Drushinizi`→义勇兵 ·
  **`Shin Hoto`→新炮塔 · `Hara Kamei`→战地指挥部 · `Jiaotache`→自行车**（本轮 3 条）
