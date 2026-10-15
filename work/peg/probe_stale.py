# -*- coding: utf-8 -*-
"""扫描产物 .data/.rdata 里「仍是旧分辨率」的 16 位值，并按控件记录（步长 36）解码上下文。

用途：v4 的补丁是「把母本里等于 800/799/796/600/599/572/571/570 的地方改成新值」。
      凡产物里还留着这些旧值的地方，就是 v4 漏掉的布局常量——右侧花屏/按钮拉伸的嫌疑点。

记录布局：+0 u16 flags  +2 i16 x  +4 i16 y  +6 i16 right  +8 i16 bottom（由命中测试 0x43ff28 实证）

用法：
    python probe_stale.py [--all]
"""
import struct
import sys

ORIG = r"D:\Program Files\PeG-1\PeG030.exe"
PROD = r"D:\Program Files\PeG-1\PeG030res.exe"
STALE = {800: "w", 799: "w-1", 796: "w-4", 600: "h", 599: "h-1", 572: "h-28",
         571: "h-28", 570: "h-30", 762: "btn-x", 787: "btn-right", 756: "vbtn-x",
         781: "vbtn-right", 745: "panel", 760: "panel2", 768: "h_of_1024"}
SECTIONS = [(".rdata", 0x48C000, 0x8A600, 4608), (".data", 0x48E000, 0x8B800, 136192)]


def load(p):
    with open(p, "rb") as f:
        return f.read()


def main():
    show_all = "--all" in sys.argv
    a, b = load(ORIG), load(PROD)
    total = 0
    for name, va0, raw, size in SECTIONS:
        print("==== %s ====" % name)
        for off in range(0, size - 2):
            v = struct.unpack_from("<H", b, raw + off)[0]
            if v not in STALE:
                continue
            ov = struct.unpack_from("<H", a, raw + off)[0]
            if ov != v:
                continue  # 说明这里被改过，不是漏点
            va = va0 + off
            total += 1
            # 视为 x(+2) 或 right(+6) 时的记录解码
            outs = []
            for delta, pos in ((2, "x"), (6, "right")):
                base = va - delta
                if base < va0:
                    continue
                boff = base - va0 + raw
                dec = struct.unpack_from("<5h", b, boff)
                outs.append("rec@0x%06x(%s)=flags%d x%d y%d r%d b%d" % (
                    base, pos, dec[0], dec[1], dec[2], dec[3], dec[4]))
            print("  VA 0x%06x 值 %d(%s) | %s" % (va, v, STALE[v], "  ".join(outs)))
    print("合计未改动的旧分辨率 16 位值：%d 处" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
