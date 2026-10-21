# 阶段 0 · 工具链参数化与 `.xscn` 闭环验证

对象：`D:\OpenGeneral`（OpenGeneral 波兰发行版，OpenGen 25.02.26.0）
试刀 efile：`EFILE_GUS_Zx`
对应计划：`docs\73-OpenGeneral汉化阶段计划.md` §三 阶段 0
日期：2026-10-16

---

## 一 结论

| 项 | 结果 |
|---|---|
| 工具链能否服务 `D:\OpenGeneral` | ✅ 已参数化，**一处未改业务判据** |
| `D:\OpenPG2` 既有流程是否受影响 | ✅ 默认值不变，向后兼容（见 §三） |
| `.xscn` 闭环是否跑通 | ✅ export → prematch → **真写** → verify → 逐槽对拍，**异常 0** |
| 正式游戏目录是否被动过 | ❌ **一个字节都没动**（闭环跑在隔离的 poc 根上） |
| 阶段 0 出口判定 | ✅ 通过 |

试刀量测（与 `_probe_og_coverage.py` 的独立量测完全吻合，互为印证）：

```
[D:\OpenGeneral]
EFILE_GUS_Zx .xscn 唯一串 1818 / 槽 2968
master 精确命中    748 (41.1%)
词级组合命中        0 (0.0%)
纯代号（保留）    563 (31.0%)
=> 程序覆盖 72.1%；需 LLM 的仅 507 条 (27.9%)
```

---

## 二 改动清单（3 处）

### 2.1 `work\xscn\xscn.py` —— 根目录参数化

| 改动 | 前 | 后 |
|---|---|---|
| 根目录 | `ROOT = r"D:/OpenPG2"` | `ROOT = os.environ.get("XSCN_ROOT") or r"D:/OpenPG2"`，并支持 `--root` |
| efile 名 | `norm_efile()` 后直接拼接 | 新增 `resolve_dir()`：按磁盘**真实大小写**解析 |

```python
def resolve_dir(parent, name):
    """按磁盘上的真实大小写解析子目录名；找不到返回 None。"""
    if not os.path.isdir(parent):
        return None
    for d in sorted(os.listdir(parent)):
        if d.upper() == name.upper() and os.path.isdir(os.path.join(parent, d)):
            return d
    return None

class Ctx(object):
    def __init__(self, efile, root=None):
        self.root = os.path.abspath(root or ROOT)
        ef = norm_efile(efile)
        self.efile = resolve_dir(self.root, ef) or ef   # 用磁盘真实大小写
        self.game = os.path.join(self.root, self.efile, "SCENARIO")
        ...
```

`main()` 里 `root = argv[argv.index("--root") + 1] if "--root" in argv else None`，传给 `Ctx`。

### 2.2 `work\xscn\apply_master.py` —— 同上

- `ROOT` 改为环境变量 + `--root`；
- `ef` 由 `a.strip().upper()` 改为 `xscn.norm_efile(a)` 再接 `xscn.resolve_dir(root, ef)`；
- 量测目录 `D = os.path.join(root, ef, "SCENARIO")`（原为 `ROOT`）；
- 输出首行打印 `[root]`，避免在混合工作区里看不出作用对象；
- 用法串补上 `[--root D:\OpenGeneral]`。

### 2.3 新增 `work\xscn\check_loop.py` —— 闭环逐槽复核器

`xscn.py verify` 只给「条目数 / 含汉字数 / 尾部残留」这类**汇总**指标。本器补上**逐槽、逐字节**的强判据，任何 efile 写完都能跑：

1. **结构零偏差**：`slots_of()` 槽位数、组表、尾部残留逐文件比对；
2. **改动落点可控**：所有字节差异必须落在槽内；**串区起始之前的场景数据必须逐字节相同**，且长度相同；
3. **编码正确**：每个新串按 `gbk` 能解码、含汉字、无 `U+FFFD`；
4. **原文未受损**：A/B 两份逐文件比对，未改动槽必须逐字节一致。

用法：`python check_loop.py <POC_ROOT> <BACKUP_SCENARIO> <EFILE>`（异常数即退出码）。

---

## 三 向后兼容论证

`D:\OpenPG2` 的行为**可证明未变**：

