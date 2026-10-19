# -*- coding: utf-8 -*-
"""
build_v10.py — v10 构建器：把「屏幕画布」从 800x600 修到目标分辨率，并（可选）重排 UI

背景（本轮重大发现）：引擎里有一批**写死的 800x600**，它们不在 v4 站点表里
（站点表只覆盖了尺寸常量与 10 处代码侧 imm32），所以 16:9 产物里它们仍是旧值：

  A. 屏幕描述符（每次 SetDisplayMode 后由 0x44219F 初始化，被 0x4235E5 的
     Blt 漏斗当作裁剪框）：
       0x4421D4  mov dword [0x676988], 0x31F   ; right  = 799
       0x4421DE  mov dword [0x67698C], 0x257   ; bottom = 599
       0x442219  mov dword [0x676968], 0x31F   ; right  = 799
       0x442223  mov dword [0x67696C], 0x257   ; bottom = 599
     ⇒ dst.right = min(sprite_w, 799 - dx)：dx 超过 800 之后裁剪框变成负数，
       这正是 v4/v7/v8a/v9a 反复出现「拉伸带/彩带/黑区/底栏不出现」的共同根因。

  B. 坐标夹取（光标/选择位置被夹到旧屏幕内）：
       0x43B22C  mov dword [0x61E928], 0x31F   ; x 上限 799
       0x43B242  mov dword [0x61E92C], 0x257   ; y 上限 599
       0x43BD8F  mov dword [0x61E928], 0x31F   ; 同一夹取的第二份代码
       0x43BDA5  mov dword [0x61E92C], 0x257
     （注意：16:9 产物已经把这些夹取的 _比较_ 值改成了 1920/1080，
       却没改夹取 _写入_ 值 ⇒ 夹取逻辑自相矛盾，鼠标移出 800x600 后越界采样。）

  C. 整屏重绘分发器（脏标志驱动，标志极少被置位，新暴露区域从不重画）：
       0x4489D8  je 0x4489F5  ->  90 90    ; 每帧都走 0x44AC45（顶栏+底栏+控件循环）

  D.（仅 --ui）UI 记录表重排：工具列贴右缘、动作条居中、底栏贴底
       + 0x45696D  mov word [0x4A42EC], 0x31F -> 新右缘（右侧面板的显示位置）

用法：
    python build_v10.py --w 1920 --h 1080                 # 干跑，打印全部站点
    python build_v10.py --w 1920 --h 1080 --apply        # 落盘 v10a 与 v10b
"""
import argparse
import hashlib
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE = os.path.join(HERE, "out", "PeG030-1920x1080.exe")
BASE_MD5 = "44ac5cfe5a5875aa5ef51efd3d1afcf4"
TSV = os.path.join(HERE, "out", "ui_layout_v9.tsv")
IMAGE_BASE = 0x400000

# (指令 VA, 宽度, 目标地址, 旧值, 标签, 说明)
CANVAS_SITES = [
    (0x4421D4, "dword", 0x676988, 799, "w-1", "屏幕描述符.right"),
    (0x4421DE, "dword", 0x67698C, 599, "h-1", "屏幕描述符.bottom"),
    (0x442219, "dword", 0x676968, 799, "w-1", "第二屏幕描述符.right"),
    (0x442223, "dword", 0x67696C, 599, "h-1", "第二屏幕描述符.bottom"),
    (0x43B22C, "dword", 0x61E928, 799, "w-1", "坐标夹取 x 上限"),
    (0x43B242, "dword", 0x61E92C, 599, "h-1", "坐标夹取 y 上限"),
    (0x43BD8F, "dword", 0x61E928, 799, "w-1", "坐标夹取 x 上限（第二份）"),
    (0x43BDA5, "dword", 0x61E92C, 599, "h-1", "坐标夹取 y 上限（第二份）"),
]
REPAINT_SITE = (0x4489D8, b"\x74\x1b", b"\x90\x90", "每帧强制整屏重绘")
PANEL_SITE = (0x45696D, "word", 0x4A42EC, 799, "w-1", "右侧面板显示位置")
DESC_VAS = {0x4421D4, 0x4421DE, 0x442219, 0x442223}


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sections(data):
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    sec0 = e_lfanew + 24 + opt_size
    secs = []
    for i in range(nsec):
        off = sec0 + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        secs.append(dict(name=name, va=va, vsize=vsize, raw=raw, rawsize=rawsize))
    return secs


def va_to_off(data, secs, va):
    rva = va - IMAGE_BASE
    for s in secs:
        if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
            return s["raw"] + (rva - s["va"])
    raise SystemExit("VA 0x%08X 不在任何节内" % va)


def write_imm(data, secs, va, kind, expect_target, old, new):
    off = va_to_off(data, secs, va)
    if kind == "word":
        if data[off] != 0x66:
            raise SystemExit("VA 0x%08X 期望 16 位前缀 66，实为 %02X" % (va, data[off]))
        off += 1
    elif data[off] == 0x66:
        raise SystemExit("VA 0x%08X 是 16 位前缀，请用 kind=word" % va)
    if data[off:off + 2] != b"\xc7\x05":
        raise SystemExit("VA 0x%08X 不是 mov [imm], imm（前两字节 %s）"
                         % (va, data[off:off + 2].hex(" ")))
    tgt = struct.unpack_from("<I", data, off + 2)[0]
    if tgt != expect_target:
        raise SystemExit("VA 0x%08X 目标地址 0x%08X != 期望 0x%08X" % (va, tgt, expect_target))
    if kind == "dword":
        cur = struct.unpack_from("<I", data, off + 6)[0]
        fmt, size = "<I", 4
    else:
        cur = struct.unpack_from("<H", data, off + 6)[0]
        fmt, size = "<H", 2
    if cur == new:
        return "skip"
    if cur != old:
        raise SystemExit("VA 0x%08X 现值 %d 既非母本值 %d 也非目标值 %d" % (va, cur, old, new))
    struct.pack_into(fmt, data, off + 6, new)
    if struct.unpack_from(fmt, data, off + 6)[0] != new:
        raise SystemExit("VA 0x%08X 回读失败" % va)
    return "written"


