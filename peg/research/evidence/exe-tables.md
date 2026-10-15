# PeG030.exe 内置字符串表（落档）

> 全部为 **`char[N]` 定长字段数组**，实测**步长 20 字节（0x14）**。位于 `.data`（VA `0x48E000`，FO `0x8B800`，`VA = FO + 0x402800`）。
> 这些表**不在** GUI 文本文件里，是 exe 硬编码 —— 与 OpenPG 的 `[sides]`/`[classes]` 内置表同构。
> 复算：`work\peg\analyze_pe.py` ＋ 下方 dump 命令（见 §六）。

---

## 一、⚠️ 工程约束：字段宽 20 字节

定长字段 ⇒ **文本最长 19 字节（含结尾 NUL 共 20）**。
⇒ **中文化时每条不得超过 9 个汉字**（GBK 2 字节/字：9×2 + 1 = 19）。

| 原文 | 字节 | 中文示例 | 占用 | 余量 |
|---|---:|---|---:|---:|
| `United States` | 13 | 美国 | 4 | 充裕 |
| `United Kingdom` | 14 | 英国 | 4 | 充裕 |
| `Battle Cruiser` | 14 | 战列巡洋舰 | 10 | ✅ 恰好 |
| `Air Defense` | 11 | 防空 | 4 | 充裕 |
| `Coastal Naval` | 13 | 近岸海军 | 8 | ✅ |
| `Combat Engineer` | 15 | 战斗工兵 | 8 | ✅ |

⇒ 该约束**不构成障碍**（这些名词的中文都短于英文），但必须在写 patch 时逐条核长，**超出即覆盖下一字段**。

---

## 二、阵营 / 国家槽表 ★（研究观察 O1 核心）

**VA `0x492FEC` ~ `0x493168`｜20 条 × 20 B｜FO `0x907EC` ~ `0x90968`**

| # | VA | 原文 |
|---:|---|---|
| 0 | `0x492FEC` | United States |
| 1 | `0x493000` | Russia |
| 2 | `0x493014` | China |
| 3 | `0x493028` | Vietnam |
| 4 | `0x49303C` | North Korea |
| 5 | `0x493050` | South Korea |
| 6 | `0x493064` | Thailand |
| 7 | `0x493078` | Germany |
| 8 | `0x49308C` | United Kingdom |
| 9 | `0x4930A0` | France |
| 10 | `0x4930B4` | Japan |
| 11 | `0x4930C8` | Singapore |
| 12 | `0x4930DC` | Indonesia |
| 13 | `0x4930F0` | Australia |
| 14 | `0x493104` | Mongolia |
| 15 | `0x493118` | Taiwan |
| 16 | `0x49312C` | Ukraine |
| 17 | `0x493140` | Kazakhstan |
| 18 | `0x493154` | Malaysia |
| 19 | `0x493168` | United Nations |

> **研究注记**：`Gui030.txt` 行 1–20 与上表**逐条同序**，即 GUI 文本**覆盖** exe 内置表。
> 而 `GUI98.TXT` / `GUISA.txt` / `GUISP.TXT` 的**同一槽位**被改写成 `Islamic Coalition` /
> `E. Euro-Bloc: Rom/Czech/Hun/Ukr` / `SE Asia: Sing/Indo/Aus/Thai/Mal` 等 ⇒ **槽位是可换壳的阵营模板**，
> 不是固定国别表。逐行对照见 `evidence/gui-languages.tsv`。

---

## 三、兵种（Unit Class）表

**VA `0x492C2C` ~ `0x492DBC`｜21 条 × 20 B**

| # | 原文 | # | 原文 |
|---:|---|---:|---|
| 0 | Infantry | 11 | Helicopter |
| 1 | Tank | 12 | Airtrans |
| 2 | Recon | 13 | U-Boat |
| 3 | Antitank | 14 | Destroyer |
| 4 | **Flak** | 15 | Battleship |
| 5 | Fort | 16 | Carrier |
| 6 | Truck | 17 | Sea Trans |
| 7 | Artillery | 18 | Battle Cruiser |
| 8 | Air Defense | 19 | Cruiser |
| 9 | Fighter | 20 | Light Cruiser |
| 10 | Tac Bomber | | |

> 注：`Flak` 与 OpenPG 本工作区 POLICY §5「`FlaK` 等大写缩写保留」一致，可沿用既有口径。

---

## 四、其余定长表

| 表 | VA 起 | 条数 | 内容 |
|---|---|---:|---|
| 附属编制标签 | `0x492B48` | 10 | None · Cav · Combat Eng. · Air Defense · Bridge Eng. · Attack Heli · Antitank · CSU · FIST · MUNITION |
| 目标类型 | `0x492DD8` | 4 | Soft · Hard · Air · Sea |
| 防御/反潜类型 | `0x492E30` | 3 | Ground Def · Air Def · Close/ASW |
| 运输方式 | `0x492E70` | 4 | No Trans · Naval · Air Mobile · Airborne |
| 作战域 | `0x492EC8` | 2 | Surface · Air |
| **移动类型** | `0x492EF8` | 11 | Track · Half Track · Wheeled · Leg · Gun · Air · Deep Naval · Coastal Naval · All Terrain · Amphibious · Submerged |
| 态势 | `0x493180` | 2 | Defensive · Offensive |
| 天气 | `0x4931B0` | 4 | Fair · Cloudy · Rain · Snow |

**另（位于 `.rdata`，非 20 B 定长）**：月份名 `January`…`December`，FO `0x8B47C` ~ `0x8B500`。

**对话框标题**：内嵌于 `RT_DIALOG` 资源（`Enter number` / `Hex Properties` / `Choose Tile Id` / `Select Countries` / `Create Army` /
`Select Terrain` / `Choose Transport` / `Choose Scenario Screen` / `Load/Save` / `Dialog to define labels I want for Resources` 等 21 个）。

---

## 五、汉化处置建议

| 表 | 是否必须改 exe | 理由 |
|---|---|---|
| 国家槽表 | **否**（优先） | GUI 文本按行覆盖；仅在 GUI 未覆盖到的界面（若有）才需改 exe |
| 兵种表 | **否**（优先） | 同上；`strings_efile` 类覆盖层机制在 OpenPG 已验证可行 |
| 移动类型 / 天气 / 态势 | **待实机确认** | 界面可见性强，但 GUI 是否有对应行需实测 |
| 对话框标题 | **是** | 唯一确定必须改资源的一处（数量少） |

⚠️ 改 exe 内置表时：**必须保持 20 字节字段宽**，短名用 NUL 补齐，**不得整体压缩表长**（后续字段偏移会串位）。

---

## 六、复算命令

```bash
cd D:/DSH/军事游戏汉化
PY=C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe
$PY - <<'EOF'
import re
d=open(r'D:\Program Files\PeG\PeG030.exe','rb').read()
FO0,VA0=0x8b800,0x48e000
for m in re.finditer(rb'[\x20-\x7e]{2,26}\x00', d[0x90300:0x90a00]):
    fo=0x90300+m.start()
    print('FO %#08x  VA %#08x  %r'%(fo, fo-FO0+VA0, m.group()[:-1].decode('latin-1')))
EOF
```
