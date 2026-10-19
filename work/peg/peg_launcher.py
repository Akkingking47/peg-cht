# -*- coding: utf-8 -*-
"""peg_launcher.py — PeG 运行期内存补丁启动器（母本 exe 一个字节都不改）

思路（借《突袭》MultiCAD「通用产物 + 配置选分辨率」的模式）：
    CreateProcess(CREATE_SUSPENDED) 把 PeG030.exe 挂起启动
    → 在主线程还没执行任何指令前，按站点表改内存里的
      「尺寸常量 / 屏幕画布描述符 / 强制重绘开关 / UI 记录表」
    → 逐项回读校验 → 恢复页保护 → ResumeThread 放行
    ⇒ 分发形态变成「原版 exe + 启动器 + 参数」，换分辨率只改参数。

补丁来源（全部是既有定论，不再现场推导）：
  1) 尺寸站点表  work\\peg\\out\\res_diff_v4.tsv（va=立即数地址；按 tag 重算）
  2) 代码侧 10 处 imm32 尺寸（与模板脚本 patch_res_wh.py 完全一致）
  3) A 组：屏幕描述符 right/bottom（0x4421D4/0x4421DE/0x442219/0x442223）
  4) B 组：0x4489D8  je 0x4489F5 -> 90 90（每帧强制走整屏刷新 0x44AC45）
  5) D 组：UI 记录表位移（work\\peg\\out\\ui_layout_v9.tsv，按 delta 重算）
           + 0x45696D  mov word [0x4A42EC], 799 -> w-1

用法：
  python peg_launcher.py --w 1920 --h 1080 --dry-run     # 只打印方案，不启动
  python peg_launcher.py --w 1920 --h 1080 --selftest    # 挂起启动→打补丁→校验→杀掉（游戏未跑）
  python peg_launcher.py --w 1920 --h 1080               # 正常启动游戏
可选：--exe <路径>  --cwd <目录>  --no-ui  --no-repaint  --no-canvas
"""
import argparse
import ctypes
import hashlib
import os
import struct
import sys
import time

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

MOTHER = os.path.join(GAME, "PeG030.exe")
MOTHER_MD5 = "c462e897b3aa1c384870c857ce9e01df"
IMAGE_BASE = 0x400000

# (imm32 VA, 旧值, tag, 说明) —— 与 patch_res_wh.py 的 CODE_EDITS 一致
CODE_EDITS = [
    (0x41C4D7, 0x23B, "h-28", "面板矩形 bottom 571"),
    (0x41C4DE, 0x31F, "w-1", "面板矩形 right 799"),
    (0x44C5CD, 0x23A, "h-30", "屏幕边框 push 570"),
    (0x44C5D2, 0x31C, "w-4", "屏幕边框 push 796"),
    (0x44C731, 0x320, "w", "视口裁剪组1 mov eax,800"),
    (0x44C778, 0x258, "h", "视口裁剪组1 mov edx,600"),
    (0x44C86A, 0x320, "w", "视口裁剪组2 mov edx,800"),
    (0x44C8B1, 0x258, "h", "视口裁剪组2 mov ecx,600"),
    (0x44CC68, 0x320, "w", "视口裁剪组3 mov edx,800"),
    (0x44CCAF, 0x258, "h", "视口裁剪组3 mov ecx,600"),
    # 底栏（0x44C547，call 0x47047A）y=572 / 底边=600：**已回退，暂不修改**。
    #   原因：实测改成 h-28 / h 之后游戏无法启动（这两个值疑似参与底栏源面的尺寸/索引，
    #   拉到 1052/1080 后越界）。要动它们必须先弄清 0x47047A 的参数语义。
]

# A 组：屏幕描述符（写死 799/599 的两个 DrawTarget 裁剪框）
#   注意：这里是**立即数地址**（指令 VA + 6），不是指令地址
CANVAS_SITES = [
    (0x4421DA, 799, "w-1", "屏幕描述符#1 right"),
    (0x4421E4, 599, "h-1", "屏幕描述符#1 bottom"),
    (0x44221F, 799, "w-1", "屏幕描述符#2 right"),
    (0x442229, 599, "h-1", "屏幕描述符#2 bottom"),
]

REPAINT = (0x4489D8, b"\x74\x1b", b"\x90\x90", "每帧强制整屏刷新（je->nop）")
# R 组：地图屏每帧都执行「清层 + 整块重绘」。
# 0x42CF61 是地图屏的每帧处理器（唯一调用者 0x44047C 落在状态机跳转表里的一格）：
#   0x42CF82  movsx eax, byte[0x4af324]     ; 一次性"已初始化"标志
#   0x42CF89  test eax, eax
#   0x42CF8B  jne 0x42CF9E                  ; 已初始化 => 跳过 0x43F7E4
#   0x42CF8D  mov byte[0x4af324], 1
#   0x42CF96  call 0x43F7E4                 ; 清三层 + 按 extent 整块重绘地图
#   0x42CF9E  call 0x42D0F2                 ; 每帧都在跑：重算移动范围并写遮挡层
# 症状"选中单位后范围阴影只闪一帧 / 移动鼠标才稳定"与此吻合：0x42D0F2 每帧都在标记，
# 但像素只在 0x43F7E4 那条整块重绘里落到地图面。把 jne 改成 nop 即每帧重绘一次。
MAPREPAINT = (0x42CF8B, b"\x75\x11", b"\x90\x90",
              "R 地图屏每帧整块重绘（jne->nop）")
