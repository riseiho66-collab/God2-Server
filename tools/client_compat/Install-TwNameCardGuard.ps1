[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$CandidateExe,
    [Parameter(Mandatory=$true)][string]$OriginalBackup,
    [Parameter(Mandatory=$true)][string]$BlackBoxReport,
    [Parameter(Mandatory=$true)][string]$ReceiptPath
)
$ErrorActionPreference = 'Stop'
$sourceHash = '99cde6b666101c0702d712a1a15bf4d83f225a1a521a9c601bd32a6e42debe25'
$repository = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$client = [IO.Path]::GetFullPath((Join-Path $repository '../God2/God2.exe'))
$candidate = (Resolve-Path -LiteralPath $CandidateExe).ProviderPath
$backup = (Resolve-Path -LiteralPath $OriginalBackup).ProviderPath
$report = (Resolve-Path -LiteralPath $BlackBoxReport).ProviderPath
$receipt = [IO.Path]::GetFullPath($ReceiptPath)
if (Test-Path -LiteralPath $receipt) { throw 'Installation receipt already exists.' }
if (-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($receipt)) -PathType Container)) { throw 'Receipt parent must exist.' }
if ($candidate -eq $client -or $backup -eq $client -or $candidate -eq $backup) { throw 'Candidate, original backup and active client must differ.' }
$qa = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$bytes = [IO.File]::ReadAllBytes($candidate)
$before = [IO.File]::ReadAllBytes($backup)
function Get-BytesHash([byte[]]$value) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($value))).Replace('-','').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}
$newHash = Get-BytesHash $bytes
if ((Get-BytesHash $before) -ne $sourceHash) { throw 'Original rollback backup does not match the pinned client.' }
if ($qa.schema -ne 'tw-name-card-native-blackbox/1' -or $qa.passed -ne $true -or $qa.tests -lt 21 -or
    $qa.source_sha256 -ne $sourceHash -or $qa.patched_sha256 -ne $newHash -or
    $qa.network_connections -ne 0 -or $qa.database_opened -ne $false) { throw 'Required native black-box receipt does not match the candidate.' }
$stream = [IO.File]::Open($client,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$changed = $false
try {
    $current = New-Object byte[] $stream.Length
    $done=0
    while ($done -lt $current.Length) {
        $read=$stream.Read($current,$done,$current.Length-$done)
        if ($read -eq 0) { throw 'Short active-client read.' }
        $done+=$read
    }
    if ((Get-BytesHash $current) -ne $sourceHash) { throw 'Active client changed; no write performed.' }
    try {
        $changed=$true
        $stream.Position=0
        $stream.Write($bytes,0,$bytes.Length)
        $stream.SetLength($bytes.Length)
        $stream.Flush($true)
        $stream.Position=0
        $verify = New-Object byte[] $bytes.Length
        $done=0
        while ($done -lt $verify.Length) {
            $read=$stream.Read($verify,$done,$verify.Length-$done)
            if ($read -eq 0) { throw 'Short installed-client read.' }
            $done+=$read
        }
        if ((Get-BytesHash $verify) -ne $newHash) { throw 'Installed client verification failed.' }
    } catch {
        $stream.Position=0
        $stream.Write($before,0,$before.Length)
        $stream.SetLength($before.Length)
        $stream.Flush($true)
        $changed=$false
        throw
    }
} finally { $stream.Dispose() }
$result = [ordered]@{
    schema='tw-name-card-guard-install/1'; installedAt=(Get-Date -Format o)
    activeClient=$client; beforeSHA256=$sourceHash; afterSHA256=$newHash
    originalBackup=$backup; originalBackupSHA256=(Get-BytesHash $before)
    candidate=$candidate; blackBoxReport=$report; blackBoxReportSHA256=(Get-FileHash -LiteralPath $report -Algorithm SHA256).Hash.ToLowerInvariant()
    installed=$changed; exclusiveClientFileAccess=$true; activation='next client launch'
    databaseOpened=$false; serverChanged=$false; credentialsRead=$false
    gameWindowUiAcceptance=$false
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $receipt -Encoding utf8
$result | ConvertTo-Json -Depth 5