- `ROOT` 默认值仍是 `D:/OpenPG2`，环境变量未设时与改动前完全一致；
- `resolve_dir(ROOT, "EFILE_AG")` 在 PG2 下返回目录本身的名字 `EFILE_AG`（全大写），与旧 `norm_efile()` 的 `.upper()` 结果**逐字符相同**；
- `D` 由 `ROOT` 换成 `root`，而 `root` 默认即 `ROOT`。

已实测（一次性烟囱测试）：

| 调用 | 解析出的 efile | `game` 是否存在 |
|---|---|---|
| `Ctx("AG", None)` | `EFILE_AG` | ✅ |
| `Ctx("GUS_Zx", r"D:\OpenGeneral")` | `EFILE_GUS_Zx` | ✅ |
| `Ctx("gus", r"D:\OpenGeneral")` | `EFILE_GUS` | ✅（**不会**误撞 `EFILE_GUS_Wx`） |
| `Ctx("GUS_Wx", r"D:\OpenGeneral")` | `EFILE_GUS_Wx` | ✅ |
| `Ctx("ALBERICH", r"D:\OpenGeneral")` | `EFILE_ALBERICH` | ✅ |

> ⚠️ **踩坑更正**：`docs\73` §六 与早前评估里我把「`--efile` 的 `.upper()` 匹配不到 `EFILE_GUS_Wx`」列为**风险**，这是**想当然**。Windows 文件系统本就不区分大小写，`os.path.join(root, "EFILE_GUS_WX")` 本来就能打开 `EFILE_GUS_Wx` —— 它**不是功能故障**，只是让备份路径 / work 目录 / 日志里出现一个磁盘上不存在的名字，排查时极具误导性。现在归一到真实名，属于**可读性修正**，不是修 bug。

---

## 四 闭环验证（全套证据）

### 4.1 备份（**独立命令**，硬纪律 §2）

```
源 76 个 / 目标 76 个 / 不符 0
清单 -> backup\ORIGINAL-EFILE_GUS_Zx\xscn-manifest.tsv (6463 B)
```

- 目标：`backup\ORIGINAL-EFILE_GUS_Zx\SCENARIO\`，所有 `*.xscn` 逐字节复制 + SHA256 双向核对；
- 清单 TSV（`name / size / sha256`）供后续还原对拍；
- 与 `xscn.py verify` 期望的路径约定 `backup\ORIGINAL-<efile>\SCENARIO` 一致；
- **目的不只是备份，也是阶段 2 的常驻前置件**。

### 4.2 导出与匹配

```
python work\xscn\apply_master.py --root D:\OpenGeneral --efile GUS_Zx --with-words
→ work\efile_gus_zx\prematch-map.tsv（748 条程序已定）
  work\efile_gus_zx\prematch-miss.tsv（1096 条待定）
```

### 4.3 空跑核对改写计划（默认 dry-run，未写盘）

```
词典 748 条；计划改写 951 条 / 文件 28 / 总文件 76
   G06_30.xscn   g-1.0  'Leningrad'   -> '列宁格勒'
   G27_STA00.xscn g0.0  'Liska River' -> '利斯卡河'
   G27_STA00.xscn g0.2  'V.Buzinovka' -> '上布济诺夫卡'
   ...
```

### 4.4 在**隔离 poc 根**上真跑（不动正式目录）

```
D:\DSH\_poc_root\EFILE_GUS_Zx\SCENARIO\   ← 从正式根逐字节复制 76 个 .xscn（不符 0）
python work\xscn\xscn.py --root D:\DSH\_poc_root --efile GUS_Zx apply \
       --map work\efile_gus_zx\prematch-map.tsv --apply
→ 写入完成 28/28        # 全部经 write_checked：写 .new → 回读校验 → 才替换
```

### 4.5 内置 verify（对拍备份）

```
EFILE_GUS_Zx: 备份条目 2968 / 现状条目 2968      ← 槽位数完全一致
   现状含汉字 1003 / 无汉字 1965
   尾部残留分布: [(0, 76)]                      ← 76 个文件尾部残留全为 0（旧坑 1 未复发）
   结构偏差文件: 0
