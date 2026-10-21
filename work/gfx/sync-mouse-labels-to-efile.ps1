<#
.SYNOPSIS
  把根级已汉化的鼠标标签图，同步到遮蔽它的 efile 级 OPENGUI 目录。

.DESCRIPTION
  背景：OpenGen 加载图片时，<efile>\OPENGUI\ 下的同名文件会**遮蔽** <游戏根>\OPENGUI\。
  本作 `EFILE_GUS_Zx` 自带的 mouse_build.png / mouse_missions.png 经像素级比对
  （与根级原始备份**0 个不同像素**）确认就是「根级原版的未译版」，仅容器格式不同
  （RGB 24bpp vs 索引色），因此直接用根级汉化版覆盖，效果与重跑
  `localize-mouse-labels.ps1` 完全等价，且不引入新的重绘风险。

  幂等：目标与源逐字节相同时跳过。
  安全：默认 dry-run，必须显式 -Apply 才写盘；备份文件已存在时不覆盖（保留最初的原始件）。

.NOTES
  不属于本脚本范围的同名遮蔽：
    - EFILE_GUS_Zx\OPENGUI\hex_text.png ：洋红色键(#FF00FF)的**纯图标覆盖层**，
      19 格各 16x16 图标、无任何文字，与 backup\hextext-orig\EFILE_Clu__OPENGUI__hex_text.png
      同类（docs\07 已记录 EFILE_Clu 为此形态并跳过）=> 语言无关，不改。
    - mouse_nums.png ：数字点阵，语言无关，不改。

.EXAMPLE
  pwsh -File .\sync-mouse-labels-to-efile.ps1              # 只报告
  pwsh -File .\sync-mouse-labels-to-efile.ps1 -Apply       # 实际写入
#>
[CmdletBinding()]
param(
    [string]$SourceDir = 'D:\OpenGeneral\OPENGUI',
    [string[]]$Targets = @(
        'D:\OpenGeneral\EFILE_GUS_Zx\OPENGUI\mouse_build.png',
        'D:\OpenGeneral\EFILE_GUS_Zx\OPENGUI\mouse_missions.png'
    ),
    [string]$BackupDir = 'D:\DSH\军事游戏汉化\backup\OpenGeneral-EFILE_GUS_Zx-opengui',
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$mode = if ($Apply) { 'APPLY' } else { 'DRY-RUN' }
Write-Host "=== sync-mouse-labels-to-efile [$mode] ==="
Write-Host "源目录 : $SourceDir"
Write-Host "备份到 : $BackupDir"
Write-Host ""

$changed = 0
$skipped = 0
$failed = 0

foreach ($t in $Targets) {
    $name = Split-Path -Leaf $t
    $src = Join-Path $SourceDir $name

    if (-not (Test-Path -LiteralPath $src)) { Write-Warning "源不存在，跳过: $src"; $failed++; continue }
    if (-not (Test-Path -LiteralPath $t))   { Write-Warning "目标不存在，跳过: $t";   $failed++; continue }

    $hSrc = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
    $hDst = (Get-FileHash -LiteralPath $t   -Algorithm SHA256).Hash

    if ($hSrc -eq $hDst) {
        Write-Host ("[跳过] {0,-22} 已是汉化版（与源同哈希 {1}）" -f $name, $hSrc.Substring(0, 12))
        $skipped++
        continue
    }

    $szDst = (Get-Item -LiteralPath $t).Length
    $szSrc = (Get-Item -LiteralPath $src).Length
    Write-Host ("[待写] {0,-22} {1} B ({2})  ->  {3} B ({4})" -f `
        $name, $szDst, $hDst.Substring(0, 12), $szSrc, $hSrc.Substring(0, 12))

    if (-not $Apply) { $changed++; continue }

    # 1) 备份（已存在则不覆盖，保留最初原始件）
    if (-not (Test-Path -LiteralPath $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }
    $bak = Join-Path $BackupDir $name
    if (Test-Path -LiteralPath $bak) {
        Write-Host ("       备份已存在，保留: {0}" -f $bak)
    } else {
        Copy-Item -LiteralPath $t -Destination $bak -Force
        Write-Host ("       已备份 -> {0}" -f $bak)
    }

    # 2) 先写到临时文件并回读校验，再落盘
    $tmp = "$t.tmp"
    Copy-Item -LiteralPath $src -Destination $tmp -Force
    $hTmp = (Get-FileHash -LiteralPath $tmp -Algorithm SHA256).Hash
    if ($hTmp -ne $hSrc) {
        Remove-Item -LiteralPath $tmp -Force
        Write-Warning "临时文件校验失败，未落盘: $t"
        $failed++
        continue
    }
    Move-Item -LiteralPath $tmp -Destination $t -Force

    # 3) 落盘后回读校验
    $hNow = (Get-FileHash -LiteralPath $t -Algorithm SHA256).Hash
    if ($hNow -ne $hSrc) {
        Write-Warning "落盘后校验失败: $t"
        $failed++
        continue
    }
    Write-Host ("       已写入并校验通过 ({0})" -f $hNow.Substring(0, 12))
    $changed++
}

Write-Host ""
Write-Host ("汇总: 需处理 {0} / 已同步跳过 {1} / 异常 {2}" -f $changed, $skipped, $failed)
if (-not $Apply -and $changed -gt 0) {
    Write-Host "（dry-run，未写盘。确认后加 -Apply 执行）"
}
if ($failed -gt 0) { exit 1 }
exit 0
