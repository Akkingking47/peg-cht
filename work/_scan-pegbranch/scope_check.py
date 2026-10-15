# -*- coding: utf-8 -*-
"""确认 scope 命名 + 统计当前工作区 PeG 侧资产里 32 个地名的新旧状态。只读。"""
import os, collections, glob

WS = r"D:\DSH\军事游戏汉化"

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return b.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', 'replace').splitlines()

# 1) 主库里的全部 scope
cg = os.path.join(WS, "glossary", "layers", "common-glossary.tsv")
cnt = collections.Counter()
with open(cg, 'rb') as f:
    head = f.read(4)
for ln in read(cg):
    if ln.startswith('#') or not ln.strip():
        continue
    c = ln.split('\t')
    if len(c) > 3:
        cnt[c[3]] += 1
print("=== common-glossary.tsv 的 scope 分布 ===")
for k, v in cnt.most_common():
    print("  %-24s %d" % (k, v))

# 2) 32 个地名在当前 PeG 侧资产中的新旧状态
PAIRS = [
    ("沃尔日斯基", "伏尔加斯基"), ("俄罗斯科耶", "鲁斯科耶"), ("库里", "九里"),
    ("波塔尼河", "双溪大年"), ("米古姆", "美金"), ("镇永", "进永"),
    ("初代", "哈茨泰"), ("土路", "塔路"), ("奇奥", "千绪"), ("千早", "奇瓦盖"),
    ("奥体川", "奥库泰河"), ("诸塚", "诸津"), ("空四十四", "空十四"),
    ("洪松", "洪城"), ("五结", "梧栖"), ("奈川", "内川"),
    ("马列奇卡河", "小列奇卡河"), ("哈曼", "咸安"), ("苏城", "苏昌"),
    ("宁德", "盈德"), ("阿克罗马", "阿克罗玛"), ("帕纳空西阿瑜陀耶", "大城"),
    ("哈哲泰", "卡热泰"), ("昭披耶河", "湄南河"), ("黑龙江", "阿穆尔河"),
    ("莱河", "赖河"), ("乌拉尔机械厂", "乌拉尔马什"), ("切尔通贝", "切尔通拜"),
    ("卡利尼诺", "加里宁诺"), ("别洛亚尔斯基", "别洛亚尔斯科耶"),
    ("杰斯亚特尼科瓦", "杰夏特尼科瓦"),
]
# 只在这个地名自己的行上判（避免子串噪声）：行里同时要有对应的英文 key
KEYS = {
    "沃尔日斯基": ["Wolzskij", "Volzhshiy"], "俄罗斯科耶": ["Russkoye"],
    "库里": ["Kuri"], "波塔尼河": ["Potani"], "米古姆": ["Migum"],
    "镇永": ["Chingyong", "Chinyong"], "初代": ["Hatsutai"], "土路": ["Toro"],
    "奇奥": ["Chio"], "千早": ["Chiwagai"], "奥体川": ["Okutai"],
    "诸塚": ["Morotsu"], "空四十四": ["Khlong Sip Si", "Klong Sip Si"],
    "洪松": ["Hongsong"], "五结": ["Wuchieh"], "奈川": ["Naikawa"],
    "马列奇卡河": ["Malaja"], "哈曼": ["Haman"], "苏城": ["Suchan"],
    "宁德": ["Yongdok"], "阿克罗马": ["Acroma"], "帕纳空西阿瑜陀耶": ["Ayutthaya"],
    "哈哲泰": ["Khazhetay"], "昭披耶河": ["Chao Praya", "Chayo Praya"],
    "黑龙江": ["Amur"], "莱河": ["Rai"], "乌拉尔机械厂": ["Uralmash"],
    "切尔通贝": ["Chertonbay"], "卡利尼诺": ["Kalinino"],
    "别洛亚尔斯基": ["Beloyarskoye"], "杰斯亚特尼科瓦": ["Desyatnikova"],
}

FILES = ["peg/research/scenario-map.tsv", "peg/research/scenario-long-zh.tsv",
         "work/glossary/pegww2-glossary.tsv"]

print("\n=== 每个地名在「同 key 行」上用的是旧名还是新名 ===")
for p in FILES:
    fp = os.path.join(WS, p.replace('/', os.sep))
    if not os.path.exists(fp):
        print("  [缺] %s" % p); continue
    lines = read(fp)
    print("\n-- %s (%d 行) --" % (p, len(lines)))
    for old, new in PAIRS:
        o = n = 0
        for ln in lines:
            if any(k in ln for k in KEYS[old]):
                if new in ln and new != "大城":
                    n += 1
                elif old in ln:
                    o += 1
                elif new in ln:
                    n += 1
        if o or n:
            print("  %-16s 旧[%s]×%d  新[%s]×%d" % ("", old, o, new, n))
