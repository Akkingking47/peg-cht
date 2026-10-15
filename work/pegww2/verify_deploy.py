#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 部署后独立核验：游戏目录现状 vs 成品 vs 原版三方 sha 对齐。

判据（缺一不可）：
  · 游戏目录当前文件 sha == 成品 sha            （覆盖生效）
  · `<名>.orig-backup` sha == 原版备份 sha      （备份链完整）
  · 游戏目录当前文件 sha != 原版 sha            （确实变了）
"""
import hashlib
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BK_EXE = os.path.join(WS, "pegww2", "testbed", "backup", "exe")
BK_TXT = os.path.join(WS, "pegww2", "testbed", "backup", "text")
OUT_EXE = os.path.join(WS, "pegww2", "testbed", "out", "exe")
OUT_TXT = os.path.join(WS, "pegww2", "testbed", "out", "text")
_REPORT = os.path.join(WS, "pegww2", "research", "evidence", "verify-deploy.txt")
_sink = io.StringIO()


class _Tee:
    def __init__(self, *s):
        self.s = s

    def write(self, x):
        for t in self.s:
            t.write(x)
        return len(x)

    def flush(self):
        for t in self.s:
            t.flush()


sys.stdout = _Tee(sys.stdout, _sink)


def sha(p):
    if not os.path.isfile(p):
        return "(缺)"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def check(label, cur, prod, orig, bakpath):
    s_cur, s_prod, s_orig, s_bak = sha(cur), sha(prod), sha(orig), sha(bakpath)
    ok = (s_cur == s_prod) and (s_bak == s_orig) and (s_cur != s_orig)
    print(f"  {label:24s} {'✅' if ok else '❌'}  当前={s_cur[:12]} 成品={s_prod[:12]} "
          f"原版={s_orig[:12]} 备份文件={s_bak[:12]}  [{os.path.basename(bakpath)}]")
    return ok


def main():
    print("=" * 104)
    print("部署后核验（游戏目录 / 成品 / 原版 三方 sha 对齐）")
    print("=" * 104)
    allok = True
    print("\n[efile]")
    for f in sorted(os.listdir(OUT_EXE)):
        if not f.lower().endswith(".exe"):
            continue
        allok &= check(f, os.path.join(GAME, f), os.path.join(OUT_EXE, f),
                       os.path.join(BK_EXE, f), os.path.join(GAME, f + ".orig-backup"))
    print("\n[文本]")
    for f in sorted(os.listdir(OUT_TXT)):
        allok &= check(f, os.path.join(GAME, f), os.path.join(OUT_TXT, f),
                       os.path.join(BK_TXT, f), os.path.join(GAME, f + ".orig-backup"))

    print("\n[试点内容抽查]（游戏目录当前 WW2Gui.txt 的试点行）")
    import re
    raw = open(os.path.join(GAME, "WW2Gui.txt"), "rb").read()
    lines = re.split(rb"\r\n|\r|\n", raw)
    for ln, want in [(40, "下一部队"), (44, "补给"), (46, "征募部队"),
                     (54, "结束回合"), (61, "全屏"), (63, "退出游戏")]:
        got = lines[ln - 1].decode("gbk", "replace")
        print(f"  行{ln:<4d} {got:12s} {'✅' if got == want else '❌ 期望 ' + want}")
    print(f"\n  行数 {len(lines)}（原版 605）")

    print("\n[本批新增抽查]（界面层文件的行数一致性 + 关键行）")
    for f, nsrc in (("WW2Misc.txt", 45), ("WW2Tips.TXT", 44)):
        b = open(os.path.join(GAME, f), "rb").read()
        ls = re.split(rb"\r\n|\r|\n", b)
        print(f"  {f}: 行数 {len(ls)}（原版 {nsrc}） {'✅' if len(ls) == nsrc else '❌'}")
    b = open(os.path.join(GAME, "WW2Tips.TXT"), "rb").read()
    ls = re.split(rb"\r\n|\r|\n", b)
    print(f"  提示 行1 = {ls[0].decode('gbk', 'replace')[:50]}")
    b = open(os.path.join(GAME, "WW2Misc.txt"), "rb").read()
    ls = re.split(rb"\r\n|\r|\n", b)
    print(f"  杂项 行12(地形) = {ls[11].decode('gbk', 'replace')} / 行1 = {ls[0].decode('gbk', 'replace')}")
    print("\n" + ("=" * 104))
    print(f"总判定: {'✅ 全部对齐，可实机验证' if allok else '❌ 存在不一致，勿实机'}")
    return 0 if allok else 1


if __name__ == "__main__":
    rc = main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
    sys.exit(rc)
