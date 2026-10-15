# -*- coding: utf-8 -*-
"""把分支(军事游戏汉化-1)的 32 个地名订正，逐个到当前工作区的新词库里查有没有条目/冲突。只读。"""
import os, glob, io

WS = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(WS, "work", "_scan-pegbranch")

# (分支原译, 分支改成, 备注)
PAIRS = [
    ("沃尔日斯基", "伏尔加斯基", "Volzhsky 伏尔加格勒卫星城"),
    ("俄罗斯科耶", "鲁斯科耶", "Burnoshevo Russkoye"),
    ("库里", "九里", "구리市（限首尔/仁川图；库页岛 Kuri 另议）"),
    ("波塔尼河", "双溪大年", "Sungai Petani 吉打州"),
    ("米古姆", "美金", "미금"),
    ("镇永", "进永", "金海市進永邑"),
    ("初代", "哈茨泰", "原名未定 ⇒ 音译"),
    ("土路", "塔路", "Tōro＝今 Shakhtyorsk"),
    ("奇奥", "千绪", "千緒 Chio"),
    ("千早", "奇瓦盖", "原名未定 ⇒ 音译"),
    ("奥体川", "奥库泰河", "オクタイ川 无汉字 ⇒ 音译"),
    ("诸塚", "诸津", "諸津 Morotsu"),
    ("空四十四", "空十四", "คลองสิบสี่＝14"),
    ("洪松", "洪城", "Hongseong"),
    ("五结", "梧栖", "台中梧栖（原译串到宜兰五结）"),
    ("奈川", "内川", "内川 Naikawa"),
    ("马列奇卡河", "小列奇卡河", "Малая 对应 Большая"),
    ("哈曼", "咸安", "Haman 咸安郡"),
    ("苏城", "苏昌", "Сучан 标准中文旧称"),
    ("宁德", "盈德", "Yongdok 庆尚北道盈德郡"),
    ("阿克罗马", "阿克罗玛", "Acroma 音节"),
    ("帕纳空西阿瑜陀耶", "大城", "Phra Nakha Si Ayutthaya"),
    ("哈哲泰", "卡热泰", "Khazhetay"),
    ("昭披耶河", "湄南河", "Chao Phraya 与地图侧统一"),
    ("黑龙江", "阿穆尔河", "⚠️ 分支把简报侧改成俄方名"),
    ("莱河", "赖河", "Rai River"),
    ("乌拉尔机械厂", "乌拉尔马什", "Uralmash"),
    ("切尔通贝", "切尔通拜", "Chertonbay"),
    ("卡利尼诺", "加里宁诺", "Калинин"),
    ("别洛亚尔斯基", "别洛亚尔斯科耶", "-skoye"),
    ("杰斯亚特尼科瓦", "杰夏特尼科瓦", "Деся-"),
]

TARGETS = [t for p in PAIRS for t in p[:2]]

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return b.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', 'replace').splitlines()

files = []
for pat in ('glossary\\**\\*.tsv', 'glossary\\**\\*.md',
            'peg\\research\\*.tsv', 'peg\\research\\*.txt',
            'docs\\*.md'):
    files.extend(glob.glob(os.path.join(WS, pat), recursive=True))
files = sorted(set(files))
print("扫描文件数:", len(files))

# 命中表：中文名 -> [(文件, 行号, 该行)]
hits = {t: [] for t in TARGETS}
for f in files:
    rel = os.path.relpath(f, WS)
    try:
        lines = read(f)
    except Exception:
        continue
    for i, ln in enumerate(lines):
        for t in TARGETS:
            if t in ln:
                hits[t].append((rel, i + 1, ln.strip()[:210]))

report = []
report.append("# 分支地名订正 × 当前新词库 交叉核对（只读实测）\n")
report.append("扫描范围：`glossary\\**`、`peg\\research\\*`、`docs\\*.md`，共 %d 个文件\n" % len(files))

for old, new, note in PAIRS:
    report.append("\n## %s → %s\n" % (old, new))
    report.append("- 分支理由：%s\n" % note)
    for label, name in (("分支【旧】名", old), ("分支【新】名", new)):
        h = hits.get(name, [])
        report.append("- **%s `%s`**：命中 %d 处\n" % (label, name, len(h)))
        for rel, ln, txt in h[:8]:
            report.append("    - `%s:%d` %s\n" % (rel, ln, txt))
        if len(h) > 8:
            report.append("    - …另 %d 处\n" % (len(h) - 8))

open(os.path.join(OUT, "placename-crosscheck.md"), "w", encoding="utf-8").write("".join(report))
print("写出", os.path.join(OUT, "placename-crosscheck.md"))

# 控制台摘要：只看"新名在词库里有条目"的
print("\n=== 摘要：分支新名是否已在当前词库中出现 ===")
for old, new, note in PAIRS:
    n = len(hits.get(new, []))
    o = len(hits.get(old, []))
    print("%-14s -> %-14s  新名命中 %3d  旧名命中 %3d" % (old, new, n, o))
