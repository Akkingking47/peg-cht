# -*- coding: utf-8 -*-
"""按 _cleanup-list.json 把冗余文件送入【回收站】（可还原）。
分批执行，每批复验；保留同内容副本仍存在。默认 DRY-RUN，--apply 才执行。"""
import ctypes, json, os, sys, collections
from ctypes import wintypes

ROOT = r"D:\DSH\军事游戏汉化"
os.chdir(ROOT)
APPLY = "--apply" in sys.argv

FO_DELETE = 3
FOF_SILENT = 0x0004
FOF_NOCONFIRMATION = 0x0010
FOF_ALLOWUNDO = 0x0040          # ★ 送回收站
FOF_NOERRORUI = 0x0400


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_uint16),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]


def recycle(paths):
    """paths: 绝对路径列表。返回 (retcode, aborted)。"""
    op = SHFILEOPSTRUCTW()
    op.hwnd = None
    op.wFunc = FO_DELETE
    op.pFrom = "\0".join(paths) + "\0\0"
    op.pTo = None
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
    op.fAnyOperationsAborted = False
    op.hNameMappings = None
    op.lpszProgressTitle = None
    ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return ret, bool(op.fAnyOperationsAborted)


def main():
    lst = json.load(open(r"peg\testbed\_cleanup-list.json", encoding="utf-8"))
    man = {}
    for ln in open(r"peg\testbed\cleanup-manifest-2026-10-10.tsv", encoding="utf-8"):
        if ln.startswith("#") or ln.startswith("待移除"):
            continue
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 2:
            man[p[0]] = p[1]

    abs_paths = [os.path.join(ROOT, p) for p in lst]
    exist = [p for p in abs_paths if os.path.exists(p)]
    missing = [p for p in abs_paths if not os.path.exists(p)]
    print(f"清单 {len(lst)} 条；实际存在 {len(exist)}；已不存在 {len(missing)}")
    tot = sum(os.path.getsize(p) for p in exist)
    print(f"待回收合计 {tot/1e6:.1f} MB")

    if not APPLY:
        print("\n（DRY-RUN；加 --apply 才送回收站）")
        return

    CHUNK = 150
    done = 0
    failed = []
    for i in range(0, len(exist), CHUNK):
        batch = exist[i:i + CHUNK]
        ret, aborted = recycle(batch)
        n = i // CHUNK + 1
        still = [p for p in batch if os.path.exists(p)]
        status = "✓" if (ret == 0 and not aborted and not still) else "⚠️"
        print(f"  批 {n:2d}: {len(batch):4d} 个  ret={ret} aborted={aborted} 残留={len(still)}  {status}")
        if ret != 0 or aborted or still:
            failed.append((n, ret, aborted, len(still)))
        done += len(batch) - len(still)

    print(f"\n已送回收站 {done} 个文件")

    # 清理因之而空的目录（仅限 recover/ 与已清空的 poc 子目录）
    removed_dirs = 0
    for root in ("recover", "poc", "pgforever/poc"):
        for r, dirs, fs in os.walk(os.path.join(ROOT, root), topdown=False):
            if not os.listdir(r):
                try:
                    os.rmdir(r); removed_dirs += 1
                except OSError:
                    pass
    print(f"已删除空目录 {removed_dirs} 个")

    # 复验：保留副本仍在
    keep_bad = []
    checked = 0
    for rem, kept in man.items():
        if kept.startswith(("事故中间构建", "官方手册", "已清空", "recover/")):
            continue
        if not kept:
            continue
        checked += 1
        if not os.path.exists(os.path.join(ROOT, kept)):
            keep_bad.append((rem, kept))
    print(f"复验保留副本：检查 {checked} 条，缺失 {len(keep_bad)} 条")
    if keep_bad:
        for a, b in keep_bad[:10]:
            print(f"    ⚠️ {b} 不存在（原移除 {a}）")
    if failed:
        print(f"\n⚠️ 有 {len(failed)} 个批次异常：{failed}")
    else:
        print("\n✓ 全部批次成功")


if __name__ == "__main__":
    main()
