# -*- coding: utf-8 -*-
r"""OpenGen (SDL2) screenshot / input driver.

Pure ASCII source.

  python ogsnap.py info
  python ogsnap.py shot  <out.png>
  python ogsnap.py click <x> <y> [pause]
  python ogsnap.py key   <vk> [count]
  python ogsnap.py seq   <prefix> [interval] [count]

Clicks are delivered with PostMessage to the client area -- no foreground
focus required.  Screenshots use PrintWindow(hwnd, memdc, 2) so that other
windows covering the game do not matter.
"""
import ctypes
import struct
import subprocess
import sys
import time
import zlib
from ctypes import wintypes

user = ctypes.windll.user32
gdi = ctypes.windll.gdi32

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass
user.SetProcessDPIAware()

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102

TITLE_HINTS = ("Open General", "OpenGen", "Open Gen")
CLASS_HINTS = ("SDL_app", "SDL")


def pids_of(name="OpenGen.exe"):
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + name, "/FO", "CSV", "/NH"],
                             capture_output=True).stdout.decode("mbcs", "ignore")
    except Exception:
        return []
    res = []
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[0].lower() == name.lower():
            try:
                res.append(int(parts[1]))
            except ValueError:
                pass
    return res


def find_window():
    """Return the best-matching top-level window of OpenGen.

    Prefers the *newest* process (highest pid) and the largest visible client
    area -- a single OpenGen run can expose a dozen top-level windows and
    picking the wrong one silently screenshots another instance.
    """
    pids = set(pids_of())
    newest = max(pids) if pids else None
    cands = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        p = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if pids and p.value not in pids:
            return True
        n = user.GetWindowTextLengthW(hwnd) + 1
        tb = ctypes.create_unicode_buffer(n)
        user.GetWindowTextW(hwnd, tb, n)
        cls = ctypes.create_unicode_buffer(256)
        user.GetClassNameW(hwnd, cls, 256)
        vis = bool(user.IsWindowVisible(hwnd))
        r = wintypes.RECT()
        user.GetClientRect(hwnd, ctypes.byref(r))
        area = (r.right - r.left) * (r.bottom - r.top)
        score = 0
        if pids and p.value in pids:
            score += 4
        if newest is not None and p.value == newest:
            score += 8
        if any(h.lower() in tb.value.lower() for h in TITLE_HINTS):
            score += 4
        if any(h.lower() in cls.value.lower() for h in CLASS_HINTS):
            score += 4
        if vis:
            score += 1
        if score >= 4:
            cands.append((score, vis, area, hwnd, tb.value, cls.value, p.value))
        return True

    user.EnumWindows(cb, 0)
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1], t[2]), reverse=True)
    s, vis, area, hwnd, title, cls, pid = cands[0]
    return dict(hwnd=hwnd, title=title, cls=cls, pid=pid, visible=vis, score=s,
                n=len(cands), area=area,
                all=[(c[6], c[4], c[5], c[2], c[1]) for c in cands])


def client_size(hwnd):
    r = wintypes.RECT()
    user.GetClientRect(hwnd, ctypes.byref(r))
    return r.right - r.left, r.bottom - r.top


class BMIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_int),
                ("biHeight", ctypes.c_int), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_int),
                ("biYPelsPerMeter", ctypes.c_int), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BMI(ctypes.Structure):
    _fields_ = [("bmiHeader", BMIH), ("bmiColors", wintypes.DWORD * 3)]


def png_write(path, w, h, bgra):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        row = bgra[y * w * 4:(y + 1) * w * 4]
        for x in range(w):
            b, g, r = row[x * 4], row[x * 4 + 1], row[x * 4 + 2]
            raw += bytes((r, g, b))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + \
        chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(out)


def shot(hwnd, out):
    w, h = client_size(hwnd)
    hdc = user.GetDC(hwnd)
    memdc = gdi.CreateCompatibleDC(hdc)
    hbmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, hbmp)
    ok = user.PrintWindow(hwnd, memdc, 2)
    bi = BMI()
    bi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi.GetDIBits(memdc, hbmp, 0, h, buf, ctypes.byref(bi), 0)
    png_write(out, w, h, buf.raw)
    gdi.DeleteObject(hbmp)
    gdi.DeleteDC(memdc)
    user.ReleaseDC(hwnd, hdc)
    print("shot %dx%d -> %s (PrintWindow=%s)" % (w, h, out, ok))
    return w, h


def click(hwnd, x, y, pause=1.2):
    lp = (y << 16) | x
    user.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.15)
    user.PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lp)
    time.sleep(0.08)
    user.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(pause)
    print("click (%d,%d)" % (x, y))


def key(hwnd, vk, count=1, pause=0.6):
    for _ in range(count):
        user.PostMessageW(hwnd, WM_KEYDOWN, vk, 0)
        time.sleep(0.05)
        user.PostMessageW(hwnd, WM_KEYUP, vk, 0)
        time.sleep(pause)
        print("key vk=%d" % vk)


