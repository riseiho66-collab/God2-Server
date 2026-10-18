param(
    [Parameter(Mandatory=$true)][string]$ClientRoot,
    [Parameter(Mandatory=$true)][string]$StagingRoot,
    [Parameter(Mandatory=$true)][string]$ReceiptRoot
)
# CUSTOM-0152. The client must restart to reload its native CAN scene table.
$ErrorActionPreference='Stop'
$client=(Resolve-Path -LiteralPath $ClientRoot).Path
$stage=(Resolve-Path -LiteralPath $StagingRoot).Path
$receipt=[IO.Path]::GetFullPath($ReceiptRoot)
$relative='Data2/map/island01/Island01.can'
$old='f2b9ca9dc4dcebcd1c1c40de14ea63f1b2061993f644c49b9c7baca9ce2d2f97'
$new='73156f4c2060f92e1be59fa9c2df30841b3df204121491a765c1ca21e68796ad'
function HashFile([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
if ((Test-Path -LiteralPath $receipt) -or !(Test-Path -LiteralPath (Split-Path -Parent $receipt) -PathType Container)) { throw 'Receipt root must be new with an existing parent.' }
if ($receipt.StartsWith($client+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Receipt must be outside the client.' }
$running=@(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($client+'\',[StringComparison]::OrdinalIgnoreCase) -and $_.Name -match '^God2.*\.exe$'
})
if ($running.Count) { throw 'Close this game and launcher before applying the scene table.' }
$manifest=Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.designId -ne 'CUSTOM-0152' -or $manifest.path -ne $relative -or $manifest.oldSHA256 -ne $old -or $manifest.newSHA256 -ne $new) { throw 'Unexpected CAN candidate.' }
$target=Join-Path $client $relative
$source=Join-Path $stage $relative
if ((HashFile $target) -ne $old -or (HashFile $source) -ne $new) { throw 'CAN source/candidate changed.' }
$before=[IO.File]::ReadAllBytes($target)
$after=[IO.File]::ReadAllBytes($source)
if ($before.Length -ne 2580 -or $after.Length -ne 2580) { throw 'CAN length changed.' }
$changed=@(0..2579 | Where-Object { $before[$_] -ne $after[$_] })
if (($changed -join ',') -ne '2340,2344,2364') { throw 'Unexpected CAN byte differences.' }
[IO.Directory]::CreateDirectory($receipt) | Out-Null
$backup=Join-Path $receipt 'Island01.original.can'
[IO.File]::WriteAllBytes($backup,$before)
if ((HashFile $backup) -ne $old) { throw 'Rollback baseline changed.' }
try {
    if ((HashFile $target) -ne $old) { throw 'CAN changed during application.' }
    [IO.File]::WriteAllBytes($target,$after)
    if ((HashFile $target) -ne $new) { throw 'Applied CAN failed verification.' }
    [pscustomobject]@{ designId='CUSTOM-0152'; appliedAt=(Get-Date).ToString('o'); target=$target; beforeSHA256=$old; afterSHA256=$new; actualChangedBytes=3; fields=@('scene10->34','scene12->33','scene22->29'); serverRouteAcceptance='SEPARATE'; databaseModified=$false } |
        ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $receipt 'applied.json') -Encoding utf8
} catch {
    [IO.File]::WriteAllBytes($target,$before)
    if ((HashFile $target) -ne $old) { throw 'Application failed and rollback needs inspection.' }
    throw
}
Write-Output 'Applied three repaired room selectors; original CAN records and all other scenes preserved.'
