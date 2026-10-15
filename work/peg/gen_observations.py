# -*- coding: utf-8 -*-
"""生成 peg/research/observations.tsv —— 可填证的研究观察主表
原文与出处全部由文件实测得出（行号 / VA / 文件名），可复算。
"""
import os, struct

GAME = r"D:\Program Files\PeG"
OUT = r"D:\DSH\军事游戏汉化\peg\research\observations.tsv"

def lines(fn):
    return open(os.path.join(GAME, fn), "rb").read().decode("cp1252").split("\r\n")

gui030 = lines("Gui030.txt")
gui97 = lines("GUI97.TXT")
gui97deu = lines("GUI97.DEU")
gui97fra = lines("GUI97.FRA")
guisp = lines("GUISP.TXT")
gui98 = lines("GUI98.TXT")
guisa = lines("GUISA.txt")

# exe 国名表：VA 0x492FEC 起，步长 20
countries_va = [0x492fec + i * 20 for i in range(20)]
rows = []
def add(oid, cat, original, src, loc, note=""):
    rows.append([oid, cat, original, src, loc, note, "", "", "待填"])

# ---------- O1 阵营 / 国家列表 ----------
for i, va in enumerate(countries_va):
    add(f"O1-{i+1:02d}", "O1 阵营槽", gui030[i], "Gui030.txt",
        f"行 {i+1}；exe 内置表 VA {va:#x}（FO {va-0x48e000+0x8b800:#x}）",
        "槽位固定 20 条 × 20 字节；GUI 文本可覆盖 exe 内置表")
# 槽位复用（同一槽在别的 e-file 里被改写成不同阵营）
for ln, tag in [(4, "GUI98.TXT"), (5, "GUI98.TXT"), (7, "GUISP.TXT"), (12, "GUISP.TXT"),
                (13, "GUISP.TXT"), (14, "GUISP.TXT"), (20, "GUISA.txt")]:
    src = {"GUI98.TXT": gui98, "GUISP.TXT": guisp, "GUISA.txt": guisa}[tag]
    add(f"O1-{ln}R", "O1 槽位复用", f"GUI97/Gui030 行{ln}: {gui030[ln-1]!r}  ↔  {tag} 同行: {src[ln-1]!r}",
        f"Gui030.txt / {tag}", f"行 {ln}",
        "同一槽位在不同 e-file 被重标为不同阵营 ⇒ 阵营标签是**可换壳的槽位**，非固定国别表")

# ---------- O2 叙事立场 ----------
plies = [
    ("Scenario/nspegu01.ply", "The Chinese and the North Koreans look poised to make a sudden attack on Seoul.  Stop them at all costs."),
    ("Scenario/nspegu19.ply", "The Chinese and the North Koreans look like they're entrenched in Seoul, but it's up to you to take it all back.  Don't let me down commander!"),
    ("Scenario/nspegu25.ply", "Storming Volgograd / The U.S. mobilizes its forces to aid their Russian allies ... to drive the People's Republic of China from the Urals ..."),
    ("Userscen/Crimson.ply", "Russian rebels have seized and taken control of ICBM missile bases in the outskirts of Artem ..."),
    ("Userscen/Demise of Osma.ply", "The demise of Osma / Taliban forces have retreated to their stronghold in Kandahar ..."),
    ("Userscen/Eome2.ply", "I MEF is asked by CINCPACFOR to bypass Hanoi in order to allow Vietnamese exile forces to retake the city ..."),
    ("Userscen/Land Reclamation.ply", "Since 1945 Japans Northern Islands have been illegally in Russian hands. Chinese aggression has given us the opportunity ..."),
    ("Userscen/RetStal27.ply", "Return to Stalingrad / ... German and Italian Troops return to Stalingrad, this time to help their Russian Ally to repulse Chinese Army ..."),
    ("Userscen/Revolution.ply", "Chinese Rebels have decided to join forces with america and strike singapore ..."),
    ("Userscen/Sarajevo.ply", "Siege of Sarajevo 28/10/1992 / Serbian Army is ready to launch his final assault ..."),
    ("Scenario/nspegu10.ply", "Enter Scenario Description（占位未填）"),
    ("Userscen/*.ply", "（共 14 个 .ply：13 个 501 B ＋ 1 个 525 B；全文见 evidence/ply-narrative.txt）"),
]
for i, (fn, txt) in enumerate(plies, 1):
    add(f"O2-{i:02d}", "O2 叙事立场", txt, fn, "见 evidence/ply-narrative.txt（定长记录，原文原样）")

