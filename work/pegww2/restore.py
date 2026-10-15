#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 一键回滚：从游戏目录的 `<名>.orig-backup` 还原原版。

纪律：默认 dry-run，`--apply` 才写；还原后回读校验 sha 必须等于工作区原版备份。
用法:
  python restore.py                 # dry-run
  python restore.py --apply         # 还原 12 efile + WW2Gui.txt
  python restore.py --apply --keep-backups   # 还原后删除 .orig-backup（默认保留）
"""
import hashlib
import io
import os
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
BK_EXE = os.path.join(WS, "pegww2", "testbed", "backup", "exe")
BK_TXT = os.path.join(WS, "pegww2", "testbed", "backup", "text")
_REPORT = os.path.join(WS, "pegww2", "research", "evidence", "restore-report.txt")
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


def restore(name, orig_src, apply_, keep):
    cur = os.path.join(GAME, name)
    bak = cur + ".orig-backup"
    if not os.path.isfile(bak):
        return f"⚠ 无备份，跳过（{os.path.basename(bak)} 不存在）"
    s_bak, s_orig, s_cur = sha(bak), sha(orig_src), sha(cur)
    if s_bak != s_orig:
        return f"⚠ 备份与工作区原版不一致 ⇒ 拒绝（bak={s_bak[:12]} orig={s_orig[:12]}）"
    if s_cur == s_orig:
        return "已是原版(no-op)"
    if not apply_:
        return "dry-run（将还原）"
    with open(bak, "rb") as f:
        data = f.read()
    with open(cur, "wb") as f:
        f.write(data)
    assert sha(cur) == s_orig, "还原后回读校验失败"
    msg = "已还原 + 回读一致"
    if not keep:
        os.remove(bak)
        msg += "（并删除备份）"
    return msg


def main():
    apply_ = "--apply" in sys.argv
    keep = "--keep-backups" not in sys.argv
    print("=" * 90)
    print(f"PeG-WW2 回滚  {'[APPLY]' if apply_ else '[DRY-RUN]'}  保留备份={keep}")
    print("=" * 90)
    print("\n[efile]")
    for f in sorted(os.listdir(BK_EXE)):
        if f.lower().endswith(".exe"):
            print(f"  {f:24s} {restore(f, os.path.join(BK_EXE, f), apply_, keep)}")
    print("\n[文本]")
    for f in sorted(os.listdir(BK_TXT)):
        print(f"  {f:24s} {restore(f, os.path.join(BK_TXT, f), apply_, keep)}")
    if not apply_:
        print("\n[DRY-RUN] 未写任何文件。加 --apply 还原。")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
