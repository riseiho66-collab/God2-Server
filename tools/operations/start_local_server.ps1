# Task Scheduler owns this hidden wrapper so the loopback server survives
# interactive tool/terminal sessions. It starts once; Task Scheduler handles
# bounded restart attempts on failure.
$ErrorActionPreference = 'Stop'
$serverRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$binary = Join-Path $serverRoot 'build-town-visibility/Release/god2-server.exe'
$configuration = Join-Path $serverRoot 'artifacts/releases/town-chat-welcome-20260924/server-config.json'
$output = Join-Path $serverRoot 'artifacts/releases/town-chat-welcome-20260924/task-stdout.log'
$errors = Join-Path $serverRoot 'artifacts/releases/town-chat-welcome-20260924/task-stderr.log'
$child = Start-Process -FilePath $binary -ArgumentList @('--config', $configuration) `
    -WorkingDirectory $serverRoot -WindowStyle Hidden -Wait -PassThru `
    -RedirectStandardOutput $output -RedirectStandardError $errors
exit $child.ExitCode
