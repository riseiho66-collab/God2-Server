param([string]$ReleaseName = 'native-npc-policy-20260926-01')
$ErrorActionPreference = 'Stop'
if ($ReleaseName -notmatch '^(native-(npc|monster)-policy|kunlun-birthplace|world-clock)-[0-9-]+$') { throw 'Invalid release directory name' }
$serverRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$releaseRoot = Join-Path $serverRoot ('artifacts/releases/' + $ReleaseName)
$activeBinary = Join-Path $serverRoot 'build-town-visibility/Release/god2-server.exe'
$activeConfig = Join-Path $serverRoot 'artifacts/releases/town-chat-welcome-20260924/server-config.json'
$manifest = Get-Content -LiteralPath (Join-Path $releaseRoot 'manifest.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $activeBinary).Hash.ToLowerInvariant() -ne $manifest.old_server_sha256) {
    throw 'Active executable changed since staging'
}
if ((Get-FileHash -LiteralPath $activeConfig).Hash.ToLowerInvariant() -ne $manifest.original_config_sha256) {
    throw 'Active config changed since staging'
}
$connections = @(Get-NetTCPConnection -LocalPort 2592 -ErrorAction SilentlyContinue)
if (@($connections | Where-Object State -eq Established).Count) {
    throw 'Player connection active; staged update retained without interruption'
}
$listeners = @($connections | Where-Object State -eq Listen)
if ($listeners.Count -ne 1) { throw 'Expected one live game listener' }
$serverProcess = Get-Process -Id $listeners[0].OwningProcess
if ($serverProcess.Path -ne $activeBinary) { throw 'Listener executable differs from managed server' }
Stop-ScheduledTask -TaskName 'GOD2 Local Server'
if (Get-Process -Id $serverProcess.Id -ErrorAction SilentlyContinue) {
    Stop-Process -Id $serverProcess.Id
}
try {
    Copy-Item -LiteralPath (Join-Path $releaseRoot 'god2-server.candidate.exe') -Destination $activeBinary -Force
    Copy-Item -LiteralPath (Join-Path $releaseRoot 'server-config.candidate.json') -Destination $activeConfig -Force
    Start-ScheduledTask -TaskName 'GOD2 Local Server'
    $deadline = (Get-Date).AddSeconds(15)
    do {
        Start-Sleep -Milliseconds 300
        $ready = @(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)
    } while (-not $ready.Count -and (Get-Date) -lt $deadline)
    if ($ready.Count -ne 1) { throw 'Updated server did not listen' }
    if ((Get-FileHash -LiteralPath $activeBinary).Hash.ToLowerInvariant() -ne $manifest.candidate_sha256) {
        throw 'Installed server identity mismatch'
    }
    $installedConfig = Get-Content -LiteralPath $activeConfig -Raw | ConvertFrom-Json
    [pscustomobject]@{ Applied=$true; Port=2592; Process=$ready[0].OwningProcess; NativeNpcPlacementsOnly=$installedConfig.development.diagnostic_town.native_npc_placements_only; NativeMonsterPlacementsOnly=$installedConfig.development.native_monster_placements_only; NewCharacterBirthplace=$installedConfig.world.new_character_birthplace } | ConvertTo-Json -Compress
} catch {
    Stop-ScheduledTask -TaskName 'GOD2 Local Server' -ErrorAction SilentlyContinue
    foreach ($running in @(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue)) {
        if ($running.Path -eq $activeBinary) { Stop-Process -Id $running.Id }
    }
    Copy-Item -LiteralPath (Join-Path $releaseRoot 'god2-server.before.exe') -Destination $activeBinary -Force
    Copy-Item -LiteralPath (Join-Path $releaseRoot 'server-config.before.json') -Destination $activeConfig -Force
    Start-ScheduledTask -TaskName 'GOD2 Local Server'
    throw
}
