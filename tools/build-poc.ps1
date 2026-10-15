<#
  OpenGen 汉化 POC（概念验证）脚本
  =================================
  目的：一次性验证阻塞性假设，然后再投入批量翻译。

  验证清单：
    H1  中文能否正常显示（GBK 写入 + 中文字体 + TTF_RenderUNICODE 链路）
    H2  引擎是否接受 UI_Lang=zh（或语言下拉框是否出现 zh）
    H3  中文在 12px 下是否可读
    H4  字号放大到 14px 后布局是否溢出
    H5  较长译文是否被截断
    H6  equip.txt 与 equip.xeqp 谁生效（见 -Action probe-equip）

  用法：
    .\build-poc.ps1 -Action status            # 查看当前状态
    .\build-poc.ps1 -Action apply -FontSize 12   # 应用 POC（12px）
    .\build-poc.ps1 -Action apply -FontSize 14   # 改用 14px 复测
    .\build-poc.ps1 -Action rollback          # 完全回滚，恢复原状

  安全保证：
    - 全程只新增 strings-zh.txt 与 FONTS\Deng.ttf，外加备份后的 Settings.cfg 定点修改
    - 首次 apply 前自动备份 Settings.cfg 到 backup\Settings.cfg.orig
    - rollback 可完全恢复
#>

[CmdletBinding()]
param(
    [ValidateSet('status', 'apply', 'rollback', 'probe-equip')]
    [string]$Action = 'status',

    [ValidateSet(12, 14, 16)]
    [int]$FontSize = 12,

    [string]$EquipFile
)

$ErrorActionPreference = 'Stop'

$Game      = 'D:\OpenPG2'
$Settings  = Join-Path $Game 'Settings.cfg'
$TplPath   = Join-Path $Game 'OPENTXT_SAMPLE\strings-en-template.txt'
$ZhPath    = Join-Path $Game 'OPENGUI\strings-zh.txt'
$FontSrc   = 'C:\Windows\Fonts\Deng.ttf'
$FontDst   = Join-Path $Game 'FONTS\Deng.ttf'
$BackupDir = 'D:\DSH\军事游戏汉化\backup'
$SettingsOrig = Join-Path $BackupDir 'Settings.cfg.orig'
$ZhBackup  = Join-Path $BackupDir 'strings-zh.txt.poc'

$EncCp1252 = [Text.Encoding]::GetEncoding(1252)
$EncGbk    = [Text.Encoding]::GetEncoding(936)
$EncUtf8No = New-Object Text.UTF8Encoding($false)

# POC 词条：主菜单为主（一启动即可见），兼顾战斗信息、地形、兵种、胜负
$Map = [ordered]@{
    'Select Equipment'              = '选择装备'
    'Play Scenario'                 = '单人场景'
    'Play Campaign'                 = '战役模式'
    'Multiplayer scenario'          = '多人游戏'
    'Play by e-mail'                = '邮件对战'
    'Review best careers'           = '最佳战绩'
    'Start game editor (Suite)'     = '游戏编辑器'
    'Load a saved game'             = '载入存档'
    'Settings'                      = '设置'
    'Play intro video'              = '开场动画'
    'Show version'                  = '版本信息'
    'Exit the game'                 = '退出游戏'

    'Next unit'                     = '下一部队'
    'Cancel move'                   = '取消移动'
    'Requisition'                   = '征募部队'
    'Deploy'                        = '部署'
    'Headquarters'                  = '司令部'
    'End turn'                      = '结束回合'
    'Air mode'                      = '空中模式'
    'Chat'                          = '聊天'

    'Destroyed %d  Suppressed %d'   = '击毁 %d  压制 %d'
    'Overrun attack!'               = '突击！'
    'Surrender'                     = '投降'
    'Rugged defense'                = '顽强防御'
    'Support Fire'                  = '火力支援'

    'Brilliant Victory'             = '辉煌胜利'
    'Victory'                       = '胜利'
    'Tactical Victory'              = '战术胜利'
    'Loss'                          = '失败'

    'Clear'                         = '平原'
    'City'                          = '城市'
    'Forest'                        = '森林'
    'Hill'                          = '丘陵'
    'Mountain'                      = '山地'
    'Ocean'                         = '海洋'

    'Infantry'                      = '步兵'
    'Artillery'                     = '炮兵'
    'Fighter'                       = '战斗机'
    'Destroyer'                     = '驱逐舰'
    'Battleship'                    = '战列舰'

    'Axis'                          = '轴心国'
    'Allied'                        = '盟军'

    'Scenario title'                = '场景标题'
    'Unit name'                     = '部队名称'
    'Score'                         = '得分'
    'Date'                          = '日期'

    # --- POC 验证锚点 ---
    # 触发成本极低（启动后按 Esc 即可），用于判定 strings-zh.txt 是否真的生效
    'Do you really want to exit ? ...'             = '确定要退出游戏吗？'
    'Do you really want to launch the Suite ?'     = '确定要启动编辑器吗？'
    'Do you want to save current scenario first ?' = '要先保存当前场景吗？'
}

