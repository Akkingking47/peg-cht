$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$out = Join-Path $root '_tm07_probe.txt'
$zhDir = Join-Path $root 'zh'
$rows = New-Object System.Collections.ArrayList
foreach ($f in (Get-ChildItem $zhDir -Filter 'part-*.tsv' | Sort-Object Name)) {
    $t = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
    foreach ($ln in ($t -split "`r`n|`n")) {
        if ($ln -eq '') { continue }
        $p = $ln -split "`t"
        if ($p.Count -ne 2) { continue }
        if ($p[1] -eq '' -or $p[1] -eq $p[0]) { continue }
        [void]$rows.Add([pscustomobject]@{ Src = $p[0]; Dst = $p[1]; File = $f.Name })
    }
}
$patterns = @(
    '/[VIX]+$',
    'Aust\.',
    'Pavia|Brescia|Pistoia|Imperiali|Savona|Spezia|Napoli|Trieste|Littorio|Ariete|Centauro',
    "d'Arm",
    'Africa|African',
    'Saharian|Zouave|Foreign Legion',
    'Rif |Rifle|Rif Div',
    'Destroyer|Fighter|Air Division|Air Army|Guard Air|Naval Landing|Commando',
    'Guards|Corrales|Toledo|Legion|Columna|Celere|Tokko|Yokosuka',
    'Habforce',
    'RTR|CLY|KOH|FDF|RAE|RAA|TKR|WM |NCAC|EAC|Y Force|Wang Army|War Area|Burma',
    'RAD|DIM|DLM|BLM|DC |CC$|Cuir|EDAC|DLC|RAM|RSA|RSM|BS |DBI|Secteur|GRDI|Maritimes',
    'Gpt|DChA|ChA |Cie|Bie|Ban|Bon|Bn ca|Pio|Pion|Auf|PzJ|Pzj|Schtz|Sch ',
    'Rifle|Rif Div|RDiv',
    'Group|Brig|Brigade',
    'Cav\.|Mtn|Tk\.|MG|AT |Aty|RHA|Rgt|Regt',
    'Legion|Tercio|Somali|Capitol|Honor|Volunteer|Special Guard|Guard',
    'Maru|USS|HMS|HMAS'
)
$sb = New-Object System.Text.StringBuilder
foreach ($pat in $patterns) {
    [void]$sb.AppendLine("##### PATTERN: $pat")
    foreach ($r in $rows) {
        if ($r.Src -match $pat) { [void]$sb.AppendLine("$($r.Src)`t=>`t$($r.Dst)") }
    }
}
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
"written $out rows=$($rows.Count)"
