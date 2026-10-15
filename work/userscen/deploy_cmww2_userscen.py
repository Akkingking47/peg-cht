# -*- coding: utf-8 -*-
r"""COMWW2 `USERSCEN` 层交付（2026-09-30）。

三层一起做（这是**全库首个被汉化的 USERSCEN**）：
  1. 2 个 `.xscn` **标题**（原地改，走 `userscen_tool.py apply`）
  2. 2 个 `.ply` 简报 → `TEXT-ZH\\USERSCEN\\`
  3. 2 个 `readme-*.txt` → `TEXT-ZH\\USERSCEN\\`

硬约束：`.ply`/`.txt` 逐文件沿用**自己的**换行；GBK 无 BOM；原文侧只读。

用法: python deploy_cmww2_userscen.py [--dry]
"""
import importlib.util
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
US = r"D:\OpenPG2\EFILE_COMWW2\USERSCEN"
TZH = r"D:\OpenPG2\EFILE_COMWW2\TEXT-ZH\USERSCEN"
MAP = os.path.join(HERE, "cmww2-userscen-title-map.tsv")

# ---- ① 标题（src 由脚本从文件实读校验，不手抄）----
TITLES = {
    "khalkin1.xscn": "哈拉哈河1：日军进攻",
    "khalkin2.xscn": "哈拉哈河2：朱可夫突击",
}

# ---- ② 简报正文（**只给中间文字**，前后白空由脚本从原文继承）----
PLY_MID = {
    "khalkin1_i.ply":
        "整个6月，不断有报告称苏蒙军队在诺门罕附近河流两岸活动，并对孤立的满洲国部队发动了小规模袭击。"
        "月底，日军第23步兵师团长小松原道太郎中将获准「驱逐入侵者」。日军的计划是两路夹击。"
        "三个联队外加第四个联队的一部——其中包括第23师团的两个联队（第71、第72步兵联队，"
        "以及第64步兵联队的一个大队）——以及从第7步兵师团借调、由角田新一郎大佐指挥的第26步兵联队，"
        "将越过哈拉哈河，消灭西岸拜恩查干山上的苏军，然后左转向南推进至川渡桥。"
        "第二路攻击由日本帝国陆军第1战车团（第1战车团，即安冈支队）承担，"
        "下辖第3、第4战车联队，第64步兵联队一部，从第7步兵师团抽调的第28步兵联队一个大队，"
        "第24工兵联队，以及第13野战炮兵联队一个大队，全部由安冈正臣中将统一指挥。"
        "这支部队将攻击哈拉哈河东岸、霍尔斯坦河以北的苏军。日军的两路攻势打算在两翼会合。",
    "khalkin2_i.ply":
        "朱可夫认定，打破僵局的时机到了。1939年8月20日5时45分，苏军炮兵与557架战斗机和轰炸机"
        "袭击了日军阵地，这是苏联空军史上第一次战斗轰炸机攻势。约5万名苏蒙士兵——隶属第57特别军——"
        "防守着哈拉哈河东岸。三个步兵师和一个坦克旅在密集炮火与苏联空军的支援下渡河。"
        "日军被苏军中央部队的进攻钉住之后，苏军装甲部队横扫两翼，从后方攻击日军，"
        "完成了一次经典的双重包围。8月25日，苏军两翼在诺门罕村会合，日军第23步兵师团陷入重围。"
        "8月26日，日军为解救第23师团发起的反击失败。8月27日，第23师团试图突围，同样失败。"
        "被围部队拒绝投降后，再次遭到炮击与空袭。到8月31日，蒙古一侧边境上的日军已被消灭，"
        "只剩下满洲一侧第23师团的残部。苏军达成了自己的目标。",
}

# ---- ③ readme（逐行对应，不继承白空：内容本身即全文）----
TXT_LINES = {
    "readme-khalkin1.txt": [
        "Open General 剧本",
        "",
        "「哈拉哈河：日军进攻」",
        "",
        "E-File：综合版（COMWW2）",
        "",
        "Laurent Mennier",
        "",
        "2015",
    ],
    "readme-khalkin2.txt": [
        "Open General 剧本",
        "",
        "「哈拉哈河2：朱可夫突击」",
        "",
        "E-File：综合版（COMWW2）",
        "",
        "作者：Laurent Mennier",
        "",
        "2015",
    ],
}


def detect_nl(raw):
    return "\n" if (raw.count(b"\n") > 0 and raw.count(b"\r\n") == 0) else "\r\n"


def write_blob(path, blob, nl):
    with open(path, "wb") as f:
        f.write(blob)
    back = open(path, "rb").read()
    if back != blob:
        raise SystemExit("回读不一致: %s" % path)
    if back[:3] == b"\xef\xbb\xbf":
        raise SystemExit("含 BOM: %s" % path)
    if nl == "\r\n" and back.count(b"\n") != back.count(b"\r\n"):
        raise SystemExit("含裸 LF: %s" % path)
    if nl == "\n" and back.count(b"\r\n"):
        raise SystemExit("混入 CRLF: %s" % path)


def main():
    dry = "--dry" in sys.argv
    os.makedirs(TZH, exist_ok=True)

    # ① 标题 map（src 实读）
    spec = importlib.util.spec_from_file_location(
        "u", os.path.join(HERE, "userscen_tool.py"))
    u = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(u)
    rows = []
    for f, dst in TITLES.items():
        _, _, src, _ = u.read_title(os.path.join(US, f))
        rows.append((f, src, dst))
        print("  标题 %-16s %r -> %r" % (f, src, dst))
    with io.open(MAP, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("file\tsrc\tdst\n")
        for f, s, d in rows:
            fh.write("%s\t%s\t%s\n" % (f, s, d))
    print("  → %s（BOM=%s）" % (MAP, open(MAP, "rb").read(3) == b"\xef\xbb\xbf"))

    # ② .ply：中间文字 + 继承白空
    for f, mid in PLY_MID.items():
        raw = open(os.path.join(US, f), "rb").read()
        nl = detect_nl(raw)
        src = raw.decode("cp1252")
        # 逐行：本层每个 .ply 只有「正文行」一种实义行
        lead = src[:len(src) - len(src.lstrip("\r\n"))]
        trail = src[len(src.rstrip("\r\n")):]
        dst = lead + mid + trail
        blob = dst.encode("gbk")
        if nl == "\r\n":
            blob = blob.replace(b"\r\n", b"\r\n")
        if not dry:
            write_blob(os.path.join(TZH, f), blob, nl)
        print("  %s %-18s %4dB -> %4dB（%s，%d 汉字）"
              % ("已写" if not dry else "干跑", f, len(raw), len(blob),
                 "CRLF" if nl == "\r\n" else "LF",
                 sum(1 for c in dst if "\u4e00" <= c <= "\u9fff")))

    # ③ .txt：逐行
    for f, lines in TXT_LINES.items():
        raw = open(os.path.join(US, f), "rb").read()
        nl = detect_nl(raw)
        src_lines = raw.decode("cp1252").split(nl)
        if len(src_lines) != len(lines):
            raise SystemExit("%s 行数不符：原文 %d / 译文 %d" % (f, len(src_lines), len(lines)))
        dst = nl.join(lines)
        blob = dst.encode("gbk")
        if not dry:
            write_blob(os.path.join(TZH, f), blob, nl)
        print("  %s %-18s %4dB -> %4dB（%s，%d 行）"
              % ("已写" if not dry else "干跑", f, len(raw), len(blob),
                 "CRLF" if nl == "\r\n" else "LF", len(lines)))
    print("干跑完成（未写盘）" if dry else "全部写出")


if __name__ == "__main__":
    main()
