param([string]$RunId = '',
      [string]$SourceRun = 'native-town-natural-npc-preload-20260921-01',
      [switch]$ObserveOnly,
      [switch]$ObserveNpcButtons,
      [switch]$NpcDialogue,
      [ValidateSet('open','page','cancel','confirm','reopen')][string]$NpcStop = 'page',
      [ValidateRange(30,600)][int]$TimeoutSeconds = 300)
$ErrorActionPreference = 'Stop'
if (-not $RunId) { $RunId = 'native-ui-world-movement-' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
$source = Join-Path $PSScriptRoot "../../artifacts/runs/$SourceRun/town-diagnostic-accounts.db"
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw 'Saved town source database missing' }
$flags = @(
    'god2-strike-runner', '--mode', 'MODE_COMPAT', '--run-id', $RunId, '--timeout', "$TimeoutSeconds",
    '--zero-ui-prefix', '--warning-input-trace', '--auto-pagefile-capacity', '--taiwan-resource-locale',
    '--network-strike', '--cpp-server', '--c2s-strike', '--lab-case', 'A',
    '--post-seed', '--s2c0003', '--login-terminal', '--server-list', '--legacy-character-list-candidate',
    '--recovered-account-auth', '--recovered-character-create', '--recovered-dual-connection', '--recovered-world-entry',
    '--isolated-database', '--movement-lab', '--observe-login-entry', '--probe-login-command',
    '--probe-login-panel', '--probe-login-submit', '--probe-server-confirm',
    '--observe-character-create', '--probe-character-create', '--observe-created-refresh',
    '--probe-character-select', '--observe-world-entry', '--observe-world-loop', '--observe-world-frames',
    '--town-entry-lab', '--town-consensus-path', '--restore-town-database', (Resolve-Path -LiteralPath $source).Path,
    '--town-spawn-guides', '--observe-npc-state'
)
if ($ObserveOnly -and $NpcDialogue) { throw 'Choose either restored-position observation or NPC dialogue' }
if ($ObserveOnly) { $flags += '--verify-restored-town-position' }
elseif ($NpcDialogue) { $flags += @('--ui-npc-dialogue', '--ui-npc-stop', $NpcStop) }
else { $flags += '--ui-world-movement' }
if ($ObserveNpcButtons) {
    if ($ObserveOnly) { throw 'NPC button observation requires live external UI wait' }
    $flags += '--observe-ui-npc-buttons'
}
python tools/strike_lab/apex.py @flags
exit $LASTEXITCODE
