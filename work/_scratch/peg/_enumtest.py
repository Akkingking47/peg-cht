import ctypes as C
k32=C.WinDLL("kernel32",use_last_error=True)
k32.CreateToolhelp32Snapshot.restype=C.c_void_p
k32.CreateToolhelp32Snapshot.argtypes=[C.c_uint32,C.c_uint32]
class PE(C.Structure):
    _fields_=[("dwSize",C.c_uint32),("cntUsage",C.c_uint32),("th32ProcessID",C.c_uint32),("th32DefaultHeapID",C.c_void_p),("th32ModuleID",C.c_uint32),("cntThreads",C.c_uint32),("th32ParentProcessID",C.c_uint32),("pcPriClassBase",C.c_int32),("dwFlags",C.c_uint32),("szExeFile",C.c_char*260)]
k32.Process32First.argtypes=[C.c_void_p,C.POINTER(PE)]; k32.Process32Next.argtypes=[C.c_void_p,C.POINTER(PE)]
s=k32.CreateToolhelp32Snapshot(2,0); print("snap",hex(s or 0),"size",C.sizeof(PE),"err",C.get_last_error())
p=PE(); p.dwSize=C.sizeof(PE); r=k32.Process32First(s,C.byref(p)); print("first",r,"err",C.get_last_error())
n=0; names=[]
while r:
    n+=1
    if b'PeG' in p.szExeFile or b'peg' in p.szExeFile: names.append((p.th32ProcessID,p.szExeFile))
    r=k32.Process32Next(s,C.byref(p))
print("count",n,"peg:",names)
