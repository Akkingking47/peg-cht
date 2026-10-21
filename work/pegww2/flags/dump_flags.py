# -*- coding: utf-8 -*-
"""从 WW2GEN.dat 导出旗集（FLAGS*.S16）并渲染成对照图 —— 只读。

用途：判断 6 套旗集中哪一套是「史实旗集」，为后续替换/换集提供证据。

容器格式（实测，与 work\\peg\\render_s16.py 一致）：
  .dat 头 = <II: cnt, unk>；随后 cnt 条 × 17 字节：13 字节名字(latin-1,NUL 截断) + 4 字节 LE 偏移
  条目 = <I n>；随后 n 条 × 40 字节帧表 <10I>：w h sx sy fw fh starts nbytes comp load
  帧数据 = base + starts 起 nbytes 字节；base = 帧表结束处（偏移相对 base）

帧编码：
  comp==0：w*h 个 RGB565 小端 u16 原图
  comp==1：RLE —— 重复 (count:u8, color:u16LE)，解出 w*h 个像素
  ⚠️ 像素数 = w*h（不是 fw*fh）；fw/fh 是外框，sx/sy 是外框内偏移
  ⚠️ 0xF81F 是洋红透键（rubber 色）

用法：
    python work\\pegww2\\flags\\dump_flags.py --list
    python work\\pegww2\\flags\\dump_flags.py --render FLAGSE.S16
    python work\\pegww2\\flags\\dump_flags.py --render-all
    python work\\pegww2\\flags\\dump_flags.py --meta FLAGSE.S16
"""
import argparse
import os
import struct
import sys

from PIL import Image, ImageDraw

WS = r"D:\DSH\军事游戏汉化"
GAME = r"D:\Program Files\PeG-WW2"
DAT = os.path.join(GAME, "WW2GEN.dat")
OUT = os.path.join(WS, "work", "pegww2", "flags", "out")
KEY = 0xF81F          # 洋红透键
SETS = ["FLAGS1.S16", "FLAGSB.S16", "FLAGSD.S16", "FLAGSE.S16", "FLAGSM.S16", "FLAGSV.S16"]


def read_dir(path=DAT):
    with open(path, "rb") as f:
        cnt, _ = struct.unpack("<II", f.read(8))
        f.seek(8)
        ent = {}
        for _ in range(cnt):
            r = f.read(17)
            nm = r[:13].split(b"\x00")[0].decode("latin-1").upper()
            ent[nm] = struct.unpack("<I", r[13:17])[0]
    return ent


ENT = read_dir()


def frames(name):
    """返回 (帧表list, base)。"""
    with open(DAT, "rb") as f:
        f.seek(ENT[name])
        n, = struct.unpack("<I", f.read(4))
        idx = []
        for i in range(n):
            w, h, sx, sy, fw, fh, starts, nbytes, comp, load = struct.unpack("<10I", f.read(40))
            idx.append(dict(i=i, w=w, h=h, sx=sx, sy=sy, fw=fw, fh=fh,
                            starts=starts, nbytes=nbytes, comp=comp, load=load))
        base = f.tell()
    return idx, base


def raw_bytes(e, base):
    with open(DAT, "rb") as f:
        f.seek(base + e["starts"])
        return f.read(e["nbytes"])


# ---------- 内存缓冲版（apply/verify 用，避免盘上状态与内存不一致） ----------

def read_dir_buf(buf):
    cnt, = struct.unpack_from("<I", buf, 0)
    ent = {}
    for i in range(cnt):
        r = bytes(buf[8 + i * 17: 8 + i * 17 + 17])
        nm = r[:13].split(b"\x00")[0].decode("latin-1").upper()
        ent[nm] = struct.unpack_from("<I", r, 13)[0]
    return ent


def frames_buf(name, buf, ent):
    off = ent[name]
    n, = struct.unpack_from("<I", buf, off)
    idx = []
    p = off + 4
    for i in range(n):
        w, h, sx, sy, fw, fh, starts, nbytes, comp, load = struct.unpack_from("<10I", buf, p)
        idx.append(dict(i=i, w=w, h=h, sx=sx, sy=sy, fw=fw, fh=fh,
                        starts=starts, nbytes=nbytes, comp=comp, load=load))
        p += 40
    return idx, p


def raw_buf(e, base, buf):
    return bytes(buf[base + e["starts"]: base + e["starts"] + e["nbytes"]])


