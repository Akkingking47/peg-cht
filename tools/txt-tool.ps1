<#
  OpenGen 汉化文本工具
  --------------------
  用途：编码校验 / 编码转换 / 行结构比对

  用法示例：
    # 1. 检查翻译文件是否符合引擎要求，并与模板逐行比对
    .\txt-tool.ps1 -Action check -File D:\OpenPG2\OPENGUI\strings-zh.txt `
                   -Template D:\OpenPG2\OPENTXT_SAMPLE\strings-en-template.txt

    # 2. UTF-8 工作稿 -> GBK 出稿（游戏实际读取的编码）
    .\txt-tool.ps1 -Action to-gbk -File .\work\strings-zh.utf8.txt -Out .\out\strings-zh.txt

    # 3. GBK 原文 -> UTF-8（便于翻译与 git diff）
    .\txt-tool.ps1 -Action to-utf8 -File D:\OpenPG2\OPENGUI\strings-de.txt -Out .\work\strings-de.utf8.txt

  说明：
    - 引擎以 MultiByteToWideChar(CP_ACP) 解码文本，本机 ACP=936，故出稿编码必须是 GBK(936) 且无 BOM。
    - 不支持 .ttc 字体；与文本编码无关，仅提示。
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('check', 'to-gbk', 'to-utf8')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [string]$File,

    [string]$Out,

    [string]$Template
)

$ErrorActionPreference = 'Stop'

# Windows PowerShell 5.1 没有 Encoding.Latin1，统一用 28591
$Enc28591 = [Text.Encoding]::GetEncoding(28591)
$EncGbk = [Text.Encoding]::GetEncoding(936)
$EncGbkStrict = [Text.Encoding]::GetEncoding(936,
    [Text.EncoderFallback]::ExceptionFallback,
    [Text.DecoderFallback]::ExceptionFallback)
$EncUtf8Strict = New-Object Text.UTF8Encoding($false, $true)

function Read-RawLines {
    param([string]$Path)
    $bytes = [IO.File]::ReadAllBytes($Path)
    $text = $Enc28591.GetString($bytes)
    # 统一按 CRLF 与 LF 切分，保留空行
    return ,@($text -split "`r`n|`n")
}

