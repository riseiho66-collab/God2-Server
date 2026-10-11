param([string]$RunId = '', [switch]$Quest, [switch]$FullQuest, [switch]$Map,
      [switch]$Indoor, [switch]$IndoorMove, [switch]$Battle, [switch]$PostBattleMove,
      [switch]$Render)
$ErrorActionPreference = 'Stop'
if (-not $RunId) { $RunId = 'native-fresh-town-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
$flags = @(
    'god2-strike-runner', '--mode', 'MODE_COMPAT', '--run-id', $RunId, '--timeout', '180',
    '--zero-ui-prefix', '--warning-input-trace', '--auto-pagefile-capacity', '--taiwan-resource-locale',
    '--network-strike', '--cpp-server', '--c2s-strike', '--lab-case', 'A',
    '--post-seed', '--s2c0003', '--login-terminal', '--server-list', '--legacy-character-list-candidate',
    '--recovered-account-auth', '--recovered-character-create', '--recovered-dual-connection', '--recovered-world-entry',
    '--isolated-database', '--movement-lab', '--observe-login-entry', '--probe-login-command', '--probe-login-panel',
    '--probe-login-submit', '--probe-server-confirm', '--observe-character-create', '--probe-character-create',
    '--observe-created-refresh', '--probe-character-select', '--observe-world-entry', '--observe-world-loop',
    '--observe-world-frames', '--town-entry-lab', '--town-consensus-path', '--town-fresh-spawn',
    '--town-spawn-guides', '--town-quest-progress', '--observe-npc-state'
)
if ($PostBattleMove) { $Battle = $true }
if ($Battle) { $IndoorMove = $true }
if ($IndoorMove) { $Indoor = $true }
if ($Indoor) { $Map = $true }
if ($Map) { $FullQuest = $true }
if ($FullQuest) { $Quest = $true }
if ($Quest) {
    $flags += @('--observe-quest-text-table', '--probe-npc-request', '--probe-quest-confirm',
                '--observe-quest-transport', '--complete-npc-conversation')
}
if ($FullQuest) { $flags += @('--town-quest-chain', '--town-quest-reward-chain') }
if ($Map) { $flags += '--town-map-probe' }
if ($Indoor) {
    $flags += @('--town-scene-probe', '--town-scene-indoor-probe', '--town-scene-indoor-transfer')
}
if ($IndoorMove) { $flags += '--town-scene-follow-move' }
if ($Battle) {
    $flags += @('--town-battle-after-quest', '--diagnostic-battle-transition',
                '--observe-socket-battle-vitals', '--diagnostic-battle-participants',
                '--diagnostic-battle-player-appearance', '--diagnostic-battle-animations',
                '--diagnostic-battle-skill-seed', '--diagnostic-battle-hotbar',
                '--probe-socket-skill-select', '--probe-socket-skill-command',
                '--diagnostic-battle-skill-settlement', '--diagnostic-battle-terminal',
                '--diagnostic-battle-resources', '--observe-socket-outcome-panel',
                '--observe-socket-battle-exit')
}
if ($PostBattleMove) { $flags += '--probe-post-battle-movement' }
if ($Render) { $flags += '--observe-town-npc-render' }
python tools/strike_lab/apex.py @flags
exit $LASTEXITCODE
