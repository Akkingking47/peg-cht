# -*- coding: utf-8 -*-
"""修正 `.SCN` 的「场景位置标志」(@11349)，使引擎能找到场景简报/说明文件
================================================================================
PFS 字段 180（SCN.txt）：
    Scenario location flag | 偏移 11349 | 1 字节
      $0 = SCENARIO 目录 & .TXT 文件
      $1 = USERSCEN 目录 & .PLY 文件

即引擎据此决定「描述/简报文件去哪儿找、用什么扩展名」：
    flag=0 → Scenario\\<@11329 去扩展名>.txt
    flag=1 → Userscen\\<@11329 去扩展名>.ply

实证（文件访问时间，2026-10-10 16:52:34 游戏启动）：
    Tutorial.txt   被读 ✓  (flag=0)
    Sarajevo.ply   被读 ✓  (flag=1)
    nspegu19.txt   **未读** ✗  ← flag=1，引擎却去 Userscen 找 nspegu19.ply（不存在）
⇒ 表现为**没有简报/描述**。

本脚本：扫描所有进列表场景，若「引擎将要读的文件」不存在、而「另一侧的同名文件」存在，
则翻转 @11349 到正确值。**只改这 1 个字节，其余原样**。

用法：
    python work/peg/fix_scn_intro_flag.py            # dry-run（默认，只报告）
    python work/peg/fix_scn_intro_flag.py --apply    # 实际写入（先备份到 backup_scn_flag/）
"""
import os
import shutil
import struct
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


ROOT = WS
SNAP = os.path.join(ROOT, r"peg\testbed\backup-scn-flag")   # 改动前的原始快照

OFF_INTRO = 11329          # Scenario intro file name（20B，含或不含扩展名）
OFF_FLAG = 11349           # Scenario location flag（1B）


def exists_ci(d, name):
    if not name:
        return False
    low = name.lower()
    return any(f.lower() == low for f in os.listdir(d))


def engine_target(sub, stem, intro, flag):
    """引擎实际会去读的文件（全路径）"""
    base = os.path.splitext(intro)[0] if intro else stem
    if flag == 0:
        return os.path.join(GAME, "Scenario", base + ".txt"), "Scenario/" + base + ".txt"
    return os.path.join(GAME, "Userscen", base + ".ply"), "Userscen/" + base + ".ply"


def alt_target(sub, stem, intro, flag):
    """另一侧的同名文件（用于判断该翻转到哪个值）"""
    base = os.path.splitext(intro)[0] if intro else stem
    if flag == 0:      # 现读 Scenario/*.txt → 备用：Userscen/*.ply
        return os.path.join(GAME, "Userscen", base + ".ply"), "Userscen/" + base + ".ply"
    return os.path.join(GAME, "Scenario", base + ".txt"), "Scenario/" + base + ".txt"


def main():
    apply = "--apply" in sys.argv
    plans = []
    for sub in ("Scenario", "Userscen"):
        d = os.path.join(GAME, sub)
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".scn"):
                continue
            p = os.path.join(d, f)
            b = bytearray(open(p, "rb").read())
            if len(b) <= OFF_FLAG:
                continue
            # ⚠️ 不按 active 过滤：战役专用场景（active=1）同样会用到简报
            #    判定条件只有「现目标不存在 + 另一侧存在」，天然安全。
            stem = f[:-4]
            intro = b[OFF_INTRO:OFF_INTRO + 20].split(b"\x00")[0].decode("cp1252", "replace")
            flag = b[OFF_FLAG]
            now, now_disp = engine_target(sub, stem, intro, flag)
            alt, alt_disp = alt_target(sub, stem, intro, flag)
            if os.path.exists(now) or not os.path.exists(alt):
                continue                              # 现今能读到 ⇒ 无需改；两侧都没 ⇒ 无从改
            new_flag = 1 - flag
            plans.append((sub, f, stem, intro, flag, new_flag, now_disp, alt_disp, p))

    if not plans:
        print("✅ 无需修正：已无「现目标不存在、另一侧同名文件存在」的场景。")
        print("   （注：两侧都没有的场景＝战役专用/作者未提供简报，无从严判，不动。）")
        return

    print(f"需修正 {len(plans)} 个场景的 @11349：\n")
    for sub, f, stem, intro, fl, nf, now_disp, alt_disp, p in plans:
        print(f"  {sub}/{f:22s} intro={intro!r}")
        print(f"      现在读: {now_disp}  ✗")
        print(f"      改后读: {alt_disp}  ✓   (@11349 {fl} → {nf})")

    if not apply:
        print("\n[dry-run] 未写入。加 --apply 执行。")
        return

    os.makedirs(SNAP, exist_ok=True)
    for sub, f, stem, intro, fl, nf, now_disp, alt_disp, p in plans:
        snap = os.path.join(SNAP, sub)
        os.makedirs(snap, exist_ok=True)
        if not os.path.exists(os.path.join(snap, f)):
            shutil.copy2(p, os.path.join(snap, f))     # 首次改动前留一份原始快照
        b = bytearray(open(p, "rb").read())
        b[OFF_FLAG] = nf
        open(p, "wb").write(bytes(b))
        print(f"  ✓ 已改 {sub}/{f}: @11349 {fl} → {nf}（原始快照 → {SNAP}）")
    print(f"\n完成，共 {len(plans)} 个。快照目录：{SNAP}")


if __name__ == "__main__":
    main()
