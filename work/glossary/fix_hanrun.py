#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""装备名「采购格标签宽度截断」修正器

⚠️⚠️ **已搁置，不要执行**（2026-10-16 结论，见 docs\\77 §7.7）⚠️⚠️
    用户的实机反例推翻了本文档原先的「连续汉字 ≥4 就截断」假说：
    `国民警卫`（4 个汉字）在采购格里**完整显示**，而同为 4 个汉字的 `装甲步?` 却被截。
    ⇒ 真正的触发条件是**采购格标签的可用像素宽度**（阈值落在 (52, 60] px），**不是字符数**。
    同一名字在**单位面板**里完整显示，信息不丢失；`D:\\OpenPG2` 已交付版 26.2% 的条目同样超宽。
    ⇒ 处置决定：**不改数据**。本脚本保留作为「若日后要治窄格宽度」的第一稿工具。

背景（已被上述结论取代，仅存记录）：
    引擎在装备浏览器/采购界面绘制名字时，超过标签宽度就截断，
    截断后多显示为 `X?`（`伞兵工兵 1944`→`伞兵工?`、`突击工兵 40`→`突击工?`、`托特行动队`→`托特行?`），
    但 `Wehr. 步兵 38`→`Wehr. 步兵` 无 `?` ⇒ 实际截断点由字节预算决定，精确阈值未解释。

本脚本做两件事：
  1. 机械兜底：把每一段连续汉字**均衡切段**（每段 ≤ LIMIT，且不产生单字段）后用空格连接。
     `防御工事`(4) -> `防御 工事`    `正规步兵`(4) -> `正规 步兵`
     `装甲掷弹兵`(5) -> `装甲掷 弹兵`  `摩托车巡逻队`(6) -> `摩托车 巡逻队`
  2. 人工/LLM 覆盖：`--map FILE` 传一份 TSV（`原串<TAB>新串`），优先级高于机械兜底。
     机械切分对固定词（`防御工事`）与专名（`沙恩霍斯特`）会切得难看，需 LLM 逐条定切点。

⚠️ 本脚本**只对「连续」判据有效**。若实机证明引擎是按「汉字总数」截断，
   则分隔符无效，必须改用缩短译名（本脚本不负责）。

纪律：默认 dry-run；--apply 才写盘；写盘走 .tmp -> 回读校验 -> os.replace；先备份。
"""
import os
import re
import sys
import shutil

OG = os.environ.get("OG_ROOT") or r"D:\OpenGeneral"
WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BKROOT = os.path.join(os.path.dirname(WORK), "backup")

HAN = re.compile(r"[\u4e00-\u9fff]+")
LIMIT = 3
SEP = " "


def chunks(t, limit):
    """把 t 均衡切成 ceil(len/limit) 段，每段 ≤ limit 且尽量等长、不长于 limit。"""
    n = len(t)
    k = (n + limit - 1) // limit
    base, rem = divmod(n, k)
    out, pos = [], 0
    for i in range(k):
        ln = base + (1 if i < rem else 0)
        out.append(t[pos:pos + ln])
        pos += ln
    return out


def split_han(s, limit=LIMIT, sep=SEP):
    def rep(m):
        t = m.group(0)
        return t if len(t) <= limit else sep.join(chunks(t, limit))
    return HAN.sub(rep, s)


def han_stats(s):
    runs = HAN.findall(s)
    return sum(len(r) for r in runs), (max(len(r) for r in runs) if runs else 0)


def read_lines(path, enc):
    raw = open(path, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    return [x.decode(enc, "replace")
            for x in raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n")]


def load_map(path):
    d = {}
    for ln in read_lines(path, "utf-8"):
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) >= 2 and parts[0]:
            d[parts[0]] = parts[1]
    return d


def main():
    if "--efile" not in sys.argv:
        raise SystemExit(__doc__ + "\n用法: python fix_hanrun.py --efile EFILE_GUS [--apply] "
                                  "[--limit N] [--map FILE] [--show N]")
    ef = sys.argv[sys.argv.index("--efile") + 1].strip()
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else LIMIT
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 40
    override = load_map(sys.argv[sys.argv.index("--map") + 1]) if "--map" in sys.argv else {}
    apply_ = "--apply" in sys.argv

    src = os.path.join(OG, ef, "equip.txt")
    dst = os.path.join(OG, ef, "TEXT-ZH", "equip.txt")
    if not os.path.exists(dst):
        raise SystemExit("找不到 %s（根级是否已完成？）" % dst)

    a = read_lines(src, "cp1250")
    b = read_lines(dst, "gbk")
    if len(a) != len(b):
        raise SystemExit("行数不一致：原文 %d / 译文 %d" % (len(a), len(b)))

    hits, from_map = [], 0
    new = list(b)
    for i, s in enumerate(b):
        tot, run = han_stats(s)
        if run <= limit:
            continue
        t = override.get(s, split_han(s, limit))
        if t == s:
            continue
        if s in override:
            from_map += 1
        hits.append((i, s, t, tot, run))
        new[i] = t

    print("[%s] 总行 %d" % (ef, len(b)))
    print("  连续汉字 > %d 的条目：%d（其中由 --map 裁定 %d）" % (limit, len(hits), from_map))
    if not hits:
        print("  无需改动。")
        return
    for i, s, t, tot, run in hits[:show]:
        print("   行%-6d %-26s -> %-28s (总%d/连%d)" % (i + 1, s, t, tot, run))
    if len(hits) > show:
        print("   ... 另 %d 条" % (len(hits) - show))

    out = "\r\n".join(new).encode("gbk")
    if not apply_:
        print("  dry-run：未写盘（加 --apply 落盘）")
        return

    bak = os.path.join(BKROOT, "OpenGeneral-%s-TEXTZH-equip.before-hanrun" % ef)
    os.makedirs(bak, exist_ok=True)
    shutil.copy2(dst, os.path.join(bak, "equip.txt"))

    tmp = dst + ".tmp"
    open(tmp, "wb").write(out)
    chk = open(tmp, "rb").read().decode("gbk").replace("\r\n", "\n").split("\n")
    assert len(chk) == len(a), "回读行数不一致"
    for j, s in enumerate(a):
        if not s.strip():
            assert chk[j].strip() == "", "空行被改：%d" % (j + 1)
    os.replace(tmp, dst)
    print("  已写入 %s（备份 %s）" % (dst, bak))


if __name__ == "__main__":
    main()