def decode(e, data):
    """解出 w*h 个 RGB565 像素。"""
    npx = e["w"] * e["h"]
    if e["comp"] == 0:
        return list(struct.unpack_from("<%dH" % npx, data, 0))
    out = []
    i = 0
    L = len(data)
    while i + 3 <= L and len(out) < npx:
        c = data[i]
        col = struct.unpack_from("<H", data, i + 1)[0]
        i += 3
        out.extend([col] * c)
    return out[:npx]


def rgb565(v):
    if v == KEY:
        return (255, 0, 255)
    return (((v >> 11) & 0x1F) << 3, ((v >> 5) & 0x3F) << 2, (v & 0x1F) << 3)


def build_frame(e, base):
    px = decode(e, raw_bytes(e, base))
    img = Image.new("RGB", (e["fw"], e["fh"]), (255, 0, 255))
    for y in range(e["h"]):
        for x in range(e["w"]):
            img.putpixel((e["sx"] + x, e["sy"] + y), rgb565(px[y * e["w"] + x]))
    return img


def classify(v):
    if v == KEY:
        return "."
    r, g, b = rgb565(v)
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 45:
        return "K"
    if mn > 205:
        return "W"
    if r > 150 and g < 90 and b < 90:
        return "R"
    if 60 < r <= 150 and g < 70 and b < 70:
        return "r"
    if r > 160 and g > 160 and b < 110:
        return "Y"
    if g > 100 and r < 120 and b < 120:
        return "G"
    if b > 110 and r < 110 and g < 130:
        return "B"
    if b > 150 and g > 150 and r < 150:
        return "b"
    if mx - mn < 40:
        return "x"
    return "?"


def grid(name, which, step=1):
    idx, base = frames(name)
    for i in which:
        e = idx[i]
        px = decode(e, raw_bytes(e, base))
        img = [[KEY] * e["fw"] for _ in range(e["fh"])]
        for y in range(e["h"]):
            for x in range(e["w"]):
                img[e["sy"] + y][e["sx"] + x] = px[y * e["w"] + x]
        print("-- %s [%d]  w=%d h=%d sx=%d sy=%d fw=%d fh=%d comp=%d nbytes=%d  step=%d" %
              (name, i, e["w"], e["h"], e["sx"], e["sy"], e["fw"], e["fh"], e["comp"], e["nbytes"], step))
        for r in range(0, e["fh"], step):
            print("   " + "".join(classify(v) for v in img[r][::step]))


def cmp_sets(a, b, n=20):
    """逐国籍比对两套旗集第 0 块的像素签名，列出差异。"""
    import hashlib
    fa, ba = frames(a)
    fb, bb = frames(b)
    nations = [l.strip() for l in
               open(os.path.join(GAME, "WW2Gui.txt.orig-backup"), encoding="latin-1").read().splitlines()]
    print("== %s  vs  %s  (块0, 前 %d 国籍)" % (a, b, n))
    for i in range(min(n, len(fa), len(fb))):
        pa = decode(fa[i], raw_bytes(fa[i], ba))
        pb = decode(fb[i], raw_bytes(fb[i], bb))
        ha = hashlib.sha1(struct.pack("<%dH" % len(pa), *pa)).hexdigest()[:8]
        hb = hashlib.sha1(struct.pack("<%dH" % len(pb), *pb)).hexdigest()[:8]
        nm = nations[i] if i < len(nations) else "?"
        print("  %2d %-14s %s  %s   %s" % (i, nm, ha, hb, "SAME" if ha == hb else "DIFF"))


TARGETS = {  # 德国帧 = 大旗 4 拷贝(i,i+20,i+40,i+60) + 小旗 2 拷贝(80+i,100+i)
    "FLAGS1.S16": [2, 22, 42, 62, 82, 102],
    "FLAGSD.S16": [2, 22, 42, 62, 82, 102],
    "FLAGSE.S16": [2, 22, 42, 62, 82, 102],
}


def sample_palette():
    """从现有 FLAGSE[2] 采样红/白，保证与引擎渲染一致；黑固定 0x0000。"""
    from collections import Counter
    idx, base = frames("FLAGSE.S16")
    px = decode(idx[2], raw_bytes(idx[2], base))
    c = Counter(px)
    reds = sorted(((v, n) for v, n in c.items() if classify(v) in ("R", "r")),
                  key=lambda kv: -kv[1])
    whites = sorted(((v, n) for v, n in c.items() if classify(v) == "W"),
                    key=lambda kv: -kv[1])
    return (reds[0][0] if reds else 0xF800, whites[0][0] if whites else 0xFFFF)


