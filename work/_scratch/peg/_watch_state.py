# -*- coding: utf-8 -*-
"""只读状态观察器 v4：高频轮询 + 只记变化（含光标格与范围表取值分布）。

目的：查清“选中单位后范围阴影不立即显示、滚动一次才显示”的机制。全程只读。

监视：SEL=word[0x686FD4]；光标格 CC=(word[0x4AF2E8],word[0x4AF2EC])；
范围表 0x622D4A（行距 0x13B、格距 7、格内 word）在真实地图区 (i<27,j<37) 上的取值分布 top2；
光标格上的表值 TV；f0/f4=dword[0x4AF2F0]/[0x4AF2F4]；d74=word[0x498D74]；d78=byte[0x498D78]；
f324=byte[0x4AF324]；f388=byte[0x4AF388]；两张 1bpp 层 0x4CCE40/0x53D640 的位数（250ms 一次）。
用法：python _watch_state.py --wait 2400 --secs 2400
日志：work\\peg\\out\\watch-state.txt
"""
import ctypes, ctypes.wintypes as w, time, os, argparse

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
u32 = ctypes.WinDLL('user32', use_last_error=True)

TH32CS_SNAPPROCESS = 0x2
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400
INVALID = ctypes.c_void_p(-1).value


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)), ("th32ModuleID", w.DWORD),
                ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", w.DWORD), ("szExeFile", ctypes.c_char * 260)]


k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
k32.OpenProcess.restype = ctypes.c_void_p
k32.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k32.ReadProcessMemory.restype = w.BOOL
k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [ctypes.c_void_p]


def find_pid(name):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID:
        return 0
    e = PROCESSENTRY32(); e.dwSize = ctypes.sizeof(PROCESSENTRY32)
    pid = 0
    ok = k32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.decode('latin1').lower() == name.lower():
            pid = e.th32ProcessID
            break
        ok = k32.Process32Next(snap, ctypes.byref(e))
    k32.CloseHandle(ctypes.c_void_p(snap))
    return pid


def rd(h, va, n):
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(va), buf, n, ctypes.byref(got))
    if not ok or got.value != n:
        return None
    return buf.raw


def u16(b, o=0):
    return int.from_bytes(b[o:o + 2], 'little')


def u32v(b, o=0):
    return int.from_bytes(b[o:o + 4], 'little')


def popcount(buf):
    return sum(bin(x).count('1') for x in buf)


def cursor():
    pt = w.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


TABLE, TSTRIDE, CSTRIDE, ROWS, COLS = 0x622D4A, 0x13B, 7, 37, 27
A0, B0, LEN = 0x4CCE40, 0x53D640, 0x70800


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wait', type=int, default=2400)
    ap.add_argument('--secs', type=int, default=2400)
    ap.add_argument('--exe', default='PeG030.exe')
    a = ap.parse_args()

    outdir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'peg', 'out'))
    os.makedirs(outdir, exist_ok=True)
    log = open(os.path.join(outdir, 'watch-state.txt'), 'a', encoding='utf-8', buffering=1)

    def say(s):
        log.write(s + '\n')

    pid = 0
    t0 = time.time()
    while time.time() - t0 < a.wait and not pid:
        pid = find_pid(a.exe)
        if not pid:
            time.sleep(0.5)
    if not pid:
        say('[%s] no process %s after %ds' % (time.strftime('%H:%M:%S'), a.exe, a.wait))
        return
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        say('[%s] OpenProcess failed pid=%d err=%d' % (time.strftime('%H:%M:%S'), pid, ctypes.get_last_error()))
        return
    say('[%s] attached pid=%d base=0x400000 (v4: CC/TV/top2)' % (time.strftime('%H:%M:%S'), pid))

    prev = None
    prev_mask = None
    last_mask = 0.0
    last_beat = 0.0
    start = time.time()
    nlog = 0
    while time.time() - start < a.secs:
        if not find_pid(a.exe):
            say('[%s] process gone' % time.strftime('%H:%M:%S'))
            break
        cur = cursor()
        b = rd(h, 0x686FD4, 2)
        cc = rd(h, 0x4AF2E8, 4)
        f = rd(h, 0x4AF2F0, 8)
        tb = rd(h, TABLE, TSTRIDE * ROWS + CSTRIDE)
        g = rd(h, 0x498D74, 2)
        g2 = rd(h, 0x498D78, 1)
        g3 = rd(h, 0x4AF324, 1)
        g4 = rd(h, 0x4AF388, 1)
        if not (b and cc and f and tb and g and g2 and g3 and g4):
            time.sleep(0.2)
            continue
        sel = u16(b)
        cci, ccj = u16(cc), u16(cc, 2)
        counts = {}
        for j in range(ROWS):
            base = j * TSTRIDE
            for i in range(COLS):
                o = base + i * CSTRIDE
                if o + 2 <= len(tb):
                    v = u16(tb, o)
                    counts[v] = counts.get(v, 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:2]
        top = top + [(0, 0)] * (2 - len(top))
        to = ccj * TSTRIDE + cci * CSTRIDE
        tv = u16(tb, to) if to + 2 <= len(tb) else -1
        st = (cur[0], cur[1], cci, ccj, sel, tv, top[0][0], top[0][1], top[1][0], top[1][1],
              u32v(f, 0), u32v(f, 4), u16(g), g2[0], g3[0], g4[0])
        now = time.time()
        if st != prev:
            nlog += 1
            if nlog <= 800:
                say('[%s +%.1fs] cur=(%d,%d) CC=(%d,%d) SEL=%d TV=%d top1=%d:%d top2=%d:%d f0=%d f4=%d '
                    'd74=%d d78=%d f324=%d frag=%d'
                    % (time.strftime('%H:%M:%S'), now - start, st[0], st[1], cci, ccj, sel, tv,
                       st[6], st[7], st[8], st[9], st[10], st[11], st[12], st[13], st[14], st[15]))
            prev = st
        if now - last_mask >= 0.25:
            ma, mb = rd(h, A0, LEN), rd(h, B0, LEN)
            if ma and mb:
                m = (popcount(ma), popcount(mb))
                if m != prev_mask:
                    say('[%s +%.1fs] MASK A=%d B=%d (dA=%s dB=%s)'
                        % (time.strftime('%H:%M:%S'), now - start, m[0], m[1],
                           '' if not prev_mask else m[0] - prev_mask[0],
                           '' if not prev_mask else m[1] - prev_mask[1]))
                    prev_mask = m
            last_mask = now
        if now - last_beat >= 20:
            say('[%s +%.1fs] beat SEL=%d CC=(%d,%d) TV=%d top1=%d:%d f4=%d d78=%d d74=%d frag=%d cur=(%d,%d)'
                % (time.strftime('%H:%M:%S'), now - start, sel, cci, ccj, tv, st[6], st[7],
                   st[11], st[13], st[12], st[15], st[0], st[1]))
            last_beat = now
        time.sleep(0.004)
    say('[%s] watch ended after %.0fs' % (time.strftime('%H:%M:%S'), time.time() - start))
    k32.CloseHandle(ctypes.c_void_p(h))


main()
