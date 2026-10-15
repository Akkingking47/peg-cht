# 35 · COMWW2 `prose` 层收官 → `.txt` 层 100%（2026-09-30）

> 承接 `docs\34`（label 层收官 + COMWW2 开工量测）。本轮把 COMWW2 场景 `.txt` 从 **22.0% 拉到 100.0%**，
> 使 COMWW2 达到「已收官」判据（`.xscn` 漏译 ≤0.5% 且 `.txt` >99% 且 `.ply` 全译）。
> 全部数字为**直读文件实测**（不看映射表），复核脚本见 §六。

---

## 一、结论

| 项 | 起点 | 终点 |
|---|---:|---:|
| `.txt` 覆盖 | 227 / 1,032（22.0%） | **1,032 / 1,032（100.0%）** |
| `prose` 待译唯一叙事段 | 220 | **0** |
| `prose-zh.tsv` 条目 | 683 | **903** |
| 输出汉字（label / prose / 同组） | — | **65,381 / 69,981 / 13,176 = 148,538** |
| 结构异常（BOM / 换行 / 行数） | — | **0** |
| 原文组内不一致 | — | **0 / 898 组** |

**COMWW2 ⇒ 第 7 个「已收官」efile**（AG · AO · BASEKORP · NASHORNPBEM · OLGWW2 · OPENPG · **COMWW2**）。
全库 `.txt` 合计 **5,305 → 6,110 / 14,967（35.4% → 40.8%）**。

---

## 二、为什么之前停在 22%：三个叠加原因

1. **未合并的产出**：09-29 已译的 495 条里有 50 条（b10）**没并进块目录**，`merge_prose_block.py` 从未对 b10 跑过。
2. **剩下的 220 条没人译**：其余分块只到 `prose-dst-b10.txt`，`_prose_authority.txt` 的 715 条里
   序号 496–715 仍为英文。
