# PeG-WW2 DOCS 汉化 · .xls（Biff8）处理器 —— 抽取 / 回写 · 默认 dry-run
# 依赖：本机 Excel COM（已实测可用）。**原件零改动**：只在 docs-zh\ 下另存副本。
#
# 用法:
#   pwsh -File doc_xls.ps1 -Mode extract -Batch D5
#   pwsh -File doc_xls.ps1 -Mode build   -Batch D5 [-Apply]
#   pwsh -File doc_xls.ps1 -Mode verify  -Batch D5
param(
  [Parameter(Mandatory=$true)][ValidateSet('extract','build','verify')][string]$Mode,
  [string]$Batch = 'D5',
  [switch]$Apply
)
$ErrorActionPreference = 'Continue'
$WS    = 'D:\DSH\军事游戏汉化'
$DOCS  = 'D:\Program Files\PeG-WW2\DOCS'
$ROOT  = Join-Path $WS 'pegww2\docs-zh'
$SRC   = Join-Path $ROOT '_src'
$FILL  = Join-Path $ROOT '_fill'

# D5 批次清单（27 份战役路径表）
$FILES = @(
  '1st SS Leibstandarte Division\LSSAH.xls',
  'Band of Brothers\BoB.xls',
  'Blitzkrieg Objective France\FI.xls',
  'Boot of Death\IT.xls',
  'British Campaign in Europe\WD.xls',
  'Das Reich\DR.xls',
  'Deutsches Afrika Korps\DAK.xls',
  'For Stalin and Motherland\ZS.xls',
  'Germany at War\GAW.xls',
  'Mediterranean 46\LH_GER46.xls',
  'Operation Sealion\Sealion.xls',
  'Red Alert\RA.xls',
  'Red Menace (German side)\RG.xls',
  'Red Menace\RM.xls',
  'Red World Order\S00.xls',
  'Reich Defence\Reich Defense.xls',
  'Road to Berlin\RTB Campaign Path.xls',
  'Romanian Struggle\R7.xls',
  'SSI Campaigns\Blitzkrieg.xls',
  'SSI Campaigns\Crusade in the West (UK).xls',
  'SSI Campaigns\Crusade in the West (US).xls',
  'SSI Campaigns\Defending the Reich.xls',
  'SSI Campaigns\Onward to Berlin.xls',
  'The 7 PzrArmee defends the Reich\7Pzr.xls',
  'The Gallantry of the 7 PzrArmee\G7Pzr.xls',
  'Waffen SS\Waffen SS.xls',
  'WW2½\WWII½.xls'
)

function Get-Translatable($s) {
  if ($null -eq $s) { return $false }
  $t = [string]$s
  if ($t.Trim().Length -eq 0) { return $false }
  # 含 >=2 个连续字母才算可译（纯数字/日期/符号跳过）
  return [regex]::IsMatch($t, '[A-Za-z]{2,}') -and -not [regex]::IsMatch($t, '^[\d\s\-/\.:,]+$')
}

$script:xl = $null
function Open-Xl {
  if ($null -eq $script:xl) {
    $script:xl = New-Object -ComObject Excel.Application
    $script:xl.Visible = $false
    $script:xl.DisplayAlerts = $false
  }
  return $script:xl
}

