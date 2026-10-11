param([string]$RunId = '', [switch]$ColdReconnect, [switch]$PostBattleMove,
      [switch]$PostBattleReturn,
      [switch]$PostBattleDoor,
      [switch]$DoorReconnect,
      [switch]$MovedReconnect,
      [string]$BattleSourceRun = 'native-town-quest-battle-20260923-05',
      [string]$DoorSourceRun = 'native-town-battle-door-20260923-01')
$ErrorActionPreference = 'Stop'
if ($ColdReconnect -and $PostBattleMove) { throw 'Cold reconnect and battle movement are separate runs' }
if ($PostBattleReturn -and ($ColdReconnect -or $PostBattleMove)) { throw 'Post-battle return requires its own battle run' }
if ($PostBattleDoor -and ($ColdReconnect -or $PostBattleMove -or $PostBattleReturn)) { throw 'Post-battle doorway requires its own battle run' }
if ($DoorReconnect -and ($ColdReconnect -or $PostBattleMove -or $PostBattleReturn -or $PostBattleDoor -or $MovedReconnect)) { throw 'Door reconnect requires its own run' }
if (-not $RunId) { $RunId = 'native-town-quest-battle-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
$flags = @(
    'god2-strike-runner', '--mode', 'MODE_COMPAT', '--run-id', $RunId, '--timeout', '180',
    '--zero-ui-prefix', '--warning-input-trace', '--auto-pagefile-capacity', '--taiwan-resource-locale',
    '--network-strike', '--cpp-server', '--c2s-strike', '--lab-case', 'A',
    '--post-seed', '--s2c0003', '--login-terminal', '--server-list', '--legacy-character-list-candidate',
    '--recovered-account-auth', '--recovered-character-create', '--recovered-dual-connection', '--recovered-world-entry',
    '--isolated-database', '--movement-lab', '--observe-login-entry', '--probe-login-command', '--probe-login-panel',
    '--probe-login-submit', '--probe-server-confirm', '--observe-character-create', '--probe-character-create',
    '--observe-created-refresh', '--probe-character-select', '--observe-world-entry', '--observe-world-loop',
    '--observe-world-frames', '--town-entry-lab', '--town-consensus-path', '--restore-town-database',
    $(if ($DoorReconnect) { "artifacts/runs/$DoorSourceRun/town-diagnostic-accounts.db" }
      elseif ($ColdReconnect) { "artifacts/runs/$BattleSourceRun/town-diagnostic-accounts.db" }
      else { 'artifacts/runs/native-town-indoor-relogin-20260921-03/town-diagnostic-accounts.db' }),
    '--town-spawn-guides', '--town-quest-progress', '--town-map-probe', '--town-scene-probe',
    '--town-scene-indoor-probe', '--town-scene-indoor-transfer', '--observe-npc-state', '--town-battle-after-quest',
    '--diagnostic-battle-transition', '--observe-socket-battle-vitals', '--diagnostic-battle-participants',
    '--diagnostic-battle-player-appearance', '--diagnostic-battle-animations', '--diagnostic-battle-skill-seed',
    '--diagnostic-battle-hotbar', '--probe-socket-skill-select', '--probe-socket-skill-command',
    '--diagnostic-battle-skill-settlement', '--diagnostic-battle-terminal', '--diagnostic-battle-resources',
    '--observe-socket-outcome-panel', '--observe-socket-battle-exit'
)
if ($ColdReconnect -or $DoorReconnect) {
    $battleFlags = @('--town-battle-after-quest', '--diagnostic-battle-transition', '--observe-socket-battle-vitals',
        '--diagnostic-battle-participants', '--diagnostic-battle-player-appearance', '--diagnostic-battle-animations',
        '--diagnostic-battle-skill-seed', '--diagnostic-battle-hotbar', '--probe-socket-skill-select',
        '--probe-socket-skill-command', '--diagnostic-battle-skill-settlement', '--diagnostic-battle-terminal',
        '--diagnostic-battle-resources', '--observe-socket-outcome-panel', '--observe-socket-battle-exit')
    $flags = @($flags | Where-Object { $_ -notin $battleFlags })
    if ($ColdReconnect) {
        $flags += '--town-completed-quest-restore'
        if ($MovedReconnect) { $flags += '--town-post-battle-position-restore' }
    }
    if ($DoorReconnect) {
        $probeFlags = @('--town-map-probe', '--town-scene-probe', '--town-scene-indoor-probe', '--town-scene-indoor-transfer')
        $flags = @($flags | Where-Object { $_ -notin $probeFlags })
        $flags += @('--observe-quest-text-table', '--probe-npc-request', '--probe-quest-confirm',
                    '--observe-quest-transport', '--complete-npc-conversation', '--town-door-reconnect')
    }
}
if ($MovedReconnect -and -not $ColdReconnect) { throw 'Moved reconnect requires cold reconnect mode' }
if ($PostBattleMove) { $flags += '--probe-post-battle-movement' }
if ($PostBattleReturn) {
    $flags += @('--town-scene-return-probe', '--town-scene-return-commit', '--town-return-after-battle')
}
if ($PostBattleDoor) { $flags += '--town-door-after-battle' }
python tools/strike_lab/apex.py @flags
exit $LASTEXITCODE
