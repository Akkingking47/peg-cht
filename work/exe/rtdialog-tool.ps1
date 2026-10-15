<#
  rtdialog-tool.ps1 —— OpenGen.exe RT_DIALOG 对话框模板汉化工具
  =====================================================================
  为什么用这个而不是改 .text：
    战役浏览器的文字不是代码里的字符串，而是【RT_DIALOG 对话框模板】
    里的 UTF-16 静态文本 / 按钮标题。UTF-16 下中文与英文同为 2 字节/字符，
    中文信息密度更高，因此多数译文更短 → 可【等长替换 + 尾部空格填充】，
    后续控件偏移完全不变，比改 push 地址安全得多。

  用法：
    # 列出所有对话框资源
    .\rtdialog-tool.ps1 -Action list

    # 解析某个对话框，列出全部控件文本（含资源ID、偏移、是否可译）
    .\rtdialog-tool.ps1 -Action dump -DialogId 483

    # 应用翻译（translations.tsv 每行 `对话框ID<TAB>原文<TAB>译文`）
    .\rtdialog-tool.ps1 -Action apply -Translations .\dlg.tsv

  铁律：
    - 译文【字符数】必须 <= 原文，不足处补空格（保住后续控件偏移）
    - 资源ID（IDBUT_OK / IDBUT_CANCEL / SysListView32 等）绝不翻译
    - 只写资源区，不改字节总数、不改文件大小
#>
[CmdletBinding()]
param(
    [ValidateSet('list', 'dump', 'apply', 'verify', 'rollback')]
    [string]$Action = 'list',
    [int]$DialogId = 0,
    [string]$Translations,
    [string]$Efile = 'D:\OpenPG2\OpenGen.exe',
    [string]$OriginalExe = 'D:\DSH\军事游戏汉化\backup\OpenGen.exe.original'
)

$ErrorActionPreference = 'Stop'

# ---- PE / 资源常量（本版本）----
$ImageBase = 0x400000
$RsrcFO    = 0x5BEC00
$RsrcRVA   = 0xEAB000
$U16       = [Text.Encoding]::Unicode

function Read-Bytes { param([string]$P) return [IO.File]::ReadAllBytes($P) }

