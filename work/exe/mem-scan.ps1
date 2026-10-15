<#
  mem-scan.ps1 —— 在游戏进程内存中搜索字符串
  用法: .\mem-scan.ps1 -ProcessName OpenGen -Patterns "Bocage","Fort","Clear"
  目的: 判断地图地形标签是「exe 映像内的静态数据」还是「运行时动态生成的堆数据」
#>
[CmdletBinding()]
param(
    [string]$ProcessName = 'OpenGen',
    [string[]]$Patterns = @('Bocage','Fort','Mountain','Forest','Swamp'),
    [int]$MaxHitsPerPattern = 10
)

$src = @"
using System;
using System.Runtime.InteropServices;
public class MemScan {
    [StructLayout(LayoutKind.Sequential)]
    public struct MEMORY_BASIC_INFORMATION {
        public IntPtr BaseAddress;
        public IntPtr AllocationBase;
        public uint AllocationProtect;
        public IntPtr RegionSize;
        public uint State;
        public uint Protect;
        public uint Type;
    }
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool CloseHandle(IntPtr h);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr VirtualQueryEx(IntPtr h, IntPtr addr, out MEMORY_BASIC_INFORMATION mbi, IntPtr len);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr read);
    [DllImport("kernel32.dll")] public static extern bool IsWow64Process(IntPtr h, out bool wow64);
}
"@
if (-not ("MemScan" -as [type])) { Add-Type -TypeDefinition $src -Language CSharp }

$proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $proc) { throw "进程 $ProcessName 未运行" }

$PROCESS_QUERY_INFORMATION = 0x0400
$PROCESS_VM_READ           = 0x0010
$h = [MemScan]::OpenProcess($PROCESS_QUERY_INFORMATION -bor $PROCESS_VM_READ, $false, $proc.Id)
if ($h -eq [IntPtr]::Zero) { throw "OpenProcess 失败，错误码 $([Runtime.InteropServices.Marshal]::GetLastWin32Error())" }
Write-Host ("已打开进程 PID={0} 句柄={1}" -f $proc.Id, $h)

$isWow = $false
[void][MemScan]::IsWow64Process($h, [ref]$isWow)
Write-Host ("目标为 WOW64 32 位进程: {0}" -f $isWow)
Write-Host ''

# 搜索模式（ASCII 与 UTF-16LE 两种）
$needles = @{}
foreach ($pat in $Patterns) {
    $ascii = [Text.Encoding]::ASCII.GetBytes($pat)
    $u16 = [Text.Encoding]::Unicode.GetBytes($pat)
    $needles["$pat (ASCII)"] = $ascii
    $needles["$pat (UTF16)"] = $u16
}

$hits = @{}
foreach ($k in $needles.Keys) { $hits[$k] = New-Object System.Collections.Generic.List[uint32] }

# 遍历内存区域
$addr = [uint32]0x10000                      # 跳过 NULL 页
$maxAddr = if ($isWow) { [uint32]0x7FFFFFFF } else { [uint32]0x7FFFFFFF }
$mbi = New-Object 'MemScan+MEMORY_BASIC_INFORMATION'
$scanned = 0
while ($addr -lt $maxAddr) {
    $q = [MemScan]::VirtualQueryEx($h, [IntPtr][uint32]$addr, [ref]$mbi, [IntPtr][uint32][Runtime.InteropServices.Marshal]::SizeOf($mbi))
    if ($q -eq [IntPtr]::Zero) { break }
    $base = [uint32]$mbi.BaseAddress.ToInt64()
    $size = [uint32]$mbi.RegionSize.ToInt64()
    if ($size -eq 0) { break }

    # 只看已提交(0x1000)且可读的区（PAGE_READONLY 0x02 / READWRITE 0x04 / WRITECOPY 0x08 / EXECUTE_READ 0x20 / EXECUTE_READWRITE 0x40）
    $okState = ($mbi.State -band 0x1000) -ne 0
    $okProt  = ($mbi.Protect -band 0x02) -ne 0 -or ($mbi.Protect -band 0x04) -ne 0 -or ($mbi.Protect -band 0x08) -ne 0 -or ($mbi.Protect -band 0x20) -ne 0 -or ($mbi.Protect -band 0x40) -ne 0
    $noGuard = ($mbi.Protect -band 0x100) -eq 0        # 排除 PAGE_GUARD

    if ($okState -and $okProt -and $noGuard -and $size -le 64MB) {
        $buf = New-Object byte[] $size
        $read = [IntPtr]::Zero
        $r = [MemScan]::ReadProcessMemory($h, [IntPtr][uint32]$base, $buf, [IntPtr][uint32]$size, [ref]$read)
        if ($r) {
            $n = [int]$read.ToInt64()
            $scanned += $n
            foreach ($k in $needles.Keys) {
                if ($hits[$k].Count -ge $MaxHitsPerPattern) { continue }
                $nd = $needles[$k]
                $first = $nd[0]
                for ($i = 0; ($i + $nd.Length) -le $n; $i++) {
                    if ($buf[$i] -ne $first) { continue }
                    $m = $true
                    for ($j = 1; $j -lt $nd.Length; $j++) { if ($buf[$i + $j] -ne $nd[$j]) { $m = $false; break } }
                    if ($m) {
                        $hits[$k].Add([uint32]($base + $i))
                        if ($hits[$k].Count -ge $MaxHitsPerPattern) { break }
                    }
                }
            }
        }
    }
    $next = [uint32]($base + $size)
    if ($next -le $addr) { $addr = $addr + 0x1000 } else { $addr = $next }
}

[void][MemScan]::CloseHandle($h)
Write-Host ("扫描 {0:N0} 字节内存" -f $scanned)
Write-Host ''
$imgBase = [uint32]$proc.MainModule.BaseAddress.ToInt64()
$imgEnd  = $imgBase + [uint32]$proc.MainModule.ModuleMemorySize
Write-Host ("exe 映像范围: 0x{0:X8} - 0x{1:X8}" -f $imgBase, $imgEnd)
Write-Host ''
foreach ($k in $needles.Keys) {
    Write-Host ("--- {0} : {1} 处 ---" -f $k, $hits[$k].Count)
    foreach ($a in $hits[$k]) {
        $where = if ($a -ge $imgBase -and $a -lt $imgEnd) {
            "exe映像内 (文件偏移 0x{0:X6})" -f ($a - $imgBase + 0x400)
        } else { '堆/其他' }
        Write-Host ("    0x{0:X8}  {1}" -f $a, $where)
    }
}
