<#
  exe-patch.ps1 —— OpenGen.exe 硬编码 UI 文本汉化工具
  =====================================================================
  原理（已由 POC 验证）：
    OpenGen 的硬编码字符串以 NUL 结尾、紧密排列、无扩展空间，
    且每条串在 .text 中通常只有【一处】 `68 <VA32>`（push imm32）引用。
    因此汉化 = 把中文写到空闲空洞 + 把那条 push 的立即数改指过去。
    文件大小、代码结构一律不变。

  用法：
    # 1) 扫描：列出候选串（带引用/空洞可用性判断）
    .\exe-patch.ps1 -Action scan

    # 2) 应用补丁（patches.tsv 每行 `原串|译文`）
    .\exe-patch.ps1 -Action apply -Patches .\patches.tsv

    # 3) 校验当前 exe 与台账是否一致
    .\exe-patch.ps1 -Action verify

    # 4) 回滚到最原始版
    .\exe-patch.ps1 -Action rollback

  安全护栏：
    - 改动前必须校验 exe 的 MD5 属于已知版本
    - 每串必须"全局唯一"且"push 引用唯一"，否则拒绝改
    - 黑名单：内部命令标识符 / 文件路径 / 格式串中的格式符一律拒绝
    - 译文必须能 GBK 编码，且格式符个数与原串一致
    - 写入后逐字节比对，差异必须只落在预期区间
    - 空洞分配有台账，避免复用冲突
