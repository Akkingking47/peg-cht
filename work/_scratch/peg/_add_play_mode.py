# -*- coding: utf-8 -*-
"""给 diag_ddraw.py 增加 --play（可操作）配置：独占全屏 + 原生鼠标 + info 日志。"""
import io

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
before = len(src)

# ---------- 1) 插入常量 ----------
anchor = "DDC_MD5 = \"26275ed572a4df16141b26e952b50106\""
assert anchor in src, "找不到 DDC_MD5 常量"
INS = '''

# ini 内容：默认只采日志；--play 时换成「可操作」配置
PLAY_SETTINGS = (
    "; play test\n"
    "LogLevel = info\n"
    "FullscreenMode = exclusive\n"
    "MouseSensitivity = native\n"
    "MousePollingRate = native\n"
    "GdiInterops = all\n")
INI_SETTINGS = os.environ.get("DDC_INI_SETTINGS", "LogLevel = trace\n")
'''
src = src.replace(anchor, anchor + INS, 1)

# ---------- 2) ini 写入内容改为 INI_SETTINGS ----------
old_ini = '"LogLevel = trace\\n")'
assert old_ini in src, "找不到 ini 写入语句"
src = src.replace(old_ini, "INI_SETTINGS)", 1)

# ---------- 3) CLI 增加 --play ----------
old_cli = '    ap.add_argument("--dry-run", action="store_true")'
assert old_cli in src
src = src.replace(old_cli, old_cli + '\n    ap.add_argument("--play", action="store_true",\n'
                  '                    help="用可操作配置（独占全屏 + 原生鼠标 + info 日志）换层，供人工试玩")', 1)

# ---------- 4) main 里让 --play 生效 ----------
old_parse = "    a = ap.parse_args()\n"
assert old_parse in src
src = src.replace(old_parse, old_parse +
                  '    if getattr(a, "play", False):\n'
                  '        global INI_SETTINGS\n'
                  '        INI_SETTINGS = PLAY_SETTINGS\n', 1)

io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
print("原 %d 字节 → 现 %d 字节" % (before, len(chk)))
for k in ("PLAY_SETTINGS", "INI_SETTINGS", "--play", "INI_SETTINGS)"):
    print("  %-14s 出现 %d 次" % (k, chk.count(k)))
import ast
ast.parse(chk)
print("语法 OK")
