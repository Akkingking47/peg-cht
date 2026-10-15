<#
  mem-dump.ps1 —— 在游戏进程内存中搜索并 dump 上下文
  用法: .\mem-dump.ps1 -Pattern "Ocean" -Context 120
#>
[CmdletBinding()]
param(
    [string]$ProcessName = 'OpenGen',
    [string]$Pattern = 'Ocean',
    [int]$Context = 120,
    [int]$MaxHits = 6
)

$src = @"
using System;
using System.Runtime.InteropServices;
public class MemDump {
    [StructLayout(LayoutKind.Sequential)]
    public struct MEMORY_BASIC_INFORMATION {
        public IntPtr BaseAddress; public IntPtr AllocationBase; public uint AllocationProtect;
        public IntPtr RegionSize; public uint State; public uint Protect; public uint Type;
    }
    [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr OpenProcess(uint a, bool i, int pid);
    [DllImport("kernel32.dll", SetLastError=true)] public static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll", SetLastError=true)] public static extern IntPtr VirtualQueryEx(IntPtr h, IntPtr a, out MEMORY_BASIC_INFORMATION m, IntPtr l);
    [DllImport("kernel32.dll", SetLastError=true)] public static extern bool ReadProcessMemory(IntPtr h, IntPtr a, byte[] b, IntPtr s, out IntPtr r);
}
"@
if (-not ("MemDump" -as [type])) { Add-Type -TypeDefinition $src -Language CSharp }

$proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $proc) { throw "进程未运行" }
$h = [MemDump]::OpenProcess(0x0410, $false, $proc.Id)
if ($h -eq [IntPtr]::Zero) { throw "OpenProcess 失败" }

$patA = [Text.Encoding]::ASCII.GetBytes($Pattern)
$patU = [Text.Encoding]::Unicode.GetBytes($Pattern)
$found = @()

$addr = [uint32]0x10000
$mbi = New-Object 'MemDump+MEMORY_BASIC_INFORMATION'
while ($addr -lt [uint32]0x7FFFFFFF -and $found.Count -lt $MaxHits) {
    $q = [MemDump]::VirtualQueryEx($h, [IntPtr][uint32]$addr, [ref]$mbi, [IntPtr][uint32][Runtime.InteropServices.Marshal]::SizeOf($mbi))
    if ($q -eq [IntPtr]::Zero) { break }
    $base = [uint32]$mbi.BaseAddress.ToInt64()
    $size = [uint32]$mbi.RegionSize.ToInt64()
    if ($size -eq 0) { break }
    $ok = (($mbi.State -band 0x1000) -ne 0) -and (($mbi.Protect -band 0x02) -ne 0 -or ($mbi.Protect -band 0x04) -ne 0 -or ($mbi.Protect -band 0x08) -ne 0 -or ($mbi.Protect -band 0x20) -ne 0 -or ($mbi.Protect -band 0x40) -ne 0) -and (($mbi.Protect -band 0x100) -eq 0) -and $size -le 64MB
    if ($ok) {
        $buf = New-Object byte[] $size
        $read = [IntPtr]::Zero
        if ([MemDump]::ReadProcessMemory($h, [IntPtr][uint32]$base, $buf, [IntPtr][uint32]$size, [ref]$read)) {
            $n = [int]$read.ToInt64()
            foreach ($nd in @($patA, $patU)) {
                for ($i = 0; ($i + $nd.Length) -le $n; $i++) {
                    if ($buf[$i] -ne $nd[0]) { continue }
                    $m = $true
                    for ($j = 1; $j -lt $nd.Length; $j++) { if ($buf[$i + $j] -ne $nd[$j]) { $m = $false; break } }
                    if ($m) {
                        $found += [pscustomobject]@{ Addr = [uint32]($base + $i); IsU16 = ($nd.Length -eq $patU.Length -and $patU[0] -eq $nd[0] -and $patU.Length -gt 1) }
                        if ($found.Count -ge $MaxHits) { break }
                    }
                }
                if ($found.Count -ge $MaxHits) { break }
            }
        }
    }
    $next = [uint32]($base + $size)
    $addr = if ($next -le $addr) { $addr + 0x1000 } else { $next }
}

Write-Host ("找到 {0} 处" -f $found.Count)
Write-Host ''
foreach ($f in $found) {
    Write-Host ("=== 0x{0:X8} ===" -f $f.Addr)
    $lo = [uint32]([Math]::Max(0x10000, [int64]$f.Addr - $Context))
    $len = $Context * 2
    $buf = New-Object byte[] $len
    $read = [IntPtr]::Zero
    if ([MemDump]::ReadProcessMemory($h, [IntPtr][uint32]$lo, $buf, [IntPtr][uint32]$len, [ref]$read)) {
        $n = [int]$read.ToInt64()
        # 按 NUL 切分显示可读串
        $cur = New-Object System.Text.StringBuilder
        for ($i = 0; $i -lt $n; $i++) {
            $c = $buf[$i]
            if ($c -ge 32 -and $c -le 126) { [void]$cur.Append([char]$c) }
            else {
                if ($cur.Length -ge 2) {
                    $abs = $lo + $i - $cur.Length
                    Write-Host ("    [0x{0:X8}] {1}" -f $abs, $cur.ToString())
                }
                [void]$cur.Clear()
            }
        }
        if ($cur.Length -ge 2) { Write-Host ("    [0x{0:X8}] {1}" -f ($lo + $n - $cur.Length), $cur.ToString()) }
    }
    Write-Host ''
}
[void][MemDump]::CloseHandle($h)
