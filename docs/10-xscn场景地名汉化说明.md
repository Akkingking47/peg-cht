# 10 · `.xscn` 场景地名/番号汉化说明

> 解决「鼠标移到格子上，顶部中部的名称仍是英文」的问题。
> 例：`Gan River (Only passable with boats) [10 10]`

---

## 一、这行字从哪来（**不是地图图片**）

来自 **场景文件 `.xscn`**（编译后的场景数据），不是 `.map` 地图图片、不是 exe、不是 `strings_efile.txt`。

复现路径：`EFILE_OLGWW2\SCENARIO\RSCHI03.xscn`（南昌之战）。

## 二、`.xscn` 文件结构（已逐字节验证）

```
[场景数据（头部 + 六角格表 …）]
<N:0001>                          ← 场景标记（唯一，全文件只出现 1 次）
13 00 "Battle for Nanchang"       ← 标题：u16 字节长度 + 内容
15 00                             ← 第 1 组：u16 条目数（21）
   04 00 "LAKE"
   09 00 "Gan River"
   24 00 "Gan River (Only passable with boats)"   ← 顶栏显示的就是这一整条
   12 00 "Gan River (Bridge)"
   08 00 "Nanchang" …
68 00                             ← 第 2 组：u16 条目数（104）
   17 00 "11 R/9 Bde/6 Div./[11A]" …              ← 部队番号/编成名
<文件结束>
```

要点：

- 每条都是 **u16 字节长度 + 内容**（**变长**，不是定长槽）
- 第 1 组 = **地图地名/通行说明**；第 2 组 = **部队番号/编成**
- 顶栏那一行 = **一条整串**（`地名 + (括号说明)`）＋ 引擎另拼的 `[x y]` 坐标
- 字符串编码按 `CP_ACP=936` 读取 ⇒ **写 GBK(936)**

## 三、为什么可以放心改长度（**不会溢出**）

| 证据 | 结论 |
|---|---|
| 字符串区**位于文件尾部**，且 **186/187 个文件解析恰好到 EOF**（唯一例外 `jh3ceut.xscn` 尾部多 2 字节，脚本会原样保留） | 改长度只让文件变长/变短，**后面没有数据需要修补** |
| 全 187 个文件里，**指向串区起点的指针 = 0 个** | 引擎是靠扫描 `<N:` 标记定位的，不是靠偏移 |
| 24 个文件存在「数值恰好等于某条串起点」的 u32，但都是 `0x9800`/`0x10000` 这类圆整常量，出现率**低于随机巧合期望** | 噪声，非引用 |
| u16 长度前缀上限 65,535 字节；最长原文才 62 字节 | 余量极大 |

实测中英字节数（GBK）：`Gan River (Only passable with boats)` 36→20、`Battle for Nanchang` 19→8、
`Capture this hex for playing the Greater Europe campaign path!` 62→30。
**91/125 条变短**，仅部队番号类会略增（31 条，平均 +4）。

## 四、规模

| efile | `.xscn` 文件 | 字符串条目 | 唯一串 |
|---|---|---|---|
| **OLGWW2** | 187 | 16,058 | **10,243** |
| **OPENPG** | 54 | 2,329 | **1,053** |

内容类型：普通地名（`To Sint-Niklaas`/`Rupel`/`Salm River`）、带说明的（`(off-map)`/`(I CA)`/
`(Only passable with boats)`/`(Captured)`/`[International Bridge]`，共 2,510 条）、
部队番号编成（2,543 条）、少量游戏提示（`Capture this hex for …`、`AIRFIELD: OUT OF THE MAP LIMITS`）。

## 五、工具 `tools/xscn-tool.ps1`

```powershell
# 体检：逐文件解析，报告条目数 / 是否恰好到 EOF
& '.\tools\xscn-tool.ps1' -Action list -Efile EFILE_OLGWW2

# 导出原文（5 列 TSV：文件 组 索引 原文 原文；标题组号为 -1）
& '.\tools\xscn-tool.ps1' -Action export -Efile EFILE_OLGWW2 -Map work\xscn-export.tsv
& '.\tools\xscn-tool.ps1' -Action export -File RSCHI03.xscn -Map work\xscn-RSCHI03.tsv

# 回写（5 列 TSV：文件 组 索引 期望原文 新译文）
& '.\tools\xscn-tool.ps1' -Action apply -Map work\xscn-RSCHI03-map.tsv            # 干跑
& '.\tools\xscn-tool.ps1' -Action apply -Map work\xscn-RSCHI03-map.tsv -DryRun    # 只预览
```

