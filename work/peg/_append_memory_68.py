# -*- coding: utf-8 -*-
"""向 .workbuddy\\memory\\MEMORY.md 追加一条（自动取下一个编号，幂等）。"""
import io, re, os

P = r"D:\DSH\军事游戏汉化\.workbuddy\memory\MEMORY.md"
MARK = "DDrawCompat 换层实测"

src = io.open(P, encoding="utf-8").read()
if MARK in src:
    print("已有该条目，跳过")
else:
    nums = [int(m.group(1)) for m in re.finditer(r"(?m)^(\d+)\.\s", src)]
    nxt = (max(nums) + 1) if nums else 1
    item = u"""
%d. ⭐ **DDrawCompat 换层实测：画面能出、输入全死；启动器 --dx 重复参数已修**（2026-10-15）
- 事实：换入 DDrawCompat 0.7.1（`archive\\ddraw\\ddraw-DDrawCompat-0.7.1.dll`，md5 `26275ed572a4df16141b26e952b50106`）后游戏能启动、能渲染 1920x1080，但**鼠标完全不动**（用户实测）。换回 Svens 包装（md5 `337866f0c870384f5a16c8a11c46a963`，159,232 B）即恢复。
- 取证收获：DDrawCompat 留下 17.7 MB / 149,621 行**逐次 DirectDraw 调用日志**（`D:\\Program Files\\PeG\\DDrawCompat-PeG030.log`）：`SetDisplayMode(1920,1080,16)`、`SetColorKey(&surf, 8, {0xf81f,0xf81f})` 3795 次、`CreateSurface` 3800 次（多为 caps 0x840 的系统内存小块）、`Lock/Unlock` 3791 对、`Blt` 655、`BltFast` 190、`Flip` 仅 2 次、`GetDC/DrawTextExA` 各 6-7 次。关键形状：`BltFast(&P,0,0,&P,{0,0,800,600},16)`（2 次）、`Blt(&P,{0,0,80,60},&P,{1209,565,1289,625},0x1000000)`（186 次，保存/恢复 80x60）、`Blt(&P,{1209,565,1219,583},&P,{0,0,10,18},0x1008000)`（186 次，与取证器抓到的那次命中一致）。
- 输入死的判断：DDrawCompat 默认 `FullscreenMode = borderless`（自建无边框窗口盖住游戏窗口 ⇒ 游戏收不到鼠标消息）。已加 `--play` 试玩配置（ini = LogLevel=info + FullscreenMode=exclusive(0) + MouseSensitivity/MousePollingRate=native + GdiInterops=all），入口 `D:\\Program Files\\PeG\\进游戏-16比9-DDrawCompat试玩.cmd` + 同名 .lnk；应急还原入口 `还原显示层.cmd`；已删除三个失效的「诊断-*」入口。
- 启动器：`peg_launcher.py` 的重复 `--dx/--keep-dx` 参数已修；现默认 **236 条**、`--dx`（仅水平位移的 163 条 dx 行，去重后）**372 条**；自测均通过（先校验、再写入、回读一致，exe 未改）。
- 纪律：换层脚本必须「换入前校 md5，无论怎么退出都 finally 换回」；窗口被强关会漏还原 ⇒ 保留 `--restore` 入口；调试器路线（DEBUG_ONLY_THIS_PROCESS）在 32 位进程上会让游戏建不出窗口，已废弃。
""" % nxt
    with io.open(P, "a", encoding="utf-8") as f:
        f.write(item)
    print("已追加第 %d 条，文件现 %d 字节" % (nxt, os.path.getsize(P)))
