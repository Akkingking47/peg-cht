# -*- coding: utf-8 -*-
"""地名词库冲突裁定：分支(军事游戏汉化-1)的 32 个订正 × 当前新词库。
只读；产出 work/_scan-pegbranch/placename-verdict.md 与 docs/43-*.md 的数据部分。"""
import os, glob

WS = r"D:\DSH\军事游戏汉化"
OUT = os.path.join(WS, "work", "_scan-pegbranch")

# (英文检索键, 分支新名, 分支旧名, 第几批)
ITEMS = [
    (["Wolzskij", "Volzhshiy", "Volhsk"], "伏尔加斯基", "沃尔日斯基", "5? 分支出处=第2批"),
    (["Russkoye"], "鲁斯科耶", "俄罗斯科耶", "2"),
    (["Kuri"], "九里", "库里", "3"),
    (["Potani"], "双溪大年", "波塔尼河", "2"),
    (["Migum"], "美金", "米古姆", "3"),
    (["Chingyong", "Chinyong"], "进永", "镇永", "2"),
    (["Hatsutai"], "哈茨泰", "初代", "5"),
    (["Toro"], "塔路", "土路", "5"),
    (["Chio"], "千绪", "奇奥", "5"),
    (["Chiwagai"], "奇瓦盖", "千早", "5"),
    (["Okutai"], "奥库泰河", "奥体川", "5"),
    (["Morotsu"], "诸津", "诸塚", "5"),
    (["Sip Si"], "空十四", "空四十四", "2"),
    (["Hongsong"], "洪城", "洪松", "1"),
    (["Wuchieh"], "梧栖", "五结", "1"),
    (["Naikawa"], "内川", "奈川", "5"),
    (["Malaja"], "小列奇卡河", "马列奇卡河", "2"),
    (["Haman"], "咸安", "哈曼", "2"),
    (["Suchan"], "苏昌", "苏城", "1"),
    (["Yongdok"], "盈德", "宁德", "2"),
    (["Acroma"], "阿克罗玛", "阿克罗马", "2"),
    (["Ayutthaya"], "大城", "帕纳空西阿瑜陀耶", "4"),
    (["Khazhetay"], "卡热泰", "哈哲泰", "2"),
    (["Praya", "Phraya"], "湄南河", "昭披耶河", "2"),
    (["Amur"], "阿穆尔河", "黑龙江", "1 ⚠"),
    (["Rai"], "赖河", "莱河", "1"),
    (["Uralmash"], "乌拉尔马什", "乌拉尔机械厂", "1"),
    (["Chertonbay"], "切尔通拜", "切尔通贝", "1"),
    (["Kalinino"], "加里宁诺", "卡利尼诺", "1"),
    (["Beloyarskoye"], "别洛亚尔斯科耶", "别洛亚尔斯基", "1"),
    (["Desyatnikova"], "杰夏特尼科瓦", "杰斯亚特尼科瓦", "1"),
]

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            return b.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return b.decode('utf-8', 'replace').splitlines()

layer_files = sorted(glob.glob(os.path.join(WS, "glossary", "layers", "*.tsv")))
rows = []
for f in layer_files:
    for i, ln in enumerate(read(f)):
        if ln.startswith('#') or not ln.strip():
            continue
        rows.append((os.path.basename(f), i + 1, ln))

md = []
md.append("## 逐条裁定（词库实测）\n")
md.append("| 地名 | 分支旧名 | 分支新名 | 词库里的登记 | 裁定 |")
md.append("|---|---|---|---|---|")

stat = {}
for keys, new, old, batch in ITEMS:
    hits = []
    for fn, ln_no, ln in rows:
        low = ln.lower()
        if any(k.lower() in low for k in keys):
            hits.append((fn, ln_no, ln))
    verdict = "C 直接吸收"
    detail = []
    for fn, ln_no, ln in hits:
        c = ln.split('\t')
        # 判断这行给出的中文值
        val = None
        if fn in ("common-glossary.tsv", "scope-glossary.tsv", "series-glossary.tsv", "short-glossary.tsv") and len(c) > 3:
            val = c[1]; scope = c[3]
        elif fn == "faction-places.tsv" and len(c) >= 4:
            val = "【%s】%s" % (c[1], c[3]); scope = "faction"
        elif fn == "common-drift.tsv" and len(c) >= 4:
            val = c[3]; scope = "drift"
        elif fn in ("converge-list.tsv", "scope-diff.tsv"):
            val = ln; scope = "conv"
        else:
            val = c[1] if len(c) > 1 else ln; scope = fn
        if val and (new in str(val)):
            if verdict == "C 直接吸收":
                verdict = "A 词库已同分支"
        if val and (old in str(val)):
            if verdict in ("C 直接吸收", "A 词库已同分支"):
                verdict = "B 词库仍是旧名"
        detail.append("%s → %s" % (fn, str(val)[:80]))
    if keys == ["Amur"]:
        verdict = "⚠ 阵营视角冲突"
    stat[(old, new)] = (verdict, detail)
    md.append("| `%s` | %s | **%s** | %s | **%s** |"
              % (keys[0], old, new, "<br>".join(detail[:4]) if detail else "（无登记）", verdict))

md.append("\n## 裁定口径\n")
md.append("- **A 词库已同分支** ⇒ 零冲突，直接吸收。\n")
md.append("- **B 词库仍是旧名** ⇒ 分支的新名更正确；但必须**改本作侧（`PEG_BASE`/`PEGWW2_SCN`）或已登记差异表**，不得搬用别的 scope 的值。\n")
md.append("- **C 直接吸收** ⇒ 词库无任何登记，不冲突。\n")
md.append("- **⚠ 阵营视角冲突** ⇒ 按 `faction-places.tsv` 逐文件判视角，禁止全局替换。\n")

open(os.path.join(OUT, "placename-verdict.md"), "w", encoding="utf-8").write("\n".join(md))

import collections
c = collections.Counter(v[0] for v in stat.values())
print("=== 裁定分布 ===")
for k, v in c.items():
    print("  %-22s %d" % (k, v))
print("\n=== 明细 ===")
for (old, new), (v, d) in stat.items():
    print("%-22s %-14s -> %-14s" % (v, old, new))
    for x in d[:3]:
        print("       ", x)
