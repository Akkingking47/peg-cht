$ErrorActionPreference = 'Stop'
$base = [string]([char]0x44 + [char]0x3A + [char]0x5C + [char]0x44 + [char]0x53 + [char]0x48 + [char]0x5C + [char]0x519B + [char]0x4E8B + [char]0x6E38 + [char]0x620F + [char]0x6C49 + [char]0x5316)
$inPath  = $base + '\work\xscn\chunks\chunk-02.tsv'
$outPath = $base + '\work\xscn\zh\part-02.tsv'
$mapPath = $base + '\work\xscn\_map02.psd1'
$log = $base + '\work\xscn\_dbg.txt'

$out = New-Object System.Collections.Generic.List[string]
$out.Add('inPathExists=' + [System.IO.File]::Exists($inPath))
$bytes = [System.IO.File]::ReadAllBytes($inPath)
$out.Add('byteLen=' + $bytes.Length)
$out.Add('firstBytes=' + (($bytes[0..11] | ForEach-Object { $_.ToString('X2') }) -join ' '))
$latin1 = [System.Text.Encoding]::GetEncoding(28591)
$raw = $latin1.GetString($bytes)
$out.Add('rawHex0=' + (($raw.ToCharArray()[0..7] | ForEach-Object { ([int]$_).ToString('X4') }) -join ' '))
$core = ($raw -split "`n")[0]
if ($core.EndsWith("`r")) { $core = $core.Substring(0,$core.Length-1) }
$out.Add('coreHex=' + (($core.ToCharArray() | ForEach-Object { ([int]$_).ToString('X4') }) -join ' '))
$cb = $latin1.GetBytes($core)
$out.Add('coreBytes=' + (($cb | ForEach-Object { $_.ToString('X2') }) -join ' '))
$rec = [System.Text.Encoding]::UTF8.GetString($cb)
$out.Add('recHex=' + (($rec.ToCharArray() | ForEach-Object { ([int]$_).ToString('X4') }) -join ' '))
[System.IO.File]::WriteAllLines($log, $out, (New-Object System.Text.UTF8Encoding($false)))
"done"
