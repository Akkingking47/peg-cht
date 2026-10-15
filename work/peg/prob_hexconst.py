import hint_pe as H, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
d=H.load(H.SRC); md=Cs(CS_ARCH_X86,CS_MODE_32)
RANGES=[(0x43CDCE,0x43D180,'screen->map 0x43CDCE'),
        (0x43D57E,0x43D720,'map->screen 0x43D57E'),
        (0x43ECB9,0x43EE20,'hex lookup 0x43ECB9'),
        (0x448E94,0x449B40,'map click 0x448E94'),
        (0x44B1D7,0x44B260,'0x44B1D7'),
        (0x40B5BC,0x40B660,'0x40B5BC')]
pat=re.compile(r'0x(31f|320|321|257|258|259|23b|23c|23a|19|18|1a|5dc|438|780|77f|437)\b')
for lo,hi,name in RANGES:
    fo=H.va_to_fo(lo); blob=d[fo:H.va_to_fo(hi)]
    print(f'=== {name} 0x{lo:06X}-0x{hi:06X} ===')
    for ins in md.disasm(blob, lo):
        t=f'{ins.mnemonic} {ins.op_str}'
        if pat.search(t) or 'imul' in t and ', 0x19' in t or 'idiv' in t:
            print(f'  0x{ins.address:06X}  {ins.bytes.hex(" ")}  {t}')
