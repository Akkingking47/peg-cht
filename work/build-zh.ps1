<#
  从 strings-en-template.txt + map*.tsv 生成 strings-zh.txt
  ------------------------------------------------
  设计原则：只按行号替换指定行，其余行原样保留。
  这样注释行、空行、尾随空格、TAB 全部自动保持，结构零风险。

  map 文件格式（UTF-8）：  行号|译文
    例：  22|开阔地

  用法：
    .\build-zh.ps1            # 生成到 work 目录并校验
    .\build-zh.ps1 -Deploy    # 同时部署到游戏 OPENGUI 目录
#>
[CmdletBinding()]
param([switch]$Deploy)

$ErrorActionPreference = 'Stop'

$Tpl      = 'D:\OpenPG2\OPENTXT_SAMPLE\strings-en-template.txt'
$Work     = 'D:\DSH\军事游戏汉化\work'
$OutUtf8  = Join-Path $Work 'strings-zh.utf8.txt'
$OutGbk   = Join-Path $Work 'strings-zh.txt'
$GamePath = 'D:\OpenPG2\OPENGUI\strings-zh.txt'
$Report   = Join-Path $Work '未翻译清单.txt'

$enc28591 = [Text.Encoding]::GetEncoding(28591)
$encGbk   = [Text.Encoding]::GetEncoding(936)
$utf8No   = New-Object Text.UTF8Encoding($false)
$gbkStrict = [Text.Encoding]::GetEncoding(936, [Text.EncoderFallback]::ExceptionFallback, [Text.DecoderFallback]::ExceptionFallback)

# ---------- 1. 读模板 ----------
$raw   = $enc28591.GetString([IO.File]::ReadAllBytes($Tpl))
$lines = $raw -split "`r`n"
$total = $lines.Count
Write-Host ("模板行数(含末尾空元素) = {0}" -f $total) -ForegroundColor Cyan

# ---------- 2. 读映射 ----------
$map    = @{}
$errors = New-Object System.Collections.Generic.List[string]
foreach ($i in 1..4) {
    $f = Join-Path $Work "map$i.tsv"
    if (-not (Test-Path $f)) { Write-Host "  缺少 map$i.tsv，跳过" -ForegroundColor Yellow; continue }
    $mr = $utf8No.GetString([IO.File]::ReadAllBytes($f))
    $n = 0
    foreach ($l in ($mr -split "\r?\n")) {
        if ($l.Length -eq 0 -or $l.Trim().Length -eq 0) { continue }
        $p = $l.Split('|', 2)
        if ($p.Count -ne 2) { $errors.Add("map$i 格式错误(缺少分隔符): $l"); continue }
        $no = 0
        if (-not [int]::TryParse($p[0].Trim(), [ref]$no)) { $errors.Add("map$i 行号无效: $l"); continue }
        if ($map.ContainsKey($no)) { $errors.Add("行号重复出现: $no"); continue }
        $map[$no] = $p[1]
        $n++
    }
    Write-Host ("  map$i.tsv 读入 {0} 条" -f $n)
}
Write-Host ("映射总数 = {0}" -f $map.Count) -ForegroundColor Cyan

# ---------- 3. 逐行替换 + 校验 ----------
$applied = 0
foreach ($no in ($map.Keys | Sort-Object)) {
    if ($no -lt 1 -or $no -gt $total) { $errors.Add("行号越界: $no"); continue }
    $cur = $lines[$no - 1]
    if ([string]::IsNullOrWhiteSpace($cur)) { $errors.Add("行 $no 是空行，不应翻译"); continue }
    if ($cur.TrimStart().StartsWith('*'))   { $errors.Add("行 $no 是注释行，不应翻译"); continue }
    if ($cur -match '[\u4e00-\u9fff]')      { $errors.Add("行 $no 原文已含中文，已跳过（防止重复替换）"); continue }
    $lines[$no - 1] = $map[$no]
    $applied++
}
Write-Host ("实际替换 = {0} 行" -f $applied) -ForegroundColor Green

