"""Run the isolated CUSTOM-0059 TCP fixture; never launch or access a live DB.

The executable uses real loopback TCP and Session seed/login/select/world
parsing. Auth handlers and battle admission are explicitly synthetic. This
does not assert full Application login, native rendering or player acceptance.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

def main() -> None:
    binary = ROOT / 'build/tests/Release/thousand-bulls-blackbox.exe'
    output = ROOT / 'artifacts/custom-skills/thousand-bulls'
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'blackbox-server-wire.json'
    result = subprocess.run([str(binary), str(report)], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=45, check=False)
    (output / 'blackbox-server-tcp.log').write_bytes(result.stdout)
    if result.returncode:
        raise SystemExit(f'Fixture failed ({result.returncode}); inspect blackbox-server-tcp.log')
    data = json.loads(report.read_text(encoding='utf-8'))
    if data.get('status') != 'PASS' or len(data.get('cases', [])) != 18:
        raise SystemExit('Missing complete eighteen-scenario report')
    data['test_executable_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
    data['tcp_log_sha256'] = hashlib.sha256(result.stdout).hexdigest()
    data['limitations'] = [
        'Synthetic account admission and trusted fixture battle entry; not Application/DB authentication.',
        'Invalid friendly/subset/repeat commands fail closed without state mutation.',
        'A forged low-MP command bypassing native client eligibility fails closed; same-session MP recovery is not asserted.',
        'Wire and authoritative-state conservation do not establish native four-phase rendering or sound acceptance.'
    ]
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: 18 real TCP scenarios; {report}')

if __name__ == '__main__':
    main()