# S 组：地图每帧上屏（去掉「滚动位置没变就跳过 0x41FF8A 那一笔地图上屏 BltFast」的 je）。
# 0x42D464 是地图屏的每帧处理器，后半段（不受 [0x498D74] 脏标志约束）逻辑：
#   0x42D509  movsx eax, word[edx*2 + 0x498d34]   ; 缓存的 scrollX（按槽位）
#   0x42D518  movsx ecx, word[0x4af2f8]           ; 当前 scrollX
#   0x42D51F  cmp eax, ecx / jne 0x42D53D         ; 变了 -> 去上屏
#   0x42D52A  movsx eax, word[edx*2 + 0x498d38]   ; 缓存的 scrollY
#   0x42D532  movsx ecx, word[0x4af2fc]           ; 当前 scrollY
#   0x42D539  cmp eax, ecx
#   0x42D53B  je 0x42D581                         ; ← 两个滚动都【没变】就跳过上屏
#   0x42D53D  ... 更新缓存
#   0x42D579  call 0x41FF8A                       ; 地图面 -> 后备/主面 的那一笔 BltFast
# 症状「选中单位后范围阴影只闪一帧 / 鼠标不动就不显示」正对应这条：0x42D0F2 每帧都把
# 范围烘进地图面，但滚动没变时地图面根本不上屏。把 0x42D53B 的 je 改成 nop 即每帧上屏。
PRESENT = (0x42D53B, b"\x74\x44", b"\x90\x90",
           "S 地图每帧上屏（je->nop）")
# T 组：移动范围每帧重算（默认**不打**，用 --range-every 打开）。
#   函数 0x42D445 是地图屏的每帧回调（被 0x44047C 经状态机表调用），全文：
#     0x42D445  push ebp / 0x42D446 mov ebp,esp / 0x42D448 call 0x471499
#     0x42D44D  cmp dword [0x4af2f4], 0   ; [0x4af2f4] 由悬停/点选命令置 1
#     0x42D454  je  0x42D45D              ; == 0 => 只画悬停单位信息
#     0x42D456  call 0x42D1A5             ; != 0 => 重算移动范围并写格表 [0x622D4A]
#     0x42D45B  jmp 0x42D462
#     0x42D45D  call 0x42D3C3             ; 悬停信息分支
#   每帧地图屏处理器 0x42D0F2 用「格表 [0x622D4A] == word[0x686FD4]」决定每格点亮/擦除，
#   而格表只在悬停变化那一帧重算 ⇒ 选中单位后鼠标不动，格表还是旧内容，阴影不出来
#   （用户 m05319 第 1 条）。9 字节等价改写：先无条件 call 0x42D1A5，再 jmp 到 0x42D45D，
#   两个分支都保留（不会像直接 NOP 掉 je 那样弄丢悬停信息面板）。
RANGE_EVERY = (0x42D44D, b"\x83\x3d\xf4\xf2\x4a\x00\x00\x74\x07",
               b"\xe8\x53\xfd\xff\xff\xeb\x09\x90\x90",
               "T 移动范围每帧重算（cmp/je -> call 0x42D1A5 + jmp 0x42D45D）")
# P 组：0x450553 那个刷新器 = 读共享标志 -> 画地图/覆盖层 -> 清标志；
# 把 0x45055C 的 je 改成 nop，让它每帧都尝试画这一层（清标志的逻辑保留）
OVERLAY = (0x45055C, b"\x74\x2d", b"\x90\x90", "地图覆盖层每帧重画（je->nop，单点）")
# 立即数地址（指令 0x45696D = 66 c7 05 <abs32> <imm16>，imm16 在 +7）
PANEL = (0x456974, 799, "w-1", "右侧面板显示位置 mov word [0x4A42EC]")

# E 组：悬停「小说明框」的 300x60 面板位块（call 0x41EB70，flags=0x1008000 即
#   DDBLT_WAIT|DDBLT_KEYSRC）。该面板先被 DDBLT_COLORFILL 涂上色键色 word[0x6769B0]
#   (品红)，再整体 KEYSRC 抠图上传——依赖显示层真正执行色键。
#   实测：Svens 包装（用户机上的 ddraw.dll）在该路径上不抠图 ⇒ 屏上直接露出品红。
#   关键事实：面板目标位置 x=800，正好等于母本屏宽 ⇒ 母本里 0x41EB70 的
#   「x >= 屏宽 ⇒ 直接放弃」分支命中，**这两处位块在 800x600 下从不执行**，
#   所以母本 800x600 里既没有品红也没有这些残留。把这两处 call 改成 nop，
#   等价于恢复母本的实际行为（文字仍由 0x47010B 直画到后台缓冲 [0x676904]，照样显示）。
TOOLTIP_SITES = [
    (0x44C929, b"\xe8\x42\x22\xfd\xff", b"\x90" * 5,
     "E 悬停说明框面板位块 #1（0x44C7BE 路径）-> nop"),
    (0x44CD27, b"\xe8\x44\x1e\xfd\xff", b"\x90" * 5,
     "E 悬停说明框面板位块 #2（0x44CC.. 路径）-> nop"),
]

