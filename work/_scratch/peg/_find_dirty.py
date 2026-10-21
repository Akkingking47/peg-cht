b = open(r"D:\Program Files\PeG\PeG030.exe", "rb").read()
tgt = bytes.fromhex("748d4900")
hits = []
i = 0
while True:
    i = b.find(tgt, i)
    if i < 0:
        break
    va = i - 0x400 + 0x401000
    prev = b[i - 3:i].hex()
    hits.append((va, prev))
    i += 1
print("count", len(hits))
for va, prev in hits:
    print("%X %s" % (va, prev))
