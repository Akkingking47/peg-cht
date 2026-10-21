# -*- coding: utf-8 -*-
r"""番号展开 · 收口落盘器（幂等 · 默认 dry-run · --apply 才写）

背景（2026-10-20 复核实测）：
  `_番号展开-对照表-20261020.tsv` 共 6414 行，其中**处置=译 5854 行**，
  但实测这些「译」行的**原文行根本没进 `ww2-scn-map.tsv`** ⇒ 游戏里 `64/16`/`5/4`/`105/72`
  这类纯数字番号**仍是原文**。本脚本把「已裁定」的译法整行落到值模式真源。

输入：
  pegww2/research/_番号展开-对照表-20261020.tsv
  pegww2/research/ww2-scn-map.tsv
产出：
  research/_番号收口-定词表-20261020.tsv   未解 token 的裁决 + 依据
  research/_番号收口-落盘表-20261020.tsv   逐行「真源现值 → 新值」（只列实需改动）
  research/_番号收口-冲突表-20261020.tsv   同一原文行给出多译法的行（值模式无法承载 ⇒ 待 per-file 覆盖）

落地口径：
  ① 处置=译          → 直接用「建议译法」（该档生成时已无未解 token）
  ② 处置=舰名/部分待判/待判 → 用裁决器替换后**再无残留拉丁 token**者才落
  ③ 处置=保留        → 不落（本即「原样保留」）
  ④ 同一原文行出现多译法 → 不落，登记冲突表（值模式整行键控承载不了）
"""
import io
import os
import re
import shutil
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
DER = os.path.join(RES, "_derived")          # 生成器产出（可复算，勿手改；见 research/README.md）
TBL = os.path.join(DER, "_番号展开-对照表-20261020.tsv")
MAP = os.path.join(RES, "ww2-scn-map.tsv")
os.makedirs(DER, exist_ok=True)
PEND = ("舰名待译", "部分待判", "待判")

CJK = re.compile(r"[\u4e00-\u9fff]")
SEP = re.compile(r"(\s+|/)")

# ── 裁决表（每条都有仓内实证；无据一律保留） ──────────────────────────────
DECIDE = [
    (r"\d+PJ", lambda m: "第" + m.group(0)[:-2] + "反坦克营",
     "token PJ→反坦克营(share 1.00)；行 PJ/5 Panzer→反坦克营/第5装甲师"),
    (r"LW", lambda m: "空军", "token LW→空军(share 1.00)"),
    (r"RN", lambda m: "皇家海军", "RN=Royal Navy；与 HMS/KMS/USS/ITS 同属军种前缀口径"),
    (r"Niciloso Da Recco", lambda m: "尼科洛索·达雷科号", "意大利航海家级驱逐舰，音译+号"),
    (r"Antonio Pigafetta", lambda m: "安东尼奥·皮加费塔号", "意大利航海家级驱逐舰，音译+号"),
    (r"Giovanni Di Verazza", lambda m: "乔瓦尼·达·韦拉扎诺号", "意大利航海家级驱逐舰 Giovanni da Verrazzano"),
    (r"Lanzerotto Malocell", lambda m: "兰泽罗托·马洛切洛号", "意大利航海家级驱逐舰 Lanzerotto Malocello"),
    (r"Tazzoli", lambda m: "塔佐利号", "意大利潜艇 Tazzoli，音译+号"),
    (r"L\.Malocello", lambda m: "L.马洛切洛号", "同上舰，短名形式"),
    (r"Alpino", lambda m: "阿尔皮诺号", "意大利士兵级驱逐舰 Alpino，音译+号"),
    (r"Andrea Doria", lambda m: "安德烈亚·多里亚号", "意大利战列舰 Andrea Doria，音译+号"),
    (r"Duca degli Abruzzi", lambda m: "阿布鲁佐公爵号", "意大利轻巡 Duca degli Abruzzi，音译+号"),
    (r"C\.Mirabello", lambda m: "C.米拉贝洛号", "意大利侦察舰 C. Mirabello，音译+号"),
    (r"Squalo", lambda m: "斯夸洛号", "意大利潜艇 Squalo，音译+号"),
    (r"Bismarck", lambda m: "俾斯麦号", "德国战列舰 Bismarck，音译+号"),
    (r"Scharnhorst", lambda m: "沙恩霍斯特号", "德国战列舰 Scharnhorst，音译+号"),
    (r"Achilles", lambda m: "阿基里斯号", "英国轻巡 HMS Achilles，音译+号"),
    (r"SMG", lambda m: "意潜艇", "行 SMG Giada→意潜艇贾达号（既有译法）"),
]
SUBST = sorted(DECIDE, key=lambda x: -len(x[0].replace("\\", "")))


