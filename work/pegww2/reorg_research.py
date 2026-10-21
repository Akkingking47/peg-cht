# -*- coding: utf-8 -*-
r"""PeG-WW2 · research/ 资产整理 v2（判据升级）

**为什么换判据**（v1 的教训）：v1 用「零入引用」，结果 149 个文件只减了 68——
因为「被 README 提过一句」也被当成引用。对方目标是**减少上下文成本**，
真正的判据是「**下一次工作要不要直接打开它**」：

  ① **源码功能依赖（脚本运行时按路径读）** ⇒ 留顶层（真源 / 输入 / 填表）
  ② **脚本生成它（派生）** ⇒ 移 `research/_derived/`（可复算，勿手改；生成器已重定向）
  ③ **同族同构小表** ⇒ **合并成 1 个**（+ `src` 列）后归档到 `_superseded/merged/`
  ④ **历史留痕（仅被文档提及）** ⇒ 归档 `_superseded/retired/`（可逆，不删）

用法：
  python reorg_research.py            # dry-run：出完整计划 + 落点统计
  python reorg_research.py --apply    # 执行（移动 + 合并 + 写留痕）
"""
import hashlib
import io
import os
import re
import shutil
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WS = r"D:\DSH\军事游戏汉化"
R = os.path.join(WS, "pegww2", "research")
SUP = os.path.join(R, "_superseded")
DER = os.path.join(R, "_derived")
APPLY = "--apply" in sys.argv

# ── ① 留顶层：真源 / 填表 / 支撑 / 人读（显式清单，白名单） ────────────────
KEEP = {
    # 真源（改了才生效）
    "ww2-scn-map.tsv", "ww2-eqp-map.tsv", "WW2Gui-map.tsv", "WW2Misc-map.tsv",
    "WW2Tips-map.tsv", "WW2NAME-map.tsv", "_scn-file-overrides.tsv",
    "unit-abbr-map.tsv", "banned.tsv", "policy-keep-non-gb2312.tsv",
    # 人工填表（下一次改动会直接编辑它）
    "WW2Gui-fill.tsv", "WW2Misc-fill.tsv", "WW2Tips-fill.tsv", "WW2NAME-fill.tsv",
    "ww2-eqp-fill.tsv", "_desc-authored.tsv",
    # 生成器输入 / 支撑表
    "_scn-国别.tsv", "_u-position-ladder.tsv", "_场景国籍精确归属-20261020.tsv",
    "_场景列表台账.tsv", "_场景列表_最终序号.md", "_场景列表分组编号提案.tsv",
    "各国军语风格口径.md",
    # 口径资产（被 `方法/` 引用为定稿样本）
    "_scn-sample.tsv", "_scn-sample-nations.tsv", "_scn-sample-west.tsv",
    "_scn-sample-west-zh.tsv", "_scn-sample-zh.tsv",
    # 人读
    "README.md", "进度-场景层.md", "实机复测清单-场景层.md",
    "_同类译法问题-审计.md", "_审核报告-终态-20261019.md",
    # 交付物
    "番号展开-对照表-20261020.xlsx",
}

# ── ② 派生物（脚本会重生成 ⇒ 移 _derived/，勿手改） ──────────────────────
DERIVED = [
    r"_u-token-map-mined\.tsv", r"_u-line-map-mined\.tsv",
    r"_番号展开-对照表-20261020\.tsv",
    r"_番号-字母后缀码-待判清单-20261020\.tsv",
    r"_番号-有意保留代号清单-20261020\.tsv",
    r"_番号-舰名碎片-并入清单-20261020\.tsv",
    r"_番号未展开统计-20261020\.tsv",
    r"_番号未展开统计-按SCN国籍-20261020\.tsv",
    r"_番号未展开统计-按SCN国籍v2-20261020\.tsv",
    r"_番号收口-[^/]+\.tsv",
    r"_scn-stats\.tsv",
    r"_对照-[^/]+\.tsv",
]

# ── ③ 同族同构小表 ⇒ 合并（族名, 正则, 汇总名） ──────────────────────────
MERGE = [
    ("scn-fill-autofix", re.compile(r"^_scn-fill-autofix-[^/]+\.tsv$"),
     "_scn-fill-autofix-汇总.tsv"),
    ("审核-终态-20261019", re.compile(r"^_审核-终态-20261019-[^/]+\.tsv$"),
     "_审核-终态-20261019-汇总.tsv"),
]

# ── ④ 其余历史留痕 ⇒ retired/（安全网：不在以上三类的**全部归档**） ────────
ROOT_MD_KEEP = {"README.md"}


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def read_lines(p):
    return [l.rstrip("\r\n") for l in io.open(p, encoding="utf-8")]


