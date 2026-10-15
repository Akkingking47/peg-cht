# -*- coding: utf-8 -*-
import io, sys, os, glob, re
sys.stdout.reconfigure(encoding="utf-8")
SRC = r"D:\OpenPG2\EFILE_BASEKORP\SCENARIO"
ZH = r"D:\OpenPG2\EFILE_BASEKORP\TEXT-ZH\SCENARIO"

# 1) bc_it_teu.xscn 里那条可疑串的原始字节上下文
p = os.path.join(SRC, "bc_it_teu.xscn")
b = open(p, "rb").read()
i = b.find(b"\x04q~")
print("bc_it_teu.xscn size", len(b), "offset of probe", i)
print("raw:", b[max(0, i - 40):i + 60])

# 2) 已部署的 ssbdm 散文里，日舰/舰名怎么处理
HAN = re.compile(r"[\u4e00-\u9fff]")
for kw in ["大和", "武藏", "长门", "金刚", "赤城", "瑞凤", "最上", "山本", "联合舰队"]:
    hits = []
    for f in sorted(glob.glob(os.path.join(ZH, "ssbdm*.txt"))):
        t = open(f, "rb").read().decode("gbk", "replace")
        if kw in t:
            hits.append(os.path.basename(f))
    print("ZH ssbdm 含 %-6s -> %s" % (kw, hits[:5]))

# 3) 原文侧有没有 Akagi / Yamato 等
for kw in ["Akagi", "Yamato", "Nagato", "Kongo", "Musashi", "Zuiho", "Mogami", "Midway"]:
    hits = []
    for f in sorted(glob.glob(os.path.join(ZH, "ssbdm*.txt"))) + sorted(glob.glob(os.path.join(SRC, "ssbdm*.txt"))):
        t = open(f, "rb").read().decode("gbk", "replace")
        if kw in t:
            hits.append(os.path.basename(f))
    print("含 %-8s -> %s" % (kw, hits[:6]))

# 4) ssbdm_47.xscn / ssbdm_26.xscn 串区全量（看这批 'Xxx 的邻居）
def parse(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("x", r"D:\DSH\军事游戏汉化\work\xscn\xscn.py")
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    return m.parse(path)

for fn in ["ssbdm_47.xscn", "ssbdm_26.xscn"]:
    _t, ent = parse(os.path.join(SRC, fn))
    print("=== %s (%d 串)" % (fn, len(ent)))
    for e in ent:
        s = e.decode("gbk", "replace")
        print("   |" + s[:70])