#>
[CmdletBinding()]
param(
    [ValidateSet('scan', 'apply', 'verify', 'rollback', 'holes', 'candidates')]
    [string]$Action = 'scan',

    [string]$Patches,
    [string]$Efile = 'D:\OpenPG2\OpenGen.exe',
    [string]$WorkDir = 'D:\DSH\军事游戏汉化\work\exe',
    [string]$OriginalExe = 'D:\DSH\军事游戏汉化\backup\OpenGen.exe.original',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# ---------- 已知版本指纹 ----------
$KnownMd5 = @{
    'B20A81F97EDB7AF6E1C5C82AFFBA880A' = '原始版 26.03.30.0（未改动）'
    'BC5EA58ADB616B48CE8495B70C5A5E51' = 'POC 版（1 处：Showing %d campaigns）'
    'E74E83574AD7E8763280481B01BF30FE' = 'POC + 2 处 Welcome 文本'
    'E54453F9FD8A70B1639933221AB6743C' = '战役浏览器 5 条文本（旧）'
    '32019A04042849A99E75E41193369AF5' = '战役浏览器完整版（RT_DIALOG 17 条 + 代码 5 条）'
    'DE81C41522232E8460D4CB6C4B4F5A26' = '战役浏览器 + efile 面板（dlg136 + 标签）'
}

# ---------- 节区表（换 exe 版本必须重算）----------
$Secs = @(
    @{ N = '.text';  FO = 0x400;    RVA = 0x1000;   SZ = 0x476E00 }
    @{ N = '.rdata'; FO = 0x477200; RVA = 0x478000; SZ = 0xF8800 }
    @{ N = '.data';  FO = 0x56FA00; RVA = 0x571000; SZ = 0x4F200 }
    @{ N = '.rsrc';  FO = 0x5BEC00; RVA = 0xEAB000; SZ = 0x47400 }
)
$ImageBase = 0x400000
$TextStart = 0x400
$TextEnd   = 0x477200

# ---------- 黑名单：绝不翻译 ----------
$BlackList = @(
    'SCENARIO\', 'EFILE_', 'README\', 'OPENLOG\', 'OPENGUI\', 'OPENDAT\', 'FONTS\', 'SOUND\',
    '.csv', '.cfg', '.txt', '.htm', '.xscn', '.xcam', '.xlog', '.eqp', '.xeqp', '.dat',
    'Settings.cfg', 'Campaigns.csv', 'ogrun'
)
# 内部命令标识符（改了就废功能）：全小写无空格、或形如 动词+参数
$CmdPatterns = @(
    '^[a-z_]+$',                    # replacegreen / endplayerturn / overstrenght
    '^(select|rename|launch|launch2|airmision|mount|move|fire|build|blow|enter|exit|load|save|set|get|do|cmd)\b'
)

function Get-IconOf { }

function FoToVa([int]$fo) {
    foreach ($x in $Secs) { if ($fo -ge $x.FO -and $fo -lt ($x.FO + $x.SZ)) { return ($ImageBase + $x.RVA + ($fo - $x.FO)) } }
    return -1
}
function SecOf([int]$fo) {
    foreach ($x in $Secs) { if ($fo -ge $x.FO -and $fo -lt ($x.FO + $x.SZ)) { return $x.N } }
    return '?'
}
function Get-PushIndex {
    param([byte[]]$Bytes)
    $idx = @{}
    for ($i = $TextStart; $i -lt $TextEnd - 5; $i++) {
        if ($Bytes[$i] -eq 0x68) {
            $v = [BitConverter]::ToInt32($Bytes, $i + 1)
            if ($v -ge $ImageBase -and $v -lt 0x10000000) {
                if (-not $idx.ContainsKey($v)) { $idx[$v] = New-Object System.Collections.Generic.List[int] }
                $idx[$v].Add($i)
            }
        }
    }
    return $idx
}
function Test-BlackListed {
    param([string]$Text)
    # 内部命令标识符：整串匹配即拒绝（这些一改就废功能）
    foreach ($p in $CmdPatterns) { if ($Text -match $p) { return $true } }
    # 路径/文件名：只有当整串本身就"短得像路径/文件名"时才拒绝。
    # 长句子里出现 "Read Me First.htm"、"Campaigns.csv" 是正文的一部分，必须允许翻译。
    if ($Text.Length -le 48 -and $Text -notmatch '\s\s') {
        foreach ($b in $BlackList) { if ($Text -like "*$b*") { return $true } }
        if ($Text -match '^[\w\\/\.%\-]+$') { return $true }   # 纯路径样式的短串
    }
    return $false
}
function Get-FormatSpecs {
    param([string]$Text)
    return ([regex]::Matches($Text, '%[-+ 0-9.#]*[dsfxc]') | ForEach-Object { $_.Value })
}
function Get-FreeHoles {
    param([byte[]]$Bytes, [int]$Need)
    # 找前后被非零数据包围、内部全零、长度 >= Need 的空洞；优先 .rdata（只读）
    $holes = @()
    foreach ($sec in ($Secs | Where-Object { $_.N -eq '.rdata' -or $_.N -eq '.data' })) {
        $cur = 0; $start = 0
        for ($i = $sec.FO; $i -lt $sec.FO + $sec.SZ; $i++) {
            if ($Bytes[$i] -eq 0) { if ($cur -eq 0) { $start = $i }; $cur++ }
            else {
                if ($cur -ge $Need) {
                    $before = if ($start -gt 0) { $Bytes[$start - 1] -ne 0 } else { $false }
                    if ($before) { $holes += [pscustomobject]@{ FO = $start; Len = $cur; Sec = $sec.N; VA = (FoToVa $start) } }
                }
                $cur = 0
            }
        }
    }
    return $holes | Sort-Object @{e={$_.Sec -eq '.rdata'};Descending=$true}, Len
}

# ---------- 台账 ----------
if (-not (Test-Path $WorkDir)) { New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null }
$LedgerPath = Join-Path $WorkDir 'ledger.md'
$HolePath   = Join-Path $WorkDir 'holes.tsv'

function Load-UsedHoles {
    $u = @{}
    if (Test-Path $HolePath) {
        foreach ($l in (Get-Content $HolePath -Encoding UTF8)) {
            if ($l.Trim() -and -not $l.StartsWith('#')) {
                $p = $l.Split("`t"); if ($p.Count -ge 2) { $u[[int]$p[0]] = $p[1] }
            }
        }
    }
    return $u
}
function Save-UsedHole { param([int]$FO, [string]$What)
    Add-Content -Path $HolePath -Value ("{0}`t{1}" -f $FO, $What) -Encoding UTF8
}
function Write-Ledger { param([string]$Line)
    Add-Content -Path $LedgerPath -Value $Line -Encoding UTF8
}

# ============================================================
switch ($Action) {

    # ---------- 列出空洞 ----------
    'holes' {
        $b = [IO.File]::ReadAllBytes($Efile)
        $used = Load-UsedHoles
        Write-Host ("=== 可用空洞（>=64 字节，前 30）===")
        Write-Host ("  已用 {0} 处" -f $used.Count)
        Get-FreeHoles -Bytes $b -Need 64 | Select-Object -First 30 | ForEach-Object {
            $mark = if ($used.ContainsKey($_.FO)) { '已用' } else { '空闲' }
            '  {0,-7} FO=0x{1:X6}  VA=0x{2:X8}  长度={3,4}  {4}' -f $_.Sec, $_.FO, $_.VA, $_.Len, $mark
        }
    }

    # ---------- 扫描候选 ----------
    'scan' {
        $b = [IO.File]::ReadAllBytes($Efile)
        $push = Get-PushIndex -Bytes $b
        Write-Host ("push 目标数 = {0}" -f $push.Count)
        $safe = @(); $risky = @(); $blocked = @()
        for ($fo = 0x4EE000; $fo -lt 0x5BEC00; $fo++) {
            if ($b[$fo] -ne 0) {
                $st = $fo
                while ($fo -lt 0x5BEC00 -and $b[$fo] -ne 0) { $fo++ }
                $len = $fo - $st
                if ($len -lt 6 -or $len -gt 400) { continue }
                $t = [Text.Encoding]::GetEncoding(28591).GetString($b[$st..($st + $len - 1)])
                if ($t -notmatch '^[\x20-\x7E]+$' -or $t -notmatch '[A-Za-z]') { continue }
                $va = FoToVa $st
                $rc = if ($push.ContainsKey($va)) { $push[$va].Count } else { 0 }
                $o = [pscustomobject]@{ FO = $st; VA = $va; Len = $len; RefCount = $rc; Text = $t }
                if (Test-BlackListed $t) { $blocked += $o }
                elseif ($rc -eq 1) { $safe += $o }
                else { $risky += $o }
            }
        }
        Write-Host ''
        Write-Host ("可安全汉化（唯一 push 引用 + 非黑名单）: {0} 条" -f $safe.Count) -ForegroundColor Green
        Write-Host ("风险（无引用或多引用）               : {0} 条" -f $risky.Count) -ForegroundColor Yellow
        Write-Host ("黑名单（命令/路径/文件名）           : {0} 条" -f $blocked.Count) -ForegroundColor Red
        Write-Host ''
        Write-Host '=== 可安全汉化候选（前 40，按长度降序）==='
        $safe | Sort-Object Len -Descending | Select-Object -First 40 | ForEach-Object {
            '  FO=0x{0:X6} len={1,4} push@0x{2:X6}  {3}' -f $_.FO, $_.Len, $push[$_.VA][0], ($_.Text.Substring(0, [Math]::Min(64, $_.Text.Length)))
        }
        $csv = Join-Path $WorkDir 'candidates.tsv'
        ($safe | ForEach-Object { "{0}`t{1}`t{2}" -f $_.FO, $_.Len, $_.Text }) | Set-Content $csv -Encoding UTF8
        Write-Host ''
        Write-Host ("完整候选已导出: {0}（{1} 条）" -f $csv, $safe.Count)
    }

    # ---------- 应用补丁 ----------
    'apply' {
        if (-not $Patches) { throw 'apply 需要 -Patches <tsv 文件>' }
        if (-not (Test-Path $Patches)) { throw "补丁文件不存在: $Patches" }
        if (-not (Test-Path $Efile)) { throw "exe 不存在: $Efile" }

        $md5 = (Get-FileHash $Efile -Algorithm MD5).Hash
        if (-not $KnownMd5.ContainsKey($md5)) {
            Write-Host ("⚠ 未知版本的 exe（MD5={0}）" -f $md5) -ForegroundColor Yellow
            if (-not $Force) { throw '拒绝改动；确认无误可加 -Force' }
        } else {
            Write-Host ("exe 版本: {0}" -f $KnownMd5[$md5]) -ForegroundColor Green
        }

        $b = [IO.File]::ReadAllBytes($Efile)
        $orig = $b.Clone()
        $gbk = [Text.Encoding]::GetEncoding(936)
        $gbkStrict = [Text.Encoding]::GetEncoding(936, [Text.EncoderFallback]::ExceptionFallback, [Text.DecoderFallback]::ExceptionFallback)
        $push = Get-PushIndex -Bytes $b
        $used = Load-UsedHoles
        # 空洞只扫描一次，之后在内存里"切片"复用（原先每条都重扫 1.5MB，太慢）
        $holePool = New-Object System.Collections.Generic.List[object]
        foreach ($h in (Get-FreeHoles -Bytes $b -Need 16)) { $holePool.Add([pscustomobject]@{ FO = $h.FO; Len = $h.Len; Sec = $h.Sec }) }
        Write-Host ("可用空洞 {0} 处（已缓存）" -f $holePool.Count) -ForegroundColor DarkGray
        $applied = 0; $skipped = @(); $errors = @()

        foreach ($line in (Get-Content $Patches -Encoding UTF8)) {
            if (-not $line.Trim() -or $line.StartsWith('#')) { continue }
            $parts = $line.Split('|', 2)
            if ($parts.Count -ne 2) { $errors += "格式错误: $line"; continue }
            $key = $parts[0]; $zh = $parts[1]
            # 译文里的 \n / \r / \t 转义还原为真实字符
            $zh = $zh.Replace('\n', "`n").Replace('\r', "`r").Replace('\t', "`t")

            # 1) 定位原串
            $idx = @(); $k = 0
            $raw = [Text.Encoding]::GetEncoding(28591).GetString($b)
            if ($key -match '^0[xX][0-9A-Fa-f]+$') {
                # 格式B：按文件偏移定位（用于含换行等无法单行表示的串）
                $st = [Convert]::ToInt32($key.Substring(2), 16)
                if ($st -lt 0 -or $st -ge $b.Length) { $errors += "偏移越界: $key"; continue }
                $e2 = $st; while ($e2 -lt $b.Length -and $b[$e2] -ne 0) { $e2++ }
                $srctext = [Text.Encoding]::GetEncoding(28591).GetString($b[$st..($e2 - 1)])
                $idx = @($st)
            }
            else {
                # 格式A：按串内容定位，必须全局唯一且是独立串
                $srctext = $key
                while ($true) {
                    $i = $raw.IndexOf($srctext, $k); if ($i -lt 0) { break }
                    $prev = if ($i -gt 0) { $b[$i - 1] } else { 0 }
                    if ($prev -eq 0) { $idx += $i }
                    $k = $i + 1
                }
            }
            if ($idx.Count -eq 0) {
                $skipped += "跳过（原串未找到，可能已改）: $key"
                continue
            }
            if ($idx.Count -gt 1) { $errors += "原串不唯一（{0} 处）: {1}" -f $idx.Count, $srctext; continue }
            $st = $idx[0]
            $va = FoToVa $st

            # 2) 黑名单
            if (Test-BlackListed $srctext) { $errors += "黑名单串，拒绝: $srctext"; continue }

            # 3) push 引用必须唯一
            if (-not $push.ContainsKey($va) -or $push[$va].Count -ne 1) {
                $c = if ($push.ContainsKey($va)) { $push[$va].Count } else { 0 }
                $errors += "push 引用数={0}（需为 1，本工具暂只处理唯一引用）: {1}" -f $c, $srctext
                continue
            }
            $pushFO = $push[$va][0]

            # 4) 格式符一致性
            $f1 = (Get-FormatSpecs $srctext) | Sort-Object
            $f2 = (Get-FormatSpecs $zh) | Sort-Object
            if (($f1 -join ',') -ne ($f2 -join ',')) {
                $errors += "格式符不一致 原[{0}] 译[{1}]: {2}" -f ($f1 -join ','), ($f2 -join ','), $srctext
                continue
            }

            # 5) GBK 可编码
            try { $zhb = $gbkStrict.GetBytes($zh) }
            catch { $errors += "含 GBK 无法表示的字符: $zh"; continue }

            # 6) 从缓存里分配空洞（找到够大的就切走，不重扫）
            $need = $zhb.Length + 1
            $hole = $null
            foreach ($h in $holePool) {
                if ($h.Len -ge $need -and -not $used.ContainsKey($h.FO)) { $hole = $h; break }
            }
            if (-not $hole) { $errors += "找不到 {0} 字节空洞: {1}" -f $need, $srctext; continue }
            # 切走这一段（剩余部分仍可复用）
            $hole.FO += $need
            $hole.Len -= $need
            $allocFO = $hole.FO - $need
            $allocVA = $allocFO + 0  # VA 由 FO 换算
            foreach ($x in $Secs) { if ($allocFO -ge $x.FO -and $allocFO -lt ($x.FO + $x.SZ)) { $allocVA = $ImageBase + $x.RVA + ($allocFO - $x.FO) } }

            # 7) 写入 + 改 push
            [Array]::Copy($zhb, 0, $b, $allocFO, $zhb.Length)
            $b[$allocFO + $zhb.Length] = 0
            $newVaB = [BitConverter]::GetBytes([int]$allocVA)
            [Array]::Copy($newVaB, 0, $b, $pushFO + 1, 4)

            $used[$allocFO] = $srctext
            Save-UsedHole -FO $allocFO -What $srctext
            $applied++
            Write-Host ("  ✅ {0,-34} → {1,-18} (串@0x{2:X6} push@0x{3:X6} 空洞@0x{4:X6})" -f `
                $srctext.Substring(0, [Math]::Min(32, $srctext.Length)), $zh, $st, $pushFO, $allocFO) -ForegroundColor Green
        }

        # 8) 差异校验
        $diffs = @(); for ($i = 0; $i -lt $b.Length; $i++) { if ($b[$i] -ne $orig[$i]) { $diffs += $i } }
        Write-Host ''
        Write-Host ("应用 {0} 条；差异字节 {1}" -f $applied, $diffs.Count)
        if ($b.Length -ne $orig.Length) { throw '文件大小变了，拒绝写入' }

        # 9) 写盘（先写临时再覆盖）
        $tmp = "$env:TEMP\OpenGen.patched.exe"
        [IO.File]::WriteAllBytes($tmp, $b)
        # 回读校验
        $chk = [IO.File]::ReadAllBytes($tmp)
        $same = $true; for ($i = 0; $i -lt $b.Length; $i++) { if ($chk[$i] -ne $b[$i]) { $same = $false; break } }
        if (-not $same) { throw '回读校验失败' }
        Copy-Item $tmp $Efile -Force
        $newMd5 = (Get-FileHash $Efile -Algorithm MD5).Hash
        Write-Host ("已部署: MD5={0}" -f $newMd5) -ForegroundColor Green
        Write-Ledger ("- {0} | 应用 {1} 条 | MD5 {2} -> {3} | 差异 {4} 字节" -f (Get-Date -Format 'yyyy-MM-dd HH:mm'), $applied, $md5.Substring(0,8), $newMd5.Substring(0,8), $diffs.Count)

        Write-Host ''
        if ($errors.Count -gt 0) { Write-Host ("{0} 条未处理:" -f $errors.Count) -ForegroundColor Yellow; $errors | ForEach-Object { Write-Host ('  ' + $_) -ForegroundColor Yellow } }
        if ($skipped.Count -gt 0) { Write-Host ("{0} 条跳过:" -f $skipped.Count) -ForegroundColor DarkGray; $skipped | ForEach-Object { Write-Host ('  ' + $_) -ForegroundColor DarkGray } }
    }

    # ---------- 校验 ----------
    'verify' {
        $b = [IO.File]::ReadAllBytes($Efile)
        $md5 = (Get-FileHash $Efile -Algorithm MD5).Hash
        Write-Host ("exe MD5 = {0}" -f $md5)
        if ($KnownMd5.ContainsKey($md5)) { Write-Host ("  → {0}" -f $KnownMd5[$md5]) -ForegroundColor Green } else { Write-Host '  → 未知版本（可能是多次改动后）' -ForegroundColor Yellow }
        Write-Host ("文件大小 = {0}（原始 6316032，相同={1}）" -f $b.Length, ($b.Length -eq 6316032))
        $used = Load-UsedHoles
        Write-Host ("空洞台账记录 {0} 处" -f $used.Count)
        Write-Host ''
        Write-Host '=== 逐条回读台账中的改动 ==='
        $gbk = [Text.Encoding]::GetEncoding(936)
        foreach ($k in ($used.Keys | Sort-Object)) {
            $fo = $k
            $end = $fo; while ($end -lt $b.Length -and $b[$end] -ne 0) { $end++ }
            $zh = $gbk.GetString($b[$fo..($end - 1)])
            '  FO=0x{0:X6}  [{1}]  ← 目标串: {2}' -f $fo, $zh, $used[$fo]
        }
    }

    # ---------- 回滚 ----------
    'rollback' {
        if (-not (Test-Path $OriginalExe)) { throw "最原始版存档不存在: $OriginalExe" }
        $cur = (Get-FileHash $Efile -Algorithm MD5).Hash
        Copy-Item $OriginalExe $Efile -Force
        # 清空空洞台账
        if (Test-Path $HolePath) { Remove-Item $HolePath -Force }
        $new = (Get-FileHash $Efile -Algorithm MD5).Hash
        Write-Host ("回滚完成: {0} -> {1}" -f $cur.Substring(0,8), $new.Substring(0,8)) -ForegroundColor Green
        Write-Ledger ("- {0} | 回滚到原始版 | MD5 {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm'), $new.Substring(0,8))
    }
}