def unresolved(orig, prop):
    o = [t for t in SEP.split(orig) if t and not SEP.fullmatch(t)]
    out = []
    for t in SEP.split(prop):
        if not t.strip() or SEP.fullmatch(t) or CJK.search(t):
            continue
        if re.fullmatch(r"[-\[\]0-9]+", t):
            continue
        if t in o and t not in out:
            out.append(t)
    return out


def resolve(prop):
    new = prop
    for rx, fn, _why in SUBST:
        new = re.sub(r"(?<![A-Za-z0-9])" + rx + r"(?![A-Za-z0-9])", fn, new)
    new = re.sub(r"意潜艇\s+", "意潜艇", new)
    new = re.sub(r"意海军\s+", "意海军", new)
    return re.sub(r"\s{2,}", " ", new).strip()


# ── 读对照表 ──────────────────────────────────────────────────────────────
rows = []
for i, raw in enumerate(io.open(TBL, encoding="utf-8")):
    if i == 0 or raw.startswith("#"):
        continue
    f = raw.rstrip("\r\n").split("\t")
    if len(f) >= 10:
        rows.append(f)

tokstat = defaultdict(lambda: {"n": 0, "nat": Counter(), "dec": None, "why": ""})
for f in rows:
    if f[8] not in PEND:
        continue
    for t in unresolved(f[5], f[6]):
        e = tokstat[t]
        e["n"] += 1
        e["nat"][f[0]] += 1
        if e["dec"] is None:
            if re.fullmatch(r"[Uu]-\d+", t):
                e["dec"], e["why"] = None, "德军 U 艇番号，中文惯例原样保留"
            else:
                for rx, fn, why in DECIDE:
                    if re.fullmatch(rx, t):
                        e["dec"], e["why"] = fn(None) if False else fn(re.match(rx, t)), why
                        break
                else:
                    e["dec"], e["why"] = None, "仓内无 CJK 先例 / 跨义冲突 ⇒ 保留原文"

# ── 逐行汇总（原文行 → 候选译法集合） ─────────────────────────────────────
#  ⚠️ 纯数字键（单段裸数字，如 `16`/`100`）**不落**：`ingest_layers.load_pairs` 会跳过
#     纯数字 en 键（既有约定，防噪声），落了会让 layer_gate 报「缺失 N」而拒绝构建。
cand = defaultdict(set)
numskip = []
for f in rows:
    orig, prop, disp = f[5], f[6], f[8]
    if not orig.strip():
        continue
    if disp == "译":
        v = prop.strip()
    elif disp in PEND:
        v = resolve(prop)
        if v and unresolved(orig, v):
            v = ""
    else:
        v = ""
    if not v or v == orig:
        continue
    if re.fullmatch(r"\d+", orig):
        numskip.append((orig, v))
        continue
    cand[orig].add(v)

conf = {k: sorted(v) for k, v in cand.items() if len(v) > 1}
ok = {k: sorted(v)[0] for k, v in cand.items() if len(v) == 1}

# ── 读真源 ────────────────────────────────────────────────────────────────
raw = io.open(MAP, encoding="utf-8-sig", newline="").read()
nl = "\r\n" if "\r\n" in raw else "\n"
lines = raw.replace("\r\n", "\n").split("\n")
idx = {ln.split("\t")[0]: i for i, ln in enumerate(lines) if ln.strip() and not ln.startswith("#")}
upd, add, same = [], [], []
for k in sorted(ok):
    if k in idx:
        cur = lines[idx[k]].split("\t")[1]
        (same if cur == ok[k] else upd).append(k if cur == ok[k] else (k, cur, ok[k]))
    else:
        add.append((k, ok[k]))

