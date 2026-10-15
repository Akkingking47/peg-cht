# -*- coding: utf-8 -*-
"""清 COMWW2 label 保留集里**明摆着的英文编制名**（43 条中的 42 条；`HQ` 保留）。

背景（09-30 发现）：`label-keep.tsv` ＋ `xscn-uniq-final3.tsv` 的唯一保留集 306 条里，
42 条是**普通英文编制名/番号**（`216th Battery`、`2nd Jaeger Batt.`、`10th Sapernii Brig.`…），
游戏内仍显示英文。根因＝保留集整批继承 `.xscn` 残留，而残留混进了普通英文词。

口径（全部有据）：
  - `work\\xscn\\POLICY.md` 编制名表：`Batt.`→营 · `Brig.`→旅 · `Div.`→师 · `Corps`→军 ·
    `Abt.`→营 · `Aufklarungs`→侦察 · `Sturm.`→突击炮 · `Jaeger`→猎兵 · `Sapernii`→工兵 ·
    `Rocket`→火箭炮 · `Anti-tank`→反坦克 · `Guard`→近卫 · `SP Art.`→自行火炮
  - `BAP`/`VAK`/`AAD`/`KBF` 保留缩写（`POLICY.md` §五/补充 5：拿不准一律保留），只加中文类别说明
  - 本 efile 已交付实证：`GK Norw.`→挪威山地军 · `Pi`→工兵 · `Pz Bn Zbv`→装甲营（特种用途） ·
    `JgdPz. Abt.`→反坦克歼击营 · `SchlFl.Div.`→对地攻击航空师 · `Mar.`→海军

落盘三件事（缺一即跨层不一致）：
  1. 已交付 `TEXT-ZH\\SCENARIO\\*.txt` 整行精确替换 —— **按原文 md5 同组同步**；
  2. `comww2-xscn-map.tsv`（`.xscn` 译文表）键去重；
  3. `label-keep.tsv` / `xscn-uniq-final3.tsv` 两份保留集移除已译键。

用法:
    python fix_label_keep.py --doc                      # 只生成对照表（人工复核）
    python fix_label_keep.py --dry
    python fix_label_keep.py --apply
"""
import hashlib
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\OpenPG2\EFILE_COMWW2\SCENARIO"
ZH = r"D:\OpenPG2\EFILE_COMWW2\TEXT-ZH\SCENARIO"
TABLE = os.path.join(HERE, "label-keep-zh.tsv")

