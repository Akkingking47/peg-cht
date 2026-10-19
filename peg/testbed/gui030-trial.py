# -*- coding: utf-8 -*-
"""Gui030.txt 实机试点工具（R2 验证）—— 备份 / 构建 / 部署 / 还原 / 校验

用法:
  python gui030-trial.py backup     # 备份原文（只读游戏目录，+ 记录 md5）
  python gui030-trial.py build      # 生成试点文件（不动游戏目录）
  python gui030-trial.py deploy     # 部署（先验证备份 md5）
  python gui030-trial.py restore    # 还原原文（验证 md5 == 原始）
  python gui030-trial.py verify     # 报告当前状态

纪律：备份与覆盖分两条独立命令；部署前先验备份；还原后回读校验。
"""
import os, sys, hashlib, shutil

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


SRC = os.path.join(GAME, "Gui030.txt")
KIT = os.path.join(WS, "peg", "testbed")
BK = os.path.join(KIT, "backup", "Gui030.txt")
TRIAL = os.path.join(KIT, "Gui030.trial.txt")
MD5F = os.path.join(KIT, "backup", "Gui030.txt.md5")
# 原始 md5（2026-10-10 实测）
ORIG_MD5 = "f3b14bb91f8d8d462433b4b9afc22ae2"

# 两套替换集（行号 → 译文）；其余行字节原样保留
SETS = {
 "trial": {
    3:  "中国",           # China          国名槽
    35: "大胜",           # Brilliant Victory 胜利分级
    40: "下一单位",        # Next Unit      主按钮
    44: "补给",           # Supply
    46: "购买单位",        # Requisition Unit
    54: "结束回合",        # End Turn
    55: "档案",           # Dossier
    61: "全屏",           # Full Screen
    63: "退出游戏",        # Exit Game
    64: "检视部队",        # Inspect Unit
 },
 # ⭐ 等长探针 v4：中文译文「用 ASCII 空格补齐到与英文原行完全相同的字节数」
 # 目的：若标签按「字节偏移」定位，则等长替换后所有后续标签应恢复正确。
 # pad=True 表示自动补空格至原长；字符串里不要带尾空格。
 "probe4": {
   3:  ("中国", True),            # China           5 B
   35: ("大胜", True),            # Brilliant Victory 17 B
   40: ("下一单位", True),        # Next Unit        9 B
   44: ("补给", True),            # Supply           6 B
   46: ("购买单位", True),        # Requisition Unit 16 B
   54: ("结束回合", True),        # End Turn         8 B
   55: ("档案", True),            # Dossier          7 B
   61: ("全屏", True),            # Full Screen      11 B
   63: ("退出游戏", True),        # Exit Game        9 B
   64: ("检视部队", True),        # Inspect Unit     12 B
 },
 # 映射探针 v3：每行一个「互不相同的单字」⇒ 必定不超宽、不触发滚动 ⇒ 可干净读出
 # 「哪个按钮读哪一行」，同时验证「不超宽就不漂/不出方块」
 "probe3": {
   3:  "天", 35: "地", 40: "玄", 44: "黄", 46: "宇",
   54: "宙", 55: "洪", 61: "荒", 63: "日", 64: "月",
 },
 # 判别探针 v2：每行标签用「互不相同的 4 字」，一眼看出①读的是哪一行②显示了几字
 "probe2": {
   3:  "中国",
   35: "大胜",
   40: "甲乙丙丁",
   44: "戊己庚辛",
   46: "壬癸子丑",
   54: "寅卯辰巳",
   55: "午未申酉",
   61: "戌亥天地",
   63: "玄黄日月",
   64: "一二三四五六七八九十",
 },
 # ⭐⭐ 自标识探针 v5：把【行号】写在标签最前面（ASCII，1 字节/字），后接 10 个互不相同汉字。
 # 判读三件事，一次悬停全拿到：
 #   ① 开头能看到行号      ⇒ 无「按字节前偏移」
 #   ② 行号整段消失、直接是汉字 ⇒ 存在前偏移，且偏移量可数出来
 #   ③ 可见汉字个数        ⇒ 该格能容几个汉字
 # 40–52 用 壹贰叁… ；53–64 用 甲乙丙…  ⇒ 首字即可判断行号落在哪一段
 "probe5": {**{n: f"{n}壹贰叁肆伍陆柒捌玖拾" for n in range(40, 53)},
            **{n: f"{n}甲乙丙丁戊己庚辛壬癸" for n in range(53, 65)},
            **{3: "中国", 35: "大胜"}},
 # 全块探针 v6：把 40..64 整段（地图按钮提示块）都换成同一串 10 汉字，
 # 用来测「每个按钮各自的格宽」，并确认该块与按钮的对应关系。
 "probe6": {**{n: "壹贰叁肆伍陆柒捌玖拾" for n in range(40, 65)},
            **{3: "中国", 35: "大胜"}},
 # ⭐ 整块真实译文 v7：地图右侧按钮提示块 行 40–64 全译（自然长度，不补齐）
 # 配合 patch-labeldrop.py 的补丁测试：每个按钮都会显示自己那条中文 ⇒ 一次即可量出各框宽
 "block": {
   40: "下一单位",      41: "取消移动",      42: "上下车",
   43: "空运",          44: "补给",          45: "补充兵",
   46: "购买单位",      47: "野战司令部",    48: "空中模式",
   49: "战略地图",      50: "游戏功能",      51: "其他选项",
   52: "聊天",          53: "玩法说明 - ",   54: "结束回合",
   55: "部队档案",      56: "显示六角格",    57: "音频设置",
   58: "邮件对战",      59: "录像",          60: "回放回合",
   61: "全屏",          62: "显示地形",      63: "退出游戏",
   64: "检视部队",
   3: "中国", 35: "大胜",
 },
 # ⭐ 最短标签测试 v8：只放 2 个汉字 ⇒ 排除「框宽不足」这个变量。
 # 用于验证 patch-mbcs.py 的「双字节引擎」改造是否让中文正常显示。
 "short": {
   40: "下一",   44: "补给",   46: "购买",   54: "结束",
   55: "档案",   61: "全屏",   63: "退出",   64: "检视",
   3: "中国",    35: "大胜",
 },
 # 容量探针：用重复「中」字测每格可容几个汉字（1..10）
 "probe": {
   3:  "中国",                 # 国名（基线）
   35: "大胜",                 # 2 字基线
   40: "中",                   # Next Unit
   44: "中中",
   46: "中中中",
   54: "中中中中",
   55: "中中中中中",           # Dossier
   61: "中中中中中中",
   63: "中中中中中中中中",
   64: "中中中中中中中中中中",
 },
}
REPL = SETS["trial"]


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def cmd_backup():
    if os.path.exists(BK):
        print(f"[skip] 备份已存在: {BK}")
    else:
        os.makedirs(os.path.dirname(BK), exist_ok=True)
        shutil.copy2(SRC, BK)
        print(f"[ok] 备份 → {BK}")
    m = md5(BK)
    open(MD5F, "w").write(m + "  Gui030.txt\n")
    cur = md5(SRC)
    print(f"     备份 md5 = {m}")
    print(f"     现网 md5 = {cur}   {'(=原始)' if cur == ORIG_MD5 else '(!= 原始，注意)'}")
    return m


