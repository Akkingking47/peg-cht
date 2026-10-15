#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 部署：把工作区成品写入游戏目录（**唯一**会写游戏目录的脚本）。

纪律（前作血泪）：
  · **覆盖与备份分两条命令**：本脚本先另存 `<名>.orig-backup`，再覆盖；备份已存在则校验其 sha 一致，不重复备份
  · 默认 **dry-run**，`--apply` 才写
  · 每次写入后 **回读校验**（sha 必须等于成品）
  · **幂等**：目标已等于成品 ⇒ no-op（仍确保备份存在）
  · **绝不从游戏目录读原文来生成产物**（生成侧一律读 testbed/backup/）

用法:
  python deploy.py --exe                     # 12 个 efile（dry-run）
  python deploy.py --exe --apply
  python deploy.py --text WW2Gui.txt --apply
"""
import hashlib
import io
import os
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
OUT_EXE = os.path.join(WS, "pegww2", "testbed", "out", "exe")
OUT_TXT = os.path.join(WS, "pegww2", "testbed", "out", "text")
BK_EXE = os.path.join(WS, "pegww2", "testbed", "backup", "exe")
BK_TXT = os.path.join(WS, "pegww2", "testbed", "backup", "text")
_REPORT = os.path.join(WS, "pegww2", "research", "evidence", "deploy-report.txt")
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
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def deploy(src, dst, apply_, orig_hint=None):
    """返回 (状态串)。

    orig_hint: 工作区里的**原版备份**路径。用于判定「游戏目录里已有的 .orig-backup 是否可信」：
      · 完整可信判据 = 已有 .orig-backup 的 sha == 原版备份 sha
        （⚠️ 不能拿它和「当前目标」比 —— 二次部署时目标已是上一版成品，会比出假冲突。
         本项目实测踩过：WW2Gui.txt 试点版部署后再部署全量版被误判为「备份不一致」而拒绝）
    """
    if not os.path.isfile(src):
        return f"缺成品 {os.path.relpath(src, WS)}"
    if not os.path.isfile(dst):
        return f"⚠ 目标不存在 {dst}"
    ss, ds = sha(src), sha(dst)
    truth = sha(orig_hint) if (orig_hint and os.path.isfile(orig_hint)) else None
    bak = dst + ".orig-backup"
    if ss == ds:
        # 幂等：已部署。确保备份存在
        if os.path.isfile(bak):
            return "已部署(no-op)"
        if apply_:
            shutil.copy2(dst, bak)
            assert sha(bak) == ds
            return "已部署(补建备份)"
        return "已部署(待补建备份)"
    # 需要覆盖 ⇒ 先确认备份链健康
    if os.path.isfile(bak):
        bs = sha(bak)
        if truth is not None:
            if bs != truth:
                return (f"⚠ 已有备份 ≠ 原版(bak={bs[:12]} 原版={truth[:12]}) ⇒ 拒绝覆盖"
                        f"（请人工确认备份链）")
            baknote = "备份已是原版(可信)"
        else:
            baknote = "备份已存在(无原版可比对)"
    else:
        baknote = "将新建备份"
    if not apply_:
        return f"dry-run（{baknote}）"
    if not os.path.isfile(bak):
        if truth is None:
            return "⚠ 无原版可比对且无备份 ⇒ 拒绝覆盖（防把成品当原版备份）"
        shutil.copy2(orig_hint, bak)
        assert sha(bak) == truth, "备份回读校验失败"
    with open(src, "rb") as f:
        data = f.read()
    with open(dst, "wb") as f:
        f.write(data)
    back = sha(dst)
    assert back == ss, f"覆盖后回读校验失败 {back[:12]} != {ss[:12]}"
    return f"已覆盖 + 回读一致（{baknote}）"


def main():
    apply_ = "--apply" in sys.argv
    print("=" * 96)
    print(f"PeG-WW2 部署  {'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print(f"游戏目录: {GAME}")
    print("=" * 96)
    if "--exe" in sys.argv:
        print("\n[efile]")
        for f in sorted(os.listdir(OUT_EXE)):
            if not f.lower().endswith(".exe"):
                continue
            print(f"  {f:24s} {deploy(os.path.join(OUT_EXE, f), os.path.join(GAME, f), apply_, os.path.join(BK_EXE, f))}")
    if "--text" in sys.argv:
        i = sys.argv.index("--text")
        names = []
        for a in sys.argv[i + 1:]:
            if a.startswith("--"):
                break
            names.append(a)
        print("\n[文本]")
        for f in names:
            print(f"  {f:24s} {deploy(os.path.join(OUT_TXT, f), os.path.join(GAME, f), apply_, os.path.join(BK_TXT, f))}")
    if not ("--exe" in sys.argv or "--text" in sys.argv):
        print("\n未指定目标：用 --exe / --text <名…>")
    if not apply_:
        print("\n[DRY-RUN] 未写任何文件。加 --apply 落盘。")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.dirname(_REPORT), exist_ok=True)
    with open(_REPORT, "w", encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