# 原文 → 译文（整行精确；`HQ` 为纯代号，按口径保留，**不在此表**）
FIX = [
    ("1  Mixed  Air Div", "第1混成航空师"),
    ("9th Kv. Div.", "第9装甲师"),
    ("10th Kv. Div.", "第10装甲师"),
    ("10th Sapernii Brig.", "第10工兵旅"),
    ("11th Sapernii Brig.", "第11工兵旅"),
    ("20th Sap. Batt.", "第20工兵营"),
    ("409th Sapernii Batt.", "第409工兵营"),
    ("19th Aufklarungs Abt.", "第19侦察营"),
    ("244th Sturm. Abt.", "第244突击炮营"),
    ("2nd Jaeger Batt.", "第2猎兵营"),
    ("4th Anti-tank Brig.", "第4反坦克旅"),
    ("8th Guard Tank Corps", "近卫第8坦克军"),
    ("216th Battery", "第216炮兵连"),
    ("307th Grds. Rocket Batt.", "近卫第307火箭炮营"),
    ("13th SP Art. Brig.", "第13自行火炮旅"),
    ("1434th SP Art. Reg.", "第1434自行炮兵团"),
    ("292nd SP Art. Reg.", "第292自行炮兵团"),
    ("344th SP Art. Reg.", "第344自行炮兵团"),
    ("360th SP Art. Reg.", "第360自行炮兵团"),
    ("53rd JdgPz. Abt.", "第53反坦克歼击营"),
    ("9th Div. HQ", "第9师司令部"),
    ("27th Reg. HQ", "第27团司令部"),
    ("62nd Army HQ", "第62集团军司令部"),
    ("13th KBF", "第13（KBF，波罗的海舰队）"),
    ("5th KBF", "第5（KBF，波罗的海舰队）"),
    ("173rd BAP", "第173（BAP，轰炸航空兵团）"),
    ("23rd BAP", "第23（BAP，轰炸航空兵团）"),
    ("38th BAP", "第38（BAP，轰炸航空兵团）"),
    ("18th AAD", "第18（AAD，防空师）"),
    ("406th VAK", "第406（VAK，高炮军）"),
    ("408th VAK", "第408（VAK，高炮军）"),
    ("14 MG bn [GK Norw.]", "第14机枪营 [挪威山地军]"),
    ("4 MG Bn [GK Norw.]", "第4机枪营 [挪威山地军]"),
    ("214 Pi Bn [GK Norw.]", "第214工兵营 [挪威山地军]"),
    ("405 Pi Bn [GK Norw.]", "第405工兵营 [挪威山地军]"),
    ("40 Pz Bn Zbv [GK Norw.]", "第40装甲营（特种用途）[挪威山地军]"),
    ("244 (Res) Flk Bn [GK Norw.]", "第244预备高炮营 [挪威山地军]"),
    ("504 Mar. Art Bn [GK Norw.]", "第504海军炮兵营 [挪威山地军]"),
    ("730 sArt Bn [GK Norw.]", "第730重炮营 [挪威山地军]"),
    ("13. JgdFl.Div.", "第13歼击航空师"),
    ("6. JgdFl.Div.", "第6歼击航空师"),
    ("15. SchlFl.Div.", "第15对地攻击航空师"),
    ("33. SchlFl.Div.", "第33对地攻击航空师"),
    # 09-30 二次扫描补入：`151 Wing [RAF]` 也是整行英文（方括号内 `RAF` 按口径保留）
    ("151 Wing [RAF]", "第151联队 [RAF]"),
]
EXPECT = 44


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    apply = "--apply" in sys.argv
    doc = "--doc" in sys.argv
    if not apply:
        print("（干跑模式；--apply 才写盘）")

    # 结构：原文 md5 → 同组文件名（保证组内一致）
    groups = {}
    for f in sorted(os.listdir(SRC)):
        if f.lower().endswith(".txt"):
            groups.setdefault(md5b(open(os.path.join(SRC, f), "rb").read()), []).append(f)

    fixmap = dict(FIX)
    if len(fixmap) != EXPECT:
        raise SystemExit("FIX 表 %d 条 ≠ 预期 %d" % (len(fixmap), EXPECT))

    if doc:
        with io.open(TABLE, "w", encoding="utf-8", newline="") as fh:
            fh.write("src\tdst\n")
            for s, d in FIX:
                fh.write("%s\t%s\n" % (s, d))
        print("→ %s（%d 条）" % (TABLE, len(FIX)))
        return

    # ① 已交付 .txt 整行替换
    changed_files = 0
    hits_total = 0
    hit_keys = set()
    for f in sorted(os.listdir(ZH)):
        if not f.endswith(".txt"):
            continue
        p = os.path.join(ZH, f)
        raw = open(p, "rb").read()
        nl = "\n" if (raw.count(b"\n") and not raw.count(b"\r\n")) else "\r\n"
        lines = raw.decode("gbk").split(nl)
        n = 0
        for i, l in enumerate(lines):
            k = l.strip()
            if k in fixmap:
                lines[i] = l.replace(k, fixmap[k])
                n += 1
                hit_keys.add(k)
        if not n:
            continue
        blob = nl.join(lines).encode("gbk")
        if apply:
            with open(p, "wb") as fh:
                fh.write(blob)
            back = open(p, "rb").read()
            if back != blob:
                raise SystemExit("回读不一致: %s" % f)
            if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
                raise SystemExit("含裸 LF: %s" % f)
        changed_files += 1
        hits_total += n
        print("  %s %-18s %d 处" % ("已写" if apply else "干跑", f, n))

    # ⚠️ 同组同步：命中文件的原文同组成员必须一起改（否则组内不一致）
    need = set()
    for f in os.listdir(ZH):
        if not f.endswith(".txt"):
            continue
        h = md5b(open(os.path.join(SRC, f), "rb").read()) if os.path.exists(os.path.join(SRC, f)) else None
        if h in groups:
            for g in groups[h]:
                need.add(g)
    if apply:
        for f in sorted(need):
            p = os.path.join(ZH, f)
            if not os.path.exists(p):
                continue
            raw = open(p, "rb").read()
            nl = "\n" if (raw.count(b"\n") and not raw.count(b"\r\n")) else "\r\n"
            lines = raw.decode("gbk").split(nl)
            n = 0
            for i, l in enumerate(lines):
                k = l.strip()
                if k in fixmap:
                    lines[i] = l.replace(k, fixmap[k])
                    n += 1
            if n:
                blob = nl.join(lines).encode("gbk")
                with open(p, "wb") as fh:
                    fh.write(blob)
                if open(p, "rb").read() != blob:
                    raise SystemExit("回读不一致: %s" % f)

    print("① .txt：命中文件 %d / 行 %d；唯一键 %d（预期 42）" % (changed_files, hits_total, len(hit_keys)))
    miss = set(fixmap) - hit_keys
    if miss:
        print("  !! 未命中（可能已译或键不符）：%s" % sorted(miss))

    # ② 映射表键去重
    xm = os.path.join(HERE, "comww2-xscn-map.tsv")
    if os.path.exists(xm):
        rows = [l for l in io.open(xm, encoding="utf-8").read().replace("\r\n", "\n").split("\n") if l.strip()]
        head, body = rows[0], rows[1:]
        kept, dropped = [], []
        for l in body:
            c = l.split("\t")
            if c and c[0] in fixmap:
                dropped.append(c[0])
            else:
                kept.append(l)
        print("② 映射表：剔除 %d 条（%s）" % (len(dropped), dropped[:6]))
        if apply:
            with io.open(xm, "w", encoding="utf-8", newline="") as fh:
                fh.write("\n".join([head] + kept) + "\n")

    # ③ 两份保留集移除已译键
    for name in ("label-keep.tsv", "xscn-uniq-final3.tsv"):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        rows = [l for l in io.open(p, encoding="utf-8").read().replace("\r\n", "\n").split("\n") if l.strip()]
        head, body = rows[0], rows[1:]
        kept, dropped = [], []
        for l in body:
            c = l.split("\t")
            if c and c[0] in fixmap:
                dropped.append(c[0])
            else:
                kept.append(l)
        print("③ %s：剔除 %d 条" % (name, len(dropped)))
        if apply:
            with io.open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write("\n".join([head] + kept) + "\n")
    print("完成（%s）" % ("已写盘" if apply else "干跑"))


if __name__ == "__main__":
    main()
