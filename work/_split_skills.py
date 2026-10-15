# -*- coding: utf-8 -*-
"""按「汉化阶段」把巨型单文件技能切分为 SKILL.md + references/（内容零丢失，只重排）。

用法：python _split_skills.py [win-game|sd25] [--apply]
不加 --apply 则只预览（打印各 blocks 行数与覆盖校验）。
"""
import os, re, sys, shutil

SK = r"C:\Users\Administrator\.workbuddy\skills"

# ============================================================
# win-game-html-ui-localization
# ============================================================
WG_SRC = os.path.join(SK, "win-game-html-ui-localization", "SKILL.md")

# (起, 止含, 容器标题 or None=保留原样)
WG_BLOCKS = {
    "01-foundation-encoding.md": dict(
        title="地基：编码判别 · 来源排查 · 资源勘察",
        stage="阶段 0 · 侦察",
        chunks=[
            (12, 73, None),            # §一 编码：先做判别实验
            (384, 396, "## 来源判别：最强线索「同一画面半中半英」"),
            (588, 594, None),          # §十二 资源规模探查
            (919, 958, None),          # §十七 路径模板 → push 点 → 目录回溯
            (1344, 1409, None),        # §二十三 原文侧「乱码」诊断
        ]),
    "02-html-ui-layer.md": dict(
        title="HTML/界面层：三种来源 · 替换规则 · 长文本截断",
        stage="阶段 1 · 界面层",
        chunks=[
            (74, 210, None),           # §二 前半：三种来源 + 词义拆表 + per_file + 标签保护
            (491, 551, None),          # §九 长文本截断
            (552, 563, None),          # §十 进程级 UTF-8 代码页
        ]),
    "03-binary-data-tables.md": dict(
        title="二进制数据表：唯一可译区 · 定长/变长表",
        stage="阶段 2 · 数据层",
        chunks=[
            (211, 340, "## 定长记录表（MAPNAMES.STR 类）与「超长槽」"),
            (642, 766, None),          # §十四 唯一可译区
            (767, 849, None),          # §十五 变长表 .xscn
            (1465, 1531, None),        # §二十五 count == 0 是合法空组
        ]),
    "04-exe-hardcoded.md": dict(
        title="exe 层：宽串 · PE 解析 · 短串三板斧 · 紧凑串块",
        stage="阶段 3 · exe 层",
        chunks=[
            (397, 440, None),          # §三 UTF-16 宽串
            (595, 641, None),          # §十三 PE 解析 RVA↔偏移
            (1609, 1713, None),        # §二十七 短串三板斧
            (1714, 1829, None),        # §二十八 紧凑对齐串块
        ]),
    "05-glossary-governance.md": dict(
        title="译名治理：跨文件一致性 · 标准译名库 · 权威核对",
        stage="阶段 4 · 译名治理",
        chunks=[
            (1002, 1071, None),        # §十九 原始语言硬桥
            (1072, 1143, None),        # §二十 建立标准译名库
            (1144, 1243, None),        # §二十一 对照权威译名
            (1244, 1343, None),        # §二十二 译名统一：规则栈 + 6 坑
        ]),
    "06-audit-and-delivery.md": dict(
        title="审计与交付：进度审计 · 文本层清单审计 · 自检",
        stage="阶段 5 · 审计交付",
        chunks=[
            (473, 481, None),          # §六 回填脚本要点
            (482, 490, None),          # §七 交付前自检清单
            (850, 918, None),          # §十六 文本层清单审计
            (959, 1001, None),         # §十八 进度审计
        ]),
    "07-render-and-font.md": dict(
        title="渲染与字体：挤/叠/糊 · 译错 vs 字形糊",
        stage="阶段 6 · 渲染",
        chunks=[
            (368, 383, "## 先分清「译错」和「字形糊」"),
            (1532, 1608, None),        # §二十六 挤/叠/糊
        ]),
    "08-scheduling.md": dict(
        title="排期：按「目标优先级」分批",
        stage="阶段 7 · 排期",
        chunks=[
            (1410, 1464, None),        # §二十四 排期
        ]),
    "09-gui-verification.md": dict(
        title="验证手段：GUI 自动化 · 截图定位 · PostMessage 合成点击",
        stage="辅助 · 验证",
        chunks=[
            (341, 367, "## `PostMessage` 合成点击（绕过前台焦点限制）"),
            (441, 464, None),          # §四 GUI 自动化分档
            (465, 472, None),          # §五 截图与元素定位
            (564, 587, None),          # §十一 受限验证策略
        ]),
}

# ============================================================
# sd25-pe
# ============================================================
SD_SRC = os.path.join(SK, "sd25-pe", "SKILL.md")


def load(path):
    return open(path, encoding="utf-8").read().split("\n")


def build_refs(src, blocks, header_note):
    """返回 {filename: content}，并做覆盖校验"""
    n = len(src)
    covered = [False] * (n + 1)
    out = {}
    for fn, cfg in blocks.items():
        parts = [f"# {cfg['title']}", "", f"> {header_note}",
                 f"> 阶段：**{cfg['stage']}**", "", "---", ""]
        for (a, b, container) in cfg["chunks"]:
            for i in range(a, b + 1):
                covered[i] = True
            body = src[a - 1:b]
            if container:
                parts.append(container)
                parts.append("")
            body = list(body)
            while body and not body[-1].strip():
                body.pop()
            parts.extend(body)
            parts.extend(["", "---", ""])
        while parts and not parts[-1].strip():
            parts.pop()
        out[fn] = "\n".join(parts) + "\n"
    # 覆盖校验：1..n 全部应被覆盖（除头 11 行 frontmatter/标题）
    missing = [i for i in range(12, n + 1) if not covered[i]]
    dup = []
    for fn, cfg in blocks.items():
        for (a, b, _) in cfg["chunks"]:
            for i in range(a, b + 1):
                pass
    return out, missing


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "win-game"
    apply = "--apply" in sys.argv

    if mode == "win-game":
        src = load(WG_SRC)
        note = "摘自「Windows 游戏汉化通用手法」技能（`win-game-html-ui-localization`）。**章节编号沿用原技能全局编号**，便于与旧记录对照。"
        refs, missing = build_refs(src, WG_BLOCKS, note)
        dest = os.path.join(SK, "win-game-html-ui-localization", "references")
    else:
        print("sd25 尚未定义"); return

    print(f"源文件 {len(src)} 行")
    print("\n各 reference：")
    for fn, c in refs.items():
        nl = c.count("\n")
        print(f"  {fn:34s} {nl:5d} 行  {len(c.encode('utf-8')):7d} B")
    print(f"\n覆盖校验：未覆盖行 = {missing if missing else '无 ✓'}")

    if not apply:
        print("\n（预览模式；加 --apply 才写盘）")
        return
    os.makedirs(dest, exist_ok=True)
    for fn, c in refs.items():
        open(os.path.join(dest, fn), "w", encoding="utf-8", newline="\n").write(c)
    print(f"\n已写 {len(refs)} 个 reference → {dest}")


if __name__ == "__main__":
    main()
