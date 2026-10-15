<#
  rtdialog-apply-all.ps1 —— 批量写回对话框译文（性能优化版）
  =====================================================================
  与 rtdialog-tool.ps1 -Action apply 的区别：
    原脚本对每条译文都重新解析整个对话框，279 条会超时。
    本脚本先按对话框 ID 分组，每个对话框只解析一次，最后一次性写盘。

  输入 TSV 格式：对话框ID <TAB> 英文原文 <TAB> 中文译文
  约束：中文译文长度 <= 英文原文长度（UTF-16 等长写回，剩余填空格 + NUL）
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Translations,
    [string]$Efile = 'D:\OpenPG2\OpenGen.exe'
)

$ErrorActionPreference = 'Stop'

$RsrcFO  = 0x5BEC00
$RsrcRVA = 0xEAB000
$U16     = [Text.Encoding]::Unicode

# ---------- 解析器（与 rtdialog-tool.ps1 相同逻辑） ----------
function Get-Dialogs {
    param([byte[]]$B)
    $list = @()
    $named = [BitConverter]::ToInt16($B, $RsrcFO + 12)
    $idc   = [BitConverter]::ToInt16($B, $RsrcFO + 14)
    $ent   = $RsrcFO + 16
    for ($i = 0; $i -lt ($named + $idc); $i++) {
        $typeId = [BitConverter]::ToInt32($B, $ent + $i * 8) -band 0xFFFF
        $off    = [BitConverter]::ToInt32($B, $ent + $i * 8 + 4)
        if ($typeId -ne 5) { continue }
        $sub = $RsrcFO + ($off -band 0x7FFFFFFF)
        $n2 = [BitConverter]::ToInt16($B, $sub + 12); $i2 = [BitConverter]::ToInt16($B, $sub + 14)
        for ($j = 0; $j -lt ($n2 + $i2); $j++) {
            $blkId = [BitConverter]::ToInt32($B, $sub + 16 + $j * 8) -band 0xFFFF
            $soff  = [BitConverter]::ToInt32($B, $sub + 16 + $j * 8 + 4)
            $d = $RsrcFO + ($soff -band 0x7FFFFFFF)
            $n3 = [BitConverter]::ToInt16($B, $d + 12); $i3 = [BitConverter]::ToInt16($B, $d + 14)
            for ($k = 0; $k -lt ($n3 + $i3); $k++) {
                $dataOff = [BitConverter]::ToInt32($B, $d + 16 + $k * 8 + 4)
                $do = $RsrcFO + $dataOff
                $rva  = [BitConverter]::ToInt32($B, $do)
                $size = [BitConverter]::ToInt32($B, $do + 4)
                $fo   = $RsrcFO + ($rva - $RsrcRVA)
                $list += [pscustomobject]@{ Id = $blkId; FO = $fo; Size = $size }
            }
        }
    }
    return $list
}

function Read-Sz {
    param([byte[]]$B, [int]$P)
    $s = ''
    while ($true) {
        $c = [BitConverter]::ToUInt16($B, $P)
        if ($c -eq 0) { break }
        $s += [char]$c; $P += 2
        if ($s.Length -gt 4000) { break }
    }
    return @{ Text = $s; Next = $P + 2 }
}