# ---------- 4. 统计未翻译的内容行 ----------
$untrans = New-Object System.Collections.Generic.List[string]
for ($i = 0; $i -lt $total; $i++) {
    $l = $lines[$i]
    if ([string]::IsNullOrWhiteSpace($l)) { continue }
    if ($l.TrimStart().StartsWith('*'))   { continue }
    if ($l -match '[\u4e00-\u9fff]')      { continue }
    # 纯符号/格式串（无字母）视为无需翻译
    if ($l -notmatch '[A-Za-z]')          { continue }
    $untrans.Add(("{0}|{1}" -f ($i + 1), $l))
}

$header = @(
    "# 以下内容行仍为英文（或有意保留）。请逐条确认是否需要翻译。",
    "# 格式: 行号|原文",
    "# 生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "# 未翻译条数: $($untrans.Count)",
    ""
)
[IO.File]::WriteAllText($Report, ($header + $untrans) -join "`r`n", $utf8No)
Write-Host ("仍未翻译的内容行 = {0} 条（清单: {1}）" -f $untrans.Count, $Report) -ForegroundColor Yellow

# ---------- 5. 写文件 ----------
$text = $lines -join "`r`n"

try { [void]$gbkStrict.GetBytes($text) }
catch {
    Write-Host '错误：存在无法用 GBK 表示的字符，未写出文件：' -ForegroundColor Red
    foreach ($ch in $text.ToCharArray() | Select-Object -Unique) {
        try { [void]$gbkStrict.GetBytes([string]$ch) }
        catch { Write-Host ("  '{0}'  U+{1:X4}" -f $ch, [int][char]$ch) -ForegroundColor Red }
    }
    throw '中止'
}

[IO.File]::WriteAllBytes($OutUtf8, $utf8No.GetBytes($text))
[IO.File]::WriteAllBytes($OutGbk, $encGbk.GetBytes($text))
Write-Host ("已生成 UTF-8 工作稿: {0} ({1} 字节)" -f $OutUtf8, (Get-Item $OutUtf8).Length) -ForegroundColor Green
Write-Host ("已生成 GBK  出稿  : {0} ({1} 字节)" -f $OutGbk, (Get-Item $OutGbk).Length) -ForegroundColor Green

# ---------- 6. 结构自检 ----------
$chk = $enc28591.GetString([IO.File]::ReadAllBytes($OutGbk)) -split "`r`n"
if ($chk.Count -ne $total) { $errors.Add("行数不一致: 模板 $total vs 输出 $($chk.Count)") }
else {
    $mis = 0
    for ($i = 0; $i -lt $total; $i++) {
        $a = $lines[$i]; $b = $chk[$i]
        $aC = $a.TrimStart().StartsWith('*'); $bC = $b.TrimStart().StartsWith('*')
        $aB = [string]::IsNullOrWhiteSpace($a); $bB = [string]::IsNullOrWhiteSpace($b)
        $ok = (($aC -and $bC) -or ($aB -and $bB) -or ((-not $aC -and -not $aB -and -not $bC -and -not $bB)))
        if (-not $ok) { $mis++ }
    }
    if ($mis -eq 0) { Write-Host '结构自检: 注释/空行/内容行逐行对应 OK' -ForegroundColor Green }
    else { $errors.Add("结构自检发现 $mis 处错位") }
}

# ---------- 7. 部署 ----------
if ($Deploy) {
    if (-not (Test-Path (Split-Path $GamePath))) { throw "游戏 OPENGUI 目录不存在" }
    if (Test-Path $GamePath) { Copy-Item $GamePath "$GamePath.bak" -Force }
    Copy-Item $OutGbk $GamePath -Force
    Write-Host ("已部署到游戏: {0}" -f $GamePath) -ForegroundColor Green
}

# ---------- 8. 错误汇总 ----------
Write-Host ''
if ($errors.Count -gt 0) {
    Write-Host ("发现 {0} 个问题：" -f $errors.Count) -ForegroundColor Red
    $errors | Select-Object -First 30 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
}
else {
    Write-Host '全部校验通过，无问题。' -ForegroundColor Green
}
Write-Host ''
