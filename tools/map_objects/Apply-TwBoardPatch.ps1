param(
    [Parameter(Mandatory=$true)][string]$ClientRoot,
    [Parameter(Mandatory=$true)][string]$StagingRoot,
    [Parameter(Mandatory=$true)][string]$ReceiptRoot
)
# CUSTOM-0151. Apply only the reviewed three-map candidate with a small rollback baseline.
$ErrorActionPreference = 'Stop'
$client = (Resolve-Path -LiteralPath $ClientRoot).Path
$stage = (Resolve-Path -LiteralPath $StagingRoot).Path
$receipt = [IO.Path]::GetFullPath($ReceiptRoot)
if (Test-Path -LiteralPath $receipt) { throw 'Receipt root must be new.' }
if (!(Test-Path -LiteralPath (Split-Path -Parent $receipt) -PathType Container)) { throw 'Receipt parent must exist.' }
if ($receipt.StartsWith($client + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Receipt must be outside the client.' }
function HashFile([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$pins = @{
    'Data2/map/island01/cityi1/cityi1.mdlZ' = 'bb2b72c2cb368ad9e91046783e1c9638ef02318f589cf462f0c45bbfdce04618'
    'Data2/map/south002/citys02/citys02.mdlZ' = 'cf97d0114f636da64d01069b020e9bd290a13e3f13d74960255987d36807e306'
    'Data2/map/south002/citys09/citys09.mdlZ' = 'cdc85743f2b0364c6edb83898a10e01872b97e6e9dd92cc6085a6dba19276aa8'
}
$panelHash = '151033be38448d6f1dabbc1314caad3546f8da80a9be3bab4c754cd85d74b2ed'
$manifest = Get-Content -LiteralPath (Join-Path $stage 'manifest.json') -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'god2-tw-fixed-board-staging/1' -or $manifest.designId -ne 'CUSTOM-0151' -or $manifest.maps.Count -ne 3) { throw 'Unexpected staging manifest.' }
$running = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($client + '\', [StringComparison]::OrdinalIgnoreCase) -and $_.Name -match '^God2.*\.exe$'
})
if ($running.Count) { throw 'Close the client and launcher before applying map resources.' }
$candidate = @()
$seen = @{}
foreach ($map in $manifest.maps) {
    if (!$pins.ContainsKey($map.path) -or $seen.ContainsKey($map.path) -or $map.oldSHA256 -ne $pins[$map.path]) { throw 'Unexpected/duplicate source map.' }
    $seen[$map.path] = $true
    $target = Join-Path $client $map.path
    $source = Join-Path $stage $map.path
    if ((HashFile $target) -ne $pins[$map.path] -or (HashFile $source) -ne $map.newSHA256) { throw 'Map source/candidate hash mismatch.' }
    $panelRelative = (Split-Path -Parent $map.path) + '/npcboard.ROMZ'
    if (Test-Path -LiteralPath (Join-Path $client $panelRelative)) { throw 'Panel target already exists; inspect rather than overwrite.' }
    if ((HashFile (Join-Path $stage $panelRelative)) -ne $panelHash) { throw 'Panel candidate hash mismatch.' }
    $candidate += [pscustomobject]@{ relative=$map.path; oldHash=$map.oldSHA256; newHash=$map.newSHA256; existed=$true }
    $candidate += [pscustomobject]@{ relative=$panelRelative; oldHash=$null; newHash=$panelHash; existed=$false }
}
if (($manifest.maps.placements | Measure-Object).Count -ne 7) { throw 'Expected seven board placements.' }
$created = New-Item -ItemType Directory -Path $receipt
$written = @()
try {
    foreach ($file in $candidate | Where-Object existed) {
        $backup = Join-Path (Join-Path $receipt 'original') $file.relative
        [IO.Directory]::CreateDirectory((Split-Path -Parent $backup)) | Out-Null
        [IO.File]::Copy((Join-Path $client $file.relative), $backup, $false)
        if ((HashFile $backup) -ne $file.oldHash) { throw 'Rollback baseline hash mismatch.' }
    }
    foreach ($file in $candidate) {
        $target = Join-Path $client $file.relative
        if ($file.existed) {
            if ((HashFile $target) -ne $file.oldHash) { throw 'Source changed during application.' }
        } elseif (Test-Path -LiteralPath $target) { throw 'Panel appeared during application.' }
        $written += $file
        [IO.File]::Copy((Join-Path $stage $file.relative), $target, $file.existed)
        if ((HashFile $target) -ne $file.newHash) { throw 'Applied file hash mismatch.' }
    }
    [pscustomobject]@{
        designId='CUSTOM-0151'; appliedAt=(Get-Date).ToString('o'); clientRoot=$client
        stagingManifestSHA256=(HashFile (Join-Path $stage 'manifest.json'))
        files=$candidate; nativeClientAcceptance='PENDING'; databaseModified=$false; executableModified=$false
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receipt 'applied.json') -Encoding utf8
    Write-Output 'Applied three maps / seven fixed board panels. Native-client acceptance remains pending.'
} catch {
    $originalError = $_
    $rollbackErrors = @()
    foreach ($file in $written) {
        try {
            $target = Join-Path $client $file.relative
            if ($file.existed) {
                [IO.File]::Copy((Join-Path (Join-Path $receipt 'original') $file.relative), $target, $true)
                if ((HashFile $target) -ne $file.oldHash) { throw 'Rollback hash mismatch.' }
            } elseif (Test-Path -LiteralPath $target) {
                $failed = Join-Path (Join-Path $receipt 'failed-new-files') $file.relative
                [IO.Directory]::CreateDirectory((Split-Path -Parent $failed)) | Out-Null
                Move-Item -LiteralPath $target -Destination $failed
            }
        } catch { $rollbackErrors += $_.Exception.Message }
    }
    [pscustomobject]@{ error=$originalError.Exception.Message; rollbackErrors=$rollbackErrors } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $receipt 'failed.json') -Encoding utf8
    if ($rollbackErrors.Count) { throw ('Application failed; rollback needs inspection: ' + ($rollbackErrors -join '; ')) }
    throw $originalError
}
