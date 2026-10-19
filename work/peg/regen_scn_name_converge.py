#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PeG 场景重生成（落实裁定①新名）：**先建到临时目录**，逐文件证明「只改了预期的 13 个名字」，
再 promote 到 `peg\\testbed\\scn-zh`，最后 deploy 到游戏（各步分开，铁律三）。

用法：
    python regen_scn_name_converge.py              # 只建到临时目录 + 差异证明（不动任何现有产物）
    python regen_scn_name_converge.py --promote    # 通过证明后，覆盖 peg\\testbed\\scn-zh
    python regen_scn_name_converge.py --deploy     # 备份游戏侧 + 只写有差异的文件
"""
import hashlib
import io
import os
import shutil
import sys

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scn_zh as G  # noqa: E402

TMP = os.path.join(WS, "peg", "testbed", "_regen-name-converge")
CUR = os.path.join(WS, "peg", "testbed", "scn-zh")
GAMEDIR = GAME
BACKUP = os.path.join(WS, "backup", "before-name-converge", "peg-game")

# 旧名 → 新名（与 fix_name_converge.py 同源；用于「只改预期」证明）
PAIRS = [
    ("阿克罗马", "阿克罗玛"), ("库里", "九里"), ("沃尔日斯基", "伏尔加斯基"),
    ("布尔诺舍沃-俄罗斯科耶", "布尔诺舍沃-鲁斯科耶"), ("奥体川", "奥库泰河"),
    ("镇永", "进永"), ("奇奥", "千绪"), ("千早", "奇瓦盖"), ("初代", "哈茨泰"),
    ("诸塚", "诸津"), ("土路", "塔路"), ("奈川", "内川"),
]


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def walk(root):
    out = {}
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            out[os.path.relpath(p, root).replace("\\", "/")] = p
    return out


def apply_pairs(text, pairs):
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def main():
    do_promote = "--promote" in sys.argv
    do_deploy = "--deploy" in sys.argv

    print("=== 1. 建到临时目录（不碰现有产物）")
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    G.OUTDIR = TMP
    mp = G.load_map()
    lmp = G.load_long()
    nmp = G.load_numbers()
    keys = G.build_matcher(mp)
    print(f"映射表 {len(mp)} 条 · 长段表 {len(lmp)} 条 · 序号表 {len(nmp)} 条")
    # ⚠️ 必须把「按场景定点覆盖」也传进去，否则本脚本重建的产物会忽略该层
    #    （曾因此让 Khabarovsk4_m.txt 的 Amur River 覆盖静默失效）
    ovr = G.load_scn_override()
    print(f"按场景定点覆盖：{len(ovr)} 条（{len({s for s, _ in ovr})} 个场景）")
    G.cmd_build(mp, keys, lmp, nmp, ovr)

    print("\n=== 2. 与现有 scn-zh 比对，并证明差异只是这 13 个名字")
    a, b = walk(TMP), walk(CUR)
    only_tmp = sorted(set(a) - set(b))
    only_cur = sorted(set(b) - set(a))
    changed = []
    for rel in sorted(set(a) & set(b)):
        if md5(a[rel]) != md5(b[rel]):
            changed.append(rel)
    print(f"临时 {len(a)} 个 · 现有 {len(b)} 个 · 内容不同 {len(changed)} 个 "
          f"· 仅临时有 {len(only_tmp)} · 仅现有有 {len(only_cur)}")
    if only_tmp:
        print("   仅临时有:", only_tmp[:10])
    if only_cur:
        print("   仅现有有:", only_cur[:10])

    unexplained = []
    for rel in changed:
        old_t = io.open(b[rel], encoding="gbk", errors="replace").read()
        new_t = io.open(a[rel], encoding="gbk", errors="replace").read()
        if apply_pairs(old_t, PAIRS) == new_t:
            continue
        unexplained.append(rel)
    print(f"   ⇒ 差异可完全由这 13 个名字解释：{len(changed) - len(unexplained)}/{len(changed)}")
    if unexplained:
        print(f"   ⛔ 无法解释的文件 {len(unexplained)} 个（前 12）：")
        for rel in unexplained[:12]:
            old_t = io.open(b[rel], encoding="gbk", errors="replace").read()
            new_t = io.open(a[rel], encoding="gbk", errors="replace").read()
            print(f"      · {rel}")
            for i, (o, n) in enumerate(zip(old_t.splitlines(), new_t.splitlines()), 1):
                if o != n:
                    print(f"          行{i}  旧 {o[:70]!r}")
                    print(f"               新 {n[:70]!r}")
                    break
        print("   ⇒ 未通过证明，停止（不 promote、不 deploy）")
        return
    print(f"   ✅ 全部 {len(changed)} 个差异文件均可解释")

    if not (do_promote or do_deploy):
        print("\n（未加 --promote/--deploy，临时产物保留在 " + TMP + "）")
        return

    print("\n=== 3. promote 到 scn-zh")
    if do_promote:
        n = 0
        for rel, src in a.items():
            dst = os.path.join(CUR, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
        print(f"   已写入 {n} 个文件 → {CUR}")
    else:
        print("   （跳过）")

    if not do_deploy:
        return

    print("\n=== 4. 备份游戏侧（只备份要动的文件）并部署")
    os.makedirs(BACKUP, exist_ok=True)
    n = 0
    for rel in changed:
        sub = rel.split("/")[0]
        dst = os.path.join(GAMEDIR, sub, os.path.basename(rel))
        if not os.path.exists(dst):
            print(f"   ⚠️ 游戏侧不存在，跳过 {rel}")
            continue
        bk = os.path.join(BACKUP, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(dst, bk)                     # 先备份
        n += 1
    print(f"   已备份 {n} 个文件 → {BACKUP}")
    m = 0
    for rel in changed:
        sub = rel.split("/")[0]
        src = os.path.join(CUR, rel.replace("/", os.sep))
        dst = os.path.join(GAMEDIR, sub, os.path.basename(rel))
        if not os.path.exists(dst):
            continue
        shutil.copy2(src, dst)                     # 再覆盖（与备份分开）
        m += 1
    print(f"   已部署 {m} 个文件 → {GAMEDIR}")
    # 回读
    bad = [rel for rel in changed
           if os.path.exists(os.path.join(GAMEDIR, rel.split('/')[0], os.path.basename(rel)))
           and md5(os.path.join(CUR, rel.replace("/", os.sep)))
           != md5(os.path.join(GAMEDIR, rel.split("/")[0], os.path.basename(rel)))]
    print(f"   回读校验：{'✅ 全部一致' if not bad else '❌ ' + str(bad[:6])}")


if __name__ == "__main__":
    main()
