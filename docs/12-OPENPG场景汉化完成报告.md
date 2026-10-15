# 12 · `.xscn` 场景地名 —— `EFILE_OPENPG` 全量完成报告

> 承接 `11-xscn场景汉化完成报告.md`（OLGWW2 全量）。本轮完成 **`EFILE_OPENPG` 全部 54 个场景**，
> 至此**主程序自带两个 efile 的场景数据全部中文化**。

---

## 一、成果

| 项 | 数值 |
|---|---|
| 处理文件 | **54 / 54** 个 `.xscn` |
| 字符串条目 | **2,329** 条（100% 覆盖） |
| 唯一原文 | **1,083** 条 |
| ├ 复用 OLGWW2 已完成映射 | 424 处 |
| ├ 复用 PGForever 地图地名表 | 1,775 处 |
| └ 本轮新译 / 修正 | 184 处（56 条唯一原文） |
| 未命中（保留原文） | **0** |
| 实际写入 | **2,329** 处 |

**结构验证 54/54 通过**（独立 Python 解析器，非补丁脚本自校验）：

- 条目数、分组数与 `backup\ORIGINAL-EFILE_OPENPG\SCENARIO\` 官方原始 **零偏差**
- 尾部剩余字节与原始 **零偏差**（无截断、无错位）
- 2,329 条译文 **100% 含 GBK 双字节**（即全部中文化）

抽样：

| 文件 | 标题 | 地名样例 |
|---|---|---|
| `elalamein.xscn` | 阿拉曼 | 托布鲁克 / 比尔哈希姆 / 马特鲁港 / 崎岖沙漠 / 意军营地 / 空地 / 沙地 |
| `d-day.xscn` | 诺曼底登陆 | 瑟堡 / 巴约 / 卡昂 / 法莱斯 / 阿夫朗什 / 莫尔坦 / 圣梅尔埃格利斯 / 树篱地 |
| `berlin(east).xscn` | 东柏林 | 但泽 / 柯尼斯堡 / 施特拉尔松德 / 维斯瓦河 / 易北河 |

## 二、⚠️ 与 OLGWW2 的结构差异（重要）

| | OLGWW2 | **OPENPG** |
|---|---|---|
| 组 0 | 地图地名 / 通行说明 | 地图地名 / 通行说明 |
| 组 1+ | **部队番号编成**（13,000+ 条） | **不存在**（0 条） |
| 条目分布 | 组 0 + 组 1 混合 | **全部 2,329 条集中在组 0** |

⇒ OPENPG 是纯地名场景，**没有番号模板**，因此不需要 `POLICY.md` 里的编制名对照表与「第 N」序号规则。
`xscn-build-map.ps1` 的 `Norm()` 规范化对本轮**无实际作用**（无番号可规范）。

## 三、复用结构（本轮最大的成本节约）

按优先级：**本轮 overrides > OLGWW2 映射 > PGForever 地图地名表 > 保留原文**

1. **OLGWW2 已完成映射**（`work\xscn-all-map.tsv`，10,381 条原文）→ 命中 **136 条唯一原文 / 424 处**
2. **PGForever 地图地名表**（`work\xscn\pgf-lookup.tsv`，4,559 条）→ 额外命中 **906 条唯一原文 / 1,775 处**

两者合计覆盖 1,042 / 1,083 条唯一原文 = **96.2%**，只需新译 41 条。

> 复用维持了「同一地名在 OpenGen 与 PGForever 里译法一致」，是本项目口径统一的既定做法
> （OLGWW2 那轮同样复用了 PGForever 旧表 409 条）。

### ★ 发现：PGForever 表有 14 条译名被长度限制截断

PGForever 的 `MAPNAMES.STR` 是 **20 字节定长槽（实际可用 ≤19 字节 / 6 汉字）**，
溢出时会「降级为纯音译」——**丢掉了原文里的通名或后半截地名**。抽样发现 14 条：

| 原文 | PGForever 表（截断） | 本轮 OPENPG 用（完整） |
|---|---|---|
| `Aix-en-Provence` | 艾克斯 | 普罗旺斯地区艾克斯 |
| `St. Mere Eglise` | 圣梅尔 | 圣梅尔埃格利斯 |
| `St. Vaast-la-Haugue` | 圣瓦斯特 | 圣瓦斯特拉乌格 |
| `St. Sauveur-le-V.` | 圣索沃尔 | 圣索沃尔勒维孔特 |
| `Bosanki Petrovac` | 波斯尼亚 | 波斯尼亚彼得罗瓦茨 |
| `Cherkez Kermen` | 切尔克斯 | 切尔克斯克尔曼 |
| `Dmitrovsk-Orlovskiy` | 德米特罗夫 | 德米特罗夫斯克-奥尔洛夫斯基 |
| `Dmitriyev-Lgovskiy` | 德米特里耶夫 | 德米特里耶夫-利戈夫斯基 |
| `Frankfurt an Main` | 美因河法兰克 | 美因河畔法兰克福 |
| `Marche-en-Famenne` | 法梅讷马尔什 | 法梅讷地区马尔什 |
| `Tunbridge Wells` | 坦布里奇 | 坦布里奇韦尔斯 |
| `Turnu Severin` | 塞维林堡 | 图尔努塞维林 |
| `Conde-sur-Noireau` | 诺瓦罗孔代 | 诺瓦罗河畔孔代 |
| `Zekiah Swamp Run` | 泽基亚溪 | 泽基亚沼泽溪 |

`.xscn` 是**变长存储**（u16 长度前缀），不受 19 字节限制，故本轮采用完整译名。

> ⚠️ **由此产生一处口径分叉**：同一地名在 **PGForever**（受 19 字节约束）与 **OpenPG**（无约束）
> 可能显示不同。这是**刻意的**——如需回改 PGForever 侧，属于独立工程操作，需另行确认。

## 四、本轮新建的唯一原文（41 条）

### 战役 / 行动标题（25 条）

| 原文 | 译文 | 说明 |
|---|---|---|
| Finland | 芬兰 | |
| Balkans | 巴尔干 | |
| Barbarossa | 巴巴罗萨 | 行动代号 |
| Anvil | 铁砧 | 行动代号 |
| Cobra | 眼镜蛇 | 行动代号 |
| Husky | 哈士奇 | 行动代号 |
| Market Garden | 市场花园 | 行动代号 |
| D-Day | 诺曼底登陆 | ⚠️ 未直译「D日」，取玩家可读的通行叫法 |
| Berlin (East) / (West) | 东柏林 / 西柏林 | 括号按中文习惯去除 |
| Byelorussia | 白俄罗斯 | |
| Caucasus | 高加索 | |
| Early Moscow | 莫斯科前期 | ⚠️ 歧义项，取「前期」 |
| Moscow 41 | 莫斯科41 | |
| North Africa | 北非 | |
| Low Countries | 低地国家 | |
| Norway / Poland / France / Scotland / Tunisia / Washington | 挪威 / 波兰 / 法国 / 苏格兰 / 突尼斯 / 华盛顿 | |
| Sealion 40 / Sealion43 / Sealion Plus | 海狮40 / 海狮43 / 海狮增强版 | 行动代号 |
| Ski Raiders | 滑雪突击队 | `game101.xscn` 标题 |

### 地图说明 / 地形标注（16 条）

| 原文 | 译文 | 依据 |
|---|---|---|
| BOCAGE / FOREST / FORTIFICATION / MOUNTAIN | 树篱地 / 森林 / 要塞 / 山地 | 与 `strings-zh.txt` 22–41 行地形名表一致 |
| RIVER / ROUGH / SWAMP | 河流 / 崎岖地 / 沼泽 | 同上 |
| SAND | 沙地 | 出现在北非/中东场景，同场景有「崎岖沙漠」「空地」「海洋」 |
| Abandoned Airfield | 废弃机场 | |
| American Camp | 美军营地 | 同场景有「德军营地」「意军营地」 |
| Inlet | 小海湾 | |
| Port / Port Algiers / Port Marseilles | 港口 / 阿尔及尔港 / 马赛港 | 沿用「X港」式（马特鲁港 / 卜雷加港） |
| Steep Hill | 陡坡 | 同场景有「陡崖」 |

> `CLEAR`→空地、`OCEAN`→海洋、`LAKE`→湖 三条由 OLGWW2 映射复用，**未采用** UI 层的
> 「开阔地」等措辞 —— 保持 `.xscn` 层内部口径一致。

## 五、工具与流程

```
1) 导出    tools\xscn-tool.ps1 -Action export -Efile EFILE_OPENPG -Map work\xscn\openpg-orig.tsv
2) 分析    work\xscn\_analyze*-openpg.py（复用命中率 / 截断可疑项 / 语境核对）
3) 建表    work\xscn-openpg\overrides.tsv（56 条：41 新译 + 14 截断修正，优先级最高）
4) 合并    work\xscn-openpg\build-map.py → openpg-map.tsv（5 列，2383 行）
5) 干跑    -DryRun → files=54 written=2329 read-verify-skipped=0
6) 写入    tools\xscn-patch.ps1 -Efile EFILE_OPENPG -Map ... -BackupDir backup\xscn-names-orig-openpg
7) 验证    work\xscn-openpg\verify.py（独立解析器，54/54 结构零偏差）
```

> **本轮未派子代理**：唯一待译仅 41 条（OLGWW2 是 9,826 条），新译由主代理直接完成，
> 开销低于分片 + 校验 + 合并的流程成本。

## 六、本轮踩到的坑

**Write 工具写出的 `.tsv` 带 UTF-8 BOM** → 读取时首个键名变成 `\ufeffAbandoned Airfield`，
自检直接报「原文未在语料中出现」。

⇒ 生成器已改为 **剥 BOM + 用 `utf-8-sig` 容错读取**，并把 overrides.tsv 重写为无 BOM。
（与既有铁律同源：*凡是交给引擎/脚本按字节比对的文件，必须确认它到底有没有 BOM*。）

## 七、回滚

```powershell
# 方式 1：从写入前备份还原单个文件
Copy-Item 'D:\DSH\军事游戏汉化\backup\xscn-names-orig-openpg\<名>.xscn' `
          'D:\OpenPG2\EFILE_OPENPG\SCENARIO\' -Force

# 方式 2：从官方整包还原全部（推荐，293 个齐全）
& 'D:\DSH\军事游戏汉化\tools\xscn-rollback.ps1' `
    -Efile EFILE_OPENPG `
    -Pristine 'D:\DSH\军事游戏汉化\backup\ORIGINAL-EFILE_OPENPG\SCENARIO'
```

> 生效方式：**退出场景重新载入**（或重启游戏）。

## 八、未做

- 其余 19 个 efile（AG / AO / ATOMIC / BASEKORP / COMWW2 / KAISER / LXF / OPENAK / OPENPEG / OoB /
  PzLIGA / SON …）的 `.xscn` 均未做 —— 其 UI 文本同样全英文，需先建 `TEXT-ZH\`。
- ⚠️ 统计时注意「假已改」：`EFILE_LXF` 426 个 `.xscn` 是 **2026-02-20 安装时间戳**、
  `EFILE_BASEKORP` 8 个是 **2026-06-22 官方自带**，**内容仍是英文**。