function Get-SettingsValue {
    param([string]$Key)
    $line = Get-Content $Settings | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if ($line) { return $line.Substring($Key.Length + 1) }
    return '(未设置)'
}

function Show-Status {
    Write-Host ''
    Write-Host '=== OpenGen 汉化 POC 当前状态 ===' -ForegroundColor Cyan

    Write-Host ''
    Write-Host '[Settings.cfg]' -ForegroundColor White
    foreach ($k in 'EFolder', 'UI_Lang', 'Font1', 'SzFont1', 'Font2', 'SzFont2') {
        Write-Host ("  {0,-10} = {1}" -f $k, (Get-SettingsValue $k))
    }

    Write-Host ''
    Write-Host '[文件]' -ForegroundColor White
    Write-Host ("  {0,-46} {1}" -f 'strings-zh.txt', $(if (Test-Path $ZhPath) { "存在 ($((Get-Item $ZhPath).Length) 字节)" } else { '不存在' }))
    Write-Host ("  {0,-46} {1}" -f 'FONTS\Deng.ttf', $(if (Test-Path $FontDst) { "存在 ($([Math]::Round((Get-Item $FontDst).Length / 1MB, 1)) MB)" } else { '不存在' }))
    Write-Host ("  {0,-46} {1}" -f 'backup\Settings.cfg.orig', $(if (Test-Path $SettingsOrig) { '已备份' } else { '未备份' }))

    Write-Host ''
    Write-Host '[其他语言文件]' -ForegroundColor White
    Get-ChildItem (Join-Path $Game 'OPENGUI') -Filter 'strings-*.txt' -ErrorAction SilentlyContinue |
        ForEach-Object { Write-Host ("  {0,-20} {1} 字节" -f $_.Name, $_.Length) }
    Write-Host ''
}

function Invoke-Rollback {
    if (Test-Path $SettingsOrig) {
        Copy-Item $SettingsOrig $Settings -Force
        Write-Host 'Settings.cfg 已恢复为原始版本' -ForegroundColor Green
    }
    else {
        Write-Host '未找到备份 Settings.cfg.orig，未改动 Settings.cfg' -ForegroundColor Yellow
    }

    if (Test-Path $ZhPath) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        Move-Item $ZhPath $ZhBackup -Force
        Write-Host ("strings-zh.txt 已移出游戏目录 -> {0}" -f $ZhBackup) -ForegroundColor Green
    }

    if (Test-Path $FontDst) {
        Remove-Item $FontDst -Force
        Write-Host 'FONTS\Deng.ttf 已删除' -ForegroundColor Green
    }

    Write-Host ''
    Write-Host '回滚完成，游戏已恢复原状。' -ForegroundColor Green
    Write-Host ''
}

