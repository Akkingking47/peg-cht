param(
  [string]$Work = 'D:\DSH\军事游戏汉化\work\xscn',
  [string]$Root = 'D:\OpenPG2',
  [string]$Efile = 'EFILE_OLGWW2',
  [string]$Out = 'D:\DSH\军事游戏汉化\work\xscn-all-map.tsv'
)
# 合并 25 个分片 + 迷你块 + 标题 → 规范化 → 为全部 .xscn 生成 5 列回写映射
$ErrorActionPreference = 'Stop'
$ENC = [Text.Encoding]::GetEncoding(1252)
$u8 = New-Object Text.UTF8Encoding($false)

function Norm([string]$s) {
  if ([string]::IsNullOrEmpty($s)) { return $s }
  # 方括号内「数字 + 编制名」补「第」
  $s = [regex]::Replace($s, '\[(\d+)\s*(集团军群|集团军|军|师|旅|营)\]', '[第$1$2]')
  # 英文序数后缀（仅当紧跟编制名时）
  $s = [regex]::Replace($s, '(\d+)(th|st|nd|rd)\s*(?=(团|旅|师|军|集团军|营|骑兵|炮兵团|步兵|联队|大队))', '第$1')
  $s = $s.Replace('[Korea]', '[朝鲜]')
  $s = $s.Replace('[Kwantung]', '[关东军]')
  $s = $s.Replace('Hikodan', '飞行团')
  $s = $s.Replace('Tokko', '特攻')
  return $s
}

# ---------- 1. 汇总所有分片 ----------
$tr = @{}
$conflict = 0
$files = @(Get-ChildItem $Work -Filter 'part-*.tsv' -File | Sort-Object Name)
$files += Get-Item (Join-Path $Work 'zh\part-*.tsv') -ErrorAction SilentlyContinue
foreach ($f in (Get-ChildItem (Join-Path $Work 'zh') -Filter 'part-*.tsv' -File | Sort-Object Name)) {
  foreach ($line in [IO.File]::ReadAllLines($f.FullName, [Text.Encoding]::UTF8)) {
    if ($line.Trim().Length -eq 0) { continue }
    $c = $line -split "`t"
    if ($c.Count -lt 2) { continue }
    $k = $c[0]; $v = $c[1]
    if ($tr.ContainsKey($k)) { if ($tr[$k] -ne $v) { $conflict++ } ; continue }
    $tr[$k] = $v
  }
}
Write-Host ("  分片文件 {0} 个，汇总唯一原文 {1} 条，内容冲突 {2} 条" -f (Get-ChildItem (Join-Path $Work 'zh') -Filter 'part-*.tsv' -File).Count, $tr.Count, $conflict)

# ---------- 1b. 补 PGForever 旧译表 ----------
$lk = Join-Path $Work 'pgf-lookup.tsv'
if (Test-Path -LiteralPath $lk) {
  $n = 0
  foreach ($line in [IO.File]::ReadAllLines($lk, [Text.Encoding]::UTF8)) {
    $c = $line -split "`t"
    if ($c.Count -lt 2) { continue }
    if (-not $tr.ContainsKey($c[0])) { $tr[$c[0]] = $c[1]; $n++ }
  }
  Write-Host ("  补充 PGForever 命中 {0} 条" -f $n)
}
# ---------- 2. 规范化 ----------
$norm = @{}
foreach ($k in $tr.Keys) { $norm[$k] = Norm $tr[$k] }

# ---------- 3. 为每个 .xscn 生成 5 列映射 ----------
$rows = New-Object System.Collections.ArrayList
$noTr = New-Object System.Collections.ArrayList
$scnDir = Join-Path (Join-Path $Root $Efile) 'SCENARIO'
foreach ($p in (Get-ChildItem $scnDir -Filter '*.xscn' -File | Sort-Object Name)) {
  $b = [IO.File]::ReadAllBytes($p.FullName)
  $st = -1
  for ($i = 0; $i -le $b.Length - 3; $i++) { if ($b[$i] -eq 0x3C -and $b[$i + 1] -eq 0x4E -and $b[$i + 2] -eq 0x3A) { $st = $i; break } }
  if ($st -lt 0) { continue }
  $g = $st; while ($g -lt $b.Length -and $b[$g] -ne 0x3E) { $g++ }
  $off = $g + 1
  # title
  $L = [int]$b[$off] + [int]$b[$off + 1] * 256
  $title = $ENC.GetString($b, $off + 2, $L); $off = $off + 2 + $L
  if ($norm.ContainsKey($title)) { [void]$rows.Add(("{0}`t-1`t0`t{1}`t{2}" -f $p.Name, $title, $norm[$title])) }
  else { [void]$noTr.Add(("TITLE`t{0}`t{1}" -f $p.Name, $title)) }
  # items
  $gi = 0
  while ($off + 2 -le $b.Length) {
    $cnt = [int]$b[$off] + [int]$b[$off + 1] * 256
    if ($cnt -le 0 -or $cnt -gt 4000) { break }
    $off += 2
    $good = $true
    for ($k = 0; $k -lt $cnt; $k++) {
      if ($off + 2 -gt $b.Length) { $good = $false; break }
      $L = [int]$b[$off] + [int]$b[$off + 1] * 256
      if ($L -le 0 -or ($off + 2 + $L) -gt $b.Length) { $good = $false; break }
      $s = $ENC.GetString($b, $off + 2, $L); $off = $off + 2 + $L
      if ($norm.ContainsKey($s)) { [void]$rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}" -f $p.Name, $gi, $k, $s, $norm[$s])) }
      else { [void]$noTr.Add(("{0}`t{1}`t{2}`t{3}" -f $p.Name, $gi, $k, $s)) }
    }
    if (-not $good) { break }
    $gi++; if ($gi -gt 64) { break }
  }
}
[IO.File]::WriteAllLines($Out, $rows, $u8)
Write-Host ("  已生成映射 {0} 行 -> {1}" -f $rows.Count, $Out)
Write-Host ("  未命中译文的串 {0} 条" -f $noTr.Count)
if ($noTr.Count -gt 0) {
  [IO.File]::WriteAllLines((Join-Path $Work 'untranslated.tsv'), $noTr, $u8)
  Write-Host "  （明细见 work\xscn\untranslated.tsv；这些将按规则 1 原字节保留，无害）"
  $noTr | Select-Object -First 10 | ForEach-Object { '    ' + $_ }
}
