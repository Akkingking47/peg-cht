import ctypes as C
k32 = C.WinDLL("kernel32", use_last_error=True)
k32.CreateToolhelp32Snapshot.restype = C.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [C.c_uint32, C.c_uint32]
class TE(C.Structure):
    _fields_=[("dwSize",C.c_uint32),("cntUsage",C.c_uint32),("th32ThreadID",C.c_uint32),("th32OwnerProcessID",C.c_uint32),("tpBasePri",C.c_int32),("tpDeltaPri",C.c_int32),("dwFlags",C.c_uint32)]
k32.Thread32First.argtypes=[C.c_void_p,C.POINTER(TE)]
k32.Thread32First.restype=C.c_int
k32.Thread32Next.argtypes=[C.c_void_p,C.POINTER(TE)]
k32.Thread32Next.restype=C.c_int
snap = k32.CreateToolhelp32Snapshot(0x4, 0)
print("snap=",hex(snap or 0),"err=",C.get_last_error())
te=TE(); te.dwSize=C.sizeof(TE)
r=k32.Thread32First(snap,C.byref(te))
print("first=",r,"err=",C.get_last_error())
n=0; tids=[]
while r:
    n+=1
    tids.append((te.th32OwnerProcessID,te.th32ThreadID))
    r=k32.Thread32Next(snap,C.byref(te))
print("total",n,"last err",C.get_last_error())
print("target pids:",[t for t in tids if t[0] in (15928,21232)])
