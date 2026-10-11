"""Prompt-synchronized CDB driver, bounded and using existing firewall checks."""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

HOME = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(HOME/'tools/research'))
from host_capture import digest, powershell, firewall_query, firewall_ready, ARTIFACT
from mode_trace_review import markers
from trace_qualification.frame_stack import TransitionFrameStack

ROOT = HOME/'artifacts/capture_work/host-20260918-1430'
OUT = ROOT/'output'


class Driver:
    def __init__(self, command, run):
        self.log = (OUT/f'{run}-native.log').open('xb')
        self.commands = (OUT/f'{run}-commands.txt').open('x', encoding='ascii')
        self.p = subprocess.Popen(command, cwd=ROOT/'client', stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        self.q = queue.Queue()
        self.deadline = time.monotonic()+110
        self.reader = threading.Thread(target=self.read, daemon=True)
        self.reader.start()

    def read(self):
        try:
            while True:
                data = os.read(self.p.stdout.fileno(), 65536)
                if not data:
                    break
                self.log.write(data)
                self.log.flush()
                self.q.put(data)
        finally:
            self.q.put(None)

    def stop(self):
        data = b''
        while True:
            remaining = self.deadline-time.monotonic()
            if remaining <= 0:
                raise TimeoutError('Capture deadline')
            item = self.q.get(timeout=min(remaining, 20))
            if item is None:
                raise RuntimeError('Debugger exited before prompt')
            data += item
            if re.search(rb'\d+:\d+>\s*$', data):
                return data.decode('ascii', errors='replace')

    def command(self, text):
        self.commands.write(text+'\n')
        self.commands.flush()
        self.p.stdin.write((text+'\n').encode('ascii'))
        self.p.stdin.flush()
        return self.stop()

    def close(self):
        if self.p.poll() is None:
            try:
                self.p.stdin.write(b'q\n')
                self.p.stdin.flush()
                self.p.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                subprocess.run(['taskkill.exe','/PID',str(self.p.pid),'/T','/F'], capture_output=True, timeout=15)
                self.p.wait(timeout=10)
        self.reader.join(timeout=5)
        self.log.close()
        self.commands.close()


def run(name, probe=False):
    if any(OUT.glob(name+'-*')):
        raise ValueError('Outputs already exist')
    request = json.loads((ROOT/'host-request.json').read_text())
    if digest(ROOT/'debugger/cdb.exe') != request['tool']['sha256']:
        raise ValueError('Debugger identity mismatch')
    if powershell('([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) | ConvertTo-Json'):
        raise ValueError('Must not run elevated')
    state = powershell('$v=& { '+firewall_query(request)+' }; $v | ConvertTo-Json -Depth 8')
    if not firewall_ready(state, request['programs']):
        raise ValueError('Firewall not ready')
    if digest(ROOT/'client/God2.exe') != ARTIFACT or digest(request['original']) != ARTIFACT:
        raise ValueError('Client identity mismatch')
    if not probe:
        receipt = json.loads((OUT/'prompt-probe-result.json').read_text())
        if receipt['result'] != 'PROBE_PASS':
            raise ValueError('Interactive probe missing')
    (OUT/f'{name}-firewall.json').write_text(json.dumps(state,indent=2))
    target = [str(Path(os.environ['WINDIR'])/'SysWOW64/cmd.exe'),'/c','exit'] if probe else [str(ROOT/'client/God2.exe')]
    driver = Driver([str(ROOT/'debugger/cdb.exe'), *target], name)
    result = {'result':'FAILED', 'debugger_pid':driver.p.pid}
    stack = TransitionFrameStack()
    try:
        driver.stop()
        if probe:
            value = driver.command('.echo PROMPT_PROBE_OK')
            if 'PROMPT_PROBE_OK' not in value:
                raise ValueError('Probe marker absent')
            result['result'] = 'PROBE_PASS'
            return
        driver.command('r @$t0 = poi(@$peb+8)')
        driver.command('bp (@$t0+302001)')
        driver.command('g')
        driver.command('bc *')
        driver.command('ba e 1 (@$t0+3023bf)')
        driver.command('g')
        driver.command('bc *')
        driver.command('t')
        snapshot = driver.command('r')
        if 'eip=0054a3e8' not in snapshot:
            raise ValueError('Candidate mismatch')
        driver.command('r @$t3 = poi(ntdll!Wow64Transition)')
        driver.command('ba e 1 @$t3')
        driver.command('bp (@$t0+14ed7a)')
        driver.command('sxe av')
        driver.command('t 0n20000')
        known_returns = {}
        next_bp = 2
        for _ in range(40):
            text = driver.command('.printf "SYNC_STOP pid=%x tid=%x pc=%p sp=%p expected=%p caller=%p gate=%p time=%I64x\\n", @$tpid, @$tid, @eip, @esp, poi(@esp), poi(@esp+4), @$t3, @$dbgtime')
            event = markers(text, 'SYNC_STOP')[0]
            event['event_index'] = _
            event.pop('native_line', None)
            if event['pc'] == 0x54ed7a:
                result['client_reconnected'] = True
                break
            if event['pc'] == event['gate']:
                stack.enter(event)
                if event['expected'] not in known_returns:
                    known_returns[event['expected']] = next_bp
                    driver.command(f'bp{next_bp} {event["expected"]:x}')
                    next_bp += 1
                driver.command('g')
            elif event['pc'] in known_returns:
                event['caller'] = event['expected']
                if not stack.returned(event):
                    raise ValueError('Unexplained return mismatch')
                if name == 'sync-b' and not any(f['status'] == 'OPEN' and f['expected_return_pc'] == event['pc'] for f in stack.frames):
                    driver.command(f'bc {known_returns.pop(event["pc"])}')
                driver.command('t 0n20000')
            else:
                raise ValueError('Unexpected stop or step budget exhausted')
        result.update(stack.finish())
        result['result'] = 'PARTIALLY_QUALIFIED' if result['all_returned'] and result.get('client_reconnected') else 'FAILED'
    except Exception as error:
        result.update(error=repr(error), **stack.finish())
        if isinstance(error, (TimeoutError, queue.Empty, OSError, RuntimeError)):
            result['result'] = 'TOOL_ERROR'
    finally:
        driver.close()
        result['native_sha256'] = digest(OUT/f'{name}-native.log')
        (OUT/f'{name}-result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:v for k,v in result.items() if k not in ('frames','unmatched')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name', choices=('prompt-probe','sync-a','sync-b'))
    args = parser.parse_args()
    run(args.name, args.name == 'prompt-probe')
