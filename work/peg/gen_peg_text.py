# -*- coding: utf-8 -*-
"""
PeG 文本文件通用中文化生成器
================================================================
设计：**译法与逻辑分离** —— 映射表存 tsv（可读可改可复用），本脚本只管生成与校验。

映射表格式 `peg/research/<name>-map.tsv`：
    第一列 = 整数 ⇒ 按【行号】映射（每行内容不同时用，如 tips 长句）
    第一列 = 文本 ⇒ 按【原文整串】映射（同值多行时用，如 equip 装备名）
    第二列 = 译文
    以 # 开头的行为注释

用法：
    python work/peg/gen_peg_text.py <target>            # 生成（含校验）
    python work/peg/gen_peg_text.py <target> deploy     # 生成并部署到游戏目录
    python work/peg/gen_peg_text.py <target> restore    # 从备份还原

四道硬校验（任一不过即拒绝落盘）：
    ① 行数与原文件严格一致
    ② printf 格式符 %s/%d 顺序与个数保留
    ③ 无 CR/LF/TAB 控制字符混入
    ④ 禁用译法黑名单扫描（整串精确匹配）
"""
import os
import re
import sys

ROOT = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG"
BACKUP = os.path.join(ROOT, r"peg\testbed\backup")
RESEARCH = os.path.join(ROOT, r"peg\research")
TESTBED = os.path.join(ROOT, r"peg\testbed")

TOK = re.compile(r"%[sd]")

# 禁用译法（整串精确匹配；与 gen_gui030_zh.py 保持一致）
BANNED = {
    "补充兵": "应为「补充兵员」", "野战司令部": "应为「战地司令部」",
    "检视部队": "应为「查看部队」", "其他选项": "应为「更多选项」",
    "部队档案": "应为「战后报告」", "下一单位": "应为「下一部队」",
    "大胜": "应为「决定性胜利」", "声望": "应为「威望」",
    "遮断": "应为「空中封锁」", "野鼬鼠": "应为「防空压制」",
    "快打快撤": "应为「打了就跑」", "坑道鼠": "应为「坑道兵」",
    "前沿观察员": "应为「炮兵观察员」", "反炮兵": "应为「炮火压制」",
    "间接防御": "应为「远程防御」", "战斗工兵": "应为「工兵」",
    "轻型护卫舰": "应为「护卫舰」", "反应防御": "应为「防御反击」",
    "闪击": "应为「闪电战」", "占领者": "应为「攻坚专家」",
    "埋伏者": "应为「伏击者」",
}


