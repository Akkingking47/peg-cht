# OpenGeneral 原文编码（cp1250）与「假汉字」吞串修复

> 对象：`D:\OpenGeneral`（OpenGen 25.02.26.0）· 参照：`D:\OpenPG2`（OpenGen 26.03.30.0，已汉化主线）
> 起因：`docs\75` §六 待查 5「变音符折写」——查 GUS 根级 `equip.txt` 的变音符密度时，
> 发现 `PZL.50a Jastrz¹b` 按 cp1252 解出是乱码，按 **cp1250** 解出才是正确的 `Jastrząb`。
> 顺着这条线查出**三个真实缺陷**，且其中一个会让约 2,600 条波兰语字符串被**静默判为「保留原文」**。

## 〇 一句话结论

`D:\OpenGeneral` 的原文**不是 cp1252**（项目 `docs\23` 的既有假定），而是 **cp1250**；
而 `xscn.py` 的 `decode()` 又**先试 GBK**，把大量波兰/西文串吞成了假汉字。两处一起修，
GUS 的程序覆盖率由 **53.4% → 46.8%**（**降了**，见 §五：旧数字是被假汉字虚高的），
而 `D:\OpenPG2` 的 21 个 efile **逐项数字完全不变**。

## 一 三个缺陷

| # | 位置 | 症状 | 性质 |
|---|---|---|---|
| 1 | `work\xscn\xscn.py` 的 `decode()` | 先试 `ENC_OUT`(gbk)，只要解出 CJK 就判「已汉化」 | 对**从未汉化**的 root 会把源文本吞成假汉字 |
| 2 | `work\xscn\apply_master.py:171` | 取串写死 `.decode("cp1252", "replace")`，**绕过 `decode()`** | 编码探测对它无效；`--enc-in` 形同虚设 |
| 3 | `D:\DSH\_probe_og_coverage.py:78` 等量测脚本 | 同一处写死 cp1252 | 量出来的覆盖率不可信 |

### 缺陷 1 的实测量级（`D:\DSH\_probe_gbk_swallow.py`）

| efile | 串总数 | 含高位字节 | 其中被 GBK+CJK 吞掉 |
|---|---:|---:|---:|
| `EFILE_GUS` | 69,732 | 2,963 (4.25%) | **2,636（89%）** |
| `EFILE_ALBERICH` | 324 | 19 (5.86%) | **16（84%）** |

吞掉的样例（左＝真实文本，右＝被吞后的假汉字）：

```
GUS      p³k. Gustlik              ->  p砶. Gustlik
GUS      Mielecki Pu³k Lotniczy    ->  Mielecki Pu砶 Lotniczy
GUS      W³adze Cywilne m. Wilno   ->  W砤dze Cywilne m. Wilno
ALBERICH San Martín del Tesorillo  ->  San Mart韓 del Tesorillo
ALBERICH Legión Espanola           ->  Legi髇 Espanola
```

**为什么危害大**：这些假汉字串既不在 master 里、`TOK` 正则也切不出正常词元
（`³`=U+00B3 不在 `\u00c0-\u024f` 内），于是被 `apply_master.py` 归入
「纯代号（程序已定＝保留原文）」——**翻译流程会静默跳过它们，成品里留下乱码**。

## 二 修复设计

### 2.1 `xscn.py`

新增两个模块级开关与配套函数：

```python
ENC_IN = "cp1252"
ENC_OUT = "gbk"
SRC_FIRST = False          # True = 源文本不是 GBK ⇒ decode() 跳过 GBK 探测

def set_src_first(on): ...
def set_enc_in(name): ...  # 不传/传 auto 时按探测
SUSPECT_CP1252 = "\u00b9\u00b2\u00b3\u00bc\u00bd\u00be"   # ¹²³¼½¾
def pick_enc_from_bytes(raw, text_file=True): ...   # cp1252/cp1250 取可疑字符更少者，打平退回 cp1252
def guess_enc_in(path): ...                          # 单文本文件版
```

`decode()` 改为：

```python
def decode(raw):
    if SRC_FIRST:
        return ENC_IN, raw.decode(ENC_IN, "replace")
    try:
        s = raw.decode(ENC_OUT)
        if any("\u4e00" <= c <= "\u9fff" for c in s):
            return ENC_OUT, s
    except Exception:
        pass
    return ENC_IN, raw.decode(ENC_IN, "replace")
```

CLI 新增 `--enc-in cp1250|cp1252|utf-8|auto`、`--src-first` / `--gbk-first`。

### 2.2 `apply_master.py`

