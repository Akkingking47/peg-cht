# -*- coding: utf-8 -*-
"""
PeG 高分辨率 · v8：修复「画出来的刀具列被横向拉伸」

## 前情
- 母本 `D:\\Program Files\\PeG\\PeG030.exe`（md5 c462e897b3aa1c384870c857ce9e01df）固定 800x600。
- v4/v5c/v7 这一系列的补丁都把「工具列 13 条记录」的 x/right 加 224（对应 1024 宽），
  但实机（v7a 截图）显示：把这批记录 x/right +224 之后，画出来的不是「平移到 986..1011」，
  而是从 800 起被横向拉伸成 186 px 的彩条。

## 根因（v8 的假设，静态证据）
绘制 handler `0x44ACDA(index)` 从 `[0x4cce2c] + index*0x24` 取记录，构 rect
{x=rec+2, y=rec+4-1, right=rec+6+1, bottom=rec+8+1, surface=[0x676904]}，然后调用
5 参数助手 `0x4235E5(rect*, ctrl, mode, dx, dy)`，其中 **dx 不是记录坐标本身**，而是
    dx = 0x2EF(751) - rec.x      (`0x44AD7E mov edx,0x2ef; 0x44AD83 sub edx,[ebp-0x18]`)
    dy = 0x16 (22) - (rec.y - 1)  (`0x44AD75 mov ecx,0x16; 0x44AD7A sub ecx,[ebp-0x14]`)
即 751/22 是**与记录坐标配对使用的锚点常数**。母本里 rec.x = 762，dx = 751-762 = -11（很小的
相对偏移）；把 rec.x 改成 986 而锚点仍 751 时，dx 变成 -235 —— 助手拿到一个量级完全不同的
相对偏移，于是出现「拉伸/越界取样」的彩条。

## 本脚本
在 v7a（= v5c + 仅 0x4A22F8 那 13 条记录 x/right +224，md5 f7b611c935fc9f34365e157cb2ec6b37）
基础上，把锚点 751 同样 +224 -> 975（0x3CF），使 dx 恢复母本关系（975-986 = -11）。

两个变体：
- **v8a（保守）**：只改 2 处 `mov edx, 0x2ef`（0x44AD7E / 0x44ADA5，绑定记录的计算式）。
- **v8b（激进）**：v8a + 另外 3 处 `push 0x2ef`（0x43AA47 / 0x448849 / 0x448940）。

用法：
  python patch_v8_anchor.py            # 干跑：只报告定位结果与断言，不写文件
  python patch_v8_anchor.py --apply    # 写出 out\\v8a.exe / out\\v8b.exe
"""
import hashlib
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BASE = os.path.join(OUT, "v7a.exe")
BASE_MD5 = "f7b611c935fc9f34365e157cb2ec6b37"

OLD = 0x2EF    # 751
NEW = 0x3CF    # 975 = 751 + 224

MOV_PAT = b"\xba" + OLD.to_bytes(4, "little")   # mov edx, 0x2ef
PUSH_PAT = b"\x68" + OLD.to_bytes(4, "little")  # push 0x2ef
NEW_MOV = b"\xba" + NEW.to_bytes(4, "little")
NEW_PUSH = b"\x68" + NEW.to_bytes(4, "little")

TEXT_VA, TEXT_RAW = 0x401000, 0x400


def fo_to_va(fo):
    return fo - TEXT_RAW + TEXT_VA


def md5(b):
    return hashlib.md5(b).hexdigest()


def find_all(data, pat):
    out, i = [], data.find(pat)
    while i >= 0:
        out.append(i)
        i = data.find(pat, i + 1)
    return out


def build(data, sites):
    b = bytearray(data)
    for pat, new, fo in sites:
        assert bytes(b[fo:fo + len(pat)]) == pat, "站点 %#x 内容断言失败" % fo
        b[fo:fo + len(pat)] = new
    # 回读校验
    for pat, new, fo in sites:
        assert bytes(b[fo:fo + len(new)]) == new, "站点 %#x 回读校验失败" % fo
    return bytes(b)


def main():
    apply_ = "--apply" in sys.argv
    data = open(BASE, "rb").read()
    got = md5(data)
    print("基点 : %s" % BASE)
    print("大小 : %d 字节   md5 %s" % (len(data), got))
    if got != BASE_MD5:
        print("拒绝：基点 md5 期望 %s，实际 %s" % (BASE_MD5, got))
        return 1

    mov_sites = find_all(data, MOV_PAT)
    push_sites = find_all(data, PUSH_PAT)
    print("\n定位 mov edx,0x2ef  : %d 处 %s" % (len(mov_sites), ["%#x" % fo_to_va(f) for f in mov_sites]))
    print("定位 push 0x2ef      : %d 处 %s" % (len(push_sites), ["%#x" % fo_to_va(f) for f in push_sites]))
    if len(mov_sites) != 2 or len(push_sites) != 3:
        print("拒绝：站点数量与预期不符（期望 2 / 3）")
        return 1

    a_sites = [(MOV_PAT, NEW_MOV, fo) for fo in mov_sites]
    b_sites = a_sites + [(PUSH_PAT, NEW_PUSH, fo) for fo in push_sites]

    va = build(data, a_sites)
    vb = build(data, b_sites)
    for name, out, blob in (("v8a", os.path.join(OUT, "v8a.exe"), va),
                            ("v8b", os.path.join(OUT, "v8b.exe"), vb)):
        diff = sum(1 for x, y in zip(data, blob) if x != y)
        print("\n%s：751 -> 975 站点 %d 处，差异 %d 字节，md5 %s"
              % (name, len(a_sites) if name == "v8a" else len(b_sites), diff, md5(blob)))
        if apply_:
            tmp = out + ".tmp"
            with open(tmp, "wb") as f:
                f.write(blob)
            assert md5(open(tmp, "rb").read()) == md5(blob), "回读 md5 不符"
            os.replace(tmp, out)
            print("   已写出 %s" % out)
    if not apply_:
        print("\n[dry-run] 未写入。加 --apply 执行。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