# ── 定词表 ────────────────────────────────────────────────────────────────
dt = os.path.join(DER, "_番号收口-定词表-20261020.tsv")
with io.open(dt, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 番号残留待判 · 收口定词表（依据全部取自仓内实测/既有译法，无据者一律保留）\n")
    fh.write("token\t行数\t国别分布\t裁决\t依据\n")
    for t in sorted(tokstat, key=lambda k: (-tokstat[k]["n"], k)):
        e = tokstat[t]
        natd = "/".join("%s%d" % kv for kv in e["nat"].most_common(3))
        fh.write("%s\t%d\t%s\t%s\t%s\n" % (t, e["n"], natd,
                 ("译：" + e["dec"]) if e["dec"] else "保留", e["why"]))
print("定词表：%s（token %d：译 %d / 保留 %d）" % (os.path.basename(dt), len(tokstat),
      sum(1 for k in tokstat if tokstat[k]["dec"]), sum(1 for k in tokstat if not tokstat[k]["dec"])))

# ── 落盘表 / 冲突表 ───────────────────────────────────────────────────────
lp = os.path.join(DER, "_番号收口-落盘表-20261020.tsv")
with io.open(lp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 番号收口 · 落盘表（真源现值 → 新值；只列**实需改动**）\n原文行\t真源现值\t新值\n")
    for k, o, n in sorted(upd):
        fh.write("%s\t%s\t%s\n" % (k, o, n))
cp = os.path.join(DER, "_番号收口-冲突表-20261020.tsv")
with io.open(cp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 番号收口 · 同原文行多译法（值模式整行键控承载不了 ⇒ 须走 per-file 覆盖）\n原文行\t候选译法\n")
    for k in sorted(conf):
        fh.write("%s\t%s\n" % (k, " | ".join(conf[k])))
print("落盘表：%s（待更新 %d · 待新增 %d · 已一致 %d）" % (os.path.basename(lp), len(upd), len(add), len(same)))
print("冲突表：%s（%d 行同键多译，已剔除不落）" % (os.path.basename(cp), len(conf)))
np_ = os.path.join(DER, "_番号收口-纯数字键未落-20261020.tsv")
with io.open(np_, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("# 单段裸数字键（如 16）/ 拟译（**不落真源**：词库 ingest 跳过纯数字键，落了会被 layer_gate 拒）\n原文行\t拟译\n")
    for k, v in sorted(set(numskip)):
        fh.write("%s\t%s\n" % (k, v))
print("纯数字键未落表：%s（%d 行）" % (os.path.basename(np_), len(set(numskip))))
for k in sorted(conf)[:5]:
    print("  ! %s -> %s" % (k, " | ".join(conf[k])))

# ── 写回 ──────────────────────────────────────────────────────────────────
APPLY = "--apply" in sys.argv
if not APPLY:
    print("\n(dry-run，未写入 %s；确认后加 --apply)" % MAP)
    sys.exit(0)

bk = MAP + ".pre-desig-close"
if not os.path.exists(bk):
    shutil.copy2(MAP, bk)
    print("备份 → %s" % bk)
for k, _o, n in upd:
    c = lines[idx[k]].split("\t")
    c[1] = n
    lines[idx[k]] = "\t".join(c)
for k, n in add:
    lines.append("%s\t%s\t番号收口" % (k, n))
io.open(MAP, "w", encoding="utf-8-sig", newline="").write(nl.join(lines))
print("已写 %s（%d 行 → %d 行）" % (MAP, len(lines) - len(add), len(lines)))

# ── 回读校验 ──────────────────────────────────────────────────────────────
raw2 = io.open(MAP, encoding="utf-8-sig", newline="").read().replace("\r\n", "\n").split("\n")
idx2 = {ln.split("\t")[0]: ln.split("\t")[1] for ln in raw2 if ln.strip() and not ln.startswith("#")}
bad = [k for k in ok if idx2.get(k) != ok[k]]
print("回读：应生效 %d 行 · 不一致 %d %s" % (len(ok), len(bad), bad[:5]))
sys.exit(1 if bad else 0)
