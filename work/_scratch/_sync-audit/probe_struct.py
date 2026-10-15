# -*- coding: utf-8 -*-
"""只读侦察：两作「地图地名栏」与「简报/说明文件」的真实载体结构。"""
import os, re, sys

G1 = r"D:\Program Files\PeG"
G2 = r"D:\Program Files\PeG-WW2"


def fld(b, o, n=40):
    return b[o:o + n].split(b"\x00")[0].decode("latin-1")


def survey(tag, root, scndir, onedir):
    S = os.path.join(root, scndir)
    print("=" * 78)
    print(f"### {tag}  {S}")
    if not os.path.isdir(S):
        print("   (不存在)"); return
    files = os.listdir(S)
    print(f"   目录内文件 {len(files)} 个")
    exts = {}
    for f in files:
        e = os.path.splitext(f)[1].lower()
        exts[e] = exts.get(e, 0) + 1
    print("   扩展名分布：", dict(sorted(exts.items(), key=lambda x: -x[1])[:12]))
    # 找一个同时有 _m 与 .scn 的 stem
    stems = set(f[:-4] for f in files if f.lower().endswith('.scn'))
    cand = None
    for st in sorted(stems):
        if os.path.isfile(os.path.join(S, st + "_m.txt")) or os.path.isfile(os.path.join(S, st + "_m.TXT")):
            cand = st; break
    print(f"   .scn {len(stems)} 个；样本 stem = {cand}")
    if not cand:
        return
    # .scn 字段
    p = os.path.join(S, cand + ".scn")
    b = open(p, "rb").read()
    print(f"   {cand}.scn 大小 {len(b)} · @11329='{fld(b,11329)}' · @11349=0x{b[11349]:02X}")
    intro, flag = fld(b, 11329), b[11349]
    for dd, ex in ((onedir, ".ply"), (S, ".TXT")) if flag else ((S, ".TXT"), (onedir, ".ply")):
        for nm in (intro + ex, intro + ex.lower(), intro + ex.upper()):
            fp = os.path.join(dd, nm)
            if os.path.isfile(fp):
                t = open(fp, "rb").read()
                print(f"   ⭐简报文件 {os.path.relpath(fp, root)}  {len(t)} B")
                try:
                    s = t.decode("gbk")
                    print("      解码 gbk 前 6 非空行：")
                    n = 0
                    for ln in re.split(r"\r\n|\r|\n", s):
                        if ln.strip():
                            print("        | " + ln.strip()[:96]); n += 1
                            if n >= 6: break
                except Exception as e:
                    print("      gbk 解码失败", e)
                break
        else:
            continue
        break
    # 地图地名栏
    for nm in (cand + "_m.txt", cand + "_m.TXT"):
        fp = os.path.join(S, nm)
        if os.path.isfile(fp):
            t = open(fp, "rb").read()
            print(f"   ⭐地图地名栏 {nm}  {len(t)} B")
            try:
                s = t.decode("gbk")
                ls = [x for x in re.split(r"\r\n|\r|\n", s) if x.strip()]
                print(f"      非空行 {len(ls)}；前 12 行：")
                for ln in ls[:12]:
                    print("        | " + ln.strip()[:96])
            except Exception as e:
                print("      gbk 解码失败", e)
            break


survey("PeG（前作）", G1, "Scenario", "Scenario")
survey("PeG-WW2", G2, "SCENARIO", "USERSCEN")