$totCells = 0; $totFiles = 0; $totWords = 0; $drift = 0
foreach ($rel in $FILES) {
  # ⭐ 源只从**英文原件备份**取：游戏目录投放后已是中文，不能当原文
$ORIG  = Join-Path $WS 'backup\ORIGINAL-PeGWW2-DOCS'
$srcPath = Join-Path $ORIG $rel
if (-not (Test-Path $srcPath)) { $srcPath = Join-Path $DOCS $rel }
  if (-not (Test-Path $srcPath)) { Write-Output "  ⚠️ 缺文件: $rel"; continue }
  $srcTsv  = Join-Path $SRC  ($rel + '.cells.tsv')
  $fillTsv = Join-Path $FILL ($rel + '.cells.tsv')

  if ($Mode -eq 'extract') {
    New-Item -ItemType Directory -Force -Path (Split-Path $srcTsv)  | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $fillTsv) | Out-Null
    $xl = Open-Xl
    $wb = $xl.Workbooks.Open($srcPath, 0, $true)   # ReadOnly
    $rows = New-Object System.Collections.ArrayList
    foreach ($ws in $wb.Worksheets) {
      $cnt = 0
      try { $cnt = $ws.UsedRange.Count } catch { $cnt = 0 }
      if ($cnt -le 0) { continue }
      $ur = $ws.UsedRange
      $r0 = $ur.Row; $c0 = $ur.Column; $rn = $ur.Rows.Count; $cn = $ur.Columns.Count
      for ($r = 0; $r -lt $rn; $r++) {
        for ($c = 0; $c -lt $cn; $c++) {
          $cell = $ws.Cells.Item($r0 + $r, $c0 + $c)
          $v = $null
          try { $v = $cell.Value2 } catch { continue }
          if (Get-Translatable $v) {
            [void]$rows.Add([pscustomobject]@{ Sheet=$ws.Name; Row=($r0+$r); Col=($c0+$c); Text=[string]$v })
          }
        }
      }
    }
    $wb.Close($false)
    $sw = [System.IO.StreamWriter]::new($srcTsv, $false, [System.Text.UTF8Encoding]::new($false))
    $sw.WriteLine("# $rel · 表格文字格抽取（工作表 \t 行 \t 列 \t 原文）")
    $sw.WriteLine("工作表`t行`t列`t原文")
    foreach ($x in $rows) { $sw.WriteLine("$($x.Sheet)`t$($x.Row)`t$($x.Col)`t$($x.Text -replace "`t",'\t')") }
    $sw.Close()
    if (-not (Test-Path $fillTsv)) {
      $sw2 = [System.IO.StreamWriter]::new($fillTsv, $false, [System.Text.UTF8Encoding]::new($false))
      $sw2.WriteLine("# $rel · 译文填写表：只改第五列（译文）")
      $sw2.WriteLine("工作表`t行`t列`t原文`t译文")
      foreach ($x in $rows) { $sw2.WriteLine("$($x.Sheet)`t$($x.Row)`t$($x.Col)`t$($x.Text -replace "`t",'\t')`t") }
      $sw2.Close()
    }
    $totCells += $rows.Count; $totFiles++
    Write-Output ("  [extract] {0,-52} 文字格 {1,4}" -f $rel.Substring(0,[Math]::Min(52,$rel.Length)), $rows.Count)
  }
  elseif ($Mode -eq 'build' -or $Mode -eq 'verify') {
    if (-not (Test-Path $fillTsv)) { Write-Output "  ⚠️ 无译文表: $rel"; continue }
    $tr = @{}
    foreach ($line in [System.IO.File]::ReadAllLines($fillTsv, [System.Text.Encoding]::UTF8)) {
      if ($line.Trim().Length -eq 0 -or $line.StartsWith('#') -or $line.StartsWith('工作表')) { continue }
      $p = $line.Split("`t")
      if ($p.Count -ge 5 -and $p[4].Trim().Length -gt 0) {
        $tr["$($p[0])|$($p[1])|$($p[2])"] = $p[4]
      }
    }
    if ($Mode -eq 'verify') {
      Write-Output ("  [verify ] {0,-52} 待写 {1,4}" -f $rel.Substring(0,[Math]::Min(52,$rel.Length)), $tr.Count)
      continue
    }
    if (-not $Apply) { Write-Output ("  [build  ] {0,-52} 待写 {1,4}（dry-run；加 -Apply）" -f $rel.Substring(0,[Math]::Min(52,$rel.Length)), $tr.Count); continue }
    $xl = Open-Xl
    $wb = $xl.Workbooks.Open($srcPath, 0, $false)
    $n = 0
    foreach ($k in $tr.Keys) {
      $parts = $k.Split('|'); $sh = $parts[0]; $r = [int]$parts[1]; $c = [int]$parts[2]
      try { $wb.Worksheets.Item($sh).Cells.Item($r,$c).Value2 = $tr[$k]; $n++ } catch { Write-Output "     ⚠️ 写入失败 $k" }
    }
    $dst = Join-Path $ROOT $rel   # 另存到 docs-zh（**不改原件**）
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    $wb.SaveAs($dst, 56)          # 56 = xlExcel8 (.xls 97-2003)
    $wb.Close($false)
    Write-Output ("  [build  ] {0,-52} 已写 {1,4} 格 → {2}" -f $rel.Substring(0,[Math]::Min(52,$rel.Length)), $n, $rel)
    $totCells += $n
  }
}
if ($script:xl) { try { $script:xl.Quit() } catch {} ; [System.Runtime.InteropServices.Marshal]::ReleaseComObject($script:xl) | Out-Null }
Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Kill() }
Write-Output ""
Write-Output ("== 汇总：文件 {0} 个 · 文字格 {1}" -f $totFiles, $totCells)