function Get-Dialogs {
    param([byte[]]$B)
    $list = @()
    $named = [BitConverter]::ToInt16($B, $RsrcFO + 12)
    $idc   = [BitConverter]::ToInt16($B, $RsrcFO + 14)
    $ent   = $RsrcFO + 16
    for ($i = 0; $i -lt ($named + $idc); $i++) {
        $typeId = [BitConverter]::ToInt32($B, $ent + $i * 8) -band 0xFFFF
        $off    = [BitConverter]::ToInt32($B, $ent + $i * 8 + 4)
        if ($typeId -ne 5) { continue }                      # 5 = RT_DIALOG
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

function Read-Sz {          # 读 NUL 结尾的 UTF-16 串
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

function Parse-Dialog {
    param([byte[]]$B, [int]$FO, [int]$Size)
    $p = $FO
    $dlgVer = [BitConverter]::ToUInt16($B, $p); $sig = [BitConverter]::ToUInt16($B, $p + 2)
    if ($sig -ne 0xFFFF) { throw "不是 DLGTEMPLATEEX (sig=0x$('{0:X4}' -f $sig))" }
    $p += 4
    $helpId = [BitConverter]::ToInt32($B, $p); $p += 4
    $exStyle = [BitConverter]::ToInt32($B, $p); $p += 4
    $style = [BitConverter]::ToInt32($B, $p); $p += 4
    $cdit = [BitConverter]::ToUInt16($B, $p); $p += 2
    $x = [BitConverter]::ToInt16($B, $p); $y = [BitConverter]::ToInt16($B, $p + 2)
    $cx = [BitConverter]::ToInt16($B, $p + 4); $cy = [BitConverter]::ToInt16($B, $p + 6); $p += 8
    # 菜单
    $m = [BitConverter]::ToUInt16($B, $p)
    if ($m -eq 0) { $p += 2 }
    elseif ($m -eq 0xFFFF) { $p += 4 }
    else { $r = Read-Sz -B $B -P $p; $p = $r.Next }
    # 窗口类
    $c = [BitConverter]::ToUInt16($B, $p)
    if ($c -eq 0) { $p += 2 }
    elseif ($c -eq 0xFFFF) { $p += 4 }
    else { $r = Read-Sz -B $B -P $p; $p = $r.Next }
    # 标题
    $r = Read-Sz -B $B -P $p; $title = $r.Text; $titleFO = $p; $p = $r.Next
    if (($p - $FO) % 4 -ne 0) { $p += (4 - (($p - $FO) % 4)) % 4 }
    $items = @()
    for ($i = 0; $i -lt $cdit; $i++) {
        if ($p -ge $FO + $Size) { break }
        $help = [BitConverter]::ToInt32($B, $p); $p += 4
        $cex  = [BitConverter]::ToInt32($B, $p); $p += 4
        $cst  = [BitConverter]::ToInt32($B, $p); $p += 4
        $ix = [BitConverter]::ToInt16($B, $p); $iy = [BitConverter]::ToInt16($B, $p + 2)
        $icx = [BitConverter]::ToInt16($B, $p + 4); $icy = [BitConverter]::ToInt16($B, $p + 6); $p += 8
        $id = [BitConverter]::ToInt32($B, $p); $p += 4
        # 类
        $ck = [BitConverter]::ToUInt16($B, $p)
        $cls = ''
        if ($ck -eq 0xFFFF) { $ord = [BitConverter]::ToUInt16($B, $p + 2); $cls = "ord:$('{0:X4}' -f $ord)"; $p += 4 }
        else { $r = Read-Sz -B $B -P $p; $cls = $r.Text; $p = $r.Next }
        # 标题
        $tFO = $p
        $tk = [BitConverter]::ToUInt16($B, $p)
        if ($tk -eq 0xFFFF) { $ord = [BitConverter]::ToUInt16($B, $p + 2); $txt = "<ord:$('{0:X4}' -f $ord)>"; $p += 4 }
        else { $r = Read-Sz -B $B -P $p; $txt = $r.Text; $p = $r.Next }
        $extra = [BitConverter]::ToUInt16($B, $p); $p += 2
        if ($extra -gt 0) { $p += $extra }
        if (($p - $FO) % 4 -ne 0) { $p += (4 - (($p - $FO) % 4)) % 4 }
        $items += [pscustomobject]@{
            Idx = $i; Help = $help; Style = ('0x{0:X8}' -f $cst); X = $ix; Y = $iy
            Cx = $icx; Cy = $icy; CtrlId = $id; Class = $cls
            Text = $txt; TextFO = $tFO; TextChars = $txt.Length
        }
    }
    return [pscustomobject]@{ Ver = $dlgVer; Style = ('0x{0:X8}' -f $style); Cdit = $cdit
        X = $x; Y = $y; Cx = $cx; Cy = $cy; Title = $title; TitleFO = $titleFO; Items = $items }
}

# 资源ID / 类名 —— 绝不翻译
$IdLike = @('^ID[A-Z_0-9]+$', '^Sys[A-Za-z0-9]+$', '^Button$', '^Static$', '^Edit$', '^ComboBox$', '^msctls_', '^#\d+$')
function Test-IdLike { param([string]$T)
    if ([string]::IsNullOrWhiteSpace($T)) { return $true }
    foreach ($p in $IdLike) { if ($T -match $p) { return $true } }
    return $false
}

$B = Read-Bytes $Efile

switch ($Action) {

    'list' {
        $dlgs = Get-Dialogs -B $B
        Write-Host ("RT_DIALOG 资源 {0} 个:" -f $dlgs.Count)
        foreach ($d in ($dlgs | Sort-Object Id)) { '  ID={0,-6} FO=0x{1:X6}  大小={2,5}' -f $d.Id, $d.FO, $d.Size }
    }

    'dump' {
        if ($DialogId -le 0) { throw 'dump 需要 -DialogId' }
        $dlgs = Get-Dialogs -B $B
        $d = $dlgs | Where-Object { $_.Id -eq $DialogId } | Select-Object -First 1
        if (-not $d) { throw "未找到对话框 ID=$DialogId" }
        $parsed = Parse-Dialog -B $B -FO $d.FO -Size $d.Size
        Write-Host ("=== 对话框 ID={0}  FO=0x{1:X6}  大小={2}  控件数={3} ===" -f $d.Id, $d.FO, $d.Size, $parsed.Cdit)
        Write-Host ("  标题: [{0}]" -f $parsed.Title)
        Write-Host ''
        Write-Host ('{0,3} {1,-12} {2,-8} {3,6} {4,-6} {5}' -f '#', '类', '控件ID', 'TextFO', '可译', '文本')
        Write-Host ('-' * 100)
        foreach ($it in $parsed.Items) {
            $ok = -not (Test-IdLike $it.Text)
            '  {0,2} {1,-12} {2,-8} 0x{3:X6} {4,-6} [{5}]' -f $it.Idx, $it.Class, $it.CtrlId, $it.TextFO, $(if ($ok) { '是' } else { '否' }), $it.Text
        }
    }

    'apply' {
        if (-not $Translations) { throw 'apply 需要 -Translations <tsv>' }
        if (-not (Test-Path $Translations)) { throw "文件不存在: $Translations" }
        $md5 = (Get-FileHash $Efile -Algorithm MD5).Hash
        Write-Host ("当前 exe MD5 = {0}" -f $md5)
        $b2 = $B.Clone()
        $dlgs = Get-Dialogs -B $b2
        $applied = 0; $errs = @()
        foreach ($line in (Get-Content $Translations -Encoding UTF8)) {
            if (-not $line.Trim() -or $line.StartsWith('#')) { continue }
            $p = $line.Split("`t")
            if ($p.Count -lt 3) { $errs += "格式错误(需 对话框ID<TAB>原文<TAB>译文): $line"; continue }
            $did = 0; if (-not [int]::TryParse($p[0].Trim(), [ref]$did)) { $errs += "对话框ID无效: $line"; continue }
            $src = $p[1]; $zh = $p[2]
            $d = $dlgs | Where-Object { $_.Id -eq $did } | Select-Object -First 1
            if (-not $d) { $errs += "找不到对话框 ID=$did"; continue }
            $parsed = Parse-Dialog -B $b2 -FO $d.FO -Size $d.Size
            $hit = $parsed.Items | Where-Object { $_.Text -eq $src } | Select-Object -First 1
            if (-not $hit) { $errs += "对话框 $did 中找不到原文: $src"; continue }
            if (Test-IdLike $src) { $errs += "疑似资源ID，拒绝: $src"; continue }
            if ($zh.Length -gt $src.Length) {
                $errs += "译文过长（原 {0} 字符 / 译 {1} 字符，需 <=）：{2}" -f $src.Length, $zh.Length, $src
                continue
            }
            # 等长写入：译文 + 尾部空格填充 + NUL
            $padded = $zh.PadRight($src.Length, ' ')
            $bytes = $U16.GetBytes($padded)
            [Array]::Copy($bytes, 0, $b2, $hit.TextFO, $bytes.Length)
            $b2[$hit.TextFO + $bytes.Length] = 0
            $b2[$hit.TextFO + $bytes.Length + 1] = 0
            $applied++
            Write-Host ("  ✅ [ID={0}] {1,-46} -> {2}" -f $did, $src, $zh) -ForegroundColor Green
        }
        if ($b2.Length -ne $B.Length) { throw '文件大小变了，拒绝写入' }
        $tmp = "$env:TEMP\OpenGen.dlg.exe"
        [IO.File]::WriteAllBytes($tmp, $b2)
        Copy-Item $tmp $Efile -Force
        Write-Host ''
        Write-Host ("应用 {0} 条；新 MD5 = {1}" -f $applied, (Get-FileHash $Efile -Algorithm MD5).Hash) -ForegroundColor Green
        if ($errs.Count -gt 0) { Write-Host ("{0} 条未处理:" -f $errs.Count) -ForegroundColor Yellow; $errs | ForEach-Object { Write-Host ('  ' + $_) -ForegroundColor Yellow } }
    }

    'verify' {
        $dlgs = Get-Dialogs -B $B
        Write-Host ("RT_DIALOG {0} 个；文件大小 {1}" -f $dlgs.Count, $B.Length)
        $orig = Read-Bytes $OriginalExe
        $d = 0
        for ($i = 0; $i -lt $B.Length; $i++) { if ($B[$i] -ne $orig[$i]) { $d++ } }
        Write-Host ("与原始版差异 {0} 字节" -f $d)
    }

    'rollback' {
        Copy-Item $OriginalExe $Efile -Force
        Write-Host ("已回滚到原始版: {0}" -f (Get-FileHash $Efile -Algorithm MD5).Hash) -ForegroundColor Green
    }
}