# ---------- O3 多语言外壳 ----------
add("O3-01", "O3 多语言实践", f"英语 GUI97.TXT（{len(gui97)} 行）／德语 GUI97.DEU（{len(gui97deu)} 行）／法语 GUI97.FRA（{len(gui97fra)} 行）三份同构文本包",
    "GUI97.TXT / GUI97.DEU / GUI97.FRA", "目录根；逐行对照见 evidence/gui-languages.tsv",
    "SSI 官方即用「换文本文件」实现德/法发行 ⇒ 本地化机制为厂商原生设计")
add("O3-02", "O3 多语言实践", "德语样本：Österrceich / die Tschechloslovakei / Großbritannien；法语样本：Autriche / Tchécoslovaquie 风格拼写",
    "GUI97.DEU / GUI97.FRA", "行 1–10（见 gui-languages.tsv 第 2、3 列）")
add("O3-03", "O3 多语言实践", "exe 内多语言分支：LoadLanguageConfigFile / lang.cfg / 与 'german'、'french' 比较（调试串 'we are german' / 'we are french'）",
    "PeG030.exe", "字符串 VA 区（FO 0x9E81C 附近 lang.cfg）")
add("O3-04", "O3 多语言实践", "社区俄语化：标题画面俄文 'Генерал Холодной войны'（与英文 'COLD WAR GENERAL' 并存）",
    "CWGEN.dat → ST030.S16[1]", "图形 800×600；渲染证据 symbol-layer/ST030_title.png")

# ---------- O4 文本外置化 ----------
add("O4-01", "O4 外置化程度", "exe 硬编码 5 个文本 stem：Equip30 / gui030 / misc030 / name030 / tips030",
    "PeG030.exe", "字符串表（Text.c 模块：InitGlobalText / LoadEquipText / LoadScenarioText）",
    "⇒ 换语言＝换同名文本文件，零代码改动")
add("O4-02", "O4 外置化程度", f"Gui030.txt {len(gui030)} 行 / 11,855 B（纯 ASCII）；Gui031.txt 同规模",
    "Gui030.txt / Gui031.txt", "目录根")
add("O4-03", "O4 外置化程度", "装备名 Equip30/31/97/98/SA/SP.TXT 合计 4,850 行；人名 Name030.txt 1,000 行 ＋ NAMES*.TXT 1,062 行",
    "多个 *.TXT", "目录根（明细见 docs\\38 §一）")
add("O4-04", "O4 外置化程度", "场景文本 Scenario\\*.TXT 790 文件 / 8,502 行 / 223 KB；9 类命名后缀（_M 地图格名 / _U 部队名 / I 简报 / BV·V·TV·L 战后评述…）",
    "Scenario\\*.TXT", "官方规范 PFS `SCN & CAM text files` 表")
add("O4-05", "O4 外置化程度", "二进制层零文本：.scn×213 每文件仅 2 个文件名引用；.map×46 可打印串 0；.eqp 仅图标码",
    ".scn / .map / .eqp", "实测（work\\peg\\census_text.py）",
    "⇒ 立场/叙事的替换成本几乎为零，这是核心渗透机制")

# ---------- O5 符号层 ----------
for i, (s, ln) in enumerate([("Brilliant Victory", 35), ("Victory", 36),
                             ("Tactical Victory", 37), ("Loss", 38), ("It's A Draw - ", 39)], 1):
    add(f"O5-{i:02d}", "O5 符号层", s, "Gui030.txt", f"行 {ln}（早期 GUI97.TXT 行 32–36 对应）",
        "胜利分级体系：大胜 / 胜 / 战术胜 / 败 / 平")
add("O5-06", "O5 符号层", "HONOR ROLL 荣誉榜画面（含栏目标题，为位图烘焙文字）", "CWGEN.dat → HEX.S16[0]",
    "图形 800×600；渲染证据 symbol-layer/HEX_honor-roll.png")
add("O5-07", "O5 符号层", "MEDALS.S16[0] 勋章界面底图（纯深绿底，无文字；勋章为独立图形）", "CWGEN.dat → MEDALS.S16[0]",
    "图形 265×185；渲染证据 symbol-layer/MEDALS_medal-board.png")
add("O5-08", "O5 符号层", "exe 内置兵种表含 'Flak'（11 条 × 20 B @ VA 0x492C2C）", "PeG030.exe",
    "见 evidence/exe-tables.md")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("obs_id\t分类\t原文\t出处文件\t定位\t观察要点\t中文译文\t译者\t状态\n")
    for r in rows:
        f.write("\t".join(x.replace("\t", " ") for x in r) + "\n")
print("observations.tsv:", len(rows), "rows")
