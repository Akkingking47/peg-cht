b = open(r"D:\Program Files\PeG\PeG030.exe", "rb").read()


def calls(va, span=0xC0):
    i = va - 0x401000 + 0x400
    out = []
    j = i
    while j < i + span:
        if b[j] == 0xE8:
            rel = int.from_bytes(b[j + 1:j + 5], "little", signed=True)
            out.append((j + 5 - 0x400 + 0x401000) + rel)
            j += 5
        else:
            j += 1
    return out


for va in (0x4517F7, 0x450553, 0x4443C3, 0x446B9E, 0x43FE70, 0x4517F7 + 0xC0):
    print("%X -> %s" % (va, " ".join("%X" % c for c in calls(va, 0x100))))