def png_read_rgb(path):
    """Decode a PNG written by png_write (8-bit RGB, filter 0)."""
    d = open(path, "rb").read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n"
    i = 8
    idat = b""
    w = h = 0
    while i < len(d):
        ln = struct.unpack(">I", d[i:i + 4])[0]
        tag = d[i + 4:i + 8]
        data = d[i + 8:i + 8 + ln]
        if tag == b"IHDR":
            w, h = struct.unpack(">II", data[:8])
        elif tag == b"IDAT":
            idat += data
        i += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3 + 1
    rows = []
    for y in range(h):
        off = y * stride
        assert raw[off] == 0, "unexpected filter %d" % raw[off]
        rows.append(raw[off + 1:off + 1 + w * 3])
    return w, h, rows


def zoom(src, x, y, cw, ch, scale, out):
    w, h, rows = png_read_rgb(src)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + cw), min(h, y + ch)
    ow, oh = (x1 - x0) * scale, (y1 - y0) * scale
    raw = bytearray()
    for yy in range(y0, y1):
        row = rows[yy]
        line = bytearray()
        for xx in range(x0, x1):
            px = row[xx * 3:xx * 3 + 3]
            line += px * scale
        for _ in range(scale):
            raw.append(0)
            raw += line

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0)
    open(out, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                          chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
    print("zoom (%d,%d)-(%d,%d) x%d -> %s (%dx%d)" % (x0, y0, x1, y1, scale, out, ow, oh))


def diff_scan(src, y0, y1, minw=8, gold=True):
    """Find horizontal runs of gold-ish (or any non-dark) pixels inside a y band."""
    w, h, rows = png_read_rgb(src)
    y0, y1 = max(0, y0), min(h, y1)
    cols = []
    for x in range(w):
        hit = 0
        for y in range(y0, y1):
            r, g, b = rows[y][x * 3], rows[y][x * 3 + 1], rows[y][x * 3 + 2]
            if gold:
                if r > 110 and g > 85 and b < 140 and (r - b) > 40:
                    hit += 1
            else:
                if (r + g + b) > 150:
                    hit += 1
        cols.append(hit)
    runs = []
    x = 0
    while x < w:
        if cols[x] > 0:
            s = x
            while x < w and cols[x] > 0:
                x += 1
            if x - s >= minw:
                runs.append((s, x - 1, (s + x - 1) // 2, x - s))
        else:
            x += 1
    print("band y=%d..%d  runs>=%d : %d" % (y0, y1, minw, len(runs)))
    for s, e, c, ln in runs:
        print("   x %4d..%4d  center=%4d  width=%d" % (s, e, c, ln))
    return runs


def cmp_img(a, b):
    wa, ha, ra = png_read_rgb(a)
    wb, hb, rb = png_read_rgb(b)
    if (wa, ha) != (wb, hb):
        print("size differs %dx%d vs %dx%d" % (wa, ha, wb, hb))
        return 2
    tot = 0
    mx = 0
    nd = 0
    for y in range(ha):
        xa, xb = ra[y], rb[y]
        for x in range(wa * 3):
            d = abs(xa[x] - xb[x])
            tot += d
            if d > mx:
                mx = d
            if d > 24:
                nd += 1
    n = wa * ha * 3
    print("mean=%.3f  max=%d  pixels>24=%d (%.3f%%)  [%s vs %s]"
          % (tot / float(n), mx, nd, 100.0 * nd / n, a, b))
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "zoom":
        zoom(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]),
             int(sys.argv[6]), int(sys.argv[7]), sys.argv[8])
        return 0
    if cmd == "cmp":
        return cmp_img(sys.argv[2], sys.argv[3])
    if cmd == "scan":
        diff_scan(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]),
                  int(sys.argv[5]) if len(sys.argv) > 5 else 8)
        return 0
    info = find_window()
    if not info:
        print("OpenGen window not found (running pids: %s)" % pids_of())
        return 1
    hwnd = info["hwnd"]
    if cmd == "info":
        w, h = client_size(hwnd)
        print("hwnd=%s pid=%d class=%r title=%r visible=%s candidates=%d client=%dx%d"
              % (hwnd, info["pid"], info["cls"], info["title"], info["visible"], info["n"], w, h))
        for pid, title, cls, area, vis in info.get("all", [])[:14]:
            print("   cand pid=%-7d vis=%-5s area=%-9d class=%r title=%r" % (pid, vis, area, cls, title))
        return 0
    if cmd == "shot":
        shot(hwnd, sys.argv[2] if len(sys.argv) > 2 else "og.png")
        return 0
    if cmd == "click":
        click(hwnd, int(sys.argv[2]), int(sys.argv[3]),
              float(sys.argv[4]) if len(sys.argv) > 4 else 1.2)
        return 0
    if cmd == "key":
        key(hwnd, int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1)
        return 0
    if cmd == "seq":
        pre = sys.argv[2] if len(sys.argv) > 2 else "seq"
        iv = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
        cnt = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        for i in range(cnt):
            shot(hwnd, "%s%02d.png" % (pre, i))
            time.sleep(iv)
        return 0
    print("unknown cmd %r" % cmd)
    return 1


if __name__ == "__main__":
    sys.exit(main())