function Invoke-Apply {
    Write-Host ''
    Write-Host ("=== 应用 POC（字号 {0}px）===" -f $FontSize) -ForegroundColor Cyan

    # --- 0. 前置检查 ---
    foreach ($p in $Settings, $TplPath) {
        if (-not (Test-Path $p)) { throw "缺少必要文件: $p" }
    }

    # --- 1. 备份 Settings.cfg（只备份一次，保留最原始版本）---
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    if (-not (Test-Path $SettingsOrig)) {
        Copy-Item $Settings $SettingsOrig -Force
        Write-Host ("[1/4] 已备份 Settings.cfg -> {0}" -f $SettingsOrig) -ForegroundColor Green
    }
    else {
        Write-Host '[1/4] Settings.cfg 原始备份已存在，跳过' -ForegroundColor DarkGray
    }

    # --- 2. 安装中文字体 ---
    if (-not (Test-Path $FontSrc)) { throw "找不到中文字体: $FontSrc" }
    Copy-Item $FontSrc $FontDst -Force
    Write-Host ("[2/4] 中文字体已安装 -> {0} ({1} MB)" -f $FontDst, [Math]::Round((Get-Item $FontDst).Length / 1MB, 1)) -ForegroundColor Green

    # --- 3. 生成 strings-zh.txt（结构严格对齐模板）---
    $raw = [IO.File]::ReadAllText($TplPath, $EncCp1252)
    $lines = $raw -split "`r`n"
    $hits = 0
    $usedKeys = New-Object System.Collections.Generic.HashSet[string]

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $trimmed = $lines[$i].Trim()
        if ($trimmed -and $Map.Contains($trimmed)) {
            # 保留原有前后空白，只替换正文
            $lines[$i] = $lines[$i].Replace($trimmed, $Map[$trimmed])
            $hits++
            [void]$usedKeys.Add($trimmed)
        }
    }

    $text = $lines -join "`r`n"
    # 校验可编码为 GBK
    $strict = [Text.Encoding]::GetEncoding(936, [Text.EncoderFallback]::ExceptionFallback, [Text.DecoderFallback]::ExceptionFallback)
    try { [void]$strict.GetBytes($text) }
    catch { throw '生成的文本含无法用 GBK 表示的字符，已中止（不会写出文件）' }

    [IO.File]::WriteAllBytes($ZhPath, $EncGbk.GetBytes($text))
    Write-Host ("[3/4] 已生成 {0}" -f $ZhPath) -ForegroundColor Green
    Write-Host ("      模板行数 {0} / 实际替换 {1} 处 / 命中词条 {2} 条" -f $lines.Count, $hits, $usedKeys.Count)

    $missed = $Map.Keys | Where-Object { -not $usedKeys.Contains($_) }
    if ($missed) {
        Write-Host ('      未命中（模板中不存在该行，已忽略）: ' + ($missed -join ', ')) -ForegroundColor Yellow
    }

    # --- 4. 改写 Settings.cfg ---
    $cfgRaw = [IO.File]::ReadAllText($Settings, $EncCp1252)
    $cfgLines = $cfgRaw -split "`r`n"
    $out = foreach ($l in $cfgLines) {
        switch -Regex ($l) {
            '^UI_Lang=' { 'UI_Lang=zh' }
            '^Font1=' { 'Font1=Deng.ttf' }
            '^Font2=' { 'Font2=Deng.ttf' }
            '^SzFont1=' { "SzFont1=$FontSize" }
            '^SzFont2=' { "SzFont2=$FontSize" }
            default { $l }
        }
    }
    [IO.File]::WriteAllBytes($Settings, $EncCp1252.GetBytes(($out -join "`r`n")))
    Write-Host '[4/4] Settings.cfg 已更新: UI_Lang=zh, Font1/Font2=Deng.ttf' -ForegroundColor Green

    Write-Host ''
    Write-Host '--- 应用后状态 ---' -ForegroundColor Cyan
    foreach ($k in 'EFolder', 'UI_Lang', 'Font1', 'SzFont1', 'Font2', 'SzFont2') {
        Write-Host ("  {0,-10} = {1}" -f $k, (Get-SettingsValue $k))
    }
    Write-Host ''
    Write-Host '下一步：启动 OpenGen.exe，检查主菜单是否显示中文。' -ForegroundColor Yellow
    Write-Host '回滚：.\build-poc.ps1 -Action rollback' -ForegroundColor DarkGray
    Write-Host ''
}

function Invoke-ProbeEquip {
    # 判定引擎读 equip.txt 还是 equip.xeqp：
    # 临时重命名 equip.xeqp，若游戏仍能正常显示单位，则说明读的是 equip.txt。
    if (-not $EquipFile) { throw 'probe-equip 需要 -EquipFile 指定 efile 目录，例如 D:\OpenPG2\EFILE_OPENPG' }
    if (-not (Test-Path $EquipFile)) { throw "目录不存在: $EquipFile" }

    $xeqp = Join-Path $EquipFile 'equip.xeqp'
    $txt = Join-Path $EquipFile 'equip.txt'
    Write-Host ''
    Write-Host '=== equip 生效性探测 ===' -ForegroundColor Cyan
    Write-Host ("  equip.txt  : {0}" -f $(if (Test-Path $txt) { '存在' } else { '不存在' }))
    Write-Host ("  equip.xeqp : {0}" -f $(if (Test-Path $xeqp) { '存在' } else { '不存在' }))

    if (Test-Path $xeqp) {
        $bak = "$xeqp.probe-bak"
        if (Test-Path $bak) { throw "已存在 $bak，请先运行 -Action rollback-probe 或手动清理" }
        Move-Item $xeqp $bak -Force
        Write-Host ''
        Write-Host '已将 equip.xeqp 临时改名为 equip.xeqp.probe-bak' -ForegroundColor Yellow
        Write-Host '请启动游戏并进入该 efile 的征募/单位列表：' -ForegroundColor Yellow
        Write-Host '  - 若单位名称仍正常显示  => 引擎读 equip.txt（可直接汉化 txt）' -ForegroundColor White
        Write-Host '  - 若单位名称缺失/报错    => 引擎读 equip.xeqp（需用 OpenSuite 重新编译）' -ForegroundColor White
        Write-Host ''
        Write-Host ("恢复：Rename-Item '{0}' 'equip.xeqp'" -f $bak) -ForegroundColor DarkGray
    }
    Write-Host ''
}

switch ($Action) {
    'status' { Show-Status }
    'apply' { Invoke-Apply }
    'rollback' { Invoke-Rollback }
    'probe-equip' { Invoke-ProbeEquip }
}
