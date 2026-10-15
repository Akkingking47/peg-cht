# -*- coding: utf-8 -*-
"""对子代理产出的 `_prose_rest_dst_partNN.txt` 做**术语一致性**订正。

订正依据（全部来自已交付件实证，不凭常识）：
  1. `COMWW2` label 层（TEXT-ZH 已交付 227 文件）用 **胜利点** 译 `VH`/`Victory Hex`
     ⇒ `.xscn` 映射表同源（`comww2-xscn-map.tsv`）也如此；本层必须跟随。
  2. `comww2-xscn-map.tsv`/`_xscn_dict.tsv` 已有专名：`Jamuga`→亚穆加 · `Woronino`→沃罗尼诺 ·
     `Lysjanka`→利相卡 · `Ostroff`→奥斯特罗夫 · `Plessistyi`→普列西斯蒂 · `Nagyszeben`→纳吉塞本。
  3. 胜利等级全库口径：`BV/DV`→辉煌胜利/决定性胜利 · `V`→胜利 · `TV/MV`→战术胜利/勉强胜利。
  4. `〔存疑〕` 是**译者标注**，不是原文内容 ⇒ 必须删除（不得进入游戏文本）。
  5. 已交付件中无 `〔列兵〕` 这类方括号补注 ⇒ 删除。

用法:
    python fix_prose_rest.py --dry
    python fix_prose_rest.py --apply
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = sorted(f for f in os.listdir(HERE) if re.match(r"^_prose_rest_dst_part\d+\.txt$", f))

# (模式, 替换, 是否正则) 按顺序应用；仅在 **| 之后** 的译文侧替换
REPL = [
    # 译者标注，不是原文
    ("〔存疑〕", "", False),
    ("〔列兵〕", "", False),
    # 胜利点（跟随已交付 label 层口径）
    ("胜利格", "胜利点", False),
    # 胜利等级缩写展开（长模式优先，避免 VHs 被误伤）
    # ⚠️ 口径以**本 efile** 的 `TEXT-ZH\strings_efile.txt [results]` 为准（MECHANICS §30）：
    #    Decisive Victory / Victory / Marginal Victory / Loss → 决定性胜利 / 胜利 / 险胜 / 失败
    ("TV/MV", "险胜", False),
    ("BV/DV", "决定性胜利", False),
    ("勉强胜利", "险胜", False),
    ("战术胜利", "险胜", False),
    # 单字母等级：仅在「获得/可得/得」后的等级语境（连同其前空格一起吃掉）
    (r"(可得|获得|得)\s*BV\b", r"\1辉煌胜利", True),
    (r"(可得|获得|得)\s*DV\b", r"\1决定性胜利", True),
    (r"(可得|获得|得)\s*TV\b", r"\1战术胜利", True),
    (r"(可得|获得|得)\s*MV\b", r"\1勉强胜利", True),
    (r"(可得|获得|得)\s*V\b(?!H)", r"\1胜利", True),
    # 胜利点缩写（连同其两侧空格一起吃掉，避免 `所有 VH` → `所有 胜利点` / `个 VH 可得` → `个胜利点 可得`）
    (r"\s*VHs\s*", "胜利点", True),
    (r"\s*VH\s*", "胜利点", True),
    # 部署格缩写
    (r"\s*DHs\s*", "部署格", True),
    (r"\s*DH\s*", "部署格", True),
    ("部署格（部署格）", "部署格", False),
    # 未知缩写按口径保留，但补一句可读的说明（SH = 己方部署用格）
    ("完全没有我方SH，", "完全没有我方SH（部署格），", False),
    # 专名跟随权威表
    ("雷相卡（Lysjanka）", "利相卡", False),
    ("雷相卡", "利相卡", False),
    ("Jamuga", "亚穆加", False),
    ("Woronino", "沃罗尼诺", False),
    ("Ostroff", "奥斯特罗夫", False),
    ("Plessistyi", "普列西斯蒂", False),
    # 空白卫生
    ("  ", " ", False),
]


def clean(dst):
    s = dst
    for a, b, is_re in REPL:
        s = re.sub(a, b, s) if is_re else s.replace(a, b)
    s = re.sub(r"\s+([，。；：！？、）】》])", r"\1", s)
    s = re.sub(r"([（【《])\s+", r"\1", s)
    # 折叠同义重复（`险胜/险胜` → `险胜`；`决定性胜利/决定性胜利` → 单次）
    s = re.sub(r"([\u4e00-\u9fff]{2,4})/\1", r"\1", s)
    # 等级词收敛到**本 efile** 的 4 级制（`strings_efile.txt [results]`）：
    #   Decisive Victory→决定性胜利 · Victory→胜利 · Marginal Victory→险胜 · Loss→失败
    #   原文里 BV/DV/TV/MV 混用（Panzer General 旧称）⇒ 一律收敛
    s = s.replace("辉煌胜利/决定性胜利", "决定性胜利")
    s = s.replace("辉煌胜利", "决定性胜利")
    s = s.replace("险胜/小胜", "险胜")
    # 基础表遗留的等级串（`gen_prose_zh.py` 的基础表覆盖不到块外条目）
    s = s.replace("战术胜利/险胜", "险胜")
    s = s.replace("战术胜利/微胜", "险胜")

    s = s.strip()
    return s


def main():
    apply = "--apply" in sys.argv
    changed = 0
    for pf in PARTS:
        path = os.path.join(HERE, pf)
        with io.open(path, encoding="utf-8", newline="") as f:
            raw = f.read()
        if raw.startswith("\ufeff"):
            raise SystemExit("BOM: %s" % pf)
        lines = [x for x in raw.replace("\r\n", "\n").split("\n") if x.strip()]
        out = []
        for ln in lines:
            no, sep, dst = ln.partition("|")
            new = clean(dst)
            if new != dst:
                changed += 1
                print("  %s %s\n     - %s\n     + %s" % (pf, no.strip(), dst[:110], new[:110]))
            out.append("%s|%s" % (no, new))
        if apply:
            with io.open(path, "w", encoding="utf-8", newline="") as f:
                f.write("\n".join(out) + "\n")
            back = io.open(path, encoding="utf-8", newline="").read()
            if back.startswith("\ufeff"):
                raise SystemExit("输出含 BOM: %s" % pf)
            got = [x for x in back.replace("\r\n", "\n").split("\n") if x.strip()]
            if len(got) != len(out):
                raise SystemExit("回读行数不一致: %s" % pf)
            for a, b in zip(got, out):
                if a != b:
                    raise SystemExit("回读内容不一致: %s :: %r" % (pf, a[:60]))
    print("%s：订正 %d 行（%s）" % ("已写" if apply else "干跑", changed, "apply" if apply else "dry"))


if __name__ == "__main__":
    main()

