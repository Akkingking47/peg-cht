#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PeG-WW2 场景重生成（落实裁定①新名）：建到临时目录 → 逐文件证明「只改了预期的 12 个名字」
→ promote 到 `pegww2\\testbed\\out` → deploy 到游戏。各步分开（铁律三）。

用法：
    python regen_scn_name_converge.py              # 只建到临时目录 + 差异证明
    python regen_scn_name_converge.py --promote    # 通过证明后覆盖 pegww2\\testbed\\out
    python regen_scn_name_converge.py --deploy     # 备份游戏侧 + 只写有差异的文件
"""
import hashlib
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_scn as G  # noqa: E402

WS = r"D:\DSH\军事游戏汉化"
TMP = os.path.join(WS, "pegww2", "testbed", "_regen-name-converge")
CUR = os.path.join(WS, "pegww2", "testbed", "out")
GAMEDIR = r"D:\Program Files\PeG-WW2"
BACKUP = os.path.join(WS, "backup", "before-name-converge", "ww2-game")

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
    G.OUTROOT = TMP                                  # ⭐ 关键：只改模块全局，不动正式 out
    G.main()

    print("\n=== 2. 与现有 out 比对，并证明差异只是这 12 个名字")
    a, b = walk(TMP), walk(CUR)
    only_tmp = sorted(set(a) - set(b))
    only_cur = sorted(set(b) - set(a))
    changed = [rel for rel in sorted(set(a) & set(b)) if md5(a[rel]) != md5(b[rel])]
    print(f"临时 {len(a)} 个 · 现有 out {len(b)} 个 · 内容不同 {len(changed)} 个 "
          f"· 仅临时有 {len(only_tmp)} · 仅现有有 {len(only_cur)}")
    if only_tmp:
        print("   仅临时有:", only_tmp[:10])
    if only_cur:
        print("   仅现有有:", only_cur[:10])

    unexplained = []
    for rel in changed:
        old_t = io.open(b[rel], encoding="gbk", errors="replace").read()
        new_t = io.open(a[rel], encoding="gbk", errors="replace").read()
        if apply_pairs(old_t, PAIRS) != new_t:
            unexplained.append(rel)
    print(f"   ⇒ 差异可完全由这 12 个名字解释：{len(changed) - len(unexplained)}/{len(changed)}")
    if unexplained:
        print(f"   ⛔ 无法解释的文件 {len(unexplained)} 个（前 10）：")
        for rel in unexplained[:10]:
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

    print("\n=== 3. promote 到 out")
    if do_promote:
        n = 0
        for rel in changed + only_tmp:
            dst = os.path.join(CUR, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(a[rel], dst)
            n += 1
        print(f"   已写入 {n} 个文件 → {CUR}")
    else:
        print("   （跳过）")

    if not do_deploy:
        return

    print("\n=== 4. 备份游戏侧（只备份要动的文件）并部署")
    os.makedirs(BACKUP, exist_ok=True)
    targets = changed + only_tmp
    n = 0
    for rel in targets:
        dst = os.path.join(GAMEDIR, rel.replace("/", os.sep))
        if not os.path.exists(dst):
            continue
        bk = os.path.join(BACKUP, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(dst, bk)
        n += 1
    print(f"   已备份 {n} 个文件 → {BACKUP}")
    m = 0
    for rel in targets:
        src = os.path.join(CUR, rel.replace("/", os.sep))
        dst = os.path.join(GAMEDIR, rel.replace("/", os.sep))
        if not os.path.exists(dst):
            print(f"   ⚠️ 游戏侧不存在，跳过 {rel}")
            continue
        shutil.copy2(src, dst)
        m += 1
    print(f"   已部署 {m} 个文件 → {GAMEDIR}")
    bad = [rel for rel in targets
           if os.path.exists(os.path.join(GAMEDIR, rel.replace("/", os.sep)))
           and md5(os.path.join(CUR, rel.replace("/", os.sep)))
           != md5(os.path.join(GAMEDIR, rel.replace("/", os.sep)))]
    print(f"   回读校验：{'✅ 全部一致' if not bad else '❌ ' + str(bad[:6])}")


if __name__ == "__main__":
    main()
