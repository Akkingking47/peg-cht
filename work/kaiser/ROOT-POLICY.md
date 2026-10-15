# KAISER 根级四件套 · 翻译口径（子代理必读）

目标 efile：`EFILE_KAISER`（Open General / OpenPG 的**一战**装备文件，作者 Juankar，
覆盖 1850–1926）。题材含：一战各战场、俄国内战、意土战争、巴尔干战争、日俄战争、
美西战争、布尔战争、义和团、殖民地战争。**装备/单位名是多语言的**（德/俄/波/捷/匈/
土/芬/爱沙尼亚/拉脱维亚/立陶宛/罗马尼亚/塞克/保/希/意/西/葡/法/英/日/阿尔巴尼亚/亚美尼亚…）。

---

## 一、总原则（铁律）

1. **武器/装备/飞机/舰艇的「型号代号」一律保留原文**：
   `Albatros C.III` `Fokker D.VII` `Sopwith Pup` `10,5cm lFH 98/09` `Canon de 75 mle 1897`
   `122-mm Gaubitsa obr.1909` `QF 2pdr MkII 'Pom-Pom'` `Bristol M.1C Bullet` `76.2mm PK02`。
   ⇒ **不要**把 `Infanterie` 以外的人名、厂名、机名、舰名译成中文。
2. **舰级名保留原文**（`Bayern Class` `Queen Elizabeth Class` `Tegetthoff Class`），
   **舰名保留原文**（`Novik` `Aurora` `Potemkin` `Rurik` `Suffren`）。
3. **只译「通名/类别词」** —— 即「这是什么兵种/什么类别的装备/什么建筑设施」的词：
   如 `Infanterie`=步兵、`Piechota`=步兵、`Pehota`=步兵、`Pushka`=火炮、`Howitzer`=榴弹炮、
   `Bunker`=碉堡、`Wagon`=马车、`Truck`=卡车、`Sail Frigate`=风帆护卫舰。
4. **未知/拿不准的词一律不译**（输出里就不写它）——宁可漏，不可错。
   特别地：**人名、地名、厂名、部队番号、政党、民族名（作专有名词时）不要译**。
5. 中文用词要**跨语言统一**：德语 `Infanterie`、俄语 `Pehota`、波兰语 `Piechota`、
   捷克语 `Pechota`、匈牙利语 `Gyalogság`、芬兰语 `Jalkaväki` 一律译「步兵」。
6. 罗马数字/序号（`I` `II` `XIV` `MkII`）不译。

---

## 二、任务（token 表翻译）

输入：`work\kaiser\_tok_partNN.txt`，每行三列（TAB 分隔）：
```
token  出现次数  一个含该 token 的实际装备名样例
```
输出：`work\kaiser\_tok_dst_partNN.txt`，每行两列（TAB 分隔）：
```
token  中文
```

**只输出你要翻译的 token**；**不需要翻译的 token 直接不输出**（不要写「保留」「—」「同原文」）。

### 必须输出的（例）

| token | 中文 |
|---|---|
| Infanterie / Infantry / Piechota / Pehota / Jalkaväki | 步兵 |
| Kavallerie / Cavalry / Kawaleria / Süvari | 骑兵 |
| Artillerie / Artillery | 炮兵 |
| Pioniere / Sapper / Saperzy | 工兵 |
| Wagon / Wagen / Vagun / Vagon | 马车 |
| Truck | 卡车 |
| Bunker | 碉堡 |
| Fort | 要塞 |
| Howitzer / Haubitsa / Haubica / Houfnice | 榴弹炮 |
| Gun / Pushka / Armata / Top / Ágyú | 火炮 |
| Mortar / Mörser / Mortira / Minomet | 迫击炮 |

### 绝对不要输出的（例）

`Albatros` `Fokker` `Sopwith` `Nieuport` `SPAD` `Skoda` `Krupp` `Schneider` `Canon`（厂/机名）
`Alaska` `Bayern` `Novik` `Aurora`（地名/舰名）
`Class` `Mk` `MkI` `II` `XIV` `mm` `cm` `obr.` `wz.` `vz.` `md.` `Mle` `pdr` `cwt`（型号标记）
`mm` `cm` `mm.` `sm.`（单位）

---

## 三、格式纪律

- UTF-8 **无 BOM**，行间 `\n`，**一行一个 `token<TAB>中文`**，不要表头、不要序号、不要空行。
- token 必须**与输入逐字相同**（含大小写与撇号）。
- 中文不要含 TAB。

---

## 四、分片与回报

每个子代理处理自己那一片（见派发指令里的文件名与条数）。
完成自检后**只回复一行**：`part-NN 完成，共 M 条`（不要贴内容）。