安全机制（**都是踩过坑之后加的**）：

1. **读校验**：写入前，文件当前文本必须**逐字等于** TSV 第 4 列的「期望原文」，否则该条跳过 ⇒ 幂等、防错位
2. **前缀切片断言**：重建后长度必须 ≥ 前缀长度，否则拒写
3. **写后回读校验**：写完立即重新解析，条目数不符就报错
4. **自动备份**到 `backup\xscn-names-orig\` 并验证存在

## 六、样板场景（已完成）

`EFILE_OLGWW2\SCENARIO\RSCHI03.xscn`（**南昌之战**）：

- 42671 → **42496 字节**，125 条全部替换，读校验 0 跳过
- 回读验证：标题《南昌之战》，**恰好解析到 EOF**
- 地名：湖 / 赣江 / 乐化 / 长埠 / 蛟桥 / **赣江（仅船只可通过）** / 冶楼 / 稻田 / 湾里 / 新建 /
  **赣江（有桥）** / 南昌 / 望城岗 / 罗家集 / 黄溪 / 青云谱 / 生米街 / 莲塘 / 西山 / 澄潭 / 浮山
- 番号（节选）：`第11团/第9旅/第6师/[第11军]`、`第101团/第101旅/第101师/[第11军]`、
  `第118师/[第79军]`、`第9预备师/[第49军]`、`第197师/[第8军]`、`[第9战区司令部]`、
  `第5特别陆战队`、`第12大队`、`独立飞行第17中队`、`[鄱阳湖守备队]`

> 口径说明（**待你确认**）：`Div./Bde./R./Corps` 一律用**中性**的 `师/旅/团/军`，
> 因为同一模板同时用于中日双方；日方专有单位用通行译名（`SNLF`→特别陆战队、`Datai`→大队、
> `Sentai`→战队、`Hiko Chutai`→飞行中队）。若你希望日军部队用「师团/旅团/联队」，
> 需要在译表里逐条区分阵营（同一串如 `106 Div.` 只能选一种）。

## 七、⚠️ 本次两个严重事故与教训（**务必记住**）

### 事故 1：文件被截断成 2042 字节
`BinaryWriter.Write($keep)` 里 `$keep` 是 PowerShell 切片产生的 **`System.Object[]`**，
PowerShell 绑定了错误的重载，**静默只写了 1 个字节** —— 前缀 40,455 字节全丢，`.xscn` 报废。

- **教训**：往 `BinaryWriter` 写数组**必须显式 `[byte[]]` 强转**；空/错长度**不会报错**
- **补救**：立即从 `backup\ORIGINAL-EFILE_OLGWW2\SCENARIO\` 还原（官方整包 187 个 `.xscn` 齐全），MD5 一致
- **防复发**：写入前断言 `outBytes.Length >= 前缀长度`，写入后回读校验

### 事故 2：备份写进了乱码目录（`D:\DSH\鍐涗簨娓告垙姹夊寲`）
脚本 `.ps1` 由 write 工具存为 **UTF-8 无 BOM**，而 PowerShell 5.1 按 **GBK** 解析无 BOM 文件 ⇒
参数默认值里的中文路径 `D:\DSH\军事游戏汉化\…` 变成乱码 ⇒
`New-Item`/`Copy-Item` 在乱码路径下创建了目录树，`Test-Path` 检查的是同一个乱码路径所以**没报错**，
而真正该有备份的目录是空的。

- **教训**：**含中文的 `.ps1` 必须存 UTF-8 with BOM**（或干脆脚本纯 ASCII、中文只走命令行参数）
- 事后已把乱码目录里的原图取回正确位置并删除乱码树

> 这两条已同步进 `08-文本来源排查方法论.md` §七 与项目记忆 `MEMORY.md`。
