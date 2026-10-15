# -*- coding: utf-8 -*-
"""修 `ww2-scn-map.tsv` 里「译文＝原文」的自等行：`Viel Glück!`（死译，成品 DAK_SP1_i.txt:6 /
Fi04_i.txt:6 因此一直是德文）。规范形取同表 ASCII 兄弟行 row9395 `Viel Gluck!` → `祝好运！`。

背景（教训）：英文原件由 `gen_scn.py:180` 用 **latin-1** 解码（1 字节=1 码位），所以 `ü`
(0xFC) 解出来就是真正的 `ü`；先前用 UTF-8 读原件做「该行是否存在于原件」的核查，会把
含高位字节的行误判成「映射表遗留死行」⇒ **原件核查必须与生成器同用 latin-1**。
"""
import io, os, shutil, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MAP = r"D:\DSH\军事游戏汉化\pegww2\research\ww2-scn-map.tsv"
BAK = r"D:\DSH\军事游戏汉化\backup\before-vielgluck\ww2-scn-map.tsv"
EN, ZH = "Viel Glück!", "祝好运！"

lines = io.open(MAP, encoding="utf-8-sig").read().replace("\r\n", "\n").split("\n")
hit, out = 0, []
for l in lines:
    c = l.split("\t")
    if len(c) >= 3 and c[0] == EN and c[1] == EN:       # 自等行 = 漏译
        c[1], c[2] = ZH, "词库"
        hit += 1
        l = "\t".join(c)
    out.append(l)
print("命中自等行 %d 条（en=%r）" % (hit, EN))
if hit and "--apply" in sys.argv:
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if not os.path.isfile(BAK):
        shutil.copy2(MAP, BAK)
        print("备份 → %s" % BAK)
    io.open(MAP, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("已写入 %s" % MAP)