def use_set(name):
    global REPL, TRIAL
    REPL = SETS[name]
    TRIAL = os.path.join(KIT, f"Gui030.{name}.txt")

def cmd_build():
    raw = open(BK, "rb").read()
    assert b"\r\n" in raw
    lines = raw.split(b"\r\n")
    print(f"原文: {len(raw)} B / {len(lines)} 段（CRLF 切分）")
    out = []
    for i, ln in enumerate(lines, 1):
        if i in REPL:
            spec = REPL[i]
            txt, pad = spec if isinstance(spec, tuple) else (spec, False)
            zh = txt.encode("gbk")
            if pad:
                if len(zh) > len(ln):
                    print(f"  !! 行 {i}: 中文 {len(zh)} B > 原文 {len(ln)} B，无法等长")
                else:
                    zh = zh + b" " * (len(ln) - len(zh))
            flag = "  [等长]" if pad else ""
            print(f"  行 {i:>3}: {ln.decode('cp1252')!r}  →  {txt!r}  "
                  f"({len(ln)} B → {len(zh)} B){flag}")
            out.append(zh)
        else:
            out.append(ln)
    data = b"\r\n".join(out)
    open(TRIAL, "wb").write(data)
    print(f"[ok] 试点文件 → {TRIAL}  ({len(data)} B，行数一致: {len(data.split(chr(13).encode()+chr(10).encode())) == len(lines)})")


def cmd_deploy():
    if not os.path.exists(BK):
        sys.exit("!! 无备份，拒绝部署。先跑 backup")
    assert md5(BK) == ORIG_MD5, "!! 备份 md5 与原始不符，拒绝部署"
    if not os.path.exists(TRIAL):
        sys.exit("!! 无试点文件，先跑 build")
    cur = md5(SRC)
    if cur != ORIG_MD5:
        print(f"[warn] 现网 Gui030.txt 已非原始 (md5={cur})，仍将覆盖；可用 restore 还原")
    shutil.copy2(TRIAL, SRC)
    print(f"[ok] 已部署试点 → {SRC}")
    print(f"     现网 md5 = {md5(SRC)}")
    print("     ⚠️ 现在请手动启动游戏观察；观察完跑 restore 还原。")


def cmd_restore():
    if not os.path.exists(BK):
        sys.exit("!! 无备份，无法还原")
    shutil.copy2(BK, SRC)
    m = md5(SRC)
    ok = (m == ORIG_MD5)
    print(f"[{'ok' if ok else '!!'}] 已还原 → {SRC}")
    print(f"     md5 = {m}  {'== 原始 ✓' if ok else '!= 原始 ✗'}")
    return ok


def cmd_verify():
    for tag, p in (("现网", SRC), ("备份", BK), ("试点", TRIAL)):
        if os.path.exists(p):
            n = len(open(p, "rb").read().split(b"\r\n"))
            flag = ""
            if tag == "现网":
                flag = "  ← 原始" if md5(p) == ORIG_MD5 else "  ← 已被改（试点中）"
            print(f"  {tag:>4}: {p}  {os.path.getsize(p)} B  md5={md5(p)[:12]}…{flag}")
        else:
            print(f"  {tag:>4}: (不存在) {p}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd in SETS:
        use_set(cmd); cmd_build(); cmd_deploy(); 
        print(f"[note] 当前部署的是 [{cmd}] 集合")
    else:
        {"backup": cmd_backup, "build": cmd_build, "deploy": cmd_deploy,
         "restore": cmd_restore, "verify": cmd_verify}.get(cmd, cmd_verify)()
