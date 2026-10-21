# -*- coding: utf-8 -*-
"""阶段 2 三项校验 + 硬桥复核（EFILE_GUS_Zx）。

用法：python verify_all.py
异常数即退出码。
"""
import os
import sys

sys.path.insert(0, r"D:\DSH\军事游戏汉化\work\xscn")
import xscn  # noqa: E402

GAME = r"D:\OpenGeneral"
EFILE = "GUS_Zx"
anomalies = []

CTX = xscn.Ctx(EFILE, GAME)
SCEN = CTX.game
ZH = os.path.join(CTX.root, CTX.efile, "TEXT-ZH", "SCENARIO")
is_han = lambda s: any("\u4e00" <= c <= "\u9fff" for c in s)


def check_txt():
    """[1] 覆盖层 118 个 .txt + 1 个 .PLY：GBK 无 BOM、行数与原文完全一致、有汉字。"""
    names = sorted(set(
        f for f in os.listdir(SCEN) if f.lower().endswith((".txt", ".ply"))))
    n = 0
    for name in names:
        sp, zp = os.path.join(SCEN, name), os.path.join(ZH, name)
        if not os.path.exists(zp):
            anomalies.append("[txt] 缺覆盖层 %s" % name)
            continue
        sb = open(sp, "rb").read()
        zb = open(zp, "rb").read()
        if zb[:3] == b"\xef\xbb\xbf":
            anomalies.append("[txt] %s 带 BOM" % name)
            continue
        try:
            zt = zb.decode("gbk")
        except UnicodeDecodeError as e:
            anomalies.append("[txt] %s GBK 解码失败 %s" % (name, e))
            continue
        if not zb.strip():
            pass                                  # 0 字节源允许 0 字节译
        elif not is_han(zt):
            anomalies.append("[txt] %s 无汉字" % name)
            continue
        # 逐行对齐：换行数 + 每行「空/非空」形态必须一致
        sn, zn = sb.count(b"\n"), zb.count(b"\n")
        if sn != zn:
            anomalies.append("[txt] %s 换行数 源%d/译%d" % (name, sn, zn))
            continue
        if sb and zb:
            sf = [bool(x.strip()) for x in sb.split(b"\n")]
            zf = [bool(x.strip()) for x in zb.split(b"\n")]
            if sf != zf:
                diff = [i for i in range(min(len(sf), len(zf))) if sf[i] != zf[i]]
                anomalies.append("[txt] %s 段落形态不一致 行%s" % (name, diff[:5]))
                continue
        n += 1
    print("[1] 覆盖层 GBK/无BOM/行对齐：通过 %d / %d" % (n, len(names)))


def _slots(f):
    """返回 [(gi, k, 现串, 原件)]；原件来自备份目录，用于判定该槽是否被改写。

    ⚠️ 为什么必须拿备份对拍：未改写的槽里可能残留 cp1250 高位字节（如 `ń`=0xF1），
    用 GBK 解码会造出**假汉字**（`SBS Podhalańskich` -> `SBS Podhala駍kich`），
    据此判中文会误报。以「与备份字节不同」为准才是硬判据。
    """
    data, items, _ = xscn.parse(os.path.join(SCEN, f))
    bdata, bitems, _ = xscn.parse(os.path.join(CTX.bak, f))
    bmap = {(g, k): xscn.raw_at(bdata, o, L) for g, k, o, L in bitems}
    out = []
    for gi, k, off, L in items:
        raw = xscn.raw_at(data, off, L)
        out.append((gi, k, raw, bmap.get((gi, k))))
    return out


def check_xscn():
    """[2] 独立解析器 verify：条目数与备份一致、尾部残留 0、改写槽的字节确为 GBK 汉字。"""
    xscn.set_enc_in("cp1250")
    files = CTX.files()
    total = changed = badenc = resid = 0
    for f in files:
        data, items, meta = xscn.parse(os.path.join(SCEN, f))
        if items is None:
            anomalies.append("[xscn] %s 解析失败" % f)
            continue
        if meta[3] != meta[4]:
            resid += 1
            anomalies.append("[xscn] %s 尾部残留 %d B" % (f, meta[4] - meta[3]))
        total += len(items)
        for gi, k, raw, old in _slots(f):
            if old is not None and raw == old:
                continue
            changed += 1
            try:
                s = raw.decode("gbk")
            except UnicodeDecodeError:
                badenc += 1
                anomalies.append("[xscn] %s 组%d 第%d槽 非合法 GBK" % (f, gi, k))
                continue
            if not is_han(s) and raw.strip():
                anomalies.append("[xscn] %s 组%d 第%d槽 改写后无汉字: %r" % (f, gi, k, s))
    print("[2] 独立解析器：文件 %d / 条目 %d / 改写槽 %d / 非GBK %d / 尾部残留文件 %d"
          % (len(files), total, changed, badenc, resid))


def check_bridge():
    """[3] 硬桥：被改写过的 .xscn 地名/番号串必须逐条出现在同名 <name>.txt 覆盖层里。"""
    xscn.set_enc_in("cp1250")
    pairs = miss = checked = nosrc = 0
    for f in CTX.files():
        base = os.path.splitext(f)[0]
        zp = os.path.join(ZH, base + ".txt")
        if not os.path.exists(zp):
            nosrc += 1                       # 原包就没有该场景的标签表（G06 全族）
            continue
        pairs += 1
        lines = set(x.strip() for x in open(zp, encoding="gbk").read().split("\n")
                    if x.strip())
        for gi, k, raw, old in _slots(f):
            if gi == -1 or (old is not None and raw == old):
                continue
            t = raw.decode("gbk", "replace").strip()
            if not t:                        # 原件非中文（纯编号/代号）被保留
                continue
            checked += 1
            if t not in lines:
                miss += 1
                if miss <= 10:
                    anomalies.append("[bridge] %s 组%d 未在标签表: %r" % (base, gi, t))
    print("[3] .xscn↔.txt 硬桥：配对 %d / 校验中文串 %d / 未命中 %d / 无标签表 %d"
          % (pairs, checked, miss, nosrc))


if __name__ == "__main__":
    check_txt()
    check_xscn()
    check_bridge()
    print("\n=== 异常 %d ===" % len(anomalies))
    for a in anomalies[:40]:
        print("  " + a)
    sys.exit(len(anomalies))