```

### 4.6 `check_loop.py` 逐槽对拍（强判据）

```
文件 76 / 槽 3044 / 改动槽 951 / 未改动槽 2093 / 有改动文件 28
异常 0
```

（`槽 3044 = apply 的 2968 条目 + 76 个标题槽`；`apply_master` 只统计条目，`cmd_apply` 多算标题槽，故 dry-run 的 951 与这里一致。）

### 4.7 体积变化

28 个文件合计 `1,099,502 → 1,100,505` 字节（**+1,003**，最大单文件 +333 B）——与 1,003 条中文（GBK 双字节对 ASCII 单字节）量级相符，**无异常膨胀**。

### 4.8 抽样（原文 cp1252 → 现 GBK）

```
G27_STA00.xscn g0.0 'Liska River' -> '利斯卡河'
G27_STA00.xscn g0.1 "Os'kinsky"   -> '奥西金斯基'
G27_STA00.xscn g0.3 'Kalmykov'    -> '卡尔梅科夫'
G27_STA00.xscn g0.5 'Don River'   -> '顿河'
G27_STA00.xscn g0.7 'Volga'       -> '伏尔加河'
```

### 4.9 清场

`D:\DSH\_poc_root` 已删除（可由 §六 的 2 条命令重建）。**正式游戏目录全程未被写入**。

---

## 五 遗留与下一步

1. **GUS_Zx 还剩 507 条唯一串需人工/LLM**（`prematch-miss.tsv`，另有 563 条纯代号计为保留原文）。
2. **高频单位番号是待定榜的主体**，且现有工具链**原理上无法**自动处理：

   ```
   62 A   x79      95 SD    x34      4 TA    x44
   112 SD x28      8 AA     x20      300 SD  x19      4 Luftfl. x19
   ```

   这些是「第62集团军 / 第95步兵师 / 第4坦克集团军」这类番号缩写。`apply_master.py` 的 `word_ok()` 有**两条硬判据**：`if re.search(r"\d", s): return False`（含数字一律交 LLM）+ 去掉命中 token 后不能有残留 —— 所以词级路径**永远不会**碰它们。**建议阶段 2 增加一条番号规则**（如 `^\d+ (A|TA|SD|AA|Gds|Luftfl\.)$` → `第N…`），否则这 507 条里的大头（合计 200+ 频次）每次都要 LLM 重做。
3. `check_loop.py` 已固化，后续每个 efile 写完都跑。
4. **下一步：阶段 1（GUS 家族根级，一套覆盖 4 个 efile）**，见 `docs\73` §三。

---

## 六 复现命令

```powershell
# 0) 备份（独立命令，先跑）
$src='D:\OpenGeneral\EFILE_GUS_Zx\SCENARIO'; $dst='D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_GUS_Zx\SCENARIO'
New-Item -ItemType Directory -Path $dst -Force | Out-Null
Copy-Item "$src\*.xscn" $dst

# 1) 程序优先匹配
C:\Python314\python.exe "D:\DSH\军事游戏汉化\work\xscn\apply_master.py" `
  --root D:\OpenGeneral --efile GUS_Zx --with-words

# 2) 隔离 poc 根（不动正式目录）
$poc='D:\DSH\_poc_root\EFILE_GUS_Zx\SCENARIO'
New-Item -ItemType Directory -Path $poc -Force | Out-Null
Copy-Item "$src\*.xscn" $poc

# 3) 空跑 → 真写
$X='D:\DSH\军事游戏汉化\work\xscn\xscn.py'; $M='D:\DSH\军事游戏汉化\work\efile_gus_zx\prematch-map.tsv'
C:\Python314\python.exe $X --root D:\DSH\_poc_root --efile GUS_Zx apply --map $M            # dry-run
C:\Python314\python.exe $X --root D:\DSH\_poc_root --efile GUS_Zx apply --map $M --apply    # 写入

# 4) 两重校验
C:\Python314\python.exe $X --root D:\DSH\_poc_root --efile GUS_Zx verify
C:\Python314\python.exe "D:\DSH\军事游戏汉化\work\xscn\check_loop.py" `
  D:\DSH\_poc_root "$dst" EFILE_GUS_Zx
```

> 环境：`C:\Python314\python.exe`（3.14.7）。跑前设 `$env:PYTHONIOENCODING='utf-8'; $env:PYTHONUTF8='1'`。
> `apply` / `apply_master` 的 `--root` 亦可免传，改用环境变量 `XSCN_ROOT=D:\OpenGeneral`。