# F 组：通用位块助手 0x41EB70 内部的裁剪算术（报告 report-hintbox.md 的 ★ 根因）。
#   助手把请求矩形按「硬编码屏宽」裁剪：外层判定常量早就被补成 0x780/0x438，
#   但真正的减法仍是旧基准 −0x320(800)/−0x258(600)。于是任何 x+w > 新屏宽 的矩形
#   会被减去 (x+w−800) —— 远大于它自身宽度 —— 宽度变成负数、右边界倒退到 800，
#   位块把一大片内存斜着搬来搬去。用户 m02665 实测的「画面破碎」正是这个签名：
#   损坏区 x=800..1918（恰好从旧屏宽 800 开始）、y=580..821、横向锯齿步长 ≈101 px。
CLIP_ARITH = [
    (0x41EC11, b"\xe0\xfc\xff\xff", b"\x80\xf8\xff\xff", "F 裁剪算术 x：-800 → -1920"),
    (0x41EC2C, b"\xe0\xfc\xff\xff", b"\x80\xf8\xff\xff", "F 裁剪算术 x：-800 → -1920"),
    (0x41EC94, b"\xa8\xfd\xff\xff", b"\xc8\xfb\xff\xff", "F 裁剪算术 y：-600 → -1080"),
]

# G 组：次级界面（战略地图视口 / 子界面文本矩形与居中基准）。
#   报告 work\peg\out\report-secondary-ui.md §3.1 的 14 处「确证」。
#   S2：视口设置器 0x424C73 的两个调用者仍传旧 799/571（孪生 0x41C4D7/DB 早已打成 1919/1052
#       ⇒ 只补一半），加上贴边滚动判定仍比 799/599 ⇒ 战略地图一动鼠标就在 x≈800 处撕裂。
#   S3：全 exe 唯一文本路径 0x4700C6 的排版矩形写死 (0,0,800,600)，38 个 UI 站点共用；
#       0x43BCF7 还用「400 − 文本宽/2」硬居中 ⇒ 子界面必然回到旧 800×600 区域。
SECONDARY = [
    (0x45A0F2, 0x23B, "h-28", "G S2 战略地图视口 0x45A0AF bottom 571"),
    (0x45A0F7, 0x31F, "w-1", "G S2 战略地图视口 0x45A0AF right 799"),
    (0x45A94B, 0x23B, "h-28", "G S2 战略地图视口 0x45A945 bottom 571"),
    (0x45A950, 0x31F, "w-1", "G S2 战略地图视口 0x45A945 right 799"),
    (0x4567C4, 0x31F, "w-1", "G S2 贴边滚动判定（右）"),
    (0x4567DE, 0x257, "h-1", "G S2 贴边滚动判定（下）"),
    (0x4568E2, 0x31F, "w-1", "G S2 贴边滚动判定 2（右）"),
    (0x4568FC, 0x257, "h-1", "G S2 贴边滚动判定 2（下）"),
    (0x456984, 0x31F, "w-1", "G S2 滚动方向判定（右）"),
    (0x456A3E, 0x257, "h-1", "G S2 滚动方向判定（下）"),
    (0x4700DD, 0x320, "w", "G S3 文本排版矩形 right 800"),
    (0x4700E4, 0x258, "h", "G S3 文本排版矩形 bottom 600"),
    (0x43BCF8, 0x190, "w/2", "G S3 消息框硬居中基准 400"),
    (0x43BCAE, 0x190, "w/2", "G S3 消息框 right 400"),
]

# H 组（候选，默认打；--no-extra 可关）：报告 §3.2 的 C1–C4。
#   整屏重绘区登记（留 599/799 则 y>599 永不重绘）+ 25×25 格子绘制器的边界剔除。
EXTRA = [
    (0x42E497, 0x257, "h-1", "H 候选 整屏重绘区 bottom 599"),
    (0x42E49C, 0x31F, "w-1", "H 候选 整屏重绘区 right 799"),
    (0x46CF45, 0x320, "w", "H 候选 25x25 格子剔除 800"),
    (0x46CF4E, 0x258, "h", "H 候选 25x25 格子剔除 600"),
]

