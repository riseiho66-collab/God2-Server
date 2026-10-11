"""Generate environment status from inventory/probe/launch records, not certificates."""
import argparse
import hashlib
import json
from pathlib import Path

from runtime_environment_probe import ARTIFACT, ready
from runtime_evidence import RuntimeStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--prior-evidence', type=Path, required=True)
    parser.add_argument('--sandbox-state', type=Path, required=True)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--status', type=Path, required=True)
    args = parser.parse_args()
    if args.matrix.exists() or args.status.exists():
        parser.error('Reports already exist; preserve prior snapshots')
    inventory = json.loads(args.inventory.read_text(encoding='utf-8-sig'))
    host = json.loads(args.host.read_text(encoding='utf-8-sig'))
    probe = json.loads((args.evidence/'environment-probe.json').read_text(encoding='utf-8'))
    events = json.loads((args.evidence/'client-code-integrity.json').read_text(encoding='utf-8-sig'))
    launch = json.loads((args.evidence/'cdb-startup.json').read_text(encoding='utf-8-sig'))
    native = (args.evidence/'cdb-startup-stdout.log').read_text(encoding='utf-8-sig')
    prior = json.loads((args.prior_evidence/'code-integrity.json').read_text(encoding='utf-8-sig'))
    sandbox_state = json.loads(args.sandbox_state.read_text(encoding='utf-8-sig'))
    if sandbox_state.get('WindowsSandboxEnvironments') != []:
        parser.error('This historical report requires a recorded sandbox shutdown')
    denied = ('Debuggee initialization failed, Win32 error 0n4551' in native
              and any(e['Id'] == 3077 and '\\God2Work\\God2.exe' in e['Message'] for e in events))
    operational = ready(probe, probe['tool']['sha256'])
    if not denied or not operational or list(args.evidence.glob('*-mapped.bin')):
        parser.error('This report describes the measured ready-tool/client-denied case only')
    state = {'artifact_id': ARTIFACT, 'operational_probe': 'RUNTIME_ENVIRONMENT_READY' if operational else 'BLOCKED',
             'runtime_attempt': 'BLOCKED_EXTERNAL_POLICY' if denied else 'UNKNOWN',
             'debugger_pid': launch['pid'], 'client_pid': None, 'client_native_trace': None,
             'memory_dump': None, 'environment_active': False,
             'scope': 'Historical operational observations; not a gate certificate or reusable live authorization',
             'required_external_action': 'Owner/admin must provide an approved isolated lab allowing this exact original GOD2 executable and the Microsoft x86 CDB. Do not disable security controls.',
             'reconstruction': RuntimeStore(Path('artifacts')).status(ARTIFACT), 'record_hashes': {}}
    for path in [args.inventory, args.host, args.sandbox_state, *args.evidence.glob('*.json'), *args.evidence.glob('*.log')]:
        state['record_hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    tools = inventory['tools']
    vs = [t for t in tools if Path(t['path']).name.lower() in ('devenv.exe', 'msvsmon.exe')]
    signed_x32 = next((t for t in tools if Path(t['path']).name.lower() == 'x32dbg.exe'), {})
    prior_denied = any(e['Id'] == 3077 and '\\Debugger\\headless.exe' in e['Message'] for e in prior)
    rows = [
        ['Windows Sandbox / prior headless', 'x86', 'Offline (prior record)', 'x64dbg headless.exe', 'NotSigned (inventory)', 'BLOCKED' if prior_denied else 'UNKNOWN', 'Not attempted', 'Not established', 'YES: approved tool/lab', 'BLOCKED_EXTERNAL_POLICY'],
        ['Windows Sandbox / installed Microsoft CDB', 'x86', 'Offline; source read-only; output writable', 'CDB '+probe['tool']['product_version'], probe['tool']['signature_status'], 'PASS' if operational else 'UNKNOWN', 'BLOCKED 4551 / event 3077' if denied else 'UNKNOWN', 'Benign x86 debug PASS; GOD2 dump absent', 'YES: GOD2 authorization/lab', state['runtime_attempt']],
        ['Existing WinDbg on host', 'x86/x64', 'Host not isolated', 'Installed Microsoft WinDbg/CDB', 'Valid (inventory)', 'UNKNOWN on host', 'Not attempted', 'UNKNOWN on host', 'YES: isolated lab arrangement', 'UNKNOWN'],
        ['Existing Visual Studio native debugger', 'x64 IDE / x86 monitor', 'Host not isolated', 'devenv / msvsmon', 'Valid' if vs and all(t.get('signature_status') == 'Valid' for t in vs) else 'UNKNOWN', 'UNKNOWN', 'Not attempted', 'UNKNOWN in approved isolation', 'YES: isolated lab arrangement', 'UNKNOWN'],
        ['Dedicated Hyper-V lab', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'Not attempted', 'UNKNOWN; VM enumeration unavailable' if host['hyper_v'] == 'UNKNOWN' else 'See host inventory', 'YES: owner/admin lab access', 'UNKNOWN'],
        ['Owner-approved x86 debugger candidate', 'x86', 'Sandbox candidate, not tested', 'Signed x32dbg.exe', signed_x32.get('signature_status', 'UNKNOWN'), 'UNKNOWN (not headless result)', 'Not attempted', 'UNKNOWN', 'YES: suitable client authorization/lab', 'UNKNOWN'],
        ['Separate disposable owner VM', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'Not attempted', 'UNKNOWN; no environment supplied', 'YES', 'UNKNOWN'],
    ]
    header = ['Environment', 'Architecture', 'Isolation', 'Debugger / tracer', 'Signed / trusted status', 'Application Control result', 'Client execution result', 'Runtime capture capability', 'Owner approval required?', 'Status']
    lines = ['# Runtime Environment Matrix', '', 'Generated from local observations. Signed does not mean allowed; UNKNOWN does not mean blocked.', '',
             '| '+' | '.join(header)+' |', '| '+' | '.join(['---']*len(header))+' |']
    lines += ['| '+' | '.join(row)+' |' for row in rows]
    lines += ['', '## Current Blocker', '',
              f"Operational probe: `{state['operational_probe']}` (historical; sandbox stopped).",
              f"GOD2 launch: `{state['runtime_attempt']}`. CDB PID {launch['pid']} is NOT a client PID.",
              'No GOD2 execution trace, mapped image, unpack transition or certificate was produced.', '',
              state['required_external_action'], '',
              '## Evidence', '', f'- Inventory: `{args.inventory.as_posix()}`',
              f'- Probe, raw launch output and Code Integrity events: `{args.evidence.as_posix()}`',
              f'- Machine-readable state: `{args.status.as_posix()}`',
              '- Policy ID: `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`.',
              '- The initial `.ps1` probe was rejected by script execution policy. No policy was changed; subsequent probes used normal native commands through the Sandbox CLI.',
              '- WindowsApps sharing was access-denied; the readable Microsoft tool files were copied to a staging directory with unchanged executable hash/signature. No ACL was altered.', '',
              '## References', '',
              '- [CDB command-line options](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/cdb-command-line-options)',
              '- [Microsoft error enumeration: 4551](https://source.dot.net/Microsoft.Private.Windows.Core/Generated/Basic.CompilerLog.Util/Basic.CompilerLog.Util.Impl.BasicGeneratedFilesAnalyzerReference/Windows.Win32.WIN32_ERROR.g.cs.html)', '']
    args.matrix.write_text('\n'.join(lines), encoding='utf-8')
    args.status.write_text(json.dumps(state, indent=2), encoding='utf-8')
    print(json.dumps({'operational_probe': state['operational_probe'], 'runtime_attempt': state['runtime_attempt']}))


if __name__ == '__main__':
    main()
