# -*- coding: utf-8 -*-
"""从 CWGEN.dat 抽取 .s16 并渲染（验证 UI 图是否含烘焙文字）"""
import struct, os, sys
from PIL import Image

# ── 路径真源 ────────────────────────────────────────────────────────
# 可用环境变量覆盖；缺省值＝本项目作者本机的目录布局。
WS       = os.environ.get("PEG_WORKSPACE", r"D:\DSH\军事游戏汉化")
GAME     = os.environ.get("PEG_GAME",      r"D:\Program Files\PeG")
GAME_ALT = os.environ.get("PEG_GAME_ALT",  r"D:\Program Files\PeG-1")
# ───────────────────────────────────────────────────────────────────


DAT = os.path.join(GAME, "CWGEN.dat")
OUT = os.path.join(WS, "work", "peg", "s16")
os.makedirs(OUT, exist_ok=True)

def read_dir():
    with open(DAT, "rb") as f:
        cnt, _ = struct.unpack("<II", f.read(8))
        f.seek(8)
        ent = {}
        for _ in range(cnt):
            r = f.read(17)
            nm = r[:13].split(b"\x00")[0].decode("latin-1").upper()
            ofs = struct.unpack("<I", r[13:17])[0]
            ent[nm] = ofs
    return ent

ENT = read_dir()

def parse_s16(name):
    ofs = ENT[name]
    with open(DAT, "rb") as f:
        f.seek(ofs)
        n, = struct.unpack("<I", f.read(4))
        idx = []
        for i in range(n):
            w, h, sx, sy, fw, fh, starts, nbytes, comp, load = struct.unpack("<10I", f.read(40))
            idx.append(dict(i=i, w=w, h=h, sx=sx, sy=sy, fw=fw, fh=fh,
                            starts=starts, nbytes=nbytes, comp=comp, load=load))
        base = f.tell()
        blob = f.read()
    return idx, base, blob

def render(name, which=0, scale=1):
    idx, base, blob = parse_s16(name)
    e = idx[which]
    print(f"{name}: n={len(idx)}  base=0x{base:x}  blob={len(blob)}")
    print(f"  [{which}] {e}")
    # 按 Starts 定位
    off = e["starts"]
    data = blob[off:off + (e["fw"] * e["fh"] * 2 if e["nbytes"] == 0 else e["nbytes"])]
    W, H = e["fw"], e["fh"]
    if e["nbytes"] == 0:
        return None
    if e["comp"] == 0 and e["nbytes"] >= W * H * 2:
        px = struct.unpack_from("<%dH" % (W * H), data, 0)
        img = Image.new("RGB", (W, H))
        img.putdata([((v >> 11) << 3, ((v >> 5) & 0x3F) << 2, (v & 0x1F) << 3) for v in px])
        if scale != 1:
            img = img.resize((W * scale, H * scale), Image.NEAREST)
        fn = os.path.join(OUT, f"{name}_{which}.png")
        img.save(fn)
        print("   -> wrote", fn, img.size)
        return fn
    print("   skip (comp=%d nbytes=%d w*h*2=%d)" % (e["comp"], e["nbytes"], W * H * 2))
    return None

for nm in ["STRNGM.S16", "BUTTN30.S16", "MAINBAR.S16", "ST030.S16", "HEX.S16", "AIRSET.S16"]:
    try:
        idx, base, blob = parse_s16(nm)
        print("\n==", nm, "n=", len(idx))
        for e in idx[:4]:
            print("   ", e)
        # 找最大的几个
        big = sorted(idx, key=lambda d: -d["fw"] * d["fh"])[:3]
        print("    max:", [(d["i"], d["fw"], d["fh"], d["nbytes"], d["comp"], d["starts"]) for d in big])
        render(nm, big[0]["i"])
    except Exception as ex:
        print(nm, "ERR", ex)
