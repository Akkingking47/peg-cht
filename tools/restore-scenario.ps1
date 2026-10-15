<#
  restore-scenario.ps1 —— 把 efile 的 SCENARIO\ 恢复到官方原始状态
  =====================================================================
  背景：
    2026-09-20 部署场景文本汉化时，因 PowerShell 语法错误导致"先备份"那一步
    整段未执行，而"覆盖"那一段执行了 → EFILE_OLGWW2 / EFILE_OPENPG 的
    SCENARIO\*.txt 被中文译文覆盖，当时没有原文备份。
    事后从官网重新下载了官方 efile 包并整包存档，本脚本用于一键回滚。

  原始版基线（官方包整包存档）：
    backup\ORIGINAL-EFILE_OLGWW2\   (1199 个文件)
    backup\ORIGINAL-EFILE_OPENPG\   (349 个文件)

  用法：
    # 预览将要恢复哪些文件（不改动）
    .\restore-scenario.ps1 -WhatIf

    # 恢复指定 efile 的 SCENARIO\*.txt 为英文原文
    .\restore-scenario.ps1 -Efile EFILE_OLGWW2

    # 恢复全部
    .\restore-scenario.ps1 -Efile all
#>
[CmdletBinding()]
param(
    [ValidateSet('EFILE_OLGWW2', 'EFILE_OPENPG', 'all')]
    [string]$Efile = 'all',
    [string]$GameDir = 'D:\OpenPG2',
    [string]$BackupDir = 'D:\DSH\军事游戏汉化\backup',
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

$targets = if ($Efile -eq 'all') { @('EFILE_OLGWW2', 'EFILE_OPENPG') } else { @($Efile) }

foreach ($ef in $targets) {
    $src = Join-Path $BackupDir "ORIGINAL-$ef\SCENARIO"
    $dst = Join-Path $GameDir "$ef\SCENARIO"

    Write-Host ""
    Write-Host ("=== {0} ===" -f $ef)
    if (-not (Test-Path $src)) { Write-Host ("  跳过：找不到原始基线 {0}" -f $src) -ForegroundColor Yellow; continue }
    if (-not (Test-Path $dst)) { Write-Host ("  跳过：找不到游戏目录 {0}" -f $dst) -ForegroundColor Yellow; continue }

    $files = @(Get-ChildItem $src -File)
    Write-Host ("  原始基线: {0}（{1} 个文件）" -f $src, $files.Count)
    Write-Host ("  目标目录: {0}" -f $dst)

    if ($WhatIf) {
        Write-Host "  [预览模式] 将把上述文件复制到目标目录，未做任何改动" -ForegroundColor Cyan
        continue
    }

    $n = 0
    foreach ($f in $files) {
        Copy-Item $f.FullName (Join-Path $dst $f.Name) -Force
        $n++
    }
    Write-Host ("  已恢复 {0} 个文件" -f $n) -ForegroundColor Green
}

Write-Host ""
Write-Host "完成。若要重新应用中文，运行场景部署脚本即可。" -ForegroundColor Green
