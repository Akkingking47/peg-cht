#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only string/resource survey of a PE file. Extracts ASCII and UTF-16LE
printable strings and searches for localization-relevant tokens. Never writes
to the target file."""
import sys, re

def ascii_strings(data, minlen=4):
    out = []
    pat = re.compile(rb'[\x20-\x7e]{%d,}' % minlen)
    for m in pat.finditer(data):
        out.append((m.start(), m.group().decode('latin-1')))
    return out

def utf16_strings(data, minlen=4):
    out = []
    pat = re.compile(rb'(?:[\x20-\x7e]\x00){%d,}' % minlen)
    for m in pat.finditer(data):
        try:
            s = m.group().decode('utf-16-le')
            out.append((m.start(), s))
        except Exception:
            pass
    return out

def main():
    path = sys.argv[1]
    with open(path, 'rb') as f:
        data = f.read()
    print("=== FILE: %s ===" % path)
    print("size bytes: %d" % len(data))

    toks = ["Font", "EastFont", "CreateFont", "MS Sans", "Arial", "Courier",
            "SimSun", "SimHei", "charset", "CharSet", "DEFAULT_CHARSET",
            "ANSI_CHARSET", ".bmp", ".BMP", ".scn", ".oob", ".gph", ".cnt",
            "Menu", "Scenario", "Exit", "File", "Edit", "Help", "Turn",
            "Unit", "Victory", "Defeat", "CodePage", "codepage", "936",
            "GetText", "DialogBox", "LoadString"]
    # ASCII
    a = ascii_strings(data, 4)
    # UTF-16
    u = utf16_strings(data, 4)

    print("\n--- ASCII string count: %d ---" % len(a))
    print("--- UTF-16LE string count: %d ---" % len(u))

    # Show tokens of interest
    for t in toks:
        tb = t.encode('latin-1')
        hits_a = [o for (off,o) in a if tb in o.encode('latin-1')]
        if hits_a:
            print("\n[ASCII token] %s (%d hits):" % (t, len(hits_a)))
            for o in hits_a[:8]:
                print("   ", repr(o[:120]))
        # utf16
        for (off,o) in u:
            if t in o:
                print("\n[UTF16 token] %s: %r" % (t, o[:120]))
                break

    # Print a sampling of the longest/most informative ASCII strings (UI-ish)
    print("\n--- Sample of ASCII strings containing spaces (likely UI/text) ---")
    shown = 0
    for (off,o) in a:
        if ' ' in o and len(o) > 8:
            print("  %08x  %s" % (off, o[:160]))
            shown += 1
            if shown >= 60:
                break

if __name__ == '__main__':
    main()