def load_map(name):
    """返回 (mode, mapping)；mode ∈ {'line','text'}"""
    p = os.path.join(RESEARCH, f"{name}-map.tsv")
    if not os.path.exists(p):
        print(f"❌ 找不到映射表 {p}")
        sys.exit(1)
    line_mode = None
    m = {}
    with open(p, encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            s = raw.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            parts = s.split("\t")
            if len(parts) < 2:
                print(f"❌ 映射表第 {ln} 行格式错误（需 TAB 分列）：{s!r}")
                sys.exit(1)
            if parts[0].strip() in ("行号", "line", "#行号"):
                print(f"❌ {p} 看起来是【行级对照表】而非【映射表】"
                      f"（表头 {parts[0]!r}）。映射表应是 2 列：键<TAB>译文")
                sys.exit(1)
            if len(parts) >= 3:
                print(f"❌ 映射表第 {ln} 行有 {len(parts)} 列，应为 2 列：{s!r}")
                sys.exit(1)
            k, v = parts[0], parts[1]
            is_line = k.strip().isdigit()
            if line_mode is None:
                line_mode = is_line
            elif line_mode != is_line:
                print(f"❌ 映射表第 {ln} 行混合了行号与原文两种模式")
                sys.exit(1)
            if is_line:
                m[int(k)] = v
            else:
                m[k] = v
    return ("line" if line_mode else "text"), m


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1]
    cmd = sys.argv[2] if len(sys.argv) > 2 else "build"

    src_name = f"{name}.txt"
    src = os.path.join(BACKUP, src_name)          # 真源＝备份
    dst = os.path.join(TESTBED, f"{src_name}.zh.txt")
    live = os.path.join(GAME, src_name)

    if cmd == "restore":
        live = os.path.join(GAME, src_name)
        data = open(src, "rb").read()
        open(live, "wb").write(data)
        print(f"✅ 已还原 {live}  ({len(data)} B)")
        return

    if not os.path.exists(src):
        print(f"❌ 找不到原文备份 {src}")
        sys.exit(1)

    mode, mp = load_map(name)
    raw = open(src, "rb").read()
    lines = raw.split(b"\r\n")
    n = len(lines)
    print(f"原文：{src}   ({n} 行 / {len(raw)} B)   映射模式：{'行号' if mode=='line' else '原文串'}  条目 {len(mp)}")

    # ---- 构造 ----
    def lookup(en):
        """text 模式：先精确匹配，再容忍首尾空白（原文偶有尾空格）"""
        if en in mp:
            return mp[en]
        return mp.get(en.rstrip()) or mp.get(en.strip())

    out, used, unchanged = [], set(), []
    for i, lb in enumerate(lines, 1):
        en = lb.decode("cp1252")
        if mode == "line":
            zh = mp.get(i)
            key = i
        else:
            zh = lookup(en)
            key = en if en in mp else (en.rstrip() if en.rstrip() in mp else en.strip())
        if zh is None:
            out.append(lb)
            if en.strip():
                unchanged.append((i, en))
        else:
            out.append(zh.encode("gbk"))
            used.add(key)

    # 未命中的映射条目（写多/写错）
    unused = [k for k in mp if k not in used]
    if unused:
        print(f"⚠️ 映射表有 {len(unused)} 条未用到：{unused[:10]}")

    # ---- 校验 ① 行数 ----
    if len(out) != n:
        print(f"❌ 行数不一致：{len(out)} != {n}")
        sys.exit(1)
    print(f"  译 {len(used)} 处 / 原样保留 {len(unchanged)} 行 ✅")

    # ---- 校验 ② 格式符 ----
    bad = []
    for i, lb in enumerate(lines, 1):
        en = lb.decode("cp1252")
        zh = mp.get(i) if mode == "line" else mp.get(en)
        if zh and TOK.findall(en) != TOK.findall(zh):
            bad.append((i, en, zh))
    if bad:
        print("❌ 格式符不匹配：")
        for i, e, z in bad:
            print(f"   行{i} EN={e!r} ZH={z!r}")
        sys.exit(1)
    print("  格式符 %s/%d 保留 ✅")

    # ---- 校验 ③ 控制字符 ----
    badc = [(i, z) for i, z in (mp.items() if mode == "line" else [(k, v) for k, v in mp.items()])
            if any(c in z for c in "\r\n\t")]
    if badc:
        print(f"❌ 译文含控制字符：{badc[:5]}")
        sys.exit(1)
    print("  无 CR/LF/TAB ✅")

    # ---- 校验 ④ 黑名单 ----
    hits = []
    for k, z in mp.items():
        for b, why in BANNED.items():
            if z.strip() == b or z.strip().rstrip("-: ").strip() == b:
                hits.append((k, b, why))
    if hits:
        print("❌ 命中禁用译法：")
        for k, b, why in hits:
            print(f"   {k} 「{b}」— {why}")
        sys.exit(1)
    print("  禁用译法 0 命中 ✅")

    # ---- 落盘 ----
    data = b"\r\n".join(out)
    open(dst, "wb").write(data)
    print(f"\n✅ 成品：{dst}\n   {len(data)} B（原 {len(raw)} B，{len(data)-len(raw):+d}）")

    if cmd == "deploy":
        open(live, "wb").write(data)
        print(f"✅ 已部署 {live}")

    # 未命中清单（便于补译）
    if unchanged:
        miss = os.path.join(TESTBED, f"_untranslated_{name}.txt")
        with open(miss, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {name} 未命中行（原文，共 {len(unchanged)} 行）\n")
            for i, e in unchanged:
                f.write(f"{i}\t{e}\n")
        print(f"   未命中清单：{miss}")


if __name__ == "__main__":
    main()