3. **同组重复文件从来没被铺过**（最隐蔽）：两个生成器只写 `rep-list.tsv` 的**代表文件** 898 个，
   而 `SCENARIO\` 有 **1,032** 个 `.txt` ⇒ 即使 rep 全译，报表也永远到不了 100%。

> ⚠️ 第 3 条同时说明：09-29 记的「label 227 ✅ 已部署」是**按 rep 计**，
> 实际有 86 个内容组的 134 个同组成员从未生成。**判进度必须全目录核对，不能只看代表清单。**

---

## 三、执行过程（可复现）

| # | 步骤 | 工具 | 结果 |
|---:|---|---|---|
| 1 | 合并遗漏的 b10 | `merge_prose_block.py --block b10 --from 446 --to 495` | 50 条，抽查 4 条逐字对上 |
| 2 | 导出剩余清单 | `export_prose_dst.py` | 220 条 / 47,308 字符 |
| 3 | 切 10 份 | `split_prose_rest.py --parts 10` | 每份 22 条（4.3–5.7K 字符） |
| 4 | 10 个子代理并行翻译 | `PROSE-POLICY.md` 为文体口径 | 220/220 全部通过自检 |
| 5 | 校验后合并 | `merge_prose_rest.py --apply` | 10 个 `prose-zh-blocks/rest-NN.tsv`；真源覆盖 715/715 |
| 6 | 术语一致性订正 | `fix_prose_rest.py` | 5 类不一致共 40+ 行 |
| 7 | 合成 | `build_prose_zh.py` | 903 条（块内为准，打印 17 条冲突） |
| 8 | 部署 | `gen_prose_zh.py` | 671 rep，69,952 汉字 |
| 9 | 铺同组重复文件 | `propagate_dup_txt.py` | +134 文件 ⇒ 1,032 |
| 10 | 番号行订正 | `fix_scenario_lines.py` | 12 处 |

---

## 四、术语口径（全部以**已交付件**为据）

| 项 | 定译 | 依据 |
|---|---|---|
| `VH` / `VHs` | **胜利点** | COMWW2 label 层 48 文件已用；`VH` 在该层零残留 |
| `DH` / `DHs` | 部署格 | 同上（本 efile 仅 4 行用到） |
| `Decisive Victory` / `Victory` / `Marginal Victory` / `Loss` | **决定性胜利 / 胜利 / 险胜 / 失败** | ⭐ **本 efile** `TEXT-ZH\strings_efile.txt [results]` 逐行实测 |
| `BV` / `DV` / `TV` / `MV`（原文混用，Panzer General 旧称） | 一律收敛到上面 4 级 | 同上；收敛后 `辉煌胜利`/`战术胜利`/`勉强胜利` **清零** |
| `Herr General` / `Herr Feldmarschall` | 将军阁下 / 元帅阁下 | 已交付件 943 处 |
| `Comrade X` | X同志 | 苏方一律「同志」 |
| `Lysjanka` / `Jamuga` / `Woronino` | 利相卡 / 亚穆加 / 沃罗尼诺 | `comww2-xscn-map.tsv` · `_xscn_dict.tsv` |
| `2nd Jaeger Batt.` / `19th Aufklarungs Abt.` / `5CBRom` … | 第2猎兵营 / 第19侦察营 / 第5骑兵旅（罗马尼亚） | `work\xscn\POLICY.md` 编制名表 + 本 efile 既有对译 |
| `lvjtn9 AT gmail DOT com` | **保留原文** | 反爬混淆写法，非可译文本 |

---

## 五、四个硬坑（全部已修 + 已写进脚本注释）

1. **换行判定**：`elif n_crlf == n_lf: nl = "\r\n"` 把「纯 LF 文件（n_crlf=0, n_lf=1）」判成 CRLF，
   而 COMWW2 恰好有 **52 个纯 LF** ⇒ 输出换行错。修法＝`detect_nl()`：`n_crlf==0 且 n_lf>0 ⇒ LF`。
2. **部署循环误用泄漏变量**：校验用了**构建循环最后一轮**留下的 `nl` ⇒ 部署中断在 `hun01_b.txt`。
   修法＝`plan` 元组携带每个文件自己的 `nl`。
3. **同组重复文件漏铺**（见 §二.3）：新工具 `propagate_dup_txt.py`，**按原文 md5 分组**、
   逐文件沿用自己换行，把 rep 译文铺满同组。
4. **合成优先级反了**：`build_prose_zh.py` 原为「冲突保留原表」，把本轮订正**静默回滚 17 条**。
   改为**块内为准**并打印冲突。

---

## 六、独立复核（与生成器自述无关）

```python
# 逐文件核对：BOM / GBK 可解 / 换行沿用 / 行数一致 / 组内一致
SCENARIO .txt = 1032 ; TEXT-ZH = 1032 ; 缺失 0
结构异常 0 ; 原文组 898 ; 组内不一致 0
label 227 文件 / 17,925 非空行 / 65,381 汉字（与 docs\34 记录**逐字相同，零回归**）
```

回滚：`TEXT-ZH\SCENARIO\` 整目录删除即回退；旧文件备份
`backup\ORIGINAL-EFILE_COMWW2\TEXT-ZH-SCENARIO-before-prose\`（227 个）。
**原文侧零改动**（`SCENARIO\*.txt` mtime 仍 2018/2019）。

---

## 七、遗留（新发现，未修）

**label 保留集里 43 条明摆着的英文编制名**：唯一保留集 306 条中，43 条是普通英文名
（`216th Battery` · `2nd Jaeger Batt.` · `4th Anti-tank Brig.` · `244th Sturm. Abt.` ·
`10th Sapernii Brig.` · `[GK Norw.]` 批 `214 Pi Bn` / `244 (Res) Flk Bn` / `4 MG Bn` …），
**游戏内仍显示英文**。根因＝保留集由 `.xscn` 残留整批继承，而残留混进了普通英文词
（与 `donor 恒等保留` 吞普通名词同型）。**建议单列一批**：查既有对译 → 译 → 回填
`comww2-xscn-map.tsv` 与 `label-keep.tsv` / `xscn-uniq-final3.tsv`。
另有 47 条含 4+ 字母的残留行属缩写/代号型，按口径保留，正常。

---

## 八、下一批

1. `.tmsg` —— 20 个（15 个有正文，其余 5 个纯空行），**已导出** `work\comww2\comww2-tmsg-export.tsv`，
   工具 `work\tmsg\tmsg.py` 现成（纯文本层：`首 CRLF 段 + 正文 + 尾 CRLF 段`，首尾段必须逐字节保留）
2. `.xsch` —— 本 efile **0 个**
3. `L8` 位图 —— `EFILE_COMWW2\OPENGUI\hex_text.png` 等
4. `.front`(199) / `.xcam`(10) / `.doc`(1) —— 先判性（AG 的 `.xcam` 内实为场景文件名引用，非标题）
5. label 保留集 43 条清理（§七）
