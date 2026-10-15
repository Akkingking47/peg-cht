#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 W20 后半程（用户批准的 **A′**）：删掉**英文原文没有的**「兵器/兵种类别词」。

判据（唯一、可复算）：
    译文含类别词 C，而该条**英文原文里没有与 C 对应的词**（含标准缩写，如 PaK/GMC/ATG/How/FlaK/MGMC）
    ⇒ 删掉 C。英文**已表示**该信息则保留（`PaK`=反坦克炮 / `sFH`=重型榴弹炮 / `GMC`=反坦克炮 等）。
    型号代号（PaK/FK/sFH/K18/K38/M18/Morser/leFH/GrW/sIG…）与载具括注**一字不动**。

⚠️ **两条踩过的坑（已固化为代码约束 + 回归断言）**：
    ① 规则表**必须先长后短**（`反坦克炮` 在 `坦克炮` 前）；
    ② 光有顺序不够 —— 还要**区间占用**：`反坦克炮` 判定保留后，短规则 `坦克炮` 仍会咬同一段，
       留下 `5cm 反`。凡判定保留的片段，其区间被占用，落在其内的规则不得再动。
    ③ 删类别词**不能留下光秃秃的「自行」** ⇒ 「自行X炮」整体列出。

纪律：默认 dry-run；`--apply` 才写；写前备份 `.pre-w20b`；写后回读校验；幂等；回归断言不过则拒绝落盘。
"""
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
MAP = os.path.join(RES, "ww2-eqp-map.tsv")
BAK = MAP + ".pre-w20b"
LOG = os.path.join(RES, "_eqp-typeword-strip.tsv")

_AA = r"(?:AA|FlaK|MGMC|FlakPz|20/65|61-K|obr\.38|Quad|M1A1|M15A1|M16)"
RU = r"(?i)(?:^|[^A-Za-z0-9])"
#    (要删的中文片段, 英文原文中表示「原文已有该信息」的正则)   ⚠️ 顺序 = 长词优先（先复合后单元）
RULES = [
    ("自行重型步兵炮", RU + r"sIG"),
    ("自行反坦克炮", RU + r"(Jgd|Jagd|PzJgd|GMC)"),
    ("自行榴弹炮", RU + r"HMC"),
    ("自行步兵炮", RU + r"sIG"),
    ("自行火炮", r"$^"),                       # 英文从未写「自行火炮」⇒ 一律删
    ("自行高炮", _AA),
    ("重型榴弹炮", RU + r"sFH"),
    ("轻型榴弹炮", RU + r"leFH"),
    ("轻型加农炮", RU + r"leFK"),
    ("重型步兵炮", RU + r"sIG"),
    ("反坦克炮", RU + r"(ATG|AT\s*Gun|anti-?tank|PaK|Pzjgr|GMC)"),
    ("加农炮", RU + r"(gun|Gun|kanone|K18|K38|K39|K02|K34|FK\b|FG\b)"),
    ("高射炮", _AA),
    ("高炮", _AA),
    ("榴弹炮", RU + r"Ho"),
    ("臼炮", RU + r"Morser"),
    ("火箭炮", RU + r"(rocket|NbWf|Wurf)"),
    ("迫击炮", RU + r"(mortar|GrW)"),
    ("野战炮", RU + r"field\s*gun"),
    ("步兵炮", RU + r"Grille"),
    ("坦克炮", RU + r"tank\s*gun"),
    ("炮兵", RU + r"(ARTY|Artillery)"),
    ("机枪", RU + r"(MG|machine\s*gun|Bren)"),
]

# 回归断言：英文原文 → (现译文, 期望译文)
REGRESSION = [
    # —— 保留（英文已有对应词）——
    ("5cm PaK w/Wagon", "5cm 反坦克炮（马车牵引）", "5cm 反坦克炮（马车牵引）"),
    ("12.8cm PaK44 w/251/1", "12.8cm PaK44 反坦克炮（SdKfz 251/1）", "12.8cm PaK44 反坦克炮（SdKfz 251/1）"),
    ("15 sFH 18  w/251/1", "15 sFH 18 重型榴弹炮（SdKfz 251/1）", "15 sFH 18 重型榴弹炮（SdKfz 251/1）"),
    ("10.5 leFH18m w/Carro", "10.5 leFH18m 轻型榴弹炮（车辆牵引）", "10.5 leFH18m 轻型榴弹炮（车辆牵引）"),
    ("8.8 FK18 ATG w/251/1", "8.8 FK18 反坦克炮（SdKfz 251/1）", "8.8 FK18 反坦克炮（SdKfz 251/1）"),
    ("M16 MGMC", "M16 自行高炮", "M16 自行高炮"),
    ("M15A1 MGMC", "M15A1 自行高炮", "M15A1 自行高炮"),
    ("FlaKPz IV Wirbelwind", "旋风自行高炮", "旋风自行高炮"),
    ("M3 GMC", "M3 自行反坦克炮", "M3 自行反坦克炮"),
    ("JgdPz IV/48", "IV 号自行反坦克炮 L/48", "IV 号自行反坦克炮 L/48"),
    ("JgdPanther", "黑豹自行反坦克炮", "黑豹自行反坦克炮"),
    ("T19 HMC", "T19自行榴弹炮", "T19自行榴弹炮"),
    ("Bunker Artillery", "掩体炮兵", "掩体炮兵"),
    ("88 mm ARTY w/251/1", "88 mm 炮兵（SdKfz 251/1）", "88 mm 炮兵（SdKfz 251/1）"),
    ("MG Infanterie w/251/1", "机枪步兵（SdKfz 251/1）", "机枪步兵（SdKfz 251/1）"),
    ("sIG33 38(t)M", "sIG33 38(t)M 重型步兵炮运载车", "sIG33 38(t)M 重型步兵炮运载车"),
    ("sIG IB Bison", "IB 野牛自行重型步兵炮", "IB 野牛自行重型步兵炮"),
    # —— 删除（英文没有该信息）——
    ("25mm SA34 w/Charrette", "25mm SA34 反坦克炮（马车牵引）", "25mm SA34（马车牵引）"),
    ("17 Pdr w/Truck", "17 磅反坦克炮（卡车牵引）", "17 磅（卡车牵引）"),
    ("21cm M18 w/LKW", "21cm M18 臼炮（卡车牵引）", "21cm M18（卡车牵引）"),
    ("3.7 inch w/Truck", "3.7 英寸高炮（卡车牵引）", "3.7 英寸（卡车牵引）"),
    ("20mm w/Truck", "20mm 高炮（卡车牵引）", "20mm（卡车牵引）"),
    ("PzA IV Hummel", "野蜂自行榴弹炮", "野蜂"),
    ("PzA II Wespe", "黄蜂自行榴弹炮", "黄蜂"),
    ("T30 HMC", "T30 自行榴弹炮", "T30 自行榴弹炮"),
    ("Sem 90/53", "Sem 90/53 自行火炮", "Sem 90/53"),
    ("Grille", "蟋蟀自行步兵炮", "蟋蟀"),
    ("Marder IIIM", "黄鼠狼 IIIM 自行反坦克炮", "黄鼠狼 IIIM"),
    ("SS JgdPanther", "党卫军黑豹自行反坦克炮", "党卫军黑豹自行反坦克炮"),
    ("Marder IIK", "黄鼠狼 IIK 自行反坦克炮", "黄鼠狼 IIK"),
    ("JagdTiger", "猎虎自行反坦克炮", "猎虎自行反坦克炮"),
    ("Marder IIIH", "黄鼠狼 IIIH 自行反坦克炮", "黄鼠狼 IIIH"),
    ("Grille 88mm FlaK 41", "蟋蟀 88mm FlaK 41 自行高炮", "蟋蟀 88mm FlaK 41 自行高炮"),
    ("75mm FH M1A1 w/Truck", "75mm FH M1A1 榴弹炮（卡车牵引）", "75mm FH M1A1（卡车牵引）"),
    ("Hurricane II/Handley Page Halifax MkI Air Support", "飓风 II/Handley Page 哈利法克斯 MkI 空中支援",
     "飓风 II/Handley Page 哈利法克斯 MkI 空中支援"),
    ("Infantry", "步兵", "步兵"),
]

_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def transform(en, zh):
    """删掉英文原文没有的类别词。**区间占用**防「先长后短」之外的重叠再咬（见模块 docstring）。"""
    removed = []
    out = zh
    used = []
    for word, keep_pat in RULES:
        i = out.find(word)
        if i < 0:
            continue
        j = i + len(word)
        if any(not (j <= a or i >= b) for a, b in used):
            continue
        if re.search(keep_pat, en):
            used.append((i, j))
            continue
        out = out[:i] + out[j:]
        removed.append(word)
        used = [(a - len(word), b - len(word)) if a >= j else (a, min(b, i)) for a, b in used]
    out = re.sub(r"（\s*）", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out).strip()
    out = re.sub(r"\s+（", "（", out)
    return out, removed


def regression():
    bad = []
    for en, cur, want in REGRESSION:
        got, _ = transform(en, cur)
        if got != want:
            bad.append((en, cur, want, got))
    print("== 回归断言（%d 条）==" % len(REGRESSION))
    if bad:
        print("  ❌ 失败 %d 条：" % len(bad))
        for en, cur, want, got in bad:
            print("     %-42s 旧=%r 期望=%r 得到=%r" % (en[:42], cur, want, got))
    else:
        print("  ✅ 全部通过")
    return not bad


def main():
    apply_ = "--apply" in sys.argv
    ok = regression()
    if not ok and apply_:
        print("\n  ⛔ 回归断言未过 ⇒ 拒绝落盘")
        return 1
    raw = open(MAP, encoding="utf-8-sig").read().split("\n")
    out, hits = [], []
    for i, l in enumerate(raw):
        if not l.strip() or l.startswith("#"):
            out.append(l)
            continue
        f = l.split("\t")
        if len(f) < 3 or not re.search(r"[\u4e00-\u9fff]", f[1]):
            out.append(l)
            continue
        new, removed = transform(f[0], f[1])
        if removed and new and new != f[1]:
            old = f[1]
            f[1] = new
            f[2] = (f[2] + "+W20类别词") if f[2].strip() else "W20类别词"
            hits.append((i + 1, f[0], old, new, removed))
            out.append("\t".join(f))
        else:
            out.append(l)
    print()
    print("=" * 116)
    print(f"W20/A′ 删类别词  真源={os.path.relpath(MAP, WS)}  模式={'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print("=" * 116)
    print(f"  命中 {len(hits)} 行")
    for no, en, oz, nz, rm in hits:
        print("   行%-5d 删%-14s %2d→%2d字  %-34s 【旧】%s" % (no, "+".join(rm), len(oz), len(nz), nz, oz[:34]))
    if hits:
        lens = sorted(len(nz) for _, _, _, nz, _ in hits)
        print(f"\n  改动后长度：最短 {lens[0]} / 中位 {lens[len(lens)//2]} / 最长 {lens[-1]}")
    else:
        print("  （无命中：幂等）")
    if apply_:
        if not os.path.isfile(BAK):
            shutil.copy2(MAP, BAK)
            print(f"\n  备份 ⇒ {os.path.relpath(BAK, WS)}")
        with open(MAP, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
        back = open(MAP, encoding="utf-8-sig").read().split("\n")
        print(f"  回读：行数 {len(back)}（原 {len(raw)}）{'✅' if len(back) == len(raw) else '❌'}")
        if not os.path.isfile(LOG):
            with open(LOG, "w", encoding="utf-8", newline="\n") as f:
                f.write("# W20/A′ 类别词删除留痕\n真源行号\t英文原文\t原译文\t新译文\t删除词\t原字数\t新字数\n")
        with open(LOG, "a", encoding="utf-8", newline="\n") as f:
            for no, en, oz, nz, rm in hits:
                f.write(f"{no}\t{en}\t{oz}\t{nz}\t{'|'.join(rm)}\t{len(oz)}\t{len(nz)}\n")
        print(f"  留痕 ⇒ {os.path.relpath(LOG, WS)}")
    else:
        print("\n  ⇒ dry-run，未写入。加 --apply 落盘。")
    return 0 if ok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.join(RES, "evidence"), exist_ok=True)
    with open(os.path.join(RES, "evidence", "w20b-typeword-strip.txt"), "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
