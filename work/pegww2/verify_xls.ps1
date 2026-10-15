# PeG-WW2 DOCS · D5（.xls）逐格核验 —— **只开副本**（本机 Excel COM 同实例开两个 workbook 会 E_FAIL）
# 判据：
#   G3-a 已填格：副本值 == 译表译文
#   G3-b 未填格：副本值 == 译表里记录的**原值**（证明没有误改/丢数据；地图文件名按纪律保留原文正落此类）
param([string]$Batch = 'D5')
$ErrorActionPreference = 'Continue'
$WS = 'D:\DSH\军事游戏汉化'; $ROOT = Join-Path $WS 'pegww2\docs-zh'
$FILL = Join-Path $ROOT '_fill'

$FILES = @(
  '1st SS Leibstandarte Division\LSSAH.xls','Band of Brothers\BoB.xls',
  'Blitzkrieg Objective France\FI.xls','Boot of Death\IT.xls',
  'British Campaign in Europe\WD.xls','Das Reich\DR.xls',
  'Deutsches Afrika Korps\DAK.xls','For Stalin and Motherland\ZS.xls',
  'Germany at War\GAW.xls','Mediterranean 46\LH_GER46.xls',
  'Operation Sealion\Sealion.xls','Red Alert\RA.xls',
  'Red Menace (German side)\RG.xls','Red Menace\RM.xls',
  'Red World Order\S00.xls','Reich Defence\Reich Defense.xls',
  'Road to Berlin\RTB Campaign Path.xls','Romanian Struggle\R7.xls',
  'SSI Campaigns\Blitzkrieg.xls','SSI Campaigns\Crusade in the West (UK).xls',
  'SSI Campaigns\Crusade in the West (US).xls','SSI Campaigns\Defending the Reich.xls',
  'SSI Campaigns\Onward to Berlin.xls','The 7 PzrArmee defends the Reich\7Pzr.xls',
  'The Gallantry of the 7 PzrArmee\G7Pzr.xls','Waffen SS\Waffen SS.xls',
  'WW2½\WWII½.xls'
)
function Read-Cells($p) {
  $d = @{}
  if (-not (Test-Path $p)) { return $d }
  foreach ($line in [System.IO.File]::ReadAllLines($p, [System.Text.Encoding]::UTF8)) {
    if ($line.Trim().Length -eq 0 -or $line.StartsWith('#') -or $line.StartsWith('工作表')) { continue }
    $f = $line.Split("`t")
    if ($f.Count -ge 4) {
      $zh = if ($f.Count -ge 5) { $f[4] } else { '' }
      $d["$($f[0])|$($f[1])|$($f[2])"] = @{ orig = $f[3]; zh = $zh }
    }
  }
  return $d
}
$filesOk = 0; $filesBad = 0; $chkFill = 0; $chkKeep = 0; $badFill = 0; $badKeep = 0
foreach ($rel in $FILES) {
  $dst = Join-Path $ROOT $rel
  if (-not (Test-Path $dst)) { Write-Output "  X 缺副本: $rel"; $filesBad++; continue }
  $cells = Read-Cells (Join-Path $FILL ($rel + '.cells.tsv'))
  if ($cells.Count -eq 0) { Write-Output "  ! 空译表: $rel"; continue }
  $xl = $null; $wb = $null
  $nf = 0; $nk = 0; $nFill = 0; $nKeep = 0; $sample = New-Object System.Collections.ArrayList
  try {
    $xl = New-Object -ComObject Excel.Application; $xl.Visible = $false; $xl.DisplayAlerts = $false
    $wb = $xl.Workbooks.Open($dst, 0, $true)
    foreach ($k in $cells.Keys) {
      $p = $k.Split('|'); $sh = $p[0]; $r = [int]$p[1]; $c = [int]$p[2]
      $v = $null
      try { $v = $wb.Worksheets.Item($sh).Cells.Item($r, $c).Value2 } catch { [void]$sample.Add("取格失败 $sh r${r}c${c}"); continue }
      if ($cells[$k].zh.Trim().Length -gt 0) {
        $chkFill++; $nFill++
        if ([string]$v -ne [string]$cells[$k].zh) { $badFill++; $nf++; if ($sample.Count -lt 3) { [void]$sample.Add("已填 r${r}c${c} 期望[$($cells[$k].zh)]实得[$v]") } }
      } else {
        $chkKeep++; $nKeep++
        if ([string]$v -ne [string]$cells[$k].orig) { $badKeep++; $nk++; if ($sample.Count -lt 3) { [void]$sample.Add("未填 r${r}c${c} 原值[$($cells[$k].orig)]被改成[$v]") } }
      }
    }
  } catch { [void]$sample.Add("Excel 异常: $($_.Exception.Message)") }
  finally { if ($wb) { try { $wb.Close($false) } catch {} }; if ($xl) { try { $xl.Quit() } catch {} } }
  Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { try { $_.Kill() } catch {} }
  Start-Sleep -Milliseconds 400
  if ($nf -eq 0 -and $nk -eq 0 -and $sample.Count -eq 0) {
    $filesOk++
    Write-Output ("  OK {0,-46} 已填 {1,4} 正确 · 未填 {2,4} 原样" -f $rel.Substring(0, [Math]::Min(46, $rel.Length)), $nFill, $nKeep)
  } else {
    $filesBad++
    Write-Output ("  NG {0,-46} 已填错 {1} · 未填被改 {2} · {3}" -f $rel.Substring(0, [Math]::Min(46, $rel.Length)), $nf, $nk, ($sample -join ' | '))
  }
}
Write-Output ""
Write-Output ("== D5 核验汇总：文件 OK {0} / NG {1} · 已填格核对 {2}（错 {3}）· 未填格核对 {4}（被改 {5}）" -f $filesOk, $filesBad, $chkFill, $badFill, $chkKeep, $badKeep)
