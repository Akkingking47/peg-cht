# OpenGen efile 语言机制与汉化要点

> 本文由实测 + 反汇编确认，纠正了此前的一个错误假设，务必作为后续汉化其他 efile 的依据。

---

## 一、结论速查

| 机制 | 作用范围 | 是否生效 | 汉化方式 |
|---|---|---|---|
| `Settings.cfg` 的 `UI_Lang` | 决定语言代码 | — | `UI_Lang=strings-zh` |
| **`STRINGS-XX`**（文件名前缀） | UI 界面文本 | ✅ 生效 | 放 `<游戏根>\OPENGUI\strings-zh.txt` |
| **`TEXT-XX\`（efile 根目录）** | `equip.txt` / `names.txt` / `nations.txt` / `strings_efile.txt` / `fronts.txt` | ✅ **生效** | 放 `<efile>\TEXT-ZH\<同名文件>` |
| **`TEXT-XX\SCENARIO\`** | 场景文本 `.txt` | ❌ **不生效** | 游戏根本不查这个路径 |
| **覆盖 `<efile>\SCENARIO\` 原文** | 场景文本 `.txt` | ✅ 生效 | 直接覆盖原文件（**必须先备份**） |

---

## 二、关键证据

### 2.1 `TEXT-XX\SCENARIO\` 不生效（反汇编）

读取战役描述的函数（`0x352A00`–`0x352D00`）内，路径拼装用的字符串是：

```
0x352AF8  push "\SCENARIO\"
0x352B1D  push "%s%s"
0x352C58  push "%s%s.txt"
0x352B6C  push "Campaign file not found ..."     ← 读失败时的提示
```

**整个函数区间内不存在 `TEXT-` 字样**（已程序化确认）。

### 2.2 `TEXT-XX\` 根目录生效（实测）

进入**装备浏览器**，装备类别名显示为中文（`步兵`/`坦克`/`侦察`…），
这些来自 `<efile>\TEXT-ZH\strings_efile.txt` 的 `[classes]` 段 → **证明根文件走 `TEXT-ZH`**。

### 2.3 官方语言包的结构佐证

| 语言包 | `SCENARIO\` | 根文件 |
|---|---|---|
| `EFILE_AG\TEXT-DE`（官方德语） | 284 个 .txt | `equip.txt`/`fronts.txt`/`nations.txt`/`strings_efile.txt` |
| `EFILE_GCE\TEXT-ES`（官方西语） | — | `nations.txt`/`strings_efile.txt` |
| `EFILE_OLGWW2\TEXT-ES`（官方西语） | 143 个 .txt | 无 |

官方包**同时**放根文件和 `SCENARIO\` —— 说明作者的标准做法是这样，
但 `SCENARIO\` 那一份**实际从未被游戏读取**（官方语言包可能同样有这个盲区）。

---

## 三、语言代码解析

- `Settings.cfg` → `UI_Lang=strings-zh`
- 语言代码 = `zh`
- `TEXT-` + 代码 → 目录名 `TEXT-ZH`（Windows 大小写不敏感）
- `STRINGS-` + 代码 → 文件名前缀 `strings-zh`

`efile.txt` 里**没有语言字段**，语言完全由 `Settings.cfg` 决定。

---

## 四、⚠️ 操作纪律（血泪教训）

**2026-09-20 事故**：部署场景文本时，一条命令里同时做「备份 + 覆盖」，
命令含 PowerShell 语法错误（`"$D:\OpenPG2\..."` 被当成变量名）→
**PowerShell 遇到语法错误会拒绝执行整个脚本**，于是备份没跑、覆盖却在下一条命令里执行了，
导致 `EFILE_OLGWW2`（807 个）与 `EFILE_OPENPG`（190 个）的 `SCENARIO\*.txt` 原始英文被覆盖且无备份。

**救回方式**：从官网重新下载官方 efile 包：

- `https://www.open-general.com/install/efiles_r/EFILE_OLGWW2.zip`
- `https://www.open-general.com/install/efiles_r/EFILE_OPENPG.zip`
- 存档为 `backup\ORIGINAL-EFILE_OLGWW2\`、`backup\ORIGINAL-EFILE_OPENPG\`

**今后必须遵守**：

1. **备份与覆盖放两条独立命令**，先确认备份成功（列目录 + 校验 MD5）再执行覆盖
2. 改文件前先在**小范围**（1 个文件）验证脚本能跑通
3. 任何批量操作前，先 `-WhatIf` 或预览输出
4. 覆盖后立即抽检：确认目标内容是中文、非目标文件未被触碰

---

## 五、回滚

```powershell
# 场景文本回滚为官方英文
.\tools\restore-scenario.ps1 -WhatIf              # 预览
.\tools\restore-scenario.ps1 -Efile EFILE_OLGWW2
.\tools\restore-scenario.ps1 -Efile all
```

`TEXT-ZH\` 目录直接删除即可移除 efile 级本地化（根文件部分）。

---

## 六、目录清单（当前状态）

```
EFILE_OLGWW2\
  ├─ SCENARIO\*.txt          ← 已覆盖为中文（807 个，生效）
  ├─ TEXT-ZH\
  │    ├─ equip.txt          ← 生效（1417 处）
  │    ├─ names.txt          ← 生效（2232 处）
  │    ├─ nations.txt        ← 生效
  │    ├─ strings_efile.txt  ← 生效
  │    └─ SCENARIO\          ← 不生效（游戏不查），保留作译文存档
  └─ TEXT-ES\                ← 官方西语包

backup\
  ├─ ORIGINAL-EFILE_OLGWW2\  ← 官方整包存档（1199 文件，22.2 MB）
  └─ ORIGINAL-EFILE_OPENPG\  ← 官方整包存档（349 文件，6.3 MB）
```
