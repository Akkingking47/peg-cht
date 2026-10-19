# -*- coding: utf-8 -*-
"""
patch_fullrepaint.py — 强制全屏重绘（v10a 的第二个站点改动）

背景：PeG 的界面是「脏标志驱动」的增量刷新。`0x4489CC` 是每帧的界面更新分发器：

    0x4489cf  movsx eax, word[0x498d74]
    0x4489d6  test  eax, eax
    0x4489d8  je    0x4489f5          ; 标志=0 → 只做控件增量刷新 0x423CD6
    0x4489da  movsx ecx, byte[0x4af360]
    0x4489e1  test  ecx, ecx
    0x4489e3  jne   0x4489f5
    0x4489e5  call  0x44ac45          ; 整屏刷新：顶栏 0x44C50A + 底栏 0x44C57B + 控件循环 0x423CD6
    0x4489ea  mov   word[0x498d74], 0 ; 清「需要整屏刷新」标志
    0x4489f5  call  0x423cd6

`word[0x498d74]` 是「需要整屏刷新」的一次性标志（置 1 于 0x425CA8，清 0 于若干处）。
把它置位的时机很少，所以改分辨率后新暴露出来的底栏/新区域从来不画。

本补丁：把 `0x4489d8` 的两字节条件跳转 `74 1b` 改成 `90 90`（永不跳过），
使 0x44AC45 每次分发都被调用 ⇒ 顶栏/底栏/控件每帧重画。

用法：
    python patch_fullrepaint.py [--out out\\x.exe] [--apply]
"""
import argparse
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE = os.path.join(HERE, "out", "PeG030-1920x1080.exe")
BASE_MD5 = "44ac5cfe5a5875aa5ef51efd3d1afcf4"      # 16:9 构建产物
VA = 0x4489D8                                       # 条件跳转 je 0x4489f5
OLD = b"\x74\x1b"
NEW = b"\x90\x90"                                   # 两个 NOP
IMAGE_BASE = 0x400000


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
    raise SystemExit("VA 0x%08x 不在任何节内" % va)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--out", default=os.path.join(HERE, "out", "PeG030-1920x1080-fr.exe"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.base):
        raise SystemExit("缺基准文件：%s" % args.base)
    got = md5_of(args.base)
    print("基准 : %s" % args.base)
    print("md5  : %s" % got)
    if got != BASE_MD5:
        raise SystemExit("基准 md5 不是 %s（期望 16:9 构建产物），拒绝继续" % BASE_MD5)

    with open(args.base, "rb") as f:
        data = bytearray(f.read())
    secs = parse_sections(data)
    off = va_to_off(data, secs, VA)
    cur = bytes(data[off:off + len(OLD)])
    print("站点 : VA 0x%08X  file_off 0x%X  当前 %s" % (VA, off, cur.hex(" ")))
    if cur != OLD:
        raise SystemExit("站点内容与母本不符（期望 %s），拒绝继续" % OLD.hex(" "))

    if not args.apply:
        print("\n[干跑] 将把 %s 改为 %s（强制每次分发都走整屏刷新 0x44AC45）" % (OLD.hex(" "), NEW.hex(" ")))
        print("加 --apply 落盘。")
        return

    data[off:off + len(NEW)] = NEW
    # 改后回读校验
    back = bytes(data[off:off + len(NEW)])
    if back != NEW:
        raise SystemExit("回读校验失败")
    tmp = args.out + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    with open(tmp, "rb") as f:
        chk = f.read()
    if chk != bytes(data):
        raise SystemExit("临时文件回读不一致")
    os.replace(tmp, args.out)
    print("\n[已写入] %s" % args.out)
    print("md5  : %s" % md5_of(args.out))
    base_data = open(args.base, "rb").read()
    diff = [i for i in range(len(base_data)) if base_data[i] != data[i]]
    print("与基准差异字节数：%d（位置：%s）" % (len(diff), ["0x%X" % i for i in diff]))


if __name__ == "__main__":
    main()