新增 `detect_src_first(root)`：**该 root 下有任意 efile 带 `TEXT-ZH\` ⇒ False**（保留 GBK 优先）；
整个 root 都没有 ⇒ True。这样「是否已汉化」这个判据从「猜某条串」上升为「看目录事实」。

实测：`D:\OpenPG2` 21 个 efile 中 18 个有 `TEXT-ZH` ⇒ `False`；`D:\OpenGeneral` 5 个全无 ⇒ `True`。

新增 `detect_enc(root, ef, sample=30)`，两条关键设计（都是被实测逼出来的）：

1. **只取串负载**（`parse` + `raw_at`），不读整文件。第一版读整文件，被 `.xscn` 二进制段的
   任意字节淹没，把高位字节密度为 0 的 `GUS_Zx` / `GUS_Wx` / PG2 的 `AG` 全误判成 cp1250。
2. **跳过会走 `ENC_OUT` 分支的串**（与 `decode()` 同判据）。已汉化 efile 因此样本为空、
   恒返回 cp1252 ⇒ `ENC_IN` 对它们是空操作，PG2 行为可证明不变。

`main()` 里把取串一行由写死 cp1252 改为 `xscn.ENC_IN`：

```python
s = xscn.raw_at(data, off, L).decode(xscn.ENC_IN, "replace").strip()
```

刻意**不走 `xscn.decode()`**：那条路会先试 GBK，而这里是「取源文本」不是「判是否已汉化」。
当 `ENC_IN == "cp1252"`（PG2 全域）时与原写法**逐字符等价**。

## 三 验证

### 3.1 单元

```
set_enc_in("cp1250") 后  b"Pu\xb3k Lotniczy"  :  'Pu³k' -> 'Pułk'   ✅
guess_enc_in(r"D:\OpenGeneral\EFILE_GUS\equip.txt")  = cp1250      ✅
```

### 3.2 PG2 回归（必须完全不变）

| 检查 | 结果 |
|---|---|
| 21 个 efile 的 `detect_enc` | **全部 cp1252**，无非 cp1252 项 ✅ |
| `detect_src_first(D:\OpenPG2)` | `False` ✅ |
| 独立探针全量：`AG` 0.2% / `OLGWW2` 58.7% / `NOKORP` 63.5% / **合计 31.9%** | 与修复前逐项一致 ✅ |

### 3.3 双工具交叉

`docs\73` 用的量测脚本（写死 cp1252）已重写为 `D:\DSH\_probe_og_cov2.py`
（ASCII-only 输出，见 §六）。两条独立路径对比：

| efile | `apply_master.py` | `_probe_og_cov2.py` |
|---|---:|---:|
| EFILE_GUS | 46.7% | 46.8% |
| GUS_PeG | 34.8% | 34.9% |
| GUS_Wx | 33.0% | 33.1% |
| GUS_Zx | 72.1% | 72.1% |
| ALBERICH | 78.1% | 78.1% |

差额来自词级匹配计数（`word` 26 条），属正常。

## 四 更正后的数字（取代 `docs\73` §一 原表）

`detect_enc` 结果：**GUS = cp1250**（高位字节密度 5.30%），
ALBERICH / GUS_Zx / GUS_PeG / GUS_Wx = cp1252（ALBERICH 的 `.xscn` 实为西班牙语，
`Alcalá Galiano` / `José Luis Díez` / `Chamberí - Madrid`，两种表解码相同）。

| efile | `detect_enc` | 唯一串 | 槽位 | master 精确 | 纯代号 | **程序覆盖** | 需人工/LLM |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `EFILE_ALBERICH` | cp1252 | 320 | 324 | 250 | 0 | **78.1%** | 70 |
| `EFILE_GUS` | **cp1250** | 27,367 | 61,975 | 9,550 | 3,243 | **46.8%** | 14,548 |
| `EFILE_GUS_PeG` | cp1252 | 6,526 | 14,259 | 2,260 | 13 | **34.9%** | 4,246 |
| `EFILE_GUS_Wx` | cp1252 | 39,654 | 76,082 | 5,737 | 7,334 | **33.1%** | 26,512 |
| `EFILE_GUS_Zx` | cp1252 | 1,818 | 2,968 | 748 | 563 | **72.1%** | 507 |
| **合计** | | **75,685** | **155,608** | 18,545 | 11,153 | **39.4%** | **45,883** |

与 `docs\73` 原表对比：

| | 原（`docs\73`） | 更正后 |
|---|---:|---:|
| 唯一串 | 81,629 | **75,685** |
| 需人工/LLM | 46,842 | **45,883** |
| 程序覆盖 | 42.6% | **39.4%** |

**覆盖率的「下降」不是退步**：旧数字用 cp1252 把波兰语解成乱码，那些乱码串因为切不出词元
而被归进「纯代号＝保留原文」，**虚增了程序覆盖率**。更正后它们如实落进「需人工/LLM」。
即：真实待译量比原估**略多**（GUS 一侧 15,507 → 14,548 看着少，是因为唯一串本身从
33,311 降到 27,367——乱码变体合并了）。

> ⚠️ `docs\73` 原表的槽位分母（GUS 69,732）出自早期的 `_probe_og_measure.py`，
> 与 `apply_master.py` 的迭代口径不同。现统一以 `apply_master.py` 为准。
> 已核：`slots_of` 比 `items` 只多出「标题槽」（GUS 906 个），不构成量级差。

## 五 对阶段计划的影响

1. **阶段 1 根级**：`apply_master_root.py` 已先期修好（`SUSPECT` 判据 + `read_lines(..., enc="auto")`），
   GUS / ALBERICH 选出 cp1250 并解出正确的 `Jastrząb` / `Hrušínski` / `@ciezkie czołgi`；
   `OLGWW2\equip.txt` 仍 cp1252（`3.7cm FlaK Möbelwagen`）。**它另需补 UTF-8 优先分支**：
   `OLGWW2\names.txt` 真值是 UTF-8，被误判 cp1250（`Barrón` → `BarrĂłn`）——已在 `pick_enc_from_bytes`
   里补上，但 `apply_master_root.py` 自己那份 `_pick_enc` 待同步。
2. **阶段 2+ `.xscn`**：`apply_master.py` 现在会自动选表，**不必再手工传 `--enc-in`**。
3. `docs\23` 通篇假定「原文侧应为 cp1252」，**未考虑 cp1250** ⇒ 该文档需加一条修订说明；
   但其 A 类（UTF-8 混入）/B 类（假汉字）判据仍适用，只是「哪种表」这一层要按 root 区分。
4. **`work\audit\progress.py` 不是「写死 cp1252 会漏报」的 bug，而是 PG2 专属**（已核实）：
   它 `L26 GAME = r"D:\OpenPG2"`，且判据是 PG2 形状的（`FAKE_HAN` 黑名单扫
   `backup\ORIGINAL-*` + 未开始 efile；还带 BASEKORP「空壳」等 PG2 科目）。
   ⇒ **不要**把它参数化硬套到 `D:\OpenGeneral`。
   **需要的是一个 OpenGeneral 侧独立进度审计器**，且它的假汉字黑名单必须从
   **cp1250/cp1252 原文侧**重建（不能沿用 PG2 的 `backup\ORIGINAL-*` 树）。
   时机：阶段 2（`EFILE_GUS_Zx`）产出第一份成品后，否则无对象可审。

5. `apply_master_root.py` 的 `_pick_enc` **已含 UTF-8 优先分支**（早前那轮已修，本文件
   §五.1 的原判断作废）。实测 6 例全部正确：

   | 文件 | 判定 | 样例 |
   |---|---|---|
   | `D:\OpenPG2\EFILE_OLGWW2\names.txt` | **utf-8** | `Barrón` |
   | `D:\OpenPG2\EFILE_OLGWW2\equip.txt` | cp1252 | `3.7cm FlaK Möbelwagen` |
   | `D:\OpenPG2\EFILE_KAISER\names.txt` | cp1252 | `Stefánik` |
   | `D:\OpenGeneral\EFILE_GUS\equip.txt` | **cp1250** | `PZL.50a Jastrząb` |
   | `D:\OpenGeneral\EFILE_ALBERICH\equip.txt` | **cp1250** | `PZL.50a Jastrząb` |
   | `D:\OpenGeneral\EFILE_GUS\names.txt` | **cp1250** | `Hrušínski` |

   限界：UTF-8 判定是**整文件**粒度，对「同文件内混用 cp1252 与 UTF-8」会退到
   cp1250/cp1252（该情形由 `work\glossary\restore_orig_encoding.py` 逐行处理，不在本路径）。

## 六 踩坑记录

| 坑 | 现象 | 记法 |
|---|---|---|
| PowerShell 5.1 读写 UTF-8 | `(Get-Content -Raw f) -replace ... \| Set-Content f` 把含中文的 `.py` 双重编码成不可读文件（`璇嶅簱`），且**逆变换也救不回被截断的多字节** | 改写含 CJK 的文件**只用 `edit`/`write` 工具**，或 `[IO.File]::ReadAllText/WriteAllBytes` 显式 `UTF8`。与 `docs\70` 记的「`.ps1` 必须带 UTF-8 BOM」同源 |
| 量测脚本先于工具链修好 | 脚本自己写死 cp1252，于是「修好工具链」跑出来的数字仍不对 | 量测脚本**必须复用**被量测工具的函数（`detect_enc` / `detect_src_first`），不得平行实现 |
| 整文件打分 | 用整个 `.xscn` 的字节分布判编码，被二进制段淹没 | 只对**语义相关的字节区间**打分 |

## 七 证据方法

| 结论 | 方法 | 产物 |
|---|---|---|
| GUS/ALBERICH 是 cp1250 | `_probe_encin.py` 单元测试 + `pick_enc_from_bytes` 打分 | 本文件 §三.1 |
| 2,636 / 16 条被 GBK 吞 | `_probe_gbk_swallow.py`（`parse`+`raw_at`，复刻 `decode()` 判据） | §一 表 |
| 各 efile 高位字节密度 | `_probe_encin.py`（各扫 40 个 `.xscn`） | §四 表 |
| PG2 未受影响 | 21 个 efile `detect_enc` 全表 + 独立探针全量对照 | §三.2 |
| 双工具一致 | `_probe_og_cov2.py` 与 `apply_master.py` 并跑 | §三.3 |
| 槽位口径差 | `_probe_slotcount.py`（`items` vs `slots_of`） | §四 注 |
