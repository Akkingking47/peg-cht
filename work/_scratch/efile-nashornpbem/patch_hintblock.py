# -*- coding: utf-8 -*-
"""
OpenGen.exe 地图提示/单位信息串块 汉化补丁器
======================================================================
方式：**原地等长/缩短替换**——只改字符串内容，多余字节填 0。
      不动任何代码、不改字符串起点、不改文件长度。
约束：译文 GBK 字节数 <= 原串字节数；printf 格式符个数必须一致。
"""
import struct, re, sys, os, hashlib

EXE = r"D:/OpenPG2/OpenGen.exe"
FMT = re.compile(r"%[-+ 0-9.#]*[dsfxc]")

# ---------------------------------------------------------------- 译文
# (VA, 译文)
PATCHES = [
    # --- 简介弹窗 / 暂停回放 ---
    (0x911F84, "按 ESC 键关闭此简介并继续"),
    (0x912238, "已暂停 .. 按 P 继续或按 Ctrl+Q 退出游戏"),
    (0x912268, "回放 .. 按 P 暂停或按回车中断"),
    # --- 地图 tooltip ---
    (0x911F00, " 胜利格: "),
    (0x911EC8, " 支援:"),
    (0x911EEC, " 支援:P%d "),
    (0x911F70, "  占领方: "),
    (0x9120E0, "胜利格归: "),
    (0x9120F0, "双方均可"),
    (0x912220, "双方"),
    (0x912208, "支援：所有者"),
    (0x912218, "支援："),
    (0x912198, "支援"),
    (0x912114, "超出地图边界"),
    (0x9120D4, "* 直到T%d"),
    (0x9120A4, " 地图%d x %d"),
    (0x91212C, "EH: 陆、海、空"),
    (0x912144, "EH: 陆、海"),
    (0x912158, "EH: 空"),
    # --- 阵营 ---
    (0x912160, "敌军"), (0x91217C, "敌军"), (0x9121B0, "敌军"),
    (0x9121DC, "敌军"), (0x9121F0, "敌军"), (0x912200, "敌军"),
    (0x912174, "友军"), (0x9121A0, "友军"), (0x9121A8, "友军"),
    (0x9121D4, "友军"), (0x9121F8, "友军"), (0x912228, "友军"),
    (0x9120FC, " (友军)"), (0x912184, " (友军)"),
    (0x912108, " (敌军)"), (0x912190, " (敌军"),
    # --- 战斗预测 / 单位统计 ---
    (0x911FBC, "赔率: %d-%d   "),
    (0x911FD4, "AP:%d 要塞:%d 港口:%d 车站:%d 桥梁:%d pp"),
    (0x912014, " 燃料:%d %s"),
    (0x912028, " 弹药:- "),
    (0x912034, " 弹药:%d/%d "),
    (0x912050, " 移动%d 维护%d"),
    (0x912068, " %s%d/%d 经验%d 工事%d"),
    (0x9120B4, " 弹药:%d "),
    # --- 其他 ---
    (0x91229C, " 无威望奖励或惩罚 "),
    (0x9122BC, "(%d,%d)  点击显示/选择选项: #%d ... %s"),
]


def parse_pe(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, pe + 6)[0]
    szopt = struct.unpack_from("<H", d, pe + 20)[0]
    IB = struct.unpack_from("<I", d, pe + 24 + 28)[0]
    sh = pe + 24 + szopt
    secs = []
    for i in range(nsec):
        o = sh + i * 40
        nm = d[o:o + 8].rstrip(b"\x00").decode()
        vsz, rva, rsz, fo = struct.unpack_from("<IIII", d, o + 8)
        secs.append((nm, rva, vsz, fo, rsz))
    return IB, secs


def main():
    apply_ = "--apply" in sys.argv
    d = open(EXE, "rb").read()
    IB, secs = parse_pe(d)

    def va2fo(va):
        rva = va - IB
        for n, sva, vsz, f0, rsz in secs:
            if sva <= rva < sva + max(vsz, rsz):
                return f0 + (rva - sva)
        return None

    print("译文条数:", len(PATCHES))
    errs = []
    plan = []
    for va, zh in PATCHES:
        fo = va2fo(va)
        if fo is None:
            errs.append("%08X 无法换算" % va); continue
        e = d.index(b"\x00", fo)
        orig = d[fo:e]
        try:
            otxt = orig.decode("ascii")
        except Exception:
            errs.append("%08X 原串非 ASCII" % va); continue
        try:
            zhb = zh.encode("gbk")
        except Exception as ex:
            errs.append("%08X 译文无法 GBK 编码: %s" % (va, ex)); continue
        if re.search(r"[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", zh):
            errs.append("%08X 译文含非中文非常见字符" % va); continue
        fo_cnt = len(FMT.findall(otxt))
        fz_cnt = len(FMT.findall(zh))
        if fo_cnt != fz_cnt:
            errs.append("%08X 格式符个数不符 %d -> %d" % (va, fo_cnt, fz_cnt)); continue
        if len(zhb) > len(orig):
            errs.append("%08X 译文超长 %d > %d (%r)" % (va, len(zhb), len(orig), zh)); continue
        plan.append((va, fo, orig, zhb))

    print("可应用:", len(plan), " 错误:", len(errs))
    for e in errs:
        print("  !!", e)
    if errs:
        print("有错误，终止。"); return

    print("\n%-9s %-4s %-4s  %s" % ("VA", "原长", "译长", "内容"))
    for va, fo, orig, zhb in plan:
        print("%08X %4d %4d  %-46r -> %s" % (va, len(orig), len(zhb),
                                             orig.decode("ascii")[:44], zhb.decode("gbk")))
    total = sum(len(z) for _, _, _, z in plan)
    print("\n译文合计 %d 字节；原串合计 %d 字节（净减 %d）"
          % (total, sum(len(o) for _, _, o, _ in plan), sum(len(o) for _, _, o, _ in plan) - total))

    if not apply_:
        print("\n=== dry-run（未写入）===")
        return

    buf = bytearray(d)
    changed = []
    for va, fo, orig, zhb in plan:
        n = len(orig) + 1                      # 原占用（含终止符）
        new = zhb + b"\x00" * (n - len(zhb))   # 缩短后余下填 0
        assert len(new) == n
        buf[fo:fo + n] = new
        changed.append((fo, fo + n))
    # 差异只应落在预期区间
    diff = [i for i in range(len(d)) if d[i] != buf[i]]
    outside = [i for i in diff if not any(a <= i < b for a, b in changed)]
    print("\n差异字节数:", len(diff), " 区间数:", len(changed), " 区间外差异:", len(outside))
    if outside:
        print("  !! 区间外差异（前 10）:", ["0x%X" % i for i in outside[:10]])
        return
    # 写临时 -> 回读 -> 落盘
    tmp = EXE + ".tmp"
    with open(tmp, "wb") as f:
        f.write(buf)
    back = open(tmp, "rb").read()
    if back != bytes(buf):
        print("  !! 回读不一致"); os.remove(tmp); return
    os.replace(tmp, EXE)
    print("已写入。新 MD5 =", hashlib.md5(open(EXE, "rb").read()).hexdigest().upper())
    print("文件大小 =", os.path.getsize(EXE))


if __name__ == "__main__":
    main()
