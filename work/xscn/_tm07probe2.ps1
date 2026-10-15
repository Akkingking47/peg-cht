$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$out = Join-Path $root '_tm07_probe2.txt'
$zhDir = Join-Path $root 'zh'
$rows = New-Object System.Collections.ArrayList
foreach ($f in (Get-ChildItem $zhDir -Filter 'part-*.tsv' | Sort-Object Name)) {
    $t = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    foreach ($ln in ($t -split "`r`n|`n")) {
        if ($ln -eq '') { continue }
        $p = $ln -split "`t"
        if ($p.Count -ne 2) { continue }
        if ($p[1] -eq '' -or $p[1] -eq $p[0]) { continue }
        [void]$rows.Add([pscustomobject]@{ Src = $p[0]; Dst = $p[1] })
    }
}
$patterns = @(
    'USAFFE|USAFFA',
    'Red Banner',
    'Pesada|\bDO\b',
    'WM |MA Div|KMT|PLA Div|KPA|ROK|SNLF|Maru|Korean|Korea',
    'NJA|2NZEF|NZEF',
    'Gpt|DChA|ChA',
    'aaB|aaR|Bn ca| ca ',
    'Bie|Cie|Sapeurs|Bon ',
    'Celere|Columna|Tokko|Yokosuka|Corrales|Toledo|Coldstream|Legion',
    'Destroyer|Destroyer Group|Squadron|Sqn|Flotilla|Group',
    'Med\.|Mortar|Pdr|inch|mm ',
    'Saharian|Zouave|Grouping|Secteur|Groupement|Tercio',
    'Cav\.|Cuir|Hussars|Dragoon|Lancers|Chasseurs|Dragons',
    'Garrison|Yeomanry|BEF|Arm\.|AA|MG|Ind\.|Res\.|Bn Eng',
    'Pz\.|Pz |Leicht|LD|Krad|Schtz|Sch',
    'Army Free|Free|Y Force|Y Forces|EAC|NCAC|Wang',
    'RD|RZ|DLC|BLM|DIM|DLM|RDP|RAM|RSA|RSM|GRDI|GRCA|DC|CC|EDAC',
    'Honor|Volunteer|Special Guard|Capitol|Somali|Guard'
)
$sb = New-Object System.Text.StringBuilder
foreach ($pat in $patterns) {
    [void]$sb.AppendLine("##### PATTERN: $pat")
    foreach ($r in $rows) {
        if ($r.Src -match $pat) { [void]$sb.AppendLine("$($r.Src)`t=>`t$($r.Dst)") }
    }
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
"written $out"
