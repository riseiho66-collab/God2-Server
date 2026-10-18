# Task Scheduler owns this hidden wrapper so the loopback server survives
# interactive tool/terminal sessions. It starts once; Task Scheduler handles
# bounded restart attempts on failure.
$ErrorActionPreference = 'Stop'
$serverRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$release = Join-Path $serverRoot 'artifacts/releases/map-transfer-repair-20261018'
$deployment = Get-Content -LiteralPath (Join-Path $release 'deployment.json') -Raw | ConvertFrom-Json
$binary = [IO.Path]::GetFullPath($deployment.newExecutable)
$configuration = [IO.Path]::GetFullPath($deployment.newConfig)
$rootPrefix = $serverRoot + [IO.Path]::DirectorySeparatorChar
foreach ($path in @($binary, $configuration)) {
    if (-not $path.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw 'Deployed server path is unavailable or outside the server project.'
    }
}
if ((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash -ine $deployment.newExecutableSHA256) {
    throw 'Deployed server binary does not match its verified release receipt.'
}
$output = Join-Path $release 'task-stdout.log'
$errors = Join-Path $release 'task-stderr.log'
$env:GOD2_LOG_FILE_ONLY = '1'
$child = Start-Process -FilePath $binary -ArgumentList @('--config', $configuration) `
    -WorkingDirectory $serverRoot -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput $output -RedirectStandardError $errors
exit $child.ExitCode
