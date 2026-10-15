import collections
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
UI = r"D:\DSH\军事游戏汉化\peg\research\ui-glossary.tsv"
PEGUI = r"D:\DSH\军事游戏汉化\work\glossary\pegww2-glossary.tsv"

# 类别 → 层归属（按用户口径：游戏选项/机制=专项；地名/人名/部队名/军事用语=通用）
COMMON = {"兵种", "编制", "军衔", "移动方式", "地形", "天气", "缩写", "数值", "阵营", "舰艇", "装备名", "后勤"}
SCOPE = {"菜单", "游戏机制", "战果", "战斗提示", "指挥官技能", "特种装备", "战术", "工事", "属性"}

cnt = collections.Counter()
ex = collections.defaultdict(list)
for l in io.open(UI, encoding="utf-8-sig"):
    if l.startswith("#"):
        continue
    c = l.rstrip("\n").split("\t")
    if len(c) < 2 or not c[0].strip():
        continue
    cat = c[2].strip() if len(c) > 2 else "?"
    if cat in COMMON:
        k = "通用"
    elif cat in SCOPE:
        k = "专项"
    else:
        k = "待分"
    cnt[k] += 1
    ex[(k, cat)].append((c[0].strip(), c[1].strip()))

print("=== 界面术语表 %d 条，按类别分层的机器初判 ===" % sum(cnt.values()))
for k in ("通用", "专项", "待分"):
    print("  %-4s %4d 条" % (k, cnt[k]))
print()
for (k, cat), v in sorted(ex.items(), key=lambda x: (x[0][0], -len(x[1]))):
    print("  %-4s %-8s %3d 条   例: %s" % (k, cat, len(v), "、".join(a for a, _ in v[:6])))

print()
print("=== 明确建议 ===")
print("  通用层（跨项目复用）: 兵种·编制·军衔·移动方式·地形·天气·缩写·数值·阵营·舰艇·装备名·后勤")
print("  专项层（各项目自定）: 菜单·游戏机制·战果·战斗提示·指挥官技能·特种装备·属性")
print("  待分（需人工二分）  : 战术（军语如「警戒射击」vs 游戏造词如「打了就跑」）· 工事")