def merge_family(rx, outname):
    """同构表合并：跳过 `#` 注释，统一表头，追加 `源文件` 列。"""
    files = sorted(f for f in os.listdir(R) if rx.match(f))
    if not files:
        return None, [], []
    header, rows, seen = None, [], []
    for fn in files:
        ls = [l for l in read_lines(os.path.join(R, fn)) if not l.startswith("#")]
        if not ls:
            seen.append(fn)
            continue
        if header is None:
            header = ls[0]
        elif ls[0] != header:
            seen.append(fn + "(表头不同)")
            continue
        for l in ls[1:]:
            if l.strip():
                rows.append(l.split("\t") + [fn])
        seen.append(fn)
    if not rows:
        return None, [], seen
    dst = os.path.join(SUP, "merged", outname)
    if APPLY:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with io.open(dst, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# 同族合并汇总（reorg_research.py v2）· 源文件列见末列\n")
            fh.write("\t".join(header.split("\t") + ["源文件"]) + "\n")
            fh.write("\n".join("\t".join(r) for r in rows) + "\n")
    return dst, rows, seen


# ── 计划 ─────────────────────────────────────────────────────────────────
files = [f for f in sorted(os.listdir(R)) if os.path.isfile(os.path.join(R, f))]
plan = {}
for f in files:
    if f in KEEP:
        plan[f] = "keep"
    elif any(re.match(rx, f) for rx in DERIVED):
        plan[f] = "derived"
    elif any(rx.match(f) for _n, rx, _o in MERGE):
        plan[f] = "merge"
    else:
        plan[f] = "retired"

print("== research/ 顶层 %d 个 → 计划 ==" % len(files))
cnt = defaultdict(int)
for f in files:
    cnt[plan[f]] += 1
for k in ("keep", "derived", "merge", "retired"):
    print("   %-8s %d" % (k, cnt[k]))
print("\n[keep] 留顶层（%d）：%s" % (cnt["keep"], ", ".join(sorted(f for f in files if plan[f] == "keep"))))
print("\n[derived] → _derived/：%s" % ", ".join(sorted(f for f in files if plan[f] == "derived")))
print("\n[merge] → _superseded/merged/：%s" % ", ".join(sorted(f for f in files if plan[f] == "merge")))
print("\n[retired] → _superseded/retired/ 共 %d 个（末尾列全）" % cnt["retired"])
ret = sorted(f for f in files if plan[f] == "retired")
for i in range(0, len(ret), 4):
    print("   " + "  ".join("%-34s" % x for x in ret[i:i + 4]))

tgt = cnt["keep"] + 1        # + 新增 _derived/README.md 不算顶层
print("\n预计顶层：%d → **%d**（_derived/ 另计 %d · _superseded/merged %d）"
      % (len(files), cnt["keep"], cnt["derived"], cnt["merge"]))
if not APPLY:
    print("\n(dry-run，未改任何文件；确认后加 --apply)")
    sys.exit(0)

# ── 执行 ─────────────────────────────────────────────────────────────────
os.makedirs(DER, exist_ok=True)
os.makedirs(os.path.join(SUP, "retired"), exist_ok=True)
os.makedirs(os.path.join(SUP, "merged"), exist_ok=True)
man = ["# research 资产整理 v2 · 留痕（20261020）", "",
       "判据见 `pegww2/方法/资产治理与索引规范.md`；本文件记**逐文件落点**。", ""]
merged_notes = []
for name, rx, out in MERGE:
    dst, rows, seen = merge_family(rx, out)
    if dst:
        merged_notes.append((out, len(rows), len(seen)))
        man += ["## 合并 → `_superseded/merged/%s`（%d 行，源 %d 个）" % (out, len(rows), len(seen)), ""]
        man += ["- `%s`" % s for s in seen] + [""]
        for fn in seen:
            if not fn.endswith("(表头不同)"):
                os.remove(os.path.join(R, fn))
moved = defaultdict(list)
for f in files:
    src = os.path.join(R, f)
    if plan[f] == "derived":
        shutil.move(src, os.path.join(DER, f))
        moved["derived"].append(f)
    elif plan[f] == "retired":
        shutil.move(src, os.path.join(SUP, "retired", f))
        moved["retired"].append(f)
for sub in ("derived", "retired"):
    man += ["## → `%s/`（%d 个）" % (sub, len(moved[sub])), ""]
    man += ["- `%s`" % f for f in sorted(moved[sub])] + [""]
man += ["## 留顶层（%d）" % len(KEEP), ""]
man += ["- `%s`" % f for f in sorted(KEEP & set(files))] + [""]
io.open(os.path.join(SUP, "README-assets-v2.md"), "w", encoding="utf-8", newline="\n").write("\n".join(man) + "\n")
print("\n已执行：derived %d · retired %d · merged %s"
      % (len(moved["derived"]), len(moved["retired"]),
         ", ".join("%s(%d 行)" % (o, n) for o, n, _s in merged_notes)))
print("顶层现有 %d 个" % len([f for f in os.listdir(R) if os.path.isfile(os.path.join(R, f))]))
print("留痕 -> %s" % os.path.join(SUP, "README-assets-v2.md"))