def write_bytes(data, secs, va, old, new, tag):
    off = va_to_off(data, secs, va)
    cur = bytes(data[off:off + len(old)])
    if cur == new:
        return "skip"
    if cur != old:
        raise SystemExit("VA 0x%08X 当前 %s 既非母本 %s 也非目标 %s"
                         % (va, cur.hex(" "), old.hex(" "), new.hex(" ")))
    data[off:off + len(new)] = new
    if bytes(data[off:off + len(new)]) != new:
        raise SystemExit("VA 0x%08X 回读失败" % va)
    return "written"


def load_ui_sites():
    rows = []
    with open(TSV, "r", encoding="utf-8") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            rows.append(dict(idx=p[0], field=p[1], va=int(p[2], 16),
                             delta=p[3], new=int(p[4]), tag=p[5] if len(p) > 5 else ""))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--skip-desc", action="store_true",
                    help="跳过 A 组（屏幕描述符 4 处），只保留 B（强制重绘）与 D（UI 重排）")
    args = ap.parse_args()
    W, H = args.w, args.h

    if md5_of(args.base) != BASE_MD5:
        raise SystemExit("基准不是 16:9 构建产物（md5 期望 %s）" % BASE_MD5)
    base = open(args.base, "rb").read()
    print("基准 %s  目标 %dx%d\n" % (os.path.basename(args.base), W, H))

    # ---- 第一遍：画布修复 ----
    d1 = bytearray(base)
    secs = parse_sections(d1)
    print("== A/B 画布站点（%d 处 + 1 处重绘）" % len(CANVAS_SITES))
    for va, kind, tgt, old, tag, note in CANVAS_SITES:
        if args.skip_desc and va in DESC_VAS:
            print("   0x%08X  [0x%08X]  %d    %s   （--skip-desc：跳过）" % (va, tgt, old, note))
            continue
        new = W - 1 if tag == "w-1" else H - 1
        st = write_imm(d1, secs, va, kind, tgt, old, new)
        print("   0x%08X  [0x%08X]  %d -> %d   %s%s"
              % (va, tgt, old, new, note, "   （已是目标值，跳过）" if st == "skip" else ""))
    st = write_bytes(d1, secs, *REPAINT_SITE[:4])
    print("   0x%08X  %s   %s%s" % (REPAINT_SITE[0], REPAINT_SITE[1].hex(" "),
                                    REPAINT_SITE[3],
                                    "   （已是目标值，跳过）" if st == "skip" else ""))

    # ---- 第二遍：UI 重排 ----
    d2 = bytearray(d1)
    secs2 = parse_sections(d2)
    print("\n== D UI 重排（记录表 %s + 面板位置 1 处）" % os.path.basename(TSV))
    rows = load_ui_sites()
    for r in rows:
        off = va_to_off(d2, secs2, r["va"])
        cur = struct.unpack_from("<H", d2, off)[0]
        if cur != r["new"]:
            struct.pack_into("<H", d2, off, r["new"])
            if struct.unpack_from("<H", d2, off)[0] != r["new"]:
                raise SystemExit("0x%08X 回读失败" % r["va"])
        print("   idx%-2s %-6s 0x%08X  %d -> %d  (%s)%s"
              % (r["idx"], r["field"], r["va"], cur, r["new"], r["tag"],
                 "   （已是目标值，跳过）" if cur == r["new"] else ""))
    va, kind, tgt, old, tag, note = PANEL_SITE
    new = W - 1
    st = write_imm(d2, secs2, va, kind, tgt, old, new)
    print("   0x%08X  [0x%08X] %d -> %d  %s%s"
          % (va, tgt, old, new, note, "   （已是目标值，跳过）" if st == "skip" else ""))

    if not args.apply:
        print("\n[干跑] 加 --apply 落盘 v10a / v10b"
              + ("（--skip-desc 时为 v10c / v10d）" if args.skip_desc else ""))
        return

    suffix = "c" if args.skip_desc else "a"
    out_a = os.path.join(HERE, "out", "PeG030-%dx%d-v10%s.exe" % (W, H, suffix))
    out_b = os.path.join(HERE, "out", "PeG030-%dx%d-v10%s.exe"
                         % (W, H, "d" if args.skip_desc else "b"))
    for path, payload in ((out_a, d1), (out_b, d2)):
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(payload)
        with open(tmp, "rb") as f:
            if f.read() != bytes(payload):
                raise SystemExit("临时文件回读不一致：%s" % path)
        os.replace(tmp, path)
        diff = [i for i in range(len(base)) if base[i] != payload[i]]
        runs = 1 + sum(1 for k in range(1, len(diff)) if diff[k] != diff[k - 1] + 1)
        print("\n[已写入] %s\n   md5 %s\n   与基准差异 %d 字节 / %d 段"
              % (path, md5_of(path), len(diff), runs))


if __name__ == "__main__":
    main()