# 只取「控件标题」的位置（用于替换），返回 tab: TextFO -> 文本
function Get-TextSlots {
    param([byte[]]$B, [int]$FO, [int]$Size)
    $p = $FO
    $sig = [BitConverter]::ToUInt16($B, $p + 2)
    if ($sig -ne 0xFFFF) { return @() }
    $p += 4
    $p += 4                                  # helpID
    $p += 4                                  # exStyle
    $p += 4                                  # style
    $cdit = [BitConverter]::ToUInt16($B, $p); $p += 2
    $p += 8                                  # x,y,cx,cy
    # 菜单
    $m = [BitConverter]::ToUInt16($B, $p)
    if ($m -eq 0) { $p += 2 } elseif ($m -eq 0xFFFF) { $p += 4 } else { $r = Read-Sz -B $B -P $p; $p = $r.Next }
    # 类
    $c = [BitConverter]::ToUInt16($B, $p)
    if ($c -eq 0) { $p += 2 } elseif ($c -eq 0xFFFF) { $p += 4 } else { $r = Read-Sz -B $B -P $p; $p = $r.Next }
    # 标题
    $r = Read-Sz -B $B -P $p; $p = $r.Next
    if (($p - $FO) % 4 -ne 0) { $p += (4 - (($p - $FO) % 4)) % 4 }
    $slots = @()
    for ($i = 0; $i -lt $cdit; $i++) {
        if ($p -ge $FO + $Size) { break }
        $p += 4 + 4 + 4                          # helpID, exStyle, style
        $p += 8                                  # x,y,cx,cy
        $p += 4                                  # ctrl id
        $ck = [BitConverter]::ToUInt16($B, $p)
        if ($ck -eq 0xFFFF) { $p += 4 } else { $r = Read-Sz -B $B -P $p; $p = $r.Next }
        $tFO = $p
        $tk = [BitConverter]::ToUInt16($B, $p)
        $txt = ''
        if ($tk -eq 0xFFFF) { $p += 4 }
        else { $r = Read-Sz -B $B -P $p; $txt = $r.Text; $p = $r.Next }
        $extra = [BitConverter]::ToUInt16($B, $p); $p += 2
        if ($extra -gt 0) { $p += $extra }
        if (($p - $FO) % 4 -ne 0) { $p += (4 - (($p - $FO) % 4)) % 4 }
        if ($tk -ne 0xFFFF -and $txt.Length -gt 0) { $slots += [pscustomobject]@{ FO = $tFO; Text = $txt } }
    }
    return $slots
}

# ---------- 主流程 ----------
$u8 = New-Object Text.UTF8Encoding($false)
$rows = @($u8.GetString([IO.File]::ReadAllBytes($Translations)) -split "\r?\n" | Where-Object { $_.Trim() })
Write-Host ("读入译文 {0} 条" -f $rows.Count)

$B = [IO.File]::ReadAllBytes($Efile)
$orig = $B.Clone()
$dialogs = Get-Dialogs -B $B
Write-Host ("exe 内对话框 {0} 个" -f $dialogs.Count)

# 按对话框分组
$byId = @{}
foreach ($r in $rows) {
    $p = $r.Split("`t")
    if ($p.Count -lt 3) { continue }
    $id = [int]$p[0]
    if (-not $byId.ContainsKey($id)) { $byId[$id] = @() }
    $byId[$id] += ,@($p[1], $p[2])
}

$applied = 0; $errs = @()
foreach ($id in ($byId.Keys | Sort-Object)) {
    $d = $dialogs | Where-Object { $_.Id -eq $id } | Select-Object -First 1
    if (-not $d) { $errs += "找不到对话框 ID=$id"; continue }
    # 只解析一次
    $slots = Get-TextSlots -B $B -FO $d.FO -Size $d.Size
    foreach ($pair in $byId[$id]) {
        $en = $pair[0]; $zh = $pair[1]
        $slot = $slots | Where-Object { $_.Text -eq $en } | Select-Object -First 1
        if (-not $slot) { $errs += "ID=$id 中找不到原文: $en"; continue }
        if ($zh.Length -gt $en.Length) { $errs += "译文过长 ID=${id} : $en"; continue }
        # 等长写入：译文 + 空格填充到原文长度，然后 NUL
        $padded = $zh.PadRight($en.Length, ' ')
        $nb = $U16.GetBytes($padded)
        [Array]::Copy($nb, 0, $B, $slot.FO, $nb.Length)
        $B[$slot.FO + $nb.Length] = 0
        $B[$slot.FO + $nb.Length + 1] = 0
        $applied++
    }
    Write-Host ("  ID={0,-6} 已处理 {1} 条" -f $id, $byId[$id].Count) -ForegroundColor DarkGray
}

if ($B.Length -ne $orig.Length) { throw '文件大小变了，拒绝写入' }
$tmp = "$env:TEMP\OpenGen.dlgall.exe"
[IO.File]::WriteAllBytes($tmp, $B)
Copy-Item $tmp $Efile -Force

$diffs = 0; for ($i = 0; $i -lt $B.Length; $i++) { if ($B[$i] -ne $orig[$i]) { $diffs++ } }
Write-Host ''
Write-Host ("应用 {0} 条；改动 {1} 字节" -f $applied, $diffs) -ForegroundColor Green
Write-Host ("新 MD5 = {0}" -f (Get-FileHash $Efile -Algorithm MD5).Hash) -ForegroundColor Green
if ($errs.Count -gt 0) {
    Write-Host ("{0} 条未处理:" -f $errs.Count) -ForegroundColor Yellow
    $errs | Select-Object -First 20 | ForEach-Object { Write-Host ('  ' + $_) -ForegroundColor Yellow }
}