function Get-FileFacts {
    param([string]$Path)
    $bytes = [IO.File]::ReadAllBytes($Path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $cr = @($bytes | Where-Object { $_ -eq 13 }).Count
    $lf = @($bytes | Where-Object { $_ -eq 10 }).Count
    $eol = if ($cr -eq 0) { 'LF (Unix)' } elseif ($cr -eq $lf) { 'CRLF (Windows) OK' } else { "MIXED (CR=$cr LF=$lf) 需修正" }

    $validUtf8 = $true
    try { [void]$EncUtf8Strict.GetString($bytes) } catch { $validUtf8 = $false }

    $validGbk = $true
    try { [void]$EncGbkStrict.GetString($bytes) } catch { $validGbk = $false }

    [pscustomobject]@{
        Bytes     = $bytes.Length
        Bom       = $hasBom
        Eol       = $eol
        ValidUtf8 = $validUtf8
        ValidGbk  = $validGbk
    }
}

switch ($Action) {

    'check' {
        if (-not (Test-Path $File)) { throw "文件不存在: $File" }
        $f = Get-FileFacts -Path $File

        Write-Host ''
        Write-Host '=== 文件事实 ===' -ForegroundColor Cyan
        Write-Host ("  文件        : {0}" -f (Resolve-Path $File))
        Write-Host ("  字节        : {0}" -f $f.Bytes)
        Write-Host ("  BOM         : {0}" -f $(if ($f.Bom) { '有 (UTF-8 BOM) — 需去除' } else { '无 — OK' }))
        Write-Host ("  行尾        : {0}" -f $f.Eol)
        Write-Host ("  严格UTF-8   : {0}" -f $f.ValidUtf8)
        Write-Host ("  严格GBK     : {0}" -f $f.ValidGbk)

        # 引擎期望：无 BOM + CRLF + 合法 GBK
        $ok = (-not $f.Bom) -and $f.ValidGbk -and ($f.Eol -like 'CRLF*')
        if ($ok) {
            Write-Host '  引擎兼容性  : OK (无BOM / CRLF / 合法GBK)' -ForegroundColor Green
        }
        else {
            Write-Host '  引擎兼容性  : 不合格，见上方各项' -ForegroundColor Yellow
        }

        if ($Template) {
            if (-not (Test-Path $Template)) { throw "模板不存在: $Template" }
            Write-Host ''
            Write-Host '=== 与模板逐行比对 ===' -ForegroundColor Cyan

            $aLines = Read-RawLines -Path $Template
            $bLines = Read-RawLines -Path $File
            Write-Host ("  模板行数    : {0}" -f $aLines.Count)
            Write-Host ("  译文行数    : {0}" -f $bLines.Count)

            $n = [Math]::Max($aLines.Count, $bLines.Count)
            $diffs = New-Object System.Collections.Generic.List[string]

            for ($i = 0; $i -lt $n; $i++) {
                $a = if ($i -lt $aLines.Count) { $aLines[$i] } else { '<缺失>' }
                $b = if ($i -lt $bLines.Count) { $bLines[$i] } else { '<缺失>' }

                $aIsComment = $a.TrimStart().StartsWith('*')
                $bIsComment = $b.TrimStart().StartsWith('*')
                $aIsBlank = [string]::IsNullOrWhiteSpace($a)
                $bIsBlank = [string]::IsNullOrWhiteSpace($b)

                # 结构规则：注释行对注释行，空行对空行，内容行对内容行
                $structOk = (($aIsComment -and $bIsComment) -or ($aIsBlank -and $bIsBlank) -or
                             (-not $aIsComment -and -not $aIsBlank -and -not $bIsComment -and -not $bIsBlank))
                if (-not $structOk) {
                    $diffs.Add(("  行 {0,4}: 结构错位 模板='{1}'  译文='{2}'" -f ($i + 1), $a, $b))
                }
            }

            if ($diffs.Count -eq 0) {
                Write-Host '  行结构      : 完全对应 OK' -ForegroundColor Green
            }
            else {
                Write-Host ("  行结构      : {0} 处错位（必须修正，否则 UI 串位）" -f $diffs.Count) -ForegroundColor Red
                $diffs | Select-Object -First 40 | ForEach-Object { Write-Host $_ -ForegroundColor Red }
                if ($diffs.Count -gt 40) { Write-Host ("  ... 另有 {0} 处" -f ($diffs.Count - 40)) }
            }

            # 译文长度提示
            Write-Host ''
            Write-Host '=== 译文长度抽样（超长可能被截断） ===' -ForegroundColor Cyan
            $long = @()
            for ($i = 0; $i -lt [Math]::Min($aLines.Count, $bLines.Count); $i++) {
                $a = $aLines[$i]; $b = $bLines[$i]
                if ($a -and -not $a.TrimStart().StartsWith('*') -and $a.Trim()) {
                    if ($b.Length -gt ($a.Length * 1.5) -and $b.Length -gt 8) {
                        $long += ("  行 {0,4}: EN({1}) -> ZH({2})  '{3}' => '{4}'" -f ($i + 1), $a.Length, $b.Length, $a, $b)
                    }
                }
            }
            if ($long.Count -eq 0) { Write-Host '  无显著超长项' -ForegroundColor Green }
            else {
                $long | Select-Object -First 25 | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
                if ($long.Count -gt 25) { Write-Host ("  ... 另有 {0} 处" -f ($long.Count - 25)) }
            }
        }
        else {
            Write-Host ''
            Write-Host '（未提供 -Template，已跳过行结构比对）' -ForegroundColor DarkGray
        }
        Write-Host ''
    }

    'to-gbk' {
        if (-not (Test-Path $File)) { throw "文件不存在: $File" }
        if (-not $Out) { throw 'to-gbk 需要 -Out 指定输出路径' }

        $bytes = [IO.File]::ReadAllBytes($File)
        # 支持带 BOM 的 UTF-8 工作稿
        $text = $EncUtf8Strict.GetString($bytes)
        $text = $text -replace "^\uFEFF", ''

        # 统一为 CRLF
        $text = ($text -replace "`r`n", "`n") -replace "`n", "`r`n"

        # 校验所有字符都能映射到 GBK
        try { [void]$EncGbkStrict.GetBytes($text) }
        catch {
            Write-Host '错误：存在无法用 GBK 表示的字符（如生僻字、emoji、全角例外符号）：' -ForegroundColor Red
            foreach ($ch in $text.ToCharArray() | Select-Object -Unique) {
                try { [void]$EncGbkStrict.GetBytes([string]$ch) }
                catch { $cp = 'U+{0:X4}' -f [int][char]$ch; Write-Host ("  '{0}'  {1}" -f $ch, $cp) -ForegroundColor Red }
            }
            throw '转换中止，未写出文件'
        }

        $outDir = Split-Path -Parent $Out
        if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

        # 无 BOM 写出
        [IO.File]::WriteAllBytes($Out, $EncGbk.GetBytes($text))
        Write-Host ("已写出 GBK(936) 无BOM CRLF: {0}  ({1} 字节)" -f (Resolve-Path $Out), (Get-Item $Out).Length) -ForegroundColor Green
    }

    'to-utf8' {
        if (-not (Test-Path $File)) { throw "文件不存在: $File" }
        if (-not $Out) { throw 'to-utf8 需要 -Out 指定输出路径' }

        $bytes = [IO.File]::ReadAllBytes($File)
        $text = $EncGbk.GetString($bytes)
        $text = ($text -replace "`r`n", "`n") -replace "`n", "`r`n"

        $outDir = Split-Path -Parent $Out
        if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

        $utf8NoBom = New-Object Text.UTF8Encoding($false)
        [IO.File]::WriteAllBytes($Out, $utf8NoBom.GetBytes($text))
        Write-Host ("已写出 UTF-8 无BOM CRLF: {0}  ({1} 字节)" -f (Resolve-Path $Out), (Get-Item $Out).Length) -ForegroundColor Green
    }
}
