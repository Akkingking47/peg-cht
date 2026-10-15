# -*- coding: utf-8 -*-
"""把试玩配置参数化：--mode exclusive|borderless（默认 exclusive）。
   exclusive 解决了输入；borderless 已知画面/截图正常。两者其它设置相同。"""
import io, ast

P = r"D:\DSH\军事游戏汉化\work\peg\diag_ddraw.py"
src = io.open(P, encoding="utf-8").read()
NL = chr(92) + "n"

start = src.index("# ini 内容")
endmark = 'INI_SETTINGS = os.environ.get("DDC_INI_SETTINGS", "LogLevel = trace' + NL + '")'
end = src.index(endmark) + len(endmark)

block = "\n".join([
    "# ini 内容：默认只采日志；--play 时按 --mode 生成试玩配置",
    "def play_settings(mode):",
    '    """试玩用 ini：mode = exclusive | borderless"""',
    '    fs = "exclusive(0)" if mode == "exclusive" else "borderless"',
    '    return ("; play test (%s)' + NL + '"',
    '            "LogLevel = info' + NL + '"',
    '            "FullscreenMode = %s' + NL + '"',
    '            "MouseSensitivity = native' + NL + '"',
    '            "MousePollingRate = native' + NL + '"',
    '            "GdiInterops = all' + NL + '") % (mode, fs)',
    "",
    "",
    endmark,
])
src = src[:start] + block + src[end:]

# main 里改成按 --mode 生成
old_hook = '        INI_SETTINGS = PLAY_SETTINGS'
new_hook = '        INI_SETTINGS = play_settings(a.mode)'
assert src.count(old_hook) == 1, "找不到 main 钩子"
src = src.replace(old_hook, new_hook, 1)

# CLI 增加 --mode
old_cli = '    ap.add_argument("--play", action="store_true",'
assert src.count(old_cli) == 1
src = src.replace(old_cli,
                  '    ap.add_argument("--mode", default="exclusive",\n'
                  '                    choices=["exclusive", "borderless"],\n'
                  '                    help="--play 时的全屏模式（exclusive 修输入；borderless 画面/截图正常）")\n'
                  + old_cli, 1)

io.open(P, "w", encoding="utf-8", newline="").write(src)
chk = io.open(P, encoding="utf-8").read()
ast.parse(chk)
print("语法 OK，%d 字节" % len(chk))
for i, ln in enumerate(chk.splitlines(), 1):
    if "play_settings" in ln or "--mode" in ln or "FullscreenMode" in ln:
        print("  %d| %s" % (i, ln.strip()[:110]))
