# -*- coding: utf-8 -*-
"""v6：把界面「面板左缘基准 620」在四处代码里的立即数改成 844（= 新面板左缘）。

前情（v5a/v5b 为什么还会花）：
  1024×768 下面板矩形由代码硬编码：右 799 / 下 571 → 左 = 右 − 180 + 1 = 620。
  v5a/v5b 已经把 799→1023、571→740 改掉，面板变成 {844, 22, 1023, 740}；
  但**画控件的代码里还有 4 处把「620」当面板左缘基准**（做 `620 − 控件x` 这类运算），
  它们没跟着改 → 控件记录的 x 已经右移到 986，而绘制路径仍按 620 运算 ⇒ 位置算成
  越界值 ⇒ 花屏/横向拉伸条。

真因证据（母本，`find_imm.py 0x26c` 只有 4 处命中，全是面板左缘语义）：
  FO 0x01B967  VA 0x41C567  `sub ecx, 0x26c`     面板子控件坐标换算
  FO 0x01C51E  VA 0x41D11E  `mov eax, 0x26c`     控件绘制回调 0x41D0AC 里的 `620 − 控件x`
  FO 0x05F772  VA 0x460372  `push 0x26c`         矩形绘制调用 0x47E5A0 的 x 参数
  FO 0x0704A2  VA 0x4710A2  `mov eax, 0x26c`     同类 `620 − 控件x`

本脚本的输入是 v5a/v5b 产物（不碰母本、不碰中文补丁），只做这 4 处等长替换。
用法：
    python patch_v6_panelref.py                 # 干跑，列出将要改的 4 处
    python patch_v6_panelref.py --apply         # 生成 out\v6a.exe / out\v6b.exe
    python patch_v6_panelref.py --src-v5b-only --apply
"""
import os
import sys
import hashlib
import shutil

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
GAMEDIR = GAME_ALT

# 输入产物（v5 变体）与其 md5
INPUTS = [
    ("v6a", os.path.join(OUT, "v5a.exe"), "8b03c59b638a9020557bcbd0a67bbbac"),
    ("v6b", os.path.join(OUT, "v5b.exe"), "0d38ae6222d3b0dff30298ea3072c69f"),
]

OLD = bytes.fromhex("6c020000")   # 620
NEW = bytes.fromhex("4c030000")   # 844

# (名称, 文件偏移, VA, 上下文指令)
SITES = [
    ("panel-child",  0x01B967, 0x41C567, "sub ecx, 0x26c"),
    ("draw-widget",  0x01C51E, 0x41D11E, "mov eax, 0x26c   (620 - 控件x)"),
    ("draw-rect-1",  0x05F772, 0x460372, "push 0x26c"),
    ("draw-rect-2",  0x0704A2, 0x4710A2, "mov eax, 0x26c   (620 - 控件x)"),
]

# 中文补丁三处（必须在产物里仍然成立）
CN_CHECKS = [
    ("charset 0x4718E3", 0x070CE3, bytes.fromhex("6a86")),
    ("__mbcodepage 0x4ABC8C", 0x0A948C, bytes.fromhex("a803")),
    ("LCID 0x7BE86", 0x07BE86, bytes.fromhex("b804080000")),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    apply = "--apply" in sys.argv
    print("=== v6 面板左缘基准 620 -> 844 ===")
    print("干跑模式" if not apply else "**应用模式**")

    for name, src, want_md5 in INPUTS:
        if not os.path.exists(src):
            print("\n[%s] 跳过：输入不存在 %s" % (name, src))
            continue
        d = bytearray(open(src, "rb").read())
        got = md5(bytes(d))
        print("\n[%s] 输入 %s" % (name, src))
        print("      md5 %s" % got)
        if got != want_md5:
            print("      !! md5 与记录不符（期望 %s）——中止，未修改" % want_md5)
            continue

        ok = True
        for label, fo, va, ctx in SITES:
            cur = bytes(d[fo:fo + 4])
            if cur == NEW:
                print("      %-12s FO 0x%06X VA 0x%06X 已是 844（幂等跳过）  %s" % (label, fo, va, ctx))
                continue
            if cur != OLD:
                print("      %-12s FO 0x%06X VA 0x%06X 期望 %s，实际 %s —— 不匹配，中止" %
                      (label, fo, va, OLD.hex(), cur.hex()))
                ok = False
                continue
            print("      %-12s FO 0x%06X VA 0x%06X %s -> %s   %s" %
                  (label, fo, va, OLD.hex(), NEW.hex(), ctx))
            if apply:
                d[fo:fo + 4] = NEW
        if not ok:
            print("      !! 有站点不匹配，本变体跳过")
            continue

        if not apply:
            print("      [dry-run] 未写文件。加 --apply 生成。")
            continue

        # 回读校验
        for label, fo, va, ctx in SITES:
            assert bytes(d[fo:fo + 4]) == NEW, "回读失败 @%s" % label
        for label, fo, want in CN_CHECKS:
            cur = bytes(d[fo:fo + len(want)])
            assert cur == want, "中文补丁被破坏：%s 期望 %s 实际 %s" % (label, want.hex(), cur.hex())
        assert len(d) == 734720, "长度变化"

        dst = os.path.join(OUT, name + ".exe")
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            f.write(bytes(d))
        os.replace(tmp, dst)
        print("      写出 %s  md5 %s" % (dst, md5(bytes(d))))
        game = os.path.join(GAMEDIR, "PeG030-%s.exe" % name)
        shutil.copy2(dst, game)
        print("      复制到 %s" % game)
        print("      中文补丁三处复核 OK")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    main()
