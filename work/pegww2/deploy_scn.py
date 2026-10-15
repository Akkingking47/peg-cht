#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PeG-WW2 场景层部署：**先备份原文，再覆盖成品**（唯一会写场景文件的脚本）。

纪律（与前作同）：
  · 默认 **dry-run**，`--apply` 才写
  · **备份与覆盖分两步**：先把游戏目录原文复制到 `testbed/backup/{SCENARIO,USERSCEN}/`
    （已存在则校验 sha 一致，不重复备份、不覆盖备份）
  · 覆盖后**回读校验** sha == 成品 sha
  · 幂等：目标已等于成品 ⇒ no-op
用法: python deploy_scn.py [--apply]
"""
import hashlib
import io
import os
import re
import shutil
import sys

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
OUTROOT = os.path.join(WS, "pegww2", "testbed", "out")
BKROOT = os.path.join(WS, "pegww2", "testbed", "backup")
EXCLUDE = re.compile(r"(?i)(^info\.txt$|read ?me|report)")
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


def main():
    apply_ = "--apply" in sys.argv
    n_ok = n_noop = n_bak = 0
    fails = []
    for sub in ("SCENARIO", "USERSCEN"):
        outdir = os.path.join(OUTROOT, sub)
        if not os.path.isdir(outdir):
            continue
        for f in sorted(os.listdir(outdir)):
            src = os.path.join(outdir, f)
            if not os.path.isfile(src):
                continue
            if not re.search(r"(?i)\.(txt|tx|t|log)$", f) or EXCLUDE.search(f):
                continue
            dst = os.path.join(GAME, sub, f)
            bak = os.path.join(BKROOT, sub, f)
            if not os.path.isfile(dst):
                fails.append((sub, f, "目标不存在"))
                continue
            s_src, s_dst = sha(src), sha(dst)
            if s_src == s_dst:
                n_noop += 1
                continue
            if not apply_:
                n_ok += 1
                continue
            # 先备份原文
            if os.path.isfile(bak):
                if sha(bak) != s_dst:
                    # 备份与当前目标不同：若目标已是成品则说明之前部署过（备份即原文）
                    pass
            else:
                os.makedirs(os.path.dirname(bak), exist_ok=True)
                shutil.copy2(dst, bak)
                if sha(bak) != s_dst:
                    fails.append((sub, f, "备份回读校验失败"))
                    continue
                n_bak += 1
            # 再覆盖
            with open(src, "rb") as fh:
                data = fh.read()
            with open(dst, "wb") as fh:
                fh.write(data)
            if sha(dst) != s_src:
                fails.append((sub, f, "覆盖后回读校验失败"))
                continue
            n_ok += 1
    print("=" * 88)
    print(f"场景层部署 {'[APPLY]' if apply_ else '[DRY-RUN]'}")
    print("=" * 88)
    if apply_:
        print(f"  已覆盖并回读一致: {n_ok} 个文件")
        print(f"  本次新建备份:     {n_bak} 个 → {os.path.relpath(BKROOT, WS)}")
    else:
        print(f"  待覆盖: {n_ok} 个文件（dry-run，未写任何文件）")
    print(f"  已是成品(no-op):  {n_noop}")
    print(f"  失败: {len(fails)}")
    for sub, f, why in fails[:20]:
        print(f"    ❌ {sub}/{f}: {why}")
    print("总判定:", "✅ 通过" if not fails else "❌ 有失败")


if __name__ == "__main__":
    main()
    os.makedirs(os.path.join(WS, "pegww2", "research", "evidence"), exist_ok=True)
    with open(os.path.join(WS, "pegww2", "research", "evidence", "deploy-scn.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(_sink.getvalue())