BM9 = ["....BBBB.", "B...B....", "B...B....", "B...B....",
       "BBBBBBBBB", "....B...B", "....B...B", "....B...B", "..BBB...."]
BM5 = ["..BB.", "B.B..", "BBBBB", ".B..B", ".BB.."]   # 顺时针钩：上→东 右→南 下→西 左→北

PNG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "reich_flag_800.png")
_PNG = False   # False=未加载 / None=无文件 / Image=已加载
_PNG_Q = None  # (w0, h0, 三色覆盖掩码 bytes×3)


def png_img():
    global _PNG
    if _PNG is False:
        _PNG = Image.open(PNG_PATH).convert("RGB") if os.path.exists(PNG_PATH) else None
    return _PNG


def png_masks(pal_rgb):
    """史实旗 PNG → 满分辨率三色量化 → 圆盘居中化 → 三张覆盖掩码（只算一次）。
    ① 直接对 RGB 最近色量化会让黑/白边界的抗锯齿灰被吸到 RED（红比白更近中灰），
      盘内出现红噪点；先钉成索引色再按掩码面积多数表决则边缘干净。
    ② Wikimedia《Flag_of_Germany_(1935–1945).svg》是圆盘偏旗杆侧的国防旗版
      （实测盘心 x=359.5 ≠ 画布中心 400）；裁圆盘方块贴回画布中心合成居中版。"""
    global _PNG_Q
    if _PNG_Q is None:
        src = png_img()
        w0, h0 = src.size
        sbuf = src.tobytes()
        q = bytearray(w0 * h0)
        for k in range(w0 * h0):
            i3 = k * 3
            r, g, b = sbuf[i3], sbuf[i3 + 1], sbuf[i3 + 2]
            bd, bc = 1 << 30, 0
            for ci, (pr, pg, pb) in enumerate(pal_rgb):
                dd = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
                if dd < bd:
                    bd, bc = dd, ci
            q[k] = bc
        # 圆盘居中化：白盘 bbox → 裁正方块 → 贴回画布中心
        xs = [k % w0 for k, v in enumerate(q) if v == 1]
        ys = [k // w0 for k, v in enumerate(q) if v == 1]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        s = max(x1 - x0, y1 - y0) + 1
        scx, scy = (x0 + x1) // 2, (y0 + y1) // 2
        q2 = bytearray(w0 * h0)                       # 全红底
        sx0, sy0 = scx - s // 2, scy - s // 2
        dx0, dy0 = w0 // 2 - s // 2, h0 // 2 - s // 2
        for yy in range(s):
            srow, drow = sy0 + yy, dy0 + yy
            if 0 <= srow < h0 and 0 <= drow < h0:
                for xx in range(s):
                    sx, dx = sx0 + xx, dx0 + xx
                    if 0 <= sx < w0 and 0 <= dx < w0:
                        q2[drow * w0 + dx] = q[srow * w0 + sx]
        masks = [bytes(255 if v == c else 0 for v in q2) for c in range(3)]
        _PNG_Q = (w0, h0, masks[0], masks[1], masks[2])
    return _PNG_Q


def drawable_rect(name, w, h):
    """可绘区（含端点）。保留原图描边/底座结构：
    大旗 FLAGSE=白上/左+黑右/下描边；FLAGS1/FLAGSD=黑右/下描边；
    小旗=黑环（FLAGSE 另有 rows8-10 白底座）。"""
    if w >= 15:
        if name == "FLAGSE.S16":
            return 1, h - 2, 1, w - 2
        return 0, h - 2, 0, w - 2
    return 1, 7, 1, w - 2


def compose(name, e, orig, RED, WHITE, BLACK=0x0000):
    """在原帧像素上合成史实德国旗：保留描边/底座，重绘可绘区为 红底+白盘+黑卐。
    有 assets/reich_flag_800.png 时 = PNG LANCZOS 缩放 + 三色量化（真实图案）；
    无素材时退回内置 BM9/BM5 字形自绘。"""
    w, h = e["w"], e["h"]
    px = list(orig)
    r0, r1, c0, c1 = drawable_rect(name, w, h)
    rw, rh = c1 - c0 + 1, r1 - r0 + 1
    pal_v = (RED, WHITE, BLACK)
    pal_rgb = (rgb565(RED), rgb565(WHITE), (0, 0, 0))
    src = png_img()
    if src is not None:
        # 三色覆盖掩码 BOX 面积缩放 → 逐像素多数表决（平票偏向 黑>白>红）
        w0, h0, m0, m1, m2 = png_masks(pal_rgb)
        cov = [Image.frombytes("L", (w0, h0), m).resize((rw, rh), Image.BOX).tobytes()
               for m in (m0, m1, m2)]
        for y in range(rh):
            row = (r0 + y) * w + c0
            bi = y * rw
            for x in range(rw):
                px[row + x] = pal_v[max((cov[0][bi + x], 0), (cov[1][bi + x], 1),
                                        (cov[2][bi + x], 2))[1]]
        return px
    big = (r1 - r0 + 1) >= 9
    cx, cy = (c0 + c1) / 2.0, (r0 + r1) / 2.0
    r = min(c1 - c0 + 1, r1 - r0 + 1) / 2.0 - 0.5
    for y in range(r0, r1 + 1):
        for x in range(c0, c1 + 1):
            px[y * w + x] = WHITE if (x - cx) ** 2 + (y - cy) ** 2 <= r * r else RED
    bm = BM9 if big else BM5
    ox, oy = int(cx) - len(bm[0]) // 2, int(cy) - len(bm) // 2
    for yy, row in enumerate(bm):
        for xx, ch in enumerate(row):
            if ch == "B":
                X, Y = ox + xx, oy + yy
                if r0 <= Y <= r1 and c0 <= X <= c1 and px[Y * w + X] == WHITE:
                    px[Y * w + X] = BLACK
    return px


def encode_rle_min(px):
    """最小 RLE (count:u8, color:u16)，count 上限 255。"""
    out = bytearray()
    i, n = 0, len(px)
    while i < n:
        v = px[i]
        j = i
        while j < n and px[j] == v and j - i < 255:
            j += 1
        out.append(j - i)
        out += struct.pack("<H", v)
        i = j
    return bytes(out)


def encode_rle(px, nbytes):
    """就地写入版：不足 nbytes 用 count=0 空游程补齐（解码端 0 像素，无害）。"""
    return pad_rle(encode_rle_min(px), nbytes)


def pad_rle(data, nbytes):
    """把已编码 RLE 补齐到 nbytes。"""
    need = nbytes - len(data)
    if need < 0 or need % 3:
        raise SystemExit("RLE 长度 %d 与目标 nbytes=%d 不兼容" % (len(data), nbytes))
    return data + b"\x00\x00\x00" * (need // 3)


def preview(RED, WHITE):
    """合成全部目标帧并输出 ASCII 网格 + PNG 蒙太奇（不落盘）。"""
    cells = []
    for name, ids in TARGETS.items():
        idx, base = frames(name)
        for i in ids:
            e = idx[i]
            orig = decode(e, raw_bytes(e, base))
            px = compose(name, e, orig, RED, WHITE)
            img = Image.new("RGB", (e["w"], e["h"]))
            img.putdata([rgb565(v) for v in px])
            cells.append((name, i, e, px, img))
    for nm, i, e, px, _ in cells:
        if (nm, i) in (("FLAGS1.S16", 2), ("FLAGSE.S16", 2), ("FLAGSE.S16", 82), ("FLAGS1.S16", 82)):
            print("-- %s [%d]（合成稿） w=%d h=%d" % (nm, i, e["w"], e["h"]))
            for y in range(e["h"]):
                print("   " + "".join(classify(v) for v in px[y * e["w"]:(y + 1) * e["w"]]))
    sc = 12
    reps, seen = [], set()
    for nm, i, e, px, img in cells:
        if e["w"] not in seen:
            seen.add(e["w"])
            reps.append((nm, i, e, img))
    W = sum(e["w"] for _, _, e, _ in reps) * sc + (len(reps) + 1) * 10
    H = max(e["h"] for _, _, e, _ in reps) * sc + 12
    mont = Image.new("RGB", (W, H), (24, 24, 24))
    d = ImageDraw.Draw(mont)
    x = 5
    for nm, i, e, img in reps:
        big = img.resize((e["w"] * sc, e["h"] * sc), Image.NEAREST)
        mont.paste(big, (x, 0))
        d.text((x + 1, e["h"] * sc + 2), "%s[%d]" % (nm[:6], i), fill=(255, 255, 0))
        x += e["w"] * sc + 10
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, "german_redesign_preview.png")
    mont.save(fn)
    print("\n预览图 ->", fn, mont.size)


def rebuild_set_buf(name, buf, ent, repl):
    """整体重建旗集 blob：repl = {帧号: 新RLE字节}（其余帧字节原样保留）。
    内容尾之后的尾部整体后移，目录中偏移 >= 旧内容尾 的条目 += 增量。
    前置断言：帧 starts 连续、blob 内无其他条目。"""
    idx, base = frames_buf(name, buf, ent)
    blob_start = ent[name]
    pos = 0
    for e in idx:
        if e["starts"] != pos:
            raise SystemExit("%s starts 不连续 @%d（%d != %d），拒绝重排" %
                             (name, e["i"], e["starts"], pos))
        pos += e["nbytes"]
    content_end = base + pos
    for nm2, o2 in ent.items():
        if blob_start < o2 < content_end:
            raise SystemExit("%s blob 内部存在其他条目 %s@%d" % (name, nm2, o2))
    tbl = bytearray(struct.pack("<I", len(idx)))
    data = bytearray()
    for e in idx:
        if e["i"] in repl:
            d = repl[e["i"]]
            nb = len(d)
        else:
            d = bytes(buf[base + e["starts"]: base + e["starts"] + e["nbytes"]])
            nb = e["nbytes"]
        tbl += struct.pack("<10I", e["w"], e["h"], e["sx"], e["sy"], e["fw"], e["fh"],
                           len(data), nb, e["comp"], e["load"])
        data += d
    new_blob = bytes(tbl) + bytes(data)
    grow = len(new_blob) - (content_end - blob_start)
    tail = bytes(buf[content_end:])
    cur_eof = content_end + len(tail)                  # 拼接前当前 EOF
    buf[blob_start:] = new_blob + tail
    cnt, = struct.unpack_from("<I", buf, 0)
    patched = beyond = 0
    for i in range(cnt):
        p = 8 + i * 17 + 13
        o, = struct.unpack_from("<I", buf, p)
        if content_end <= o < cur_eof:
            struct.pack_into("<I", buf, p, o + grow)
            patched += 1
        elif o >= cur_eof:
            beyond += 1
    print("%s blob重排: %d -> %d B (%+d)，尾部后移 %d B，目录补丁 %d 条%s" %
          (name, content_end - blob_start, len(new_blob), grow, len(tail), patched,
           "" if not beyond else "，⚠ %d 条偏移越界(未动)" % beyond))


def apply_flags(dry=True):
    RED, WHITE = sample_palette()
    print("调色: RED=0x%04X WHITE=0x%04X BLACK=0x0000" % (RED, WHITE))
    bak = DAT + ".orig-backup"
    if not dry and not os.path.exists(bak):
        import shutil
        shutil.copy2(DAT, bak)
        print("已备份 ->", os.path.basename(bak))
    buf = bytearray(open(DAT, "rb").read())
    size0 = len(buf)
    ent = read_dir_buf(buf)
    # 哨兵条目（原偏移≥原EOF，空 blob）：跨多次重排会被当成普通条目误补丁，
    # 其终态偏移恒为 原偏移+总增量（=新 EOF），最后强制修正。
    cnt0, = struct.unpack_from("<I", buf, 0)
    sentinels = {}
    for i in range(cnt0):
        nm = bytes(buf[8 + i * 17: 8 + i * 17 + 13]).split(b"\x00")[0].decode("latin-1").upper()
        if ent[nm] >= size0:
            sentinels[nm] = ent[nm]
    if sentinels:
        print("哨兵条目:", {k: v for k, v in sentinels.items()})
    plan = {}
    for name, ids in TARGETS.items():
        idx, base = frames_buf(name, buf, ent)
        d = {}
        for i in ids:
            e = idx[i]
            orig = decode(e, raw_buf(e, base, buf))
            px = compose(name, e, orig, RED, WHITE)
            data = encode_rle_min(px)
            assert decode(dict(e, comp=1), data) == px, "round-trip %s[%d]" % (name, i)
            fits = len(data) <= e["nbytes"]
            d[i] = (e, data, fits)
            print("%-11s[%3d] w=%2d h=%2d 旧nbytes=%3d 新RLE=%3d  %s" %
                  (name, i, e["w"], e["h"], e["nbytes"], len(data),
                   "就地写入" if fits else "触发blob重排"))
        plan[name] = d
    if dry:
        print("\ndry-run 完成，未写盘。")
        return
    rebuilt = []
    for name, ids in TARGETS.items():
        d = plan[name]
        if any(not d[i][2] for i in ids):
            rebuild_set_buf(name, buf, ent, {i: d[i][1] for i in ids})
            ent = read_dir_buf(buf)
            rebuilt.append(name)
    for name, ids in TARGETS.items():
        if name in rebuilt:
            continue
        d = plan[name]
        idx2, base2 = frames_buf(name, buf, ent)
        for i in ids:
            e = idx2[i]
            data = pad_rle(d[i][1], e["nbytes"])
            s = base2 + e["starts"]
            buf[s: s + e["nbytes"]] = data
    if sentinels:
        total = len(buf) - size0
        nfix = 0
        for i in range(cnt0):
            nm = bytes(buf[8 + i * 17: 8 + i * 17 + 13]).split(b"\x00")[0].decode("latin-1").upper()
            if nm in sentinels:
                exp = sentinels[nm] + total
                cur, = struct.unpack_from("<I", buf, 8 + i * 17 + 13)
                if cur != exp:
                    struct.pack_into("<I", buf, 8 + i * 17 + 13, exp)
                    nfix += 1
        if nfix:
            print("哨兵条目终态修正: %d 条（总增量 %+d）" % (nfix, total))
    open(DAT, "wb").write(buf)
    print("\n已写盘 -> %s（%d 字节，增量 %+d）" % (DAT, len(buf), len(buf) - size0))


def fix_sentinel():
    """修复当前 dat 中哨兵条目（原偏移≥原EOF，空 blob）的目录偏移：
    跨多次重排会被误当普通条目补丁，正确终态 = 原偏移 + 总增量（=新 EOF）。"""
    old = open(DAT + ".orig-backup", "rb").read()
    buf = bytearray(open(DAT, "rb").read())
    eo, en = read_dir_buf(old), read_dir_buf(buf)
    total = len(buf) - len(old)
    cnt, = struct.unpack_from("<I", buf, 0)
    nfix = 0
    for i in range(cnt):
        nm = bytes(buf[8 + i * 17: 8 + i * 17 + 13]).split(b"\x00")[0].decode("latin-1").upper()
        oo = eo[nm]
        if oo >= len(old):
            exp = oo + total
            if en[nm] != exp:
                struct.pack_into("<I", buf, 8 + i * 17 + 13, exp)
                print("修复哨兵 %s: %d -> %d" % (nm, en[nm], exp))
                nfix += 1
            else:
                print("哨兵 %s 已正确 @%d" % (nm, en[nm]))
    if nfix:
        open(DAT, "wb").write(buf)
        print("已写盘，修复 %d 条（总增量 %+d）" % (nfix, total))
    else:
        print("无需修复")


def verify():
    """apply 后回读校验：目录/偏移/帧元数据/像素逐一比对备份。"""
    bak = DAT + ".orig-backup"
    if not os.path.exists(bak):
        raise SystemExit("无备份 %s，无法校验" % bak)
    old = open(bak, "rb").read()
    new = open(DAT, "rb").read()
    grow = len(new) - len(old)
    print("文件大小: %d -> %d (%+d)" % (len(old), len(new), grow))
    eo, en = read_dir_buf(old), read_dir_buf(new)

    def nmlist(b):
        cnt, = struct.unpack_from("<I", b, 0)
        return [bytes(b[8 + i * 17: 8 + i * 17 + 13]) for i in range(cnt)]
    print("目录名字序列一致:", nmlist(old) == nmlist(new))
    # 各重建集尺寸增量（帧数据 nbytes 总差；帧表大小不变）：(旧内容尾, 尺寸增量)
    grows = []
    for name in TARGETS:
        io_, bo = frames_buf(name, old, eo)
        in_, bn = frames_buf(name, new, en)
        g = sum(e["nbytes"] for e in in_) - sum(e["nbytes"] for e in io_)
        if g:
            grows.append((bo + sum(e["nbytes"] for e in io_), g))
    print("重建增量:", grows)
    same = shifted = 0
    weird = []
    exp_of = {}
    for nm, oo in eo.items():
        # 哨兵条目（oo≥原EOF）同样适用该公式：其 ce 全部命中 → exp = oo+总增量 = 新EOF
        exp = oo + sum(g for ce, g in grows if oo >= ce)
        exp_of[nm] = exp
        on = en[nm]
        if on == oo:
            same += 1
        elif on == exp:
            shifted += 1
        else:
            weird.append((nm, oo, on, exp))
    print("目录偏移: 不变 %d 条 / 按预期后移 %d 条 / 异常 %d 条" % (same, shifted, len(weird)))
    for w in weird[:10]:
        print("   异常:", w)

    RED, WHITE = sample_palette()
    bad = 0
    for name in SETS + ["VICFLAGS.S16"]:
        if name not in eo or name not in en:
            continue
        io_, bo = frames_buf(name, old, eo)
        in_, bn = frames_buf(name, new, en)
        if len(io_) != len(in_):
            print("✗ %s 帧数 %d -> %d" % (name, len(io_), len(in_)))
            bad += 1
            continue
        tg = set(TARGETS.get(name, []))
        ndiff = 0
        for e1, e2 in zip(io_, in_):
            meta_keys = ("w", "h", "sx", "sy", "fw", "fh", "comp", "load")
            if any(e1[k] != e2[k] for k in meta_keys):
                print("✗ %s[%d] 帧元数据变化" % (name, e1["i"]))
                bad += 1
            p1 = decode(e1, raw_buf(e1, bo, old))
            p2 = decode(e2, raw_buf(e2, bn, new))
            if e1["i"] in tg:
                exp = compose(name, e1, p1, RED, WHITE)
                if p2 != exp:
                    print("✗ %s[%d] 新像素 != 预期合成稿" % (name, e1["i"]))
                    bad += 1
                if p1 == p2:
                    print("✗ %s[%d] 目标帧未变化" % (name, e1["i"]))
                    bad += 1
                ndiff += 1
            elif p1 != p2:
                print("✗ %s[%d] 非目标帧像素变化" % (name, e1["i"]))
                bad += 1
        if ndiff:
            print("✓ %-13s %d 帧已替换，其余 %d 帧不变" % (name, ndiff, len(io_) - ndiff))

    # 非旗资源抽查：HEAD 2 条（最早重建点之前）+ TAIL 3 条（最晚重建点之后，按各自预期偏移对齐）
    byoff = sorted(eo.items(), key=lambda kv: kv[1])
    if grows:
        lo = min(eo[n] for n in TARGETS)
        ce_max = max(ce for ce, _ in grows)
        head = [nm for nm, o in byoff if o < lo][-2:]
        tail = [nm for nm, o in byoff if o >= ce_max and o < len(old)]
        tail = [tail[0], tail[len(tail) // 2], tail[-1]]
        for nm in head:
            o, e = eo[nm], exp_of[nm]
            ok = old[o:o + 4096] == new[e:e + 4096]
            print("%s HEAD %-13s @%d 字节一致: %s" % ("✓" if ok else "✗", nm, o, ok))
            bad += 0 if ok else 1
        for nm in tail:
            o, e = eo[nm], exp_of[nm]
            ok = old[o:o + 4096] == new[e:e + 4096]
            print("%s TAIL %-13s @%d -> @%d 字节一致: %s" % ("✓" if ok else "✗", nm, o, e, ok))
            bad += 0 if ok else 1
        if grow:
            print("（文件总增量 %d B = 各重建增量之和 %d B: %s）" %
                  (grow, sum(g for _, g in grows), sum(g for _, g in grows) == grow))
            bad += 0 if sum(g for _, g in grows) == grow else 1
    print("\n校验结果: %s（%d 处问题）" % ("全部通过" if bad == 0 else "存在失败", bad))
    return bad


def dupes(name, n=20):
    """同一旗集内，两个国籍共用同一张旗 = 明显的错旗嫌疑。"""
    import hashlib
    idx, base = frames(name)
    nations = [l.strip() for l in
               open(os.path.join(GAME, "WW2Gui.txt.orig-backup"), encoding="latin-1").read().splitlines()]
    seen = {}
    for i in range(min(n, len(idx))):
        px = decode(idx[i], raw_bytes(idx[i], base))
        h = hashlib.sha1(struct.pack("<%dH" % len(px), *px)).hexdigest()[:8]
        seen.setdefault(h, []).append(i)
    print("== %s  重复旗组:" % name)
    bad = 0
    for h, ids in sorted(seen.items(), key=lambda kv: kv[1][0]):
        if len(ids) > 1:
            bad += 1
            print("   %s -> %s" % (h, ", ".join("%d(%s)" % (i, nations[i] if i < len(nations) else "?") for i in ids)))
    if not bad:
        print("   (无重复)")


def meta(name, show_all=False):
    idx, base = frames(name)
    dims = {}
    comps = {}
    print("== %s  frames=%d  base=%d" % (name, len(idx), base))
    for e in idx:
        dims[(e["w"], e["h"])] = dims.get((e["w"], e["h"]), 0) + 1
        comps[e["comp"]] = comps.get(e["comp"], 0) + 1
    print("   (w,h) 分布:", sorted(dims.items(), key=lambda kv: -kv[1]))
    print("   comp 分布:", comps)
    if show_all:
        for e in idx:
            print("   %3d w=%2d h=%2d sx=%d sy=%d fw=%2d fh=%2d comp=%d nbytes=%d" %
                  (e["i"], e["w"], e["h"], e["sx"], e["sy"], e["fw"], e["fh"], e["comp"], e["nbytes"]))
    return idx, base


def render(name, scale=6, cols=12, pad=2, label=True):
    idx, base = frames(name)
    cells = [e for e in idx if e["fw"] > 0 and e["fh"] > 0 and e["w"] > 0]
    if not cells:
        print(name, "无可渲染帧"); return None
    cw = max(e["fw"] for e in cells) * scale + pad
    ch = max(e["fh"] for e in cells) * scale + pad + (10 if label else 0)
    rows = (len(cells) + cols - 1) // cols
    mont = Image.new("RGB", (cols * cw, rows * ch), (24, 24, 24))
    d = ImageDraw.Draw(mont)
    for k, e in enumerate(cells):
        img = build_frame(e, base).resize((e["fw"] * scale, e["fh"] * scale), Image.NEAREST)
        r, c = divmod(k, cols)
        x, y = c * cw, r * ch
        mont.paste(img, (x, y))
        if label:
            d.text((x + 1, y + e["fh"] * scale + 1), "%d" % e["i"], fill=(255, 255, 0))
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name.replace(".", "_") + "_montage.png")
    mont.save(fn)
    print("%-12s 渲染 %d 帧 → %s  %s" % (name, len(cells), fn, mont.size))
    return fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--meta", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--grid", nargs="+", default=None,
                    help="SET [i,j,...]  无索引则全部")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--draw", action="store_true", help="绘制史实德国旗预览（不写盘）")
    ap.add_argument("--dry-run", action="store_true", help="apply 预演：只打印规划不写盘")
    ap.add_argument("--apply", action="store_true", help="写入 WW2GEN.dat（先自动备份）")
    ap.add_argument("--verify", action="store_true", help="apply 后回读校验（对比 .orig-backup）")
    ap.add_argument("--fix-sentinel", action="store_true",
                    help="修复哨兵条目（原偏移≥原EOF）的目录偏移到 原偏移+总增量")
    ap.add_argument("--dupes", default=None)
    ap.add_argument("--cmp", nargs=2, default=None, help="SET_A SET_B")
    ap.add_argument("--render", default=None)
    ap.add_argument("--render-all", action="store_true")
    ap.add_argument("--scale", type=int, default=6)
    ap.add_argument("--cols", type=int, default=12)
    a = ap.parse_args()
    if a.list:
        for nm in SETS + ["VICFLAGS.S16"]:
            print("%-14s ofs=%d" % (nm, ENT.get(nm, -1)))
        return 0
    if a.draw:
        RED, WHITE = sample_palette()
        print("调色: RED=0x%04X WHITE=0x%04X" % (RED, WHITE))
        preview(RED, WHITE)
        return 0
    if a.dry_run:
        apply_flags(dry=True)
        return 0
    if a.apply:
        apply_flags(dry=False)
        return 0
    if a.verify:
        return 1 if verify() else 0
    if a.fix_sentinel:
        fix_sentinel()
        return 0
    if a.dupes:
        dupes(a.dupes)
        return 0
    if a.cmp:
        cmp_sets(a.cmp[0], a.cmp[1])
        return 0
    if a.meta:
        meta(a.meta, a.all)
        return 0
    if a.grid:
        nm = a.grid[0]
        if len(a.grid) > 1:
            which = [int(x) for x in ",".join(a.grid[1:]).split(",") if x != ""]
        else:
            which = list(range(len(frames(nm)[0])))
        grid(nm, which, a.step)
        return 0
    if a.render:
        render(a.render, a.scale, a.cols)
        return 0
    if a.render_all:
        for nm in SETS:
            render(nm, a.scale, a.cols)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