# M 组：地图面尺寸与地图绘制界 1920 -> 4096（0x780 -> 0x1000）
#   0x41FF8A（每帧地图上屏）把地图面 [0x655574] 的窗口 (x, y, x+W, y+H) BltFast 到后备缓冲，
#   其中 x/y 是滚动坐标、W/H 是视口宽高（我们补成 1920x1031）。母本视口 800x600、地图面
#   1920x1920，天然留有 1120 的滚动余量；视口变宽后余量归零 => 一横向滚动（x>0）源矩形就
#   超出地图面，DirectDraw 会整笔拒绝（代码只在 0x42000B 记日志，不回退）=> 地图区域保持黑/旧内容。
#   把地图面与所有地图绘制界一起放大到 4096，余量恢复。
#   这 31 处都是母本原有的 1920（与补丁改出来的屏幕 1920 无交集，见 _plan_vs_780.py 的核对输出）。
MAP_SITES = [
    (0x41F3FA, "地图面界 cmp edx,1920"),
    (0x424AD3, "地块位块 局部R/高"),
    (0x424ADA, "地块位块 局部R/宽"),
    (0x424B31, "地块位块 局部R/高2"),
    (0x424B38, "地块位块 局部R/宽2"),
    (0x424BA6, "地块位块 界 cmp"),
    (0x424BB1, "地块位块 界 cmp"),
    (0x424BE9, "地块位块 界 cmp"),
    (0x424BF4, "地块位块 界 cmp"),
    (0x43D733, "直写 界 cmp"),
    (0x43D747, "直写 界 cmp"),
    (0x43DB03, "直写 界 cmp"),
    (0x43DB72, "直写 界 cmp"),
    (0x43DB83, "直写 行距 imul"),
    (0x43DEC7, "直写 界 cmp"),
    (0x43DF37, "直写 界 cmp"),
    (0x43DF48, "直写 行距 imul"),
    (0x43E2F0, "直写 界 cmp"),
    (0x43E360, "直写 界 cmp"),
    (0x43E371, "直写 行距 imul"),
    (0x43E6B5, "直写 界 cmp"),
    (0x43E725, "直写 界 cmp"),
    (0x43E736, "直写 行距 imul"),
    (0x441BFD, "地图面A dwHeight"),
    (0x441C04, "地图面A dwWidth"),
    (0x441C90, "地图面B dwHeight"),
    (0x441C97, "地图面B dwWidth"),
    (0x455BB6, "地图面界 cmp"),
    (0x455BBD, "地图面界 cmp"),
    (0x455BE1, "地图面界 cmp"),
    (0x455BE8, "地图面界 cmp"),
]

TAGS = ("w", "w-1", "w-4", "h", "h-1", "h-28", "h-30", "dx", "dy", "w/2")


def new_value(tag, old, w, h):
    return {
        "w": w, "w-1": w - 1, "w-4": w - 4,
        "h": h, "h-1": h - 1, "h-28": h - 28, "h-30": h - 30,
        "dx": old + (w - 800), "dy": old + (h - 600),
        "w/2": w // 2,
    }[tag]


def find_tsv(name):
    for p in (os.path.join(HERE, name), os.path.join(OUT, name)):
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 %s" % name)


