$ErrorActionPreference = 'Stop'
$base = [string]([char]0x44 + [char]0x3A + [char]0x5C + [char]0x44 + [char]0x53 + [char]0x48 + [char]0x5C + [char]0x519B + [char]0x4E8B + [char]0x6E38 + [char]0x620F + [char]0x6C49 + [char]0x5316)
$src = $base + '\work\xscn\_build02c.ps1'
$dst = $base + '\work\xscn\_build02d.ps1'
$code = [System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes($src))
$rx = New-Object System.Text.RegularExpressions.Regex('[^\x00-\x7F]')
$esc = $rx.Replace($code, { param($mt) '([char]0x' + ([int][char]$mt.Value).ToString('X4') + ')' })
[System.IO.File]::WriteAllText($dst, $esc, (New-Object System.Text.ASCIIEncoding))
"wrote " + $dst + " ascii=" + ($rx.IsMatch($esc))
