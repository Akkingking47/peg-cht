#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梳理收尾 · 把 45 行「未译」里**确认是真漏译的 2 行**补上。

背景（本轮梳理的结论）：3685 个场景文件里 45 行正文含英文却没有中文，
其中 43 行属**有意保留**（已登记的 POLICY：`[XIII]` 罗马数字军级标记、`TNG`/`HvH`/`Roz`
等人工确认项、元数据/版权/URL、`KKKAAA...` 拟声），只有 2 行是**真漏洞**：

  ① `SCENARIO\\RG_usvsruss19_i.txt` 行4 = `Good luck! ` + **335 个 NUL 补位**
     （同文件行0/行2 早已是中文 ⇒ 单行漏译；根因是 W15：带 NUL 的串在映射表里查不到）
  ② `SCENARIO\\usvsussr10.txt` 行0 = `Allied Forces seize Vladavostok` + **470 个 NUL**
     ⚠️ 该文件**根本不在构建范围内**：693 个场景文件里只有它「有真实英文正文却无备份」
     （其余 8 个无备份的是 Dummy/READ ME/二进制/日志）⇒ 属于构建**覆盖缺口**，不是漏译。

NUL 补位**不用手写**：`gen_scn.py:197-209`（踩坑 W16）已自动把原文尾部控制字符搬回译文末尾，
且 `trail=orig[len(orig.rstrip()):]` 对「行尾=NUL」的串取空 ⇒ 不会重复补。

Vladivostok 用**国际/俄方名**「符拉迪沃斯托克」（与既有裁决一致：英文原名是国际名时照它译）。
`Vladavostok` 是原作拼写错误（应为 Vladivostok）——原文不动，译文按正确地名。

用法: python fix_two_leftovers.py [--apply]     # 默认 dry-run
"""
import hashlib
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
RES = os.path.join(WS, "pegww2", "research")
OVF = os.path.join(RES, "_scn-file-overrides.tsv")
BKROOT = os.path.join(WS, "pegww2", "testbed", "backup")
GAME = r"D:\Program Files\PeG-WW2"
CBK = os.path.join(WS, "backup", "before-two-leftovers")

# (子目录, 文件名, 行号0based, 期望原文, 译文)
ROWS = [
    ("SCENARIO", "RG_usvsruss19_i.txt", 4, "Good luck! ", "祝好运！"),
    ("SCENARIO", "usvsussr10.txt", 0, "Allied Forces seize Vladavostok", "盟军夺取符拉迪沃斯托克"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    apply_ = "--apply" in sys.argv
    print("=" * 88)
    print("梳理收尾：补最后 2 行真漏译（NUL 补位由 gen_scn W16 自动处理）")
    print("=" * 88)

    # ① usvsussr10.txt 缺备份 ⇒ 先备份原文（构建纪律：必须从 backup 读原文）
    fn = "usvsussr10.txt"
    src, bak = os.path.join(GAME, "SCENARIO", fn), os.path.join(BKROOT, "SCENARIO", fn)
    if os.path.isfile(bak):
        print("   ○ 备份已存在 %s" % os.path.relpath(bak, WS))
    elif os.path.isfile(src):
        d = open(src, "rb").read()
        print("   + 新建备份 %s（%d B, NUL %d）" % (os.path.relpath(bak, WS), len(d), d.count(b"\x00")))
        if apply_:
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            shutil.copy2(src, bak)
            if sha(bak) != sha(src):
                print("   ❌ 备份回读校验失败")
                return 1
    else:
        print("   ❌ 游戏目录无 %s" % fn)
        return 1

    # ② 逐条核对原文（防行号漂移），再写覆盖表
    t = io.open(OVF, encoding="utf-8").read()
    lines = t.split("\n")
    have = {}
    for i, l in enumerate(lines):
        c = l.split("\t")
        if len(c) >= 5 and not l.startswith("#"):
            have[(c[0], c[1], c[2])] = i

    for sub, f, idx, exp, zh in ROWS:
        p = os.path.join(BKROOT, sub, f)
        if not os.path.isfile(p):  # dry-run 尚未建备份 ⇒ 退回游戏目录（原文，未投放）
            p = os.path.join(GAME, sub, f)
        raw = open(p, "rb").read()
        cur = raw.decode("cp1252", "replace").split("\n")[idx]
        ok = cur.rstrip("\r") == exp or cur.rstrip("\r").rstrip("\x00").rstrip() == exp.rstrip()
        print("   [%s] 行%d 原文=%-42r 期望=%-42r %s"
              % (f, idx, cur.replace("\x00", "")[:42], exp, "✓" if ok else "❌ 不符"))
        if not ok:
            print("      ⇒ 行号已漂移，停止")
            return 1
        key = (sub, f, str(idx))
        if key in have:
            print("      （覆盖表已有该行 ⇒ 替换译文）")
            lines[have[key]] = "\t".join((sub, f, str(idx), exp, zh))
        else:
            lines.append("\t".join((sub, f, str(idx), exp, zh)))

    out = "\n".join(lines)
    if not apply_:
        print("\n（dry-run；加 --apply 才写覆盖表）")
        return 0
    os.makedirs(CBK, exist_ok=True)
    b = os.path.join(CBK, os.path.basename(OVF))
    if not os.path.isfile(b):
        shutil.copy2(OVF, b)
    io.open(OVF, "w", encoding="utf-8", newline="\n").write(out)
    n = sum(1 for l in out.split("\n") if l.strip() and not l.startswith("#"))
    print("\n✅ 已写 %s（现有覆盖行 %d 条）" % (os.path.relpath(OVF, WS), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