def load_tsv(name):
    with open(find_tsv(name), encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        rows = []
        for line in f:
            if not line.strip():
                continue
            rows.append(dict(zip(head, line.rstrip("\n").split("\t"))))
    return rows


def build_plan(w, h, ui=True, repaint=True, canvas=True, tooltip=False, extra=True,
               panel=True, dxdy=True, mapmargin=True, scrollfix=True, maprepaint=True,
               present=True, rangeevery=False):
    """返回 (entries, notes)；entry = dict(va,size,old,new,label)"""
    entries, notes = [], []
    seen = {}

    def add(va, size, old_bytes, new_bytes, label):
        if va in seen:
            if seen[va] == new_bytes:
                notes.append("  · 重复站点 %#x 目标一致，合并（%s）" % (va, label))
                return
            raise SystemExit("冲突：%#x 被两处补丁写成不同值（%s）" % (va, label))
        seen[va] = new_bytes
        entries.append({"va": va, "size": size, "old": old_bytes,
                        "new": new_bytes, "label": label})

    # 1) 尺寸站点表（+ K 组：传统构建器默认跳过的 dx/dy 位置行）
    n_dim = n_dx = n_skip_dx = 0
    for r in load_tsv("res_diff_v4.tsv"):
        tag = r["tag"]
        if tag not in TAGS:
            raise SystemExit("未知 tag %r" % tag)
        if tag in ("dx", "dy"):
            # dxdy: False/None=都不打；"x"=只打 dx 行（x/right 水平位移）；True/"all"=dx+dy 都打
            want = bool(dxdy) and not (dxdy == "x" and tag == "dy")
            if not want:
                n_skip_dx += 1
                continue
            n_dx += 1
        size = int(r["width"])
        old = int(r["old"])
        nv = new_value(tag, old, w, h)
        fmt = "<H" if size == 2 else "<I"
        add(int(r["va"], 16), size, struct.pack(fmt, old), struct.pack(fmt, nv),
            "%s %s/%s" % (r["section"], tag, r["note"][:26]))
        n_dim += 1
    notes.append("  · 站点表尺寸：%d 条（其中 dx/dy 位置行 %d 条%s）" %
                 (n_dim, n_dx, "" if dxdy else "，已用 --keep-dx 跳过"))

    # 2) 代码侧 imm32
    for va, old, tag, note in CODE_EDITS:
        nv = new_value(tag, old, w, h)
        add(va, 4, struct.pack("<I", old), struct.pack("<I", nv), "代码侧 " + note)

    # 3) A 组屏幕描述符
    if canvas:
        for va, old, tag, note in CANVAS_SITES:
            nv = new_value(tag, old, w, h)
            add(va, 4, struct.pack("<I", old), struct.pack("<I", nv), "A " + note)
    # 4) B 组强制重绘
    if repaint:
        va, ob, nb, note = REPAINT
        add(va, len(ob), ob, nb, "B " + note)
    # 4b) P/Q 组已回退（P 目标错、Q 无效）：见 work\peg 下记录
    # 5) D 组 UI 记录位移 + 面板位置
    if ui:
        n_ui = 0
        for r in load_tsv("ui_layout_v9.tsv"):
            va = int(r["va"], 16)
            size = int(r["width"]) if "width" in r else 2
            field = r["field"]
            delta = int(r["delta"])
            newv = int(r["new_value"])
            mother = newv - delta
            if field in ("x", "right"):
                # idx13＝动作条，水平居中 ⇒ 位移取一半
                dv = (w - 800) // 2 if r["idx"] == "13" else (w - 800)
            elif field in ("y", "bottom"):
                dv = h - 600
            else:
                raise SystemExit("未知字段 %r" % field)
            target = mother + dv
            fmt = "<H" if size == 2 else "<I"
            if va in seen:
                if seen[va] == struct.pack(fmt, target):
                    notes.append("  · UI idx%s.%s 已由尺寸表覆盖且一致" % (r["idx"], field))
                else:
                    notes.append("  · UI idx%s.%s 已被尺寸表写成其它值，保留尺寸表值"
                                 % (r["idx"], field))
                continue
            add(va, size, struct.pack(fmt, mother), struct.pack(fmt, target),
                "D 记录 idx%s.%s %d->%d" % (r["idx"], field, mother, target))
            n_ui += 1
        va, old, tag, note = PANEL
        nv = new_value(tag, old, w, h)
        add(va, 2, struct.pack("<H", old), struct.pack("<H", nv), "D " + note)
        notes.append("  · UI 记录位移：%d 条 + 面板位置 1 条" % n_ui)
    # 6) E 组悬停说明框面板位块（默认**不打**：留着面板才有按钮说明文字；nop 只是 A/B 用）
    if tooltip:
        for va, ob, nb, note in TOOLTIP_SITES:
            add(va, len(ob), ob, nb, note)
    # 7) F 组通用位块助手的裁剪算术（必须改，否则 x>800 区域会被负宽度位块撕裂）
    for va, ob, nb, note in CLIP_ARITH:
        add(va, len(ob), ob, nb, note)
    # 8) G 组：次级界面（战略地图视口 + 子界面文本矩形/居中基准）
    for va, old, tag, note in SECONDARY:
        nv = new_value(tag, old, w, h)
        add(va, 4, struct.pack("<I", old), struct.pack("<I", nv), note)
    # 9) H 组：候选站点（默认打，--no-extra 关）
    if extra:
        for va, old, tag, note in EXTRA:
            nv = new_value(tag, old, w, h)
            add(va, 4, struct.pack("<I", old), struct.pack("<I", nv), note)
    # 10) I 组：0x4A96E8 布局表的右对齐记录（报告 report-panel-table.md）
    #     该表 272 条记录（stride 15B），几何字段 x1@VA / y1@VA+2 / x2@VA+4 / y2@VA+6。
    #     逆向确证：idx 0..263 的几何**运行期绝不被写**（唯一写点 0x45E4AE 只能写
    #     idx 264/265/266），所以静态补丁站得住。
    #     本轮只打「role=RIGHT(+1120) 且宽 <= 500」的 37 条：右边缘的小元素（菜单、
    #     标签、提示框）必须与已补的工具栏按钮一起 +1120 才对齐；宽度 > 500 的
    #     跨屏长条（idx2/7/9/112/203）本轮不动。
    if panel:
        n_panel = 0
        for r in load_tsv("panel_table_v1.tsv"):
            va1, va2 = int(r["va_x1"], 16), int(r["va_x2"], 16)
            x1, x2, dx = int(r["x1"]), int(r["x2"]), int(r["dx"])
            add(va1, 2, struct.pack("<H", x1), struct.pack("<H", x1 + dx),
                "I 布局表 idx%s x1 %d->%d" % (r["idx"], x1, x1 + dx))
            add(va2, 2, struct.pack("<H", x2), struct.pack("<H", x2 + dx),
                "I 布局表 idx%s x2 %d->%d" % (r["idx"], x2, x2 + dx))
            n_panel += 1
        notes.append("  · 布局表右对齐记录：%d 条 × 2 word = %d 处"
                     % (n_panel, 2 * n_panel))
    # 11) M 组：地图面尺寸与地图绘制界 1920 -> 4096（默认打，--no-map 关）
    #     见 MAP_SITES 注释：每帧地图上屏 (0x41FF8A) 的源窗口 = 滚动坐标 + 视口宽高。
    #     视口补宽到 1920 后，地图面仍是 1920x1920 => 只要 scrollX > 0，源矩形右边界
    #     (scrollX + 1920) 就越出地图面（原生 DirectDraw 整笔拒绝）=> 地图区黑。
    #     之前单独打 M 时进场景即全黑，是因为当时横向钳位仍把 scrollX 钳成 -202（源矩形左边界
    #     为负，同样被拒）；N 组修掉钳位后 M 才有意义：面 4096 给了 2176 px 的横向余量、
    #     3065 px 的纵向余量，scrollX/Y >= 0 时源矩形永远在面内。
    if mapmargin:
        for va, note in MAP_SITES:
            add(va, 4, b"\x80\x07\x00\x00", b"\x00\x10\x00\x00", "M " + note)
        notes.append("  · M 地图面/绘制界：%d 处 1920 -> 4096" % len(MAP_SITES))
    # 12) N 组：横向滚动钳位（默认打，--no-scroll 关）
    #     实测（diag_watch.py 日志）：视口 1920x1031，而引擎算出的横向钳位上限
    #       max = mapW - 视口宽 - 1   （mapW=1719 时 = -203~-202；mapW=1631 时 = -290~-291）
    #     是负数，引擎照做，把 scrollX 强设成负数 => 地图位块源矩形从负坐标开始取图
    #     => 地图区黑/错位（"移动两下有时又正常"就是这笔时成时败）。母本 800x600 视口下
    #     这个上限恒为正，所以母本从没暴露过这个问题。
    #     8 处钳位站点结构完全相同：
    #        sub edx,eax / sub edx,1 / cmp ecx,edx / jle 跳过 / ... / mov word [0x4af2f8],cx
    #     把 cmp 改成 cmp eax,eax（ZF=1 => jle 恒成立 => 跳过 store）即可不再把 scrollX 钳成负数。
    #     纵向（0x4af2fc）的 8 处钳位不加这一改：地图高 1351 > 视口 1031，纵向确实需要钳位。
    if scrollfix:
        for va, old in ((0x41F375, 0xd0), (0x4229DF, 0xca), (0x422B07, 0xca),
                        (0x422FEE, 0xca), (0x424D91, 0xd0), (0x440FFF, 0xc1),
                        (0x44DE89, 0xca), (0x4569CA, 0xd0)):
            add(va, 1, bytes([old]), b"\xc0",
                "N 横向滚动钳位: cmp -> cmp eax,eax（守卫 0x%08X）" % (va - 1))
        notes.append("  · N 横向滚动钳位：8 处（不再强制负滚动；纵向钳位保留）")

    # R 组：地图屏每帧整块重绘（见文件头 MAPREPAINT 的注释）。默认打；若性能变差或阴影异常，
    # 用 --no-maprepaint 一键回退。
    if maprepaint:
        va, ob, nb, note = MAPREPAINT
        add(va, len(ob), ob, nb, note)
        notes.append("  · R 地图屏每帧整块重绘：1 处（选中单位后范围阴影立刻上屏）")
    # S 组：地图每帧上屏（见文件头 PRESENT 的注释）。默认打；用 --no-present 一键回退。
    if present:
        va, ob, nb, note = PRESENT
        add(va, len(ob), ob, nb, note)
        notes.append("  · S 地图每帧上屏：1 处（滚动不变也把地图面 BltFast 上屏）")
    # T 组：移动范围每帧重算（默认不打，用 --range-every 打开）。见文件头 RANGE_EVERY 注释。
    if rangeevery:
        va, ob, nb, note = RANGE_EVERY
        add(va, len(ob), ob, nb, note)
        notes.append("  · T 移动范围每帧重算：1 处（鼠标不动也按当前格重算范围表）")
    return entries, notes


# ---------------- Windows API ----------------
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
DWORD = ctypes.c_uint32
SIZE_T = ctypes.c_size_t


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", DWORD), ("lpReserved", ctypes.c_wchar_p),
                ("lpDesktop", ctypes.c_wchar_p), ("lpTitle", ctypes.c_wchar_p),
                ("dwX", DWORD), ("dwY", DWORD), ("dwXSize", DWORD),
                ("dwYSize", DWORD), ("dwXCountChars", DWORD),
                ("dwYCountChars", DWORD), ("dwFillAttribute", DWORD),
                ("dwFlags", DWORD), ("wShowWindow", ctypes.c_ushort),
                ("cbReserved2", ctypes.c_ushort),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", ctypes.c_void_p),
                ("hStdOutput", ctypes.c_void_p), ("hStdError", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", ctypes.c_void_p), ("hThread", ctypes.c_void_p),
                ("dwProcessId", DWORD), ("dwThreadId", DWORD)]


CREATE_SUSPENDED = 0x00000004
PAGE_EXECUTE_READWRITE = 0x40
PROCESS_ALL = 0x1F0FFF


def pe_image_base_of(path):
    with open(path, "rb") as f:
        d = f.read(0x400)
    e = struct.unpack_from("<I", d, 0x3C)[0]
    base = struct.unpack_from("<I", d, e + 0x34)[0]
    dllchar = struct.unpack_from("<H", d, e + 0x5E)[0]
    return base, bool(dllchar & 0x40)  # (PreferredBase, DYNAMIC_BASE?)


def wow64_peb_image_base(hp):
    """取 32 位进程的实际模块基址（WOW64 下读 32 位 PEB +0x8）"""
    buf = ctypes.c_void_p()
    ret = SIZE_T()
    # ProcessWow64Information = 26 -> 32 位 PEB 地址
    st = ntdll.NtQueryInformationProcess(ctypes.c_void_p(hp), 26,
                                         ctypes.byref(buf),
                                         ctypes.sizeof(buf), ctypes.byref(ret))
    if st == 0 and buf.value:
        out = ctypes.c_uint32()
        n = SIZE_T()
        if k32.ReadProcessMemory(ctypes.c_void_p(hp),
                                 ctypes.c_void_p(buf.value + 0x8),
                                 ctypes.byref(out), 4, ctypes.byref(n)) and n.value == 4:
            return out.value
    return None


class Tee(object):
    """把控制台输出同时写进 UTF-8 日志文件（双击 .cmd 出问题时可直接看这个文件）。"""

    def __init__(self, stream, path):
        self.stream = stream
        self.f = None
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.f = open(path, "a", encoding="utf-8")
            self.f.write("\n===== %s   %s =====\n"
                         % (time.strftime("%Y-%m-%d %H:%M:%S"), " ".join(sys.argv[1:])))
        except OSError:
            self.f = None

    def write(self, s):
        try:
            self.stream.write(s)
        except Exception:
            pass
        if self.f:
            try:
                self.f.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self):
        for f in (self.stream, self.f):
            try:
                f.flush()
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, required=True)
    ap.add_argument("--h", type=int, required=True)
    ap.add_argument("--exe", default=MOTHER)
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--no-ui", action="store_true")
    ap.add_argument("--no-repaint", action="store_true")
    ap.add_argument("--no-canvas", action="store_true")
    ap.add_argument("--no-tooltip", action="store_true",
                    help="nop 掉悬停说明框面板位块（会一起弄丢说明文字，仅供 A/B）")
    ap.add_argument("--dx", action="store_true",
                    help="打 K 组：res_diff_v4.tsv 里 163 条 dx 位置行（x/right 水平位移，+1120）；不含 dy")
    ap.add_argument("--dx-all", action="store_true",
                    help="K 组全开（dx+dy，实测会带回黑空洞）")
    ap.add_argument("--keep-dx", action="store_true", help="（兼容保留）同“不打 K 组”，现为默认")
    ap.add_argument("--no-extra", action="store_true",
                    help="不打 H 组候选站点（整屏重绘区登记 + 25x25 格子剔除）")
    ap.add_argument("--no-panel", action="store_true",
                    help="不打 I 组（0x4A96E8 布局表的 37 条右对齐记录）")
    ap.add_argument("--no-map", action="store_true",
                    help="不打 M 组（地图面/地图绘制界 1920 -> 4096；默认打，实测配合 N 组才有效）")
    ap.add_argument("--no-scroll", action="store_true",
                    help="不打 N 组（横向滚动钳位修正；默认打）")
    ap.add_argument("--maprepaint", action="store_true",
                    help="打 R 组（地图屏每帧整块重绘；默认不打：实测对阴影无效，疑似退出卡死来源）")
    ap.add_argument("--present", action="store_true",
                    help="打 S 组（地图每帧上屏；默认不打：实测对阴影无效，疑似退出卡死来源）")
    ap.add_argument("--range-every", action="store_true",
                    help="打 T 组（移动范围每帧重算；默认不打。选中单位后鼠标不动也应出阴影）")
    ap.add_argument("--relayout", action="store_true",
                    help="打重排版 P1（docs\\80）：0x4A96E8 控件矩形表按“等比缩放+以屏幕中心为不动点”"
                         "重排（1076 条站点）；自动关掉会冲突的 I 组（同表 37 条右对齐）与 K 组（dx/dy 平推）")
    ap.add_argument("--relayout-strategy", default="S2", choices=["S1", "S2"],
                    help="S2=高度优先 s=H/600（默认，16:9 玩法）；S1=等比 s=min(W/800,H/600)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log", default=os.path.join(OUT, "launcher-log.txt"),
                    help="日志文件（默认 work\\peg\\out\\launcher-log.txt）")
    ap.add_argument("--selftest", action="store_true",
                    help="挂起启动→打补丁→校验→立即杀死（游戏不会执行任何指令）")
    a = ap.parse_args()

    if a.log:
        sys.stdout = Tee(sys.stdout, os.path.abspath(a.log))
        sys.stderr = sys.stdout
    print("启动器：%s" % os.path.abspath(__file__))

    if a.w < 800 or a.h < 600:
        raise SystemExit("拒绝：需 w>=800 且 h>=600")

    with open(a.exe, "rb") as f:
        head = f.read(1 << 20)
    md5 = hashlib.md5()
    with open(a.exe, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            md5.update(chunk)
    print("目标 exe ：%s" % a.exe)
    print("  md5    ：%s  (%s)" % (md5.hexdigest(),
                                  "母本一致" if md5.hexdigest() == MOTHER_MD5 else "！非母本"))
    print("  分辨率 ：%d x %d" % (a.w, a.h))

    entries, notes = build_plan(a.w, a.h,
                                ui=not a.no_ui, repaint=not a.no_repaint,
                                canvas=not a.no_canvas,
                                tooltip=a.no_tooltip,
                                extra=not a.no_extra,
                                panel=(not a.no_panel) and not a.relayout,
                                dxdy=(False if a.relayout else
                                      ("all" if a.dx_all else ("x" if a.dx else False))),
                                mapmargin=not a.no_map, scrollfix=not a.no_scroll,
                                maprepaint=a.maprepaint, present=a.present,
                                rangeevery=a.range_every)
    if a.relayout:
        sys.path.insert(0, os.path.join(HERE, "relayout"))
        import resolve as _relayout
        rl_entries, rl_notes = _relayout.relayout_plan(a.w, a.h, a.relayout_strategy)
        entries += rl_entries
        notes += rl_notes
    print("补丁站点：%d 条" % len(entries))
    for n in notes:
        print(n)
    if a.dry_run:
        print("\n---- 逐条明细（前 200 条）----")
        for e in entries[:200]:
            print("  %#010x  %d 字节  %-12s  %s -> %s" % (
                e["va"], e["size"], e["old"].hex(), e["new"].hex(), e["label"]))
        print("(dry-run：未启动进程、未改内存)")
        return 0

    base_pref, aslr = pe_image_base_of(a.exe)
    cwd = a.cwd or os.path.dirname(a.exe)
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    pi = PROCESS_INFORMATION()
    last_err = 0
    for attempt in range(1, 4):          # WinError 5（安全软件瞬时拦截）重试
        ok = k32.CreateProcessW(ctypes.c_wchar_p(a.exe), None, None, None, False,
                                CREATE_SUSPENDED, None, ctypes.c_wchar_p(cwd),
                                ctypes.byref(si), ctypes.byref(pi))
        if ok:
            break
        last_err = ctypes.get_last_error()
        print("CreateProcess 第 %d 次失败：%s" % (attempt, ctypes.WinError(last_err)))
        time.sleep(0.7)
    if not ok:
        raise SystemExit(
            "CreateProcess 失败（已重试 3 次）：%s\n"
            "  常见原因：安全软件拦截「挂起启动」、exe 路径不对、权限不足。\n"
            "  可先用同目录的 PeG030.exe 直接双击确认游戏本身能跑。" % ctypes.WinError(last_err))
    print("已挂起启动：pid=%d" % pi.dwProcessId)
    try:
        img = wow64_peb_image_base(pi.hProcess)
        if img is None:
            img = base_pref
            print("  （取不到 PEB，按首选基址 %#x；ASLR=%s）" % (base_pref, aslr))
        else:
            print("  实际模块基址：%#x" % img)
        delta = img - IMAGE_BASE

        # 先全部校验，再统一写
        bad = []
        for e in entries:
            addr = e["va"] + delta
            buf = ctypes.create_string_buffer(e["size"])
            n = SIZE_T()
            if not k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess),
                                         ctypes.c_void_p(addr), buf, e["size"],
                                         ctypes.byref(n)) or n.value != e["size"]:
                bad.append((e, "读失败"))
                continue
            cur = buf.raw[:e["size"]]
            if cur not in (e["old"], e["new"]):
                bad.append((e, "内容=%s 期望 %s" % (cur.hex(), e["old"].hex())))
        if bad:
            print("❌ 校验不通过 %d 条（未做任何写入）：" % len(bad))
            for e, why in bad[:20]:
                print("   %#010x %s : %s" % (e["va"], e["label"], why))
            return 3

        written = 0
        for e in entries:
            addr = e["va"] + delta
            old_prot = DWORD()
            if not k32.VirtualProtectEx(ctypes.c_void_p(pi.hProcess),
                                        ctypes.c_void_p(addr), e["size"],
                                        PAGE_EXECUTE_READWRITE, ctypes.byref(old_prot)):
                print("❌ VirtualProtectEx 失败于 %#x" % e["va"])
                return 3
            n = SIZE_T()
            if not k32.WriteProcessMemory(ctypes.c_void_p(pi.hProcess),
                                          ctypes.c_void_p(addr), e["new"], e["size"],
                                          ctypes.byref(n)) or n.value != e["size"]:
                print("❌ WriteProcessMemory 失败于 %#x" % e["va"])
                return 3
            back = ctypes.create_string_buffer(e["size"])
            k32.ReadProcessMemory(ctypes.c_void_p(pi.hProcess),
                                  ctypes.c_void_p(addr), back, e["size"],
                                  ctypes.byref(n))
            if back.raw[:e["size"]] != e["new"]:
                print("❌ 回读不一致于 %#x" % e["va"])
                return 3
            k32.VirtualProtectEx(ctypes.c_void_p(pi.hProcess),
                                 ctypes.c_void_p(addr), e["size"],
                                 old_prot, ctypes.byref(DWORD()))
            written += 1
        print("✅ 内存补丁完成：%d 条已写入并回读一致（exe 文件未改动）" % written)

        if a.selftest:
            k32.TerminateProcess(ctypes.c_void_p(pi.hProcess), 0)
            print("selftest：已终止进程（游戏未执行任何指令，也没有窗口）")
            return 0
        k32.ResumeThread(ctypes.c_void_p(pi.hThread))
        print("▶ 已放行，游戏开始运行。")
        return 0
    finally:
        k32.CloseHandle(ctypes.c_void_p(pi.hThread))
        k32.CloseHandle(ctypes.c_void_p(pi.hProcess))


if __name__ == "__main__":
    sys.exit(main())
