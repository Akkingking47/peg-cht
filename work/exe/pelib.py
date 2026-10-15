# -*- coding: utf-8 -*-
"""exe 补丁公共库：PE 段/数据目录解析 + 空洞安全性检查。

⚠️ 血泪教训（2026-09-24）：
   当时把「连续 NUL 区」当空洞，选了 FO 0x51CB31（VA 0x91D931）。
   实际它是 **IMAGE_LOAD_CONFIG_DIRECTORY**（数据目录 #10，FO 0x51CB30..0x51CB70）。
   写入偏移 +16 命中 `GlobalFlagsSet` 字段 ⇒ GBK 字节变成 0xD6D0D5BF
   ⇒ 加载器把它 |= 进 ntdll!NtGlobalFlag，打开 loader snaps 等一整批调试标志
   ⇒ 进程初始化阶段在 ntdll 内 0xC0000005（游戏窗都出不来）。
   **判据「全 NUL + 0 引用」远远不够：零值字段也是字段。**

空穴判定三条（缺一不可）：
  ① 区内全 0x00
  ② **不与任何 PE 数据目录相交**（LoadConfig/Debug/Import/IAT/TLS/Exception…）
  ③ 区内每个 4 字节对齐位置都不被全 exe 引用
"""
import struct

DIRNAMES = ["Export", "Import", "Resource", "Exception", "Security", "BaseReloc",
            "Debug", "Arch", "GlobalPtr", "TLS", "LoadConfig", "BoundImport",
            "IAT", "DelayImport", "CLR", "Reserved"]


class PE(object):
    def __init__(self, d):
        self.d = d
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[pe:pe + 4] == b"PE\0\0", "不是 PE 文件"
        self.pe = pe
        nsec, = struct.unpack_from("<H", d, pe + 6)
        opt = pe + 24
        sec_off = opt + struct.unpack_from("<H", d, pe + 20)[0]
        self.sections = []
        for i in range(nsec):
            o = sec_off + 40 * i
            name = d[o:o + 8].rstrip(b"\0").decode("latin-1")
            vsize, va = struct.unpack_from("<II", d, o + 8)
            rsize, rptr = struct.unpack_from("<II", d, o + 16)
            self.sections.append((name, va, vsize, rptr, rsize))
        self.ndir, = struct.unpack_from("<I", d, opt + 92)
        self.dirs = []
        for i in range(self.ndir):
            rva, size = struct.unpack_from("<II", d, opt + 96 + 8 * i)
            if not rva or not size:
                continue
            fo = self.rva2fo(rva)[0]
            if fo is None:
                continue
            self.dirs.append((DIRNAMES[i], rva, size, fo, fo + size))

    def rva2fo(self, rva):
        for n, va, vs, rp, rs in self.sections:
            if va <= rva < va + max(vs, rs):
                return rp + (rva - va), n
        return None, "?"

    def fo2sec(self, fo):
        for n, va, vs, rp, rs in self.sections:
            if rp <= fo < rp + rs:
                return n, va + (fo - rp)
        return "?", None

    def fo2va(self, fo):
        n, rva = self.fo2sec(fo)
        return 0x400000 + rva if rva is not None else None

    def check_hole(self, fo, ln):
        """返回问题清单（空列表 = 通过）。"""
        d = self.d
        probs = []
        seg = d[fo:fo + ln]
        if len(seg) != ln:
            return ["区间超出文件尾"]
        if seg.count(0) != ln:
            off = [i for i, b in enumerate(seg) if b][0]
            probs.append("区内非 0 @+%d (0x%02X)" % (off, seg[off]))
        for name, rva, size, dfo, deo in self.dirs:
            # 目录条目可能紧邻，前后各留 32 字节余量
            if fo < deo + 32 and fo + ln > dfo - 32:
                probs.append("与 PE 数据目录 [%s] FO 0x%X..0x%X 相交（禁止！）"
                             % (name, dfo, deo))
        va = self.fo2va(fo)
        if va:
            for off in range(0, ln - 3, 4):
                c = d.count(struct.pack("<I", va + off))
                if c:
                    probs.append("VA 0x%X 被引用 %d 处" % (va + off, c))
        return probs


def describe(d):
    p = PE(d)
    out = []
    for n, va, vs, rp, rs in p.sections:
        out.append("  %-8s VA 0x%08X virt 0x%X  raw FO 0x%X 0x%X"
                   % (n, 0x400000 + va, vs, rp, rs))
    out.append("  数据目录：")
    for name, rva, size, dfo, deo in p.dirs:
        out.append("    %-12s VA 0x%08X..0x%08X  FO 0x%X..0x%X"
                   % (name, 0x400000 + rva, 0x400000 + rva + size, dfo, deo))
    return "\n".join(out)
