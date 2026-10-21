b = open(r"D:\Program Files\PeG\PeG030.exe", "rb").read()
tgt = bytes.fromhex("0fbf05748d4900")
i = 0
while True:
    i = b.find(tgt, i)
    if i < 0:
        break
    va = i - 0x400 + 0x401000
    calls = []
    j = i + 7
    while j < i + 7 + 80:
        if b[j] == 0xE8:
            rel = int.from_bytes(b[j + 1:j + 5], "little", signed=True)
            calls.append((j + 5 - 0x400 + 0x401000) + rel)
            j += 5
        else:
            j += 1
    print("%X -> %s" % (va, " ".join("%X" % c for c in calls[:6])))
    i += len(tgt)
